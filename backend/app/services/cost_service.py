import re
from typing import Dict, Any

# US national median monthly expenses (single person, 2024)
_NATIONAL_MEDIAN = 3000.0

# Expense breakdown ratios (sum = 1.0)
_RATIOS = {
    'utilities':     0.10,
    'groceries':     0.15,
    'transportation':0.15,
    'healthcare':    0.10,
    'entertainment': 0.08,
    'miscellaneous': 0.07,
}
# Housing takes the remainder (0.35)
_HOUSING_RATIO = 0.35


class CostService:
    """
    Cost-of-living comparison using static 2024 city/state data.
    No API calls — deterministic, fast, consistent.
    """

    def __init__(self):
        # Total monthly cost estimates (single person, all-in) — 2024 data
        self._city_costs: Dict[str, float] = {
            # High cost
            'manhattan':    5500, 'san francisco': 5200, 'san jose':     4900,
            'honolulu':     4500, 'new york':      4800, 'boston':       4300,
            'seattle':      4100, 'washington dc': 4000, 'washington':   4000,
            'los angeles':  4200, 'brooklyn':      4200, 'san diego':    3900,
            'oakland':      3800,
            # Medium-high
            'denver':       3600, 'portland':      3500, 'austin':       3400,
            'miami':        3400, 'chicago':       3300, 'sacramento':   3100,
            'minneapolis':  3200, 'philadelphia':  3200, 'atlanta':      3100,
            'nashville':    3000, 'raleigh':       3000, 'charlotte':    2900,
            'baltimore':    2800,
            # Medium
            'dallas':       2900, 'houston':       2800, 'las vegas':    2800,
            'riverside':    2800, 'phoenix':       2700, 'orlando':      2700,
            'columbus':     2700, 'san antonio':   2600, 'tampa':        2600,
            'milwaukee':    2600, 'kansas city':   2500, 'pittsburgh':   2500,
            'indianapolis': 2500, 'tucson':        2400, 'fresno':       2500,
            'omaha':        2400,
            # Lower cost
            'detroit':      2400, 'cincinnati':    2400, 'louisville':   2300,
            'cleveland':    2300, 'buffalo':       2300, 'albuquerque':  2300,
            'st louis':     2300, 'memphis':       2200, 'oklahoma city':2200,
            'tulsa':        2100, 'el paso':       2100,
        }

        self._state_costs: Dict[str, float] = {
            'HI': 4200, 'CA': 3800, 'NY': 3500, 'MA': 3600, 'WA': 3400,
            'NJ': 3400, 'MD': 3300, 'CT': 3300, 'CO': 3300, 'OR': 3200,
            'VA': 3100, 'IL': 3000, 'MN': 2900, 'FL': 2900, 'TX': 2800,
            'NV': 2800, 'GA': 2800, 'AZ': 2700, 'NC': 2700, 'PA': 2700,
            'UT': 2600, 'TN': 2600, 'WI': 2600, 'ID': 2500, 'SC': 2500,
            'OH': 2500, 'MI': 2500, 'LA': 2500, 'IN': 2400, 'KY': 2400,
            'MO': 2400, 'KS': 2400, 'NE': 2400, 'IA': 2300, 'AL': 2300,
            'NM': 2300, 'OK': 2200, 'AR': 2200, 'WV': 2200, 'MS': 2100,
            'MT': 2300, 'WY': 2300, 'ND': 2300, 'SD': 2200, 'AK': 3600,
            'VT': 3200, 'NH': 3100, 'ME': 2900, 'RI': 3100, 'DE': 3000,
        }

    # ── Lookup ─────────────────────────────────────────────────────────────────

    def _total_monthly(self, address: str) -> float:
        lower = address.lower()
        for city, cost in self._city_costs.items():
            if city in lower:
                return float(cost)
        match = re.search(r',\s*([A-Z]{2})\b', address)
        if match:
            code = match.group(1)
            if code in self._state_costs:
                return float(self._state_costs[code])
        return _NATIONAL_MEDIAN

    # ── Scoring ────────────────────────────────────────────────────────────────

    def _recommendation(self, diff: float, pct: float) -> str:
        if diff < -200:
            return f"Great savings! You'll save ${abs(diff):.0f}/month (${abs(diff)*12:.0f}/year). Consider investing the difference."
        if diff < 0:
            return f"You'll save ${abs(diff):.0f}/month (${abs(diff)*12:.0f}/year) — a nice financial cushion."
        if diff < 200:
            return f"Costs increase by ${diff:.0f}/month — manageable within most budgets."
        if diff < 500:
            return f"Significant increase: ${diff:.0f}/month (${diff*12:.0f}/year). Budget carefully."
        return f"Major cost increase: ${diff:.0f}/month (${diff*12:.0f}/year). Requires careful financial planning."

    # ── Builder ────────────────────────────────────────────────────────────────

    def _build_location(self, address: str) -> Dict[str, Any]:
        total = self._total_monthly(address)
        cost_index = round(total / _NATIONAL_MEDIAN, 2)

        expenses = {k: round(total * r, 2) for k, r in _RATIOS.items()}
        monthly_rent = round(total * _HOUSING_RATIO, 2)

        return {
            'total_monthly':      round(total, 2),
            'total_annual':       round(total * 12, 2),
            'cost_index':         cost_index,
            'data_source':        'Cost of Living 2025 (City Averages)',
            'housing': {
                'monthly_rent': monthly_rent,
                'annual_rent':  round(monthly_rent * 12, 2),
                'bedrooms':     2,
            },
            'expenses': expenses,
        }

    # ── Public API ─────────────────────────────────────────────────────────────

    def compare_costs(
        self,
        current_address: str,
        destination_address: str,
    ) -> Dict[str, Any]:
        """Compare cost of living between two locations."""
        current = self._build_location(current_address)
        destination = self._build_location(destination_address)

        diff = destination['total_monthly'] - current['total_monthly']
        pct = round(diff / max(current['total_monthly'], 1) * 100, 1)

        return {
            'current':     current,
            'destination': destination,
            'comparison': {
                'monthly_difference':  round(diff, 2),
                'annual_difference':   round(diff * 12, 2),
                'percent_change':      pct,
                'is_more_expensive':   diff > 0,
                'recommendation':      self._recommendation(diff, pct),
            },
        }


cost_service = CostService()
