"""Shared fixtures for Phase 4 tests."""

from __future__ import annotations

import os
import sys

import pytest

# ── Path setup so phase-1/2/3 packages are importable ─────────────────────
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
for _phase in ("phase-1", "phase-2", "phase-3", "phase-4"):
    _p = os.path.join(_PROJECT_ROOT, _phase)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from restaurant_recommender.models import RestaurantRecord
from restaurant_recommender.data_store import RestaurantDataStore
from recommendation_api.app import create_app
from llm_recommender.models import RecommendSettings


# ── Fake data ──────────────────────────────────────────────────────────────

FAKE_RECORDS = [
    RestaurantRecord(
        name="Spice Garden",
        location="Banashankari",
        listed_in_city="Banashankari",
        cuisines="North Indian, Chinese",
        approx_cost="500",
        rate="4.3/5",
        votes=320,
        rest_type="Casual Dining",
        online_order="Yes",
        book_table="Yes",
    ),
    RestaurantRecord(
        name="Tandoori Nights",
        location="Banashankari",
        listed_in_city="Banashankari",
        cuisines="North Indian",
        approx_cost="600",
        rate="4.0/5",
        votes=210,
        rest_type="Casual Dining",
        online_order="Yes",
        book_table="No",
    ),
    RestaurantRecord(
        name="Pasta Palace",
        location="Koramangala",
        listed_in_city="Koramangala 5th Block",
        cuisines="Italian, Continental",
        approx_cost="800",
        rate="4.5/5",
        votes=450,
        rest_type="Fine Dining",
        online_order="No",
        book_table="Yes",
    ),
    RestaurantRecord(
        name="Budget Bites",
        location="Jayanagar",
        listed_in_city="Jayanagar",
        cuisines="South Indian, Street Food",
        approx_cost="200",
        rate="3.2/5",
        votes=85,
        rest_type="Quick Bites",
        online_order="Yes",
        book_table="No",
    ),
    # ── Duplicates for dedup testing ──────────────────────────────
    # Same name as "Spice Garden" but listed under a different category
    RestaurantRecord(
        name="Spice Garden",
        location="Banashankari",
        listed_in_city="Banashankari",
        cuisines="North Indian, Chinese",
        approx_cost="500",
        rate="3.8/5",            # lower rating — should be deduped away
        votes=120,
        rest_type="Delivery",
        online_order="Yes",
        book_table="No",
    ),
    # Same name with different casing
    RestaurantRecord(
        name="  pasta palace  ",
        location="Koramangala",
        listed_in_city="Koramangala 5th Block",
        cuisines="Italian",
        approx_cost="800",
        rate="4.2/5",            # lower rating — should be deduped away
        votes=200,
        rest_type="Delivery",
        online_order="Yes",
        book_table="No",
    ),
]


@pytest.fixture()
def fake_store() -> RestaurantDataStore:
    """A RestaurantDataStore loaded with a handful of fake records."""
    return RestaurantDataStore(FAKE_RECORDS)


@pytest.fixture()
def app(fake_store):
    """Flask test app with fake data and default (fallback) LLM settings."""
    application = create_app(
        store=fake_store,
        settings=RecommendSettings(model="test-model"),
    )
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()
