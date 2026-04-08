import re
import math
import asyncio
import httpx
from datetime import datetime
from typing import Any, Dict, List, Optional

# Fixed hourly crime weight distribution (index = hour 0-23)
# Based on FBI UCR patterns: higher weight = more crime
_HOUR_WEIGHTS = [3,3,2,2,2,2,3,4,3,3,3,3,3,3,3,4,4,5,6,7,8,7,5,4]
_TOTAL_WEIGHT = sum(_HOUR_WEIGHTS)  # 92

# Fallback category ratios when FBI category endpoints are unavailable (FBI UCR averages)
# Property is split into its components — larceny, burglary, other_property — to avoid
# double-counting (larceny and burglary are subsets of property crime).
_CATEGORY_RATIOS = {
    'violent':        0.20,
    'larceny':        0.48,
    'burglary':       0.14,
    'other_property': 0.14,  # motor vehicle theft, arson, etc.
    'other':          0.04,
}

# Local population assumed for a walkable 1–2 mile radius around the address
_LOCAL_POP = 25_000


class CrimeService:
    """
    Crime comparison service.
    Primary: FBI Crime Data Explorer API (real data).
    Fallback: static FBI UCR 2022 city/state averages.
    """

    def __init__(self):
        self.fbi_api_base = "https://api.usa.gov/crime/fbi/cde"
        try:
            from app.core.config import settings
            self.api_key = getattr(settings, 'FBI_API_KEY', None)
        except Exception:
            self.api_key = None

        self._city_rates: Dict[str, float] = {
            'memphis': 8912, 'st louis': 8234, 'detroit': 7234,
            'baltimore': 7567, 'oakland': 7721,
            'indianapolis': 6745, 'minneapolis': 6789, 'seattle': 6500,
            'san francisco': 6168, 'atlanta': 6234, 'denver': 6321,
            'miami': 5890, 'chicago': 5218, 'houston': 5656,
            'portland': 5678, 'san antonio': 5234, 'dallas': 5235,
            'philadelphia': 4820, 'jacksonville': 4892, 'charlotte': 4890,
            'phoenix': 4621, 'fort worth': 4567, 'austin': 4321,
            'columbus': 4123, 'washington': 5100, 'los angeles': 5798,
            'san diego': 3348, 'san jose': 2865, 'boston': 2890,
            'new york': 2331, 'nyc': 2331,
        }

        # Static FBI UCR 2022 crime rates per 100k (violent + property combined), all 50 states
        self._state_rates: Dict[str, float] = {
            'NM': 4700, 'AK': 4600, 'LA': 4300, 'OK': 4300, 'SC': 4200,
            'TX': 4200, 'AL': 4200, 'MO': 4500, 'NV': 4800, 'CO': 4300,
            'AZ': 4400, 'CA': 4500, 'AR': 4100, 'GA': 4100, 'WA': 4100,
            'MD': 4000, 'OR': 4000, 'MI': 4000, 'MT': 3900, 'FL': 3900,
            'TN': 3900, 'MS': 3800, 'KS': 3400, 'WV': 3400, 'IN': 3500,
            'NC': 3500, 'UT': 3500, 'IL': 3600, 'OH': 3300, 'MN': 3200,
            'SD': 3200, 'DE': 3200, 'NE': 3000, 'KY': 3000, 'PA': 2900,
            'WI': 2900, 'HI': 2900, 'IA': 2800, 'ND': 2800, 'VA': 2800,
            'NY': 2800, 'RI': 2700, 'WY': 2600, 'ID': 2500, 'NJ': 2500,
            'MA': 2200, 'ME': 2200, 'CT': 2100, 'NH': 2000, 'VT': 2000,
        }

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _parse_hour_range(self, time_str: str) -> set:
        """Parse 'HH:MM - HH:MM' into a set of hours, handling midnight wrap-around."""
        try:
            start_str, end_str = time_str.split(' - ')
            start = int(start_str.split(':')[0])
            end   = int(end_str.split(':')[0])
            if start < end:
                return set(range(start, end))
            else:  # wraps midnight (e.g. 23:00 - 07:00)
                return set(range(start, 24)) | set(range(0, end))
        except Exception:
            return set()

    def _state_from_address(self, address: str) -> Optional[str]:
        """Extract a 2-letter US state code from a geocoded address string."""
        # Google-geocoded addresses look like "..., Atlanta, GA 30313, USA"
        match = re.search(r',\s*([A-Z]{2})\b', address)
        if match:
            code = match.group(1)
            if code not in ('US',):
                return code
        return None

    @staticmethod
    def _year_window(year: int) -> tuple:
        """
        Return (from_str, to_str) for a 3-month window within a specific year,
        ending at the same month as today (mirrors current calendar position).
        e.g. April 2026, year=2024 → from='02-2024', to='04-2024'
        """
        cm = datetime.now().month
        from_month = max(1, cm - 2)   # 3 months inclusive: cm-2, cm-1, cm
        return f"{from_month:02d}-{year}", f"{cm:02d}-{year}"

    @staticmethod
    def _flatten_agency_list(raw: Any) -> List[dict]:
        """Flatten {"COUNTY": [...agencies...]} county-keyed response into a flat list."""
        if isinstance(raw, list):
            return raw
        if isinstance(raw, dict):
            result = []
            for agencies in raw.values():
                if isinstance(agencies, list):
                    result.extend(agencies)
            return result
        return []

    def _nearest_agency(self, agencies: List[dict], lat: float, lng: float) -> Optional[dict]:
        """
        Find the closest NIBRS-reporting agency to (lat, lng) using Haversine distance.
        Within 10km, prefers City type over County. Beyond 10km, returns absolute nearest.
        Skips agencies with no coordinates or is_nibrs=False.
        """
        def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
            R = 6_371_000
            d_lat = (lat2 - lat1) * math.pi / 180
            d_lng = (lng2 - lng1) * math.pi / 180
            a = (math.sin(d_lat / 2) ** 2 +
                 math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) *
                 math.sin(d_lng / 2) ** 2)
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        def _type_score(a: dict) -> int:
            t = a.get('agency_type_name', '')
            if t == 'City':   return 2
            if t == 'County': return 1
            return 0

        candidates = []
        for a in agencies:
            if not a.get('is_nibrs'):
                continue
            a_lat = a.get('latitude')
            a_lng = a.get('longitude')
            if a_lat is None or a_lng is None:
                continue
            dist = _haversine(lat, lng, a_lat, a_lng)
            candidates.append((dist, a))

        if not candidates:
            return None

        nearby = [(d, a) for d, a in candidates if d <= 10_000]
        if nearby:
            # within 10km: prefer City > County, then closest
            nearby.sort(key=lambda x: (-_type_score(x[1]), x[0]))
            return nearby[0][1]

        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    # ── FBI API ────────────────────────────────────────────────────────────────

    def _extract_rate(self, data: Any) -> Optional[float]:
        """
        Pull an annual crime rate (per 100k) from an FBI CDE summarized state API response.
        Response shape: {'offenses': {'rates': {'State Offenses': {'01-2025': 32.66, ...}}}}
        Each value is a monthly rate per 100k — sum all months for the annual rate.
        """
        if not data:
            return None

        if isinstance(data, dict) and 'offenses' in data:
            rates_dict = data['offenses'].get('rates', {})
            monthly_values = [
                v for month_data in rates_dict.values()
                if isinstance(month_data, dict)
                for v in month_data.values()
                if v is not None and isinstance(v, (int, float)) and v > 0
            ]
            if monthly_values:
                return round(sum(monthly_values), 1)

        return None

    def _extract_agency_rate(self, data: Any, agency_name: str) -> tuple:
        """
        Extract annualized rate per 100k + raw monthly dict from offenses.rates.
        Monthly rates (already per 100k) are summed and annualized: sum * (12 / n).
        Returns (annualized_rate, monthly_dict) or (None, {}) if no usable data.
        monthly_dict shape: {"02-2024": 3.16, "03-2024": 1.58, "04-2024": 7.89}
        """
        if not data or not isinstance(data, dict):
            print(f"   [extract] {agency_name}: data missing or not a dict ({type(data)})")
            return None, {}
        rates_dict = data.get('offenses', {}).get('rates', {})
        agency_key = f"{agency_name} Offenses"
        available_keys = list(rates_dict.keys())
        monthly_raw = rates_dict.get(agency_key)
        if not monthly_raw or not isinstance(monthly_raw, dict):
            print(f"   [extract] {agency_name}: key '{agency_key}' not found. Available: {available_keys}")
            return None, {}
        monthly = {k: v for k, v in monthly_raw.items()
                   if v is not None and isinstance(v, (int, float)) and v > 0}
        if not monthly:
            print(f"   [extract] {agency_name}: monthly_raw has no valid numeric values: {monthly_raw}")
            return None, {}
        values = list(monthly.values())
        annualized = round(sum(values) * (12 / len(values)), 1)
        print(f"   [extract] {agency_name}: annualized={annualized:.1f}/100k from {len(values)} months")
        return annualized, monthly

    async def _fetch_agency_list(self, state: str) -> Optional[List[dict]]:
        """Fetch and cache all FBI reporting agencies for a state as a flat list."""
        from app.core.redis_cache import cache_get, cache_set, CACHE_7_DAYS

        cache_key = f"fbi:agency:{state.upper()}"
        cached = cache_get(cache_key)
        if cached:
            return cached
        if not self.api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self.fbi_api_base}/agency/byStateAbbr/{state.upper()}",
                    params={'API_KEY': self.api_key}
                )
            if resp.status_code != 200:
                print(f"   WARNING FBI agency list {state}: HTTP {resp.status_code}")
                return None
            agencies = self._flatten_agency_list(resp.json())
            if agencies:
                cache_set(cache_key, agencies, ttl=CACHE_7_DAYS)
                print(f"   FBI agency list {state}: {len(agencies)} agencies cached")
            return agencies or None
        except Exception as e:
            print(f"   WARNING FBI agency list error ({state}): {e}")
            return None

    async def _fetch_agency_rate(self, state: str, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """
        Find the nearest NIBRS agency to (lat, lng) and return its annualized crime rates.
        Queries V, P, LAR, BUR offense categories. Returns None on any failure → caller falls back to state.
        """
        from app.core.redis_cache import cache_get, cache_set, CACHE_7_DAYS

        coord_cache_key = f"fbi:agency_rate:{state.upper()}:{round(lat, 3)}:{round(lng, 3)}"
        cached = cache_get(coord_cache_key)
        if cached:
            print(f"   CACHE HIT agency rate {state} ({lat:.3f},{lng:.3f})")
            return cached

        agencies = await self._fetch_agency_list(state)
        if not agencies:
            return None

        agency = self._nearest_agency(agencies, lat, lng)
        if not agency:
            print(f"   FBI agency: no nearby NIBRS agency for ({lat:.3f},{lng:.3f})")
            return None

        ori  = agency['ori']
        name = agency['agency_name']
        print(f"   FBI agency selected: {name} (ORI={ori})")

        cy = datetime.now().year
        for year in [cy - 2, cy - 3]:
            from_str, to_str = self._year_window(year)
            params: Dict[str, Any] = {'from': from_str, 'to': to_str, 'API_KEY': self.api_key}
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    v_resp = await client.get(f"{self.fbi_api_base}/summarized/agency/{ori}/V",   params=params)
                    p_resp = await client.get(f"{self.fbi_api_base}/summarized/agency/{ori}/P",   params=params)
                    l_resp = await client.get(f"{self.fbi_api_base}/summarized/agency/{ori}/LAR", params=params)
                    d_resp = await client.get(f"{self.fbi_api_base}/summarized/agency/{ori}/BUR", params=params)

                print(f"   FBI agency {name} {year}: V={v_resp.status_code} P={p_resp.status_code} LAR={l_resp.status_code} BUR={d_resp.status_code}")

                def _rate_monthly(resp, label: str) -> tuple:
                    if resp.status_code != 200:
                        print(f"   [agency] {name} {label}: HTTP {resp.status_code} — {resp.text[:200]}")
                        return None, {}
                    return self._extract_agency_rate(resp.json(), name)

                v_rate, v_monthly = _rate_monthly(v_resp, 'V')
                p_rate, p_monthly = _rate_monthly(p_resp, 'P')
                l_rate, l_monthly = _rate_monthly(l_resp, 'LAR')
                d_rate, d_monthly = _rate_monthly(d_resp, 'BUR')

                if v_rate is None and p_rate is None:
                    print(f"   WARNING FBI agency {name} {year}: no usable rates (V={v_rate}, P={p_rate}), trying year-3")
                    continue

                v     = v_rate or 0.0
                p     = p_rate or round(v * 3.5, 1)
                total = round(v + p, 1)
                if total <= 0:
                    continue

                result = {
                    'total':    total,
                    'violent':  v,
                    'property': p,
                    'larceny':  l_rate,
                    'burglary': d_rate,
                    'source':   f'FBI CDE Agency ({name}, {from_str}–{to_str})',
                    'monthly': {
                        'violent':  v_monthly,
                        'property': p_monthly,
                        'larceny':  l_monthly,
                        'burglary': d_monthly,
                    },
                }
                cache_set(coord_cache_key, result, ttl=CACHE_7_DAYS)
                print(f"   OK FBI agency {name} {year} ({from_str}→{to_str}): {v:.0f}+{p:.0f}={total:.0f}/100k")
                return result

            except Exception as e:
                print(f"   WARNING FBI agency error ({ori} {year}): {e}")
                continue

        print(f"   FBI agency {name}: no data for year-2 or year-3, falling back to state")
        return None

    async def _fetch_fbi_rates(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Fetch crime rates per 100k from the FBI CDE API for all categories.
        Returns a dict with violent, property, larceny, burglary, total, source.
        """
        state = self._state_from_address(address)
        if not state:
            print(f"   WARNING FBI API: could not extract state from '{address}'")
            return None

        cy = datetime.now().year
        for year in [cy - 2, cy - 3]:
            from_str, to_str = self._year_window(year)
            params: Dict[str, Any] = {'from': from_str, 'to': to_str}
            if self.api_key:
                params['api_key'] = self.api_key

            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    v_resp, p_resp, l_resp, d_resp = await asyncio.gather(
                        client.get(f"{self.fbi_api_base}/summarized/state/{state}/V", params=params),
                        client.get(f"{self.fbi_api_base}/summarized/state/{state}/P", params=params),
                        client.get(f"{self.fbi_api_base}/summarized/state/{state}/larceny", params=params),
                        client.get(f"{self.fbi_api_base}/summarized/state/{state}/burglary", params=params),
                    )

                print(f"   FBI API {state} {year} ({from_str}→{to_str}): V={v_resp.status_code} P={p_resp.status_code}")

                v_data = v_resp.json() if v_resp.status_code == 200 else None
                p_data = p_resp.json() if p_resp.status_code == 200 else None
                l_data = l_resp.json() if l_resp.status_code == 200 else None
                d_data = d_resp.json() if d_resp.status_code == 200 else None

                violent_rate  = self._extract_rate(v_data)
                property_rate = self._extract_rate(p_data)
                larceny_rate  = self._extract_rate(l_data)
                burglary_rate = self._extract_rate(d_data)

                if violent_rate is None and property_rate is None:
                    print(f"   WARNING FBI API: no data for {state} {year}, trying year-3")
                    continue

                v = violent_rate or 0.0
                p = property_rate or round(v * 3.5, 1)
                total = round(v + p, 1)

                if total > 0:
                    cats = []
                    if larceny_rate:  cats.append(f"larceny={larceny_rate:.0f}")
                    if burglary_rate: cats.append(f"burglary={burglary_rate:.0f}")
                    print(f"   OK FBI API {state} {year}: {v:.0f}+{p:.0f}={total:.0f}/100k ({', '.join(cats) or 'no category data'})")
                    return {
                        'total':    total,
                        'violent':  v,
                        'property': p,
                        'larceny':  larceny_rate,
                        'burglary': burglary_rate,
                        'source':   f'FBI Crime Data Explorer ({from_str}–{to_str})',
                        'monthly':  {},   # state endpoint doesn't return per-agency monthly breakdown
                    }

            except Exception as e:
                print(f"   WARNING FBI API error ({state} {year}): {e}")
                continue

        return None

    def _static_rate(self, address: str) -> float:
        """Return a deterministic crime rate (per 100k) from static FBI UCR 2022 data."""
        lower = address.lower()
        for city, rate in self._city_rates.items():
            if city in lower:
                return rate
        state = self._state_from_address(address)
        if state and state in self._state_rates:
            return self._state_rates[state]
        return 3500.0  # US national average

    # ── Core metrics ───────────────────────────────────────────────────────────

    async def _get_rates(self, address: str, lat: Optional[float] = None, lng: Optional[float] = None) -> Dict[str, Any]:
        """Return a dict with total rate, source, and per-category rates.
        Priority: agency-level (if coords + API key) → state-level → static fallback."""
        from app.core.redis_cache import cache_get, cache_set, CACHE_7_DAYS

        state = self._state_from_address(address)

        # ── 1. Agency-level rate (most accurate) ──────────────────────────────
        if state and lat is not None and lng is not None and self.api_key:
            agency_result = await self._fetch_agency_rate(state, lat, lng)
            if agency_result:
                return agency_result
            print(f"   FBI agency fallback → state-level for ({lat:.3f},{lng:.3f})")

        # ── 2. State-level rate ────────────────────────────────────────────────
        if state:
            cached = cache_get(self._cache_key(state))
            if cached:
                print(f"   CACHE HIT FBI {state}")
                return cached

        result = await self._fetch_fbi_rates(address)
        if result:
            if state:
                cache_set(self._cache_key(state), result, ttl=CACHE_7_DAYS)
                print(f"   CACHE SET FBI {state} (7 days)")
            return result

        # ── 3. Static fallback ─────────────────────────────────────────────────
        rate = self._static_rate(address)
        return {
            'total':    rate,
            'violent':  None,
            'property': None,
            'larceny':  None,
            'burglary': None,
            'source':   'FBI UCR 2022 (City Averages)',
            'monthly':  {},
        }

    def _rate_to_safety_score(self, rate: float) -> float:
        """Convert crime rate per 100k to safety score 0-100 (higher = safer)."""
        if rate < 1500:  return 90.0
        if rate < 2500:  return 80.0
        if rate < 3500:  return 70.0  # near national average
        if rate < 4500:  return 60.0
        if rate < 5500:  return 50.0
        if rate < 6500:  return 40.0
        if rate < 7500:  return 30.0
        return 20.0

    def _build_location_data(self, fbi: Dict[str, Any], user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build the complete location crime dict from FBI rate data.
        Uses real FBI category rates when available; falls back to national ratios.
        Schedule-based aggregates use the user's actual work/sleep hours when provided.
        """
        rate   = fbi['total']
        source = fbi['source']

        # 30-day crime count for a typical local population radius
        total_crimes = round(rate / 100_000 * _LOCAL_POP / 12)

        def _cat_crimes(cat_rate: Optional[float], fallback_ratio: float) -> int:
            if cat_rate is not None:
                return round(cat_rate / 100_000 * _LOCAL_POP / 12)
            return round(total_crimes * fallback_ratio)

        violent_crimes  = _cat_crimes(fbi.get('violent'),  _CATEGORY_RATIOS['violent'])
        larceny_crimes  = _cat_crimes(fbi.get('larceny'),  _CATEGORY_RATIOS['larceny'])
        burglary_crimes = _cat_crimes(fbi.get('burglary'), _CATEGORY_RATIOS['burglary'])

        # other_property = property crimes not covered by larceny or burglary (MVT, arson, etc.)
        # Derived from real property rate when available; falls back to ratio.
        if fbi.get('property') is not None:
            property_crimes = round(fbi['property'] / 100_000 * _LOCAL_POP / 12)
            other_property = max(0, property_crimes - larceny_crimes - burglary_crimes)
        else:
            other_property = _cat_crimes(None, _CATEGORY_RATIOS['other_property'])

        categories = {
            'violent':        violent_crimes,
            'larceny':        larceny_crimes,
            'burglary':       burglary_crimes,
            'other_property': other_property,
            'other':          round(total_crimes * _CATEGORY_RATIOS['other']),
        }

        # Hourly distribution (deterministic, scaled to total_crimes)
        hourly = [round(total_crimes * w / _TOTAL_WEIGHT) for w in _HOUR_WEIGHTS]

        # Schedule-based aggregates derived from user profile, with defaults
        prefs = user_preferences or {}
        sleep_hours   = self._parse_hour_range(prefs.get('sleep_hours', '23:00 - 07:00')) or \
                        (set(range(23, 24)) | set(range(0, 7)))
        work_hours    = self._parse_hour_range(prefs.get('work_hours', '9:00 - 17:00')) or \
                        set(range(9, 17))
        # Commute: 2 hours bracketing the start and end of the work window
        work_start    = min(work_hours) if work_hours else 9
        work_end      = max(work_hours) + 1 if work_hours else 17
        commute_hours = {(work_start - 2) % 24, (work_start - 1) % 24,
                         work_end % 24, (work_end + 1) % 24}

        crimes_sleep   = sum(hourly[h] for h in sleep_hours)
        crimes_work    = sum(hourly[h] for h in work_hours)
        crimes_commute = sum(hourly[h] for h in commute_hours)

        max_h = max(hourly)
        threshold = max_h * 0.7
        peak_hours = [h for h, c in enumerate(hourly) if c >= threshold]

        return {
            'total_crimes':    total_crimes,
            'daily_average':   round(total_crimes / 30, 2),
            'crime_rate_per_100k': round(rate, 1),
            'safety_score':    self._rate_to_safety_score(rate),
            'data_source':     source,
            'categories':      categories,
            'monthly':         fbi.get('monthly', {}),
            'temporal_analysis': {
                'hourly_distribution':       hourly,
                'peak_hours':                peak_hours,
                'crimes_during_sleep_hours': crimes_sleep,
                'crimes_during_work_hours':  crimes_work,
                'crimes_during_commute':     crimes_commute,
            },
        }

    def _recommendation(self, current_score: float, dest_score: float, dest_rate: float) -> str:
        diff = dest_score - current_score
        if diff > 10:
            return f"The destination is significantly safer (safety score {dest_score:.0f} vs {current_score:.0f}). Crime rate: {dest_rate:.0f}/100k."
        if diff > 0:
            return f"The destination is slightly safer (safety score {dest_score:.0f} vs {current_score:.0f})."
        if diff > -10:
            return f"Safety levels are similar between locations (safety scores {dest_score:.0f} vs {current_score:.0f})."
        return f"The destination has higher crime rates. Safety score {dest_score:.0f} vs {current_score:.0f}. Consider reviewing local safety resources."

    # ── Cache key ──────────────────────────────────────────────────────────────

    @staticmethod
    def _cache_key(state: str) -> str:
        return f"fbi:state:{state.upper()}"

    # ── Public API ─────────────────────────────────────────────────────────────

    async def compare_crime_data(
        self,
        current_lat: float,
        current_lng: float,
        current_address: str,
        dest_lat: float,
        dest_lng: float,
        dest_address: str,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compare crime between two locations.
        Fetches locations sequentially to avoid connection burst 503s on FBI API.
        Uses user_preferences for schedule-based temporal analysis.
        """
        current_fbi = await self._get_rates(current_address, current_lat, current_lng)
        dest_fbi    = await self._get_rates(dest_address, dest_lat, dest_lng)

        current_data = self._build_location_data(current_fbi, user_preferences)
        dest_data    = self._build_location_data(dest_fbi, user_preferences)

        crime_diff = dest_data['total_crimes'] - current_data['total_crimes']
        pct_change = round(
            crime_diff / max(current_data['total_crimes'], 1) * 100, 1
        )
        score_diff = dest_data['safety_score'] - current_data['safety_score']

        return {
            'current':     current_data,
            'destination': dest_data,
            'comparison': {
                'crime_difference':    crime_diff,
                'crime_change_percent': pct_change,
                'score_difference':    score_diff,
                'is_safer':            score_diff > 0,
                'recommendation':      self._recommendation(
                    current_data['safety_score'],
                    dest_data['safety_score'],
                    dest_fbi['total'],
                ),
            },
        }


crime_service = CrimeService()
