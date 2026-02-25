import os
import sys
from pathlib import Path

import pytest

# Ensure the phase-2 package is importable when running tests directly.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from preference_validation import (  # type: ignore  # imported via sys.path tweak
    ValidatedPreference,
    PreferenceValidationError,
    validate_preference,
)


def test_valid_minimal_preferences():
    raw = {
        "city": "Banashankari",
        "min_rating": "4.0",
    }

    pref = validate_preference(raw)
    assert isinstance(pref, ValidatedPreference)
    assert pref.city == "Banashankari"
    assert pref.location is None
    assert pref.min_rating == pytest.approx(4.0)


def test_whitespace_and_empty_strings_are_normalized():
    raw = {
        "city": "  Koramangala  ",
        "location": "   ",
        "cuisine": "",
    }
    pref = validate_preference(raw)
    assert pref.city == "Koramangala"
    assert pref.location is None
    assert pref.cuisine is None


def test_price_range_and_cross_field_validation():
    raw = {
        "price_min": "100",
        "price_max": "500",
    }
    pref = validate_preference(raw)
    assert pref.price_min == 100
    assert pref.price_max == 500


def test_price_min_greater_than_price_max_is_error():
    raw = {
        "price_min": 600,
        "price_max": 500,
    }
    with pytest.raises(PreferenceValidationError) as exc:
        validate_preference(raw)
    msg = str(exc.value)
    assert "price_min must be less than or equal to price_max" in msg


def test_min_rating_must_be_between_0_and_5():
    raw = {"min_rating": 6.0}
    with pytest.raises(PreferenceValidationError) as exc:
        validate_preference(raw)
    assert "min_rating must be <=" in str(exc.value)


def test_max_results_must_be_positive_and_capped():
    raw = {"max_results": 0}
    with pytest.raises(PreferenceValidationError) as exc:
        validate_preference(raw)
    assert "max_results must be >=" in str(exc.value)

    raw2 = {"max_results": 101}
    with pytest.raises(PreferenceValidationError) as exc2:
        validate_preference(raw2)
    assert "max_results must be <= 100" in str(exc2.value)


def test_unknown_fields_raise_error():
    raw = {"city": "Banashankari", "min_raing": 4.0}
    with pytest.raises(PreferenceValidationError) as exc:
        validate_preference(raw)
    assert "Unknown fields" in str(exc.value)

