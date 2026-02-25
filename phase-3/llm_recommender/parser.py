from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .models import Recommendation


@dataclass(frozen=True)
class ParsedLLMResult:
    recommendations: List[Recommendation]
    parse_warnings: List[str]


def _extract_json_array(text: str) -> str:
    """
    Best-effort extraction of a JSON array from free-form text.
    """
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON array found")
    return text[start : end + 1]


def parse_recommendations(text: str) -> ParsedLLMResult:
    warnings: List[str] = []
    candidate = text.strip()
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        candidate = _extract_json_array(candidate)
        data = json.loads(candidate)

    if not isinstance(data, list):
        raise ValueError("Expected a JSON array")

    recs: List[Recommendation] = []
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            warnings.append(f"Item {i} is not an object; skipped")
            continue

        name = item.get("restaurant_name") or item.get("name") or item.get("restaurant")
        if not name or not isinstance(name, str):
            warnings.append(f"Item {i} missing restaurant_name; skipped")
            continue

        rank_val = item.get("rank")
        if isinstance(rank_val, int):
            rank = rank_val
        else:
            rank = i
            if rank_val is not None:
                warnings.append(f"Item {i} rank is not int; using position")

        explanation = item.get("explanation")
        if explanation is not None and not isinstance(explanation, str):
            warnings.append(f"Item {i} explanation is not string; dropped")
            explanation = None

        attrs = item.get("attributes")
        if attrs is not None and not isinstance(attrs, dict):
            warnings.append(f"Item {i} attributes is not object; dropped")
            attrs = None

        recs.append(
            Recommendation(
                rank=rank,
                restaurant_name=name.strip(),
                explanation=explanation.strip() if isinstance(explanation, str) else None,
                attributes=attrs,
            )
        )

    if not recs:
        raise ValueError("No valid recommendations parsed")

    return ParsedLLMResult(recommendations=recs, parse_warnings=warnings)

