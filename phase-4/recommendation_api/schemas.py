"""Request/response schemas for the recommendation API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RecommendationItem:
    """A single ranked recommendation in the API response."""

    rank: int
    restaurant_name: str
    explanation: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "restaurant_name": self.restaurant_name,
            "explanation": self.explanation,
            "attributes": self.attributes or {},
        }


@dataclass
class RecommendationResponse:
    """Full API response for POST /recommend."""

    request_id: str
    model_used: str
    filters_applied: Dict[str, Any]
    recommendations: List[RecommendationItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "model_used": self.model_used,
            "filters_applied": self.filters_applied,
            "recommendations": [r.to_dict() for r in self.recommendations],
        }


@dataclass
class ErrorResponse:
    """Standard JSON error response."""

    error: str
    details: List[str] = field(default_factory=list)
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "error": self.error,
            "details": self.details,
        }
        if self.request_id:
            d["request_id"] = self.request_id
        return d
