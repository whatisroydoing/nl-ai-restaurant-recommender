# Phase 4 — Response Contract and API Shape

Phase 4 exposes the full restaurant recommendation pipeline as a REST API.

## Setup

```bash
cd phase-4
# Use the phase-1 venv (it already has pytest; install flask too)
..\phase-1\venv\Scripts\pip install flask
```

## Run tests (offline — no API keys needed)

```powershell
cd <project-root>
$env:PYTHONPATH = ".\phase-4;.\phase-1;.\phase-2;.\phase-3"
.\phase-1\venv\Scripts\python.exe -m pytest .\phase-4\tests -v
```

## Start the dev server

```powershell
cd <project-root>
$env:PYTHONPATH = ".\phase-4;.\phase-1;.\phase-2;.\phase-3"
.\phase-1\venv\Scripts\python.exe -m recommendation_api.app
```

Then test with:

```bash
curl -X POST http://localhost:5000/recommend \
     -H "Content-Type: application/json" \
     -d '{"city": "Banashankari", "min_rating": 3.5, "max_results": 3}'
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/recommend` | Get restaurant recommendations |
| `GET`  | `/health`    | Health check |

See `PRD.md` for the full request/response contract.
