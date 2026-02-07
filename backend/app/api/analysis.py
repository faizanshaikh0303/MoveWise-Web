from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, AnalysisList
from app.api.auth import get_current_user
from app.services.places_service import places_service
from app.services.crime_service import crime_service
from app.services.cost_service import cost_service
from app.services.noise_service import noise_service
from app.services.llm_service import llm_service
from typing import List

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/", response_model=AnalysisResponse)
async def create_analysis(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive location analysis.
    This orchestrates all services to create the full report.
    """
    
    try:
        # 1. Geocode both addresses
        current_lat, current_lng = places_service.geocode_address(request.current_address)
        dest_lat, dest_lng = places_service.geocode_address(request.destination_address)
        
        if not current_lat or not dest_lat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not geocode one or both addresses"
            )
        
        # 2. Get user profile for personalization
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()
        
        user_preferences = {}
        if user_profile:
            user_preferences = {
                'work_hours': user_profile.work_hours,
                'work_address': user_profile.work_address,
                'sleep_hours': user_profile.sleep_hours,
                'noise_preference': user_profile.noise_preference,
                'hobbies': user_profile.hobbies or []
            }
        
        # 3. Fetch all data in parallel
        crime_data = await crime_service.compare_crime_rates(
            current_lat, current_lng, request.current_address,
            dest_lat, dest_lng, request.destination_address
        )
        
        amenities_data = places_service.compare_amenities(
            current_lat, current_lng,
            dest_lat, dest_lng,
            hobbies=user_preferences.get('hobbies', [])
        )
        
        cost_data = cost_service.compare_costs(
            request.current_address,
            request.destination_address
        )
        
        noise_data = noise_service.compare_noise_levels(
            request.current_address,
            request.destination_address,
            user_preferences.get('noise_preference')
        )
        
        # 4. Get commute data if work address provided
        commute_data = {}
        if user_profile and user_profile.work_address:
            commute_preference = user_profile.commute_preference or "driving"
            result = places_service.get_commute_info(
                dest_lat, dest_lng,
                user_profile.work_address,
                commute_preference
            )
            if result:
                commute_data = result
        
        # 5. Generate AI insights
        llm_analysis = llm_service.generate_lifestyle_analysis(
            request.current_address,
            request.destination_address,
            crime_data,
            amenities_data,
            cost_data,
            noise_data,
            commute_data,
            user_preferences
        )
        
        # 6. Save analysis to database
        new_analysis = Analysis(
            user_id=current_user.id,
            current_address=request.current_address,
            current_lat=str(current_lat),
            current_lng=str(current_lng),
            destination_address=request.destination_address,
            destination_lat=str(dest_lat),
            destination_lng=str(dest_lng),
            crime_data=crime_data,
            amenities_data=amenities_data,
            cost_data=cost_data,
            noise_data=noise_data,
            commute_data=commute_data,
            overview_summary=llm_analysis.get('overview_summary'),
            lifestyle_changes=llm_analysis.get('lifestyle_changes'),
            ai_insights=llm_analysis.get('ai_insights')
        )
        
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
        
        return new_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Analysis error: {e}")
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


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific analysis by ID"""
    
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return analysis


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