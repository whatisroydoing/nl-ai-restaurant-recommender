"""Phase 1 tests: loader, data store, retrieval, and end-to-end."""

import pytest

from restaurant_recommender.models import Preference, RestaurantRecord
from restaurant_recommender.loader import load_dataset_from_hf
from restaurant_recommender.data_store import RestaurantDataStore
from restaurant_recommender.retrieval import retrieve


# --- Unit: Data store filtering ---

def test_data_store_load_and_query_by_city(store):
    results = store.query(city="Banashankari")
    # In sample_records, 4 of 5 restaurants have listed_in_city = "Banashankari"
    assert len(results) == 4
    assert all(r.listed_in_city and "Banashankari" in r.listed_in_city for r in results)


def test_data_store_filter_by_location(store):
    results = store.query(location="Koramangala")
    assert len(results) == 1
    assert results[0].name == "Cafe in Koramangala"


def test_data_store_filter_by_price(store):
    results = store.query(price_max=400)
    assert len(results) == 1
    assert results[0].name == "Addhuri Udupi Bhojana"
    assert results[0].approx_cost == "300"


def test_data_store_filter_by_min_rating(store):
    results = store.query(min_rating=4.2)
    assert len(results) == 1
    assert results[0].name == "Onesta"
    assert results[0].rate == "4.6/5"


def test_data_store_filter_by_cuisine(store):
    results = store.query(cuisine="Thai")
    assert len(results) == 1
    assert results[0].name == "Spice Elephant"


def test_data_store_combined_filters(store):
    results = store.query(
        city="Banashankari",
        min_rating=4.0,
        price_max=700,
    )
    assert len(results) == 1
    assert results[0].name == "Onesta"


# --- Unit: Preference and retrieval ---

def test_retrieve_by_preference_returns_list(store):
    pref = Preference(city="Banashankari", min_rating=4.0)
    results = retrieve(store, pref, sort_by_rating=True)
    assert isinstance(results, list)
    assert len(results) >= 1
    assert all(isinstance(r, RestaurantRecord) for r in results)


def test_retrieve_sorted_by_rating_desc(store):
    pref = Preference(city="Banashankari")
    results = retrieve(store, pref, sort_by_rating=True)
    assert results[0].name == "Onesta"
    assert results[0].rating_numeric == 4.6
    ratings = [r.rating_numeric or 0 for r in results]
    assert ratings == sorted(ratings, reverse=True)


def test_retrieve_respects_top_k(store):
    pref = Preference(city="Banashankari")
    results = retrieve(store, pref, sort_by_rating=True, top_k=2)
    assert len(results) == 2


def test_retrieve_empty_preference_returns_all(store):
    pref = Preference()
    results = retrieve(store, pref, sort_by_rating=False)
    assert len(results) == 5


# --- Unit: RestaurantRecord helpers ---

def test_restaurant_record_rating_numeric():
    r = RestaurantRecord(name="X", rate="4.1/5")
    assert r.rating_numeric == 4.1
    r2 = RestaurantRecord(name="Y", rate=None)
    assert r2.rating_numeric is None


def test_restaurant_record_cost_numeric():
    r = RestaurantRecord(name="X", approx_cost="800")
    assert r.cost_numeric == 800
    r2 = RestaurantRecord(name="Y", approx_cost="1,000")
    assert r2.cost_numeric == 1000


# --- Integration: real Hugging Face load + retrieval ---

@pytest.mark.integration
def test_phase1_e2e_load_from_hf_and_retrieve():
    """Load dataset via Hugging Face API, build store, run retrieval. Requires network."""
    records = load_dataset_from_hf()
    assert len(records) > 0
    assert all(isinstance(r, RestaurantRecord) for r in records)
    assert records[0].name

    store = RestaurantDataStore(records)
    pref = Preference(city="Banashankari", min_rating=3.5)
    results = retrieve(store, pref, sort_by_rating=True, top_k=10)
    assert len(results) <= 10
    assert len(results) > 0
    for r in results:
        assert r.listed_in_city and "Banashankari" in r.listed_in_city
        assert (r.rating_numeric or 0) >= 3.5
