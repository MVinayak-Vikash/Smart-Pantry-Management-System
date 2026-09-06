"""
View 3: Item Details
In-depth view of an individual staple: weight decay trajectory, consumption/refill events,
and nutritional breakdown per 100g.
"""

import streamlit as st
import pandas as pd
from dashboard.api_client import PantryClient
from dashboard.styles import format_quantity, get_availability_badge, get_intake_badge


def render():
    st.markdown('<div class="app-header">🔍 ITEM DETAILS & TELEMETRY</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Deep dive into container telemetry history, consumption intervals, and nutrition facts.</div>',
        unsafe_allow_html=True
    )

    items = PantryClient.get_items()
    if not items:
        st.info("No items found.")
        return

    item_names = [i["name"] for i in items]
    selected_name = st.selectbox("Select Pantry Item to Inspect", item_names)

    selected_item = next(i for i in items if i["name"] == selected_name)
    item_id = selected_item["id"]

    detail = PantryClient.get_item_detail(item_id)
    history = PantryClient.get_item_consumption(item_id)

    if not detail:
        st.error(f"Could not load details for {selected_name}.")
        return

    # Item Overview Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Current Weight", format_quantity(detail["current_quantity"]))
    with c2:
        st.metric("Min Threshold", f"{int(detail['minimum_quantity'])} {detail['unit']}")
    with c3:
        avg_text = f"{detail['average_daily_intake']:.1f} g/day" if detail.get("average_daily_intake") else "Insufficient data"
        st.metric("Avg Daily Intake", avg_text)
    with c4:
        rem_text = f"{detail['remaining_days']:.1f} days" if detail.get("remaining_days") else "Insufficient data"
        st.metric("Est. Remaining Days", rem_text)

    st.markdown("<br>", unsafe_allow_html=True)

    col_chart, col_nutr = st.columns([1.5, 1])

    with col_chart:
        st.subheader("📈 Historical Weight Trajectory")
        recent_readings = detail.get("recent_weight_history", [])
        if recent_readings:
            df_readings = pd.DataFrame(recent_readings)
            df_readings["timestamp"] = pd.to_datetime(df_readings["timestamp"])
            df_readings = df_readings.sort_values("timestamp")

            st.line_chart(
                df_readings.set_index("timestamp")["weight"],
                use_container_width=True
            )
        else:
            st.info(f"No historical weight readings logged yet for {selected_name}.")

    with col_nutr:
        st.subheader("🥗 Nutrition Facts (per 100g)")
        st.caption("Reference values sourced from USDA FoodData Central / NIN India (Demo Values):")
        st.markdown(f"""
        <div class="pantry-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span><strong>Calories:</strong></span>
                <span><strong>{detail.get('calories_per_100g', 0.0)} kcal</strong></span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span>Carbohydrates:</span>
                <span>{detail.get('carbohydrates_per_100g', 0.0)} g</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span>Protein:</span>
                <span>{detail.get('protein_per_100g', 0.0)} g</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span>Fat:</span>
                <span>{detail.get('fat_per_100g', 0.0)} g</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span>Sugar:</span>
                <span>{detail.get('sugar_per_100g', 0.0)} g</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span>Sodium:</span>
                <span>{detail.get('sodium_mg_per_100g', 0.0)} mg</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>Dietary Fiber:</span>
                <span>{detail.get('fiber_per_100g', 0.0)} g</span>
            </div>
            <div class="card-divider"></div>
            <div style="font-size:0.75rem; color:#64748B;">
                Storage: <strong>{detail.get('storage_location', 'Pantry Shelf')}</strong> • RFID: <code>{detail.get('rfid_uid') or 'None'}</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Detailed Consumption & Refill Intervals Table
    st.subheader("🍽️ Consumption & Refill Event Intervals")
    if history and history.get("records"):
        df_records = pd.DataFrame(history["records"])
        df_records["timestamp"] = pd.to_datetime(df_records["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")

        st.dataframe(
            df_records[["timestamp", "previous_weight", "current_weight", "consumption", "refill_amount"]].rename(
                columns={
                    "timestamp": "Timestamp",
                    "previous_weight": "Previous (g)",
                    "current_weight": "Current (g)",
                    "consumption": "Consumed (g)",
                    "refill_amount": "Refilled (g)",
                }
            ),
            use_container_width=True,
            hide_index=True
        )

        m_c1, m_c2, m_c3 = st.columns(3)
        m_c1.metric("Total Recorded Consumption", f"{history['total_consumption']} g")
        m_c2.metric("Total Replenished", f"{history['total_refill']} g")
        m_c3.metric("Days with Recorded Data", history["days_with_data"])
    else:
        st.info("Insufficient intervals recorded to compute consumption drops. Add at least two sequential weight readings.")
