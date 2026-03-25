from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AnalysisRequest(BaseModel):
    current_address: str
    destination_address: str



class AnalysisResponse(BaseModel):
    id: int
    current_address: str
    destination_address: str
    status: str = 'completed'
    crime_data: Optional[Dict[str, Any]] = None
    amenities_data: Optional[Dict[str, Any]] = None
    cost_data: Optional[Dict[str, Any]] = None
    noise_data: Optional[Dict[str, Any]] = None
    commute_data: Optional[Dict[str, Any]] = None
    overview_summary: Optional[str] = None
    lifestyle_changes: Optional[List[str]] = None
    ai_insights: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisList(BaseModel):
    id: int
    current_address: str
    destination_address: str
    status: str = 'completed'
    created_at: datetime

    class Config:
        from_attributes = True