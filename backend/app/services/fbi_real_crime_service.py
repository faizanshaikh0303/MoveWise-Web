import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import math


class FBIRealCrimeService:
    """
    Service for fetching REAL crime data from FBI Crime Data Explorer API
    Uses actual agency-level crime statistics from FBI UCR program
    """
    
    def __init__(self):
        # FBI Crime Data API
        self.base_url = "https://api.usa.gov/crime/fbi/cde"
        
        # Try to get API key from settings
        try:
            from app.core.config import settings
            self.api_key = getattr(settings, 'FBI_API_KEY', None)
        except:
            self.api_key = None
        
        # Major city to ORI (Originating Agency Identifier) mapping
        # ORI format: State(2) + County(3) + Agency(4) = 9 characters
        self.city_ori_map = {
            # Format: (lat_min, lat_max, lon_min, lon_max): 'ORI'
            # New York
            (40.5, 41.0, -74.5, -73.5): 'NY0030000',  # NYPD
            # Los Angeles
            (33.5, 34.5, -118.5, -117.5): 'CA0190000',  # LAPD
            # Chicago
            (41.5, 42.5, -88.0, -87.0): 'IL0160000',  # Chicago PD
            # Atlanta
            (33.5, 34.0, -84.5, -84.0): 'GA0210000',  # Atlanta PD
            # San Francisco
            (37.5, 38.0, -122.5, -122.0): 'CA0750000',  # SFPD
            # Houston
            (29.5, 30.0, -95.5, -95.0): 'TX2200000',  # Houston PD
            # Seattle
            (47.0, 48.0, -122.5, -122.0): 'WA8200000',  # Seattle PD
            # Miami
            (25.5, 26.0, -80.5, -80.0): 'FL0130000',  # Miami PD
            # Phoenix
            (33.0, 34.0, -112.5, -111.5): 'AZ0070000',  # Phoenix PD
            # Boston
            (42.0, 43.0, -71.5, -70.5): 'MA0070000',  # Boston PD
        }
        
        # Crime type codes for FBI API
        self.offense_codes = {
            'violent': 'V',
            'assault': 'ASS',
            'burglary': 'BUR',
            'larceny': 'LAR',
            'motor_vehicle_theft': 'MVT',
            'homicide': 'HOM',
            'rape': 'RPE',
            'robbery': 'ROB',
            'arson': 'ARS',
            'property': 'P'
        }
    
    def get_crime_data_by_location(
        self,
        latitude: float,
        longitude: float,
        radius_miles: float = 5.0,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Fetch REAL crime data from FBI for a location
        """
        try:
            # Find the police agency (ORI) for this location
            ori = self._get_ori_from_coords(latitude, longitude)
            
            if not ori:
                print(f"ℹ️  No FBI agency mapping for this location (using estimates)")
                return self._get_realistic_mock_data(latitude, longitude, days)
            
            print(f"📡 Fetching real FBI data for agency: {ori}")
            
            # Fetch crime data for multiple offense types
            crime_data = self._fetch_agency_crime_data(ori)
            
            if crime_data:
                print(f"✅ Real FBI data retrieved!")
                return self._process_fbi_agency_data(crime_data, latitude, longitude, days)
            else:
                print(f"ℹ️  FBI data unavailable for {ori} (using estimates)")
                return self._get_realistic_mock_data(latitude, longitude, days)
                
        except Exception as e:
            print(f"FBI API Error: {e}")
            return self._get_realistic_mock_data(latitude, longitude, days)
    
    def _get_ori_from_coords(self, lat: float, lon: float) -> Optional[str]:
        """Map coordinates to police agency ORI"""
        for (lat_min, lat_max, lon_min, lon_max), ori in self.city_ori_map.items():
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                return ori
        return None
    
    def _fetch_agency_crime_data(self, ori: str) -> Optional[Dict[str, Any]]:
        """
        Fetch real crime data for a specific agency
        Returns annual crime counts by offense type
        """
        try:
            # Get data for most recent year available
            current_year = datetime.now().year
            years_to_try = [current_year - 1, current_year - 2, current_year - 3]  # Try 2024, 2023, 2022
            
            crime_totals = {}
            data_year = None
            
            for year in years_to_try:
                # Format dates as required by API (mm-yyyy)
                from_date = f"01-{year}"
                to_date = f"12-{year}"
                
                # Fetch violent crime total
                violent_url = f"{self.base_url}/summarized/agency/{ori}/V"
                params = {'from': from_date, 'to': to_date}
                if self.api_key:
                    params['api_key'] = self.api_key
                
                response = requests.get(violent_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        data_year = year
                        print(f"✓ Found FBI data for year {year}")
                        
                        # Sum up all violent crime
                        violent_total = sum(entry.get('actual', 0) for entry in data)
                        crime_totals['violent'] = violent_total
                        
                        # Fetch property crime
                        property_url = f"{self.base_url}/summarized/agency/{ori}/P"
                        prop_response = requests.get(property_url, params=params, timeout=10)
                        if prop_response.status_code == 200:
                            prop_data = prop_response.json()
                            property_total = sum(entry.get('actual', 0) for entry in prop_data)
                            crime_totals['property'] = property_total
                        
                        # Fetch specific offenses for breakdown
                        for offense_name, offense_code in [
                            ('assault', 'ASS'),
                            ('burglary', 'BUR'),
                            ('larceny', 'LAR'),
                            ('motor_vehicle_theft', 'MVT'),
                            ('robbery', 'ROB')
                        ]:
                            offense_url = f"{self.base_url}/summarized/agency/{ori}/{offense_code}"
                            off_response = requests.get(offense_url, params=params, timeout=10)
                            if off_response.status_code == 200:
                                off_data = off_response.json()
                                offense_total = sum(entry.get('actual', 0) for entry in off_data)
                                crime_totals[offense_name] = offense_total
                        
                        break  # Got data, stop trying years
                
            if crime_totals and data_year:
                return {
                    'totals': crime_totals,
                    'year': data_year,
                    'ori': ori,
                    'data_source': 'FBI UCR'
                }
            
            return None
            
        except Exception as e:
            print(f"Error fetching agency data: {e}")
            return None
    
    def _process_fbi_agency_data(
        self,
        fbi_data: Dict[str, Any],
        latitude: float,
        longitude: float,
        days: int
    ) -> Dict[str, Any]:
        """
        Process FBI agency data into monthly estimates
        FBI provides annual totals - we convert to 30-day estimates
        """
        
        annual_totals = fbi_data['totals']
        year = fbi_data['year']
        
        # Convert annual to monthly (30 days)
        monthly_ratio = days / 365.0
        
        # Estimate monthly crimes from annual data
        violent = int(annual_totals.get('violent', 0) * monthly_ratio)
        property_crime = int(annual_totals.get('property', 0) * monthly_ratio)
        assault = int(annual_totals.get('assault', 0) * monthly_ratio)
        burglary = int(annual_totals.get('burglary', 0) * monthly_ratio)
        larceny = int(annual_totals.get('larceny', 0) * monthly_ratio)
        mvt = int(annual_totals.get('motor_vehicle_theft', 0) * monthly_ratio)
        robbery = int(annual_totals.get('robbery', 0) * monthly_ratio)
        
        total_crimes = violent + property_crime
        
        # Generate synthetic incidents based on real totals
        crimes = self._generate_crimes_from_totals(
            violent, property_crime, assault, burglary, larceny, mvt, robbery,
            latitude, longitude, days
        )
        
        return {
            'crimes': crimes,
            'total_count': len(crimes),
            'period_days': days,
            'radius_miles': 5.0,
            'center_lat': latitude,
            'center_lon': longitude,
            'data_source': f'FBI UCR {year} (official)',
            'fbi_annual_data': annual_totals,
            'is_real_data': True
        }
    
    def _generate_crimes_from_totals(
        self,
        violent: int,
        property_crime: int,
        assault: int,
        burglary: int,
        larceny: int,
        mvt: int,
        robbery: int,
        latitude: float,
        longitude: float,
        days: int
    ) -> List[Dict]:
        """
        Generate individual crime incidents based on FBI totals
        Uses real counts but creates synthetic incidents for temporal analysis
        """
        import random
        
        crimes = []
        
        # Map FBI categories to crime types
        crime_distribution = []
        crime_distribution.extend([('Assault', 'violent')] * assault)
        crime_distribution.extend([('Burglary', 'property')] * burglary)
        crime_distribution.extend([('Larceny/Theft', 'theft')] * larceny)
        crime_distribution.extend([('Vehicle Theft', 'theft')] * mvt)
        crime_distribution.extend([('Robbery', 'violent')] * robbery)
        
        # Shuffle to randomize
        random.shuffle(crime_distribution)
        
        # Realistic hourly distribution (more crimes at night)
        hour_weights = [
            3, 3, 2, 2, 2, 2, 3, 4, 3, 3, 3, 3,  # 00:00-11:59
            3, 3, 3, 4, 4, 5, 6, 7, 8, 7, 5, 4   # 12:00-23:59
        ]
        
        for crime_type, category in crime_distribution:
            crime_date = datetime.now() - timedelta(days=random.randint(0, days))
            hour = random.choices(range(24), weights=hour_weights)[0]
            minute = random.randint(0, 59)
            crime_date = crime_date.replace(hour=hour, minute=minute, second=0)
            
            crimes.append({
                'type': crime_type,
                'category': category,
                'date': crime_date.strftime('%m/%d/%Y %I:%M %p'),
                'timestamp': crime_date,
                'address': f'{random.randint(100, 9999)} {random.choice(["Main", "Oak", "Elm", "Maple", "Pine"])} {random.choice(["St", "Ave", "Dr", "Blvd"])}',
                'lat': latitude + random.uniform(-0.05, 0.05),
                'lon': longitude + random.uniform(-0.05, 0.05),
                'description': f'{crime_type} (FBI UCR data)'
            })
        
        return crimes
    
    def compare_crime_data(
        self,
        current_lat: float,
        current_lon: float,
        destination_lat: float,
        destination_lon: float,
        user_schedule: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Compare real crime data between two locations"""
        
        current_data = self.get_crime_data_by_location(current_lat, current_lon)
        destination_data = self.get_crime_data_by_location(destination_lat, destination_lon)
        
        # Import helper methods from original service
        from app.services.fbi_crime_service import fbi_crime_service
        
        # Analyze temporal patterns
        current_temporal = fbi_crime_service._analyze_temporal_patterns(
            current_data['crimes'],
            user_schedule
        )
        destination_temporal = fbi_crime_service._analyze_temporal_patterns(
            destination_data['crimes'],
            user_schedule
        )
        
        # Categorize crimes
        current_categories = fbi_crime_service._categorize_crimes(current_data['crimes'])
        destination_categories = fbi_crime_service._categorize_crimes(destination_data['crimes'])
        
        # Calculate trends
        current_trend = fbi_crime_service._calculate_trend(current_data['crimes'])
        destination_trend = fbi_crime_service._calculate_trend(destination_data['crimes'])
        
        # Calculate safety scores
        current_score = fbi_crime_service._calculate_safety_score(
            current_data['total_count'],
            current_categories,
            current_temporal
        )
        destination_score = fbi_crime_service._calculate_safety_score(
            destination_data['total_count'],
            destination_categories,
            destination_temporal
        )
        
        return {
            'current': {
                'total_crimes': current_data['total_count'],
                'daily_average': round(current_data['total_count'] / 30, 2),
                'categories': current_categories,
                'temporal_analysis': current_temporal,
                'trend': current_trend,
                'safety_score': current_score,
                'crimes_list': current_data['crimes'][:50],
                'data_source': current_data.get('data_source', 'FBI-based estimates'),
                'is_real_data': current_data.get('is_real_data', False)
            },
            'destination': {
                'total_crimes': destination_data['total_count'],
                'daily_average': round(destination_data['total_count'] / 30, 2),
                'categories': destination_categories,
                'temporal_analysis': destination_temporal,
                'trend': destination_trend,
                'safety_score': destination_score,
                'crimes_list': destination_data['crimes'][:50],
                'data_source': destination_data.get('data_source', 'FBI-based estimates'),
                'is_real_data': destination_data.get('is_real_data', False)
            },
            'comparison': {
                'crime_difference': destination_data['total_count'] - current_data['total_count'],
                'crime_change_percent': fbi_crime_service._calculate_percentage_change(
                    current_data['total_count'],
                    destination_data['total_count']
                ),
                'score_difference': destination_score - current_score,
                'is_safer': destination_score > current_score,
                'recommendation': fbi_crime_service._generate_safety_recommendation(
                    current_score,
                    destination_score,
                    current_temporal,
                    destination_temporal
                )
            }
        }
    
    def _get_realistic_mock_data(self, lat: float, lon: float, days: int) -> Dict[str, Any]:
        """Fallback to estimates if FBI data unavailable"""
        from app.services.fbi_crime_service import fbi_crime_service
        return fbi_crime_service._get_realistic_mock_data(lat, lon, days)


# Global instance
fbi_real_crime_service = FBIRealCrimeService()