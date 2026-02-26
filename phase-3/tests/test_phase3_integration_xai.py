import os

import pytest

from llm_recommender import CandidateRestaurant, RecommendSettings, XAIChatCompletionsClient, recommend_with_explanations


@pytest.mark.integration
def test_phase3_xai_integration_smoke():
    """
    Optional integration test.
    Runs only if XAI_API_KEY is set in the environment.
    """
    if not os.environ.get("XAI_API_KEY"):
        pytest.skip("XAI_API_KEY not set")

    candidates = [
        CandidateRestaurant(name="Onesta", cuisines="Italian", rate="4.6/5", approx_cost="600", location="Banashankari"),
        CandidateRestaurant(name="Spice Elephant", cuisines="Thai", rate="4.1/5", approx_cost="800", location="Indiranagar"),
        CandidateRestaurant(name="Addhuri Udupi Bhojana", cuisines="South Indian", rate="3.9/5", approx_cost="300", location="Banashankari"),
    ]

    client = XAIChatCompletionsClient()
    out = recommend_with_explanations(
        preference={"city": "Banashankari", "cuisine": "Italian", "max_results": 2},
        candidates=candidates,
        client=client,
        settings=RecommendSettings(max_results=2, top_k_candidates=3, timeout_s=30.0),
    )

    assert len(out) == 2
    assert all(r.restaurant_name for r in out)
    assert all(r.explanation for r in out)

