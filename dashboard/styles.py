"""
Ultra-Modern Design System, Glassmorphism Styling, Neon Badges, and Visual Gauges
for the Smart Pantry Management System Streamlit Web Application.
"""

import streamlit as st
from typing import Dict, Any, Optional


def apply_custom_styles():
    """Apply global CSS design tokens, glowing cards, glassmorphism, and responsive typography."""
    st.markdown("""
    <style>
        /* Import clean modern tech fonts */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #F8FAFC;
        }

        /* Top Header with Vibrant Gradient */
        .app-header {
            font-family: 'Outfit', sans-serif;
            font-size: 2.35rem;
            font-weight: 800;
            background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.03em;
            margin-bottom: 0.25rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .app-subtitle {
            font-size: 0.98rem;
            color: #94A3B8;
            margin-bottom: 1.25rem;
            line-height: 1.5;
        }

        /* Live Status Banner Pill */
        .live-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 9999px;
            padding: 0.3rem 0.9rem;
            font-size: 0.78rem;
            font-weight: 600;
            color: #38BDF8;
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.15);
            margin-bottom: 1rem;
        }

        .live-dot {
            width: 8px;
            height: 8px;
            background-color: #10B981;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px #10B981;
            animation: pulse-glow 2s infinite ease-in-out;
        }

        @keyframes pulse-glow {
            0%, 100% {
                transform: scale(1);
                opacity: 1;
                box-shadow: 0 0 8px #10B981;
            }
            50% {
                transform: scale(1.3);
                opacity: 0.6;
                box-shadow: 0 0 16px #10B981;
            }
        }

        /* Notice & Disclaimer Boxes */
        .disclaimer-banner {
            background: rgba(15, 23, 42, 0.75);
            border-left: 4px solid #38BDF8;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 0.85rem 1.15rem;
            font-size: 0.88rem;
            color: #CBD5E1;
            margin-bottom: 1.25rem;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
        }
        .diet-disclaimer {
            background: rgba(30, 27, 75, 0.5);
            border-left: 4px solid #F59E0B;
            border-radius: 10px;
            padding: 0.85rem 1.15rem;
            font-size: 0.85rem;
            color: #FDE68A;
            margin-bottom: 1rem;
            backdrop-filter: blur(12px);
        }

        /* Glassmorphic Cards */
        .pantry-card {
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 1.35rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            margin-bottom: 1.15rem;
            backdrop-filter: blur(16px);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .pantry-card:hover {
            transform: translateY(-4px);
            border-color: rgba(56, 189, 248, 0.4);
            box-shadow: 0 16px 40px -4px rgba(0, 0, 0, 0.6), 0 0 20px rgba(56, 189, 248, 0.15);
        }

        .card-top-stripe {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
        }

        .card-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.6rem;
            margin-top: 0.2rem;
        }

        .card-title-wrap {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .card-icon {
            font-size: 1.4rem;
        }

        .card-title-text {
            font-family: 'Outfit', sans-serif;
            font-size: 1.25rem;
            font-weight: 700;
            color: #F8FAFC;
            letter-spacing: -0.01em;
        }

        .card-weight-big {
            font-family: 'Outfit', sans-serif;
            font-size: 2.1rem;
            font-weight: 800;
            color: #FFFFFF;
            margin: 0.25rem 0;
            letter-spacing: -0.03em;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }

        .card-subtext {
            font-size: 0.8rem;
            color: #94A3B8;
            margin-bottom: 0.75rem;
        }

        /* Visual Progress Level Bar */
        .progress-container {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 9999px;
            overflow: hidden;
            margin: 0.6rem 0;
            position: relative;
        }

        .progress-bar-fill {
            height: 100%;
            border-radius: 9999px;
            transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 0 10px currentColor;
        }

        .progress-label-row {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: #94A3B8;
            margin-bottom: 0.5rem;
        }

        /* Divider */
        .card-divider {
            margin: 0.75rem 0;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
        }

        /* Neon Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .badge-avail {
            background-color: rgba(16, 185, 129, 0.15);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.35);
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
        }

        .badge-low {
            background-color: rgba(245, 158, 11, 0.15);
            color: #FBBF24;
            border: 1px solid rgba(245, 158, 11, 0.35);
            box-shadow: 0 0 12px rgba(245, 158, 11, 0.2);
        }

        .badge-unavail {
            background-color: rgba(239, 68, 68, 0.15);
            color: #F87171;
            border: 1px solid rgba(239, 68, 68, 0.4);
            box-shadow: 0 0 12px rgba(239, 68, 68, 0.25);
        }

        .badge-normal {
            background-color: rgba(56, 189, 248, 0.12);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }

        .badge-high {
            background-color: rgba(249, 115, 22, 0.15);
            color: #FB923C;
            border: 1px solid rgba(249, 115, 22, 0.35);
            box-shadow: 0 0 12px rgba(249, 115, 22, 0.2);
        }

        .badge-insufficient {
            background-color: rgba(100, 116, 139, 0.15);
            color: #94A3B8;
            border: 1px solid rgba(100, 116, 139, 0.3);
        }

        .badge-urgent {
            background-color: rgba(239, 68, 68, 0.2);
            color: #FCA5A5;
            border: 1px solid rgba(239, 68, 68, 0.6);
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
            animation: pulse-urgent 1.5s infinite ease-in-out;
        }

        @keyframes pulse-urgent {
            0%, 100% {
                box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
            }
            50% {
                box-shadow: 0 0 20px rgba(239, 68, 68, 0.7);
            }
        }

        /* KPI Stat Containers */
        [data-testid="stMetric"] {
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 14px;
            padding: 1rem 1.15rem;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
            transition: all 0.2s ease;
        }
        [data-testid="stMetric"]:hover {
            border-color: rgba(56, 189, 248, 0.3);
            transform: translateY(-2px);
        }

        /* Global Button Enhancements */
        .stButton > button {
            background: linear-gradient(135deg, #0284C7 0%, #4F46E5 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            letter-spacing: 0.02em !important;
            padding: 0.55rem 1.25rem !important;
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3) !important;
            transition: all 0.25s ease !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(2, 132, 199, 0.5) !important;
            border-color: rgba(255, 255, 255, 0.3) !important;
        }

        /* Section Boxes */
        .section-box {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 14px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(12px);
        }

        /* Custom Modern Scrollbars */
        ::-webkit-scrollbar {
            width: 7px;
            height: 7px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.6);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(56, 189, 248, 0.25);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(56, 189, 248, 0.5);
        }
    </style>
    """, unsafe_allow_html=True)


def get_item_accent(item_name: str) -> Dict[str, str]:
    """Retrieve distinct color, icon, gradient, and glow for each pantry staple."""
    name_lower = (item_name or "").lower()
    if "rice" in name_lower:
        return {
            "icon": "🌾",
            "color": "#F59E0B",
            "gradient": "linear-gradient(90deg, #F59E0B, #D97706)",
            "glow": "rgba(245, 158, 11, 0.4)",
            "bg_tint": "rgba(245, 158, 11, 0.05)",
        }
    elif "sugar" in name_lower:
        return {
            "icon": "🧊",
            "color": "#06B6D4",
            "gradient": "linear-gradient(90deg, #06B6D4, #0284C7)",
            "glow": "rgba(6, 182, 212, 0.4)",
            "bg_tint": "rgba(6, 182, 212, 0.05)",
        }
    elif "salt" in name_lower:
        return {
            "icon": "🧂",
            "color": "#A855F7",
            "gradient": "linear-gradient(90deg, #A855F7, #7C3AED)",
            "glow": "rgba(168, 85, 247, 0.4)",
            "bg_tint": "rgba(168, 85, 247, 0.05)",
        }
    elif "ghee" in name_lower:
        return {
            "icon": "🧈",
            "color": "#10B981",
            "gradient": "linear-gradient(90deg, #10B981, #059669)",
            "glow": "rgba(16, 185, 129, 0.4)",
            "bg_tint": "rgba(16, 185, 129, 0.05)",
        }
    else:
        return {
            "icon": "🥫",
            "color": "#38BDF8",
            "gradient": "linear-gradient(90deg, #38BDF8, #6366F1)",
            "glow": "rgba(56, 189, 248, 0.4)",
            "bg_tint": "rgba(56, 189, 248, 0.05)",
        }


def format_quantity(grams: float) -> str:
    """Format grams into kg and grams dual representation."""
    if grams is None:
        return "N/A"
    if grams >= 1000:
        kg = grams / 1000.0
        return f"{kg:.2f} kg ({int(grams):,} g)"
    return f"{int(grams):,} g"


def get_availability_badge(status: str) -> str:
    if status == "AVAILABLE":
        return '<span class="badge badge-avail"><span style="color:#10B981;">●</span> AVAILABLE</span>'
    elif status == "LOW":
        return '<span class="badge badge-low"><span style="color:#F59E0B;">▲</span> LOW STOCK</span>'
    else:
        return '<span class="badge badge-unavail"><span style="color:#EF4444;">✕</span> OUT OF STOCK</span>'


def get_intake_badge(status: str) -> str:
    if status == "NORMAL":
        return '<span class="badge badge-normal">● NORMAL</span>'
    elif status == "HIGH":
        return '<span class="badge badge-high">⚠️ HIGH INTAKE</span>'
    else:
        return '<span class="badge badge-insufficient">INSUFFICIENT DATA</span>'


def get_priority_badge(priority: str) -> str:
    p = priority.upper()
    if p == "URGENT":
        return '<span class="badge badge-urgent">⚡ URGENT</span>'
    elif p == "HIGH":
        return '<span class="badge badge-low">▲ HIGH</span>'
    elif p == "MEDIUM":
        return '<span class="badge badge-normal">● MEDIUM</span>'
    else:
        return '<span class="badge badge-insufficient">LOW</span>'


def format_timestamp(ts) -> str:
    """Safely format datetime objects or ISO timestamp strings."""
    if not ts:
        return ""
    if hasattr(ts, "strftime"):
        return ts.strftime("%Y-%m-%d %H:%M")
    return str(ts)[:16].replace("T", " ")


def render_pantry_card_html(
    item: Dict[str, Any],
    pred_depletion_date: Optional[str] = None,
    avg_intake_text: str = "Insufficient data",
    rem_days_text: str = "Insufficient data"
) -> str:
    """Generate an innovative, vibrant glassmorphic card for a pantry container."""
    accent = get_item_accent(item.get("name", ""))
    avail_badge = get_availability_badge(item.get("availability_status", "AVAILABLE"))
    intake_badge = get_intake_badge(item.get("intake_status", "INSUFFICIENT_DATA"))

    curr_qty = float(item.get("current_quantity") if item.get("current_quantity") is not None else item.get("current_weight", 0.0))
    init_qty = float(item.get("initial_quantity") or 5000.0)
    fill_pct = min(100.0, max(0.0, (curr_qty / init_qty) * 100.0)) if init_qty > 0 else 0.0

    # Color shift for progress bar based on level
    if fill_pct > 40.0:
        bar_gradient = accent["gradient"]
    elif fill_pct > 15.0:
        bar_gradient = "linear-gradient(90deg, #F59E0B, #D97706)"
    else:
        bar_gradient = "linear-gradient(90deg, #EF4444, #DC2626)"

    depletion_html = (
        f"📅 Est. Runout: <strong style='color:#38BDF8;'>{pred_depletion_date}</strong>"
        if pred_depletion_date
        else f"⏱️ Remaining: <strong style='color:#38BDF8;'>{rem_days_text}</strong>"
    )

    return f"""
    <div class="pantry-card" style="border-top: 3px solid {accent['color']};">
        <div class="card-header-row">
            <div class="card-title-wrap">
                <span class="card-icon">{accent['icon']}</span>
                <span class="card-title-text">{item['name'].upper()}</span>
            </div>
            {avail_badge}
        </div>
        <div class="card-weight-big" style="color: {accent['color']};">
            {format_quantity(curr_qty)}
        </div>
        <div class="card-subtext">
            Min Limit: {int(item.get('minimum_quantity', 0))} {item.get('unit', 'g')} • Capacity: {int(init_qty):,} g
        </div>

        <div class="progress-label-row">
            <span>Container Fill Level</span>
            <span style="font-weight:700; color:{accent['color']};">{fill_pct:.1f}%</span>
        </div>
        <div class="progress-container">
            <div class="progress-bar-fill" style="width: {fill_pct}%; background: {bar_gradient};"></div>
        </div>

        <div class="card-divider"></div>

        <div style="font-size:0.83rem; margin-bottom:5px; display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#94A3B8;">Intake Status:</span>
            {intake_badge}
        </div>
        <div style="font-size:0.83rem; color:#94A3B8; margin-bottom:4px; display:flex; justify-content:space-between;">
            <span>Daily Intake:</span>
            <strong style="color:#F1F5F9;">{avg_intake_text}</strong>
        </div>

        <div class="card-divider"></div>

        <div style="font-size:0.84rem; color:#CBD5E1; text-align:center; padding-top:2px;">
            {depletion_html}
        </div>
    </div>
    """
