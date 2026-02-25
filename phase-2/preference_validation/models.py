from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ValidatedPreference:
    """Normalized, type-safe preference object used by downstream components."""

    city: Optional[str] = None
    location: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    min_rating: Optional[float] = None
    cuisine: Optional[str] = None
    max_results: Optional[int] = None


class PreferenceValidationError(ValueError):
    """Raised when raw preference input fails validation."""

    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        message = "; ".join(errors) if errors else "Invalid preferences"
        super().__init__(message)

