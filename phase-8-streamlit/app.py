import streamlit as st
import os
import sys
import uuid
import pandas as pd
from dotenv import load_dotenv

# Path setup: ensure phase-1, phase-2, phase-3 packages are importable
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
for _phase in ("phase-1", "phase-2", "phase-3"):
    _p = os.path.join(_PROJECT_ROOT, _phase)
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Phase imports
from restaurant_recommender import Preference, RestaurantDataStore, retrieve
from restaurant_recommender.loader import load_dataset_from_hf
from preference_validation.validator import validate_preference
from preference_validation.models import PreferenceValidationError
from llm_recommender.recommender import recommend_with_explanations
from llm_recommender.models import RecommendSettings

# Load environment variables
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

# Page Setup
st.set_page_config(page_title="Zomato AI Recommender", page_icon="🍴", layout="wide")

# Custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css(os.path.join(os.path.dirname(__file__), "style.css"))

# ── State Management ──────────────────────────────────────────
if "data_store" not in st.session_state:
    with st.spinner("Loading restaurant data..."):
        records = load_dataset_from_hf()
        st.session_state.data_store = RestaurantDataStore(records)

# Extract metadata for dropdowns
data_store = st.session_state.data_store
records = data_store._records
areas = sorted(list(set(r.location.strip() for r in records if r.location)))
cuisines = sorted(list(set(c.strip() for r in records if r.cuisines for c in r.cuisines.split(','))))

# ── Sidebar / Filters ──────────────────────────────────────────
st.sidebar.image("https://b.zmtcdn.com/web_assets/b40b97e677bc7b2ca77c58c61db266fe1603954218.png", width=200)
st.sidebar.title("Filters")

selected_area = st.sidebar.selectbox("📍 Select Area", ["Any"] + areas)
selected_cuisines = st.sidebar.multiselect("🍴 Cuisines", cuisines)
price_range = st.sidebar.slider("💰 Price for two (₹)", 100, 5000, (100, 5000), step=100)
min_rating = st.sidebar.slider("⭐ Minimum Rating", 0.0, 5.0, 0.0, step=0.5)
max_results = st.sidebar.number_input("📊 Max Results", 1, 10, 5)

# ── Main Content ───────────────────────────────────────────────
st.markdown("""
<div class="hero-text">
    <h1>AI <span class="hero-accent">Recommender</span></h1>
    <p>Helping you find the best places to eat in <span class="hero-accent">Bangalore</span> city</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
col1.metric("Localities", len(areas))
col2.metric("Cuisines", len(cuisines))
col3.metric("Restaurants", len(records))

if st.button("Get Recommendations ✨", use_container_width=True):
    # 1. Prepare Payload
    payload = {}
    if selected_area != "Any":
        payload["location"] = selected_area
    if selected_cuisines:
        payload["cuisine"] = selected_cuisines[0] # Using first for filtering
    
    payload["price_min"] = price_range[0]
    payload["price_max"] = price_range[1]
    payload["min_rating"] = min_rating
    payload["max_results"] = max_results

    # 2. Validate
    try:
        validated = validate_preference(payload)
    except PreferenceValidationError as e:
        st.error(f"Validation Error: {', '.join(e.errors)}")
        st.stop()

    # 3. Retrieve
    with st.spinner("Retrieving candidates..."):
        pref = Preference(
            city=validated.city,
            location=validated.location,
            price_min=validated.price_min,
            price_max=validated.price_max,
            min_rating=validated.min_rating,
            cuisine=validated.cuisine
        )
        
        candidates = retrieve(
            data_store,
            pref,
            sort_by_rating=True,
            top_k=10
        )

        # Deduplicate
        seen = set()
        unique_candidates = []
        for c in candidates:
            if c.name.strip().lower() not in seen:
                seen.add(c.name.strip().lower())
                unique_candidates.append(c)
        candidates = unique_candidates

    if not candidates:
        st.warning("No restaurants found matching your filters. Try broadening your search!")
    else:
        # 4. LLM Recommendation
        with st.spinner("AI is ranking and writing explanations..."):
            settings = RecommendSettings()
            recommendations = recommend_with_explanations(
                preference=validated,
                candidates=candidates,
                settings=settings
            )

        # 5. Display
        st.subheader("🎯 Your Recommendations")
        for rec in recommendations:
            attrs = rec.attributes or {}
            tags_html = ""
            if attrs.get("cuisines"): tags_html += f'<span class="tag">🍴 {attrs["cuisines"]}</span>'
            if attrs.get("rating"): tags_html += f'<span class="tag">⭐ {attrs["rating"]}/5</span>'
            if attrs.get("approx_cost"): tags_html += f'<span class="tag">💰 ₹{attrs["approx_cost"]}</span>'
            if attrs.get("location"): tags_html += f'<span class="tag">📍 {attrs["location"]}</span>'

            st.markdown(f"""
            <div class="rec-card">
                <div class="rec-card-rank">#{rec.rank}</div>
                <div class="rec-card-title">{rec.restaurant_name}</div>
                <div class="rec-card-explanation">{rec.explanation}</div>
                <div class="rec-card-tags">{tags_html}</div>
            </div>
            """, unsafe_allow_html=True)

st.divider()
st.caption("Built with ❤️ — AI-Powered Restaurant Recommendations")
