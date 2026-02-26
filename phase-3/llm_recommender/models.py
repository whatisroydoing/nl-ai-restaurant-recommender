from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CandidateRestaurant:
    name: str
    address: Optional[str] = None
    location: Optional[str] = None
    listed_in_city: Optional[str] = None
    cuisines: Optional[str] = None
    approx_cost: Optional[str] = None
    rate: Optional[str] = None
    votes: Optional[int] = None
    rest_type: Optional[str] = None
    dish_liked: Optional[str] = None
    online_order: Optional[str] = None
    book_table: Optional[str] = None

    @property
    def rating_numeric(self) -> Optional[float]:
        if not self.rate:
            return None
        try:
            part = str(self.rate).strip().split("/")[0].strip()
            return float(part)
        except (ValueError, IndexError):
            return None

    @property
    def cost_numeric(self) -> Optional[int]:
        if self.approx_cost is None:
            return None
        try:
            cleaned = str(self.approx_cost).replace(",", "").strip()
            return int(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None

    def to_prompt_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": self.name,
            "city": self.listed_in_city,
            "location": self.location,
            "cuisines": self.cuisines,
            "approx_cost_for_two": self.cost_numeric if self.cost_numeric is not None else self.approx_cost,
            "rating": self.rating_numeric if self.rating_numeric is not None else self.rate,
            "votes": self.votes,
            "rest_type": self.rest_type,
            "dish_liked": self.dish_liked,
            "online_order": self.online_order,
            "book_table": self.book_table,
        }
        return {k: v for k, v in data.items() if v is not None and v != ""}


@dataclass(frozen=True)
class Recommendation:
    rank: int
    restaurant_name: str
    explanation: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None


class LLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class RecommendSettings:
    model: str = "grok-2-latest"
    top_k_candidates: int = 12
    max_results: int = 5
    timeout_s: float = 20.0

