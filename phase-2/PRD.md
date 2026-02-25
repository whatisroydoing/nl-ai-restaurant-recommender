# Phase 2 — Mini PRD: Input Validation and Preference Model

**Phase:** 2  
**Status:** PRD + implementation + tests (no HTTP API)  
**Reference:** `docs/ARCHITECTURE.md` §2 Phased Delivery, §4 User Input and Flow

---

## 1. Objective

Turn **raw user input** (e.g. from an HTTP/JSON request or UI form) into a **validated preference object** that can be safely used by downstream components (Phase 1 retrieval, later the API and LLM layers).

On success, Phase 2 returns a **normalized, type-safe preference object**.  
On failure, Phase 2 returns **clear validation errors**, suitable to surface as **4xx client errors** in a future API layer.

No data loading, retrieval, LLM calls, or HTTP wiring live in Phase 2.

---

## 2. Scope

- **In scope**
  - Define a **preference schema** for:
    - `city` (e.g. Banashankari, Koramangala; aligns with dataset `listed_in(city)`)
    - `location` (area / neighborhood; aligns with dataset `location`)
    - `price_min`, `price_max` (approx cost for two people)
    - `min_rating` (minimum acceptable rating, 0–5)
    - `cuisine` (substring match on cuisines)
    - Optional: `max_results` (soft cap for number of recommendations)
  - Accept raw input as a **dictionary-like object** (e.g. parsed JSON).
  - Normalize common representations:
    - Trim whitespace from strings.
    - Treat empty strings as "not provided".
    - Parse numeric fields from strings (e.g. `"300"` → `300`, `"4.5"` → `4.5`).
  - Enforce basic **validation rules**:
    - `price_min` / `price_max` must be non-negative integers; if both provided, `price_min ≤ price_max`.
    - `min_rating` must be between `0.0` and `5.0`.
    - `max_results`, if provided, must be a positive integer within a reasonable cap (e.g. ≤ 100).
    - `city`, `location`, `cuisine` are non-empty strings after trimming, or `None`.
  - Produce a **validated preference object** that closely aligns with the Phase 1 `Preference` model.
  - Represent validation failures as a structured error (e.g. `PreferenceValidationError` with a list of field-specific messages).

- **Out of scope**
  - Enforcing that `city` / `location` / `cuisine` are in an **allowed list derived from the dataset** (that can be added later using dataset statistics).
  - Any knowledge of how preferences are transported (HTTP, CLI, etc.).
  - Mapping validation errors to concrete HTTP status codes (that belongs to the API layer in Phase 4).
  - LLM and ranking logic (Phases 3+).

---

## 3. Interfaces and Data Model

### 3.1 Input Shape

Phase 2 expects **raw input** as a mapping (e.g. `dict[str, Any]`) with the following optional keys:

- `city`: string
- `location`: string
- `price_min`: integer or string that can be parsed as integer
- `price_max`: integer or string that can be parsed as integer
- `min_rating`: float or string that can be parsed as float
- `cuisine`: string
- `max_results`: integer or string that can be parsed as integer

Unknown keys are considered **errors** (to prevent silent typos).

### 3.2 Output Shape

On success, Phase 2 returns a `ValidatedPreference` object (simple dataclass), with:

- `city: Optional[str]`
- `location: Optional[str]`
- `price_min: Optional[int]`
- `price_max: Optional[int]`
- `min_rating: Optional[float]`
- `cuisine: Optional[str]`
- `max_results: Optional[int]`

This shape is intentionally compatible with the Phase 1 `Preference` model so that later we can:

- Either reuse this object directly in retrieval, or
- Map it 1:1 into the Phase 1 `Preference` class.

### 3.3 Error Shape

On failure, Phase 2 raises a `PreferenceValidationError` that contains:

- A human-readable `message` (summary).
- A list of field-level error strings (e.g. `["price_min must be a non-negative integer", "min_rating must be between 0.0 and 5.0"]`).

The future API layer (Phase 4) can catch this exception and turn it into a 4xx JSON response.

---

## 4. Validation Rules (Initial Set)

These rules are intentionally conservative and easy to understand. They can be refined later based on dataset statistics and UX feedback.

- **Price**
  - `price_min` and `price_max`:
    - Parsed as integers from either `int` or numeric `str`.
    - Must be ≥ 0 if provided.
    - If both are provided, require `price_min ≤ price_max`.
- **Rating**
  - `min_rating`:
    - Parsed as float from `float` or numeric `str`.
    - Must be between `0.0` and `5.0` inclusive.
- **City / Location / Cuisine**
  - Strings are trimmed.
  - Empty strings (after trimming) are treated as `None`.
  - No dataset-level whitelist yet; any non-empty string is accepted.
- **Max results**
  - `max_results`, if provided, is parsed as integer.
  - Must be ≥ 1 and ≤ 100 (to avoid unbounded result sets).
- **Unknown fields**
  - Any extra keys in the input cause validation to fail, to avoid silent mistakes (e.g. `min_raing` instead of `min_rating`).

---

## 5. Implementation Plan (Phase 2 Folder)

Implementation lives under `phase-2/`:

- `phase-2/PRD.md` – this document.
- `phase-2/requirements.txt` – Python dependencies (`pytest` only).
- `phase-2/preference_validation/`
  - `__init__.py` – public API for Phase 2.
  - `models.py` – `ValidatedPreference` dataclass and `PreferenceValidationError` exception.
  - `validator.py` – `validate_preference(raw: Mapping[str, Any]) -> ValidatedPreference`.
- `phase-2/tests/`
  - `test_phase2_validation.py` – unit tests for happy paths and validation failures.

---

## 6. Exit Criteria

Phase 2 is considered complete when:

- A **validated preference model** (`ValidatedPreference`) is implemented.
- A **single entry point** function (`validate_preference`) converts raw dict input into `ValidatedPreference` or raises `PreferenceValidationError`.
- Validation rules from §4 are enforced and covered by tests.
- Running `pytest` inside `phase-2/` passes all tests.

