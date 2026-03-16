import re
import os
import asyncio
import httpx
from typing import Dict, Any, List, Optional, Tuple

# HowLoud SoundScore fallback values per state (score 0-100, higher = quieter).
# Obtained by calling the HowLoud API at the most populous city in each state.
# AK and HI returned 100 (outside HowLoud coverage) — substituted realistic estimates.
_STATE_SCORES: Dict[str, int] = {
    'AL': 67, 'AK': 75, 'AZ': 64, 'AR': 72, 'CA': 65,
    'CO': 67, 'CT': 62, 'DE': 72, 'FL': 65, 'GA': 63,
    'HI': 65, 'ID': 65, 'IL': 62, 'IN': 69, 'IA': 65,
    'KS': 73, 'KY': 68, 'LA': 73, 'ME': 65, 'MD': 64,
    'MA': 65, 'MI': 63, 'MN': 66, 'MS': 67, 'MO': 64,
    'MT': 67, 'NE': 63, 'NV': 67, 'NH': 67, 'NJ': 65,
    'NM': 68, 'NY': 65, 'NC': 66, 'ND': 74, 'OH': 70,
    'OK': 64, 'OR': 54, 'PA': 64, 'RI': 66, 'SC': 64,
    'SD': 64, 'TN': 74, 'TX': 62, 'UT': 67, 'VT': 69,
    'VA': 61, 'WA': 61, 'WV': 65, 'WI': 64, 'WY': 70,
}


class NoiseService:
    """
    Estimate noise levels using a tiered approach:
      1. HowLoud SoundScore API  – real calibrated score at the exact address
      2. HowLoud state-level score – hardcoded HowLoud scores for each state's
         major city, used when the per-address call fails
      3. National average (HowLoud score 65) – if state cannot be extracted
    """

    def __init__(self):
        self.google_api_key  = os.getenv('GOOGLE_MAPS_API_KEY')
        self.howloud_api_key = os.getenv('HOWLOUD_API_KEY')
        self.geocoding_url   = "https://maps.googleapis.com/maps/api/geocode/json"
        self.howloud_url     = "https://api.howloud.com/v2/score"


    # ── Address helper ─────────────────────────────────────────────────────────

    @staticmethod
    def _state_from_address(address: str) -> Optional[str]:
        """Extract a 2-letter US state code from a geocoded address string."""
        match = re.search(r',\s*([A-Z]{2})\b', address)
        if match:
            code = match.group(1)
            if code != 'US':
                return code
        return None

    # ── Geocoding ─────────────────────────────────────────────────────────────

    async def _geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to (lat, lng) using Google Geocoding API."""
        if not self.google_api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.geocoding_url, params={
                    'address': address,
                    'key': self.google_api_key,
                })
                data = resp.json()
                if data.get('status') == 'OK' and data.get('results'):
                    loc = data['results'][0]['geometry']['location']
                    return loc['lat'], loc['lng']
                print(f"   ⚠️ Geocoding status: {data.get('status')} for '{address}'")
        except Exception as e:
            print(f"   ⚠️ Geocoding error: {e}")
        return None

    # ── HowLoud API ───────────────────────────────────────────────────────────

    async def _fetch_howloud_score(self, lat: float, lng: float) -> Optional[Dict]:
        """
        Fetch a SoundScore from HowLoud for (lat, lng).
        Returns the result dict (unwrapped from the result array), or None.
        Response shape: {"status":"OK","result":[{score, traffic, local, airports, ...}]}
        """
        if not self.howloud_api_key:
            print(f"   ⚠️ HowLoud API key not set (HOWLOUD_API_KEY env var missing)")
            return None
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    self.howloud_url,
                    params={'lat': lat, 'lng': lng},
                    headers={'x-api-key': self.howloud_api_key},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get('result', [])
                    if result and 'score' in result[0]:
                        return result[0]
                    print(f"   ⚠️ HowLoud API: unexpected response shape: {str(data)[:120]}")
                else:
                    print(f"   ⚠️ HowLoud API: HTTP {resp.status_code} – {resp.text[:120]}")
        except Exception as e:
            print(f"   ⚠️ HowLoud API error: {e}")
        return None

    @staticmethod
    def _score_to_db(score: float) -> float:
        """
        Convert HowLoud SoundScore (0 = very loud, 100 = very quiet) to ambient dB.
        Uses piecewise linear interpolation anchored to HowLoud's own categories
        and real-world dB ranges:
          Score   0–25  → 85–75 dB  (Extremely Loud)
          Score  26–50  → 75–70 dB  (Very Loud)
          Score  51–60  → 70–65 dB  (Loud)
          Score  61–70  → 65–55 dB  (Moderate)
          Score  71–80  → 55–45 dB  (Quiet)
          Score  81–100 → 45–35 dB  (Very Quiet)
        """
        breakpoints = [(0, 85), (25, 75), (50, 70), (60, 65), (70, 55), (80, 45), (100, 35)]
        s = max(0.0, min(100.0, score))
        for i in range(len(breakpoints) - 1):
            s0, db0 = breakpoints[i]
            s1, db1 = breakpoints[i + 1]
            if s0 <= s <= s1:
                t = (s - s0) / (s1 - s0)
                return round(db0 + t * (db1 - db0), 1)
        return 35.0

    def _howloud_to_result(self, data: Dict, user_preference: str) -> Dict[str, Any]:
        """Convert a HowLoud SoundScore API response to our standard result format."""
        score = float(data.get('score', 50))
        estimated_db = self._score_to_db(score)

        indicators: List[str] = []
        if data.get('airports', 0) > 0:
            indicators.append('airport noise')
        if data.get('traffic', 0) > 30:
            indicators.append('highway traffic')
        elif data.get('traffic', 0) > 10:
            indicators.append('road traffic')
        if data.get('local', 0) > 20:
            indicators.append('local activity')
        if not indicators:
            indicators = ['residential area']

        noise_category    = self.categorize_noise_by_db(estimated_db)
        preference_score  = self.calculate_preference_score(estimated_db, noise_category, user_preference)
        level, description = self._level_description(estimated_db)
        preference_match  = self._check_preference_match(noise_category, user_preference)
        scoretext = data.get('scoretext', '').strip()

        print(f"   🔊 HowLoud SoundScore: {score:.0f}/100 → {estimated_db:.1f} dB ({noise_category})")
        return self._build_result(estimated_db, scoretext or description, indicators,
                                  preference_score, noise_category, level, preference_match,
                                  'HowLoud SoundScore API')

    def _state_score_to_result(self, score: int, user_preference: str) -> Dict[str, Any]:
        """Convert a hardcoded HowLoud state score to our standard result format."""
        estimated_db = self._score_to_db(float(score))
        noise_category    = self.categorize_noise_by_db(estimated_db)
        preference_score  = self.calculate_preference_score(estimated_db, noise_category, user_preference)
        level, description = self._level_description(estimated_db)
        preference_match  = self._check_preference_match(noise_category, user_preference)
        return self._build_result(estimated_db, description, [],
                                  preference_score, noise_category, level, preference_match,
                                  'HowLoud SoundScore (State Average)')

    @staticmethod
    def _build_result(
        score: float, description: str, indicators: List[str],
        noise_score: float, noise_category: str, level: str,
        preference_match: Dict, data_source: str,
    ) -> Dict[str, Any]:
        return {
            'level':            level,
            'score':            score,
            'noise_score':      noise_score,
            'noise_category':   noise_category,
            'description':      description,
            'indicators':       indicators,
            'preference_match': preference_match,
            'data_source':      data_source,
        }

    # ── Noise estimation ──────────────────────────────────────────────────────

    async def estimate_noise_level(
        self,
        address: str,
        user_preference: str = "moderate",
    ) -> Dict[str, Any]:
        """
        Estimate noise level for *address*.
        Priority: HowLoud (address) → HowLoud (state average) → static city lookup.
        """
        lat_lng = await self._geocode_address(address)
        if lat_lng:
            howloud_data = await self._fetch_howloud_score(*lat_lng)
            if howloud_data:
                return self._howloud_to_result(howloud_data, user_preference)

        # Fallback 1: hardcoded HowLoud state score
        state = self._state_from_address(address)
        if state and state in _STATE_SCORES:
            print(f"   ℹ️ HowLoud unavailable – using state-level score for {state} ({_STATE_SCORES[state]}/100)")
            return self._state_score_to_result(_STATE_SCORES[state], user_preference)

        # Fallback 2: national average (score 65 → ~55.8 dB, moderate)
        print(f"   ⚠️ No state match for '{address}' – using national average")
        return self._state_score_to_result(65, user_preference)

    # ── Comparison ────────────────────────────────────────────────────────────

    async def compare_noise_levels(
        self,
        current_address: str,
        destination_address: str,
        user_preference: str = "moderate",
    ) -> Dict[str, Any]:
        """
        Compare noise between two locations, both fetched in parallel.
        Returns a nested dict with 'current', 'destination', and 'comparison' keys
        so callers need only this one call to get all noise data.
        """
        current, destination = await asyncio.gather(
            self.estimate_noise_level(current_address, user_preference),
            self.estimate_noise_level(destination_address, user_preference),
        )

        db_diff    = destination['score'] - current['score']
        score_diff = destination['noise_score'] - current['noise_score']
        pref       = (user_preference or 'moderate').lower()
        impact, analysis = self._generate_impact_analysis(db_diff, pref)

        return {
            'current':     current,
            'destination': destination,
            'comparison': {
                'db_difference':    round(db_diff, 1),
                'score_difference': round(score_diff, 1),
                'is_quieter':       db_diff < 0,
                'impact':           impact,
                'analysis':         analysis,
                'preference_match': destination['preference_match'],
            },
            # Flat keys retained for backwards compatibility with current analysis.py
            'current_noise_level':          current['level'],
            'current_score':                current['score'],
            'current_noise_score':          current['noise_score'],
            'current_description':          current['description'],
            'current_indicators':           current['indicators'],
            'current_category':             current['noise_category'],
            'destination_noise_level':      destination['level'],
            'destination_score':            destination['score'],
            'destination_noise_score':      destination['noise_score'],
            'destination_description':      destination['description'],
            'destination_indicators':       destination['indicators'],
            'destination_category':         destination['noise_category'],
            'destination_preference_match': destination['preference_match'],
            'score_difference':             round(score_diff, 1),
            'db_difference':                round(db_diff, 1),
            'impact':                       impact,
            'analysis':                     analysis,
            'data_source':                  destination['data_source'],
        }

    # ── Scoring helpers ───────────────────────────────────────────────────────

    def categorize_noise_by_db(self, db_score: float) -> str:
        if db_score >= 75:   return "Very Noisy"
        elif db_score >= 65: return "Noisy"
        elif db_score >= 55: return "Moderate"
        elif db_score >= 45: return "Quiet"
        return "Very Quiet"

    def calculate_preference_score(
        self,
        db_score: float,
        noise_category: str,
        user_preference: str = "moderate",
    ) -> float:
        preference_scores = {
            'quiet':    {'Very Quiet': 100, 'Quiet': 90, 'Moderate': 60, 'Noisy': 30, 'Very Noisy': 10},
            'moderate': {'Very Quiet': 70,  'Quiet': 85, 'Moderate': 100, 'Noisy': 85, 'Very Noisy': 50},
            'lively':   {'Very Quiet': 40,  'Quiet': 60, 'Moderate': 80, 'Noisy': 95, 'Very Noisy': 100},
        }
        pref = (user_preference or 'moderate').lower()
        if pref not in preference_scores:
            pref = 'moderate'
        base_score = preference_scores[pref].get(noise_category, 50)
        print(f"   🔊 Noise scoring: {noise_category} ({db_score:.1f} dB) + '{pref}' preference = {base_score}/100")
        return float(base_score)

    def _check_preference_match(self, noise_category: str, user_preference: str) -> Dict[str, Any]:
        pref = (user_preference or 'moderate').lower()
        good_matches = {
            'quiet':    ['Very Quiet', 'Quiet'],
            'moderate': ['Quiet', 'Moderate', 'Noisy'],
            'lively':   ['Moderate', 'Noisy', 'Very Noisy'],
        }
        quality_map = {'quiet': 'peaceful', 'moderate': 'balanced', 'lively': 'vibrant'}
        return {
            'is_good_match': noise_category in good_matches.get(pref, []),
            'quality': quality_map.get(pref, 'balanced'),
        }

    @staticmethod
    def _level_description(final_db: float) -> Tuple[str, str]:
        if final_db >= 75:
            return ("Very Loud (75-85 dB)",
                    "High noise environment with highways, airports, or dense urban activity")
        elif final_db >= 65:
            return ("Loud (65-75 dB)",
                    "Moderately loud with significant traffic, transit, or nightlife nearby")
        elif final_db >= 55:
            return ("Moderate (55-65 dB)",
                    "Moderate noise levels with typical urban or suburban sounds")
        elif final_db >= 45:
            return ("Quiet-Moderate (45-55 dB)",
                    "Relatively quiet with occasional traffic or activity")
        return ("Quiet (below 45 dB)",
                "Peaceful environment with minimal noise pollution")

    @staticmethod
    def _generate_impact_analysis(db_diff: float, pref: str) -> Tuple[str, str]:
        if pref == 'lively':
            if db_diff > 10:
                return "Positive", f"Much livelier environment (increase of {db_diff:.0f} dB) – great for your vibrant lifestyle preference."
            elif db_diff > 5:
                return "Slightly Positive", f"Slightly more energetic environment (increase of {db_diff:.0f} dB)."
            elif db_diff < -10:
                return "Concerning", f"Significantly quieter environment (reduction of {abs(db_diff):.0f} dB) – may feel too calm for your preference."
            elif db_diff < -5:
                return "Noticeable", f"Somewhat quieter environment (reduction of {abs(db_diff):.0f} dB)."
            return "Neutral", "Similar noise environment to your current location."
        elif pref == 'quiet':
            if db_diff < -10:
                return "Positive", f"Much quieter environment (reduction of {abs(db_diff):.0f} dB) – aligns well with your quiet preference."
            elif db_diff < -5:
                return "Slightly Positive", f"Somewhat quieter environment (reduction of {abs(db_diff):.0f} dB), which suits your preferences."
            elif db_diff > 10:
                return "Concerning", f"Significantly louder environment (increase of {db_diff:.0f} dB). Consider noise-canceling solutions."
            elif db_diff > 5:
                return "Noticeable", f"Moderately louder environment (increase of {db_diff:.0f} dB). May require adjustment."
            return "Neutral", "Similar noise environment to your current location."
        else:  # moderate
            if abs(db_diff) > 10:
                direction = "louder" if db_diff > 0 else "quieter"
                return "Noticeable", f"Significantly {direction} environment (change of {abs(db_diff):.0f} dB)."
            elif abs(db_diff) > 5:
                direction = "louder" if db_diff > 0 else "quieter"
                return "Slightly Noticeable", f"Somewhat {direction} environment (change of {abs(db_diff):.0f} dB)."
            return "Neutral", "Similar noise environment to your current location."

noise_service = NoiseService()
