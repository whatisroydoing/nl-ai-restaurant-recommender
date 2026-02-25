# Phase 1 — Data Foundation and Retrieval

Implementation of Phase 1: load restaurant data from Hugging Face API, filter by preferences, return a list of matching restaurants (no LLM).

## Setup

```bash
cd phase-1
pip install -r requirements.txt
```

## Run unit tests (no network)

```bash
cd phase-1
set PYTHONPATH=.   # Windows CMD
# or: export PYTHONPATH=.   # Linux/macOS
pytest tests -v -m "not integration"
```

## Run integration test (loads from Hugging Face API)

```bash
cd phase-1
set PYTHONPATH=.
pytest tests -v -m integration
```

## Run all tests

```bash
cd phase-1
set PYTHONPATH=.
pytest tests -v
```

## Quick run (load + retrieve)

From project root or `phase-1` with `PYTHONPATH=phase-1`:

```python
from restaurant_recommender import load_dataset_from_hf, RestaurantDataStore, retrieve, Preference

records = load_dataset_from_hf()
store = RestaurantDataStore(records)
pref = Preference(city="Banashankari", min_rating=3.5)
results = retrieve(store, pref, sort_by_rating=True, top_k=5)
for r in results:
    print(r.name, r.rate, r.approx_cost, r.cuisines)
```
