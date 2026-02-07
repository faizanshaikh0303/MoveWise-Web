import googlemaps
from app.core.config import settings
from typing import Dict, Any, List, Tuple, Optional


class PlacesService:
    def __init__(self):
        self.client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    
    # Mapping of hobbies to place types
    HOBBY_TO_PLACE_TYPE = {
        'gym': ['gym', 'fitness'],
        'fitness': ['gym', 'fitness'],
        'workout': ['gym', 'fitness'],
        'exercise': ['gym', 'fitness'],
        
        'hiking': ['park', 'nature'],
        'park': ['park'],
        'parks': ['park'],
        'nature': ['park'],
        'outdoor': ['park'],
        
        'restaurants': ['restaurant', 'food'],
        'restaurant': ['restaurant', 'food'],
        'dining': ['restaurant', 'food'],
        'food': ['restaurant', 'food'],
        'eating': ['restaurant', 'food'],
        
        'coffee': ['cafe', 'coffee'],
        'cafe': ['cafe', 'coffee'],
        'cafes': ['cafe', 'coffee'],
        
        'shopping': ['shopping_mall', 'stores'],
        'mall': ['shopping_mall', 'stores'],
        'stores': ['shopping_mall', 'stores'],
        
        'movies': ['movie_theater', 'entertainment'],
        'cinema': ['movie_theater', 'entertainment'],
        'theater': ['movie_theater', 'entertainment'],
        
        'bars': ['bar', 'nightlife'],
        'bar': ['bar', 'nightlife'],
        'nightlife': ['bar', 'nightlife'],
        'drinks': ['bar', 'nightlife'],
        
        'library': ['library', 'books'],
        'libraries': ['library', 'books'],
        'books': ['library', 'books'],
        'reading': ['library', 'books'],
        
        'sports': ['gym', 'park'],
        'basketball': ['park'],
        'tennis': ['park'],
        'soccer': ['park'],
        
        'music': ['bar', 'restaurant'],
        'concerts': ['bar', 'restaurant'],
        
        'art': ['museum', 'gallery'],
        'museums': ['museum', 'gallery'],
        'gallery': ['museum', 'gallery'],
    }
    
    # All available amenity types
    ALL_AMENITY_TYPES = {
        'grocery_or_supermarket': 'grocery stores',
        'gym': 'gyms',
        'restaurant': 'restaurants',
        'library': 'libraries',
        'park': 'parks',
        'cafe': 'cafes',
        'shopping_mall': 'shopping malls',
        'pharmacy': 'pharmacies',
        'hospital': 'hospitals',  # Note: May include clinics and medical centers
        'movie_theater': 'movie theaters',
        'bar': 'bars',
    }
    
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
    
    def get_amenity_types_from_hobbies(self, hobbies: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Filter amenity types based on user hobbies.
        If no hobbies provided, return all types.
        """
        if not hobbies:
            return self.ALL_AMENITY_TYPES
        
        # Collect relevant place types based on hobbies
        relevant_types = set()
        
        for hobby in hobbies:
            hobby_lower = hobby.lower().strip()
            
            # Check direct mapping
            if hobby_lower in self.HOBBY_TO_PLACE_TYPE:
                for place_type in self.HOBBY_TO_PLACE_TYPE[hobby_lower]:
                    relevant_types.add(place_type)
            
            # Check if hobby contains any keywords
            for keyword, place_types in self.HOBBY_TO_PLACE_TYPE.items():
                if keyword in hobby_lower or hobby_lower in keyword:
                    for place_type in place_types:
                        relevant_types.add(place_type)
        
        # Map back to actual Google Places types
        filtered_types = {}
        for place_type, display_name in self.ALL_AMENITY_TYPES.items():
            # Extract base type (e.g., 'grocery_or_supermarket' -> 'grocery')
            base_type = place_type.split('_')[0]
            
            # Check if this type matches any relevant types
            for relevant_type in relevant_types:
                if relevant_type in place_type or relevant_type in display_name.lower():
                    filtered_types[place_type] = display_name
                    break
        
        # Always include essentials regardless of hobbies
        essentials = ['grocery_or_supermarket', 'pharmacy', 'hospital']
        for essential in essentials:
            if essential in self.ALL_AMENITY_TYPES and essential not in filtered_types:
                filtered_types[essential] = self.ALL_AMENITY_TYPES[essential]
        
        return filtered_types if filtered_types else self.ALL_AMENITY_TYPES
    
    def get_nearby_amenities(
        self, 
        lat: float, 
        lng: float, 
        radius: int = 3219,  # 2 miles in meters
        hobbies: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Get count of nearby amenities within 2-mile radius.
        Filters by user hobbies if provided.
        
        Args:
            lat: Latitude
            lng: Longitude
            radius: Search radius in meters (default 3219m = 2 miles)
            hobbies: List of user hobbies to filter amenities
        """
        amenity_types = self.get_amenity_types_from_hobbies(hobbies)
        
        results = {}
        
        for place_type, display_name in amenity_types.items():
            try:
                response = self.client.places_nearby(
                    location=(lat, lng),
                    radius=radius,
                    type=place_type
                )
                places = response.get('results', [])
                
                # Apply stricter filtering for all types to get accurate counts
                if place_type == 'hospital':
                    # Only count actual hospitals and major medical centers
                    places = [p for p in places if 
                             'hospital' in p.get('name', '').lower() or
                             'medical center' in p.get('name', '').lower() or
                             'emergency' in p.get('name', '').lower()]
                
                elif place_type == 'pharmacy':
                    # Only count actual pharmacies/drugstores
                    places = [p for p in places if
                             any(chain in p.get('name', '').lower() for chain in 
                                 ['cvs', 'walgreens', 'rite aid', 'pharmacy', 'drugstore', 
                                  'medicine', 'chemist', 'walmart', 'target', 'kroger', 'publix'])]
                
                elif place_type == 'grocery_or_supermarket':
                    # Only major grocery stores, exclude convenience stores
                    places = [p for p in places if
                             any(chain in p.get('name', '').lower() for chain in
                                 ['kroger', 'publix', 'whole foods', 'trader joe', 'safeway',
                                  'albertsons', 'food lion', 'giant', 'stop & shop', 'wegmans',
                                  'heb', 'meijer', 'aldi', 'lidl', 'costco', 'sam\'s club',
                                  'target', 'walmart', 'market', 'supermarket', 'grocery'])]
                
                elif place_type == 'restaurant':
                    # Exclude fast food chains to focus on sit-down restaurants
                    exclude_terms = ['mcdonald', 'burger king', 'wendy', 'taco bell', 
                                   'kfc', 'subway', 'pizza hut', 'domino']
                    places = [p for p in places if
                             not any(term in p.get('name', '').lower() for term in exclude_terms)]
                
                elif place_type == 'gym':
                    # Only actual gyms and fitness centers
                    places = [p for p in places if
                             any(term in p.get('name', '').lower() for term in
                                 ['gym', 'fitness', 'workout', 'planet fitness', 'la fitness',
                                  '24 hour', 'anytime fitness', 'ymca', 'crossfit', 'yoga', 
                                  'pilates', 'barre', 'orangetheory', 'f45'])]
                
                elif place_type == 'cafe':
                    # Coffee shops and cafes
                    places = [p for p in places if
                             any(term in p.get('name', '').lower() for term in
                                 ['coffee', 'cafe', 'starbucks', 'dunkin', 'peet', 'caribou',
                                  'espresso', 'roaster', 'brew'])]
                
                elif place_type == 'bar':
                    # Only actual bars and pubs
                    places = [p for p in places if
                             any(term in p.get('name', '').lower() for term in
                                 ['bar', 'pub', 'tavern', 'brewery', 'lounge', 'taproom',
                                  'saloon', 'ale house', 'sports bar'])]
                
                elif place_type == 'park':
                    # Count parks but exclude tiny playgrounds
                    places = [p for p in places if
                             'park' in p.get('name', '').lower() or
                             'garden' in p.get('name', '').lower() or
                             'trail' in p.get('name', '').lower() or
                             'recreation' in p.get('name', '').lower()]
                
                elif place_type == 'library':
                    # Only count actual public/community libraries
                    places = [p for p in places if
                             'library' in p.get('name', '').lower() or
                             'branch' in p.get('name', '').lower()]
                
                elif place_type == 'movie_theater':
                    # Only count movie theaters/cinemas
                    places = [p for p in places if
                             any(term in p.get('name', '').lower() for term in
                                 ['cinema', 'theater', 'theatre', 'amc', 'regal',
                                  'cinemark', 'movie', 'imax', 'film', 'showcase'])]
                
                elif place_type == 'shopping_mall':
                    # Only count actual malls and shopping centers
                    places = [p for p in places if
                             any(term in p.get('name', '').lower() for term in
                                 ['mall', 'plaza', 'center', 'shopping', 'galleria',
                                  'market', 'square', 'village', 'outlet'])]
                
                count = len(places)
                results[display_name] = count
            except Exception as e:
                print(f"Error fetching {place_type}: {e}")
                results[display_name] = 0
        
        return results
    
    def compare_amenities(
        self,
        current_lat: float,
        current_lng: float,
        destination_lat: float,
        destination_lng: float,
        hobbies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare amenities between two locations within 1-mile radius.
        Filters by user hobbies if provided.
        """
        
        current_amenities = self.get_nearby_amenities(current_lat, current_lng, hobbies=hobbies)
        destination_amenities = self.get_nearby_amenities(destination_lat, destination_lng, hobbies=hobbies)
        
        # Calculate total amenities
        current_total = sum(current_amenities.values())
        destination_total = sum(destination_amenities.values())
        
        # Generate comparison text
        if destination_total > current_total:
            percentage_diff = ((destination_total - current_total) / current_total * 100) if current_total > 0 else 100
            comparison_text = f"Within 2 miles, the new area offers {percentage_diff:.0f}% more amenities"
            
            # Find specific improvements
            improvements = []
            for amenity, count in destination_amenities.items():
                if count > current_amenities.get(amenity, 0):
                    improvements.append(amenity)
            
            if improvements:
                comparison_text += f", particularly better options for {' and '.join(improvements[:3])}."
            else:
                comparison_text += "."
                
        elif destination_total < current_total:
            percentage_diff = ((current_total - destination_total) / current_total * 100)
            comparison_text = f"Within 2 miles, the new area has {percentage_diff:.0f}% fewer amenities overall."
        else:
            comparison_text = "Within 2 miles, both areas offer similar amenity access."
        
        return {
            'current_amenities': current_amenities,
            'destination_amenities': destination_amenities,
            'comparison_text': comparison_text,
            'search_radius': '2 miles',
            'note': 'Filtered for major facilities only (e.g., actual hospitals, not clinics). More accurate counts.'
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


# Create singleton instance
places_service = PlacesService()