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
    # SpotCrime API - Real-time crime data with temporal analysis
    crime_data_json = Column(Text, nullable=True)
    
    # OpenStreetMap - Road classifications and noise modeling
    noise_data_json = Column(Text, nullable=True)
    
    # HUD FMR + BLS - Official cost data
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
    # Data sources used: "spotcrime,osm,hud,bls,google"
    data_sources = Column(String(500), nullable=True)
    
    # Version tracking for analysis algorithm
    analysis_version = Column(String(10), nullable=True, index=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # ===================================
    # Relationships
    # ===================================
    user = relationship("User", back_populates="analyses")
    
    # ===================================
    # Helper Properties
    # ===================================
    
    @property
    def score_breakdown(self):
        """Get formatted score breakdown"""
        return {
            'safety': self.crime_safety_score,
            'affordability': self.cost_affordability_score,
            'environment': self.noise_environment_score,
            'lifestyle': self.lifestyle_score,
            'convenience': self.convenience_score,
            'overall': self.overall_weighted_score,
            'grade': self.overall_grade
        }
    
    @property
    def is_highly_rated(self):
        """Check if destination is highly rated (>= 75)"""
        return self.overall_weighted_score and self.overall_weighted_score >= 75
    
    @property
    def has_concerns(self):
        """Check if any score is below 50"""
        scores = [
            self.crime_safety_score,
            self.cost_affordability_score,
            self.noise_environment_score,
            self.lifestyle_score,
            self.convenience_score
        ]
        return any(score and score < 50 for score in scores if score is not None)
    
    @property
    def top_strength(self):
        """Get the highest scoring category"""
        scores = {
            'Safety': self.crime_safety_score,
            'Affordability': self.cost_affordability_score,
            'Environment': self.noise_environment_score,
            'Lifestyle': self.lifestyle_score,
            'Convenience': self.convenience_score
        }
        
        # Filter out None values
        valid_scores = {k: v for k, v in scores.items() if v is not None}
        
        if not valid_scores:
            return None
        
        return max(valid_scores, key=valid_scores.get)
    
    @property
    def main_concern(self):
        """Get the lowest scoring category"""
        scores = {
            'Safety': self.crime_safety_score,
            'Affordability': self.cost_affordability_score,
            'Environment': self.noise_environment_score,
            'Lifestyle': self.lifestyle_score,
            'Convenience': self.convenience_score
        }
        
        # Filter out None values
        valid_scores = {k: v for k, v in scores.items() if v is not None}
        
        if not valid_scores:
            return None
        
        return min(valid_scores, key=valid_scores.get)
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, score={self.overall_weighted_score}, grade={self.overall_grade})>"