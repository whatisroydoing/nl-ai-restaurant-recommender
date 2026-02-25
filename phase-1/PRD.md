# Phase 1 — Mini PRD: Data Foundation and Retrieval

**Phase:** 1  
**Status:** PRD only (no implementation)  
**Reference:** [ARCHITECTURE.md](../docs/ARCHITECTURE.md) §2 Phased Delivery, §3 Data Foundation

---

## 1. Objective

Establish the restaurant data pipeline and support filtered retrieval **without any LLM**. Given user preferences (price, location, rating, cuisine), the system returns a list of matching restaurants from the dataset. No explanations, no OpenAI calls.

---

## 2. Data Source and Ingestion

- **Dataset (single source of truth):**  
**[https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)**  
Repository: `ManikaSaini/zomato-restaurant-recommendation` on Hugging Face. One split: **train** (~~51.7k rows). Formats: CSV (original), auto-converted Parquet (~~152 MB). Libraries: Datasets, pandas, Polars.
- **Ingestion method:** **Fetch the dataset via the Hugging Face API** (e.g. Datasets Hub API / `load_dataset("ManikaSaini/zomato-restaurant-recommendation")`). No manual file download or static Parquet in repo; data is loaded at runtime or during a load step via the API.
- **Size:** ~51.7k rows; consider streaming or batched load if needed for memory/performance.
- **Refresh:** Out of scope for Phase 1 detail; architecture assumes batch refresh later (Phase 6). For Phase 1, “load once via API” is sufficient.

---

## 3. Restaurant Data Store

- **Purpose:** Hold dataset records in a form that supports **filtering** by price range, location/place (city, area), rating, and cuisine.
- **Input:** Data obtained from the Hugging Face API (same schema as dataset).
- **Capabilities:**  
  - Load/populate from API response.  
  - Query/filter by: `listed_in(city)`, `location`, `approx_cost(for two people)`, `rate`, `cuisines`.  
  - Return candidate rows (restaurant records) with fields needed for later ranking and LLM context (e.g. name, location, cuisines, cost, rate, votes, optional dish_liked, rest_type).
- **Schema alignment:** Map dataset fields to a canonical **restaurant record** model used across the system (see Architecture §3 Data Foundation for key fields).

---

## 4. Retrieval Component

- **Input:** A **preference object** (price range, location/place, rating, cuisine). For Phase 1, assume this object is given in the shape that Phase 2 will validate; no validation logic required inside Phase 1.
- **Behavior:** Query the Restaurant Data Store with these preferences; return a **candidate set** of restaurants that match the filters. Optional: simple sort (e.g. by rating or votes). No top-K cap required for Phase 1 unless needed for a minimal end-to-end test.
- **Output:** List of restaurant records (filtered, optionally sorted). No explanations, no LLM.
- **Contract:**  
  - **Input:** Preference object (price, location/place, rating, cuisine).  
  - **Output:** List of restaurant records (e.g. name, location, cuisines, approx_cost, rate, and any other fields defined in the canonical model).

---

## 5. Out of Scope for Phase 1

- Input validation (Phase 2).
- LLM / OpenAI (Phase 3).
- HTTP API or API contract (Phase 4).
- Frontend UI (Phase 7).
- Data refresh strategy and runbooks (Phase 6).

---

## 6. Exit Criteria

- Dataset is **fetched via the Hugging Face API** (not via static file).
- Restaurant Data Store is populated and supports filtering by price, location, rating, cuisine.
- Retrieval component accepts a preference object and returns a list of matching restaurant records.
- End-to-end: given preferences, the system returns a **filtered list only** (no explanations). No code implementation in this PRD; this defines the scope for when implementation is started.

---

## 7. Open Points / Notes

- **HF API auth:** If the dataset is public, unauthenticated access may suffice; if not, document need for HF token/env.
- **Caching:** Optional: cache API response or store in a local persistence layer to avoid repeated API calls during development; decision left to implementation.

