"""End-to-end tests for the POST /recommend endpoint."""

from __future__ import annotations

import json


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"


# ═══════════════════════════════════════════════════════════════════
# Metadata endpoint
# ═══════════════════════════════════════════════════════════════════

class TestMetadataEndpoint:
    def test_metadata_returns_200(self, client):
        resp = client.get("/metadata")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "areas" in data
        assert "cuisines" in data
        assert isinstance(data["areas"], list)
        assert isinstance(data["cuisines"], list)

    def test_metadata_areas_are_sorted(self, client):
        data = client.get("/metadata").get_json()
        areas = data["areas"]
        assert areas == sorted(areas, key=str.lower)

    def test_metadata_cuisines_are_sorted(self, client):
        data = client.get("/metadata").get_json()
        cuisines = data["cuisines"]
        assert cuisines == sorted(cuisines, key=str.lower)

    def test_metadata_areas_are_unique(self, client):
        data = client.get("/metadata").get_json()
        areas = data["areas"]
        # FAKE_RECORDS has two "Banashankari" records → should still be one area
        assert len(areas) == len(set(areas))

    def test_metadata_cuisines_are_split_and_unique(self, client):
        """Comma-separated cuisines like 'North Indian, Chinese' are split into individual entries."""
        data = client.get("/metadata").get_json()
        cuisines = data["cuisines"]
        assert "North Indian" in cuisines
        assert "Chinese" in cuisines
        assert "Italian" in cuisines
        assert "Continental" in cuisines
        assert "South Indian" in cuisines
        assert "Street Food" in cuisines
        assert len(cuisines) == len(set(cuisines))

    def test_metadata_has_cors_headers(self, client):
        resp = client.get("/metadata")
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"


# ═══════════════════════════════════════════════════════════════════
# Recommendation happy path
# ═══════════════════════════════════════════════════════════════════

class TestRecommendHappyPath:
    def test_valid_request_returns_200(self, client):
        resp = client.post(
            "/recommend",
            json={"city": "Banashankari", "min_rating": 3.5, "max_results": 2},
        )
        assert resp.status_code == 200
        data = resp.get_json()

        # Metadata present
        assert "request_id" in data
        assert data["model_used"] == "test-model"
        assert data["filters_applied"]["city"] == "Banashankari"
        assert data["filters_applied"]["min_rating"] == 3.5

        # Recommendations list
        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) <= 2
        for rec in data["recommendations"]:
            assert "rank" in rec
            assert "restaurant_name" in rec
            assert "explanation" in rec
            assert "attributes" in rec

    def test_empty_body_returns_all_results(self, client):
        """All filters are optional — empty body is valid and returns results."""
        resp = client.post("/recommend", json={})
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) > 0
        assert data["filters_applied"] == {}

    def test_cuisine_filter(self, client):
        resp = client.post("/recommend", json={"cuisine": "Italian"})
        assert resp.status_code == 200
        data = resp.get_json()
        # Should find Pasta Palace
        names = [r["restaurant_name"] for r in data["recommendations"]]
        assert any("Pasta" in n for n in names)

    def test_recommendations_have_sequential_ranks(self, client):
        resp = client.post("/recommend", json={"city": "Banashankari"})
        assert resp.status_code == 200
        recs = resp.get_json()["recommendations"]
        if recs:
            ranks = [r["rank"] for r in recs]
            assert ranks == list(range(1, len(ranks) + 1))

    def test_location_filter(self, client):
        """Test filtering by location (used by the frontend 'Area' dropdown)."""
        resp = client.post("/recommend", json={"location": "Koramangala"})
        assert resp.status_code == 200
        recs = resp.get_json()["recommendations"]
        names = [r["restaurant_name"] for r in recs]
        assert any("Pasta" in n for n in names)

    def test_price_range_boundaries(self, client):
        """Exact boundary value for price_max should include matching restaurants."""
        resp = client.post("/recommend", json={"price_max": 500})
        assert resp.status_code == 200
        recs = resp.get_json()["recommendations"]
        names = [r["restaurant_name"] for r in recs]
        # Budget Bites (200) and Spice Garden (500) should match
        assert any("Budget" in n or "Spice" in n for n in names)


# ═══════════════════════════════════════════════════════════════════
# Deduplication
# ═══════════════════════════════════════════════════════════════════

class TestDeduplication:
    def test_duplicate_restaurants_are_removed(self, client):
        """Two records with name='Spice Garden' should produce only one recommendation."""
        resp = client.post("/recommend", json={"location": "Banashankari"})
        assert resp.status_code == 200
        recs = resp.get_json()["recommendations"]
        names = [r["restaurant_name"] for r in recs]
        assert names.count("Spice Garden") <= 1

    def test_dedup_keeps_highest_rated(self, client):
        """The deduped Spice Garden should be the 4.3 one, not the 3.8 one."""
        resp = client.post("/recommend", json={"location": "Banashankari"})
        assert resp.status_code == 200
        recs = resp.get_json()["recommendations"]
        for rec in recs:
            if rec["restaurant_name"] == "Spice Garden":
                # The 4.3 one has votes=320
                attrs = rec.get("attributes", {})
                if "rating" in attrs:
                    assert float(attrs["rating"]) >= 4.3
                break

    def test_dedup_is_case_insensitive(self, client):
        """' pasta palace  ' and 'Pasta Palace' should be treated as the same restaurant."""
        resp = client.post("/recommend", json={})
        assert resp.status_code == 200
        recs = resp.get_json()["recommendations"]
        pasta_count = sum(
            1 for r in recs
            if "pasta" in r["restaurant_name"].lower()
        )
        assert pasta_count <= 1

    def test_no_duplicates_in_full_results(self, client):
        """With no filters, all returned restaurant names should be unique."""
        resp = client.post("/recommend", json={})
        assert resp.status_code == 200
        recs = resp.get_json()["recommendations"]
        names = [r["restaurant_name"].strip().lower() for r in recs]
        assert len(names) == len(set(names))


# ═══════════════════════════════════════════════════════════════════
# CORS headers
# ═══════════════════════════════════════════════════════════════════

class TestCORSHeaders:
    def test_cors_on_get(self, client):
        resp = client.get("/health")
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"

    def test_cors_on_post(self, client):
        resp = client.post("/recommend", json={})
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"
        assert "POST" in resp.headers.get("Access-Control-Allow-Methods", "")

    def test_cors_allows_content_type_header(self, client):
        resp = client.post("/recommend", json={})
        assert "Content-Type" in resp.headers.get("Access-Control-Allow-Headers", "")


# ═══════════════════════════════════════════════════════════════════
# Validation errors
# ═══════════════════════════════════════════════════════════════════

class TestRecommendValidationErrors:
    def test_invalid_min_rating_returns_422(self, client):
        resp = client.post(
            "/recommend",
            json={"min_rating": "not-a-number"},
        )
        assert resp.status_code == 422
        data = resp.get_json()
        assert data["error"] == "Validation error"
        assert len(data["details"]) > 0

    def test_unknown_field_returns_422(self, client):
        resp = client.post(
            "/recommend",
            json={"city": "Banashankari", "unknown_field": "value"},
        )
        assert resp.status_code == 422
        data = resp.get_json()
        assert "Unknown fields" in data["details"][0]

    def test_price_min_greater_than_max_returns_422(self, client):
        resp = client.post(
            "/recommend",
            json={"price_min": 1000, "price_max": 200},
        )
        assert resp.status_code == 422

    def test_rating_out_of_range_returns_422(self, client):
        resp = client.post(
            "/recommend",
            json={"min_rating": 6.0},
        )
        assert resp.status_code == 422

    def test_negative_price_returns_422(self, client):
        resp = client.post(
            "/recommend",
            json={"price_min": -100},
        )
        assert resp.status_code == 422

    def test_negative_rating_returns_422(self, client):
        resp = client.post(
            "/recommend",
            json={"min_rating": -1.0},
        )
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════
# Bad requests
# ═══════════════════════════════════════════════════════════════════

class TestRecommendBadRequest:
    def test_non_json_body_returns_400(self, client):
        resp = client.post(
            "/recommend",
            data="this is not json",
            content_type="text/plain",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"] == "Bad request"

    def test_empty_request_no_content_type_returns_400(self, client):
        resp = client.post("/recommend")
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════
# No results / edge cases
# ═══════════════════════════════════════════════════════════════════

class TestRecommendEdgeCases:
    def test_very_specific_filters_returns_empty_list(self, client):
        """Filters that match nothing should return 200 with empty recs."""
        resp = client.post(
            "/recommend",
            json={"city": "NonExistentCity", "min_rating": 5.0},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["recommendations"] == []
        assert "request_id" in data

    def test_max_results_one(self, client):
        """Only one result when max_results=1."""
        resp = client.post("/recommend", json={"max_results": 1})
        assert resp.status_code == 200
        recs = resp.get_json()["recommendations"]
        assert len(recs) <= 1

    def test_all_optional_fields_together(self, client):
        """Submit every filter at once."""
        resp = client.post("/recommend", json={
            "city": "Banashankari",
            "location": "Banashankari",
            "cuisine": "North Indian",
            "price_min": 400,
            "price_max": 700,
            "min_rating": 3.5,
            "max_results": 5,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data["recommendations"], list)
        assert data["filters_applied"]["city"] == "Banashankari"
        assert data["filters_applied"]["cuisine"] == "North Indian"

    def test_response_has_request_id(self, client):
        """Every response should include a unique request_id."""
        resp1 = client.post("/recommend", json={})
        resp2 = client.post("/recommend", json={})
        id1 = resp1.get_json()["request_id"]
        id2 = resp2.get_json()["request_id"]
        assert id1 != id2

    def test_boundary_rating_zero(self, client):
        """min_rating of 0 should be valid and return all."""
        resp = client.post("/recommend", json={"min_rating": 0})
        assert resp.status_code == 200
        recs = resp.get_json()["recommendations"]
        assert len(recs) > 0

    def test_boundary_rating_five(self, client):
        """min_rating of 5.0 is valid but may return empty."""
        resp = client.post("/recommend", json={"min_rating": 5.0})
        assert resp.status_code == 200
