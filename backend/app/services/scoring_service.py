from typing import Dict, Any, Optional
from datetime import datetime


class ScoringService:
    """
    Comprehensive scoring system for location analysis
    Calculates weighted scores based on multiple data sources
    """
    
    # Score weights (must sum to 1.0)
    WEIGHTS = {
        'safety': 0.30,        # Crime data (30%)
        'affordability': 0.25, # Cost of living (25%)
        'environment': 0.20,   # Noise levels (20%)
        'lifestyle': 0.15,     # Amenities (15%)
        'convenience': 0.10    # Commute (10%)
    }
    
    def calculate_overall_score(
        self,
        crime_data: Dict[str, Any],
        noise_data: Dict[str, Any],
        cost_data: Dict[str, Any],
        amenities_data: Optional[Dict[str, Any]] = None,
        commute_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive location score (0-100)
        
        Returns detailed breakdown of all component scores
        """
        
        # Extract individual scores
        safety_score = crime_data.get('destination', {}).get('safety_score', 70)
        affordability_score = cost_data.get('destination', {}).get('affordability_score', 70)
        environment_score = noise_data.get('destination', {}).get('noise_score', 70)
        lifestyle_score = self._calculate_lifestyle_score(amenities_data) if amenities_data else 70
        convenience_score = self._calculate_convenience_score(commute_data) if commute_data else 70
        
        # Calculate weighted overall score
        overall_score = (
            safety_score * self.WEIGHTS['safety'] +
            affordability_score * self.WEIGHTS['affordability'] +
            environment_score * self.WEIGHTS['environment'] +
            lifestyle_score * self.WEIGHTS['lifestyle'] +
            convenience_score * self.WEIGHTS['convenience']
        )
        
        # Generate grade
        grade = self._score_to_grade(overall_score)
        
        # Generate comparison insights
        comparison_insights = self._generate_comparison_insights(
            crime_data,
            noise_data,
            cost_data,
            amenities_data,
            commute_data
        )
        
        return {
            'overall_score': round(overall_score, 1),
            'grade': grade,
            'component_scores': {
                'safety': {
                    'score': round(safety_score, 1),
                    'weight': self.WEIGHTS['safety'],
                    'contribution': round(safety_score * self.WEIGHTS['safety'], 1),
                    'status': self._get_score_status(safety_score)
                },
                'affordability': {
                    'score': round(affordability_score, 1),
                    'weight': self.WEIGHTS['affordability'],
                    'contribution': round(affordability_score * self.WEIGHTS['affordability'], 1),
                    'status': self._get_score_status(affordability_score)
                },
                'environment': {
                    'score': round(environment_score, 1),
                    'weight': self.WEIGHTS['environment'],
                    'contribution': round(environment_score * self.WEIGHTS['environment'], 1),
                    'status': self._get_score_status(environment_score)
                },
                'lifestyle': {
                    'score': round(lifestyle_score, 1),
                    'weight': self.WEIGHTS['lifestyle'],
                    'contribution': round(lifestyle_score * self.WEIGHTS['lifestyle'], 1),
                    'status': self._get_score_status(lifestyle_score)
                },
                'convenience': {
                    'score': round(convenience_score, 1),
                    'weight': self.WEIGHTS['convenience'],
                    'contribution': round(convenience_score * self.WEIGHTS['convenience'], 1),
                    'status': self._get_score_status(convenience_score)
                }
            },
            'comparison_insights': comparison_insights,
            'strengths': self._identify_strengths(
                safety_score, affordability_score, environment_score,
                lifestyle_score, convenience_score
            ),
            'concerns': self._identify_concerns(
                safety_score, affordability_score, environment_score,
                lifestyle_score, convenience_score
            ),
            'recommendation': self._generate_overall_recommendation(
                overall_score,
                safety_score,
                affordability_score,
                environment_score
            )
        }
    
    def _calculate_lifestyle_score(self, amenities_data: Dict[str, Any]) -> float:
        """
        Calculate lifestyle score from amenities data
        
        Factors:
        - Number of desired amenities nearby
        - Variety of amenity types
        - Distance to amenities
        """
        if not amenities_data:
            return 70
        
        destination = amenities_data.get('destination', {})
        
        # Get amenity counts
        total_amenities = destination.get('total_count', 0)
        unique_types = len(destination.get('by_type', {}))
        
        # Base score from quantity (0-50 points)
        quantity_score = min(50, total_amenities * 2)
        
        # Variety bonus (0-30 points)
        variety_score = min(30, unique_types * 3)
        
        # Distance penalty (0-20 points)
        # Closer amenities = higher score
        avg_distance = destination.get('average_distance', 5)
        distance_score = max(0, 20 - (avg_distance * 2))
        
        total_score = quantity_score + variety_score + distance_score
        
        return min(100, max(0, total_score))
    
    def _calculate_convenience_score(self, commute_data: Dict[str, Any]) -> float:
        """
        Calculate convenience score from commute data
        
        Factors:
        - Commute duration
        - Traffic conditions
        - Transportation options
        """
        if not commute_data:
            return 70
        
        duration_minutes = commute_data.get('duration_minutes', 30)
        
        # Ideal commute: 20 minutes or less = 100 points
        # Each additional minute reduces score
        if duration_minutes <= 20:
            base_score = 100
        elif duration_minutes <= 30:
            base_score = 90 - (duration_minutes - 20)
        elif duration_minutes <= 45:
            base_score = 80 - ((duration_minutes - 30) * 1.5)
        elif duration_minutes <= 60:
            base_score = 60 - ((duration_minutes - 45) * 2)
        else:
            base_score = max(20, 30 - ((duration_minutes - 60) * 0.5))
        
        return round(base_score, 1)
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        elif score >= 50:
            return 'C-'
        else:
            return 'D'
    
    def _get_score_status(self, score: float) -> str:
        """Get status label for a score"""
        if score >= 80:
            return 'Excellent'
        elif score >= 70:
            return 'Good'
        elif score >= 60:
            return 'Fair'
        elif score >= 50:
            return 'Needs Attention'
        else:
            return 'Concerning'
    
    def _generate_comparison_insights(
        self,
        crime_data: Dict[str, Any],
        noise_data: Dict[str, Any],
        cost_data: Dict[str, Any],
        amenities_data: Optional[Dict[str, Any]],
        commute_data: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Generate comparative insights between current and destination"""
        
        insights = {}
        
        # Crime comparison
        crime_comp = crime_data.get('comparison', {})
        crime_diff = crime_comp.get('score_difference', 0)
        if crime_diff > 10:
            insights['safety'] = f"Significantly safer ({crime_diff:+.1f} points)"
        elif crime_diff > 0:
            insights['safety'] = f"Slightly safer ({crime_diff:+.1f} points)"
        elif crime_diff > -10:
            insights['safety'] = f"Similar safety levels ({crime_diff:+.1f} points)"
        else:
            insights['safety'] = f"Less safe ({crime_diff:+.1f} points)"
        
        # Cost comparison
        cost_comp = cost_data.get('comparison', {})
        cost_diff = cost_comp.get('monthly_difference', 0)
        if cost_diff < -200:
            insights['affordability'] = f"Much cheaper (${abs(cost_diff):.0f}/month savings)"
        elif cost_diff < 0:
            insights['affordability'] = f"Slightly cheaper (${abs(cost_diff):.0f}/month savings)"
        elif cost_diff < 200:
            insights['affordability'] = f"Similar costs (${cost_diff:.0f}/month more)"
        else:
            insights['affordability'] = f"More expensive (${cost_diff:.0f}/month more)"
        
        # Noise comparison
        noise_comp = noise_data.get('comparison', {})
        db_diff = noise_comp.get('db_difference', 0)
        insights['environment'] = noise_comp.get('db_change_description', 'Similar noise levels')
        
        return insights
    
    def _identify_strengths(
        self,
        safety: float,
        affordability: float,
        environment: float,
        lifestyle: float,
        convenience: float
    ) -> list:
        """Identify top strengths (scores >= 75)"""
        
        scores = {
            'Safety': safety,
            'Affordability': affordability,
            'Environment': environment,
            'Lifestyle': lifestyle,
            'Convenience': convenience
        }
        
        strengths = [
            name for name, score in scores.items()
            if score >= 75
        ]
        
        # Sort by score
        strengths.sort(key=lambda x: scores[x], reverse=True)
        
        return strengths
    
    def _identify_concerns(
        self,
        safety: float,
        affordability: float,
        environment: float,
        lifestyle: float,
        convenience: float
    ) -> list:
        """Identify areas of concern (scores < 60)"""
        
        scores = {
            'Safety': safety,
            'Affordability': affordability,
            'Environment': environment,
            'Lifestyle': lifestyle,
            'Convenience': convenience
        }
        
        concerns = [
            {'area': name, 'score': score}
            for name, score in scores.items()
            if score < 60
        ]
        
        # Sort by score (lowest first)
        concerns.sort(key=lambda x: x['score'])
        
        return concerns
    
    def _generate_overall_recommendation(
        self,
        overall_score: float,
        safety_score: float,
        affordability_score: float,
        environment_score: float
    ) -> str:
        """Generate overall move recommendation"""
        
        # Critical factors: safety and affordability
        critical_threshold = 50
        
        if safety_score < critical_threshold:
            return "⚠️ Proceed with caution. Safety scores are concerning. Consider visiting the area and researching crime patterns before committing."
        
        if affordability_score < critical_threshold:
            return "⚠️ Financial concern. This move may strain your budget significantly. Ensure you have adequate income or savings."
        
        if overall_score >= 85:
            return "✅ Highly recommended! This location scores well across all factors and appears to be an excellent fit."
        elif overall_score >= 75:
            return "✅ Recommended. This is a solid choice with strong performance in key areas."
        elif overall_score >= 65:
            return "👍 Good option. This location has both strengths and some trade-offs to consider."
        elif overall_score >= 55:
            return "⚖️ Mixed results. Carefully weigh the pros and cons based on your priorities."
        else:
            return "⚠️ Consider alternatives. This location has several concerning factors that may impact your quality of life."
    
    def calculate_comparison_delta(
        self,
        current_scores: Dict[str, float],
        destination_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate the delta between current and destination scores"""
        
        deltas = {}
        
        for category in current_scores:
            current = current_scores[category]
            destination = destination_scores[category]
            delta = destination - current
            
            deltas[category] = {
                'current': round(current, 1),
                'destination': round(destination, 1),
                'change': round(delta, 1),
                'direction': 'improving' if delta > 5 else 'declining' if delta < -5 else 'stable',
                'percent_change': round((delta / current * 100), 1) if current > 0 else 0
            }
        
        return deltas


# Global instance
scoring_service = ScoringService()