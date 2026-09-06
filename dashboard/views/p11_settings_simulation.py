"""
View 11: Hardware Simulation Bench & System Settings
Interactive sensor simulator allowing real-time weight injection, preset lifestyle events,
multi-day time advancement, and demo environment reset.
Uses the EXACT same backend REST endpoints and processing pipeline as physical ESP32 load cells.
"""

import streamlit as st
from dashboard.api_client import PantryClient
from dashboard.styles import format_quantity


def _get_item_weight(item: dict) -> float:
    return float(item.get("current_quantity") if item.get("current_quantity") is not None else item.get("current_weight", 0.0))


def render():
    st.markdown('<div class="app-header">🧪 SIMULATION BENCH & HARDWARE TELEMETRY</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Simulate real-time load cell weight readings, test refill detection, advance time, and stress-test the system pipeline.</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="disclaimer-banner">
        <strong>🔌 Hardware-Ready Telemetry Contract:</strong>
        This simulation bench sends HTTP POST payloads identical to those transmitted by physical
        <strong>ESP32 microcontrollers</strong> paired with <strong>HX711 24-bit ADC load cell amplifiers</strong>.
        All readings pass through identical noise-filtering, refill-detection, consumption-accumulation,
        and alert-dispatch logic.
    </div>
    """, unsafe_allow_html=True)

    items = PantryClient.get_items()
    if not items:
        st.warning("No pantry items found. Please reset the database below.")
        if st.button("🔄 Initialize Default Items"):
            PantryClient.reset_demo_database()
            st.rerun()
        return

    items_map = {f"{i['name']} (Current: {format_quantity(_get_item_weight(i))})": i for i in items}

    tab_single, tab_events, tab_advance, tab_reset = st.tabs([
        "⚖️ Single Sensor Injection",
        "⚡ Preset Lifestyle Events",
        "⏩ Time Acceleration (+1d / +7d / +30d)",
        "🔄 Demo Environment Reset"
    ])

    # -------------------------------------------------------------
    # TAB 1: Single Weight Injection
    # -------------------------------------------------------------
    with tab_single:
        st.subheader("Manual Weight Reading Injection")
        st.caption("Simulate a live weight sample emitted by an IoT load cell platform.")

        sel_label = st.selectbox("Select Target Pantry Container", list(items_map.keys()))
        selected_item = items_map[sel_label]

        curr_w = _get_item_weight(selected_item)
        col_w1, col_w2 = st.columns([2, 1])

        with col_w1:
            new_weight = st.number_input(
                "New Scale Weight Reading (grams)",
                min_value=0.0,
                max_value=15000.0,
                value=curr_w,
                step=10.0,
                help="Enter the simulated current gross weight on the scale platform."
            )
        with col_w2:
            st.markdown("<br>", unsafe_allow_html=True)
            diff = new_weight - curr_w
            if diff > 0:
                st.caption(f"Change: **+{diff:.1f} g** (Refill detected if &ge; 50g)")
            elif diff < 0:
                st.caption(f"Change: **{diff:.1f} g** (Consumption)")
            else:
                st.caption("Change: 0.0 g (No delta)")

        if st.button("📡 Transmit Telemetry Reading", type="primary"):
            ok, msg = PantryClient.post_simulated_reading(selected_item["id"], new_weight)
            if ok:
                st.success(f"Telemetry transmitted for {selected_item['name']}: {new_weight:.1f} g recorded!")
                st.rerun()
            else:
                st.error(f"Transmission failed: {msg}")

    # -------------------------------------------------------------
    # TAB 2: Preset Lifestyle Events
    # -------------------------------------------------------------
    with tab_events:
        st.subheader("Simulate Real-World Scenarios")
        st.caption("Trigger multi-item consumption patterns or restock actions with a single click.")

        col_e1, col_e2 = st.columns(2)

        with col_e1:
            with st.container():
                st.markdown("#### 🍳 Daily Family Cooking")
                st.write("Simulates evening dinner prep: -180g Rice, -25g Ghee, -8g Salt.")
                if st.button("Simulate Dinner Prep", key="btn_ev_dinner"):
                    for it in items:
                        w = _get_item_weight(it)
                        if it["name"] == "Rice":
                            PantryClient.post_simulated_reading(it["id"], max(0.0, w - 180.0))
                        elif it["name"] == "Ghee":
                            PantryClient.post_simulated_reading(it["id"], max(0.0, w - 25.0))
                        elif it["name"] == "Salt":
                            PantryClient.post_simulated_reading(it["id"], max(0.0, w - 8.0))
                    st.success("Dinner prep simulated across pantry containers!")
                    st.rerun()

            st.markdown("<hr>", unsafe_allow_html=True)

            with st.container():
                st.markdown("#### 🎂 Festival Baking & Desserts")
                st.write("Simulates festive sweet preparation: -350g Sugar, -200g Rice, -75g Ghee.")
                if st.button("Simulate Festival Baking", key="btn_ev_bake"):
                    for it in items:
                        w = _get_item_weight(it)
                        if it["name"] == "Sugar":
                            PantryClient.post_simulated_reading(it["id"], max(0.0, w - 350.0))
                        elif it["name"] == "Rice":
                            PantryClient.post_simulated_reading(it["id"], max(0.0, w - 200.0))
                        elif it["name"] == "Ghee":
                            PantryClient.post_simulated_reading(it["id"], max(0.0, w - 75.0))
                    st.success("Festival baking event logged!")
                    st.rerun()

        with col_e2:
            with st.container():
                st.markdown("#### 🛒 Supermarket Bulk Restock")
                st.write("Simulates grocery shopping haul: +5,000g Rice, +2,000g Sugar, +1,000g Salt, +1,000g Ghee.")
                if st.button("Simulate Bulk Restock", key="btn_ev_restock"):
                    for it in items:
                        w = _get_item_weight(it)
                        if it["name"] == "Rice":
                            PantryClient.post_simulated_reading(it["id"], w + 5000.0)
                        elif it["name"] == "Sugar":
                            PantryClient.post_simulated_reading(it["id"], w + 2000.0)
                        elif it["name"] == "Salt":
                            PantryClient.post_simulated_reading(it["id"], w + 1000.0)
                        elif it["name"] == "Ghee":
                            PantryClient.post_simulated_reading(it["id"], w + 1000.0)
                    st.success("Refill readings logged! Containers replenished.")
                    st.rerun()

            st.markdown("<hr>", unsafe_allow_html=True)

            with st.container():
                st.markdown("#### ⚠️ Anomalous Spill / Large Depletion")
                st.write("Simulates a major jar drop or spill: -900g Sugar in a single reading.")
                if st.button("Simulate Sugar Spill", key="btn_ev_spill"):
                    for it in items:
                        w = _get_item_weight(it)
                        if it["name"] == "Sugar":
                            PantryClient.post_simulated_reading(it["id"], max(0.0, w - 900.0))
                    st.warning("Spill event logged! Check Smart Alerts for anomaly detection.")
                    st.rerun()

    # -------------------------------------------------------------
    # TAB 3: Multi-Day Time Acceleration
    # -------------------------------------------------------------
    with tab_advance:
        st.subheader("Fast-Forward Time")
        st.caption("Advance time chronologically. Realistic consumption will be generated based on household profile and recorded into SQLite.")

        col_a1, col_a2, col_a3 = st.columns(3)

        with col_a1:
            st.markdown("#### +1 Day")
            st.caption("Simulate 24 hours of normal household consumption.")
            if st.button("Advance 1 Day", key="btn_adv_1"):
                with st.spinner("Simulating 1 day of pantry usage..."):
                    ok, msg = PantryClient.simulate_advance_days(1)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        with col_a2:
            st.markdown("#### +7 Days")
            st.caption("Simulate 1 full week of usage, meals, and natural variance.")
            if st.button("Advance 7 Days", key="btn_adv_7"):
                with st.spinner("Simulating 7 days of pantry usage..."):
                    ok, msg = PantryClient.simulate_advance_days(7)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        with col_a3:
            st.markdown("#### +30 Days")
            st.caption("Simulate 1 month of usage with auto-refills on depletion.")
            if st.button("Advance 30 Days", key="btn_adv_30"):
                with st.spinner("Simulating 30 days of pantry usage..."):
                    ok, msg = PantryClient.simulate_advance_days(30)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    # -------------------------------------------------------------
    # TAB 4: Reset Demo Environment
    # -------------------------------------------------------------
    with tab_reset:
        st.subheader("Reset Demo Database to Initial State")
        st.caption("Clears historical telemetry, readings, alerts, and shopping items, restoring the 4 staple items (Rice, Sugar, Salt, Ghee) with standard initial weights.")

        st.warning("⚠️ This action resets the SQLite database back to its pristine Phase 1 benchmark state.")

        if st.button("💥 Confirm Reset Demo Database", type="secondary"):
            with st.spinner("Resetting demo environment..."):
                ok, msg = PantryClient.reset_demo_database()
                if ok:
                    st.success("Demo environment reset successfully! All staple containers replenished.")
                    st.rerun()
                else:
                    st.error(f"Reset failed: {msg}")
