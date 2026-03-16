from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, AnalysisList
from app.api.auth import get_current_user
from app.core.config import settings
from app.services.places_service import places_service
from app.services.crime_service import crime_service
from app.services.cost_service import cost_service
from app.services.noise_service import noise_service

from app.services.scoring_service import scoring_service
from app.services.llm_service import llm_service

from typing import List
import asyncio
import json
from datetime import datetime

router = APIRouter(prefix="/analysis", tags=["analysis"])


# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def safe_json_dumps(obj):
    """Safely convert object to JSON string, handling datetime objects"""
    return json.dumps(obj, cls=DateTimeEncoder)

@router.post("/", response_model=AnalysisResponse)
async def create_analysis(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive location analysis with REAL data from:
    - FBI Crime Data Explorer API (crime data)
    - HowLoud SoundScore / Google Places + OpenStreetMap (noise modeling)
    - Static 2024 cost of living data (cost)
    - Google Places (amenities)
    - Google Maps (commute)
    """
    
    try:
        print(f"🔍 Starting analysis for user {current_user.id}")

        # ── Phase 1: geocode both addresses in parallel ───────────────────────
        print("📍 Geocoding addresses...")
        (current_lat, current_lng), (dest_lat, dest_lng) = await asyncio.gather(
            asyncio.to_thread(places_service.geocode_address, request.current_address),
            asyncio.to_thread(places_service.geocode_address, request.destination_address),
        )

        if not current_lat or not dest_lat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not geocode one or both addresses"
            )

        print(f"✓ Current: ({current_lat}, {current_lng})")
        print(f"✓ Destination: ({dest_lat}, {dest_lng})")

        # ── Phase 2: user profile (fast DB read, no I/O to parallelise) ──────
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()

        if user_profile:
            user_preferences = {
                'work_hours': user_profile.work_hours or '9:00 - 17:00',
                'work_address': user_profile.work_address,
                'sleep_hours': user_profile.sleep_hours or '23:00 - 07:00',
                'noise_preference': user_profile.noise_preference or 'moderate',
                'hobbies': user_profile.hobbies if user_profile.hobbies else [],
                'commute_preference': user_profile.commute_preference or 'driving'
            }
        else:
            user_preferences = {
                'work_hours': '9:00 - 17:00',
                'work_address': None,
                'sleep_hours': '23:00 - 07:00',
                'noise_preference': 'moderate',
                'hobbies': [],
                'commute_preference': 'driving'
            }

        print(f"👤 User preferences loaded: {user_preferences.get('noise_preference')} noise")

        user_noise_pref = user_preferences.get('noise_preference', 'moderate')
        work_address = user_profile.work_address if user_profile else None
        preferred_mode = user_preferences.get('commute_preference', 'driving')
        is_work_from_home = (
            not work_address or
            work_address.strip().lower() == 'work from home' or
            (user_profile and user_profile.commute_preference == 'none')
        )

        # ── Phase 4: all external fetches in parallel ─────────────────────────
        # Crime and cost have fallbacks so they are wrapped in async helpers.
        # Commute runs its 4 transport-mode calls in parallel internally.

        async def fetch_crime():
            data = await crime_service.compare_crime_data(
                current_lat, current_lng, request.current_address,
                dest_lat, dest_lng, request.destination_address,
                user_preferences=user_preferences,
            )
            print(f"✓ Crime: {data['destination']['total_crimes']} crimes/30 days"
                  f" | Safety Score: {data['destination']['safety_score']}/100"
                  f" | Source: {data['destination']['data_source']}")
            return data

        async def fetch_cost():
            data = cost_service.compare_costs(
                request.current_address, request.destination_address
            )
            print(f"✓ Cost: ${data['destination']['total_monthly']:,.2f}/month"
                  f" | Affordability: {data['destination']['affordability_score']}/100")
            return data

        async def fetch_commute():
            if is_work_from_home:
                print("✓ Commute: Work from home (skipped)")
                return {
                    'duration_minutes': 0,
                    'distance': '0 km',
                    'method': 'none',
                    'description': 'You work from home — no commute needed!',
                    'alternatives': {}
                }
            if not work_address:
                print("✓ Commute: No work address (skipped)")
                return {
                    'duration_minutes': None,
                    'distance': 'Unknown',
                    'method': 'driving',
                    'description': 'No work address provided.',
                    'alternatives': {}
                }
            try:
                print(f"   Preferred method: {preferred_mode}")
                print(f"   Calculating times for all transportation modes in parallel...")
                modes = ['driving', 'transit', 'bicycling', 'walking']
                results = await asyncio.gather(*[
                    asyncio.to_thread(
                        places_service.get_commute_info,
                        dest_lat, dest_lng, work_address, mode
                    )
                    for mode in modes
                ], return_exceptions=True)

                all_modes = {}
                primary_result = {}
                for mode, result in zip(modes, results):
                    if isinstance(result, Exception):
                        print(f"   ⚠️  {mode}: Failed ({result})")
                        all_modes[mode] = {'duration_minutes': None, 'distance': None}
                    else:
                        all_modes[mode] = {
                            'duration_minutes': result.get('duration_minutes'),
                            'distance': result.get('distance')
                        }
                        if result.get('duration_minutes'):
                            print(f"   ✓ {mode}: {result['duration_minutes']} min")
                        if mode == preferred_mode:
                            primary_result = result

                data = {
                    'duration_minutes': primary_result.get('duration_minutes'),
                    'distance': primary_result.get('distance'),
                    'method': preferred_mode,
                    'description': primary_result.get('description'),
                    'alternatives': all_modes
                }
                print(f"✓ Primary commute: {data['duration_minutes']} min by {preferred_mode}")
                return data
            except Exception as e:
                print(f"⚠️  Commute calculation error: {e}")
                return {
                    'duration_minutes': None,
                    'distance': 'Unknown',
                    'method': preferred_mode,
                    'description': 'Unable to calculate commute time.',
                    'alternatives': {}
                }

        print("🚀 Fetching crime, noise, cost, amenities, commute in parallel...")
        (
            crime_data,
            noise_comparison,
            cost_data,
            amenities_data,
            commute_data,
        ) = await asyncio.gather(
            fetch_crime(),
            noise_service.compare_noise_levels(
                request.current_address, request.destination_address,
                user_noise_pref
            ),
            fetch_cost(),
            asyncio.to_thread(
                places_service.compare_amenities,
                current_lat, current_lng, dest_lat, dest_lng,
                user_preferences.get('hobbies', [])
            ),
            fetch_commute(),
        )

        noise_current = noise_comparison['current']
        noise_dest    = noise_comparison['destination']
        print(f"   Noise current: {noise_current['score']:.1f} dB → Score: {noise_current['noise_score']}/100")
        print(f"   Noise dest:    {noise_dest['score']:.1f} dB → Score: {noise_dest['noise_score']}/100")
        print(f"✓ Amenities: {amenities_data.get('destination', {}).get('total_count', 0)} places")

        noise_data = {
            'current': {
                'estimated_db':  noise_current['score'],
                'noise_category': noise_current['noise_category'],
                'noise_score':   noise_current['noise_score'],
                'description':   noise_current['description'],
            },
            'destination': {
                'estimated_db':  noise_dest['score'],
                'noise_category': noise_dest['noise_category'],
                'noise_score':   noise_dest['noise_score'],
                'description':   noise_dest['description'],
                'preference_match': noise_dest['preference_match'],
            },
            'comparison': {
                'db_difference':    noise_comparison['comparison']['db_difference'],
                'score_difference': noise_comparison['comparison']['score_difference'],
                'is_quieter':       noise_comparison['comparison']['is_quieter'],
                'category_change':  f"{noise_current['noise_category']} → {noise_dest['noise_category']}",
                'recommendation':   noise_comparison['comparison']['analysis'],
                'preference_match': noise_comparison['comparison']['preference_match'],
            },
        }

        # ── Phase 5: scoring (CPU-only, no I/O) ──────────────────────────────
        print("🎯 Calculating comprehensive scores...")
        scores = scoring_service.calculate_overall_score(
            crime_data=crime_data,
            noise_data=noise_data,
            cost_data=cost_data,
            amenities_data=amenities_data,
            commute_data=commute_data
        )
        print(f"✓ Overall Score: {scores['overall_score']:.1f}/100 (Grade: {scores['grade']})")
        print(f"  • Safety: {scores['component_scores']['safety']['score']:.1f}")
        print(f"  • Affordability: {scores['component_scores']['affordability']['score']:.1f}")
        print(f"  • Environment: {scores['component_scores']['environment']['score']:.1f}")
        print(f"  • Lifestyle: {scores['component_scores']['lifestyle']['score']:.1f}")
        print(f"  • Convenience: {scores['component_scores']['convenience']['score']:.1f}")

        # ── Phase 6: LLM (depends on scores, runs in thread) ─────────────────
        print("🤖 Generating AI insights (LLM)...")
        llm_analysis = await asyncio.to_thread(
            llm_service.generate_lifestyle_analysis,
            request.current_address,
            request.destination_address,
            crime_data,
            amenities_data,
            cost_data,
            noise_data,
            commute_data,
            user_preferences,
            scores
        )
        print(f"✓ AI insights generated")
        print(f"  • Overview: {len(llm_analysis.get('overview_summary', ''))} chars")
        print(f"  • Changes: {len(llm_analysis.get('lifestyle_changes', []))} items")
        print(f"  • Action steps: {len(llm_analysis.get('action_steps', []))} steps")
        
        # 7. Save to database with ALL new fields
        print("💾 Saving analysis to database...")
        
        # Helper function to clean datetime objects from dictionaries
        def clean_for_json(obj):
            """Recursively convert datetime objects to ISO strings"""
            if isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        
        # Clean all data before saving
        clean_crime = clean_for_json(crime_data)
        clean_noise = clean_for_json(noise_data)
        clean_cost = clean_for_json(cost_data)
        clean_amenities = clean_for_json(amenities_data)
        clean_commute = clean_for_json(commute_data)
        
        new_analysis = Analysis(
            user_id=current_user.id,
            current_address=request.current_address,
            current_lat=str(current_lat),
            current_lng=str(current_lng),
            destination_address=request.destination_address,
            destination_lat=str(dest_lat),
            destination_lng=str(dest_lng),
            
            # Legacy JSON fields (cleaned of datetime objects)
            crime_data=clean_crime,
            amenities_data=clean_amenities,
            cost_data=clean_cost,
            noise_data=clean_noise,
            commute_data=clean_commute,
            
            # NEW: Individual component scores
            crime_safety_score=crime_data.get('destination', {}).get('safety_score', 70),
            noise_environment_score=noise_data.get('destination', {}).get('noise_score', 70),
            cost_affordability_score=cost_data.get('destination', {}).get('affordability_score', 70),
            lifestyle_score=scores['component_scores']['lifestyle']['score'],
            convenience_score=scores['component_scores']['convenience']['score'],
            
            # NEW: Overall weighted score
            overall_weighted_score=scores['overall_score'],
            overall_grade=scores['grade'],
            
            # NEW: Detailed data storage (full API responses)
            crime_data_json=safe_json_dumps(crime_data),
            noise_data_json=safe_json_dumps(noise_data),
            cost_data_json=safe_json_dumps(cost_data),
            amenities_data_json=safe_json_dumps(amenities_data),
            commute_data_json=safe_json_dumps(commute_data),
            
            # AI insights
            overview_summary=llm_analysis.get('overview_summary'),
            lifestyle_changes=llm_analysis.get('lifestyle_changes'),
            ai_insights=llm_analysis.get('ai_insights'),
            
            # NEW: Action steps
            action_steps_json=safe_json_dumps(llm_analysis.get('action_steps', [])),
            
            # NEW: Comparison insights
            comparison_insights_json=safe_json_dumps(scores.get('comparison_insights', {})),
            
            # Metadata
            data_sources='fbi,osm,census,google',  # All FREE APIs!
            analysis_version='v2.1'  # Updated to use free APIs
        )
        
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
        
        print(f"✅ Analysis complete! ID: {new_analysis.id}")
        print(f"   Score: {new_analysis.overall_weighted_score}/100 ({new_analysis.overall_grade})")
        
        return new_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating analysis: {str(e)}"
        )


@router.get("/", response_model=List[AnalysisList])
def get_user_analyses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get all analyses for current user"""
    
    analyses = db.query(Analysis).filter(
        Analysis.user_id == current_user.id
    ).order_by(Analysis.created_at.desc()).limit(limit).all()
    
    return analyses


# ADD THIS to your analysis.py file - replaces the get_analysis function

@router.get("/{analysis_id}")
def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific analysis by ID
    
    CRITICAL FIX: Returns scores at TOP LEVEL (not nested) for frontend
    """
    
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    # IMPORTANT: Frontend expects scores at root level, not nested
    response = {
        "id": analysis.id,
        "current_address": analysis.current_address,
        "destination_address": analysis.destination_address,
        
        # ⭐ CRITICAL: Top-level scores (frontend AnalysisResult.jsx needs these!)
        "overall_score": float(analysis.overall_weighted_score or 0),
        "safety_score": float(analysis.crime_safety_score or 0),
        "affordability_score": float(analysis.cost_affordability_score or 0),
        "environment_score": float(analysis.noise_environment_score or 0),
        "lifestyle_score": float(analysis.lifestyle_score or 0),
        "convenience_score": float(analysis.convenience_score or 0),
        "grade": analysis.overall_grade or "F",
        
        # Data objects (with fallbacks)
        "crime_data": analysis.crime_data if analysis.crime_data else {},
        "cost_data": analysis.cost_data if analysis.cost_data else {},
        "noise_data": analysis.noise_data if analysis.noise_data else {},
        "amenities_data": analysis.amenities_data if analysis.amenities_data else {},
        "commute_data": analysis.commute_data if analysis.commute_data else {},
        
        # AI insights
        "overview_summary": analysis.overview_summary or "Analysis complete.",
        "lifestyle_changes": analysis.lifestyle_changes if analysis.lifestyle_changes else [],
        "ai_insights": analysis.ai_insights or "",
        
        # Metadata
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None
    }
    
    return response


@router.delete("/{analysis_id}")
def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an analysis"""
    
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    db.delete(analysis)
    db.commit()
    
    return {"message": "Analysis deleted successfully"}