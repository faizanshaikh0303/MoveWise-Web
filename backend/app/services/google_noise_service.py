import requests
from typing import Dict, Any, Optional
from app.core.config import settings


class GoogleNoiseService:
    """
    Calculate noise levels using Google Maps Places API
    Much more reliable than OSM Overpass API
    """
    
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    def analyze_noise_level(
        self,
        latitude: float,
        longitude: float,
        user_preference: str = 'moderate'
    ) -> Dict[str, Any]:
        """
        Analyze noise level based on nearby places
        Uses Google Places API to find noise sources
        """
        
        try:
            # Search for noise-generating places
            noise_sources = self._find_noise_sources(latitude, longitude)
            
            # Calculate noise score
            noise_score = self._calculate_noise_score(noise_sources, user_preference)
            
            return {
                'estimated_db': noise_score['db_level'],
                'noise_category': noise_score['category'],
                'noise_score': noise_score['score'],
                'noise_sources': noise_sources,
                'data_source': 'Google Places API',
                'preference_match': self._check_preference_match(
                    noise_score['category'],
                    user_preference
                )
            }
            
        except Exception as e:
            print(f"Google noise service error: {e}")
            return self._get_fallback_noise()
    
    def _find_noise_sources(self, lat: float, lon: float) -> Dict[str, int]:
        """Find nearby noise-generating places"""
        
        noise_source_types = {
            'airport': 90,  # Very loud
            'highway': 75,  # Loud
            'train_station': 70,
            'bus_station': 65,
            'bar': 70,
            'night_club': 80,
            'restaurant': 60,
            'shopping_mall': 65,
            'school': 60,
            'hospital': 55,
            'park': 40  # Quiet
        }
        
        found_sources = {}
        total_noise_contribution = 0
        
        for place_type, base_noise in noise_source_types.items():
            try:
                params = {
                    'location': f'{lat},{lon}',
                    'radius': 1000,  # 1km radius
                    'type': place_type,
                    'key': self.api_key
                }
                
                response = requests.get(self.places_url, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    count = len(results)
                    
                    if count > 0:
                        found_sources[place_type] = count
                        
                        # Closer and more places = more noise
                        for place in results[:3]:  # Check top 3 closest
                            # Calculate distance-based contribution
                            # (simplified - not using actual distance)
                            total_noise_contribution += base_noise * 0.1
                
            except Exception as e:
                print(f"Error checking {place_type}: {e}")
                continue
        
        return {
            'sources': found_sources,
            'total_contribution': total_noise_contribution,
            'dominant_source': max(found_sources.items(), key=lambda x: x[1])[0] if found_sources else 'none'
        }
    
    def _calculate_noise_score(self, noise_sources: Dict, preference: str) -> Dict[str, Any]:
        """Calculate noise level and score"""
        
        contribution = noise_sources.get('total_contribution', 0)
        
        # Base noise (ambient)
        base_db = 35
        
        # Add contributions from sources
        estimated_db = base_db + min(contribution, 50)
        
        # Categorize
        if estimated_db < 45:
            category = 'Very Quiet'
            score = 95
        elif estimated_db < 55:
            category = 'Quiet'
            score = 85
        elif estimated_db < 65:
            category = 'Moderate'
            score = 70
        elif estimated_db < 75:
            category = 'Noisy'
            score = 50
        else:
            category = 'Very Noisy'
            score = 30
        
        # Adjust score based on user preference
        if preference == 'quiet' and category in ['Very Quiet', 'Quiet']:
            score += 5
        elif preference == 'moderate' and category == 'Moderate':
            score += 5
        elif preference == 'lively' and category in ['Noisy', 'Very Noisy']:
            score += 5
        
        return {
            'db_level': round(estimated_db, 1),
            'category': category,
            'score': min(score, 100)
        }
    
    def _check_preference_match(self, category: str, preference: str) -> Dict:
        """Check if noise level matches user preference"""
        
        matches = {
            'quiet': ['Very Quiet', 'Quiet'],
            'moderate': ['Quiet', 'Moderate', 'Noisy'],
            'lively': ['Moderate', 'Noisy', 'Very Noisy']
        }
        
        is_match = category in matches.get(preference, [])
        
        return {
            'is_good_match': is_match,
            'quality': 'excellent' if is_match else 'poor'
        }
    
    def _get_fallback_noise(self) -> Dict:
        """Fallback noise data"""
        return {
            'estimated_db': 50.0,
            'noise_category': 'Moderate',
            'noise_score': 70.0,
            'noise_sources': {'sources': {}, 'total_contribution': 0},
            'data_source': 'Estimate',
            'preference_match': {'is_good_match': True, 'quality': 'good'}
        }
    
    def compare_noise_levels(
        self,
        current_lat: float,
        current_lon: float,
        dest_lat: float,
        dest_lon: float,
        user_preference: str = 'moderate'
    ) -> Dict[str, Any]:
        """Compare noise between two locations"""
        
        current = self.analyze_noise_level(current_lat, current_lon, user_preference)
        destination = self.analyze_noise_level(dest_lat, dest_lon, user_preference)
        
        db_diff = destination['estimated_db'] - current['estimated_db']
        
        return {
            'current': current,
            'destination': destination,
            'comparison': {
                'db_difference': round(db_diff, 1),
                'is_quieter': db_diff < 0,
                'category_change': f"{current['noise_category']} → {destination['noise_category']}"
            }
        }


# Global instance
google_noise_service = GoogleNoiseService()