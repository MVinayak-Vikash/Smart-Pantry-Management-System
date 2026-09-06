"""
View 2: Pantry Inventory
Comprehensive inventory table, category filtering, container RFID tags, and new staple addition.
"""

import streamlit as st
import pandas as pd
from dashboard.api_client import PantryClient
from dashboard.styles import (
    format_quantity, get_availability_badge, get_intake_badge, render_pantry_card_html
)


def render():
    st.markdown('<div class="app-header">📦 PANTRY CONTAINERS & INVENTORY</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Real-time smart container platforms, RFID identifiers, and capacity fill gauges.</div>',
        unsafe_allow_html=True
    )

    items = PantryClient.get_items()
    if not items:
        st.info("No pantry items found.")
        return

    # Filter controls
    col_f1, col_f2 = st.columns([1, 1])
    categories = ["All"] + sorted(list({i.get("category", "General") for i in items}))
    with col_f1:
        sel_cat = st.selectbox("Filter by Category", categories)
    with col_f2:
        sel_status = st.selectbox("Filter by Stock Status", ["All", "AVAILABLE", "LOW", "UNAVAILABLE"])

    filtered = items
    if sel_cat != "All":
        filtered = [i for i in filtered if i.get("category") == sel_cat]
    if sel_status != "All":
        filtered = [i for i in filtered if i.get("availability_status") == sel_status]

    # Visual Cards Display
    st.markdown("### 🗄️ Container Platforms")
    cols = st.columns(min(4, max(1, len(filtered))))
    for idx, it in enumerate(filtered):
        col = cols[idx % len(cols)]
        with col:
            avg_text = f"{it['average_daily_intake']:.1f} g/day" if it.get("average_daily_intake") else "Insufficient data"
            rem_text = f"~ {it['remaining_days']:.1f} days" if it.get("remaining_days") else "Insufficient data"
            card_html = render_pantry_card_html(
                item=it,
                avg_intake_text=avg_text,
                rem_days_text=rem_text
            )
            st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Detailed Specifications Table
    with st.expander("📊 Detailed Container Specifications & RFID Table", expanded=False):
        table_rows = []
        for it in filtered:
            table_rows.append({
                "ID": it["id"],
                "Item Name": it["name"],
                "Category": it.get("category", "General"),
                "Current Stock": format_quantity(it.get("current_quantity") if it.get("current_quantity") is not None else it.get("current_weight", 0)),
                "Min Threshold": f"{int(it.get('minimum_quantity', 0))} {it.get('unit', 'g')}",
                "Availability": it.get("availability_status", "AVAILABLE"),
                "Daily Intake": f"{it['average_daily_intake']:.1f} g/day" if it.get("average_daily_intake") else "N/A",
                "Est. Remaining": f"{it['remaining_days']:.1f} days" if it.get("remaining_days") else "N/A",
                "RFID UID": it.get("rfid_uid") or "None Assigned",
                "Location": it.get("storage_location") or "Pantry Shelf",
            })
        df_inv = pd.DataFrame(table_rows)
        st.dataframe(df_inv, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Add New Item Form
    with st.expander("➕ Add New Pantry Staple"):
        st.caption("Register a new container with storage thresholds and reference nutrition.")
        with st.form("add_item_form"):
            col_a1, col_a2, col_a3 = st.columns(3)
            with col_a1:
                new_name = st.text_input("Item Name", placeholder="e.g. Lentils / Dal")
                new_category = st.selectbox("Category", ["Grains & Cereals", "Pulses & Legumes", "Sweeteners", "Seasoning", "Oils & Healthy Fats", "Spices", "General"])
                new_init_qty = st.number_input("Initial Capacity (g)", min_value=100.0, value=2000.0, step=100.0)
            with col_a2:
                new_min_qty = st.number_input("Low Stock Threshold (g)", min_value=10.0, value=500.0, step=50.0)
                new_intake_limit = st.number_input("High Intake Limit (g/day)", min_value=1.0, value=80.0, step=5.0)
                new_location = st.text_input("Storage Location", value="Pantry Shelf")
            with col_a3:
                new_cal = st.number_input("Calories per 100g", min_value=0.0, value=340.0, step=10.0)
                new_rfid = st.text_input("RFID Tag UID (Optional)", placeholder="e.g. E280116060000205")
                new_perishable = st.checkbox("Perishable Item")

            submit_add = st.form_submit_button("Register Pantry Item", type="primary")
            if submit_add:
                if not new_name.strip():
                    st.error("Item name is required.")
                else:
                    try:
                        from backend.database import SessionLocal
                        from backend import crud
                        db = SessionLocal()
                        try:
                            crud.create_item(db, {
                                "name": new_name.strip(),
                                "unit": "g",
                                "initial_quantity": new_init_qty,
                                "current_quantity": new_init_qty,
                                "minimum_quantity": new_min_qty,
                                "high_intake_threshold": new_intake_limit,
                                "category": new_category,
                                "storage_location": new_location,
                                "calories_per_100g": new_cal,
                                "rfid_uid": new_rfid.strip() if new_rfid else None,
                                "is_perishable": new_perishable,
                                "active": True
                            })
                            st.success(f"Added '{new_name}' to pantry inventory!")
                            st.rerun()
                        finally:
                            db.close()
                    except Exception as e:
                        st.error(f"Error adding item: {e}")
