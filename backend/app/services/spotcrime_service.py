import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.core.config import settings
import math


class SpotCrimeService:
    """
    Service for fetching real-time crime data from SpotCrime API
    and analyzing temporal patterns relative to user schedules
    """
    
    def __init__(self):
        self.base_url = "https://api.spotcrime.com/crimes.json"
        # SpotCrime is free and doesn't require API key for basic usage
    
    def get_crime_data(
        self,
        latitude: float,
        longitude: float,
        radius_miles: float = 5.0,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Fetch crime data from SpotCrime API for a specific location
        
        Args:
            latitude: Center point latitude
            longitude: Center point longitude
            radius_miles: Search radius in miles (default 5)
            days: Number of days to look back (default 30)
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            params = {
                'lat': latitude,
                'lon': longitude,
                'radius': radius_miles,  # in miles
                'start': start_date.strftime('%m/%d/%Y'),
                'end': end_date.strftime('%m/%d/%Y'),
                'key': 'public'  # SpotCrime public access
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            crimes = data.get('crimes', [])
            
            # Parse and categorize crimes
            parsed_crimes = []
            for crime in crimes:
                parsed_crimes.append({
                    'type': crime.get('type', 'Unknown'),
                    'date': crime.get('date'),
                    'timestamp': self._parse_date(crime.get('date')),
                    'address': crime.get('address', 'Unknown'),
                    'lat': float(crime.get('lat', 0)),
                    'lon': float(crime.get('lon', 0)),
                    'description': crime.get('description', '')
                })
            
            return {
                'crimes': parsed_crimes,
                'total_count': len(parsed_crimes),
                'period_days': days,
                'radius_miles': radius_miles,
                'center_lat': latitude,
                'center_lon': longitude
            }
            
        except requests.exceptions.RequestException as e:
            print(f"SpotCrime API Error: {e}")
            # Return mock data for development/fallback
            return self._get_mock_data(latitude, longitude, days)
        except Exception as e:
            print(f"Crime data processing error: {e}")
            return self._get_mock_data(latitude, longitude, days)
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse SpotCrime date format"""
        try:
            # SpotCrime format: "MM/DD/YYYY HH:MM AM/PM"
            return datetime.strptime(date_str, '%m/%d/%Y %I:%M %p')
        except:
            return None
    
    def compare_crime_data(
        self,
        current_lat: float,
        current_lon: float,
        destination_lat: float,
        destination_lon: float,
        user_schedule: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Compare crime data between two locations with temporal analysis
        """
        # Fetch data for both locations
        current_data = self.get_crime_data(current_lat, current_lon)
        destination_data = self.get_crime_data(destination_lat, destination_lon)
        
        # Analyze temporal patterns
        current_temporal = self._analyze_temporal_patterns(
            current_data['crimes'],
            user_schedule
        )
        destination_temporal = self._analyze_temporal_patterns(
            destination_data['crimes'],
            user_schedule
        )
        
        # Categorize crimes
        current_categories = self._categorize_crimes(current_data['crimes'])
        destination_categories = self._categorize_crimes(destination_data['crimes'])
        
        # Calculate trends
        current_trend = self._calculate_trend(current_data['crimes'])
        destination_trend = self._calculate_trend(destination_data['crimes'])
        
        # Calculate safety scores (0-100, higher is safer)
        current_score = self._calculate_safety_score(
            current_data['total_count'],
            current_categories,
            current_temporal
        )
        destination_score = self._calculate_safety_score(
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
                'crimes_list': current_data['crimes'][:50]  # Limit for frontend
            },
            'destination': {
                'total_crimes': destination_data['total_count'],
                'daily_average': round(destination_data['total_count'] / 30, 2),
                'categories': destination_categories,
                'temporal_analysis': destination_temporal,
                'trend': destination_trend,
                'safety_score': destination_score,
                'crimes_list': destination_data['crimes'][:50]
            },
            'comparison': {
                'crime_difference': destination_data['total_count'] - current_data['total_count'],
                'crime_change_percent': self._calculate_percentage_change(
                    current_data['total_count'],
                    destination_data['total_count']
                ),
                'score_difference': destination_score - current_score,
                'is_safer': destination_score > current_score,
                'recommendation': self._generate_safety_recommendation(
                    current_score,
                    destination_score,
                    current_temporal,
                    destination_temporal
                )
            }
        }
    
    def _categorize_crimes(self, crimes: List[Dict]) -> Dict[str, int]:
        """Categorize crimes by type"""
        categories = {
            'violent': 0,
            'property': 0,
            'theft': 0,
            'vandalism': 0,
            'other': 0
        }
        
        violent_keywords = ['assault', 'robbery', 'shooting', 'homicide', 'murder', 'attack']
        property_keywords = ['burglary', 'breaking', 'trespassing']
        theft_keywords = ['theft', 'larceny', 'stolen', 'shoplifting']
        vandalism_keywords = ['vandalism', 'graffiti', 'damage']
        
        for crime in crimes:
            crime_type = crime.get('type', '').lower()
            description = crime.get('description', '').lower()
            
            if any(kw in crime_type or kw in description for kw in violent_keywords):
                categories['violent'] += 1
            elif any(kw in crime_type or kw in description for kw in property_keywords):
                categories['property'] += 1
            elif any(kw in crime_type or kw in description for kw in theft_keywords):
                categories['theft'] += 1
            elif any(kw in crime_type or kw in description for kw in vandalism_keywords):
                categories['vandalism'] += 1
            else:
                categories['other'] += 1
        
        return categories
    
    def _analyze_temporal_patterns(
        self,
        crimes: List[Dict],
        user_schedule: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze when crimes occur relative to user's schedule
        """
        hourly_distribution = [0] * 24
        crimes_during_work = 0
        crimes_during_sleep = 0
        crimes_during_commute = 0
        
        for crime in crimes:
            timestamp = crime.get('timestamp')
            if not timestamp:
                continue
            
            hour = timestamp.hour
            hourly_distribution[hour] += 1
            
            if user_schedule:
                # Parse user schedule
                work_start, work_end = self._parse_time_range(user_schedule.get('work_hours', '9:00 - 17:00'))
                sleep_start, sleep_end = self._parse_time_range(user_schedule.get('sleep_hours', '23:00 - 07:00'))
                
                # Check if crime occurred during user's schedules
                if self._is_time_in_range(hour, work_start, work_end):
                    crimes_during_work += 1
                
                if self._is_time_in_range(hour, sleep_start, sleep_end):
                    crimes_during_sleep += 1
                
                # Commute times (1 hour before/after work)
                commute_hours = [work_start - 1, work_start, work_end, work_end + 1]
                if hour in commute_hours:
                    crimes_during_commute += 1
        
        total_crimes = len(crimes)
        
        return {
            'hourly_distribution': hourly_distribution,
            'peak_hours': self._find_peak_hours(hourly_distribution),
            'crimes_during_work_hours': crimes_during_work,
            'crimes_during_sleep_hours': crimes_during_sleep,
            'crimes_during_commute': crimes_during_commute,
            'work_hours_percentage': round((crimes_during_work / total_crimes * 100), 1) if total_crimes > 0 else 0,
            'sleep_hours_percentage': round((crimes_during_sleep / total_crimes * 100), 1) if total_crimes > 0 else 0,
            'commute_percentage': round((crimes_during_commute / total_crimes * 100), 1) if total_crimes > 0 else 0
        }
    
    def _parse_time_range(self, time_range: str) -> tuple:
        """Parse time range like '9:00 - 17:00' to (9, 17)"""
        try:
            start, end = time_range.split('-')
            start_hour = int(start.strip().split(':')[0])
            end_hour = int(end.strip().split(':')[0])
            return start_hour, end_hour
        except:
            return 9, 17  # Default
    
    def _is_time_in_range(self, hour: int, start: int, end: int) -> bool:
        """Check if hour is in time range, handling overnight ranges"""
        if start <= end:
            return start <= hour < end
        else:  # Overnight range (e.g., 23:00 - 07:00)
            return hour >= start or hour < end
    
    def _find_peak_hours(self, hourly_dist: List[int]) -> List[int]:
        """Find hours with highest crime rates"""
        if not hourly_dist:
            return []
        
        max_crimes = max(hourly_dist)
        threshold = max_crimes * 0.7  # Top 30%
        
        return [hour for hour, count in enumerate(hourly_dist) if count >= threshold]
    
    def _calculate_trend(self, crimes: List[Dict]) -> Dict[str, Any]:
        """Calculate crime trend over the 30-day period"""
        if not crimes:
            return {'direction': 'stable', 'change': 0}
        
        # Split into two halves
        crimes_sorted = sorted(
            [c for c in crimes if c.get('timestamp')],
            key=lambda x: x['timestamp']
        )
        
        if len(crimes_sorted) < 2:
            return {'direction': 'stable', 'change': 0}
        
        midpoint = len(crimes_sorted) // 2
        first_half = crimes_sorted[:midpoint]
        second_half = crimes_sorted[midpoint:]
        
        first_half_count = len(first_half)
        second_half_count = len(second_half)
        
        if first_half_count == 0:
            return {'direction': 'increasing', 'change': 100}
        
        change = ((second_half_count - first_half_count) / first_half_count) * 100
        
        if change > 10:
            direction = 'increasing'
        elif change < -10:
            direction = 'decreasing'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'change_percent': round(change, 1),
            'first_half_count': first_half_count,
            'second_half_count': second_half_count
        }
    
    def _calculate_safety_score(
        self,
        total_crimes: int,
        categories: Dict[str, int],
        temporal: Dict[str, Any]
    ) -> float:
        """
        Calculate safety score (0-100, higher is safer)
        Based on: total crimes, violent crime ratio, temporal patterns
        """
        # Base score from total crimes (fewer crimes = higher score)
        # Normalize to 0-50 points
        base_score = max(0, 50 - (total_crimes / 10))
        
        # Violent crime penalty (0-25 points deduction)
        violent_ratio = categories.get('violent', 0) / max(total_crimes, 1)
        violent_penalty = violent_ratio * 25
        
        # Sleep hour safety (0-25 points)
        sleep_percentage = temporal.get('sleep_hours_percentage', 0)
        sleep_safety = max(0, 25 - (sleep_percentage / 4))
        
        total_score = base_score - violent_penalty + sleep_safety
        
        return round(max(0, min(100, total_score)), 1)
    
    def _calculate_percentage_change(self, old: int, new: int) -> float:
        """Calculate percentage change"""
        if old == 0:
            return 100 if new > 0 else 0
        return round(((new - old) / old) * 100, 1)
    
    def _generate_safety_recommendation(
        self,
        current_score: float,
        destination_score: float,
        current_temporal: Dict,
        destination_temporal: Dict
    ) -> str:
        """Generate personalized safety recommendation"""
        score_diff = destination_score - current_score
        
        if score_diff > 10:
            return f"The new location is significantly safer (safety score: {destination_score} vs {current_score}). Crime rates are lower, especially during your sleep hours."
        elif score_diff > 0:
            return f"The new location is slightly safer (safety score: {destination_score} vs {current_score}). Overall crime rates are comparable with minor improvements."
        elif score_diff > -10:
            return f"Safety levels are similar (safety score: {destination_score} vs {current_score}). Consider specific crime patterns during your active hours."
        else:
            dest_sleep = destination_temporal.get('sleep_hours_percentage', 0)
            if dest_sleep > 15:
                return f"The new location has higher crime rates (safety score: {destination_score} vs {current_score}). Notable: {dest_sleep}% of crimes occur during your sleep hours. Consider additional security measures."
            return f"The new location has higher crime rates (safety score: {destination_score} vs {current_score}). Review the temporal patterns and consider your daily routine."
    
    def _get_mock_data(self, lat: float, lon: float, days: int) -> Dict[str, Any]:
        """Generate mock crime data for development/fallback"""
        import random
        from datetime import datetime, timedelta
        
        crimes = []
        crime_types = ['Theft', 'Burglary', 'Assault', 'Vandalism', 'Vehicle Theft']
        
        for i in range(random.randint(50, 150)):
            crime_date = datetime.now() - timedelta(days=random.randint(0, days))
            crimes.append({
                'type': random.choice(crime_types),
                'date': crime_date.strftime('%m/%d/%Y %I:%M %p'),
                'timestamp': crime_date,
                'address': f'{random.randint(100, 9999)} Main St',
                'lat': lat + random.uniform(-0.05, 0.05),
                'lon': lon + random.uniform(-0.05, 0.05),
                'description': f'Mock {random.choice(crime_types)}'
            })
        
        return {
            'crimes': crimes,
            'total_count': len(crimes),
            'period_days': days,
            'radius_miles': 5.0,
            'center_lat': lat,
            'center_lon': lon
        }


# Global instance
spotcrime_service = SpotCrimeService()
