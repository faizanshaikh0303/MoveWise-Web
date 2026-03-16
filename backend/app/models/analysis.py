from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # ===================================
    # Location Details
    # ===================================
    current_address = Column(String, nullable=False)
    current_lat = Column(String, nullable=True)
    current_lng = Column(String, nullable=True)
    
    destination_address = Column(String, nullable=False)
    destination_lat = Column(String, nullable=True)
    destination_lng = Column(String, nullable=True)
    
    # ===================================
    # Analysis Results (Legacy JSON - kept for backward compatibility)
    # ===================================
    crime_data = Column(JSON, nullable=True)
    amenities_data = Column(JSON, nullable=True)
    cost_data = Column(JSON, nullable=True)
    noise_data = Column(JSON, nullable=True)
    commute_data = Column(JSON, nullable=True)
    
    # ===================================
    # Individual Component Scores (0-100)
    # ===================================
    crime_safety_score = Column(Float, nullable=True, index=True)
    noise_environment_score = Column(Float, nullable=True)
    cost_affordability_score = Column(Float, nullable=True, index=True)
    lifestyle_score = Column(Float, nullable=True)
    convenience_score = Column(Float, nullable=True)
    
    # ===================================
    # Overall Weighted Score
    # ===================================
    # Formula: Safety(30%) + Affordability(25%) + Environment(20%) + Lifestyle(15%) + Convenience(10%)
    overall_weighted_score = Column(Float, nullable=True, index=True)
    overall_grade = Column(String(5), nullable=True)  # A+, A, A-, B+, B, etc.
    
    # ===================================
    # Detailed Data Storage (Full API Responses as JSON Text)
    # ===================================
    # FBI Crime Data Explorer - Crime data with temporal analysis
    crime_data_json = Column(Text, nullable=True)

    # HowLoud SoundScore / Google Places + OpenStreetMap - Noise modeling
    noise_data_json = Column(Text, nullable=True)

    # Static 2024 cost of living estimates
    cost_data_json = Column(Text, nullable=True)
    
    # Google Places - Amenities data
    amenities_data_json = Column(Text, nullable=True)
    
    # Google Maps - Commute data
    commute_data_json = Column(Text, nullable=True)
    
    # ===================================
    # AI-Generated Insights (Original)
    # ===================================
    overview_summary = Column(Text, nullable=True)
    lifestyle_changes = Column(JSON, nullable=True)  # List of key changes
    ai_insights = Column(Text, nullable=True)  # Full AI analysis
    
    # ===================================
    # AI-Generated Action Steps (NEW)
    # ===================================
    # Personalized, data-driven action steps
    action_steps_json = Column(Text, nullable=True)
    
    # ===================================
    # Comparison Insights (NEW)
    # ===================================
    # Current vs Destination comparison summaries
    comparison_insights_json = Column(Text, nullable=True)
    
    # ===================================
    # Metadata
    # ===================================
    # Data sources used: "fbi,howloud,osm,cost2024,google"
    data_sources = Column(String(500), nullable=True)
    
    # Version tracking for analysis algorithm
    analysis_version = Column(String(10), nullable=True, index=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # ===================================
    # Relationships
    # ===================================
    user = relationship("User", back_populates="analyses")
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, score={self.overall_weighted_score}, grade={self.overall_grade})>"