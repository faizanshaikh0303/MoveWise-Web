import googlemaps
from app.core.config import settings
from typing import Dict, Any, List, Tuple


class PlacesService:
    def __init__(self):
        self.client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    
    def geocode_address(self, address: str) -> Tuple[float, float]:
        """Convert address to lat/lng coordinates"""
        try:
            result = self.client.geocode(address)
            if result:
                location = result[0]['geometry']['location']
                return location['lat'], location['lng']
            return None, None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None, None
    
    def get_nearby_amenities(self, lat: float, lng: float, radius: int = 8047) -> Dict[str, int]:
        """
        Get count of nearby amenities within radius (default 5 miles = 8047 meters)
        """
        amenity_types = {
            'grocery_or_supermarket': 'grocery stores',
            'gym': 'gyms',
            'restaurant': 'restaurants',
            'library': 'libraries',
            'park': 'parks',
            'cafe': 'cafes',
            'shopping_mall': 'shopping malls',
            'hospital': 'hospitals',
            'pharmacy': 'pharmacies',
            'school': 'schools',
            'movie_theater': 'movie theaters',
            'bar': 'bars',
            'gas_station': 'gas stations',
            'bank': 'banks'
        }
        
        results = {}
        
        for place_type, display_name in amenity_types.items():
            try:
                response = self.client.places_nearby(
                    location=(lat, lng),
                    radius=radius,
                    type=place_type
                )
                results[display_name] = len(response.get('results', []))
            except Exception as e:
                print(f"Error fetching {place_type}: {e}")
                results[display_name] = 0
        
        return results
    
    def compare_amenities(
        self,
        current_lat: float,
        current_lng: float,
        destination_lat: float,
        destination_lng: float
    ) -> Dict[str, Any]:
        """Compare amenities between two locations"""
        
        current_amenities = self.get_nearby_amenities(current_lat, current_lng)
        destination_amenities = self.get_nearby_amenities(destination_lat, destination_lng)
        
        # Calculate total amenities
        current_total = sum(current_amenities.values())
        destination_total = sum(destination_amenities.values())
        
        # Generate comparison text
        if destination_total > current_total:
            percentage_diff = ((destination_total - current_total) / current_total * 100) if current_total > 0 else 100
            comparison_text = f"The new area offers {percentage_diff:.0f}% more amenities"
            
            # Find specific improvements
            improvements = []
            for amenity, count in destination_amenities.items():
                if count > current_amenities.get(amenity, 0):
                    improvements.append(amenity)
            
            if improvements:
                comparison_text += f", particularly better options for {' and '.join(improvements[:3])}."
        elif destination_total < current_total:
            percentage_diff = ((current_total - destination_total) / current_total * 100)
            comparison_text = f"The new area has {percentage_diff:.0f}% fewer amenities overall."
        else:
            comparison_text = "Both areas offer similar amenity access."
        
        return {
            'current_amenities': current_amenities,
            'destination_amenities': destination_amenities,
            'comparison_text': comparison_text
        }
    
    def get_commute_info(
        self,
        origin_lat: float,
        origin_lng: float,
        work_address: str,
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """Get commute information from new location to work"""
        
        try:
            result = self.client.distance_matrix(
                origins=[(origin_lat, origin_lng)],
                destinations=[work_address],
                mode=mode,
                departure_time="now"
            )
            
            if result['rows'][0]['elements'][0]['status'] == 'OK':
                duration = result['rows'][0]['elements'][0]['duration']['value'] // 60  # Convert to minutes
                distance = result['rows'][0]['elements'][0]['distance']['text']
                
                return {
                    'duration_minutes': duration,
                    'method': mode,
                    'distance': distance,
                    'description': f"Your commute will be approximately {duration} minutes by {mode}."
                }
        except Exception as e:
            print(f"Commute calculation error: {e}")
        
        return {
            'duration_minutes': None,
            'method': mode,
            'description': "Commute information unavailable."
        }


places_service = PlacesService()