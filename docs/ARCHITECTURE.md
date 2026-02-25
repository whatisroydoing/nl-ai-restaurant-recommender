# AI-Powered Restaurant Recommendation Service — Architecture

**Version:** 1.0 · Architecture only (no implementation) · Feb 2025

---

## 1. Summary

Service that takes **user preferences** (price, location, rating, cuisine), uses the **ManikaSaini/zomato-restaurant-recommendation** Hugging Face dataset, calls the **OpenAI API** (LLM) on a filtered candidate set, and returns **ranked recommendations with short explanations**. A **frontend UI** lets users submit preferences and view results. Implementation-agnostic.

**Goals:** Reliable, explainable recommendations; clear separation of retrieval vs LLM; scalable first GenAI project.  
**Non-goals:** Custom ML training; live Zomato API; unfiltered search over full 51k+ rows.

---

## 2. Phased Delivery

| Phase | Name | Outcome | Depends on |
|-------|------|---------|------------|
| **1** | Data Foundation and Retrieval | Data Store + filtered candidate list (no LLM) | — |
| **2** | Input Validation and Preference Model | Validated preference object; 4xx for invalid input | — (can run parallel to 1) |
| **3** | LLM Integration and Explained Recommendations | Ranked list + short explanations; fallback when LLM fails | 1, 2 |
| **4** | Response Contract and API Shape | Documented API (request/response, errors, optional metadata) | 3 |
| **5** | Observability and Hardening | Logging, metrics, error matrix, config/secrets strategy | 3 (4 preferred) |
| **6** | Data Refresh and Ops Readiness | Batch refresh strategy; deployment/ops outline | 1, 5 |
| **7** | Frontend UI | Web UI: preference form → call API → display ranked recommendations + explanations | 4 |

**Phase 1:** Ingest HF dataset → Restaurant Data Store; retrieval by preferences → candidate set; no LLM. Exit: filtered list only.  
**Phase 2:** Preference schema + validation rules; supported cities/areas, price bands, rating; raw input → validated object or 4xx.  
**Phase 3:** LLM adapter (provider-agnostic); top-K (e.g. 10–15) → prompt (system + user with preferences + candidates); response formatter + fallback (e.g. retrieval order, no explanations). Exit: full flow with explanations.  
**Phase 4:** Single recommendation endpoint (e.g. POST); request/response schema; optional request_id, model_used, filters_applied; API docs.  
**Phase 5:** Logs (request_id, candidate count, LLM latency, tokens, parse success); metrics (rate, latency, LLM errors, fallback rate); error matrix (validation→4xx, retrieval→5xx, LLM failure→fallback/retry); secrets and config externalized.  
**Phase 6:** Batch refresh of Data Store (schedule/deploy); stateless deployment; runbook outline (deploy, config, refresh, secrets, monitoring).  
**Phase 7:** Frontend UI: form for price, location, rating, cuisine; submit to recommendation API; display ranked list with explanations and key attributes; handle loading and errors.

---

## 3. Data Foundation

**Source:** [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) · ~51.7k rows · ~152 MB Parquet.

**Key fields:** `name`, `address`, `location` (93), `listed_in(city)` (30), `cuisines`, `approx_cost(for two people)`, `rate`, `votes`, `rest_type`, `online_order`, `book_table`, `dish_liked`, `reviews_list`, `menu_item`, `url`, `phone`.

**Filters (pre-LLM):** Location/place → `location`, `listed_in(city)`; price → `approx_cost`; rating → `rate`; cuisine → `cuisines`. **Rule:** Retrieval returns a **bounded top-K**; LLM never sees the full dataset.

**Data access:** Load once or periodically from HF; store in queryable store (filter by city, location, price, rating, cuisine); batch refresh (no real-time sync); no PII.

---

## 4. User Input and Flow

**Preference object:** price range, location/place (city/area), rating, cuisine. Optional: online_order, book_table, rest_type, max results. Validation before retrieval and LLM.

**Flow:** Request → **Validation** → **Retrieval** (Data Store → candidate set → top-K) → **LLM** (preferences + candidates → ranked list + explanations) → **Response formatter** → response. Data Store and LLM Provider are external; retrieval does not call LLM. **Frontend:** User fills preferences in UI → UI calls recommendation API → UI renders ranked results and explanations.

```
[Frontend UI] → Input Validation → Retrieval/Filtering → LLM Layer (OpenAI API)
                      ↓                    ↓                    ↓
                 (preferences)       Data Store           OpenAI API
```

---

## 5. Components (short)

- **Input Validation:** Normalize and validate preferences; allowed values from dataset; output validated object or error.
- **Data Store:** Load/index HF data; filter by price, location, rating, cuisine; return candidate rows for ranking and LLM.
- **Retrieval:** Query Data Store with validated preferences; optional sort; trim to top-K; pass structured candidate list to LLM.
- **LLM Layer:** Build prompt (preferences + candidates); call **OpenAI API**; return structured output (rank, name, explanation, attributes). Adapter remains swappable; provider choice is OpenAI.
- **Response Formatter:** Parse LLM output to canonical schema; fallback on malformed output (e.g. retrieval order, no explanations).

---

## 6. LLM (OpenAI) and Output

**Provider:** **OpenAI API** (e.g. GPT-4 or GPT-3.5). API key via env/secret manager.

**LLM role:** Only turn **fixed top-K candidates** into ranked, user-friendly recommendations with short explanations. No filtering or querying.

**Prompt:** System = role, output format (e.g. JSON), rules (only use provided candidates, short explanations). User = preference summary + candidate list (name, location, cuisine, cost, rating, optional dish_liked/rest_type). Enforce token limits and structure.

**Output contract:** e.g. JSON array: `rank`, `restaurant_name`, `explanation`, optional `cuisine`, `approx_cost`, `rating`, `location`. Formatter validates/sanitizes.

**API response:** Optional metadata (request_id, model_used, filters_applied). Recommendations: ordered list of rank, restaurant_name, explanation, attributes. Fallback: degraded (e.g. list without explanations or error).

---

## 7. Cross-Cutting

**Security:** Secrets (LLM, HF) in env/secret manager; validate/sanitize input and LLM output.  
**Observability:** Log request_id, preferences, candidate count, LLM latency, tokens, parse result; metrics for rate, latency, LLM errors, fallback rate.  
**Cost/performance:** Top-K and compact prompts bound LLM cost; retrieval fast via indexing; optional response cache for same preferences.  
**Errors:** Validation → 4xx; retrieval/data → 5xx or degraded; LLM timeout/failure → retry or fallback; malformed LLM → fallback order + optional warning.

---

## 8. Deployment and Future

**Deployment:** Stateless backend; config/env for OpenAI endpoint, model, API key, top-K; batch refresh of Data Store; horizontal scaling; optional rate limit. **Frontend:** Served as static or app from same or separate origin; calls recommendation API (CORS if needed).

**Later (out of scope v1):** User feedback (thumbs up/down), personalization, multi-turn conversation, RAG over reviews, A/B testing prompts.

---

## 9. Frontend UI

**Purpose:** Let users enter preferences and view ranked recommendations with explanations without calling the API directly.

**Scope:** Form inputs for price range, location/place, rating, cuisine (and optional fields if supported); submit to the recommendation API (e.g. POST); display results as a ranked list with restaurant name, short explanation, and attributes (cuisine, cost, rating, location); loading and error states (validation errors, no results, server/LLM failure).

**Contract:** UI consumes the recommendation API (Phase 4). No business logic in the UI beyond form validation and display; backend remains the source of truth.

---

## 10. Summary

| Layer | Responsibility |
|-------|----------------|
| Input | Preferences → validated object |
| Data | HF dataset → Data Store, filterable, indexed |
| Retrieval | Filters + top-K → candidates for LLM |
| LLM | Candidates + preferences → ranked list + explanations |
| Output | Canonical response + fallback |
| Frontend | Preference form → API call → ranked results + explanations |

**LLM:** OpenAI API. Retrieval ensures relevance and cost control; LLM adds clarity and explanation. No implementation prescribed.
