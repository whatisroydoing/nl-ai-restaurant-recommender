import sys
from pathlib import Path

# Ensure `llm_recommender` is importable when running tests directly in phase-3.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

