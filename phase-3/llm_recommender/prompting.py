from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from .models import CandidateRestaurant


SYSTEM_PROMPT = """You are a restaurant recommendation assistant.

You will be given:
- a user preference object
- a list of candidate restaurants (bounded top-K)

Rules:
- ONLY recommend restaurants from the provided candidates.
- Output MUST be valid JSON only (no markdown, no prose).
- Keep explanations short (1-2 sentences).
- Do not hallucinate attributes that aren't in the candidate list.

Output format (JSON array):
[
  {
    "rank": 1,
    "restaurant_name": "Exact Candidate Name",
    "explanation": "Short reason based on preferences and candidate fields"
  }
]
"""


def _pref_to_dict(preference: Any) -> Dict[str, Any]:
    """
    Best-effort conversion for preference objects from Phase 2 or dict-like inputs.
    """
    if isinstance(preference, Mapping):
        raw = dict(preference)
    elif hasattr(preference, "__dict__"):
        raw = dict(vars(preference))
    else:
        # Last resort: pull a small known set of attributes.
        raw = {}
        for k in ("city", "location", "price_min", "price_max", "min_rating", "cuisine", "max_results"):
            if hasattr(preference, k):
                raw[k] = getattr(preference, k)

    allowed = {
        "city",
        "location",
        "price_min",
        "price_max",
        "min_rating",
        "cuisine",
        "max_results",
    }
    cleaned: Dict[str, Any] = {}
    for k in allowed:
        v = raw.get(k)
        if v is None or v == "":
            continue
        cleaned[k] = v
    return cleaned


def build_messages(
    preference: Any,
    candidates: Iterable[CandidateRestaurant],
    desired_results: int,
) -> List[Dict[str, str]]:
    pref_dict = _pref_to_dict(preference)
    candidate_payload = [c.to_prompt_dict() for c in candidates]

    user_payload = {
        "preferences": pref_dict,
        "desired_results": desired_results,
        "candidates": candidate_payload,
    }

    return [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]

