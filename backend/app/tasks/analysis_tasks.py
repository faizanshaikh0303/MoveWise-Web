"""
Celery task: run the full analysis pipeline in the background.

Flow:
  POST /analysis/  →  geocode  →  create Analysis(status='pending')
                   →  run_analysis_task.delay(analysis_id)  →  return immediately

  Worker:  run_analysis_task(analysis_id)
           → status='processing'
           → all parallel API calls  (FBI, noise, cost, amenities, commute, LLM)
           → update Analysis with results + status='completed'
           → on error: status='failed', error_message=...
"""

import asyncio
import json
import logging
import traceback
from datetime import datetime

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Async pipeline (runs inside asyncio.run() from the Celery task)
# ---------------------------------------------------------------------------

async def _run_pipeline(
    current_lat: float,
    current_lng: float,
    current_address: str,
    dest_lat: float,
    dest_lng: float,
    dest_address: str,
    user_preferences: dict,
) -> dict:
    """All external API calls in parallel, returns a dict of fields to write to Analysis."""

    from app.services.places_service import places_service
    from app.services.crime_service import crime_service
    from app.services.cost_service import cost_service
    from app.services.noise_service import noise_service
    from app.services.scoring_service import scoring_service
    from app.services.llm_service import llm_service

    work_address = user_preferences.get('work_address')
    preferred_mode = user_preferences.get('commute_preference', 'driving')
    is_work_from_home = (
        not work_address or
        work_address.strip().lower() == 'work from home' or
        user_preferences.get('commute_preference') == 'none'
    )
    user_noise_pref = user_preferences.get('noise_preference', 'moderate')

    # ── Commute helper ────────────────────────────────────────────────────────
    async def fetch_commute():
        if is_work_from_home:
            return {
                'duration_minutes': 0, 'distance': '0 km', 'method': 'none',
                'description': 'You work from home — no commute needed!',
                'alternatives': {}, 'convenience_score': 100.0,
            }
        if not work_address:
            return {
                'duration_minutes': None, 'distance': 'Unknown', 'method': 'driving',
                'description': 'No work address provided.',
                'alternatives': {}, 'convenience_score': 70.0,
            }
        try:
            modes = ['driving', 'transit', 'bicycling', 'walking']
            results = await asyncio.gather(*[
                asyncio.to_thread(places_service.get_commute_info, dest_lat, dest_lng, work_address, mode)
                for mode in modes
            ], return_exceptions=True)

            all_modes = {}
            primary_result = {}
            for mode, result in zip(modes, results):
                if isinstance(result, Exception):
                    all_modes[mode] = {'duration_minutes': None, 'distance': None}
                else:
                    all_modes[mode] = {
                        'duration_minutes': result.get('duration_minutes'),
                        'distance': result.get('distance'),
                    }
                    if mode == preferred_mode:
                        primary_result = result

            data = {
                'duration_minutes': primary_result.get('duration_minutes'),
                'distance': primary_result.get('distance'),
                'method': preferred_mode,
                'description': primary_result.get('description'),
                'alternatives': all_modes,
            }
            data['convenience_score'] = places_service._calculate_convenience_score(data)
            return data
        except Exception as e:
            logger.warning("Commute calculation error: %s", e)
            return {
                'duration_minutes': None, 'distance': 'Unknown', 'method': preferred_mode,
                'description': 'Unable to calculate commute time.',
                'alternatives': {}, 'convenience_score': 70.0,
            }

    # ── All external fetches in parallel ─────────────────────────────────────
    (
        crime_data,
        noise_comparison,
        cost_data,
        amenities_data,
        commute_data,
    ) = await asyncio.gather(
        crime_service.compare_crime_data(
            current_lat, current_lng, current_address,
            dest_lat, dest_lng, dest_address,
            user_preferences=user_preferences,
        ),
        noise_service.compare_noise_levels(current_address, dest_address, user_noise_pref),
        asyncio.to_thread(cost_service.compare_costs, current_address, dest_address),
        asyncio.to_thread(
            places_service.compare_amenities,
            current_lat, current_lng, dest_lat, dest_lng,
            user_preferences.get('hobbies', []),
        ),
        fetch_commute(),
    )

    # ── Noise reshape ─────────────────────────────────────────────────────────
    noise_current = noise_comparison['current']
    noise_dest    = noise_comparison['destination']
    noise_data = {
        'current': {
            'estimated_db': noise_current['score'],
            'noise_category': noise_current['noise_category'],
            'noise_score': noise_current['noise_score'],
            'description': noise_current['description'],
        },
        'destination': {
            'estimated_db': noise_dest['score'],
            'noise_category': noise_dest['noise_category'],
            'noise_score': noise_dest['noise_score'],
            'description': noise_dest['description'],
            'preference_match': noise_dest['preference_match'],
        },
        'comparison': {
            'db_difference': noise_comparison['comparison']['db_difference'],
            'score_difference': noise_comparison['comparison']['score_difference'],
            'is_quieter': noise_comparison['comparison']['is_quieter'],
            'category_change': f"{noise_current['noise_category']} → {noise_dest['noise_category']}",
            'recommendation': noise_comparison['comparison']['analysis'],
            'preference_match': noise_comparison['comparison']['preference_match'],
        },
    }

    # ── Scoring ───────────────────────────────────────────────────────────────
    scores = scoring_service.calculate_overall_score(
        crime_data=crime_data,
        noise_data=noise_data,
        cost_data=cost_data,
        amenities_data=amenities_data,
        commute_data=commute_data,
    )

    # ── LLM (depends on scores) ───────────────────────────────────────────────
    llm_analysis = await asyncio.to_thread(
        llm_service.generate_lifestyle_analysis,
        current_address, dest_address,
        crime_data, amenities_data, cost_data, noise_data, commute_data,
        user_preferences, scores,
    )

    # ── Datetime cleaner ──────────────────────────────────────────────────────
    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_clean(i) for i in obj]
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    clean_crime     = _clean(crime_data)
    clean_noise     = _clean(noise_data)
    clean_cost      = _clean(cost_data)
    clean_amenities = _clean(amenities_data)
    clean_commute   = _clean(commute_data)

    def _jdump(obj):
        return json.dumps(_clean(obj))

    return {
        # Legacy JSON columns
        'crime_data':     clean_crime,
        'amenities_data': clean_amenities,
        'cost_data':      clean_cost,
        'noise_data':     clean_noise,
        'commute_data':   clean_commute,
        # Scores
        'crime_safety_score':       crime_data.get('destination', {}).get('safety_score', 70),
        'noise_environment_score':  noise_data.get('destination', {}).get('noise_score', 70),
        'cost_affordability_score': scores['component_scores']['affordability']['score'],
        'lifestyle_score':          scores['component_scores']['lifestyle']['score'],
        'convenience_score':        scores['component_scores']['convenience']['score'],
        'overall_weighted_score':   scores['overall_score'],
        'overall_grade':            scores['grade'],
        # JSON text columns
        'crime_data_json':     _jdump(crime_data),
        'noise_data_json':     _jdump(noise_data),
        'cost_data_json':      _jdump(cost_data),
        'amenities_data_json': _jdump(amenities_data),
        'commute_data_json':   _jdump(commute_data),
        # AI insights
        'overview_summary':  llm_analysis.get('overview_summary'),
        'lifestyle_changes': llm_analysis.get('lifestyle_changes'),
        'ai_insights':       llm_analysis.get('ai_insights'),
        'action_steps_json': _jdump(llm_analysis.get('action_steps', [])),
        # Metadata
        'data_sources':      'fbi,osm,census,google',
        'analysis_version':  'v2.1',
    }


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------

@celery_app.task(name="analysis.run", bind=True)
def run_analysis_task(self, analysis_id: int):
    from app.core.database import SessionLocal
    from app.models.analysis import Analysis
    from app.models.profile import UserProfile

    logger.info("Starting analysis task for analysis_id=%d", analysis_id)

    db = SessionLocal()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            logger.error("Analysis %d not found", analysis_id)
            return

        # Mark as processing
        analysis.status = 'processing'
        db.commit()

        # Load user preferences
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == analysis.user_id
        ).first()

        user_preferences = {
            'work_hours':        (user_profile.work_hours   if user_profile else None) or '9:00 - 17:00',
            'work_address':       user_profile.work_address  if user_profile else None,
            'sleep_hours':       (user_profile.sleep_hours  if user_profile else None) or '23:00 - 07:00',
            'noise_preference':  (user_profile.noise_preference if user_profile else None) or 'moderate',
            'hobbies':            user_profile.hobbies if user_profile and user_profile.hobbies else [],
            'commute_preference':(user_profile.commute_preference if user_profile else None) or 'driving',
        }

        current_lat  = float(analysis.current_lat)
        current_lng  = float(analysis.current_lng)
        dest_lat     = float(analysis.destination_lat)
        dest_lng     = float(analysis.destination_lng)

        # Close DB session before the long async run to avoid connection stale
        db.close()
        db = None

        # Run the full pipeline
        result = asyncio.run(_run_pipeline(
            current_lat, current_lng, analysis.current_address,
            dest_lat, dest_lng, analysis.destination_address,
            user_preferences,
        ))

        # Persist results
        db = SessionLocal()
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        for field, value in result.items():
            setattr(analysis, field, value)
        analysis.status = 'completed'
        db.commit()
        logger.info("Analysis %d completed (score=%.1f)", analysis_id, result.get('overall_weighted_score', 0))

        # Notify the SSE stream so the browser updates immediately
        try:
            from app.core.redis_cache import _redis
            r = _redis()
            if r:
                r.publish(f"analysis:done:{analysis.user_id}", str(analysis_id))
        except Exception as pub_err:
            logger.warning("Could not publish SSE event: %s", pub_err)

    except Exception as exc:
        logger.error("Analysis %d failed: %s", analysis_id, exc)
        traceback.print_exc()
        try:
            if db is None:
                db = SessionLocal()
            analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if analysis:
                analysis.status = 'failed'
                analysis.error_message = str(exc)
                db.commit()
        except Exception as inner:
            logger.error("Could not update failed status: %s", inner)
    finally:
        if db:
            db.close()
