from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, AnalysisList
from app.api.auth import get_current_user
from app.services.places_service import places_service

from typing import List
import asyncio
import json

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/", response_model=AnalysisResponse)
async def create_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Geocode both addresses, create a pending Analysis record, then dispatch
    a Celery background task to run all API calls. Returns immediately.
    """
    try:
        # Geocode both addresses in parallel (fast, needed to store coords)
        (current_lat, current_lng), (dest_lat, dest_lng) = await asyncio.gather(
            asyncio.to_thread(places_service.geocode_address, request.current_address),
            asyncio.to_thread(places_service.geocode_address, request.destination_address),
        )

        if not current_lat or not dest_lat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not geocode one or both addresses"
            )

        # Create the pending record
        new_analysis = Analysis(
            user_id=current_user.id,
            current_address=request.current_address,
            current_lat=str(current_lat),
            current_lng=str(current_lng),
            destination_address=request.destination_address,
            destination_lat=str(dest_lat),
            destination_lng=str(dest_lng),
            status='pending',
        )
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)

        from app.tasks.analysis_tasks import run_analysis_background
        background_tasks.add_task(run_analysis_background, new_analysis.id)

        print(f"Analysis {new_analysis.id} queued for user {current_user.id}")
        return new_analysis

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating analysis: {str(e)}"
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
        "status": analysis.status,

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
        "action_steps": json.loads(analysis.action_steps_json) if analysis.action_steps_json else [],

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