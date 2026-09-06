"""
View 10: Household & Family Profile
Configures family demographics (Adults + Children + Elderly = Total Family Size),
dietary preferences, and nutrition targets used to dynamically scale consumption thresholds,
recipe serving quantities, and ML forecasting baselines.
"""

import streamlit as st
from dashboard.api_client import PantryClient


def render():
    st.markdown('<div class="app-header">👨‍👩‍👧‍👦 HOUSEHOLD & FAMILY PROFILE</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Demographic configuration dynamically scaling consumption thresholds, recipe portions, and pantry forecasting.</div>',
        unsafe_allow_html=True
    )

    profile, source = PantryClient.get_household()
    if not profile:
        st.error("Failed to load household profile from backend.")
        return

    st.markdown(f"""
    <div class="disclaimer-banner">
        <strong>⚙️ Dynamic System Integration:</strong>
        Family size directly drives the consumption threshold multiplier and recipe portion scaler.
        A household of 4 scales a 4-person baseline recipe by <code>1.0x</code>, while a family of 6 scales it to <code>1.5x</code>.
        Thresholds for high daily consumption scale proportionally with adult, child, and elderly equivalents.
    </div>
    """, unsafe_allow_html=True)

    # Demographic Overview Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Family Size", f"{profile.get('family_size', 4)} Members")
    with c2:
        st.metric("Adults (18–60)", profile.get("adults", 2))
    with c3:
        st.metric("Children (<18)", profile.get("children", 1))
    with c4:
        st.metric("Elderly (>60)", profile.get("elderly", 1))

    st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)

    st.subheader("📝 Edit Household Demographics & Dietary Constraints")

    with st.form("household_profile_form"):
        h_name = st.text_input("Household Profile Name", value=profile.get("household_name", "Primary Residence"))

        col_a, col_c, col_e = st.columns(3)
        with col_a:
            adults = st.number_input("Adults (A)", min_value=1, max_value=20, value=int(profile.get("adults", 2)), step=1)
        with col_c:
            children = st.number_input("Children (C)", min_value=0, max_value=20, value=int(profile.get("children", 1)), step=1)
        with col_e:
            elderly = st.number_input("Elderly (E)", min_value=0, max_value=20, value=int(profile.get("elderly", 1)), step=1)

        total_computed = adults + children + elderly
        st.caption(f"Calculated Total Household Size: **{total_computed} members** (Constraint: A + C + E = Total Size)")

        col_cal, col_goal = st.columns(2)
        with col_cal:
            cal_target = st.number_input(
                "Daily Family Calorie Baseline (kcal)",
                min_value=1000,
                max_value=30000,
                value=int(profile.get("daily_calorie_target") or 2200 * total_computed),
                step=100,
                help="Recommended daily baseline across all family members."
            )
        with col_goal:
            dietary_goal = st.selectbox(
                "Primary Dietary Goal",
                options=["BALANCED", "LOW_SUGAR", "LOW_SODIUM", "HIGH_PROTEIN", "WEIGHT_MANAGEMENT"],
                index=["BALANCED", "LOW_SUGAR", "LOW_SODIUM", "HIGH_PROTEIN", "WEIGHT_MANAGEMENT"].index(
                    profile.get("dietary_goal", "BALANCED") if profile.get("dietary_goal") in ["BALANCED", "LOW_SUGAR", "LOW_SODIUM", "HIGH_PROTEIN", "WEIGHT_MANAGEMENT"] else "BALANCED"
                )
            )

        # Dietary Preferences / Restrictions
        current_prefs = profile.get("dietary_preferences") or []
        available_prefs = ["Vegetarian", "Vegan", "Halal", "Kosher", "Gluten-Free", "Nut-Free", "Lactose-Free", "Low Carb", "Diabetic-Friendly"]
        selected_prefs = st.multiselect(
            "Dietary Preferences & Dietary Restrictions",
            options=available_prefs,
            default=[p for p in current_prefs if p in available_prefs]
        )

        notes = st.text_area("Household Notes / Special Requirements", value=profile.get("notes") or "", max_chars=300)

        submitted = st.form_submit_button("💾 Save Profile Changes", type="primary", use_container_width=True)

        if submitted:
            payload = {
                "household_name": h_name,
                "family_size": total_computed,
                "adults": adults,
                "children": children,
                "elderly": elderly,
                "daily_calorie_target": cal_target,
                "dietary_preferences": selected_prefs,
                "dietary_goal": dietary_goal,
                "notes": notes.strip() if notes else None
            }

            ok, msg = PantryClient.update_household(payload)
            if ok:
                st.success("✅ Household profile successfully updated! All consumption thresholds and recipe portions have been recalculated.")
                st.rerun()
            else:
                st.error(f"Failed to update profile: {msg}")

    # Impact Summary Box
    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)
    st.subheader("🔍 Active Engine Scaling Multipliers")

    recipe_scale = total_computed / 4.0
    st.markdown(f"""
    - **Recipe Portion Multiplier:** `x{recipe_scale:.2f}` (Scaled from 4-person culinary standard)
    - **Daily Salt Alert Threshold:** `{(5.0 * total_computed):.1f} g/day` (WHO 5g/adult/day baseline)
    - **Daily Sugar Alert Threshold:** `{(50.0 * total_computed):.1f} g/day` (WHO recommended upper limit)
    - **Per-Capita Caloric Allocation:** `{int(cal_target / total_computed)} kcal/person/day`
    """)
