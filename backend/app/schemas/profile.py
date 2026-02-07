from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProfileBase(BaseModel):
    work_hours: Optional[str] = None
    work_address: Optional[str] = None
    commute_preference: Optional[str] = None
    sleep_hours: Optional[str] = None
    noise_preference: Optional[str] = None
    hobbies: Optional[List[str]] = None


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True