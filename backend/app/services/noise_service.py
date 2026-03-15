import os
import math
import asyncio
import httpx
from typing import Dict, Any, List, Optional, Tuple


class NoiseService:
    """
    Estimate noise levels using a tiered approach:
      1. HowLoud SoundScore API  – real calibrated scores (primary, US coverage)
      2. Google Places + OpenStreetMap  – physics-based modelling (global fallback)
      3. Static city lookup  – last resort if APIs are unavailable
    """

    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.howloud_api_key = os.getenv('HOWLOUD_API_KEY')

        self.geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.howloud_url = "https://api.howloud.com/v2/score"

        self._fallback_city_noise = {
            'new york': 75, 'manhattan': 80, 'chicago': 72,
            'los angeles': 70, 'san francisco': 65, 'boston': 65,
            'seattle': 60, 'miami': 65, 'dallas': 60, 'houston': 60,
            'philadelphia': 65, 'atlanta': 60, 'washington': 65,
            'denver': 55, 'phoenix': 55, 'austin': 55, 'san diego': 55,
            'portland': 55, 'nashville': 55, 'charlotte': 50,
            'raleigh': 45, 'minneapolis': 55, 'san antonio': 55,
        }
        self._fallback_indicators = {
            'downtown': 15, 'midtown': 12, 'city center': 15,
            'financial district': 12, 'airport': 20, 'highway': 15,
            'interstate': 15, 'avenue': 8, 'boulevard': 8,
            'suburb': -15, 'residential': -10, 'quiet': -15,
            'park': -12, 'hills': -10, 'rural': -20,
        }

    # ── Geocoding ─────────────────────────────────────────────────────────────

    async def _geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to (lat, lng) using Google Geocoding API."""
        if not self.google_api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
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

    # ── HowLoud API (primary) ─────────────────────────────────────────────────

    async def _fetch_howloud_score(self, lat: float, lng: float) -> Optional[Dict]:
        """
        Fetch a SoundScore from HowLoud for (lat, lng).
        Returns the result dict (unwrapped from the result array), or None.
        Response shape: {"status":"OK","result":[{score, traffic, local, airports, ...}]}
        """
        if not self.howloud_api_key:
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
                print(f"   ⚠️ HowLoud API: HTTP {resp.status_code}")
        except Exception as e:
            print(f"   ⚠️ HowLoud API error: {e}")
        return None

    def _howloud_to_result(self, data: Dict, user_preference: str) -> Dict[str, Any]:
        """
        Convert a HowLoud SoundScore response to our standard result format.

        SoundScore mapping (0 = very loud, 100 = silent):
          estimated_dB = 85 − score × 0.45
          Score 90 → ~44 dB (quiet)
          Score 70 → ~54 dB (quiet-moderate)
          Score 50 → ~63 dB (moderate urban)
          Score 30 → ~72 dB (noisy)
          Score 10 → ~81 dB (very noisy)
        """
        score = float(data.get('score', 50))
        estimated_db = round(max(35.0, min(85.0, 85.0 - score * 0.45)), 1)

        # Build indicators from component impact scores (higher = more noise)
        indicators: List[str] = []
        airports_impact = data.get('airports', 0)
        traffic_impact = data.get('traffic', 0)
        local_impact = data.get('local', 0)

        if airports_impact > 0:
            indicators.append('airport noise')
        if traffic_impact > 30:
            indicators.append('highway traffic')
        elif traffic_impact > 10:
            indicators.append('road traffic')
        if local_impact > 20:
            indicators.append('local activity')
        if not indicators:
            indicators = ['residential area']

        noise_category = self.categorize_noise_by_db(estimated_db)
        preference_score = self.calculate_preference_score(estimated_db, noise_category, user_preference)
        level, description = self._level_description(estimated_db)
        preference_match = self._check_preference_match(noise_category, user_preference)

        # Use HowLoud's own description if available
        scoretext = data.get('scoretext', '').strip()

        print(f"   🔊 HowLoud SoundScore: {score:.0f}/100 → {estimated_db:.1f} dB ({noise_category})")
        return {
            'level': level,
            'score': estimated_db,
            'noise_score': preference_score,
            'noise_category': noise_category,
            'description': scoretext or description,
            'indicators': indicators,
            'preference_match': preference_match,
            'data_source': 'HowLoud SoundScore API',
        }

    # ── Places API (fallback) ─────────────────────────────────────────────────

    async def _search_places(
        self,
        client: httpx.AsyncClient,
        lat: float,
        lng: float,
        place_type: Optional[str],
        radius: int,
        keyword: Optional[str] = None,
    ) -> List[Dict]:
        """Run a single Google Places Nearby Search request."""
        params: Dict[str, Any] = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'key': self.google_api_key,
        }
        if keyword:
            params['keyword'] = keyword
        if place_type:
            params['type'] = place_type
        try:
            resp = await client.get(self.places_url, params=params)
            data = resp.json()
            if data.get('status') in ('OK', 'ZERO_RESULTS'):
                return data.get('results', [])
            print(f"   Places API [{place_type or keyword}]: {data.get('status')}")
        except Exception as e:
            print(f"   Places API error [{place_type or keyword}]: {e}")
        return []

    async def _fetch_all_places(self, lat: float, lng: float) -> Dict[str, List[Dict]]:
        """Fetch all noise-relevant place types in parallel."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            results = await asyncio.gather(
                self._search_places(client, lat, lng, 'airport', 20000),
                self._search_places(client, lat, lng, 'train_station', 2000),
                self._search_places(client, lat, lng, 'transit_station', 1000),
                self._search_places(client, lat, lng, 'subway_station', 500),
                self._search_places(client, lat, lng, 'night_club', 1000),
                self._search_places(client, lat, lng, 'bar', 500),
                self._search_places(client, lat, lng, 'stadium', 3000),
                self._search_places(client, lat, lng, None, 2000, keyword='industrial park'),
                return_exceptions=True,
            )
        keys = ['airports', 'train_stations', 'transit_stations', 'subway_stations',
                'nightclubs', 'bars', 'stadiums', 'industrial']
        return {
            key: (val if isinstance(val, list) else [])
            for key, val in zip(keys, results)
        }

    # ── Road proximity (OpenStreetMap) ────────────────────────────────────────

    async def _check_road_proximity(self, lat: float, lng: float) -> Dict[str, float]:
        """
        Query Overpass API for nearby roads and return per-type max dB impact.
        Road types: motorway, trunk, primary, secondary.
        """
        query = (
            f"[out:json][timeout:12];"
            f"("
            f'way["highway"="motorway"](around:2000,{lat},{lng});'
            f'way["highway"="trunk"](around:2000,{lat},{lng});'
            f'way["highway"="primary"](around:1000,{lat},{lng});'
            f'way["highway"="secondary"](around:500,{lat},{lng});'
            f');out center;'
        )
        road_impacts: Dict[str, float] = {
            'motorway': 0.0, 'trunk': 0.0, 'primary': 0.0, 'secondary': 0.0
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    self.overpass_url,
                    data={'data': query},
                    headers={'User-Agent': 'movewise_app_v1'},
                )
                data = resp.json()
            for element in data.get('elements', []):
                highway_type = element.get('tags', {}).get('highway', '')
                if highway_type not in road_impacts:
                    continue
                center = element.get('center', {})
                if not center:
                    continue
                dist = self._haversine(lat, lng, center['lat'], center['lon'])
                impact = self._road_db_impact(highway_type, dist)
                road_impacts[highway_type] = max(road_impacts[highway_type], impact)
        except Exception as e:
            print(f"   ⚠️ Overpass API error: {e}")
        return road_impacts

    # ── Distance / dB helpers ─────────────────────────────────────────────────

    @staticmethod
    def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Return distance in metres between two WGS-84 coordinates."""
        R = 6_371_000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lng2 - lng1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
        return 2 * R * math.asin(math.sqrt(a))

    @staticmethod
    def _road_db_impact(road_type: str, distance_m: float) -> float:
        """
        Estimate dB from a road at *distance_m* using line-source attenuation
        (−3 dB per doubling of distance). Reference distance: 10 m.
        """
        source_db = {'motorway': 82, 'trunk': 78, 'primary': 72, 'secondary': 65}
        base = source_db.get(road_type, 60)
        ref = max(distance_m, 10)
        attenuation = 10 * math.log10(ref / 10)
        return max(0.0, base - attenuation)

    @staticmethod
    def _airport_db_impact(distance_m: float) -> float:
        """
        Estimate ambient L_Aeq contribution from an airport at *distance_m*.
        Values reflect real-world daytime average dB near commercial airports.
        """
        thresholds = [
            (2_000,  72),  # under/near flight path
            (5_000,  65),  # within approach corridor
            (10_000, 57),  # noticeable aircraft overhead
            (15_000, 49),  # periodic flyovers
            (20_000, 42),  # distant, occasional aircraft
        ]
        for threshold, impact in thresholds:
            if distance_m < threshold:
                return float(impact)
        return 0.0

    @staticmethod
    def _point_source_db_impact(source_db: float, distance_m: float) -> float:
        """
        Estimate dB from a point source using inverse-square-law attenuation
        (−6 dB per doubling of distance). Reference distance: 10 m.
        """
        ref = max(distance_m, 10)
        attenuation = 20 * math.log10(ref / 10)
        return max(0.0, source_db - attenuation)

    def _max_impact_from_places(
        self,
        places: List[Dict],
        source_db: float,
        lat: float,
        lng: float,
        is_airport: bool = False,
    ) -> float:
        """Return the highest dB impact from a list of Places results."""
        best = 0.0
        for place in places:
            loc = place.get('geometry', {}).get('location', {})
            if not loc:
                continue
            dist = self._haversine(lat, lng, loc['lat'], loc['lng'])
            impact = (
                self._airport_db_impact(dist)
                if is_airport
                else self._point_source_db_impact(source_db, dist)
            )
            best = max(best, impact)
        return best

    @staticmethod
    def _combine_db(*db_values: float, baseline: float = 40.0) -> float:
        """Combine independent noise sources using logarithmic addition."""
        total_power = 10 ** (baseline / 10)
        for db in db_values:
            if db > 0:
                total_power += 10 ** (db / 10)
        return min(85.0, 10 * math.log10(total_power))

    # ── Noise estimation ──────────────────────────────────────────────────────

    async def estimate_noise_level(
        self,
        address: str,
        user_preference: str = "moderate",
    ) -> Dict[str, Any]:
        """
        Estimate noise level for *address*.
        Priority: HowLoud → Google Places + OSM → static city lookup.
        """
        lat_lng = await self._geocode_address(address)
        if lat_lng is None:
            print(f"   ⚠️ Geocoding failed – using static estimate for '{address}'")
            return self._static_estimate(address, user_preference)

        lat, lng = lat_lng

        # ── Primary: HowLoud SoundScore ──
        howloud_data = await self._fetch_howloud_score(lat, lng)
        if howloud_data:
            return self._howloud_to_result(howloud_data, user_preference)

        print(f"   ℹ️ HowLoud unavailable – falling back to Places + OSM for '{address}'")

        # ── Fallback: Google Places + OpenStreetMap ──
        try:
            places, road_impacts = await asyncio.gather(
                self._fetch_all_places(lat, lng),
                self._check_road_proximity(lat, lng),
            )
        except Exception as e:
            print(f"   ⚠️ Noise data fetch error: {e} – using static estimate")
            return self._static_estimate(address, user_preference)

        db_contributions: List[float] = []
        detected_indicators: List[str] = []

        # Roads
        road_labels = {'motorway': 'highway', 'trunk': 'trunk road',
                       'primary': 'major road', 'secondary': 'secondary road'}
        for road_type, impact in road_impacts.items():
            if impact > 1:
                db_contributions.append(impact)
                detected_indicators.append(road_labels.get(road_type, road_type))
                print(f"   🛣️  {road_type}: +{impact:.1f} dB")

        # Airports
        airport_impact = self._max_impact_from_places(
            places['airports'], 0, lat, lng, is_airport=True
        )
        if airport_impact > 0:
            db_contributions.append(airport_impact)
            detected_indicators.append('airport')
            print(f"   ✈️  Airport proximity: +{airport_impact:.1f} dB  ({len(places['airports'])} found)")

        # Train stations
        train_impact = self._max_impact_from_places(places['train_stations'], 80, lat, lng)
        if train_impact > 0:
            db_contributions.append(train_impact)
            detected_indicators.append('train station')
            print(f"   🚂 Train station: +{train_impact:.1f} dB")

        # Transit / subway
        transit_impact = max(
            self._max_impact_from_places(places['transit_stations'], 72, lat, lng),
            self._max_impact_from_places(places['subway_stations'], 70, lat, lng),
        )
        if transit_impact > 0:
            db_contributions.append(transit_impact)
            detected_indicators.append('transit station')

        # Nightlife (count-based, expressed as ambient L_Aeq estimate)
        nightclub_count = len(places['nightclubs'])
        bar_count = len(places['bars'])
        if nightclub_count > 0 or bar_count >= 3:
            nightlife_db = min(65, 48 + nightclub_count * 4 + bar_count * 1.5)
            db_contributions.append(nightlife_db)
            detected_indicators.append('nightlife district')
            print(f"   🍺 Nightlife ({nightclub_count} clubs, {bar_count} bars): +{nightlife_db:.1f} dB")

        # Stadiums (periodic events – weighted 30%)
        stadium_impact = self._max_impact_from_places(places['stadiums'], 90, lat, lng)
        if stadium_impact > 5:
            db_contributions.append(stadium_impact * 0.30)
            detected_indicators.append('sports venue')
            print(f"   🏟️  Stadium: +{stadium_impact * 0.30:.1f} dB (event-weighted)")

        # Industrial
        industrial_impact = self._max_impact_from_places(places['industrial'], 75, lat, lng)
        if industrial_impact > 0:
            db_contributions.append(industrial_impact)
            detected_indicators.append('industrial area')
            print(f"   🏭 Industrial: +{industrial_impact:.1f} dB")

        final_db = self._combine_db(*db_contributions)
        print(f"   🔊 Final estimated noise: {final_db:.1f} dB")

        noise_category = self.categorize_noise_by_db(final_db)
        preference_score = self.calculate_preference_score(final_db, noise_category, user_preference)
        level, description = self._level_description(final_db)
        preference_match = self._check_preference_match(noise_category, user_preference)

        return {
            'level': level,
            'score': round(final_db, 1),
            'noise_score': preference_score,
            'noise_category': noise_category,
            'description': description,
            'indicators': detected_indicators if detected_indicators else ['residential area'],
            'preference_match': preference_match,
            'data_source': 'Google Places API + OpenStreetMap Roads',
        }

    # ── Comparison ────────────────────────────────────────────────────────────

    async def compare_noise_levels(
        self,
        current_address: str,
        destination_address: str,
        user_preference: str = "moderate",
    ) -> Dict[str, Any]:
        """Compare noise between two locations, both fetched in parallel."""
        current, destination = await asyncio.gather(
            self.estimate_noise_level(current_address, user_preference),
            self.estimate_noise_level(destination_address, user_preference),
        )

        db_diff = destination['score'] - current['score']
        score_diff = destination['noise_score'] - current['noise_score']
        pref = (user_preference or 'moderate').lower()
        impact, analysis = self._generate_impact_analysis(db_diff, pref)

        return {
            'current_noise_level': current['level'],
            'current_score': current['score'],
            'current_noise_score': current['noise_score'],
            'current_description': current['description'],
            'current_indicators': current['indicators'],
            'current_category': current['noise_category'],

            'destination_noise_level': destination['level'],
            'destination_score': destination['score'],
            'destination_noise_score': destination['noise_score'],
            'destination_description': destination['description'],
            'destination_indicators': destination['indicators'],
            'destination_category': destination['noise_category'],
            'destination_preference_match': destination['preference_match'],

            'score_difference': round(score_diff, 1),
            'db_difference': round(db_diff, 1),
            'impact': impact,
            'analysis': analysis,
            'data_source': destination['data_source'],
        }

    # ── Scoring helpers ───────────────────────────────────────────────────────

    def categorize_noise_by_db(self, db_score: float) -> str:
        if db_score >= 75:
            return "Very Noisy"
        elif db_score >= 65:
            return "Noisy"
        elif db_score >= 55:
            return "Moderate"
        elif db_score >= 45:
            return "Quiet"
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
                change = abs(db_diff)
                return "Noticeable", f"Significantly {direction} environment (change of {change:.0f} dB)."
            elif abs(db_diff) > 5:
                direction = "louder" if db_diff > 0 else "quieter"
                change = abs(db_diff)
                return "Slightly Noticeable", f"Somewhat {direction} environment (change of {change:.0f} dB)."
            return "Neutral", "Similar noise environment to your current location."

    # ── Static fallback ───────────────────────────────────────────────────────

    def _static_estimate(self, address: str, user_preference: str) -> Dict[str, Any]:
        """City-lookup estimation used only when all APIs are unavailable."""
        address_lower = address.lower()
        base_score = 55

        for city, score in self._fallback_city_noise.items():
            if city in address_lower:
                base_score = score
                break

        adjustment = sum(
            change for indicator, change in self._fallback_indicators.items()
            if indicator in address_lower
        )
        final_db = float(max(30, min(85, base_score + adjustment)))

        noise_category = self.categorize_noise_by_db(final_db)
        preference_score = self.calculate_preference_score(final_db, noise_category, user_preference)
        level, description = self._level_description(final_db)
        preference_match = self._check_preference_match(noise_category, user_preference)
        detected = [k for k in self._fallback_indicators if k in address_lower]

        return {
            'level': level,
            'score': round(final_db, 1),
            'noise_score': preference_score,
            'noise_category': noise_category,
            'description': description,
            'indicators': detected if detected else ['standard residential'],
            'preference_match': preference_match,
            'data_source': 'Static city estimates (API unavailable)',
        }


noise_service = NoiseService()
