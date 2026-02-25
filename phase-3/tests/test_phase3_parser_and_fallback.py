import json

import pytest

from llm_recommender.models import CandidateRestaurant, RecommendSettings
from llm_recommender.parser import parse_recommendations
from llm_recommender.recommender import recommend_with_explanations


def test_parser_accepts_json_array():
    raw = json.dumps(
        [
            {"rank": 1, "restaurant_name": "A", "explanation": "Because."},
            {"rank": 2, "restaurant_name": "B", "explanation": "Also because."},
        ]
    )
    parsed = parse_recommendations(raw)
    assert len(parsed.recommendations) == 2
    assert parsed.recommendations[0].restaurant_name == "A"


def test_parser_extracts_array_from_wrapped_text():
    wrapped = "Sure, here you go:\n" + json.dumps([{"restaurant_name": "A", "explanation": "X"}]) + "\nThanks!"
    parsed = parse_recommendations(wrapped)
    assert parsed.recommendations[0].restaurant_name == "A"


class FakeClient:
    def __init__(self, response: str):
        self.response = response

    def generate(self, *, model: str, messages, timeout_s: float) -> str:
        return self.response


def test_recommender_uses_llm_when_json_is_valid():
    candidates = [
        CandidateRestaurant(name="Onesta", cuisines="Italian", rate="4.6/5", approx_cost="600", location="Banashankari"),
        CandidateRestaurant(name="Addhuri Udupi Bhojana", cuisines="South Indian", rate="3.9/5", approx_cost="300", location="Banashankari"),
    ]
    llm_json = json.dumps(
        [
            {"rank": 1, "restaurant_name": "Addhuri Udupi Bhojana", "explanation": "Cheap and tasty."},
            {"rank": 2, "restaurant_name": "Onesta", "explanation": "Higher rating."},
        ]
    )
    out = recommend_with_explanations(
        preference={"city": "Banashankari", "max_results": 2},
        candidates=candidates,
        client=FakeClient(llm_json),
        settings=RecommendSettings(max_results=2, top_k_candidates=10),
    )
    assert [r.restaurant_name for r in out] == ["Addhuri Udupi Bhojana", "Onesta"]
    assert out[0].explanation


def test_recommender_falls_back_on_invalid_json():
    candidates = [
        CandidateRestaurant(name="Onesta", cuisines="Italian", rate="4.6/5", approx_cost="600", location="Banashankari"),
        CandidateRestaurant(name="Addhuri Udupi Bhojana", cuisines="South Indian", rate="3.9/5", approx_cost="300", location="Banashankari"),
    ]
    out = recommend_with_explanations(
        preference={"city": "Banashankari", "max_results": 2},
        candidates=candidates,
        client=FakeClient("not json"),
        settings=RecommendSettings(max_results=2, top_k_candidates=10),
    )
    assert [r.restaurant_name for r in out] == ["Onesta", "Addhuri Udupi Bhojana"]
    assert all(r.explanation for r in out)


def test_recommender_ignores_unknown_restaurant_and_fills_remaining():
    candidates = [
        CandidateRestaurant(name="Onesta", cuisines="Italian", rate="4.6/5", approx_cost="600", location="Banashankari"),
        CandidateRestaurant(name="Addhuri Udupi Bhojana", cuisines="South Indian", rate="3.9/5", approx_cost="300", location="Banashankari"),
        CandidateRestaurant(name="Spice Elephant", cuisines="Thai", rate="4.1/5", approx_cost="800", location="Indiranagar"),
    ]
    llm_json = json.dumps(
        [
            {"rank": 1, "restaurant_name": "Not In List", "explanation": "Nope."},
            {"rank": 2, "restaurant_name": "Onesta", "explanation": "Good rating."},
        ]
    )
    out = recommend_with_explanations(
        preference={"max_results": 2},
        candidates=candidates,
        client=FakeClient(llm_json),
        settings=RecommendSettings(max_results=2, top_k_candidates=10),
    )
    # Should keep Onesta and fill second slot from remaining candidates (retrieval order)
    assert out[0].restaurant_name == "Onesta"
    assert len(out) == 2
    assert out[1].restaurant_name in {"Addhuri Udupi Bhojana", "Spice Elephant"}

