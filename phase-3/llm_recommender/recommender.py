from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence

from .models import (
    CandidateRestaurant,
    RecommendSettings,
    Recommendation,
)
from .openai_client import LLMClient, OpenAIChatCompletionsClient
from .parser import ParsedLLMResult, parse_recommendations
from .prompting import build_messages


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _template_explanation(preference: Any, candidate: CandidateRestaurant) -> str:
    parts: List[str] = []

    if candidate.rating_numeric is not None:
        parts.append(f"Rated {candidate.rating_numeric:.1f}")
    elif candidate.rate:
        parts.append(f"Rated {candidate.rate}")

    if candidate.cuisines:
        parts.append(f"serves {candidate.cuisines}")
    if candidate.cost_numeric is not None:
        parts.append(f"approx. ₹{candidate.cost_numeric} for two")
    elif candidate.approx_cost:
        parts.append(f"approx. cost {candidate.approx_cost} for two")
    if candidate.location or candidate.listed_in_city:
        where = ", ".join([x for x in [candidate.location, candidate.listed_in_city] if x])
        parts.append(f"in {where}")

    if not parts:
        return "Matches your preferences."
    sentence = ", ".join(parts[:4])
    return sentence + "."


def _coerce_candidates(items: Iterable[Any]) -> List[CandidateRestaurant]:
    out: List[CandidateRestaurant] = []
    for it in items:
        if isinstance(it, CandidateRestaurant):
            out.append(it)
            continue

        # Best-effort mapping from Phase 1 RestaurantRecord (attribute-based)
        name = getattr(it, "name", None)
        if not name:
            raise ValueError("Candidate is missing required field: name")

        out.append(
            CandidateRestaurant(
                name=str(name),
                address=getattr(it, "address", None),
                location=getattr(it, "location", None),
                listed_in_city=getattr(it, "listed_in_city", None),
                cuisines=getattr(it, "cuisines", None),
                approx_cost=getattr(it, "approx_cost", None),
                rate=getattr(it, "rate", None),
                votes=getattr(it, "votes", None),
                rest_type=getattr(it, "rest_type", None),
                dish_liked=getattr(it, "dish_liked", None),
                online_order=getattr(it, "online_order", None),
                book_table=getattr(it, "book_table", None),
            )
        )
    return out


def recommend_with_explanations(
    *,
    preference: Any,
    candidates: Sequence[Any],
    client: Optional[LLMClient] = None,
    settings: RecommendSettings = RecommendSettings(),
) -> List[Recommendation]:
    """
    Rank candidate restaurants with short explanations.

    - Uses LLM if possible.
    - Falls back to candidate order with template explanations on failure.
    """
    coerced = _coerce_candidates(candidates)
    if not coerced:
        return []

    top_k = coerced[: max(1, settings.top_k_candidates)]

    desired = settings.max_results
    if hasattr(preference, "max_results") and getattr(preference, "max_results") is not None:
        try:
            desired = int(getattr(preference, "max_results"))
        except Exception:
            desired = settings.max_results
    desired = max(1, min(desired, len(top_k)))

    messages = build_messages(preference, top_k, desired_results=desired)
    client = client or OpenAIChatCompletionsClient()

    try:
        raw = client.generate(model=settings.model, messages=messages, timeout_s=settings.timeout_s)
        parsed = parse_recommendations(raw)
        return _postprocess(preference=preference, candidates=top_k, parsed=parsed, desired=desired)
    except Exception:
        # Fallback: keep retrieval order and generate a minimal explanation.
        out: List[Recommendation] = []
        for idx, c in enumerate(top_k[:desired], start=1):
            out.append(
                Recommendation(
                    rank=idx,
                    restaurant_name=c.name,
                    explanation=_template_explanation(preference, c),
                    attributes={"cuisines": c.cuisines, "rating": c.rating_numeric or c.rate, "approx_cost": c.approx_cost, "location": c.location},
                )
            )
        return out


def _postprocess(
    *,
    preference: Any,
    candidates: Sequence[CandidateRestaurant],
    parsed: ParsedLLMResult,
    desired: int,
) -> List[Recommendation]:
    by_name: Dict[str, CandidateRestaurant] = {_normalize_name(c.name): c for c in candidates}
    used: set[str] = set()

    out: List[Recommendation] = []
    for rec in sorted(parsed.recommendations, key=lambda r: r.rank):
        key = _normalize_name(rec.restaurant_name)
        cand = by_name.get(key)
        if not cand or key in used:
            continue
        used.add(key)

        explanation = rec.explanation or _template_explanation(preference, cand)
        attrs = dict(rec.attributes or {})
        # Ensure some useful fields are present.
        attrs.setdefault("cuisines", cand.cuisines)
        attrs.setdefault("rating", cand.rating_numeric if cand.rating_numeric is not None else cand.rate)
        attrs.setdefault("approx_cost", cand.approx_cost)
        attrs.setdefault("location", cand.location)

        out.append(
            Recommendation(
                rank=len(out) + 1,
                restaurant_name=cand.name,
                explanation=explanation,
                attributes=attrs,
            )
        )
        if len(out) >= desired:
            break

    # If LLM returned fewer valid items, fill from remaining candidates.
    if len(out) < desired:
        for cand in candidates:
            key = _normalize_name(cand.name)
            if key in used:
                continue
            used.add(key)
            out.append(
                Recommendation(
                    rank=len(out) + 1,
                    restaurant_name=cand.name,
                    explanation=_template_explanation(preference, cand),
                    attributes={"cuisines": cand.cuisines, "rating": cand.rating_numeric or cand.rate, "approx_cost": cand.approx_cost, "location": cand.location},
                )
            )
            if len(out) >= desired:
                break

    return out

