from typing import Dict, Any, Optional


class ScoringService:
    """
    Comprehensive scoring system for location analysis
    Calculates weighted scores based on multiple data sources
    """
    
    # Score weights (must sum to 1.0)
    WEIGHTS = {
        'safety': 0.25,        # Crime data (25%)
        'affordability': 0.25, # Cost of living (25%)
        'environment': 0.20,   # Noise levels (20%)
        'lifestyle': 0.15,     # Amenities (15%)
        'convenience': 0.15    # Commute (15%)
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
        
        # Extract individual scores (lifestyle and convenience are pre-computed by their services)
        safety_score = crime_data.get('destination', {}).get('safety_score', 70)
        affordability_score = cost_data.get('destination', {}).get('affordability_score', 70)
        environment_score = noise_data.get('destination', {}).get('noise_score', 70)
        lifestyle_score = amenities_data.get('lifestyle_score', 70) if amenities_data else 70
        convenience_score = commute_data.get('convenience_score', 70) if commute_data else 70
        
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
    


# Global instance
scoring_service = ScoringService()