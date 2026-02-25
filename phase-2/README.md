# Phase 2 — Input Validation and Preference Model

Phase 2 implements input validation for restaurant preferences and produces a normalized, type-safe preference object that can be used by downstream components (retrieval, API, LLM).

## Setup (local)

```bash
cd phase-2
pip install -r requirements.txt
```

## Run tests

From the `phase-2` folder, run:

```bash
cd phase-2
set PYTHONPATH=.   # Windows CMD / PowerShell: $env:PYTHONPATH='.'
pytest -v
```


