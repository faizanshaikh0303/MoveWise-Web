"""Unit tests for NoiseService — pure helpers + mocked HTTP calls."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.noise_service import NoiseService, _STATE_SCORES


@pytest.fixture
def svc():
    return NoiseService()


# ── _state_from_address ───────────────────────────────────────────────────────

class TestStateFromAddress:
    def test_extracts_two_letter_code(self, svc):
        assert svc._state_from_address("Atlanta, GA 30303, USA") == "GA"

    def test_returns_none_for_us(self, svc):
        assert svc._state_from_address("Some St, US") is None

    def test_returns_none_with_no_state(self, svc):
        assert svc._state_from_address("no state here") is None

    def test_last_state_code_wins(self, svc):
        # Should grab the state, not 'US'
        result = svc._state_from_address("123 Main, New York, NY 10001, USA")
        assert result == "NY"


# ── _score_to_db ──────────────────────────────────────────────────────────────

class TestScoreToDb:
    @pytest.mark.parametrize("score,expected_range", [
        (0,   (75.0, 85.0)),
        (12,  (75.0, 85.0)),
        (25,  (75.0, 75.0)),
        (37,  (70.0, 75.0)),
        (50,  (70.0, 70.0)),
        (55,  (65.0, 70.0)),
        (60,  (65.0, 65.0)),
        (65,  (55.0, 65.0)),
        (70,  (55.0, 55.0)),
        (75,  (45.0, 55.0)),
        (80,  (45.0, 45.0)),
        (90,  (35.0, 45.0)),
        (100, (35.0, 35.0)),
    ])
    def test_score_falls_in_expected_db_range(self, score, expected_range):
        db = NoiseService._score_to_db(score)
        assert expected_range[1] >= db >= expected_range[0]

    def test_clamped_below_zero(self):
        assert NoiseService._score_to_db(-10) == NoiseService._score_to_db(0)

    def test_clamped_above_100(self):
        assert NoiseService._score_to_db(110) == NoiseService._score_to_db(100)

    def test_monotone_decreasing(self):
        """Higher HowLoud score → quieter → lower dB."""
        dbs = [NoiseService._score_to_db(s) for s in range(0, 101, 10)]
        assert dbs == sorted(dbs, reverse=True)


# ── categorize_noise_by_db ────────────────────────────────────────────────────

class TestCategorizeNoiseByDb:
    @pytest.mark.parametrize("db,expected", [
        (80.0, "Very Noisy"),
        (75.0, "Very Noisy"),
        (70.0, "Noisy"),
        (65.0, "Noisy"),
        (60.0, "Moderate"),
        (55.0, "Moderate"),
        (50.0, "Quiet"),
        (45.0, "Quiet"),
        (44.9, "Very Quiet"),
        (30.0, "Very Quiet"),
    ])
    def test_category_boundaries(self, svc, db, expected):
        assert svc.categorize_noise_by_db(db) == expected


# ── calculate_preference_score ────────────────────────────────────────────────

class TestCalculatePreferenceScore:
    def test_quiet_pref_very_quiet_env(self, svc):
        assert svc.calculate_preference_score(35.0, "Very Quiet", "quiet") == 100.0

    def test_quiet_pref_very_noisy_env(self, svc):
        assert svc.calculate_preference_score(80.0, "Very Noisy", "quiet") == 10.0

    def test_lively_pref_very_noisy_env(self, svc):
        assert svc.calculate_preference_score(80.0, "Very Noisy", "lively") == 100.0

    def test_moderate_pref_moderate_env(self, svc):
        assert svc.calculate_preference_score(60.0, "Moderate", "moderate") == 100.0

    def test_unknown_pref_defaults_to_moderate(self, svc):
        score_unknown = svc.calculate_preference_score(60.0, "Moderate", "unknown_pref")
        score_moderate = svc.calculate_preference_score(60.0, "Moderate", "moderate")
        assert score_unknown == score_moderate

    def test_none_pref_defaults_to_moderate(self, svc):
        score_none = svc.calculate_preference_score(60.0, "Moderate", None)
        score_moderate = svc.calculate_preference_score(60.0, "Moderate", "moderate")
        assert score_none == score_moderate


# ── _check_preference_match ───────────────────────────────────────────────────

class TestCheckPreferenceMatch:
    def test_quiet_pref_quiet_env_is_good(self, svc):
        result = svc._check_preference_match("Quiet", "quiet")
        assert result["is_good_match"] is True

    def test_quiet_pref_noisy_env_is_bad(self, svc):
        result = svc._check_preference_match("Very Noisy", "quiet")
        assert result["is_good_match"] is False

    def test_lively_pref_noisy_env_is_good(self, svc):
        result = svc._check_preference_match("Noisy", "lively")
        assert result["is_good_match"] is True

    def test_quality_field_present(self, svc):
        result = svc._check_preference_match("Moderate", "moderate")
        assert "quality" in result

    def test_moderate_quality_label(self, svc):
        result = svc._check_preference_match("Moderate", "moderate")
        assert result["quality"] == "balanced"


# ── _level_description ────────────────────────────────────────────────────────

class TestLevelDescription:
    @pytest.mark.parametrize("db,keyword", [
        (80.0, "Very Loud"),
        (70.0, "Loud"),
        (60.0, "Moderate"),
        (50.0, "Quiet-Moderate"),
        (40.0, "Quiet"),
    ])
    def test_level_label(self, db, keyword):
        level, _ = NoiseService._level_description(db)
        assert keyword in level


# ── _generate_impact_analysis ─────────────────────────────────────────────────

class TestGenerateImpactAnalysis:
    def test_lively_big_increase_positive(self):
        impact, _ = NoiseService._generate_impact_analysis(15.0, "lively")
        assert impact == "Positive"

    def test_lively_big_decrease_concerning(self):
        impact, _ = NoiseService._generate_impact_analysis(-15.0, "lively")
        assert impact == "Concerning"

    def test_quiet_big_decrease_positive(self):
        impact, _ = NoiseService._generate_impact_analysis(-15.0, "quiet")
        assert impact == "Positive"

    def test_quiet_big_increase_concerning(self):
        impact, _ = NoiseService._generate_impact_analysis(15.0, "quiet")
        assert impact == "Concerning"

    def test_moderate_neutral_small_change(self):
        impact, _ = NoiseService._generate_impact_analysis(3.0, "moderate")
        assert impact == "Neutral"

    def test_moderate_noticeable_large_change(self):
        impact, _ = NoiseService._generate_impact_analysis(12.0, "moderate")
        assert impact == "Noticeable"

    def test_analysis_is_string(self):
        _, analysis = NoiseService._generate_impact_analysis(0.0, "moderate")
        assert isinstance(analysis, str)


# ── _howloud_to_result ────────────────────────────────────────────────────────

class TestHowloudToResult:
    def test_airport_indicator(self, svc):
        data = {"score": 50, "airports": 5, "traffic": 0, "local": 0}
        result = svc._howloud_to_result(data, "moderate")
        assert "airport noise" in result["indicators"]

    def test_heavy_traffic_indicator(self, svc):
        data = {"score": 50, "airports": 0, "traffic": 40, "local": 0}
        result = svc._howloud_to_result(data, "moderate")
        assert "highway traffic" in result["indicators"]

    def test_light_traffic_indicator(self, svc):
        data = {"score": 50, "airports": 0, "traffic": 15, "local": 0}
        result = svc._howloud_to_result(data, "moderate")
        assert "road traffic" in result["indicators"]

    def test_local_activity_indicator(self, svc):
        data = {"score": 50, "airports": 0, "traffic": 5, "local": 25}
        result = svc._howloud_to_result(data, "moderate")
        assert "local activity" in result["indicators"]

    def test_no_noise_sources_defaults_to_residential(self, svc):
        data = {"score": 80, "airports": 0, "traffic": 0, "local": 0}
        result = svc._howloud_to_result(data, "quiet")
        assert "residential area" in result["indicators"]

    def test_data_source_is_howloud(self, svc):
        data = {"score": 70, "airports": 0, "traffic": 0, "local": 0}
        result = svc._howloud_to_result(data, "moderate")
        assert "HowLoud" in result["data_source"]


# ── _state_score_to_result ────────────────────────────────────────────────────

class TestStateScoreToResult:
    def test_returns_standard_keys(self, svc):
        result = svc._state_score_to_result(65, "moderate")
        for key in ("level", "score", "noise_score", "noise_category",
                    "description", "indicators", "preference_match", "data_source"):
            assert key in result

    def test_data_source_is_state_average(self, svc):
        result = svc._state_score_to_result(65, "moderate")
        assert "State Average" in result["data_source"]

    def test_empty_indicators(self, svc):
        result = svc._state_score_to_result(65, "moderate")
        assert result["indicators"] == []


# ── estimate_noise_level (async + mocked) ────────────────────────────────────

class TestEstimateNoiseLevel:
    async def test_uses_howloud_when_geocode_succeeds(self, svc):
        svc.google_api_key = "fake"
        svc.howloud_api_key = "fake"

        with patch.object(svc, "_geocode_address",
                          AsyncMock(return_value=(33.7, -84.4))), \
             patch.object(svc, "_fetch_howloud_score",
                          AsyncMock(return_value={"score": 70, "airports": 0,
                                                   "traffic": 5, "local": 0})):
            result = await svc.estimate_noise_level("Atlanta, GA", "moderate")

        assert result["data_source"] == "HowLoud SoundScore API"

    async def test_falls_back_to_state_when_howloud_unavailable(self, svc):
        svc.google_api_key = "fake"

        with patch.object(svc, "_geocode_address",
                          AsyncMock(return_value=(33.7, -84.4))), \
             patch.object(svc, "_fetch_howloud_score", AsyncMock(return_value=None)):
            result = await svc.estimate_noise_level("Atlanta, GA 30303, USA", "moderate")

        assert "State Average" in result["data_source"]

    async def test_falls_back_to_national_when_no_state(self, svc):
        with patch.object(svc, "_geocode_address", AsyncMock(return_value=None)):
            result = await svc.estimate_noise_level("Unknown Place ZZ", "moderate")

        assert result is not None  # should still return a result with national average

    async def test_state_in_state_scores(self, svc):
        with patch.object(svc, "_geocode_address", AsyncMock(return_value=None)):
            result = await svc.estimate_noise_level("Portland, OR 97201", "quiet")
        # OR is in _STATE_SCORES with score 54
        assert "State Average" in result["data_source"]


# ── _geocode_address (mocked httpx) ──────────────────────────────────────────

class TestGeocodeAddress:
    async def test_success(self, svc):
        svc.google_api_key = "fake-key"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "OK",
            "results": [{"geometry": {"location": {"lat": 33.748, "lng": -84.387}}}],
        }
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        with patch("httpx.AsyncClient") as MockClass:
            MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClass.return_value.__aexit__ = AsyncMock(return_value=None)
            result = await svc._geocode_address("Atlanta, GA")
        assert result == (33.748, -84.387)

    async def test_no_api_key_returns_none(self, svc):
        svc.google_api_key = None
        result = await svc._geocode_address("Atlanta, GA")
        assert result is None

    async def test_non_ok_status_returns_none(self, svc):
        svc.google_api_key = "fake-key"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "ZERO_RESULTS", "results": []}
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        with patch("httpx.AsyncClient") as MockClass:
            MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClass.return_value.__aexit__ = AsyncMock(return_value=None)
            result = await svc._geocode_address("Nonexistent Place")
        assert result is None

    async def test_exception_returns_none(self, svc):
        svc.google_api_key = "fake-key"
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("timeout"))
        with patch("httpx.AsyncClient") as MockClass:
            MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClass.return_value.__aexit__ = AsyncMock(return_value=None)
            result = await svc._geocode_address("Atlanta, GA")
        assert result is None


# ── _fetch_howloud_score (mocked httpx) ──────────────────────────────────────

class TestFetchHowloudScore:
    async def test_success(self, svc):
        svc.howloud_api_key = "fake-key"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "OK", "result": [{"score": 70}]}
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        with patch("httpx.AsyncClient") as MockClass:
            MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClass.return_value.__aexit__ = AsyncMock(return_value=None)
            result = await svc._fetch_howloud_score(33.7, -84.4)
        assert result == {"score": 70}

    async def test_no_api_key_returns_none(self, svc):
        svc.howloud_api_key = None
        result = await svc._fetch_howloud_score(33.7, -84.4)
        assert result is None

    async def test_non_200_returns_none(self, svc):
        svc.howloud_api_key = "fake"
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = "forbidden"
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        with patch("httpx.AsyncClient") as MockClass:
            MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClass.return_value.__aexit__ = AsyncMock(return_value=None)
            result = await svc._fetch_howloud_score(33.7, -84.4)
        assert result is None

    async def test_missing_score_in_result_returns_none(self, svc):
        svc.howloud_api_key = "fake"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "OK", "result": [{"no_score": True}]}
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        with patch("httpx.AsyncClient") as MockClass:
            MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClass.return_value.__aexit__ = AsyncMock(return_value=None)
            result = await svc._fetch_howloud_score(33.7, -84.4)
        assert result is None

    async def test_exception_returns_none(self, svc):
        svc.howloud_api_key = "fake"
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("network error"))
        with patch("httpx.AsyncClient") as MockClass:
            MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClass.return_value.__aexit__ = AsyncMock(return_value=None)
            result = await svc._fetch_howloud_score(33.7, -84.4)
        assert result is None


# ── compare_noise_levels ──────────────────────────────────────────────────────

class TestCompareNoiseLevels:
    async def test_returns_all_keys(self, svc):
        mock_result = {
            "score": 60.0, "noise_score": 70.0, "noise_category": "Moderate",
            "description": "Moderate", "indicators": [], "level": "Moderate",
            "preference_match": {"is_good_match": True, "quality": "balanced"},
            "data_source": "HowLoud State Average",
        }
        with patch.object(svc, "estimate_noise_level", AsyncMock(return_value=mock_result)):
            result = await svc.compare_noise_levels("Atlanta, GA", "Portland, OR", "moderate")
        assert "current" in result
        assert "destination" in result
        assert "comparison" in result

    async def test_is_quieter_when_destination_lower_db(self, svc):
        current_result = {
            "score": 70.0, "noise_score": 60.0, "noise_category": "Noisy",
            "description": "Noisy", "indicators": [], "level": "Loud",
            "preference_match": {"is_good_match": False, "quality": "balanced"},
            "data_source": "test",
        }
        dest_result = {
            "score": 50.0, "noise_score": 80.0, "noise_category": "Quiet",
            "description": "Quiet", "indicators": [], "level": "Quiet-Moderate",
            "preference_match": {"is_good_match": True, "quality": "peaceful"},
            "data_source": "test",
        }
        with patch.object(svc, "estimate_noise_level",
                          AsyncMock(side_effect=[current_result, dest_result])):
            result = await svc.compare_noise_levels("Noisy City", "Quiet Town", "quiet")
        assert result["comparison"]["is_quieter"] is True
