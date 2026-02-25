"""Canonical models for Phase 1: Preference and RestaurantRecord."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Preference:
    """User preference object for filtering restaurants."""

    price_min: Optional[int] = None  # approx cost for two (min)
    price_max: Optional[int] = None  # approx cost for two (max)
    location: Optional[str] = None   # area/neighborhood (dataset: location)
    city: Optional[str] = None      # dataset: listed_in(city)
    min_rating: Optional[float] = None  # e.g. 4.0
    cuisine: Optional[str] = None   # substring match on cuisines


@dataclass
class RestaurantRecord:
    """Canonical restaurant record for retrieval and downstream use."""

    name: str
    address: Optional[str] = None
    location: Optional[str] = None
    listed_in_city: Optional[str] = None
    cuisines: Optional[str] = None
    approx_cost: Optional[str] = None  # keep as string from dataset (e.g. "800")
    rate: Optional[str] = None         # e.g. "4.1/5"
    votes: Optional[int] = None
    rest_type: Optional[str] = None
    dish_liked: Optional[str] = None
    online_order: Optional[str] = None
    book_table: Optional[str] = None
    url: Optional[str] = None
    phone: Optional[str] = None

    @property
    def rating_numeric(self) -> Optional[float]:
        """Parse rate to float (e.g. '4.1/5' -> 4.1)."""
        if not self.rate:
            return None
        try:
            part = self.rate.strip().split("/")[0].strip()
            return float(part)
        except (ValueError, IndexError):
            return None

    @property
    def cost_numeric(self) -> Optional[int]:
        """Parse approx_cost to int (e.g. '800' or '1,000' -> 800 / 1000)."""
        if not self.approx_cost:
            return None
        try:
            cleaned = str(self.approx_cost).replace(",", "").strip()
            return int(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None
