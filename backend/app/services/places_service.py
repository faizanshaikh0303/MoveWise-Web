import googlemaps
from typing import Dict, Any, Optional, Tuple
from app.core.config import settings


class PlacesService:
    """Service for Google Places API operations"""
    
    def __init__(self):
        self.client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to coordinates"""
        try:
            result = self.client.geocode(address)
            if result:
                location = result[0]['geometry']['location']
                return location['lat'], location['lng']
            return None, None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None, None
    
    def get_nearby_amenities(self, lat: float, lng: float, radius: int = 1609, hobbies: list = None) -> Dict[str, int]:
        """
        Get count of nearby amenities within 1 mile radius
        
        Args:
            lat: Latitude
            lng: Longitude  
            radius: Search radius in meters (default 1 mile = 1609m)
            hobbies: List of user hobbies (e.g., ['coffee', 'movies', 'shopping'])
        
        Returns:
            Dictionary with amenity counts (max 20 per category from Google API)
        """
        
        # Map hobbies to Google Places types
        hobby_to_place_type = {
            'coffee': ('cafe', 'cafes'),
            'cafes': ('cafe', 'cafes'),
            'movies': ('movie_theater', 'movie theaters'),
            'cinema': ('movie_theater', 'movie theaters'),
            'shopping': ('shopping_mall', 'shopping malls'),
            'gym': ('gym', 'gyms'),
            'fitness': ('gym', 'gyms'),
            'workout': ('gym', 'gyms'),
            'bars': ('bar', 'bars'),
            'nightlife': ('bar', 'bars'),
            'restaurants': ('restaurant', 'restaurants'),
            'dining': ('restaurant', 'restaurants'),
            'food': ('restaurant', 'restaurants'),
            'parks': ('park', 'parks'),
            'outdoors': ('park', 'parks'),
            'nature': ('park', 'parks'),
            'reading': ('library', 'libraries'),
            'books': ('library', 'libraries')
        }
        
        # Always include essentials
        essential_types = {
            'grocery_or_supermarket': 'grocery stores',
            'hospital': 'hospitals',
            'pharmacy': 'pharmacies'
        }
        
        # Build search list based on hobbies
        amenity_types = essential_types.copy()
        
        if hobbies:
            print(f"🔍 Searching amenities for hobbies: {hobbies}")
            for hobby in hobbies:
                hobby_lower = hobby.lower().strip()
                if hobby_lower in hobby_to_place_type:
                    place_type, display_name = hobby_to_place_type[hobby_lower]
                    amenity_types[place_type] = display_name
        else:
            print(f"ℹ️  No hobbies specified, using defaults")
            amenity_types.update({
                'restaurant': 'restaurants',
                'cafe': 'cafes',
                'park': 'parks'
            })
        
        print(f"   Searching within {radius}m (~{radius/1609:.1f} miles)")
        print(f"   Categories: {list(amenity_types.values())}")
        
        results = {}
        
        for place_type, display_name in amenity_types.items():
            try:
                # Simple API call - NO PAGINATION
                response = self.client.places_nearby(
                    location=(lat, lng),
                    radius=radius,
                    type=place_type
                )
                
                # Just count the results (max 20 from Google)
                result_count = len(response.get('results', []))
                results[display_name] = result_count
                
                # Log if we hit the cap
                if result_count == 20:
                    print(f"   ⚠️  {display_name}: 20 (API limit - may be more)")
                elif result_count > 0:
                    print(f"   ✓ {display_name}: {result_count}")
                
            except Exception as e:
                print(f"   ❌ Error fetching {display_name}: {e}")
                results[display_name] = 0
        
        return results
    
    def compare_amenities(
        self,
        current_lat: float,
        current_lng: float,
        destination_lat: float,
        destination_lng: float,
        hobbies: list = None
    ) -> Dict[str, Any]:
        """Compare amenities between two locations based on user hobbies"""
        
        # Check if locations are the same (within ~100 meters)
        from math import radians, cos, sin, asin, sqrt
        
        def haversine_distance(lat1, lon1, lat2, lon2):
            """Calculate distance in meters between two coordinates"""
            R = 6371000  # Earth radius in meters
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return R * c
        
        distance = haversine_distance(current_lat, current_lng, destination_lat, destination_lng)
        
        # If same location (within 100m), skip amenities search
        if distance < 100:
            print(f"ℹ️  Same location detected (distance: {distance:.0f}m), skipping amenities")
            return {
                'current_amenities': {},
                'destination_amenities': {},
                'destination': {'total_count': 0, 'by_type': {}},
                'current': {'total_count': 0, 'by_type': {}},
                'comparison_text': 'Same location - no comparison needed.',
                'same_location': True
            }
        
        # Different locations - search
        print(f"\n📍 Current location amenities:")
        current_amenities = self.get_nearby_amenities(current_lat, current_lng, hobbies=hobbies)
        
        print(f"\n📍 Destination location amenities:")
        destination_amenities = self.get_nearby_amenities(destination_lat, destination_lng, hobbies=hobbies)
        
        # Calculate totals
        current_total = sum(current_amenities.values())
        destination_total = sum(destination_amenities.values())
        
        print(f"\n🔍 Summary:")
        print(f"   Current: {current_total} total")
        print(f"   Destination: {destination_total} total")
        
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
                comparison_text += f", particularly {', '.join(improvements[:3])}."
        elif destination_total < current_total:
            percentage_diff = ((current_total - destination_total) / current_total * 100)
            comparison_text = f"The new area has {percentage_diff:.0f}% fewer amenities."
        else:
            comparison_text = "Both areas offer similar amenity access."
        
        return {
            'current_amenities': current_amenities,
            'destination_amenities': destination_amenities,
            'destination': {
                'total_count': destination_total,
                'by_type': destination_amenities
            },
            'current': {
                'total_count': current_total,
                'by_type': current_amenities
            },
            'comparison_text': comparison_text,
            'same_location': False
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
                duration = result['rows'][0]['elements'][0]['duration']['value'] // 60
                distance = result['rows'][0]['elements'][0]['distance']['text']
                
                return {
                    'duration_minutes': duration,
                    'distance': distance,
                    'mode': mode,
                    'description': f"Your commute will be approximately {duration} minutes by {mode}."
                }
        except Exception as e:
            print(f"Commute calculation error: {e}")
        
        return {
            'duration_minutes': None,
            'distance': 'Unknown',
            'mode': mode,
            'description': 'Unable to calculate commute time.'
        }


# Global instance
places_service = PlacesService()