"""
View 9: Smart Alerts Center
Autonomous 24-hour deduplicated alert engine covering low stock, depletion countdowns,
anomalous spikes, dietary surges, refilling, and simulated sensor health.
"""

import streamlit as st
import pandas as pd
from dashboard.api_client import PantryClient
from dashboard.styles import get_priority_badge, format_timestamp


def _get_severity_badge(severity: str) -> str:
    s = severity.upper()
    if s == "CRITICAL":
        return '<span class="badge badge-urgent">⚡ CRITICAL</span>'
    elif s == "WARNING":
        return '<span class="badge badge-low">▲ WARNING</span>'
    elif s == "INFO":
        return '<span class="badge badge-normal">ℹ️ INFO</span>'
    return f'<span class="badge badge-insufficient">{s}</span>'


def render():
    st.markdown('<div class="app-header">🔔 SMART ALERTS CENTER</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Autonomous rule-based and ML anomaly alerts with stateful 24-hour deduplication.</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="disclaimer-banner">
        <strong>🛡️ 24-Hour Deduplication Engine:</strong>
        Alerts are evaluated against pantry inventory, ML forecasts, and consumption rates.
        To prevent alert fatigue, duplicate alerts for the same item and event type are suppressed if already emitted in the last 24 hours.
    </div>
    """, unsafe_allow_html=True)

    c_filter, c_btn = st.columns([3, 1])
    with c_filter:
        view_filter = st.radio(
            "Alert Filter",
            options=["Active / Unresolved", "All Alerts (including history)"],
            horizontal=True,
            label_visibility="collapsed"
        )
    with c_btn:
        if st.button("🔄 Sync & Re-check", use_container_width=True):
            st.rerun()

    unresolved_only = (view_filter == "Active / Unresolved")
    alerts = PantryClient.get_alerts(unresolved_only=unresolved_only)

    if not alerts:
        st.success("🎉 No active alerts! All containers, dietary thresholds, and sensors are within normal operating parameters.")
        return

    # Metrics Summary
    critical_cnt = sum(1 for a in alerts if a.get("severity") == "CRITICAL" and not a.get("is_resolved"))
    warning_cnt = sum(1 for a in alerts if a.get("severity") == "WARNING" and not a.get("is_resolved"))
    info_cnt = sum(1 for a in alerts if a.get("severity") == "INFO" and not a.get("is_resolved"))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Shown", len(alerts))
    with col2:
        st.metric("Critical", critical_cnt, delta_color="inverse")
    with col3:
        st.metric("Warnings", warning_cnt, delta_color="inverse")
    with col4:
        st.metric("Info", info_cnt)

    st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)

    # Display Alerts
    for a in alerts:
        sev_badge = _get_severity_badge(a.get("severity", "INFO"))
        is_res = a.get("is_resolved", False)
        status_text = "RESOLVED" if is_res else "ACTIVE"
        card_border = "#E2E8F0" if is_res else ("#FCA5A5" if a.get("severity") == "CRITICAL" else "#FCD34D")

        with st.container():
            col_lead, col_body, col_act = st.columns([1.5, 4.5, 1.2])

            with col_lead:
                st.markdown(f"**{a.get('alert_type', 'ALERT')}**")
                st.markdown(sev_badge, unsafe_allow_html=True)
                created_ts = format_timestamp(a.get("created_at"))
                st.caption(f"Logged: {created_ts}")

            with col_body:
                item_name = f" [{a.get('item_name')}]" if a.get("item_name") else ""
                st.markdown(f"**{a.get('title', 'Alert Notification')}{item_name}**")
                st.write(a.get("message", ""))
                if is_res:
                    res_ts = format_timestamp(a.get("resolved_at"))
                    st.caption(f"Status: ✅ Resolved at {res_ts}")

            with col_act:
                if not is_res:
                    if st.button("Mark Resolved", key=f"res_{a['id']}", use_container_width=True):
                        ok, msg = PantryClient.resolve_alert(a["id"])
                        if ok:
                            st.success("Alert resolved!")
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    st.caption("✅ Handled")

            st.markdown("<hr style='margin:0.5rem 0;'>", unsafe_allow_html=True)
