from typing import Any, Mapping, Dict, List, Optional

from .models import ValidatedPreference, PreferenceValidationError


def _as_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _parse_int(field: str, value: Any, errors: List[str], minimum: Optional[int] = None) -> Optional[int]:
    if value is None:
        return None
    try:
        ivalue = int(str(value).strip())
    except (TypeError, ValueError):
        errors.append(f"{field} must be an integer")
        return None
    if minimum is not None and ivalue < minimum:
        errors.append(f"{field} must be >= {minimum}")
    return ivalue


def _parse_float(field: str, value: Any, errors: List[str], minimum: Optional[float] = None, maximum: Optional[float] = None) -> Optional[float]:
    if value is None:
        return None
    try:
        fvalue = float(str(value).strip())
    except (TypeError, ValueError):
        errors.append(f"{field} must be a number")
        return None
    if minimum is not None and fvalue < minimum:
        errors.append(f"{field} must be >= {minimum}")
    if maximum is not None and fvalue > maximum:
        errors.append(f"{field} must be <= {maximum}")
    return fvalue


def validate_preference(raw: Mapping[str, Any]) -> ValidatedPreference:
    """
    Validate a raw preference mapping and return a normalized ValidatedPreference.

    Unknown keys result in validation errors.
    """
    allowed_keys = {
        "city",
        "location",
        "price_min",
        "price_max",
        "min_rating",
        "cuisine",
        "max_results",
    }

    errors: List[str] = []

    # Detect unknown keys early
    unknown = sorted(set(raw.keys()) - allowed_keys)
    if unknown:
        errors.append(f"Unknown fields: {', '.join(unknown)}")

    # Strings
    city = _as_str(raw.get("city"))
    location = _as_str(raw.get("location"))
    cuisine = _as_str(raw.get("cuisine"))

    # Numeric fields
    price_min = _parse_int("price_min", raw.get("price_min"), errors, minimum=0)
    price_max = _parse_int("price_max", raw.get("price_max"), errors, minimum=0)

    min_rating = _parse_float("min_rating", raw.get("min_rating"), errors, minimum=0.0, maximum=5.0)

    max_results = _parse_int("max_results", raw.get("max_results"), errors, minimum=1)
    if max_results is not None and max_results > 100:
        errors.append("max_results must be <= 100")

    # Cross-field rules
    if price_min is not None and price_max is not None and price_min > price_max:
        errors.append("price_min must be less than or equal to price_max")

    if errors:
        raise PreferenceValidationError(errors)

    return ValidatedPreference(
        city=city,
        location=location,
        price_min=price_min,
        price_max=price_max,
        min_rating=min_rating,
        cuisine=cuisine,
        max_results=max_results,
    )

