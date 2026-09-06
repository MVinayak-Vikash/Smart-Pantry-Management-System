"""
View 1: Executive Dashboard
Overview of household inventory, stock availability, depletion countdowns, and alerts.
"""

import streamlit as st
import pandas as pd
from dashboard.api_client import PantryClient
from dashboard.styles import (
    format_quantity, get_availability_badge, get_intake_badge, get_priority_badge, format_timestamp, render_pantry_card_html
)


def render():
    st.markdown('<div class="app-header">🥫 SMART PANTRY DASHBOARD</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Real-Time Inventory Health, Consumption Forecasting & Smart Kitchen Telemetry</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="live-status-pill">
        <span class="live-dot"></span>
        <span>4 LOAD CELLS ACTIVE • TELEMETRY SYNCHRONIZED • ZERO-LEAKAGE ML FORECASTING ENGINE</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer-banner">
        <strong>📌 Demonstration & Hardware Telemetry:</strong>
        This system runs with continuous simulated IoT load cell inputs in preparation for physical ESP32 + HX711 deployment.
        Intake thresholds and calculations shown are for smart storage awareness, not clinical medical advice.
    </div>
    """, unsafe_allow_html=True)

    # Fetch data
    dashboard_data, conn_mode = PantryClient.get_dashboard_summary()
    household_data, _ = PantryClient.get_household()
    alerts_data = PantryClient.get_alerts(unresolved_only=True)
    predictions_data = PantryClient.get_predictions()

    if not dashboard_data or "items" not in dashboard_data:
        st.error("Unable to load pantry data. Verify database or backend status.")
        return

    items = dashboard_data["items"]
    family_size = household_data.get("family_size", 4) if household_data else 4
    household_name = household_data.get("household_name", "My Household") if household_data else "My Household"

    # Top KPI Metrics Bar
    kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5, kpi_c6 = st.columns(6)
    with kpi_c1:
        st.metric("Household", f"{family_size} Members", help=f"Active Profile: {household_name}")
    with kpi_c2:
        st.metric("Total Staples", dashboard_data["total_items"])
    with kpi_c3:
        st.metric("Available", dashboard_data["available_count"])
    with kpi_c4:
        st.metric("Low Stock", dashboard_data["low_count"], delta=-dashboard_data["low_count"] if dashboard_data["low_count"] > 0 else 0, delta_color="inverse")
    with kpi_c5:
        # Count items running out in <= 5 days
        stockouts_count = sum(1 for p in predictions_data if p.get("remaining_days_ml") is not None and p["remaining_days_ml"] <= 5.0)
        st.metric("Predicted Depletions", stockouts_count, delta=-stockouts_count if stockouts_count > 0 else 0, delta_color="inverse")
    with kpi_c6:
        st.metric("Active Alerts", len(alerts_data), delta=-len(alerts_data) if alerts_data else 0, delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # Active Pantry Staples Grid
    st.subheader("📦 Pantry Inventory Health")
    cols = st.columns(min(4, len(items)))

    for idx, item in enumerate(items):
        col = cols[idx % len(cols)]
        with col:
            avg_intake_text = f"{item['average_daily_intake']:.1f} g/day" if item.get("average_daily_intake") is not None else "Insufficient data"
            rem_days_text = f"~ {item['remaining_days']:.1f} days" if item.get("remaining_days") is not None else "Insufficient data"

            # Match with ML predicted depletion if available
            matching_pred = next((p for p in predictions_data if p["item_id"] == item["id"]), None)
            pred_depletion_date = matching_pred.get("predicted_depletion_date") if matching_pred else None

            card_html = render_pantry_card_html(
                item=item,
                pred_depletion_date=pred_depletion_date,
                avg_intake_text=avg_intake_text,
                rem_days_text=rem_days_text
            )
            st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Lower Split: Stockout Timeline & Active Alerts Feed
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("⏳ Upcoming Depletion Countdown")
        if predictions_data:
            timeline_items = [
                {
                    "Item": p["item_name"],
                    "Current Stock": format_quantity(p["current_quantity"]),
                    "Predicted Daily": f"{p['predicted_daily_consumption']} g/day",
                    "Est. Days Left": p["remaining_days_ml"] if p["remaining_days_ml"] is not None else 999.0,
                    "Projected Date": p["predicted_depletion_date"] or "Stable",
                    "Status": p["stock_status"]
                }
                for p in predictions_data
            ]
            df_timeline = pd.DataFrame(timeline_items).sort_values("Est. Days Left")
            df_timeline["Est. Days Left"] = df_timeline["Est. Days Left"].apply(lambda x: f"{x:.1f} days" if x != 999.0 else "Stable")

            st.dataframe(df_timeline, use_container_width=True, hide_index=True)
        else:
            st.info("No predictions available yet.")

    with col_right:
        st.subheader("🚨 Active Alerts Feed")
        if alerts_data:
            for alert in alerts_data[:4]:
                sev = alert.get("severity", "WARNING")
                msg = alert.get("message", "")
                ts = format_timestamp(alert.get("created_at") or alert.get("timestamp"))
                if sev == "CRITICAL":
                    st.error(f"⚡ **{msg}** ({ts})")
                elif sev == "WARNING":
                    st.warning(f"⚠️ **{msg}** ({ts})")
                else:
                    st.info(f"ℹ️ **{msg}** ({ts})")
        else:
            st.success("✅ All systems optimal. No unresolved alerts.")
