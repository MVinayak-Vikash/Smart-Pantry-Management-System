"""
View 7: Recipes & Meal Recommendations
Inventory-aware recipe matching, dynamic family-size ingredient scaling,
pantry clearing suggestions, and healthier alternatives.
"""

import streamlit as st
from dashboard.api_client import PantryClient


def render():
    st.markdown('<div class="app-header">📖 RECIPES & COOKING RECOMMENDATIONS</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Smart inventory-matched recipes scaled automatically to your household family size.</div>',
        unsafe_allow_html=True
    )

    recs = PantryClient.get_recipe_recommendations()
    if not recs:
        st.info("No recipe recommendations available.")
        return

    family_size = recs.get("family_size", 4)
    st.info(f"👨‍👩‍👧‍👦 **Serving Scaler Active**: All ingredient portions below are dynamically calculated for **{family_size} persons**.")

    tab1, tab2, tab3, tab4 = st.tabs([
        f"🍳 Ready to Cook ({len(recs.get('ready_to_cook', []))})",
        f"🛒 Missing Ingredients ({len(recs.get('missing_ingredients', []))})",
        f"⏳ Pantry Clearers ({len(recs.get('pantry_clearers', []))})",
        f"🥗 Healthier Alternatives ({len(recs.get('healthier_alternatives', []))})"
    ])

    def render_recipe_list(recipe_list, empty_msg):
        if not recipe_list:
            st.caption(empty_msg)
            return

        for r in recipe_list:
            cat = r.get("category", "Main Dish")
            cals = int(r.get("estimated_calories_per_serving", 0))
            with st.expander(f"🍲 {r['name'].upper()} • {cat} • ~{cals} kcal/person"):
                st.markdown(f"*{r['description']}*")
                
                # Metadata Pills
                st.markdown(f"""
                <div style="display:flex; gap:0.5rem; margin:0.6rem 0; flex-wrap:wrap;">
                    <span class="badge badge-normal">⏱️ Prep: {r['prep_time_minutes']} mins</span>
                    <span class="badge badge-avail">👥 Servings: {r['target_servings']} persons</span>
                    <span class="badge badge-tag">🔥 {cals} kcal / serving</span>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("**Scaled Ingredient Quantities:**")
                for ing in r["ingredients"]:
                    is_in = ing.get("is_in_stock")
                    badge_span = '<span class="badge badge-avail">✅ In Stock</span>' if is_in else '<span class="badge badge-unavail">❌ Needs Purchase</span>'
                    curr_disp = f"<span style='color:#94A3B8;'>(Pantry: {ing['current_stock']}g)</span>" if ing.get("current_stock") is not None else "<span style='color:#64748B;'>(External Fresh)</span>"
                    st.markdown(
                        f"• **{ing['item_name']}**: `{ing['scaled_quantity']} {ing['unit']}` — {badge_span} {curr_disp}",
                        unsafe_allow_html=True
                    )

                st.markdown("<br><strong>👨‍🍳 Preparation Instructions:</strong>", unsafe_allow_html=True)
                st.info(r["instructions"])

                tags = " • ".join(r.get("tags", []))
                st.caption(f"Tags: {tags}")

    with tab1:
        render_recipe_list(recs.get("ready_to_cook", []), "No recipes are 100% in stock right now. Check missing ingredients.")

    with tab2:
        render_recipe_list(recs.get("missing_ingredients", []), "All recipes are currently cookable with pantry stock!")

    with tab3:
        render_recipe_list(recs.get("pantry_clearers", []), "No items currently approaching depletion requiring urgent pantry clearing.")

    with tab4:
        render_recipe_list(recs.get("healthier_alternatives", []), "No specific healthier alternative tags currently active.")
