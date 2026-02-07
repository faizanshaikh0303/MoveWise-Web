from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Work Schedule
    work_hours = Column(String, nullable=True)  # e.g., "9:00 AM - 5:00 PM"
    work_address = Column(String, nullable=True)
    commute_preference = Column(String, nullable=True)  # car, transit, bike, walk
    
    # Sleep Schedule
    sleep_hours = Column(String, nullable=True)  # e.g., "11:00 PM - 7:00 AM"
    noise_preference = Column(String, nullable=True)  # quiet, moderate, doesn't matter
    
    # Hobbies
    hobbies = Column(JSON, nullable=True)  # ["gym", "hiking", "restaurants"]
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="profiles")