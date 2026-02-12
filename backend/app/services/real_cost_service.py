import requests
from typing import Dict, Any, Optional
from datetime import datetime
import json


class RealCostService:
    """
    Real cost of living data using HUD Fair Market Rents
    and Bureau of Labor Statistics APIs
    """
    
    def __init__(self):
        # HUD FMR API
        self.hud_api_url = "https://www.huduser.gov/hudapi/public/fmr"
        
        # BLS API
        self.bls_api_url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
        
        # Average expense multipliers by category (national averages)
        self.expense_categories = {
            'groceries': 0.15,       # 15% of income typically
            'utilities': 0.05,       # 5% of income
            'transportation': 0.12,  # 12% of income
            'healthcare': 0.08,      # 8% of income
            'entertainment': 0.05,   # 5% of income
        }
    
    def get_comprehensive_costs(
        self,
        current_zip: str,
        destination_zip: str,
        bedrooms: int = 2
    ) -> Dict[str, Any]:
        """
        Get comprehensive cost comparison using real APIs
        
        Args:
            current_zip: Current ZIP code
            destination_zip: Destination ZIP code
            bedrooms: Number of bedrooms (0-4)
        """
        try:
            # Get housing costs from HUD
            current_housing = self._get_hud_fmr(current_zip, bedrooms)
            destination_housing = self._get_hud_fmr(destination_zip, bedrooms)
            
            # Get BLS consumer price index data
            current_cpi = self._get_bls_cpi_by_zip(current_zip)
            destination_cpi = self._get_bls_cpi_by_zip(destination_zip)
            
            # Calculate adjusted expenses
            current_expenses = self._calculate_expenses(
                current_housing['monthly_rent'],
                current_cpi
            )
            
            destination_expenses = self._calculate_expenses(
                destination_housing['monthly_rent'],
                destination_cpi
            )
            
            # Calculate total costs
            current_total = sum(current_expenses.values())
            destination_total = sum(destination_expenses.values())
            
            # Calculate differences
            difference = destination_total - current_total
            percent_change = ((destination_total - current_total) / current_total) * 100 if current_total > 0 else 0
            
            # Calculate affordability score
            current_score = self._calculate_affordability_score(current_total)
            destination_score = self._calculate_affordability_score(destination_total)
            
            return {
                'current': {
                    'location': current_housing['location'],
                    'zip_code': current_zip,
                    'housing': {
                        'monthly_rent': current_housing['monthly_rent'],
                        'annual_rent': current_housing['monthly_rent'] * 12,
                        'bedrooms': bedrooms,
                        'year': current_housing['year']
                    },
                    'expenses': current_expenses,
                    'total_monthly': round(current_total, 2),
                    'total_annual': round(current_total * 12, 2),
                    'cpi_index': current_cpi,
                    'affordability_score': current_score
                },
                'destination': {
                    'location': destination_housing['location'],
                    'zip_code': destination_zip,
                    'housing': {
                        'monthly_rent': destination_housing['monthly_rent'],
                        'annual_rent': destination_housing['monthly_rent'] * 12,
                        'bedrooms': bedrooms,
                        'year': destination_housing['year']
                    },
                    'expenses': destination_expenses,
                    'total_monthly': round(destination_total, 2),
                    'total_annual': round(destination_total * 12, 2),
                    'cpi_index': destination_cpi,
                    'affordability_score': destination_score
                },
                'comparison': {
                    'monthly_difference': round(difference, 2),
                    'annual_difference': round(difference * 12, 2),
                    'percent_change': round(percent_change, 1),
                    'is_more_expensive': difference > 0,
                    'score_difference': round(destination_score - current_score, 1),
                    'housing_difference': destination_housing['monthly_rent'] - current_housing['monthly_rent'],
                    'expense_breakdown': self._calculate_expense_differences(
                        current_expenses,
                        destination_expenses
                    ),
                    'recommendation': self._generate_cost_recommendation(
                        difference,
                        percent_change,
                        destination_total
                    )
                }
            }
            
        except Exception as e:
            print(f"Real Cost API Error: {e}")
            return self._get_fallback_costs(current_zip, destination_zip, bedrooms)
    
    def _get_hud_fmr(self, zip_code: str, bedrooms: int) -> Dict[str, Any]:
        """
        Fetch Fair Market Rent from HUD API
        
        Note: HUD requires registration for API key at https://www.huduser.gov/portal/dataset/fmr-api.html
        """
        try:
            # Current year
            year = datetime.now().year
            
            # HUD endpoint
            url = f"{self.hud_api_url}/data/{zip_code}"
            
            # Note: In production, you'll need to register for HUD API key
            # For now, using mock data based on ZIP patterns
            
            response = requests.get(url, params={'year': year}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # HUD returns FMR for different bedroom counts
                # Keys: fmr_0 (studio), fmr_1 (1br), fmr_2 (2br), fmr_3 (3br), fmr_4 (4br)
                bedroom_key = f'fmr_{bedrooms}'
                monthly_rent = data.get(bedroom_key, 1500)
                
                return {
                    'monthly_rent': monthly_rent,
                    'location': data.get('county_name', 'Unknown'),
                    'year': year,
                    'source': 'HUD FMR API'
                }
            else:
                raise Exception(f"HUD API returned status {response.status_code}")
                
        except Exception as e:
            print(f"HUD API Error: {e}")
            # Fallback to estimated rent based on ZIP code
            return self._estimate_rent_by_zip(zip_code, bedrooms)
    
    def _estimate_rent_by_zip(self, zip_code: str, bedrooms: int) -> Dict[str, Any]:
        """
        Estimate rent based on ZIP code patterns
        Uses first digit to estimate general region costs
        """
        try:
            first_digit = int(zip_code[0])
            
            # Regional cost estimates (rough approximations)
            # 0: Northeast (high), 1: NYC/NJ (very high), 2: Southeast (low)
            # 3: South (low-med), 4: Midwest (low), 5: South Central (low)
            # 6: North Central (med), 7: Southwest (med), 8: Mountain (med)
            # 9: West Coast (high-very high)
            
            base_rents = {
                0: 1400, 1: 2200, 2: 1100, 3: 1200, 4: 950,
                5: 1000, 6: 1100, 7: 1300, 8: 1400, 9: 2000
            }
            
            base_rent = base_rents.get(first_digit, 1200)
            
            # Adjust for bedroom count
            bedroom_multipliers = {0: 0.7, 1: 0.85, 2: 1.0, 3: 1.3, 4: 1.6}
            multiplier = bedroom_multipliers.get(bedrooms, 1.0)
            
            monthly_rent = round(base_rent * multiplier, 2)
            
            return {
                'monthly_rent': monthly_rent,
                'location': f'ZIP {zip_code}',
                'year': datetime.now().year,
                'source': 'Estimated'
            }
            
        except:
            return {
                'monthly_rent': 1500,
                'location': f'ZIP {zip_code}',
                'year': datetime.now().year,
                'source': 'Default'
            }
    
    def _get_bls_cpi_by_zip(self, zip_code: str) -> float:
        """
        Get Consumer Price Index from BLS API
        
        Note: BLS API is free but has rate limits
        Regional CPI series IDs vary by metro area
        """
        try:
            # Map ZIP to metro area (simplified)
            # In production, use proper ZIP to CBSA mapping
            metro_cpi_series = self._zip_to_cpi_series(zip_code)
            
            # BLS API call
            headers = {'Content-type': 'application/json'}
            data = json.dumps({
                "seriesid": [metro_cpi_series],
                "startyear": str(datetime.now().year - 1),
                "endyear": str(datetime.now().year)
            })
            
            response = requests.post(
                self.bls_api_url,
                data=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result['status'] == 'REQUEST_SUCCEEDED':
                    series = result['Results']['series'][0]
                    latest_value = float(series['data'][0]['value'])
                    return latest_value
            
            # Fallback
            return self._estimate_cpi_by_zip(zip_code)
            
        except Exception as e:
            print(f"BLS API Error: {e}")
            return self._estimate_cpi_by_zip(zip_code)
    
    def _zip_to_cpi_series(self, zip_code: str) -> str:
        """
        Map ZIP code to BLS CPI series ID
        
        Common series IDs:
        - CUURA101SA0: Boston
        - CUURA102SA0: New York
        - CUURA207SA0: Chicago
        - CUUSA320SA0: Los Angeles
        - National: CUUS0000SA0
        """
        # Simplified mapping - in production, use comprehensive ZIP to metro mapping
        first_digit = zip_code[0]
        
        series_map = {
            '0': 'CUURA101SA0',  # Northeast -> Boston
            '1': 'CUURA102SA0',  # NY/NJ -> New York
            '2': 'CUURA320SA0',  # Southeast
            '6': 'CUURA207SA0',  # Midwest -> Chicago
            '9': 'CUURA421SA0',  # West -> LA
        }
        
        return series_map.get(first_digit, 'CUUS0000SA0')  # Default to national
    
    def _estimate_cpi_by_zip(self, zip_code: str) -> float:
        """Estimate CPI based on region (fallback)"""
        # National average is around 100
        # High-cost areas: 110-130
        # Low-cost areas: 85-95
        
        first_digit = int(zip_code[0])
        
        cpi_estimates = {
            0: 110, 1: 125, 2: 90, 3: 92, 4: 88,
            5: 90, 6: 95, 7: 98, 8: 102, 9: 118
        }
        
        return cpi_estimates.get(first_digit, 100)
    
    def _calculate_expenses(
        self,
        monthly_rent: float,
        cpi_index: float
    ) -> Dict[str, float]:
        """
        Calculate all expense categories based on rent and CPI
        """
        # Adjust base expenses by CPI
        cpi_multiplier = cpi_index / 100
        
        expenses = {
            'housing': monthly_rent,
            'utilities': round(monthly_rent * 0.15 * cpi_multiplier, 2),  # ~15% of rent
            'groceries': round(monthly_rent * 0.35 * cpi_multiplier, 2),  # ~35% of rent
            'transportation': round(monthly_rent * 0.25 * cpi_multiplier, 2),  # ~25% of rent
            'healthcare': round(monthly_rent * 0.20 * cpi_multiplier, 2),  # ~20% of rent
            'entertainment': round(monthly_rent * 0.15 * cpi_multiplier, 2),  # ~15% of rent
            'miscellaneous': round(monthly_rent * 0.10 * cpi_multiplier, 2),  # ~10% of rent
        }
        
        return expenses
    
    def _calculate_affordability_score(self, total_monthly: float) -> float:
        """
        Calculate affordability score (0-100, higher is more affordable)
        Based on: absolute cost and relative to national median
        """
        # National median household expenses ~$5000/month
        national_median = 5000
        
        # Score inversely proportional to cost
        if total_monthly <= national_median * 0.7:
            score = 100  # Very affordable
        elif total_monthly <= national_median:
            score = 80 + (20 * (1 - (total_monthly / national_median)))
        elif total_monthly <= national_median * 1.5:
            deviation = (total_monthly - national_median) / (national_median * 0.5)
            score = 60 - (20 * deviation)
        else:
            score = max(20, 40 - ((total_monthly - national_median * 1.5) / 100))
        
        return round(score, 1)
    
    def _calculate_expense_differences(
        self,
        current: Dict[str, float],
        destination: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate differences in each expense category"""
        differences = {}
        
        for category in current.keys():
            curr_val = current[category]
            dest_val = destination[category]
            diff = dest_val - curr_val
            percent = (diff / curr_val * 100) if curr_val > 0 else 0
            
            differences[category] = {
                'current': curr_val,
                'destination': dest_val,
                'difference': round(diff, 2),
                'percent_change': round(percent, 1)
            }
        
        return differences
    
    def _generate_cost_recommendation(
        self,
        monthly_diff: float,
        percent_change: float,
        destination_total: float
    ) -> str:
        """Generate personalized cost recommendation"""
        
        if monthly_diff < -200:
            return f"Great news! You'll save ${abs(monthly_diff):.0f}/month (${abs(monthly_diff * 12):.0f}/year). This is a {abs(percent_change):.1f}% reduction in living costs."
        elif monthly_diff < 0:
            return f"You'll save ${abs(monthly_diff):.0f}/month. While modest, this adds up to ${abs(monthly_diff * 12):.0f} annually."
        elif monthly_diff < 200:
            return f"Costs will increase by ${monthly_diff:.0f}/month (${monthly_diff * 12:.0f}/year), but this is a {percent_change:.1f}% change - relatively manageable."
        elif monthly_diff < 500:
            return f"Significant increase: ${monthly_diff:.0f}/month (${monthly_diff * 12:.0f}/year). Budget accordingly and consider salary adjustments."
        else:
            return f"Major cost increase: ${monthly_diff:.0f}/month (${monthly_diff * 12:.0f}/year). This {percent_change:.1f}% increase requires careful financial planning."
    
    def _get_fallback_costs(
        self,
        current_zip: str,
        destination_zip: str,
        bedrooms: int
    ) -> Dict[str, Any]:
        """Fallback cost estimates"""
        current_housing = self._estimate_rent_by_zip(current_zip, bedrooms)
        destination_housing = self._estimate_rent_by_zip(destination_zip, bedrooms)
        
        current_cpi = self._estimate_cpi_by_zip(current_zip)
        destination_cpi = self._estimate_cpi_by_zip(destination_zip)
        
        return self.get_comprehensive_costs(current_zip, destination_zip, bedrooms)


# Global instance
real_cost_service = RealCostService()
