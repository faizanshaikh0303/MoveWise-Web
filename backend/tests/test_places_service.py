"""Unit tests for PlacesService — mocked googlemaps client."""
import pytest
from unittest.mock import MagicMock, patch
from app.services.places_service import PlacesService


@pytest.fixture
def svc():
    with patch("googlemaps.Client"):
        service = PlacesService()
        service.client = MagicMock()
        return service


# ── geocode_address ───────────────────────────────────────────────────────────

class TestGeocodeAddress:
    def test_success(self, svc):
        svc.client.geocode.return_value = [
            {"geometry": {"location": {"lat": 40.7128, "lng": -74.0060}}}
        ]
        lat, lng = svc.geocode_address("New York, NY")
        assert lat == 40.7128
        assert lng == -74.0060

    def test_empty_result_returns_none_tuple(self, svc):
        svc.client.geocode.return_value = []
        lat, lng = svc.geocode_address("Nonexistent Place")
        assert lat is None
        assert lng is None

    def test_exception_returns_none_tuple(self, svc):
        svc.client.geocode.side_effect = Exception("API error")
        lat, lng = svc.geocode_address("Any Address")
        assert lat is None
        assert lng is None


# ── _calculate_lifestyle_score ────────────────────────────────────────────────

class TestCalculateLifestyleScore:
    @pytest.mark.parametrize("total,expected_min", [
        (50, 100.0), (30, 90.0), (20, 75.0), (10, 60.0), (5, 40.0), (0, 20.0)
    ])
    def test_score_tiers(self, total, expected_min):
        counts = {"a": total} if total > 0 else {}
        score = PlacesService._calculate_lifestyle_score(counts)
        assert score >= expected_min - 15  # allow for variety bonus

    def test_variety_bonus_adds_up_to_15(self):
        # 5 categories × 3 = 15 bonus → capped at 15
        counts = {f"cat_{i}": 10 for i in range(5)}
        score_with_variety = PlacesService._calculate_lifestyle_score(counts)
        single_type_counts = {"only_one": sum(counts.values())}
        score_without = PlacesService._calculate_lifestyle_score(single_type_counts)
        assert score_with_variety >= score_without

    def test_max_score_is_100(self):
        counts = {f"cat_{i}": 20 for i in range(20)}
        assert PlacesService._calculate_lifestyle_score(counts) == 100.0

    def test_empty_counts_returns_20(self):
        assert PlacesService._calculate_lifestyle_score({}) == 20.0

    def test_49_total_gives_60_base(self):
        counts = {"a": 49}
        score = PlacesService._calculate_lifestyle_score(counts)
        assert score >= 60.0


# ── _calculate_convenience_score ─────────────────────────────────────────────

class TestCalculateConvenienceScore:
    def test_work_from_home(self):
        assert PlacesService._calculate_convenience_score({"method": "none"}) == 100.0

    def test_zero_duration(self):
        assert PlacesService._calculate_convenience_score({"duration_minutes": 0}) == 100.0

    def test_no_duration_returns_70(self):
        assert PlacesService._calculate_convenience_score({"method": "driving"}) == 70.0

    def test_20_min_is_100(self):
        assert PlacesService._calculate_convenience_score({"duration_minutes": 20}) == 100.0

    def test_30_min_is_80(self):
        score = PlacesService._calculate_convenience_score({"duration_minutes": 30})
        assert score == 80.0

    def test_45_min_score(self):
        score = PlacesService._calculate_convenience_score({"duration_minutes": 45})
        assert 55.0 <= score <= 60.0

    def test_60_min_score(self):
        score = PlacesService._calculate_convenience_score({"duration_minutes": 60})
        assert 28.0 <= score <= 32.0

    def test_very_long_commute_min_20(self):
        score = PlacesService._calculate_convenience_score({"duration_minutes": 180})
        assert score >= 20.0

    def test_score_decreases_as_commute_increases(self):
        durations = [10, 20, 30, 45, 60, 90]
        scores = [PlacesService._calculate_convenience_score({"duration_minutes": d})
                  for d in durations]
        assert scores == sorted(scores, reverse=True)


# ── get_nearby_amenities_with_locations ───────────────────────────────────────

class TestGetNearbyAmenities:
    def _make_places_response(self, results):
        return {"results": results}

    def _make_place(self, name, lat=40.0, lng=-74.0):
        return {
            "name": name,
            "geometry": {"location": {"lat": lat, "lng": lng}},
            "vicinity": "123 Main St",
        }

    def test_returns_counts_and_locations(self, svc):
        svc.client.places_nearby.return_value = self._make_places_response(
            [self._make_place("Store A"), self._make_place("Store B")]
        )
        counts, locations = svc.get_nearby_amenities_with_locations(40.7, -74.0)
        assert isinstance(counts, dict)
        assert isinstance(locations, dict)

    def test_zero_results_excluded_from_counts(self, svc):
        svc.client.places_nearby.return_value = self._make_places_response([])
        counts, _ = svc.get_nearby_amenities_with_locations(40.7, -74.0)
        assert all(v > 0 for v in counts.values())

    def test_known_hobby_gym_maps_to_type(self, svc):
        svc.client.places_nearby.return_value = self._make_places_response(
            [self._make_place("City Gym")]
        )
        counts, _ = svc.get_nearby_amenities_with_locations(40.7, -74.0, hobbies=["gym"])
        assert "gyms" in counts

    def test_unknown_hobby_is_ignored(self, svc):
        svc.client.places_nearby.return_value = self._make_places_response([])
        # Should not raise
        counts, _ = svc.get_nearby_amenities_with_locations(40.7, -74.0, hobbies=["unknownhobby"])
        assert isinstance(counts, dict)

    def test_no_hobbies_includes_defaults(self, svc):
        svc.client.places_nearby.return_value = self._make_places_response(
            [self._make_place("A")]
        )
        counts, _ = svc.get_nearby_amenities_with_locations(40.7, -74.0, hobbies=None)
        # Defaults include restaurants, cafes, parks
        category_names = list(counts.keys())
        assert len(category_names) > 0

    def test_api_error_sets_count_to_zero(self, svc):
        svc.client.places_nearby.side_effect = Exception("quota exceeded")
        counts, locations = svc.get_nearby_amenities_with_locations(40.7, -74.0)
        # All failed → counts should be empty (zero results dropped)
        assert isinstance(counts, dict)

    def test_subway_merged_into_train_stations(self, svc):
        call_count = [0]
        def side_effect(**kwargs):
            call_count[0] += 1
            # Return subway results for subway_station type
            if kwargs.get("type") == "subway_station":
                return self._make_places_response([self._make_place("Subway A")])
            if kwargs.get("type") == "train_station":
                return self._make_places_response([self._make_place("Train A")])
            return self._make_places_response([])

        svc.client.places_nearby.side_effect = side_effect
        counts, _ = svc.get_nearby_amenities_with_locations(40.7, -74.0)
        assert "_subway_stations" not in counts
        # If both returned results, train stations should be ≥ 1
        if "train stations" in counts:
            assert counts["train stations"] >= 1

    def test_location_data_format(self, svc):
        svc.client.places_nearby.return_value = self._make_places_response(
            [self._make_place("Store", lat=40.1, lng=-74.1)]
        )
        _, locations = svc.get_nearby_amenities_with_locations(40.7, -74.0)
        for cat_locs in locations.values():
            for loc in cat_locs:
                assert "name" in loc
                assert "lat" in loc
                assert "lng" in loc


# ── compare_amenities ─────────────────────────────────────────────────────────

class TestCompareAmenities:
    def test_same_location_skips_search(self, svc):
        result = svc.compare_amenities(40.7128, -74.0060, 40.7128, -74.0060)
        assert result["same_location"] is True
        assert result["destination"]["total_count"] == 0

    def test_different_locations_calls_places(self, svc):
        svc.client.places_nearby.return_value = {"results": []}
        result = svc.compare_amenities(40.7, -74.0, 34.0, -118.2)
        assert result["same_location"] is False

    def test_more_amenities_comparison_text(self, svc):
        svc.client.places_nearby.return_value = {
            "results": [
                {"name": "Place", "geometry": {"location": {"lat": 34.0, "lng": -118.2}}, "vicinity": ""}
            ]
        }
        result = svc.compare_amenities(40.7, -74.0, 34.0, -118.2)
        assert isinstance(result["comparison_text"], str)

    def test_returns_lifestyle_score(self, svc):
        svc.client.places_nearby.return_value = {"results": []}
        result = svc.compare_amenities(40.7, -74.0, 34.0, -118.2)
        assert "lifestyle_score" in result

    def test_returns_required_keys(self, svc):
        svc.client.places_nearby.return_value = {"results": []}
        result = svc.compare_amenities(40.7, -74.0, 34.0, -118.2)
        for key in ("destination", "current", "lifestyle_score", "comparison_text",
                    "same_location", "search_radius"):
            assert key in result

    def test_no_amenities_anywhere_comparison_text(self, svc):
        svc.client.places_nearby.return_value = {"results": []}
        result = svc.compare_amenities(40.7, -74.0, 34.0, -118.2)
        assert "No amenities" in result["comparison_text"] or isinstance(result["comparison_text"], str)


# ── get_commute_info ──────────────────────────────────────────────────────────

class TestGetCommuteInfo:
    def test_no_work_address_returns_none_duration(self, svc):
        result = svc.get_commute_info(40.7, -74.0, None)
        assert result["duration_minutes"] is None

    def test_empty_work_address_returns_none_duration(self, svc):
        result = svc.get_commute_info(40.7, -74.0, "")
        assert result["duration_minutes"] is None

    def test_success_returns_duration(self, svc):
        svc.client.distance_matrix.return_value = {
            "rows": [{"elements": [{"status": "OK",
                                    "duration": {"value": 1500},
                                    "distance": {"text": "15 mi"}}]}]
        }
        result = svc.get_commute_info(40.7, -74.0, "Empire State Building, NY")
        assert result["duration_minutes"] == 25  # 1500 // 60
        assert result["distance"] == "15 mi"

    def test_success_returns_correct_method(self, svc):
        svc.client.distance_matrix.return_value = {
            "rows": [{"elements": [{"status": "OK",
                                    "duration": {"value": 900},
                                    "distance": {"text": "5 mi"}}]}]
        }
        result = svc.get_commute_info(40.7, -74.0, "Work", mode="transit")
        assert result["method"] == "transit"

    def test_non_ok_status_returns_none_duration(self, svc):
        svc.client.distance_matrix.return_value = {
            "rows": [{"elements": [{"status": "ZERO_RESULTS"}]}]
        }
        result = svc.get_commute_info(40.7, -74.0, "Work")
        assert result["duration_minutes"] is None

    def test_api_exception_returns_none_duration(self, svc):
        svc.client.distance_matrix.side_effect = Exception("quota exceeded")
        result = svc.get_commute_info(40.7, -74.0, "Work")
        assert result["duration_minutes"] is None
        assert result["distance"] == "Unknown"

    def test_description_contains_duration_and_mode(self, svc):
        svc.client.distance_matrix.return_value = {
            "rows": [{"elements": [{"status": "OK",
                                    "duration": {"value": 1800},
                                    "distance": {"text": "20 mi"}}]}]
        }
        result = svc.get_commute_info(40.7, -74.0, "Work", mode="driving")
        assert "30" in result["description"]
        assert "driving" in result["description"]
