# Phase 3 — Mini PRD: LLM Integration and Explained Recommendations

**Phase:** 3  
**Status:** PRD (implementation to follow)  
**Reference:** `docs/ARCHITECTURE.md` §2 Phased Delivery, §6 LLM (OpenAI) and Output

---

## 1. Objective

Convert a **bounded candidate set** (from Phase 1 retrieval) plus a **validated preference object** (from Phase 2) into a **ranked list of restaurant recommendations with short explanations** using an LLM (OpenAI).

Phase 3 must:

- Produce **human-friendly explanations**.
- Return a **structured, parseable** output format.
- Provide a **reliable fallback** when the LLM fails, times out, or returns malformed output.

---

## 2. Scope

- **In scope**
  - LLM adapter module (provider-agnostic interface, OpenAI implementation).
  - Prompt construction:
    - Preferences summary
    - Candidate list (top-K)
    - Output format requirements (strict JSON)
    - Safety rules (only choose from provided candidates)
  - Calling the OpenAI API and capturing latency / errors (basic logging hooks can be minimal; full observability is Phase 5).
  - Output parsing + validation:
    - Convert LLM JSON into a canonical internal structure.
    - Handle duplicates and unknown restaurant names gracefully.
  - Fallback behavior:
    - If LLM fails: return retrieval order (or rating-sorted order) with **generic explanations** (or `None`) so the system still works.
- **Out of scope**
  - HTTP API endpoint and response contract (Phase 4).
  - Full logging/metrics dashboards (Phase 5).
  - Dataset ingestion (Phase 1) and schema validation (Phase 2) beyond using their outputs.
  - Frontend UI (Phase 7).

---

## 3. Inputs and Outputs

### 3.1 Inputs

- **Validated preferences** (Phase 2 output), fields like:
  - `city`, `location`, `price_min`, `price_max`, `min_rating`, `cuisine`, `max_results`
- **Candidate restaurants** (Phase 1 output):
  - A list of canonical restaurant records containing at least:
    - `name`, `location`, `listed_in_city`, `cuisines`, `approx_cost`, `rate`, `votes`
  - Optional fields helpful for explanations:
    - `rest_type`, `dish_liked`, `online_order`, `book_table`

### 3.2 Output

A ranked list of recommendations with explanations, each containing:

- `rank` (1..N)
- `restaurant_name` (must match one of the candidate names)
- `explanation` (1–2 short sentences)
- Optional echo of attributes used in explanation (e.g. `rating`, `approx_cost`, `cuisines`, `location`)

---

## 4. Key Requirements

### 4.1 Candidate bounding (cost control)

- Phase 3 must never send the full dataset to the LLM.
- The prompt uses a **top-K** candidate set (recommended: 10–15).

### 4.2 Output must be structured (strict JSON)

- The system must request JSON-only output from the model.
- The response parser must validate:
  - JSON parses successfully.
  - Output is a list of objects with required keys.
  - Restaurant names map to known candidates (or are dropped/normalized).
  - Rank ordering is coherent (if not, we re-rank locally by position).

### 4.3 Fallback behavior

If any of these happen:

- OpenAI request fails (network/auth/5xx)
- Request times out
- JSON is malformed or missing required fields

Then return:

- Restaurants in retrieval order (or rating-sorted order), limited to `max_results` or `top_k`.
- Explanations either:
  - Generic template explanation derived from fields (rating/cuisine/price), or
  - `None` (allowed), depending on what we choose during implementation.

---

## 5. OpenAI API Key (Do we need it now?)

- **No, not for the PRD or writing the code structure.**
- We only need an API key when we:
  - Run a true end-to-end integration test that actually calls OpenAI, or
  - Use the module in “real mode” rather than a mocked LLM client.

**Planned configuration:** read from environment variable `OPENAI_API_KEY` (or a `.env` later; secrets management is Phase 5).

---

## 6. Implementation Outline (Phase 3 Folder)

Implementation will live under `phase-3/`:

- `phase-3/PRD.md` – this document.
- `phase-3/llm_recommender/`
  - `models.py` – internal recommendation output model.
  - `prompting.py` – prompt builder (preferences + candidates → prompt).
  - `openai_client.py` – OpenAI call wrapper (timeout, retries optional).
  - `parser.py` – JSON parsing + validation.
  - `recommender.py` – orchestration: build prompt → call LLM → parse → fallback.
- `phase-3/tests/`
  - Unit tests for prompt structure, parsing, and fallback (no network).
  - Optional integration test for real OpenAI call (skipped unless key present).

---

## 7. Exit Criteria

Phase 3 is complete when:

- Given validated preferences + candidate list, the system returns a **ranked list** with **short explanations**.
- LLM output is **structured** and **validated**.
- Fallback path works and is covered by tests.
- Unit tests run offline and pass reliably; integration test is optional and gated on the presence of `OPENAI_API_KEY`.

