"""
Smart Pantry Management System - Streamlit Web Application
Multi-Page Dashboard providing end-to-end monitoring, analytics, nutrition,
ML forecasting, recipe recommendations, and hardware telemetry simulation.
"""

import sys
from pathlib import Path

# Ensure project root is always in sys.path regardless of execution directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from dashboard.styles import apply_custom_styles
from dashboard.api_client import PantryClient

# 12 Modular Views
from dashboard.views import (
    p01_dashboard,
    p02_pantry,
    p03_item_details,
    p04_consumption_analytics,
    p05_predictions,
    p06_diet_nutrition,
    p07_recipes,
    p08_shopping_list,
    p09_alerts,
    p10_household,
    p11_settings_simulation,
    p12_ml_evaluation,
)

# Set global Streamlit configuration
st.set_page_config(
    page_title="Smart Pantry Management System",
    page_icon="🥫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply unified design system
apply_custom_styles()

# Navigation definition
PAGES = {
    "🏠 1. Executive Dashboard": p01_dashboard.render,
    "📦 2. Pantry Containers": p02_pantry.render,
    "🔍 3. Item Details & Sensors": p03_item_details.render,
    "📈 4. Consumption Analytics": p04_consumption_analytics.render,
    "🔮 5. ML Consumption Forecasts": p05_predictions.render,
    "🥗 6. Dietary & Nutrition Tracking": p06_diet_nutrition.render,
    "👨‍🍳 7. Recipe Recommendations": p07_recipes.render,
    "🛒 8. Smart Grocery List": p08_shopping_list.render,
    "🔔 9. Smart Alerts Center": p09_alerts.render,
    "👨‍👩‍👧‍👦 10. Household & Family Profile": p10_household.render,
    "🧪 11. Simulation Bench & Settings": p11_settings_simulation.render,
    "📊 12. ML Evaluation & Telemetry": p12_ml_evaluation.render,
}

# -------------------------------------------------------------
# Sidebar Navigation & System Status
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🥫 SMART PANTRY")
    st.caption("AI-Powered IoT Storage Management")

    # Backend Connection Indicator
    is_online = PantryClient.is_api_online()
    if is_online:
        st.markdown('<span class="badge badge-avail">● FASTAPI ONLINE</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-low">● DIRECT DB FALLBACK</span>', unsafe_allow_html=True)

    st.markdown("<hr style='margin:0.75rem 0;'>", unsafe_allow_html=True)

    selected_page_title = st.radio(
        "Navigation",
        options=list(PAGES.keys()),
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("<hr style='margin:1rem 0;'>", unsafe_allow_html=True)

    # Global Quick Actions
    st.markdown("#### ⚡ Quick Simulation")
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        if st.button("⏩ +1 Day", use_container_width=True, help="Advance simulation time by 24 hours"):
            ok, msg = PantryClient.simulate_advance_days(1)
            if ok:
                st.toast("Advanced 1 Day!")
                st.rerun()
    with col_q2:
        if st.button("🔄 Refresh", use_container_width=True, help="Refresh client cache and data"):
            st.rerun()

    st.markdown("<hr style='margin:1rem 0;'>", unsafe_allow_html=True)
    st.caption("v2.0 Full-Software Demo • Ready for ESP32 + HX711 + RC522")

# -------------------------------------------------------------
# Render Selected Page
# -------------------------------------------------------------
render_func = PAGES.get(selected_page_title)
if render_func:
    render_func()
else:
    st.error("Page view not found.")
