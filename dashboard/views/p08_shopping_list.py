"""
View 8: Smart Grocery & Restock List
Auto-generated shopping list triggered by low stock, predicted runouts,
and Target Stock Level replenishment policies.
"""

import streamlit as st
import pandas as pd
from dashboard.api_client import PantryClient
from dashboard.styles import format_quantity, get_priority_badge, format_timestamp


def render():
    st.markdown('<div class="app-header">🛒 SMART GROCERY & RESTOCK LIST</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Automated replenishment suggestions based on container depletion forecasts and minimum thresholds.</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="disclaimer-banner">
        <strong>📋 Target Stock Level Policy:</strong>
        Suggested purchases replenish containers to their ideal capacity:
        <code>Suggested Purchase = max(0, Target Capacity - Current Stock)</code>.
        Items predicted to run out in &le; 2 days are flagged as <strong>URGENT</strong>.
    </div>
    """, unsafe_allow_html=True)

    col_btn, _ = st.columns([1, 2])
    with col_btn:
        if st.button("🔄 Re-evaluate Restock Needs", use_container_width=True, type="primary"):
            ok, msg = PantryClient.generate_shopping_list()
            if ok:
                st.success("Re-evaluated inventory against restock policy!")
                st.rerun()

    items = PantryClient.get_shopping_list()
    if not items:
        st.success("🎉 All pantry staples are well stocked! No replenishment currently needed.")
        return

    # Split into Pending and Purchased
    pending = [i for i in items if i.get("status") == "PENDING"]
    purchased = [i for i in items if i.get("status") == "PURCHASED"]

    st.subheader(f"📌 Items to Purchase ({len(pending)})")
    if pending:
        for it in pending:
            p_badge = get_priority_badge(it.get("priority", "MEDIUM"))
            dep_text = f"~{it['predicted_depletion_days']:.1f} days left" if it.get("predicted_depletion_days") else "Low stock"

            with st.container():
                c1, c2, c3, c4 = st.columns([2, 1.5, 3, 1.2])
                with c1:
                    st.markdown(f"**{it['item_name']}**")
                    st.caption(f"Current: {format_quantity(it.get('current_quantity', 0))}")
                with c2:
                    st.markdown(f"Buy: **{format_quantity(it['suggested_quantity'])}**")
                    st.caption(dep_text)
                with c3:
                    st.markdown(p_badge, unsafe_allow_html=True)
                    st.caption(it.get("reason", ""))
                with c4:
                    if st.button("✅ Purchased", key=f"buy_{it['id']}", use_container_width=True):
                        ok, msg = PantryClient.mark_shopping_purchased(it["id"])
                        if ok:
                            st.success(f"Restocked {it['item_name']}!")
                            st.rerun()
                st.markdown("<hr style='margin:0.5rem 0;'>", unsafe_allow_html=True)
    else:
        st.info("No pending items on the restock list.")

    if purchased:
        with st.expander(f"🏁 Recently Restocked Items ({len(purchased)})"):
            p_rows = []
            for it in purchased:
                p_rows.append({
                    "Item": it["item_name"],
                    "Purchased Quantity": format_quantity(it["suggested_quantity"]),
                    "Date Logged": format_timestamp(it.get("updated_at"))[:10] if it.get("updated_at") else "Recent",
                    "Status": "COMPLETED & REFILLED"
                })
            st.dataframe(pd.DataFrame(p_rows), use_container_width=True, hide_index=True)
