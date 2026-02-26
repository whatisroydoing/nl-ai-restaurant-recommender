import streamlit as st
import os
import sys
import uuid
import base64
from dotenv import load_dotenv

# Path setup: ensure phase-1, phase-2, phase-3 packages are importable
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, os.pardir))

for _phase in ("phase-1", "phase-2", "phase-3"):
    _p = os.path.join(_PROJECT_ROOT, _phase)
    if os.path.exists(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
    elif not os.path.exists(_p):
        _fallback = os.path.abspath(os.path.join(os.getcwd(), _phase))
        if os.path.exists(_fallback) and _fallback not in sys.path:
            sys.path.insert(0, _fallback)

# Phase imports
try:
    from restaurant_recommender import Preference, RestaurantDataStore, retrieve
    from restaurant_recommender.loader import load_dataset_from_hf
    from preference_validation.validator import validate_preference
    from preference_validation.models import PreferenceValidationError
    from llm_recommender.recommender import recommend_with_explanations
    from llm_recommender.models import RecommendSettings
except ImportError as e:
    st.error(f"Failed to import project modules. Error: {e}")
    st.stop()

# Load environment variables
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
load_dotenv(".env")

# Page Setup
st.set_page_config(page_title="Zomato AI Recommender", page_icon="🍴", layout="centered")

# Custom CSS and Glow Blobs
def apply_custom_style():
    with open(os.path.join(_HERE, "style.css")) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Extra style: force-dark the BaseWeb popover portal (rendered at body level,
    # outside the Streamlit app container, so needs its own injection)
    st.markdown("""
<style>
/* ── Popover portal dark override ── */
body [data-baseweb="popover"],
body [data-baseweb="popover"] > div,
body [data-baseweb="popover"] [data-baseweb="menu"] {
    background-color: #1a1a2e !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
}
body [data-baseweb="popover"] ul {
    background-color: #1a1a2e !important;
    padding: 4px 0 !important;
}
body [data-baseweb="popover"] li,
body [data-baseweb="popover"] [role="option"] {
    background-color: transparent !important;
    color: #a0a0b8 !important;
}
body [data-baseweb="popover"] li:hover,
body [data-baseweb="popover"] [role="option"]:hover,
body [data-baseweb="popover"] li[aria-selected="true"],
body [data-baseweb="popover"] [role="option"][aria-selected="true"] {
    background-color: rgba(203,32,45,0.15) !important;
    color: #f0f0f5 !important;
}
</style>
""", unsafe_allow_html=True)

    # Background Glow Blobs
    st.markdown('<div class="glow glow--1"></div><div class="glow glow--2"></div>', unsafe_allow_html=True)

apply_custom_style()

# ── Image Helper ──────────────────────────────────────────────
def get_base64_image(image_path):
    if not os.path.exists(image_path): return ""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_base64 = get_base64_image(os.path.join(_HERE, "zomato-logo.png"))

# ── State Management ──────────────────────────────────────────
if "data_store" not in st.session_state:
    with st.spinner("Loading restaurant data..."):
        records = load_dataset_from_hf()
        st.session_state.data_store = RestaurantDataStore(records)

data_store = st.session_state.data_store
records = data_store._records
areas = sorted(list(set(r.location.strip() for r in records if r.location)))
cuisines = sorted(list(set(c.strip() for r in records if r.cuisines for c in r.cuisines.split(','))))

# ── Hero Section ──────────────────────────────────────────────
st.markdown(f"""
<div class="hero-container">
    <img src="data:image/png;base64,{logo_base64}" class="hero-logo">
    <h1 class="hero-title">AI <span class="hero-accent">Recommender</span></h1>
    <p class="hero-subtitle">Helping you find the best places to eat in <span class="hero-accent">Bangalore</span> city</p>
</div>
""", unsafe_allow_html=True)

# Stats pills (Localities + Cuisines)
st.markdown(f"""
<div style="text-align:center; margin-bottom: 2rem;">
    <div class="hero__stats">
        <span class="stat">📍 <strong>{len(areas)}</strong> Localities</span>
        <span class="stat__divider">|</span>
        <span class="stat">🍽️ <strong>{len(cuisines)}</strong> Cuisines</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Preference Form (Main Layout) ──────────────────────────────
with st.container():
    col1, col2 = st.columns(2)
    selected_area = col1.selectbox("📍 Select Area", ["Any"] + areas)
    selected_cuisines = col2.multiselect("🍴 Cuisines (Multi-select)", cuisines)
    
    price_range = st.slider("💰 Price for two (₹)", 100, 5000, (100, 5000), step=100)
    
    col3, col4 = st.columns(2)
    min_rating = col3.number_input("⭐ Minimum Rating", 0.0, 5.0, 0.0, step=0.5)
    max_results = col4.number_input("📊 Max Results", 1, 10, 5)

    submit = st.button("Get Recommendations ✨")

# ── Results Logic ──────────────────────────────────────────────
if submit:
    payload = {}
    if selected_area != "Any": payload["location"] = selected_area
    if selected_cuisines: payload["cuisine"] = selected_cuisines[0]
    # Only apply price filter when the user has actually constrained the range
    if price_range[0] > 100: payload["price_min"] = price_range[0]
    if price_range[1] < 5000: payload["price_max"] = price_range[1]
    # Only apply rating filter when the user wants above 0
    if min_rating > 0.0: payload["min_rating"] = min_rating
    payload["max_results"] = max_results

    try:
        validated = validate_preference(payload)
    except PreferenceValidationError as e:
        st.error(f"Validation Error: {', '.join(e.errors)}")
        st.stop()

    with st.spinner("Finding the best spots for you..."):
        pref = Preference(
            # Don't filter by city — the dataset uses 'Bangalore' but records
            # may be inconsistent; filtering by location alone is sufficient.
            location=validated.location,
            price_min=validated.price_min,
            price_max=validated.price_max,
            min_rating=validated.min_rating,
            cuisine=validated.cuisine
        )
        
        candidates = retrieve(data_store, pref, sort_by_rating=True, top_k=10)
        
        # Deduplicate
        seen = set()
        unique_candidates = []
        for c in candidates:
            if c.name.strip().lower() not in seen:
                seen.add(c.name.strip().lower())
                unique_candidates.append(c)
        candidates = unique_candidates[:validated.max_results]

    if not candidates:
        st.warning("No restaurants found matching your filters. Try broadening your search!")
    else:
        with st.spinner("AI is personalizing your results..."):
            settings = RecommendSettings()
            recommendations = recommend_with_explanations(
                preference=validated,
                candidates=candidates,
                settings=settings
            )

        st.markdown("<br><h3>🎯 Your Recommendations</h3>", unsafe_allow_html=True)
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
                <div class="rec-card-body">
                    <div class="rec-card-name">{rec.restaurant_name}</div>
                    <div class="rec-card-explanation">{rec.explanation}</div>
                    <div class="rec-card-tags">{tags_html}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br><hr><p style='text-align:center; color:#6b6b80; font-size:0.8rem;'>Built with ❤️ — AI-Powered Restaurant Recommendations</p>", unsafe_allow_html=True)
