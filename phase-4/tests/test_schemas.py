"""Unit tests for schema serialization."""

from recommendation_api.schemas import (
    ErrorResponse,
    RecommendationItem,
    RecommendationResponse,
)


class TestRecommendationItem:
    def test_to_dict_full(self):
        item = RecommendationItem(
            rank=1,
            restaurant_name="Spice Garden",
            explanation="Great food.",
            attributes={"cuisines": "North Indian", "rating": 4.3},
        )
        d = item.to_dict()
        assert d["rank"] == 1
        assert d["restaurant_name"] == "Spice Garden"
        assert d["explanation"] == "Great food."
        assert d["attributes"]["cuisines"] == "North Indian"

    def test_to_dict_minimal(self):
        item = RecommendationItem(rank=1, restaurant_name="Test")
        d = item.to_dict()
        assert d["rank"] == 1
        assert d["restaurant_name"] == "Test"
        assert d["explanation"] is None
        assert d["attributes"] == {}


class TestRecommendationResponse:
    def test_to_dict(self):
        resp = RecommendationResponse(
            request_id="abc-123",
            model_used="gpt-4o-mini",
            filters_applied={"city": "Banashankari"},
            recommendations=[
                RecommendationItem(rank=1, restaurant_name="Spice Garden", explanation="Good."),
            ],
        )
        d = resp.to_dict()
        assert d["request_id"] == "abc-123"
        assert d["model_used"] == "gpt-4o-mini"
        assert d["filters_applied"] == {"city": "Banashankari"}
        assert len(d["recommendations"]) == 1
        assert d["recommendations"][0]["restaurant_name"] == "Spice Garden"

    def test_empty_recommendations(self):
        resp = RecommendationResponse(
            request_id="x",
            model_used="m",
            filters_applied={},
        )
        d = resp.to_dict()
        assert d["recommendations"] == []


class TestErrorResponse:
    def test_to_dict_with_request_id(self):
        err = ErrorResponse(error="Bad request", details=["oops"], request_id="r1")
        d = err.to_dict()
        assert d["error"] == "Bad request"
        assert d["details"] == ["oops"]
        assert d["request_id"] == "r1"

    def test_to_dict_without_request_id(self):
        err = ErrorResponse(error="Validation error", details=["field bad"])
        d = err.to_dict()
        assert "request_id" not in d
