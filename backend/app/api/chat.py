"""Chat endpoint — dashboard-level AI advisor."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.core.database import get_db
from app.models.user import User
from app.models.analysis import Analysis
from app.api.auth import get_current_user
from app.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


@router.post("/")
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analyses = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .all()
    )

    # Lightweight summary — injected into system prompt
    analyses_summary = [
        {
            "id": a.id,
            "from": a.current_address,
            "to": a.destination_address,
            "overall_score": round(a.overall_weighted_score or 0, 1),
            "grade": a.overall_grade or "N/A",
            "safety": round(a.crime_safety_score or 0, 1),
            "affordability": round(a.cost_affordability_score or 0, 1),
            "noise": round(a.noise_environment_score or 0, 1),
            "commute": (a.commute_data or {}).get("duration_minutes"),
        }
        for a in analyses
    ]

    # Full data keyed by ID — used by tool execution
    analyses_by_id = {
        a.id: {
            "id": a.id,
            "current_address": a.current_address,
            "destination_address": a.destination_address,
            "overall_score": round(a.overall_weighted_score or 0, 1),
            "grade": a.overall_grade or "N/A",
            "safety_score": round(a.crime_safety_score or 0, 1),
            "affordability_score": round(a.cost_affordability_score or 0, 1),
            "environment_score": round(a.noise_environment_score or 0, 1),
            "lifestyle_score": round(a.lifestyle_score or 0, 1),
            "convenience_score": round(a.convenience_score or 0, 1),
            "crime_data": a.crime_data or {},
            "cost_data": a.cost_data or {},
            "noise_data": a.noise_data or {},
            "commute_data": a.commute_data or {},
            "amenities_data": a.amenities_data or {},
            "overview_summary": a.overview_summary or "",
        }
        for a in analyses
    }

    history = [{"role": m.role, "content": m.content} for m in request.history]

    return chat_service.chat(
        user_message=request.message,
        history=history,
        analyses_summary=analyses_summary,
        analyses_by_id=analyses_by_id,
        db=db,
    )
