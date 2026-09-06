"""
View 5: Predictions & Stock Depletion Forecasting
Compares Simple Mathematical Average against Machine Learning model predictions,
displays 7d/14d/30d projections, depletion countdowns, and 90% empirical prediction ranges.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dashboard.api_client import PantryClient
from dashboard.styles import format_quantity, get_availability_badge


def render():
    st.markdown('<div class="app-header">🔮 PREDICTIONS & STOCK FORECASTING</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Machine learning daily intake forecast, multi-day demand projections, and stockout timeline.</div>',
        unsafe_allow_html=True
    )

    predictions = PantryClient.get_predictions()
    if not predictions:
        st.info("No prediction data available. Please ensure models are trained and database is initialized.")
        return

    st.markdown("""
    <div class="disclaimer-banner">
        <strong>💡 Model Comparison & Empirical Confidence Bands:</strong>
        Mathematical estimates rely solely on simple historical division (Total Usage / Days Tracked).
        Machine Learning predictions dynamically factor in household family size, day-of-week, weekend effects, and rolling trends.
        90% confidence bands are computed from residual variance on held-out test data (±1.645σ).
    </div>
    """, unsafe_allow_html=True)

    # Visual Forecast Cards
    st.markdown("### 🎯 Real-Time Depletion Forecasts")
    cols = st.columns(min(4, len(predictions)))
    from dashboard.styles import get_item_accent

    for idx, p in enumerate(predictions):
        col = cols[idx % len(cols)]
        accent = get_item_accent(p["item_name"])
        rem_days = p.get("remaining_days_ml")
        rem_text = f"{rem_days:.1f} Days" if rem_days is not None else "Stable"
        dep_date = p.get("predicted_depletion_date") or "Stable"

        card_html = f"""
        <div class="pantry-card" style="border-top: 3px solid {accent['color']};">
            <div class="card-header-row">
                <span class="card-title-text">{accent['icon']} {p['item_name'].upper()}</span>
                <span class="badge badge-tag">ML RUNRATE</span>
            </div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {accent['color']}; margin: 0.3rem 0;">
                {rem_text}
            </div>
            <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.5rem;">
                Depletion Target: <strong style="color:#F1F5F9;">{dep_date}</strong>
            </div>
            <div class="card-divider"></div>
            <div style="font-size: 0.8rem; color: #CBD5E1; display:flex; justify-content:space-between;">
                <span>Daily Burn:</span>
                <strong style="color:{accent['color']};">{p['predicted_daily_consumption']:.1f} g/day</strong>
            </div>
            <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 3px;">
                90% Range: [{p['prediction_range_90_low']}g – {p['prediction_range_90_high']}g]
            </div>
        </div>
        """
        with col:
            st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Comparison Table
    st.subheader("📊 Forecast Comparison & Multi-Day Demand Projections")
    rows = []
    for p in predictions:
        math_rate = f"{p['historical_average_daily']:.1f} g/day" if p.get("historical_average_daily") is not None else "N/A"
        ml_rate = f"{p['predicted_daily_consumption']:.1f} g/day"
        math_rem = f"~ {p['remaining_days_math']:.1f} days" if p.get("remaining_days_math") is not None else "N/A"
        ml_rem = f"~ {p['remaining_days_ml']:.1f} days" if p.get("remaining_days_ml") is not None else "N/A"
        dep_date = p.get("predicted_depletion_date") or "Stable / Infinite"
        pred_range = f"[{p['prediction_range_90_low']}g – {p['prediction_range_90_high']}g]"

        rows.append({
            "Item": p["item_name"],
            "Current Stock": format_quantity(p["current_quantity"]),
            "Mathematical Rate": math_rate,
            "ML Predicted Rate": ml_rate,
            "90% Prediction Range": pred_range,
            "7-Day Demand": f"{p['predicted_7d_consumption']} g",
            "14-Day Demand": f"{p['predicted_14d_consumption']} g",
            "30-Day Demand": f"{p['predicted_30d_consumption']} g",
            "Est. Remaining Days": ml_rem,
            "Predicted Depletion": dep_date,
            "Model Used": p.get("model_used", "ML Regressor"),
        })

    df_preds = pd.DataFrame(rows)
    st.dataframe(df_preds, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Item Depletion Trajectory Chart
    st.subheader("📉 Forward Stock Depletion Trajectory")
    st.caption("Simulated daily weight reduction based on ML predicted consumption rate:")

    item_names = [p["item_name"] for p in predictions]
    sel_item = st.selectbox("Select Item to View Depletion Curve", item_names)
    target_pred = next(p for p in predictions if p["item_name"] == sel_item)

    curr_wt = target_pred["current_quantity"]
    daily_burn = target_pred["predicted_daily_consumption"]

    if curr_wt > 0 and daily_burn > 0:
        trajectory_days = int(min(60, max(14, (curr_wt / daily_burn) + 5)))
        dates = [datetime.now().date() + timedelta(days=i) for i in range(trajectory_days)]
        weights = [max(0.0, round(curr_wt - (daily_burn * i), 1)) for i in range(trajectory_days)]

        df_curve = pd.DataFrame({
            "Date": dates,
            "Projected Weight (g)": weights,
        }).set_index("Date")

        st.line_chart(df_curve, use_container_width=True)
    else:
        st.info("Item is already depleted or predicted consumption rate is zero.")
