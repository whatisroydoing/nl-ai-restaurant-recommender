# Phase 4 — Mini PRD: Response Contract and API Shape

**Phase:** 4  
**Status:** Implementation  
**Reference:** `docs/ARCHITECTURE.md` §2 Phased Delivery, §4 User Input and Flow

---

## 1. Objective

Expose the full recommendation pipeline (validation → retrieval → LLM ranking) as a **single HTTP endpoint** with a **documented request/response contract**, proper error handling, and optional metadata.

Phase 4 must:

- Provide a **`POST /recommend`** endpoint that accepts user preferences as JSON.
- Return a **structured JSON response** with ranked recommendations, explanations, and metadata.
- Return **proper HTTP error codes** with descriptive JSON error bodies (400, 422, 500).

---

## 2. Scope

- **In scope**
  - Flask-based REST API with `POST /recommend` and `GET /health`.
  - Request validation via Phase 2's `validate_preference()`.
  - Retrieval via Phase 1's `RestaurantDataStore` + `retrieve()`.
  - LLM ranking via Phase 3's `recommend_with_explanations()`.
  - Response schema: `request_id`, `model_used`, `filters_applied`, `recommendations[]`.
  - JSON error responses for validation failures (422), bad request (400), server errors (500).
  - Offline test suite (mocked LLM and data store).
- **Out of scope**
  - Authentication / rate limiting (Phase 5).
  - Full observability / logging dashboards (Phase 5).
  - Frontend UI (Phase 7).
  - Deployment configuration.

---

## 3. API Contract

### 3.1 Request — `POST /recommend`

```json
{
  "city": "Banashankari",
  "location": "Banashankari",
  "cuisine": "North Indian",
  "price_min": 200,
  "price_max": 800,
  "min_rating": 3.5,
  "max_results": 5
}
```

All fields are **optional**. Unknown fields return a 422 error.

### 3.2 Success Response — `200 OK`

```json
{
  "request_id": "a1b2c3d4-...",
  "model_used": "gpt-4o-mini",
  "filters_applied": {
    "city": "Banashankari",
    "min_rating": 3.5
  },
  "recommendations": [
    {
      "rank": 1,
      "restaurant_name": "Spice Garden",
      "explanation": "Rated 4.3, serves North Indian, approx. ₹500 for two.",
      "attributes": {
        "cuisines": "North Indian, Chinese",
        "rating": 4.3,
        "approx_cost": "500",
        "location": "Banashankari"
      }
    }
  ]
}
```

### 3.3 Error Responses

| Status | When | Body |
|--------|------|------|
| **400** | Malformed JSON / not JSON | `{"error": "Bad request", "details": ["..."]}` |
| **422** | Validation failure | `{"error": "Validation error", "details": ["min_rating must be a number"]}` |
| **500** | Unexpected server error | `{"error": "Internal server error", "details": []}` |

---

## 4. Architecture (how it wires)

```
POST /recommend
  │
  ├─ Parse JSON body
  ├─ validate_preference(body)       ← Phase 2
  ├─ Convert to Phase 1 Preference
  ├─ retrieve(store, pref, top_k)    ← Phase 1
  ├─ recommend_with_explanations()   ← Phase 3
  └─ Build response with metadata
```

---

## 5. Exit Criteria

Phase 4 is complete when:

- `POST /recommend` returns correct responses for valid and invalid inputs.
- Response includes `request_id`, `model_used`, `filters_applied`.
- Error responses use proper HTTP status codes with JSON bodies.
- All unit tests pass offline (no OpenAI key, no Hugging Face needed).
