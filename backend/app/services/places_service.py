import googlemaps
from typing import Dict, Any, Optional, Tuple, List
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
    
    def get_nearby_amenities_with_locations(
        self, 
        lat: float, 
        lng: float, 
        radius: int = 1609, 
        hobbies: list = None
    ) -> Tuple[Dict[str, int], Dict[str, List[Dict]]]:
        """
        Get count AND locations of nearby amenities within 1 mile radius
        
        Returns:
            Tuple of (counts_dict, locations_dict)
            - counts_dict: {category: count}
            - locations_dict: {category: [{"name": "", "lat": 0, "lng": 0, "address": ""}]}
        """
        
        # Map hobbies to Google Places search params.
        # Each entry: (search_method, value, display_name)
        # search_method is 'type' (exact place type) or 'keyword' (free-text search)
        hobby_to_place_type = {
            'coffee':      ('type',    'cafe',          'cafes'),
            'cafes':       ('type',    'cafe',          'cafes'),
            'movies':      ('type',    'movie_theater', 'movie theaters'),
            'cinema':      ('type',    'movie_theater', 'movie theaters'),
            'shopping':    ('type',    'shopping_mall', 'shopping malls'),
            'gym':         ('type',    'gym',           'gyms'),
            'fitness':     ('type',    'gym',           'gyms'),
            'workout':     ('type',    'gym',           'gyms'),
            'bars':        ('type',    'bar',           'bars'),
            'nightlife':   ('type',    'bar',           'bars'),
            'restaurants': ('type',    'restaurant',    'restaurants'),
            'dining':      ('type',    'restaurant',    'restaurants'),
            'food':        ('type',    'restaurant',    'restaurants'),
            'parks':       ('type',    'park',          'parks'),
            'outdoors':    ('type',    'park',          'parks'),
            'nature':      ('type',    'park',          'parks'),
            'library':     ('type',    'library',       'libraries'),
            'reading':     ('type',    'library',       'libraries'),
            'books':       ('type',    'library',       'libraries'),
            'hiking':      ('keyword', 'hiking trail',  'hiking trails'),
            'sports':      ('type',    'stadium',       'sports venues'),
        }

        # Always include essentials (all type-based)
        essential_tasks = [
            ('grocery stores', {'type': 'grocery_or_supermarket'}),
            ('hospitals',      {'type': 'hospital'}),
            ('pharmacies',     {'type': 'pharmacy'}),
            ('train stations', {'type': 'train_station'}),
            ('bus stations',   {'type': 'bus_station'}),
            ('airports',       {'type': 'airport'}),
        ]

        # Build ordered list of (display_name, search_params) to avoid duplicates
        seen_display_names = {t[0] for t in essential_tasks}
        hobby_tasks = []

        if hobbies:
            print(f"🔍 Searching amenities for hobbies: {hobbies}")
            for hobby in hobbies:
                hobby_lower = hobby.lower().strip()
                if hobby_lower in hobby_to_place_type:
                    method, value, display_name = hobby_to_place_type[hobby_lower]
                    if display_name not in seen_display_names:
                        seen_display_names.add(display_name)
                        if method == 'type':
                            hobby_tasks.append((display_name, {'type': value}))
                        else:
                            hobby_tasks.append((display_name, {'keyword': value}))
        else:
            print(f"ℹ️  No hobbies specified, using defaults")
            for display_name, params in [
                ('restaurants', {'type': 'restaurant'}),
                ('cafes',       {'type': 'cafe'}),
                ('parks',       {'type': 'park'}),
            ]:
                if display_name not in seen_display_names:
                    seen_display_names.add(display_name)
                    hobby_tasks.append((display_name, params))

        all_tasks = essential_tasks + hobby_tasks

        print(f"   Searching within {radius}m (~{radius/1609:.1f} miles)")
        print(f"   Categories: {[t[0] for t in all_tasks]}")

        counts = {}
        locations = {}

        for display_name, search_params in all_tasks:
            try:
                # Simple API call - NO PAGINATION
                response = self.client.places_nearby(
                    location=(lat, lng),
                    radius=radius,
                    **search_params
                )
                
                results = response.get('results', [])
                result_count = len(results)
                counts[display_name] = result_count

                # Store location data for mapping
                location_list = []
                for place in results:
                    location_list.append({
                        'name': place.get('name', 'Unknown'),
                        'lat': place['geometry']['location']['lat'],
                        'lng': place['geometry']['location']['lng'],
                        'address': place.get('vicinity', ''),
                        'type': display_name
                    })

                locations[display_name] = location_list

                # Log if we hit the cap
                if result_count == 20:
                    print(f"   ⚠️  {display_name}: 20 (API limit - may be more)")
                elif result_count > 0:
                    print(f"   ✓ {display_name}: {result_count}")
                else:
                    print(f"   — {display_name}: 0 (will be hidden)")

            except Exception as e:
                print(f"   ❌ Error fetching {display_name}: {e}")
                counts[display_name] = 0
                locations[display_name] = []

        # Drop categories with no results — they add no value to the UI
        counts    = {k: v for k, v in counts.items()    if v > 0}
        locations = {k: v for k, v in locations.items() if v}

        return counts, locations
    
    @staticmethod
    def _calculate_lifestyle_score(destination_counts: Dict[str, int]) -> float:
        total = sum(destination_counts.values())
        if total >= 50:
            base = 100.0
        elif total >= 30:
            base = 90.0
        elif total >= 20:
            base = 75.0
        elif total >= 10:
            base = 60.0
        elif total >= 5:
            base = 40.0
        else:
            base = 20.0
        variety_bonus = min(len(destination_counts) * 3, 15)
        return min(base + variety_bonus, 100.0)

    @staticmethod
    def _calculate_convenience_score(commute_data: Dict[str, Any]) -> float:
        if commute_data.get('method') == 'none' or commute_data.get('duration_minutes') == 0:
            return 100.0
        duration = commute_data.get('duration_minutes')
        if duration is None:
            return 70.0
        if duration <= 20:
            return 100.0
        elif duration <= 30:
            return round(90 - (duration - 20), 1)
        elif duration <= 45:
            return round(80 - (duration - 30) * 1.5, 1)
        elif duration <= 60:
            return round(60 - (duration - 45) * 2, 1)
        else:
            return round(max(20, 30 - (duration - 60) * 0.5), 1)

    def compare_amenities(
        self,
        current_lat: float,
        current_lng: float,
        destination_lat: float,
        destination_lng: float,
        hobbies: list = None
    ) -> Dict[str, Any]:
        """Compare amenities between two locations based on user hobbies"""
        
        # Check if locations are the same (within ~200 meters)
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
        
        # If same location (within 200m), skip amenities search
        if distance < 200:
            print(f"ℹ️  Same location detected (distance: {distance:.0f}m), skipping amenities")
            return {
                'current_amenities': {},
                'destination_amenities': {},
                'destination_locations': {},
                'destination_lat': destination_lat,
                'destination_lng': destination_lng,
                'current_lat': current_lat,
                'current_lng': current_lng,
                'destination': {'total_count': 0, 'by_type': {}},
                'current': {'total_count': 0, 'by_type': {}},
                'lifestyle_score': 10.0,
                'comparison_text': 'Same location - no comparison needed.',
                'same_location': True,
                'search_radius': '1 mile'
            }
        
        # Different locations - search with location data
        print(f"\n🔍 Current location amenities:")
        current_counts, _ = self.get_nearby_amenities_with_locations(
            current_lat, current_lng, hobbies=hobbies
        )
        
        print(f"\n🔍 Destination location amenities:")
        destination_counts, destination_locations = self.get_nearby_amenities_with_locations(
            destination_lat, destination_lng, hobbies=hobbies
        )
        
        # Calculate totals
        current_total = sum(current_counts.values())
        destination_total = sum(destination_counts.values())
        
        print(f"\n📊 Summary:")
        print(f"   Current: {current_total} total")
        print(f"   Destination: {destination_total} total")
        print(f"   Locations stored: {sum(len(v) for v in destination_locations.values())} places")
        
        # Generate comparison text
        if current_total == 0 and destination_total == 0:
            comparison_text = "No amenities found within 1 mile of either location."
        elif current_total == 0:
            improvements = list(destination_counts.keys())
            comparison_text = f"The new area has {destination_total} amenities nearby"
            if improvements:
                comparison_text += f", including {', '.join(improvements[:3])}."
            else:
                comparison_text += "."
        elif destination_total == 0:
            comparison_text = "No amenities found within 1 mile of the new location."
        elif destination_total > current_total:
            percentage_diff = (destination_total - current_total) / current_total * 100
            comparison_text = f"The new area offers {percentage_diff:.0f}% more amenities"
            improvements = [a for a, c in destination_counts.items() if c > current_counts.get(a, 0)]
            if improvements:
                comparison_text += f", particularly {', '.join(improvements[:3])}."
            else:
                comparison_text += "."
        elif destination_total < current_total:
            percentage_diff = (current_total - destination_total) / current_total * 100
            comparison_text = f"The new area has {percentage_diff:.0f}% fewer amenities."
        else:
            comparison_text = "Both areas offer similar amenity access."
        
        lifestyle_score = self._calculate_lifestyle_score(destination_counts)
        print(f"   Lifestyle score: {lifestyle_score}/100")

        return {
            'current_amenities': current_counts,
            'destination_amenities': destination_counts,
            'destination_locations': destination_locations,
            'destination_lat': destination_lat,
            'destination_lng': destination_lng,
            'current_lat': current_lat,
            'current_lng': current_lng,
            'destination': {
                'total_count': destination_total,
                'by_type': destination_counts
            },
            'current': {
                'total_count': current_total,
                'by_type': current_counts
            },
            'lifestyle_score': lifestyle_score,
            'comparison_text': comparison_text,
            'same_location': False,
            'search_radius': '1 mile'
        }
    
    def get_commute_info(
        self,
        origin_lat: float,
        origin_lng: float,
        work_address: str,
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """
        Get commute information from new location to work
        
        Args:
            origin_lat: Latitude of destination address
            origin_lng: Longitude of destination address
            work_address: User's work address
            mode: Travel mode (driving, transit, bicycling, walking)
        """
        
        if not work_address:
            return {
                'duration_minutes': None,
                'distance': 'Unknown',
                'method': mode,
                'description': 'No work address provided - commute analysis unavailable.'
            }
        
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
                    'method': mode,  # Return the actual method used
                    'description': f"Your commute will be approximately {duration} minutes by {mode}."
                }
        except Exception as e:
            print(f"Commute calculation error: {e}")
        
        return {
            'duration_minutes': None,
            'distance': 'Unknown',
            'method': mode,
            'description': 'Unable to calculate commute time.'
        }


# Global instance
places_service = PlacesService()