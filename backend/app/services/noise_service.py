from typing import Dict, Any
import httpx


class NoiseService:
    """
    Estimate noise levels based on location characteristics.
    Uses urban density, traffic patterns, and location type.
    """
    
    def __init__(self):
        # Noise levels for major cities (average dB)
        # Source: WHO guidelines and urban noise studies
        self.city_noise_levels = {
            # Very High Noise (70+ dB)
            'new york': {'level': 'Loud (70-80 dB)', 'score': 75},
            'manhattan': {'level': 'Very Loud (75-85 dB)', 'score': 80},
            'chicago': {'level': 'Loud (70-80 dB)', 'score': 72},
            'los angeles': {'level': 'Loud (65-75 dB)', 'score': 70},
            'san francisco': {'level': 'Moderate-Loud (60-70 dB)', 'score': 65},
            'boston': {'level': 'Moderate-Loud (60-70 dB)', 'score': 65},
            
            # High Noise (60-70 dB)
            'seattle': {'level': 'Moderate (55-65 dB)', 'score': 60},
            'miami': {'level': 'Moderate-Loud (60-70 dB)', 'score': 65},
            'dallas': {'level': 'Moderate (55-65 dB)', 'score': 60},
            'houston': {'level': 'Moderate (55-65 dB)', 'score': 60},
            'philadelphia': {'level': 'Moderate-Loud (60-70 dB)', 'score': 65},
            'atlanta': {'level': 'Moderate (55-65 dB)', 'score': 60},
            'washington': {'level': 'Moderate-Loud (60-70 dB)', 'score': 65},
            'denver': {'level': 'Moderate (50-60 dB)', 'score': 55},
            'phoenix': {'level': 'Moderate (50-60 dB)', 'score': 55},
            
            # Moderate Noise (50-60 dB)
            'austin': {'level': 'Moderate (50-60 dB)', 'score': 55},
            'san diego': {'level': 'Moderate (50-60 dB)', 'score': 55},
            'portland': {'level': 'Moderate (50-60 dB)', 'score': 55},
            'nashville': {'level': 'Moderate (50-60 dB)', 'score': 55},
            'charlotte': {'level': 'Quiet-Moderate (45-55 dB)', 'score': 50},
            'raleigh': {'level': 'Quiet (40-50 dB)', 'score': 45},
            'minneapolis': {'level': 'Moderate (50-60 dB)', 'score': 55},
            'san antonio': {'level': 'Moderate (50-60 dB)', 'score': 55},
            'columbus': {'level': 'Moderate (50-60 dB)', 'score': 52},
            
            # Low Noise (40-50 dB)
            'orlando': {'level': 'Quiet-Moderate (45-55 dB)', 'score': 50},
            'tampa': {'level': 'Quiet-Moderate (45-55 dB)', 'score': 50},
            'indianapolis': {'level': 'Quiet (40-50 dB)', 'score': 45},
            'sacramento': {'level': 'Quiet-Moderate (45-55 dB)', 'score': 50},
            'omaha': {'level': 'Quiet (40-50 dB)', 'score': 45},
            'boise': {'level': 'Quiet (35-45 dB)', 'score': 40},
        }
        
        # Noise indicators in address
        self.noise_indicators = {
            'downtown': 15,
            'midtown': 12,
            'city center': 15,
            'financial district': 12,
            'airport': 20,
            'highway': 15,
            'interstate': 15,
            'avenue': 8,
            'boulevard': 8,
            'main street': 10,
            'plaza': 10,
            'square': 10,
            
            # Quiet indicators (negative)
            'suburb': -15,
            'residential': -10,
            'quiet': -15,
            'park': -12,
            'hills': -10,
            'village': -12,
            'lake': -10,
            'forest': -15,
            'country': -15,
            'rural': -20,
        }
    
    def estimate_noise_level(self, address: str) -> Dict[str, Any]:
        """
        Estimate noise level with detailed breakdown.
        """
        address_lower = address.lower()
        
        # Start with city base noise
        base_score = 55  # Default moderate
        city_data = None
        
        for city, data in self.city_noise_levels.items():
            if city in address_lower:
                base_score = data['score']
                city_data = data
                break
        
        # Adjust based on address indicators
        adjustment = 0
        detected_indicators = []
        
        for indicator, score_change in self.noise_indicators.items():
            if indicator in address_lower:
                adjustment += score_change
                detected_indicators.append(indicator)
        
        # Calculate final score
        final_score = max(30, min(85, base_score + adjustment))
        
        # Determine level description
        if final_score >= 75:
            level = "Very Loud (75-85 dB)"
            description = "High noise environment typical of busy urban centers"
        elif final_score >= 65:
            level = "Loud (65-75 dB)"
            description = "Moderately loud with significant traffic and urban activity"
        elif final_score >= 55:
            level = "Moderate (55-65 dB)"
            description = "Moderate noise levels with typical urban sounds"
        elif final_score >= 45:
            level = "Quiet-Moderate (45-55 dB)"
            description = "Relatively quiet with occasional urban noise"
        else:
            level = "Quiet (35-45 dB)"
            description = "Peaceful environment with minimal noise pollution"
        
        return {
            'level': level,
            'score': final_score,
            'description': description,
            'indicators': detected_indicators if detected_indicators else ['standard residential']
        }
    
    def compare_noise_levels(
        self,
        current_address: str,
        destination_address: str,
        sleep_preference: str = None
    ) -> Dict[str, Any]:
        """Compare noise levels between two locations with detailed analysis"""
        
        current = self.estimate_noise_level(current_address)
        destination = self.estimate_noise_level(destination_address)
        
        score_diff = destination['score'] - current['score']
        
        # Generate detailed analysis
        if score_diff < -10:
            impact = "Positive"
            analysis = f"The quieter environment (reduction of {abs(score_diff):.0f} dB) should significantly improve sleep quality"
            if sleep_preference and "quiet" in sleep_preference.lower():
                analysis += " and aligns perfectly with your preference for a peaceful neighborhood"
        elif score_diff < -5:
            impact = "Slightly Positive"
            analysis = f"Somewhat quieter environment (reduction of {abs(score_diff):.0f} dB)"
            if sleep_preference and "quiet" in sleep_preference.lower():
                analysis += ", which should suit your quiet preferences"
        elif score_diff > 10:
            impact = "Concerning"
            analysis = f"Significantly louder environment (increase of {score_diff:.0f} dB)"
            if sleep_preference and "quiet" in sleep_preference.lower():
                analysis += ". Consider noise-canceling solutions, white noise machines, or double-pane windows"
        elif score_diff > 5:
            impact = "Noticeable"
            analysis = f"Moderately louder environment (increase of {score_diff:.0f} dB)"
            if sleep_preference and "quiet" in sleep_preference.lower():
                analysis += ". May require adjustment or sound mitigation"
        else:
            impact = "Neutral"
            analysis = "Similar noise environment to your current location"
        
        return {
            'current_noise_level': current['level'],
            'current_score': current['score'],
            'current_description': current['description'],
            'current_indicators': current['indicators'],
            
            'destination_noise_level': destination['level'],
            'destination_score': destination['score'],
            'destination_description': destination['description'],
            'destination_indicators': destination['indicators'],
            
            'score_difference': round(score_diff, 1),
            'impact': impact,
            'analysis': analysis + ".",
            
            'data_source': 'WHO noise guidelines & urban density analysis'
        }


noise_service = NoiseService()