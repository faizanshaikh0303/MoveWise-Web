import httpx
from typing import Dict, Any, Optional


class CostService:
    """
    Service to get cost of living data.
    Uses comprehensive city and state data for accuracy.
    """
    
    def __init__(self):
        # Comprehensive city cost data (monthly, single person)
        # Source: Numbeo, BestPlaces, and other cost of living indices (2024 data)
        self.city_costs = {
            # Major Tech Hubs (High Cost)
            'san francisco': 5200,
            'san jose': 4900,
            'new york': 4800,
            'manhattan': 5500,
            'brooklyn': 4200,
            'boston': 4300,
            'seattle': 4100,
            'washington dc': 4000,
            'washington': 4000,
            'los angeles': 4200,
            'san diego': 3900,
            'oakland': 3800,
            'honolulu': 4500,
            
            # Medium-High Cost Cities
            'denver': 3600,
            'portland': 3500,
            'miami': 3400,
            'chicago': 3300,
            'philadelphia': 3200,
            'atlanta': 3100,
            'austin': 3400,
            'raleigh': 3000,
            'charlotte': 2900,
            'nashville': 3000,
            'minneapolis': 3200,
            'baltimore': 2800,
            
            # Medium Cost Cities
            'dallas': 2900,
            'houston': 2800,
            'phoenix': 2700,
            'san antonio': 2600,
            'las vegas': 2800,
            'orlando': 2700,
            'tampa': 2600,
            'sacramento': 3100,
            'riverside': 2800,
            'columbus': 2700,
            'indianapolis': 2500,
            'milwaukee': 2600,
            'kansas city': 2500,
            'omaha': 2400,
            
            # Lower Cost Cities
            'detroit': 2400,
            'cleveland': 2300,
            'pittsburgh': 2500,
            'cincinnati': 2400,
            'st louis': 2300,
            'memphis': 2200,
            'louisville': 2300,
            'oklahoma city': 2200,
            'tulsa': 2100,
            'albuquerque': 2300,
            'el paso': 2100,
            'tucson': 2400,
            'fresno': 2500,
            'buffalo': 2300,
        }
        
        # State average costs (for cities not in the list above)
        self.state_costs = {
            'california': 3800,
            'new york': 3500,
            'massachusetts': 3600,
            'washington': 3400,
            'hawaii': 4200,
            'colorado': 3300,
            'oregon': 3200,
            'maryland': 3300,
            'new jersey': 3400,
            'connecticut': 3300,
            'virginia': 3100,
            'illinois': 3000,
            'texas': 2800,
            'florida': 2900,
            'arizona': 2700,
            'nevada': 2800,
            'georgia': 2800,
            'north carolina': 2700,
            'tennessee': 2600,
            'pennsylvania': 2700,
            'ohio': 2500,
            'michigan': 2500,
            'minnesota': 2900,
            'wisconsin': 2600,
            'missouri': 2400,
            'indiana': 2400,
            'louisiana': 2500,
            'kentucky': 2400,
            'oklahoma': 2200,
            'new mexico': 2300,
            'kansas': 2400,
            'nebraska': 2400,
            'iowa': 2300,
            'utah': 2600,
            'idaho': 2500,
            'south carolina': 2500,
            'alabama': 2300,
            'arkansas': 2200,
            'mississippi': 2100,
            'west virginia': 2200,
        }
    
    def estimate_cost_of_living(self, address: str) -> float:
        """
        Estimate monthly cost of living for an address.
        Includes: rent, food, transportation, utilities, healthcare, entertainment.
        """
        
        address_lower = address.lower()
        
        # First, try to match specific cities
        for city, cost in self.city_costs.items():
            if city in address_lower:
                return cost
        
        # Then try to match states
        for state, cost in self.state_costs.items():
            if state in address_lower:
                return cost
        
        # Default to US median
        return 3000
    
    def get_cost_breakdown(self, address: str) -> Dict[str, float]:
        """
        Get detailed cost breakdown.
        Returns estimated costs for different categories.
        """
        total_cost = self.estimate_cost_of_living(address)
        
        # Typical breakdown percentages
        breakdown = {
            'housing': total_cost * 0.35,      # 35% - Rent/mortgage
            'food': total_cost * 0.15,         # 15% - Groceries & dining
            'transportation': total_cost * 0.15, # 15% - Car/transit
            'utilities': total_cost * 0.10,    # 10% - Electric, water, internet
            'healthcare': total_cost * 0.10,   # 10% - Insurance, medical
            'entertainment': total_cost * 0.08, # 8% - Going out, hobbies
            'savings': total_cost * 0.07       # 7% - Emergency fund
        }
        
        return breakdown
    
    def compare_costs(
        self,
        current_address: str,
        destination_address: str
    ) -> Dict[str, Any]:
        """Compare cost of living between two locations"""
        
        current_cost = self.estimate_cost_of_living(current_address)
        destination_cost = self.estimate_cost_of_living(destination_address)
        
        # Get breakdowns
        current_breakdown = self.get_cost_breakdown(current_address)
        destination_breakdown = self.get_cost_breakdown(destination_address)
        
        change_percentage = ((destination_cost - current_cost) / current_cost * 100) if current_cost > 0 else 0
        monthly_difference = destination_cost - current_cost
        annual_difference = monthly_difference * 12
        
        # Generate tip based on cost change
        if change_percentage > 15:
            tip = f"Budget carefully: your costs will increase by ${abs(monthly_difference):.0f}/month (${abs(annual_difference):.0f}/year). Plan for higher housing and living expenses."
        elif change_percentage > 5:
            tip = f"Slight increase of ${abs(monthly_difference):.0f}/month. Review your budget for the ${abs(annual_difference):.0f}/year increase."
        elif change_percentage < -15:
            tip = f"Great savings! You could save ${abs(monthly_difference):.0f}/month (${abs(annual_difference):.0f}/year). Consider investing the difference or upgrading your lifestyle."
        elif change_percentage < -5:
            tip = f"You'll save ${abs(monthly_difference):.0f}/month (${abs(annual_difference):.0f}/year) - a nice financial cushion."
        else:
            tip = "Similar cost of living makes budgeting straightforward for your move."
        
        return {
            'current_cost': round(current_cost, 2),
            'destination_cost': round(destination_cost, 2),
            'change_percentage': round(change_percentage, 1),
            'monthly_difference': round(monthly_difference, 2),
            'annual_difference': round(annual_difference, 2),
            'current_breakdown': {k: round(v, 2) for k, v in current_breakdown.items()},
            'destination_breakdown': {k: round(v, 2) for k, v in destination_breakdown.items()},
            'tip': tip,
            'data_source': 'Aggregated cost of living data (2024)'
        }


cost_service = CostService()