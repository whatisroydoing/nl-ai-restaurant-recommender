# Phase 7 — Frontend UI

A Zomato-inspired web UI for the restaurant recommendation system.

## Quick Start

1. **Start the API server** (from project root):

```powershell
$env:PYTHONPATH = ".\phase-4;.\phase-1;.\phase-2;.\phase-3"
.\phase-1\venv\Scripts\python.exe -m recommendation_api.app
```

2. **Open the frontend** — simply open `phase-7/index.html` in your browser, or serve it:

```powershell
cd phase-7
python -m http.server 8080
```

Then visit `http://localhost:8080`.

## Features

- Preference form (city, location, cuisine, price range, rating)
- AI-ranked recommendation cards with explanations
- Loading skeleton, empty results, and error states
- Dark theme with Zomato red (`#cb202d`) accents
