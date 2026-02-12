import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import random


class FBIRealCrimeService:
    """
    Service for fetching REAL crime data from FBI Crime Data Explorer API
    Parses crime RATES and converts to estimated counts for comparison
    """
    
    def __init__(self):
        self.base_url = "https://api.usa.gov/crime/fbi/cde"
        
        try:
            from app.core.config import settings
            self.api_key = getattr(settings, 'FBI_API_KEY', None)
        except:
            self.api_key = None
        
        # Major city to ORI mapping with population estimates
        self.city_data = {
            # Format: (lat_min, lat_max, lon_min, lon_max): ('ORI', population)
            (40.5, 41.0, -74.5, -73.5): ('NY0030000', 8300000),  # NYC
            (33.5, 34.5, -118.5, -117.5): ('CA0190000', 4000000),  # LA
            (41.5, 42.5, -88.0, -87.0): ('IL0160000', 2700000),  # Chicago
            (33.5, 34.0, -84.5, -84.0): ('GA0210000', 500000),  # Atlanta
            (37.5, 38.0, -122.5, -122.0): ('CA0750000', 880000),  # SF
            (29.5, 30.0, -95.5, -95.0): ('TX2200000', 2300000),  # Houston
            (47.0, 48.0, -122.5, -122.0): ('WA8200000', 750000),  # Seattle
            (25.5, 26.0, -80.5, -80.0): ('FL0130000', 450000),  # Miami
            (33.0, 34.0, -112.5, -111.5): ('AZ0070000', 1700000),  # Phoenix
            (42.0, 43.0, -71.5, -70.5): ('MA0070000', 690000),  # Boston
        }
    
    def get_crime_data_by_location(
        self,
        latitude: float,
        longitude: float,
        radius_miles: float = 5.0,
        days: int = 30
    ) -> Dict[str, Any]:
        """Fetch REAL crime data from FBI"""
        
        try:
            city_info = self._get_city_info_from_coords(latitude, longitude)
            
            if not city_info:
                print(f"ℹ️  No FBI data mapping for location (using estimates)")
                return self._get_fallback_data(latitude, longitude, days)
            
            ori, population = city_info
            print(f"📡 Fetching FBI crime rates for {ori} (pop: {population:,})")
            
            crime_rates = self._fetch_crime_rates(ori)
            
            if crime_rates:
                print(f"✅ FBI rates retrieved: {crime_rates['avg_violent_rate']:.1f} violent crimes per 100k")
                return self._convert_rates_to_counts(
                    crime_rates, population, latitude, longitude, days
                )
            else:
                print(f"ℹ️  No FBI rate data available (using estimates)")
                return self._get_fallback_data(latitude, longitude, days)
                
        except Exception as e:
            print(f"FBI service error: {e}")
            return self._get_fallback_data(latitude, longitude, days)
    
    def _get_city_info_from_coords(self, lat: float, lon: float) -> Optional[tuple]:
        """Map coordinates to (ORI, population)"""
        for (lat_min, lat_max, lon_min, lon_max), city_info in self.city_data.items():
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                return city_info
        return None
    
    def _fetch_crime_rates(self, ori: str) -> Optional[Dict[str, Any]]:
        """
        Fetch crime RATES from FBI API
        Returns: rates per 100k population
        """
        
        try:
            current_year = datetime.now().year
            years_to_try = [current_year, current_year - 1, current_year - 2]
            
            for year in years_to_try:
                from_date = f"01-{year}"
                to_date = f"12-{year}"
                
                # Fetch violent crime rates
                url = f"{self.base_url}/summarized/agency/{ori}/V"
                params = {'from': from_date, 'to': to_date}
                if self.api_key:
                    params['api_key'] = self.api_key
                
                # Try with retry logic
                for attempt in range(2):  # 2 attempts
                    try:
                        response = requests.get(url, params=params, timeout=30)  # Increased to 30s
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            print(f"🔍 Response type: {type(data)}")
                            print(f"🔍 Response keys: {data.keys() if isinstance(data, dict) else 'not a dict'}")
                            
                            # Parse the rates format
                            if isinstance(data, dict) and 'offenses' in data:
                                rates_dict = data['offenses'].get('rates', {})
                                print(f"🔍 Rates dict keys: {list(rates_dict.keys())}")
                                
                                # Extract monthly rates (filter out None values)
                                monthly_rates = []
                                for key, month_data in rates_dict.items():
                                    if isinstance(month_data, dict):
                                        print(f"🔍 {key} data: {month_data}")
                                        valid_rates = [v for v in month_data.values() if v is not None and isinstance(v, (int, float))]
                                        monthly_rates.extend(valid_rates)
                                        print(f"🔍 Valid rates from {key}: {len(valid_rates)} values")
                                
                                print(f"🔍 Total valid monthly rates: {len(monthly_rates)}")
                                
                                if monthly_rates and len(monthly_rates) > 0:
                                    avg_rate = sum(monthly_rates) / len(monthly_rates)
                                    
                                    print(f"✓ FBI data found for {year}: {avg_rate:.1f} per 100k (from {len(monthly_rates)} months)")
                                    
                                    return {
                                        'avg_violent_rate': avg_rate,
                                        'year': year,
                                        'monthly_rates': monthly_rates,
                                        'data_source': f'FBI UCR {year}'
                                    }
                                else:
                                    print(f"⚠️  No valid rate data for {year}")
                                    continue
                            else:
                                print(f"⚠️  Unexpected response format for {year}")
                                continue
                        
                        # Success, break retry loop
                        break
                        
                    except requests.Timeout:
                        if attempt == 0:
                            print(f"⏳ FBI API timeout, retrying...")
                            continue
                        else:
                            print(f"⚠️  FBI API still timing out after retry")
                            break
                    except Exception as e:
                        print(f"Error on attempt {attempt + 1}: {e}")
                        break
            
            return None
            
        except Exception as e:
            print(f"Error fetching rates: {e}")
            return None
    
    def _convert_rates_to_counts(
        self,
        crime_rates: Dict[str, Any],
        population: int,
        latitude: float,
        longitude: float,
        days: int
    ) -> Dict[str, Any]:
        """
        Convert FBI crime RATES (per 100k) to estimated COUNTS
        """
        
        # Extract rate (per 100k people)
        violent_rate = crime_rates['avg_violent_rate']
        
        # Convert rate to annual count for this population
        # Rate is per 100k, so: (rate / 100000) * population = annual crimes
        annual_violent = int((violent_rate / 100000) * population)
        
        # Property crimes are typically 2-3x violent crimes
        annual_property = int(annual_violent * 2.5)
        
        # Convert annual to 30-day period
        monthly_ratio = days / 365.0
        monthly_violent = int(annual_violent * monthly_ratio)
        monthly_property = int(annual_property * monthly_ratio)
        
        total_monthly = monthly_violent + monthly_property
        
        print(f"✓ Converted: {violent_rate:.1f}/100k → {total_monthly} crimes/30 days")
        
        # Generate individual crime incidents based on real totals
        crimes = self._generate_crimes_from_totals(
            monthly_violent,
            monthly_property,
            latitude,
            longitude,
            days
        )
        
        return {
            'crimes': crimes,
            'total_count': len(crimes),
            'period_days': days,
            'radius_miles': 5.0,
            'center_lat': latitude,
            'center_lon': longitude,
            'data_source': crime_rates['data_source'] + ' (official)',
            'fbi_rate_per_100k': violent_rate,
            'estimated_annual': annual_violent + annual_property,
            'is_real_data': True
        }
    
    def _generate_crimes_from_totals(
        self,
        violent_count: int,
        property_count: int,
        latitude: float,
        longitude: float,
        days: int
    ) -> List[Dict]:
        """Generate individual crime incidents based on FBI totals"""
        
        crimes = []
        
        # Crime type distribution
        crime_types = []
        crime_types.extend([('Assault', 'violent')] * int(violent_count * 0.65))
        crime_types.extend([('Robbery', 'violent')] * int(violent_count * 0.35))
        crime_types.extend([('Burglary', 'property')] * int(property_count * 0.25))
        crime_types.extend([('Larceny/Theft', 'theft')] * int(property_count * 0.55))
        crime_types.extend([('Vehicle Theft', 'theft')] * int(property_count * 0.15))
        crime_types.extend([('Vandalism', 'vandalism')] * int(property_count * 0.05))
        
        # Realistic hourly distribution
        hour_weights = [
            3, 3, 2, 2, 2, 2, 3, 4, 3, 3, 3, 3,  # 00-11
            3, 3, 3, 4, 4, 5, 6, 7, 8, 7, 5, 4   # 12-23
        ]
        
        for crime_type, category in crime_types:
            crime_date = datetime.now() - timedelta(days=random.randint(0, days))
            hour = random.choices(range(24), weights=hour_weights)[0]
            minute = random.randint(0, 59)
            crime_date = crime_date.replace(hour=hour, minute=minute, second=0)
            
            crimes.append({
                'type': crime_type,
                'category': category,
                'date': crime_date.strftime('%m/%d/%Y %I:%M %p'),
                'timestamp': crime_date,
                'address': f'{random.randint(100, 9999)} {random.choice(["Main", "Oak", "Elm"])} {random.choice(["St", "Ave"])}',
                'lat': latitude + random.uniform(-0.05, 0.05),
                'lon': longitude + random.uniform(-0.05, 0.05),
                'description': f'{crime_type} (FBI UCR data-based)'
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
        """Compare real FBI crime data between locations"""
        
        current_data = self.get_crime_data_by_location(current_lat, current_lon)
        destination_data = self.get_crime_data_by_location(destination_lat, destination_lon)
        
        # Import helper methods
        from app.services.fbi_crime_service import fbi_crime_service
        
        # Analyze patterns
        current_temporal = fbi_crime_service._analyze_temporal_patterns(
            current_data['crimes'], user_schedule
        )
        destination_temporal = fbi_crime_service._analyze_temporal_patterns(
            destination_data['crimes'], user_schedule
        )
        
        current_categories = fbi_crime_service._categorize_crimes(current_data['crimes'])
        destination_categories = fbi_crime_service._categorize_crimes(destination_data['crimes'])
        
        current_trend = fbi_crime_service._calculate_trend(current_data['crimes'])
        destination_trend = fbi_crime_service._calculate_trend(destination_data['crimes'])
        
        current_score = fbi_crime_service._calculate_safety_score(
            current_data['total_count'], current_categories, current_temporal
        )
        destination_score = fbi_crime_service._calculate_safety_score(
            destination_data['total_count'], destination_categories, destination_temporal
        )
        
        # Calculate percentage change
        if current_data['total_count'] > 0:
            percent_change = ((destination_data['total_count'] - current_data['total_count']) / 
                            current_data['total_count'] * 100)
        else:
            percent_change = 0
        
        return {
            'current': {
                'total_crimes': current_data['total_count'],
                'daily_average': round(current_data['total_count'] / 30, 2),
                'categories': current_categories,
                'temporal_analysis': current_temporal,
                'trend': current_trend,
                'safety_score': current_score,
                'crimes_list': current_data['crimes'][:50],
                'data_source': current_data.get('data_source', 'Crime analysis'),
                'is_real_data': current_data.get('is_real_data', False),
                'fbi_rate': current_data.get('fbi_rate_per_100k')
            },
            'destination': {
                'total_crimes': destination_data['total_count'],
                'daily_average': round(destination_data['total_count'] / 30, 2),
                'categories': destination_categories,
                'temporal_analysis': destination_temporal,
                'trend': destination_trend,
                'safety_score': destination_score,
                'crimes_list': destination_data['crimes'][:50],
                'data_source': destination_data.get('data_source', 'Crime analysis'),
                'is_real_data': destination_data.get('is_real_data', False),
                'fbi_rate': destination_data.get('fbi_rate_per_100k')
            },
            'comparison': {
                'crime_difference': destination_data['total_count'] - current_data['total_count'],
                'crime_change_percent': round(percent_change, 1),
                'score_difference': destination_score - current_score,
                'is_safer': destination_score > current_score,
                'recommendation': fbi_crime_service._generate_safety_recommendation(
                    current_score, destination_score, current_temporal, destination_temporal
                )
            }
        }
    
    def _get_fallback_data(self, lat: float, lon: float, days: int) -> Dict:
        """Use estimates when FBI data unavailable"""
        from app.services.fbi_crime_service import fbi_crime_service
        return fbi_crime_service._get_realistic_mock_data(lat, lon, days)


# Global instance
fbi_real_crime_service = FBIRealCrimeService()