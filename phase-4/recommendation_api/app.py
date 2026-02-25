"""Flask app — POST /recommend endpoint wiring Phases 1–3."""

from __future__ import annotations

import os
import sys
import uuid
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request

# ---------------------------------------------------------------------------
# Path setup: ensure phase-1, phase-2, phase-3 packages are importable.
# When running from the project root with PYTHONPATH already set this is a
# no-op, but it makes the module work when launched directly too.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
for _phase in ("phase-1", "phase-2", "phase-3"):
    _p = os.path.join(_PROJECT_ROOT, _phase)
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Phase 1 imports
from restaurant_recommender import Preference, RestaurantDataStore, retrieve
from restaurant_recommender.loader import load_dataset_from_hf

# Phase 2 imports
from preference_validation.validator import validate_preference
from preference_validation.models import PreferenceValidationError, ValidatedPreference

# Phase 3 imports
from llm_recommender.recommender import recommend_with_explanations
from llm_recommender.models import RecommendSettings

# Local imports
from .schemas import ErrorResponse, RecommendationItem, RecommendationResponse
from .errors import register_error_handlers


def _validated_to_phase1_preference(vp: ValidatedPreference) -> Preference:
    """Convert a Phase 2 ValidatedPreference into a Phase 1 Preference."""
    return Preference(
        city=vp.city,
        location=vp.location,
        price_min=vp.price_min,
        price_max=vp.price_max,
        min_rating=vp.min_rating,
        cuisine=vp.cuisine,
    )


def _filters_applied(vp: ValidatedPreference) -> Dict[str, Any]:
    """Build the ``filters_applied`` metadata from the validated preference."""
    d: Dict[str, Any] = {}
    if vp.city is not None:
        d["city"] = vp.city
    if vp.location is not None:
        d["location"] = vp.location
    if vp.price_min is not None:
        d["price_min"] = vp.price_min
    if vp.price_max is not None:
        d["price_max"] = vp.price_max
    if vp.min_rating is not None:
        d["min_rating"] = vp.min_rating
    if vp.cuisine is not None:
        d["cuisine"] = vp.cuisine
    if vp.max_results is not None:
        d["max_results"] = vp.max_results
    return d


# ── App factory ────────────────────────────────────────────────────────────


def create_app(
    store: Optional[RestaurantDataStore] = None,
    settings: Optional[RecommendSettings] = None,
) -> Flask:
    """
    Create and configure the Flask application.

    Parameters
    ----------
    store : RestaurantDataStore, optional
        Pre-loaded data store.  If *None*, the app loads from Hugging Face
        on first request (useful for production; tests always pass a store).
    settings : RecommendSettings, optional
        LLM configuration. Defaults to ``RecommendSettings()``.
    """
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    register_error_handlers(app)

    # ── CORS (allow frontend from any origin) ──────────────────────────
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    _settings = settings or RecommendSettings()
    _store: Dict[str, Optional[RestaurantDataStore]] = {"instance": store}

    def _get_store() -> RestaurantDataStore:
        if _store["instance"] is None:
            records = load_dataset_from_hf()
            _store["instance"] = RestaurantDataStore(records)
        return _store["instance"]  # type: ignore[return-value]

    # ── Health check ───────────────────────────────────────────────────

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    # ── Metadata endpoint (areas + cuisines for frontend dropdowns) ────

    @app.route("/metadata", methods=["GET"])
    def metadata():
        data_store = _get_store()
        areas: set[str] = set()
        cuisines: set[str] = set()
        for rec in data_store._records:
            if rec.location:
                areas.add(rec.location.strip())
            if rec.cuisines:
                for c in rec.cuisines.split(","):
                    c = c.strip()
                    if c:
                        cuisines.add(c)
        return jsonify({
            "areas": sorted(areas, key=str.lower),
            "cuisines": sorted(cuisines, key=str.lower),
        }), 200

    # ── Recommendation endpoint ────────────────────────────────────────

    @app.route("/recommend", methods=["POST"])
    def recommend():
        request_id = str(uuid.uuid4())

        # 1. Parse JSON body
        body = request.get_json(silent=True)
        if body is None:
            err = ErrorResponse(
                error="Bad request",
                details=["Request body must be valid JSON with Content-Type: application/json"],
                request_id=request_id,
            )
            return jsonify(err.to_dict()), 400

        # 2. Validate preferences (Phase 2)
        try:
            validated: ValidatedPreference = validate_preference(body)
        except PreferenceValidationError as exc:
            err = ErrorResponse(
                error="Validation error",
                details=list(exc.errors),
                request_id=request_id,
            )
            return jsonify(err.to_dict()), 422

        # 3. Convert to Phase 1 Preference and retrieve candidates
        pref = _validated_to_phase1_preference(validated)
        data_store = _get_store()
        candidates = retrieve(
            data_store,
            pref,
            sort_by_rating=True,
            top_k=_settings.top_k_candidates,
        )

        # 3b. Deduplicate by restaurant name (dataset has dupes under
        #     different listing categories).  Keep the first occurrence
        #     which is the highest-rated thanks to sort_by_rating above.
        seen_names: set[str] = set()
        unique_candidates = []
        for c in candidates:
            key = c.name.strip().lower()
            if key not in seen_names:
                seen_names.add(key)
                unique_candidates.append(c)
        candidates = unique_candidates

        # 4. Get LLM-ranked recommendations (Phase 3)
        #    recommend_with_explanations handles its own fallback.
        recommendations = recommend_with_explanations(
            preference=validated,
            candidates=candidates,
            settings=_settings,
        )

        # 5. Build response
        items = [
            RecommendationItem(
                rank=rec.rank,
                restaurant_name=rec.restaurant_name,
                explanation=rec.explanation,
                attributes=rec.attributes,
            )
            for rec in recommendations
        ]

        response = RecommendationResponse(
            request_id=request_id,
            model_used=_settings.model,
            filters_applied=_filters_applied(validated),
            recommendations=items,
        )

        return jsonify(response.to_dict()), 200

    return app


# ── Run directly ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
