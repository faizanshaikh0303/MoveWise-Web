from typing import Dict, Any
import httpx


class NoiseService:
    """
    Estimate noise levels based on location characteristics.
    Uses urban density, traffic patterns, and location type.
    NOW WITH PREFERENCE-AWARE SCORING!
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
    
    def categorize_noise_by_db(self, db_score: float) -> str:
        """Convert dB score to category"""
        if db_score >= 75:
            return "Very Noisy"
        elif db_score >= 65:
            return "Noisy"
        elif db_score >= 55:
            return "Moderate"
        elif db_score >= 45:
            return "Quiet"
        else:
            return "Very Quiet"
    
    def calculate_preference_score(
        self,
        db_score: float,
        noise_category: str,
        user_preference: str = "moderate"
    ) -> float:
        """
        Calculate noise score based on user preference
        
        Args:
            db_score: Raw noise level (30-85 dB)
            noise_category: Category (Very Quiet, Quiet, Moderate, Noisy, Very Noisy)
            user_preference: User's noise preference (quiet, moderate, lively)
            
        Returns:
            Score from 0-100 based on preference match
        """
        
        # Map categories to scores for each preference type
        preference_scores = {
            'quiet': {
                'Very Quiet': 100,  # Perfect for quiet lovers
                'Quiet': 90,        # Great
                'Moderate': 60,     # Acceptable
                'Noisy': 30,        # Poor
                'Very Noisy': 10    # Very bad
            },
            'moderate': {
                'Very Quiet': 70,   # Too quiet
                'Quiet': 85,        # Good
                'Moderate': 100,    # Perfect match
                'Noisy': 85,        # Still good
                'Very Noisy': 50    # Getting too loud
            },
            'lively': {
                'Very Quiet': 40,   # Way too quiet
                'Quiet': 60,        # Still too quiet
                'Moderate': 80,     # Getting there
                'Noisy': 95,        # Great! Love the energy
                'Very Noisy': 100   # Perfect! Vibrant atmosphere
            }
        }
        
        # Normalize preference
        pref = user_preference.lower() if user_preference else 'moderate'
        if pref not in preference_scores:
            pref = 'moderate'
        
        # Get base score from preference match
        base_score = preference_scores[pref].get(noise_category, 50)
        
        print(f"   🔊 Noise scoring: {noise_category} ({db_score:.1f} dB) + '{pref}' preference = {base_score}/100")
        
        return float(base_score)
    
    def estimate_noise_level(
        self,
        address: str,
        user_preference: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Estimate noise level with preference-aware scoring.
        
        Args:
            address: Location address
            user_preference: User's noise preference (quiet, moderate, lively)
        """
        address_lower = address.lower()
        
        # Start with city base noise
        base_score = 55  # Default moderate dB
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
        
        # Calculate final dB level
        final_db = max(30, min(85, base_score + adjustment))
        
        # Categorize the noise level
        noise_category = self.categorize_noise_by_db(final_db)
        
        # Calculate preference-aware score (0-100)
        preference_score = self.calculate_preference_score(
            final_db,
            noise_category,
            user_preference
        )
        
        # Determine level description
        if final_db >= 75:
            level = "Very Loud (75-85 dB)"
            description = "High noise environment typical of busy urban centers"
        elif final_db >= 65:
            level = "Loud (65-75 dB)"
            description = "Moderately loud with significant traffic and urban activity"
        elif final_db >= 55:
            level = "Moderate (55-65 dB)"
            description = "Moderate noise levels with typical urban sounds"
        elif final_db >= 45:
            level = "Quiet-Moderate (45-55 dB)"
            description = "Relatively quiet with occasional urban noise"
        else:
            level = "Quiet (35-45 dB)"
            description = "Peaceful environment with minimal noise pollution"
        
        # Check if it matches user preference
        preference_match = self._check_preference_match(noise_category, user_preference)
        
        return {
            'level': level,
            'score': final_db,  # Raw dB score for comparison
            'noise_score': preference_score,  # NEW: Preference-aware score for overall rating
            'noise_category': noise_category,  # NEW: Category for frontend
            'description': description,
            'indicators': detected_indicators if detected_indicators else ['standard residential'],
            'preference_match': preference_match  # NEW: Does it match user's preference?
        }
    
    def _check_preference_match(
        self,
        noise_category: str,
        user_preference: str
    ) -> Dict[str, Any]:
        """Check if noise matches user preference"""
        
        pref = user_preference.lower() if user_preference else 'moderate'
        
        # Define what's a good match for each preference
        good_matches = {
            'quiet': ['Very Quiet', 'Quiet'],
            'moderate': ['Quiet', 'Moderate', 'Noisy'],
            'lively': ['Moderate', 'Noisy', 'Very Noisy']
        }
        
        is_match = noise_category in good_matches.get(pref, [])
        
        quality_map = {
            'quiet': 'peaceful',
            'moderate': 'balanced',
            'lively': 'vibrant'
        }
        
        return {
            'is_good_match': is_match,
            'quality': quality_map.get(pref, 'balanced')
        }
    
    def compare_noise_levels(
        self,
        current_address: str,
        destination_address: str,
        sleep_preference: str = None,
        user_preference: str = "moderate"  # NEW PARAMETER
    ) -> Dict[str, Any]:
        """
        Compare noise levels between two locations with preference-aware analysis
        
        Args:
            current_address: Current location address
            destination_address: Destination location address
            sleep_preference: Sleep preferences (legacy, kept for compatibility)
            user_preference: Noise preference (quiet, moderate, lively)
        """
        
        # Get noise data for both locations WITH preference
        current = self.estimate_noise_level(current_address, user_preference)
        destination = self.estimate_noise_level(destination_address, user_preference)
        
        # dB difference (raw noise level)
        db_diff = destination['score'] - current['score']
        
        # Score difference (preference-aware)
        score_diff = destination['noise_score'] - current['noise_score']
        
        # Generate analysis based on PREFERENCE and dB change
        pref = user_preference.lower() if user_preference else 'moderate'
        
        if pref == 'lively':
            # For lively preference, louder can be GOOD
            if db_diff > 10:
                impact = "Positive"
                analysis = f"Much livelier environment (increase of {db_diff:.0f} dB) - perfect for your vibrant lifestyle preference"
            elif db_diff > 5:
                impact = "Slightly Positive"
                analysis = f"Slightly more energetic environment (increase of {db_diff:.0f} dB)"
            elif db_diff < -10:
                impact = "Concerning"
                analysis = f"Significantly quieter environment (reduction of {abs(db_diff):.0f} dB) - may feel too calm for your preference"
            elif db_diff < -5:
                impact = "Noticeable"
                analysis = f"Somewhat quieter environment (reduction of {abs(db_diff):.0f} dB)"
            else:
                impact = "Neutral"
                analysis = "Similar noise environment to your current location"
        
        elif pref == 'quiet':
            # For quiet preference, quieter is GOOD
            if db_diff < -10:
                impact = "Positive"
                analysis = f"The quieter environment (reduction of {abs(db_diff):.0f} dB) should significantly improve tranquility and aligns with your quiet preference"
            elif db_diff < -5:
                impact = "Slightly Positive"
                analysis = f"Somewhat quieter environment (reduction of {abs(db_diff):.0f} dB), which suits your quiet preferences"
            elif db_diff > 10:
                impact = "Concerning"
                analysis = f"Significantly louder environment (increase of {db_diff:.0f} dB). Consider noise-canceling solutions or sound mitigation"
            elif db_diff > 5:
                impact = "Noticeable"
                analysis = f"Moderately louder environment (increase of {db_diff:.0f} dB). May require adjustment"
            else:
                impact = "Neutral"
                analysis = "Similar noise environment to your current location"
        
        else:  # moderate
            # For moderate preference, big changes either way are notable
            if abs(db_diff) > 10:
                if db_diff > 0:
                    impact = "Noticeable"
                    analysis = f"Significantly louder environment (increase of {db_diff:.0f} dB)"
                else:
                    impact = "Noticeable"
                    analysis = f"Significantly quieter environment (reduction of {abs(db_diff):.0f} dB)"
            elif abs(db_diff) > 5:
                if db_diff > 0:
                    impact = "Slightly Noticeable"
                    analysis = f"Somewhat louder environment (increase of {db_diff:.0f} dB)"
                else:
                    impact = "Slightly Noticeable"
                    analysis = f"Somewhat quieter environment (reduction of {abs(db_diff):.0f} dB)"
            else:
                impact = "Neutral"
                analysis = "Similar noise environment to your current location"
        
        return {
            'current_noise_level': current['level'],
            'current_score': current['score'],  # Raw dB
            'current_noise_score': current['noise_score'],  # Preference-aware score
            'current_description': current['description'],
            'current_indicators': current['indicators'],
            'current_category': current['noise_category'],
            
            'destination_noise_level': destination['level'],
            'destination_score': destination['score'],  # Raw dB
            'destination_noise_score': destination['noise_score'],  # Preference-aware score
            'destination_description': destination['description'],
            'destination_indicators': destination['indicators'],
            'destination_category': destination['noise_category'],
            'destination_preference_match': destination['preference_match'],
            
            'score_difference': round(score_diff, 1),  # Preference-aware difference
            'db_difference': round(db_diff, 1),  # Raw dB difference
            'impact': impact,
            'analysis': analysis + ".",
            
            'data_source': 'WHO noise guidelines & urban density analysis'
        }


noise_service = NoiseService()