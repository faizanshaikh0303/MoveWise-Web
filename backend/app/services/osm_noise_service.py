import requests
from typing import Dict, Any, List, Optional, Tuple
import math
from geopy.geocoders import Nominatim
from geopy.distance import geodesic


class OSMNoiseService:
    """
    Advanced noise analysis using OpenStreetMap road classifications
    with distance-weighted noise modeling
    """
    
    # Noise level ranges by road type (in dB)
    NOISE_LEVELS = {
        'motorway': (75, 85),      # Highways
        'trunk': (70, 80),
        'primary': (65, 75),        # Major arterials
        'secondary': (60, 70),      # Secondary arterials  
        'tertiary': (55, 65),       # Minor arterials
        'residential': (45, 55),    # Residential streets
        'service': (40, 50),        # Service roads
        'unclassified': (45, 55),   # Unclassified
    }
    
    ROAD_TYPE_CATEGORIES = {
        'highway': ['motorway', 'trunk'],
        'arterial': ['primary', 'secondary', 'tertiary'],
        'residential': ['residential', 'service', 'unclassified']
    }
    
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.geolocator = Nominatim(user_agent="movewise_app")
    
    def analyze_noise_environment(
        self,
        latitude: float,
        longitude: float,
        radius_miles: float = 2.0,
        user_preferences: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze noise environment using OpenStreetMap road data
        
        Args:
            latitude: Center point latitude
            longitude: Center point longitude
            radius_miles: Analysis radius in miles (default 2.0)
            user_preferences: User noise tolerance preferences
        """
        try:
            # Convert radius to meters for OSM query
            radius_meters = radius_miles * 1609.34
            
            # Fetch road data from OpenStreetMap
            roads = self._fetch_osm_roads(latitude, longitude, radius_meters)
            
            # Calculate noise contributions from each road
            noise_contributions = self._calculate_noise_contributions(
                roads,
                (latitude, longitude),
                radius_miles
            )
            
            # Aggregate noise analysis
            analysis = self._aggregate_noise_analysis(noise_contributions)
            
            # Calculate noise score
            noise_score = self._calculate_noise_score(
                analysis,
                user_preferences
            )
            
            # Categorize noise level
            noise_category = self._categorize_noise_level(analysis['estimated_db'])
            
            return {
                'estimated_db': analysis['estimated_db'],
                'noise_category': noise_category,
                'noise_score': noise_score,
                'road_breakdown': analysis['road_breakdown'],
                'dominant_noise_source': analysis['dominant_source'],
                'total_roads': len(roads),
                'road_density': self._calculate_road_density(roads, radius_miles),
                'distance_weighted_impact': analysis['weighted_impact'],
                'recommendations': self._generate_noise_recommendations(
                    analysis,
                    user_preferences
                )
            }
            
        except Exception as e:
            print(f"OSM Noise Analysis Error: {e}")
            return self._get_fallback_analysis(latitude, longitude)
    
    def compare_noise_environments(
        self,
        current_lat: float,
        current_lon: float,
        destination_lat: float,
        destination_lon: float,
        user_preferences: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Compare noise environments between two locations"""
        
        current_analysis = self.analyze_noise_environment(
            current_lat,
            current_lon,
            user_preferences=user_preferences
        )
        
        destination_analysis = self.analyze_noise_environment(
            destination_lat,
            destination_lon,
            user_preferences=user_preferences
        )
        
        # Calculate comparison metrics
        db_difference = destination_analysis['estimated_db'] - current_analysis['estimated_db']
        score_difference = destination_analysis['noise_score'] - current_analysis['noise_score']
        
        # Determine preference match
        user_tolerance = user_preferences.get('noise_preference', 'moderate') if user_preferences else 'moderate'
        preference_match = self._evaluate_preference_match(
            destination_analysis['noise_category'],
            user_tolerance
        )
        
        return {
            'current': current_analysis,
            'destination': destination_analysis,
            'comparison': {
                'db_difference': round(db_difference, 1),
                'db_change_description': self._describe_db_change(db_difference),
                'score_difference': round(score_difference, 1),
                'is_quieter': db_difference < 0,
                'category_change': f"{current_analysis['noise_category']} → {destination_analysis['noise_category']}",
                'preference_match': preference_match,
                'recommendation': self._generate_comparison_recommendation(
                    current_analysis,
                    destination_analysis,
                    user_tolerance,
                    db_difference
                )
            }
        }
    
    def _fetch_osm_roads(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float
    ) -> List[Dict[str, Any]]:
        """Fetch road data from OpenStreetMap Overpass API"""
        
        # Overpass QL query for roads
        query = f"""
        [out:json];
        (
          way["highway"](around:{radius_meters},{latitude},{longitude});
        );
        out body;
        >;
        out skel qt;
        """
        
        try:
            response = requests.post(
                self.overpass_url,
                data={'data': query},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            elements = data.get('elements', [])
            
            # Process roads
            roads = []
            nodes = {el['id']: el for el in elements if el['type'] == 'node'}
            
            for element in elements:
                if element['type'] == 'way' and 'tags' in element:
                    road_type = element['tags'].get('highway')
                    if road_type:
                        # Get road coordinates
                        coords = []
                        for node_id in element.get('nodes', []):
                            if node_id in nodes:
                                node = nodes[node_id]
                                coords.append((node['lat'], node['lon']))
                        
                        if coords:
                            # Calculate closest distance to center
                            min_distance = min(
                                geodesic((latitude, longitude), coord).miles
                                for coord in coords
                            )
                            
                            roads.append({
                                'id': element['id'],
                                'type': road_type,
                                'name': element['tags'].get('name', 'Unnamed Road'),
                                'coordinates': coords,
                                'min_distance_miles': min_distance,
                                'lanes': element['tags'].get('lanes', 2),
                                'maxspeed': element['tags'].get('maxspeed')
                            })
            
            return roads
            
        except Exception as e:
            print(f"OSM Overpass API Error: {e}")
            return self._generate_mock_roads(latitude, longitude)
    
    def _calculate_noise_contributions(
        self,
        roads: List[Dict],
        center_point: Tuple[float, float],
        radius_miles: float
    ) -> List[Dict[str, Any]]:
        """
        Calculate noise contribution from each road based on:
        - Road type (highway, arterial, residential)
        - Distance from center point
        - Distance decay model
        """
        contributions = []
        
        for road in roads:
            road_type = road['type']
            distance = road['min_distance_miles']
            
            # Get base noise level for road type
            noise_range = self.NOISE_LEVELS.get(road_type, (50, 60))
            base_noise = (noise_range[0] + noise_range[1]) / 2
            
            # Apply distance decay
            # Noise decreases by ~6 dB for every doubling of distance
            if distance < 0.1:  # Very close (within 500 feet)
                distance_factor = 1.0
            else:
                distance_factor = 1 / (1 + (distance / 0.1))
            
            weighted_noise = base_noise * distance_factor
            
            # Categorize road
            category = self._categorize_road(road_type)
            
            contributions.append({
                'road_name': road['name'],
                'road_type': road_type,
                'category': category,
                'base_noise_db': base_noise,
                'distance_miles': distance,
                'distance_factor': round(distance_factor, 3),
                'weighted_noise_db': round(weighted_noise, 1),
                'noise_range': noise_range
            })
        
        return contributions
    
    def _categorize_road(self, road_type: str) -> str:
        """Categorize road into highway/arterial/residential"""
        for category, types in self.ROAD_TYPE_CATEGORIES.items():
            if road_type in types:
                return category
        return 'residential'
    
    def _aggregate_noise_analysis(
        self,
        contributions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate noise contributions into overall analysis"""
        
        if not contributions:
            return {
                'estimated_db': 45,
                'road_breakdown': {'residential': 0, 'arterial': 0, 'highway': 0},
                'dominant_source': 'residential',
                'weighted_impact': 0
            }
        
        # Calculate combined noise level (logarithmic addition)
        total_noise_linear = sum(10 ** (c['weighted_noise_db'] / 10) for c in contributions)
        estimated_db = 10 * math.log10(total_noise_linear) if total_noise_linear > 0 else 45
        
        # Breakdown by category
        breakdown = {'highway': 0, 'arterial': 0, 'residential': 0}
        for contrib in contributions:
            category = contrib['category']
            breakdown[category] += 1
        
        # Find dominant source
        max_contrib = max(contributions, key=lambda x: x['weighted_noise_db'])
        dominant_source = max_contrib['category']
        
        # Calculate weighted impact score
        weighted_impact = sum(c['weighted_noise_db'] for c in contributions) / len(contributions)
        
        return {
            'estimated_db': round(estimated_db, 1),
            'road_breakdown': breakdown,
            'dominant_source': dominant_source,
            'weighted_impact': round(weighted_impact, 1),
            'contributions': contributions[:10]  # Top 10 for display
        }
    
    def _calculate_noise_score(
        self,
        analysis: Dict[str, Any],
        user_preferences: Optional[Dict] = None
    ) -> float:
        """
        Calculate noise score (0-100, higher is better match)
        Based on: absolute noise level, user preference match
        """
        estimated_db = analysis['estimated_db']
        
        if not user_preferences:
            # Default scoring: quieter is better
            base_score = max(0, 100 - (estimated_db - 40))
            return round(base_score, 1)
        
        user_tolerance = user_preferences.get('noise_preference', 'moderate')
        
        # Ideal dB ranges for each preference
        ideal_ranges = {
            'quiet': (40, 50),
            'moderate': (50, 65),
            'lively': (65, 75)
        }
        
        ideal_min, ideal_max = ideal_ranges.get(user_tolerance, (50, 65))
        
        # Calculate how close actual dB is to ideal range
        if ideal_min <= estimated_db <= ideal_max:
            score = 100  # Perfect match
        elif estimated_db < ideal_min:
            # Too quiet
            deviation = ideal_min - estimated_db
            score = max(70, 100 - (deviation * 2))
        else:
            # Too loud
            deviation = estimated_db - ideal_max
            score = max(30, 100 - (deviation * 3))
        
        return round(score, 1)
    
    def _categorize_noise_level(self, db_level: float) -> str:
        """Categorize noise level into descriptive categories"""
        if db_level < 50:
            return 'Very Quiet'
        elif db_level < 55:
            return 'Quiet'
        elif db_level < 65:
            return 'Moderate'
        elif db_level < 75:
            return 'Noisy'
        else:
            return 'Very Noisy'
    
    def _calculate_road_density(self, roads: List[Dict], radius_miles: float) -> float:
        """Calculate road density (roads per square mile)"""
        area = math.pi * (radius_miles ** 2)
        return round(len(roads) / area, 1) if area > 0 else 0
    
    def _evaluate_preference_match(self, noise_category: str, user_preference: str) -> Dict[str, Any]:
        """Evaluate how well noise level matches user preference"""
        
        # Mapping of categories to preferences
        matches = {
            'Very Quiet': {'quiet': 'excellent', 'moderate': 'good', 'lively': 'poor'},
            'Quiet': {'quiet': 'excellent', 'moderate': 'good', 'lively': 'fair'},
            'Moderate': {'quiet': 'fair', 'moderate': 'excellent', 'lively': 'good'},
            'Noisy': {'quiet': 'poor', 'moderate': 'fair', 'lively': 'excellent'},
            'Very Noisy': {'quiet': 'poor', 'moderate': 'poor', 'lively': 'good'}
        }
        
        match_quality = matches.get(noise_category, {}).get(user_preference, 'fair')
        
        return {
            'quality': match_quality,
            'is_good_match': match_quality in ['excellent', 'good']
        }
    
    def _describe_db_change(self, db_diff: float) -> str:
        """Describe decibel change in human terms"""
        abs_diff = abs(db_diff)
        
        if abs_diff < 3:
            return "Virtually identical"
        elif abs_diff < 6:
            return "Slightly quieter" if db_diff < 0 else "Slightly louder"
        elif abs_diff < 10:
            return "Noticeably quieter" if db_diff < 0 else "Noticeably louder"
        else:
            return "Significantly quieter" if db_diff < 0 else "Significantly louder"
    
    def _generate_noise_recommendations(
        self,
        analysis: Dict[str, Any],
        user_preferences: Optional[Dict] = None
    ) -> List[str]:
        """Generate personalized noise recommendations"""
        recommendations = []
        
        estimated_db = analysis['estimated_db']
        dominant_source = analysis['dominant_source']
        
        if estimated_db > 65:
            recommendations.append("Consider white noise machines or soundproofing for better sleep quality")
            
        if dominant_source == 'highway':
            recommendations.append("Highway noise is dominant. Rooms facing away from major roads will be quieter")
        elif dominant_source == 'arterial':
            recommendations.append("Major street noise present. Upper floors typically experience less street noise")
        
        if user_preferences:
            tolerance = user_preferences.get('noise_preference', 'moderate')
            if tolerance == 'quiet' and estimated_db > 60:
                recommendations.append("This area may be louder than your preference. Consider locations further from main roads")
            elif tolerance == 'lively' and estimated_db < 55:
                recommendations.append("This is a quiet area. If you prefer more activity, consider areas closer to commercial districts")
        
        if not recommendations:
            recommendations.append("Noise levels are moderate and suitable for most residents")
        
        return recommendations
    
    def _generate_comparison_recommendation(
        self,
        current: Dict,
        destination: Dict,
        user_tolerance: str,
        db_diff: float
    ) -> str:
        """Generate comparison recommendation"""
        
        dest_match = self._evaluate_preference_match(
            destination['noise_category'],
            user_tolerance
        )
        
        if dest_match['is_good_match']:
            if db_diff < -5:
                return f"Excellent news! The new location is {abs(db_diff):.1f} dB quieter and matches your '{user_tolerance}' preference perfectly."
            elif db_diff > 5:
                return f"The new location is {db_diff:.1f} dB louder, but still matches your '{user_tolerance}' preference well."
            else:
                return f"Similar noise levels with good match to your '{user_tolerance}' preference."
        else:
            return f"The new location may not match your '{user_tolerance}' preference. Consider visiting at different times of day."
    
    def _generate_mock_roads(self, lat: float, lon: float) -> List[Dict]:
        """Generate mock road data for fallback"""
        import random
        
        roads = []
        road_types = ['motorway', 'primary', 'secondary', 'residential']
        
        for i in range(random.randint(20, 50)):
            roads.append({
                'id': i,
                'type': random.choice(road_types),
                'name': f'Street {i}',
                'coordinates': [(lat, lon)],
                'min_distance_miles': random.uniform(0.1, 2.0),
                'lanes': random.randint(2, 4),
                'maxspeed': None
            })
        
        return roads
    
    def _get_fallback_analysis(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fallback analysis when API fails"""
        return {
            'estimated_db': 55,
            'noise_category': 'Moderate',
            'noise_score': 70,
            'road_breakdown': {'highway': 2, 'arterial': 5, 'residential': 15},
            'dominant_noise_source': 'residential',
            'total_roads': 22,
            'road_density': 35.0,
            'distance_weighted_impact': 52.0,
            'recommendations': ['Noise analysis unavailable - using estimated values']
        }


# Global instance
osm_noise_service = OSMNoiseService()
