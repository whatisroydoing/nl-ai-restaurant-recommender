"""Pytest fixtures for Phase 1."""

import pytest

from restaurant_recommender.models import Preference, RestaurantRecord
from restaurant_recommender.data_store import RestaurantDataStore


@pytest.fixture
def sample_records():
    """Sample restaurant records for unit tests."""
    return [
        RestaurantRecord(
            name="Jalsa",
            location="Banashankari",
            listed_in_city="Banashankari",
            cuisines="North Indian, Mughlai, Chinese",
            approx_cost="800",
            rate="4.1/5",
            votes=775,
            rest_type="Casual Dining",
            dish_liked="Pasta, Lunch Buffet",
        ),
        RestaurantRecord(
            name="Spice Elephant",
            location="Banashankari",
            listed_in_city="Banashankari",
            cuisines="Chinese, North Indian, Thai",
            approx_cost="800",
            rate="4.1/5",
            votes=787,
            rest_type="Casual Dining",
        ),
        RestaurantRecord(
            name="Addhuri Udupi Bhojana",
            location="Banashankari",
            listed_in_city="Banashankari",
            cuisines="South Indian, North Indian",
            approx_cost="300",
            rate="3.7/5",
            votes=88,
            rest_type="Quick Bites",
        ),
        RestaurantRecord(
            name="Onesta",
            location="Banashankari",
            listed_in_city="Banashankari",
            cuisines="Pizza, Cafe, Italian",
            approx_cost="600",
            rate="4.6/5",
            votes=2556,
            rest_type="Casual Dining, Cafe",
        ),
        RestaurantRecord(
            name="Cafe in Koramangala",
            location="Koramangala",
            listed_in_city="Koramangala",
            cuisines="Cafe, Italian",
            approx_cost="500",
            rate="4.0/5",
            votes=100,
        ),
    ]


@pytest.fixture
def store(sample_records):
    """Data store preloaded with sample records."""
    s = RestaurantDataStore()
    s.load(sample_records)
    return s
