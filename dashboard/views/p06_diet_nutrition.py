"""
View 6: Diet & Nutrition Tracking
Estimated nutritional intake from tracked pantry foods and manual external meal logs.
Features lifestyle awareness disclaimers and dietary pattern indicators.
"""

import streamlit as st
import pandas as pd
from dashboard.api_client import PantryClient
from dashboard.styles import format_timestamp


def render():
    st.markdown('<div class="app-header">🥗 DIET & NUTRITION TRACKING</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Estimated calorie and macronutrient intake from tracked pantry foods and external logged meals.</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="diet-disclaimer">
        <strong>⚠️ Health & Medical Disclaimer:</strong>
        This estimate only reflects foods recorded by the system and manually logged meals.
        It is NOT a complete measure of total dietary intake and must not be used as medical advice or clinical diagnosis.
    </div>
    """, unsafe_allow_html=True)

    # Period Selector
    period = st.radio("Select Analysis Window:", ["today", "7d", "30d"], horizontal=True, format_func=lambda x: "Today" if x == "today" else ("Past 7 Days" if x == "7d" else "Past 30 Days"))

    diet_summary = PantryClient.get_diet_summary(period=period)
    if not diet_summary:
        st.info("Unable to calculate dietary summary.")
        return

    # Dietary Pattern Banner
    pattern = diet_summary.get("dietary_pattern", "NORMAL")
    desc = diet_summary.get("dietary_pattern_description", "")

    st.markdown("### 🧬 Dietary Consumption Pattern")
    if pattern == "NORMAL":
        st.success(f"🟢 **Pattern: {pattern}** — {desc}")
    elif pattern in ("HIGH_SUGAR", "HIGH_SODIUM", "HIGH_FAT"):
        st.warning(f"⚠️ **Pattern: {pattern}** — {desc}")
    elif pattern == "INCREASING_CONSUMPTION":
        st.info(f"📈 **Pattern: {pattern}** — {desc}")
    elif pattern == "IRREGULAR":
        st.info(f"🔄 **Pattern: {pattern}** — {desc}")
    else:
        st.info(f"⚪ **Pattern: {pattern}** — {desc}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Macronutrient Breakdown Comparison Cards
    pantry = diet_summary.get("tracked_pantry_intake", {})
    manual = diet_summary.get("manual_logged_intake", {})
    combined = diet_summary.get("total_combined_intake", {})

    st.subheader(f"📊 Nutritional Breakdown ({period.upper()})")

    col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
    with col_m1:
        st.metric("🔥 Total Calories", f"{combined.get('calories_kcal', 0.0):,.0f} kcal")
    with col_m2:
        st.metric("🌾 Carbohydrates", f"{combined.get('carbohydrates_g', 0.0):.1f} g")
    with col_m3:
        st.metric("💪 Protein", f"{combined.get('protein_g', 0.0):.1f} g")
    with col_m4:
        st.metric("🧈 Healthy Fats", f"{combined.get('fat_g', 0.0):.1f} g")
    with col_m5:
        st.metric("🧊 Added Sugar", f"{combined.get('sugar_g', 0.0):.1f} g")
    with col_m6:
        st.metric("🧂 Sodium", f"{combined.get('sodium_mg', 0.0):,.0f} mg")

    st.markdown("<br>", unsafe_allow_html=True)

    # Side-by-Side Source Breakdown Cards
    col_src1, col_src2 = st.columns(2)
    with col_src1:
        st.markdown("""
        <div class="pantry-card" style="border-top: 3px solid #10B981;">
            <div style="font-size: 1.05rem; font-weight: 700; color: #34D399; margin-bottom: 0.5rem;">
                🌾 Tracked Pantry Foods (Scale Measured)
            </div>
            <div style="font-size: 0.85rem; color: #CBD5E1; line-height: 1.7;">
                • <strong>Calories:</strong> {cal} kcal<br>
                • <strong>Carbs:</strong> {carb} g • <strong>Protein:</strong> {prot} g<br>
                • <strong>Fat:</strong> {fat} g • <strong>Sugar:</strong> {sug} g • <strong>Sodium:</strong> {sod} mg
            </div>
        </div>
        """.format(
            cal=pantry.get('calories_kcal', 0.0),
            carb=pantry.get('carbohydrates_g', 0.0),
            prot=pantry.get('protein_g', 0.0),
            fat=pantry.get('fat_g', 0.0),
            sug=pantry.get('sugar_g', 0.0),
            sod=pantry.get('sodium_mg', 0.0)
        ), unsafe_allow_html=True)

    with col_src2:
        st.markdown("""
        <div class="pantry-card" style="border-top: 3px solid #38BDF8;">
            <div style="font-size: 1.05rem; font-weight: 700; color: #38BDF8; margin-bottom: 0.5rem;">
                🍱 External & Manual Meal Logs (User Input)
            </div>
            <div style="font-size: 0.85rem; color: #CBD5E1; line-height: 1.7;">
                • <strong>Calories:</strong> {cal} kcal<br>
                • <strong>Carbs:</strong> {carb} g • <strong>Protein:</strong> {prot} g<br>
                • <strong>Fat:</strong> {fat} g • <strong>Sugar:</strong> {sug} g • <strong>Sodium:</strong> {sod} mg
            </div>
        </div>
        """.format(
            cal=manual.get('calories_kcal', 0.0),
            carb=manual.get('carbohydrates_g', 0.0),
            prot=manual.get('protein_g', 0.0),
            fat=manual.get('fat_g', 0.0),
            sug=manual.get('sugar_g', 0.0),
            sod=manual.get('sodium_mg', 0.0)
        ), unsafe_allow_html=True)

    st.markdown("---")

    # Lower Section: Manual Meal Logger & Recent Meals
    col_log, col_history = st.columns([1, 1.2])

    with col_log:
        st.subheader("📝 Log Meal Consumed Outside Pantry")
        st.caption("Record foods eaten outside the smart pantry to improve intake estimation:")
        with st.form("manual_meal_form"):
            m_name = st.text_input("Meal / Food Description", placeholder="e.g. Vegetable Biryani at Office")
            c_cal, c_carbs = st.columns(2)
            with c_cal:
                m_cal = st.number_input("Calories (kcal)", min_value=0.0, value=350.0, step=25.0)
            with c_carbs:
                m_carbs = st.number_input("Carbs (g)", min_value=0.0, value=45.0, step=5.0)

            c_prot, c_fat = st.columns(2)
            with c_prot:
                m_prot = st.number_input("Protein (g)", min_value=0.0, value=12.0, step=2.0)
            with c_fat:
                m_fat = st.number_input("Fat (g)", min_value=0.0, value=10.0, step=2.0)

            c_sug, c_sod = st.columns(2)
            with c_sug:
                m_sugar = st.number_input("Sugar (g)", min_value=0.0, value=4.0, step=1.0)
            with c_sod:
                m_sodium = st.number_input("Sodium (mg)", min_value=0.0, value=450.0, step=50.0)

            submit_meal = st.form_submit_button("Record External Meal", type="primary")
            if submit_meal:
                if not m_name.strip():
                    st.error("Meal description is required.")
                else:
                    ok, msg = PantryClient.log_meal({
                        "meal_name": m_name.strip(),
                        "calories": m_cal,
                        "carbohydrates": m_carbs,
                        "protein": m_prot,
                        "fat": m_fat,
                        "sugar": m_sugar,
                        "sodium": m_sodium,
                    })
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with col_history:
        st.subheader("📋 Recent Manually Logged Meals")
        meals = PantryClient.get_meal_logs()
        if meals:
            m_rows = []
            for m in meals[:10]:
                m_rows.append({
                    "Date & Time": format_timestamp(m.get("timestamp")),
                    "Meal": m["meal_name"],
                    "Calories": f"{m['calories']} kcal",
                    "Carbs": f"{m['carbohydrates']}g",
                    "Protein": f"{m['protein']}g",
                    "Fat": f"{m['fat']}g",
                })
            st.dataframe(pd.DataFrame(m_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No external meals logged yet. Use the form on the left to add one.")
