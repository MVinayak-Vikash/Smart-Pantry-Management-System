"""
View 4: Consumption Analytics
Granular daily, weekly, and monthly trends, weekday vs weekend patterns, and refill history.
"""

import streamlit as st
import pandas as pd
from dashboard.api_client import PantryClient


def render():
    st.markdown('<div class="app-header">📈 CONSUMPTION ANALYTICS</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Multi-scale temporal consumption patterns, weekend effects, and refill frequency analysis.</div>',
        unsafe_allow_html=True
    )

    items = PantryClient.get_items()
    if not items:
        st.info("No items found.")
        return

    # Combine all consumption records across items
    all_records = []
    for item in items:
        hist = PantryClient.get_item_consumption(item["id"])
        if hist and hist.get("records"):
            for r in hist["records"]:
                if r.get("consumption", 0.0) > 0:
                    all_records.append({
                        "item_name": item["name"],
                        "timestamp": pd.to_datetime(r["timestamp"]),
                        "consumption": r["consumption"],
                        "refill": r.get("refill_amount", 0.0)
                    })

    if not all_records:
        st.info("Insufficient consumption data logged yet. Use the simulation test bench to generate readings.")
        return

    df_all = pd.DataFrame(all_records)
    df_all["date"] = df_all["timestamp"].dt.date
    df_all["day_name"] = df_all["timestamp"].dt.day_name()
    df_all["is_weekend"] = df_all["timestamp"].dt.dayofweek.isin([5, 6]).map({True: "Weekend", False: "Weekday"})

    # Daily aggregation
    st.subheader("📅 Daily Consumption Over Time (All Items)")
    df_daily = df_all.groupby(["date", "item_name"])["consumption"].sum().unstack(fill_value=0.0)
    st.bar_chart(df_daily, use_container_width=True)

    col_w1, col_w2 = st.columns([1, 1])

    with col_w1:
        st.subheader("📊 Weekday vs. Weekend Comparison")
        st.caption("Average consumption (grams) per day type:")
        df_weekday = df_all.groupby(["item_name", "is_weekend"])["consumption"].mean().unstack(fill_value=0.0).round(1)
        st.dataframe(df_weekday, use_container_width=True)

    with col_w2:
        st.subheader("🔄 Total Intake Breakdown by Item")
        df_item_tot = df_all.groupby("item_name")["consumption"].sum().round(1).reset_index()
        df_item_tot.columns = ["Pantry Item", "Total Consumed (g)"]
        st.dataframe(df_item_tot, use_container_width=True, hide_index=True)
