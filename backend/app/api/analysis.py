from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, AnalysisList
from app.api.auth import get_current_user
from app.core.config import settings
# Existing services
from app.services.places_service import places_service
from app.services.crime_service import crime_service
from app.services.cost_service import cost_service
from app.services.noise_service import noise_service

# NEW: Real data services with FREE APIs
from app.services.fbi_real_crime_service import fbi_real_crime_service  # REAL FBI Data!
from app.services.census_cost_service import census_cost_service  # Census Bureau (FREE!)
from app.services.google_noise_service import google_noise_service
from app.services.scoring_service import scoring_service
from app.services.llm_service import llm_service

from typing import List
import json
import re
from datetime import datetime
import requests
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


def get_zip_from_coords(lat, lng):
    """Reverse geocode to get ZIP code"""
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'latlng': f'{lat},{lng}',
            'key': settings.GOOGLE_MAPS_API_KEY
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            for result in data.get('results', []):
                for component in result.get('address_components', []):
                    if 'postal_code' in component.get('types', []):
                        return component['short_name']
        return '10001'  # Fallback
    except:
        return '10001'

@router.post("/", response_model=AnalysisResponse)
async def create_analysis(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive location analysis with REAL data from:
    - SpotCrime API (real-time crime)
    - OpenStreetMap (noise modeling)
    - HUD FMR + BLS (cost data)
    - Google Places (amenities)
    - Google Maps (commute)
    """
    
    try:
        print(f"🔍 Starting analysis for user {current_user.id}")
        
        # 1. Geocode both addresses
        print("📍 Geocoding addresses...")
        current_lat, current_lng = places_service.geocode_address(request.current_address)
        dest_lat, dest_lng = places_service.geocode_address(request.destination_address)
        
        if not current_lat or not dest_lat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not geocode one or both addresses"
            )
        
        print(f"✓ Current: ({current_lat}, {current_lng})")
        print(f"✓ Destination: ({dest_lat}, {dest_lng})")
        
        # 2. Extract ZIP codes for cost analysis
        # current_zip = extract_zip_code(request.current_address)
        # dest_zip = extract_zip_code(request.destination_address)
        current_zip = get_zip_from_coords(current_lat, current_lng)
        dest_zip = get_zip_from_coords(dest_lat, dest_lng)
        print(f"📮 ZIP codes: {current_zip} → {dest_zip}")
        
        # 3. Get user profile for personalization
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()
        
        user_preferences = {}
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
            # Default preferences
            user_preferences = {
                'work_hours': '9:00 - 17:00',
                'work_address': None,
                'sleep_hours': '23:00 - 07:00',
                'noise_preference': 'moderate',
                'hobbies': [],
                'commute_preference': 'driving'
            }
        
        print(f"👤 User preferences loaded: {user_preferences.get('noise_preference')} noise")
        
        # 4. Fetch REAL DATA from new services
        
        # === CRIME DATA (FBI Crime Data Explorer - REAL DATA!) ===
        print("🚨 Fetching REAL crime data (FBI UCR)...")
        try:
            crime_data = fbi_real_crime_service.compare_crime_data(
                current_lat, current_lng,
                dest_lat, dest_lng,
                user_schedule=user_preferences
            )
            is_real = crime_data['destination'].get('is_real_data', False)
            print(f"✓ Crime: {crime_data['destination']['total_crimes']} crimes/30 days")
            print(f"  Safety Score: {crime_data['destination']['safety_score']}/100")
            print(f"  Data Source: {crime_data['destination'].get('data_source', 'FBI UCR')}")
            if is_real:
                print(f"  ✨ Using REAL FBI official data!")
        except Exception as e:
            print(f"⚠️  FBI Crime service error (using fallback): {e}")
            # Fallback to old service
            crime_data = await crime_service.compare_crime_rates(
                current_lat, current_lng, request.current_address,
                dest_lat, dest_lng, request.destination_address
            )
        
        # === NOISE DATA (OpenStreetMap) ===
        print("🔊 Analyzing noise environment...")
        try:
            noise_data = google_noise_service.compare_noise_levels(
                current_lat, current_lng,
                dest_lat, dest_lng,
                user_preferences.get('noise_preference', 'moderate')
            )
            print(f"✓ Noise: {noise_data['destination']['estimated_db']:.1f} dB")
            print(f"  Category: {noise_data['destination']['noise_category']}")
        except Exception as e:
            print(f"⚠️  Google Noise error (using fallback): {e}")
            # Fallback to old service
            noise_data = noise_service.compare_noise_levels(
                request.current_address,
                request.destination_address,
                user_preferences.get('noise_preference')
            )
        
        # === COST DATA (US Census Bureau - FREE!) ===
        print("💰 Calculating cost of living (US Census Bureau)...")
        try:
            cost_data = census_cost_service.get_comprehensive_costs(
                current_zip,
                dest_zip,
                bedrooms=2  # Can make this configurable via user profile
            )
            print(f"✓ Cost: ${cost_data['destination']['total_monthly']:,.2f}/month")
            print(f"  Affordability: {cost_data['destination']['affordability_score']}/100")
            print(f"  Data Source: {cost_data['destination'].get('data_source', 'Census Bureau')}")
        except Exception as e:
            print(f"⚠️  Census cost service error (using fallback): {e}")
            # Fallback to old service
            cost_data = cost_service.compare_costs(
                request.current_address,
                request.destination_address
            )
        
        # === AMENITIES DATA (Google Places) ===
        print("🏪 Finding nearby amenities (Google Places)...")
        amenities_data = places_service.compare_amenities(
            current_lat, current_lng,
            dest_lat, dest_lng,
            hobbies=user_preferences.get('hobbies', [])
        )
        print(f"✓ Amenities: {amenities_data.get('destination', {}).get('total_count', 0)} places")
        
        # === COMMUTE DATA (Google Maps) ===
        print("🚗 Calculating commute time...")
        commute_data = {}
        if user_profile and user_profile.work_address:
            work_address = user_profile.work_address
            commute_preference = user_preferences.get('commute_preference', 'driving')
            result = places_service.get_commute_info(
                dest_lat, dest_lng,
                work_address,
                commute_preference
            )
            if result:
                commute_data = result
                print(f"✓ Commute: {commute_data.get('duration_minutes', 0)} minutes")
        else:
            # Default commute data
            commute_data = {
                'duration_minutes': 25,
                'distance_miles': 12.0,
                'method': 'driving'
            }
            print(f"✓ Commute: Using default (no work address)")
        
        # 5. Calculate comprehensive scores
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
        
        # 6. Generate AI insights with real data
        print("🤖 Generating AI insights (LLM)...")
        llm_analysis = llm_service.generate_lifestyle_analysis(
            request.current_address,
            request.destination_address,
            crime_data,
            amenities_data,
            cost_data,
            noise_data,
            commute_data,
            user_preferences,
            overall_scores=scores
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

@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific analysis by ID with proper score formatting for frontend"""
    
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    # IMPORTANT: Transform to frontend-expected format
    # The frontend expects scores at the top level
    response_dict = {
        "id": analysis.id,
        "current_address": analysis.current_address,
        "destination_address": analysis.destination_address,
        
        # TOP-LEVEL SCORES (Frontend needs these!)
        "overall_score": analysis.overall_weighted_score or 0,
        "safety_score": analysis.crime_safety_score or 0,
        "affordability_score": analysis.cost_affordability_score or 0,
        "environment_score": analysis.noise_environment_score or 0,
        "lifestyle_score": analysis.lifestyle_score or 0,
        "convenience_score": analysis.convenience_score or 0,
        
        # DATA OBJECTS
        "crime_data": analysis.crime_data or {},
        "cost_data": analysis.cost_data or {},
        "noise_data": analysis.noise_data or {},
        "amenities_data": analysis.amenities_data or {},
        "commute_data": analysis.commute_data or {},
        
        # AI INSIGHTS
        "overview_summary": analysis.overview_summary,
        "lifestyle_changes": analysis.lifestyle_changes or [],
        "ai_insights": analysis.ai_insights,
        
        # METADATA
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None
    }
    
    return response_dict


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