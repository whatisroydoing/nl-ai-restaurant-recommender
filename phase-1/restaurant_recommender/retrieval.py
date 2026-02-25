"""Retrieval component: preference -> filtered list of restaurant records."""

from typing import List, Optional

from .models import Preference, RestaurantRecord
from .data_store import RestaurantDataStore


def retrieve(
    store: RestaurantDataStore,
    preference: Preference,
    sort_by_rating: bool = True,
    top_k: Optional[int] = None,
) -> List[RestaurantRecord]:
    """
    Return restaurants matching the preference, optionally sorted by rating (desc)
    and limited to top_k.
    """
    candidates = store.query_by_preference(preference)
    if sort_by_rating:
        candidates = sorted(
            candidates,
            key=lambda r: (r.rating_numeric or 0.0, r.votes or 0),
            reverse=True,
        )
    if top_k is not None and top_k > 0:
        candidates = candidates[:top_k]
    return candidates
