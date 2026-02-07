from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Location Details
    current_address = Column(String, nullable=False)
    current_lat = Column(String, nullable=True)
    current_lng = Column(String, nullable=True)
    
    destination_address = Column(String, nullable=False)
    destination_lat = Column(String, nullable=True)
    destination_lng = Column(String, nullable=True)
    
    # Analysis Results (stored as JSON)
    crime_data = Column(JSON, nullable=True)
    amenities_data = Column(JSON, nullable=True)
    cost_data = Column(JSON, nullable=True)
    noise_data = Column(JSON, nullable=True)
    commute_data = Column(JSON, nullable=True)
    
    # AI-Generated Insights
    overview_summary = Column(Text, nullable=True)
    lifestyle_changes = Column(JSON, nullable=True)  # List of key changes
    ai_insights = Column(Text, nullable=True)  # Full AI analysis
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="analyses")