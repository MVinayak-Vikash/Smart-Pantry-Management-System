"""
Smart Pantry Management System - Streamlit Dashboard (Phase 1)
Displays live metrics, stock availability, daily consumption analysis,
intake threshold alerts, and simulated sensor input for:
- Rice
- Sugar
- Salt
- Ghee
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Set Streamlit page configuration
st.set_page_config(
    page_title="Smart Pantry Management System",
    page_icon="🥫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# Custom CSS for modern styling and college project presentation
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
        text-align: center;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .disclaimer-box {
        background-color: #F1F5F9;
        border-left: 4px solid #3B82F6;
        padding: 0.75rem 1rem;
        border-radius: 4px;
        font-size: 0.85rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        height: 100%;
    }
    .card-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1E293B;
        margin: 0.3rem 0;
    }
    .metric-sub {
        font-size: 0.85rem;
        color: #64748B;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .badge-avail {
        background-color: #DCFCE7;
        color: #15803D;
        border: 1px solid #86EFAC;
    }
    .badge-low {
        background-color: #FEF3C7;
        color: #B45309;
        border: 1px solid #FCD34D;
    }
    .badge-unavail {
        background-color: #FEE2E2;
        color: #B91C1C;
        border: 1px solid #FCA5A5;
    }
    .badge-normal {
        background-color: #F1F5F9;
        color: #334155;
        border: 1px solid #CBD5E1;
    }
    .badge-high {
        background-color: #FFEDD5;
        color: #C2410C;
        border: 1px solid #FDBA74;
    }
    .badge-insufficient {
        background-color: #F1F5F9;
        color: #64748B;
        border: 1px solid #E2E8F0;
    }
    .divider {
        margin: 0.75rem 0;
        border-top: 1px dashed #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)


def format_quantity(grams: float) -> str:
    """Format grams into kg or g for clean human readability."""
    if grams >= 1000:
        val = grams / 1000.0
        return f"{val:.2f} kg ({int(grams)} g)"
    return f"{int(grams)} g"


def get_availability_badge(status: str) -> str:
    if status == "AVAILABLE":
        return '<span class="badge badge-avail">● AVAILABLE</span>'
    elif status == "LOW":
        return '<span class="badge badge-low">▲ LOW STOCK</span>'
    else:
        return '<span class="badge badge-unavail">✕ UNAVAILABLE</span>'


def get_intake_badge(status: str) -> str:
    if status == "NORMAL":
        return '<span class="badge badge-normal">NORMAL</span>'
    elif status == "HIGH":
        return '<span class="badge badge-high">⚠️ HIGH INTAKE</span>'
    else:
        return '<span class="badge badge-insufficient">INSUFFICIENT DATA</span>'


# Data fetching helpers with fallback
@st.cache_data(ttl=2)
def fetch_dashboard_data():
    """Fetch dashboard summary from FastAPI or fallback to local backend DB."""
    try:
        res = requests.get(f"{API_BASE_URL}/dashboard", timeout=2)
        if res.status_code == 200:
            return res.json(), "API"
    except Exception:
        pass

    # Direct DB fallback if FastAPI server is not actively running
    try:
        from backend.database import SessionLocal, init_db
        from backend import crud, schemas
        init_db()
        db = SessionLocal()
        try:
            items = crud.get_items(db)
            items_summary = []
            avail = low = unavail = high = 0
            for item in items:
                m = crud.compute_item_metrics(item)
                summary = schemas.ItemSummaryResponse(**m)
                items_summary.append(summary.model_dump())
                if summary.availability_status == "AVAILABLE":
                    avail += 1
                elif summary.availability_status == "LOW":
                    low += 1
                else:
                    unavail += 1
                if summary.intake_status == "HIGH":
                    high += 1
            data = {
                "items": items_summary,
                "total_items": len(items_summary),
                "available_count": avail,
                "low_count": low,
                "unavailable_count": unavail,
                "high_intake_count": high,
            }
            return data, "DirectDB"
        finally:
            db.close()
    except Exception as e:
        return None, str(e)


def fetch_item_consumption(item_id: int):
    """Fetch consumption history for an item."""
    try:
        res = requests.get(f"{API_BASE_URL}/items/{item_id}/consumption", timeout=2)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    try:
        from backend.database import SessionLocal
        from backend import crud
        db = SessionLocal()
        try:
            return crud.get_item_consumption_history(db, item_id)
        finally:
            db.close()
    except Exception:
        return None


def fetch_item_detail(item_id: int):
    """Fetch detail for an item."""
    try:
        res = requests.get(f"{API_BASE_URL}/items/{item_id}", timeout=2)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    try:
        from backend.database import SessionLocal
        from backend import crud
        db = SessionLocal()
        try:
            item = crud.get_item_by_id(db, item_id)
            if not item:
                return None
            m = crud.compute_item_metrics(item)
            m["recent_weight_history"] = [
                {"id": r.id, "item_id": r.item_id, "weight": r.weight, "timestamp": r.timestamp.isoformat()}
                for r in item.readings
            ]
            return m
        finally:
            db.close()
    except Exception:
        return None


def post_weight_reading(item_id: int, weight: float):
    """Send simulated weight reading."""
    try:
        res = requests.post(f"{API_BASE_URL}/items/{item_id}/weight", json={"weight": weight}, timeout=3)
        if res.status_code == 200:
            return True, "Reading recorded via FastAPI."
    except Exception:
        pass

    # Fallback to direct DB
    try:
        from backend.database import SessionLocal
        from backend import crud
        db = SessionLocal()
        try:
            crud.create_weight_reading(db, item_id, weight)
            return True, "Reading recorded directly into SQLite."
        finally:
            db.close()
    except Exception as e:
        return False, str(e)


def trigger_seed_data():
    """Trigger sample readings seed."""
    try:
        res = requests.post(f"{API_BASE_URL}/seed", timeout=5)
        if res.status_code == 200:
            return True, "Sample multi-day sensor readings seeded via API."
    except Exception:
        pass

    try:
        from backend.database import SessionLocal
        from backend import crud
        db = SessionLocal()
        try:
            crud.seed_sample_readings(db)
            return True, "Sample readings seeded directly into database."
        finally:
            db.close()
    except Exception as e:
        return False, str(e)


# Header
st.markdown('<div class="main-header">🥫 SMART PANTRY MANAGEMENT SYSTEM</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Phase 1: Real-Time Pantry Inventory, Consumption Tracking & Health Intake Monitoring</div>', unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer-box">
    <strong>📌 System Demonstration Notice:</strong>
    Intake thresholds and calculations shown are configurable software demonstration rules for smart storage awareness, not medical recommendations.
    Phase 1 uses simulated sensor inputs in preparation for ESP32 load-cell telemetry and container RFID integration.
</div>
""", unsafe_allow_html=True)

# Fetch Dashboard Summary
dashboard_data, conn_mode = fetch_dashboard_data()

# Sidebar: Controls & IoT Simulation
with st.sidebar:
    st.header("⚙️ System Controls")
    
    if conn_mode == "API":
        st.success("🟢 Connected to FastAPI (`127.0.0.1:8000`)")
    else:
        st.info("🟡 Local Database Mode (FastAPI offline or direct)")

    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("🧪 Simulated Sensor Data")
    st.caption("Populate realistic multi-day sensor logs for Rice, Sugar, Salt, and Ghee:")
    if st.button("📥 Load Sample Historical Data", use_container_width=True, type="primary"):
        success, msg = trigger_seed_data()
        st.cache_data.clear()
        if success:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.markdown("---")
    st.subheader("📡 Record Simulated Reading")
    st.caption("Simulates an incoming HTTP payload from an ESP32 / HX711 load cell:")
    
    if dashboard_data and "items" in dashboard_data:
        item_options = {item["name"]: item["id"] for item in dashboard_data["items"]}
        selected_item_name = st.selectbox("Select Pantry Item", list(item_options.keys()))
        selected_item_id = item_options[selected_item_name]
        
        current_item = next(i for i in dashboard_data["items"] if i["id"] == selected_item_id)
        current_wt = current_item["current_quantity"]
        
        st.caption(f"Current weight: **{current_wt} g**")
        new_weight = st.number_input(
            "New Weight Reading (g)",
            min_value=0.0,
            max_value=20000.0,
            value=float(max(0.0, current_wt - 150.0)),
            step=50.0
        )
        
        if st.button("📤 Send Weight Reading", use_container_width=True):
            ok, msg = post_weight_reading(selected_item_id, new_weight)
            st.cache_data.clear()
            if ok:
                st.success(f"Updated {selected_item_name} to {new_weight} g!")
                st.rerun()
            else:
                st.error(msg)

if not dashboard_data or "items" not in dashboard_data:
    st.error("Unable to load pantry data. Ensure the database or FastAPI backend is active.")
    st.stop()

# Overview Top KPI Metrics
items = dashboard_data["items"]
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.metric("Total Pantry Staples", dashboard_data["total_items"])
with col_kpi2:
    st.metric("Available Items", dashboard_data["available_count"])
with col_kpi3:
    st.metric("Low Stock Alerts", dashboard_data["low_count"], delta=-dashboard_data["low_count"] if dashboard_data["low_count"] > 0 else 0, delta_color="inverse")
with col_kpi4:
    st.metric("High Intake Alerts", dashboard_data["high_intake_count"], delta=-dashboard_data["high_intake_count"] if dashboard_data["high_intake_count"] > 0 else 0, delta_color="inverse")

st.markdown("<br>", unsafe_allow_html=True)
st.subheader("📦 Pantry Staples Overview")

# 4 Main Item Cards
cols = st.columns(4)

for idx, item in enumerate(items):
    col = cols[idx % 4]
    with col:
        avail_badge = get_availability_badge(item["availability_status"])
        intake_badge = get_intake_badge(item["intake_status"])
        
        avg_intake_display = (
            f"{item['average_daily_intake']:.1f} g/day"
            if item.get("average_daily_intake") is not None
            else "Insufficient data"
        )
        
        rem_days_display = (
            f"~ {item['remaining_days']:.1f} days"
            if item.get("remaining_days") is not None
            else "Insufficient data"
        )

        card_html = f"""
        <div class="card">
            <div class="card-title">
                <span>{item['name'].upper()}</span>
                {avail_badge}
            </div>
            <div class="metric-val">{format_quantity(item['current_quantity'])}</div>
            <div class="metric-sub">Min Threshold: {int(item['minimum_quantity'])} {item['unit']}</div>
            
            <div class="divider"></div>
            
            <div style="font-size:0.85rem; margin-bottom: 4px;">
                <strong>Intake Status:</strong> {intake_badge}
            </div>
            <div style="font-size:0.85rem; color:#475569;">
                <strong>Avg Intake:</strong> {avg_intake_display}
            </div>
            <div style="font-size:0.75rem; color:#64748B;">
                Configured High Limit: {int(item['high_intake_threshold'])} g/day
            </div>
            
            <div class="divider"></div>
            
            <div style="font-size:0.85rem; color:#0F172A;">
                <strong>Estimated Remaining:</strong><br>
                <span style="font-size:1.1rem; font-weight:700; color:{'#15803D' if item.get('remaining_days') else '#64748B'};">
                    {rem_days_display}
                </span>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Detailed Item Analytics & Historical View
st.subheader("📊 Consumption Analysis & History")
tab_item_names = [i["name"] for i in items]
selected_tab = st.selectbox("Select item to view historical readings and consumption intervals:", tab_item_names)

selected_item_info = next(i for i in items if i["name"] == selected_tab)
item_id = selected_item_info["id"]

col_detail1, col_detail2 = st.columns([1, 1])

history_data = fetch_item_consumption(item_id)
detail_data = fetch_item_detail(item_id)

with col_detail1:
    st.markdown(f"#### 📈 Weight Trend: {selected_tab}")
    if detail_data and detail_data.get("recent_weight_history"):
        readings_list = detail_data["recent_weight_history"]
        df_readings = pd.DataFrame(readings_list)
        df_readings["timestamp"] = pd.to_datetime(df_readings["timestamp"])
        df_readings = df_readings.sort_values("timestamp")
        
        # Display line chart
        st.line_chart(
            df_readings.set_index("timestamp")["weight"],
            use_container_width=True
        )
    else:
        st.info(f"No weight readings recorded yet for {selected_tab}. Use the sidebar to record a reading.")

with col_detail2:
    st.markdown(f"#### 🍽️ Daily Consumption Events")
    if history_data and history_data.get("records"):
        records = history_data["records"]
        df_records = pd.DataFrame(records)
        df_records["timestamp"] = pd.to_datetime(df_records["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
        
        st.dataframe(
            df_records[["timestamp", "previous_weight", "current_weight", "consumption", "refill_amount"]].rename(
                columns={
                    "timestamp": "Timestamp",
                    "previous_weight": "Previous (g)",
                    "current_weight": "Current (g)",
                    "consumption": "Consumed (g)",
                    "refill_amount": "Refill (g)",
                }
            ),
            use_container_width=True,
            hide_index=True
        )
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Consumption", f"{history_data['total_consumption']} g")
        col_m2.metric("Total Refilled", f"{history_data['total_refill']} g")
        col_m3.metric("Days with Data", history_data["days_with_data"])
    else:
        st.info("Insufficient reading intervals to calculate consumption events. Add at least two sequential readings.")

st.markdown("---")
st.caption(
    "Smart Pantry Management System • Phase 1 Core Architecture • "
    "Designed for future ESP32 (HX711) + RFID IoT container deployment"
)
