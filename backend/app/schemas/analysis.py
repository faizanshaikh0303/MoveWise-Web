from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AnalysisRequest(BaseModel):
    current_address: str
    destination_address: str


class CrimeData(BaseModel):
    current_crime_rate: Optional[float] = None
    destination_crime_rate: Optional[float] = None
    comparison: Optional[str] = None


class AmenitiesData(BaseModel):
    current_amenities: Optional[Dict[str, int]] = None
    destination_amenities: Optional[Dict[str, int]] = None
    comparison_text: Optional[str] = None


class CostData(BaseModel):
    current_cost: Optional[float] = None
    destination_cost: Optional[float] = None
    change_percentage: Optional[float] = None
    tip: Optional[str] = None


class NoiseData(BaseModel):
    current_noise_level: Optional[str] = None
    destination_noise_level: Optional[str] = None
    analysis: Optional[str] = None


class CommuteData(BaseModel):
    duration_minutes: Optional[int] = None
    method: Optional[str] = None
    description: Optional[str] = None


class AnalysisResponse(BaseModel):
    id: int
    current_address: str
    destination_address: str
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
    created_at: datetime

    class Config:
        from_attributes = True