"""Hệ thống giao diện dùng chung (kế thừa từ bản AI Personal OS)."""
from html import escape

import streamlit as st


def inject_styles() -> None:
    """Apply the shared light SaaS design system."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@500;600;700;800&display=swap');

        :root {
            --app-bg: #f5f6fa;
            --surface: #ffffff;
            --surface-soft: #fafaff;
            --ink: #20243a;
            --muted: #7b8197;
            --line: #e9eaf2;
            --accent: #7357e8;
            --accent-dark: #5b42c8;
            --accent-soft: #f0edff;
            --navy: #171a2e;
            --navy-soft: #222640;
            --success: #16866a;
            --warning: #c58a28;
            --danger: #cc5e69;
        }

        html, body, [class*="css"] {
            font-family: 'DM Sans', sans-serif;
        }
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 82% 0%, rgba(126, 103, 236, .07), transparent 28rem),
                var(--app-bg);
            color: var(--ink);
        }
        [data-testid="stHeader"],
        [data-testid="stToolbar"] {
            background: transparent !important;
            pointer-events: none;
        }
        [data-testid="stToolbarActions"],
        [data-testid="stMainMenu"],
        [data-testid="stAppDeployButton"],
        .stDeployButton,
        [data-testid="stDecoration"] {
            display: none !important;
        }
        [data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] {
            pointer-events: auto !important;
            background: rgba(255, 255, 255, 0.95) !important;
            border: 1px solid var(--line) !important;
            border-radius: 10px !important;
            box-shadow: 0 2px 8px rgba(28, 30, 62, .08) !important;
        }
        [data-testid="stSidebar"] {
            min-width: 270px;
            max-width: 270px;
        }
        [data-testid="stSidebar"] > div:first-child {
            background: linear-gradient(178deg, #171a2e 0%, #1d2139 58%, #24213f 100%);
            border-right: 1px solid rgba(255,255,255,.06);
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] small { color: #d8dbeb; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { font-size: .88rem; }
        /* Điều hướng của st.navigation: hiển thị và đổi màu cho nền tối */
        [data-testid="stSidebarNav"] { display: block; }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
        [data-testid="stSidebar"] nav a { color: #d8dbeb !important; border-radius: 10px; margin: 2px 8px; padding: .45rem .7rem; }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a span,
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a p,
        [data-testid="stSidebar"] nav a span, [data-testid="stSidebar"] nav a p { color: #d8dbeb !important; font-weight: 600; }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover,
        [data-testid="stSidebar"] nav a:hover { background: rgba(255,255,255,.08); }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"],
        [data-testid="stSidebar"] nav a[aria-current="page"] { background: rgba(115,87,232,.35); }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] span,
        [data-testid="stSidebar"] nav a[aria-current="page"] span { color: #ffffff !important; }
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
            border-radius: 12px;
            padding: .63rem .8rem;
            margin: .14rem 0;
            color: #d8dbeb;
            transition: background .18s ease, transform .18s ease;
        }
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
            background: rgba(255,255,255,.09);
            transform: translateX(2px);
        }
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p { color: inherit !important; }
        [data-testid="stSidebar"] .stButton > button {
            background: rgba(255,255,255,.08);
            border: 1px solid rgba(255,255,255,.12);
            color: #fff;
            border-radius: 11px;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(255,255,255,.14);
            border-color: rgba(255,255,255,.24);
            color: #fff;
        }
        [data-testid="stSidebar"] [data-testid="stToggle"] label { color: #e6e7f0; }

        .block-container {
            max-width: 1450px;
            padding-top: 2.15rem;
            padding-bottom: 3.5rem;
            padding-left: 2.6rem;
            padding-right: 2.6rem;
        }
        h1, h2, h3, h4 {
            color: var(--ink) !important;
            font-family: 'Manrope', sans-serif !important;
            letter-spacing: -.035em;
        }
        h1 { font-size: clamp(1.8rem, 3vw, 2.5rem) !important; font-weight: 800 !important; }
        h2 { font-size: 1.45rem !important; font-weight: 750 !important; }
        h3 { font-size: 1.08rem !important; font-weight: 750 !important; }
        p, li, label { color: #4f556c; }
        [data-testid="stCaptionContainer"] p { color: var(--muted); }
        [data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--line);
            padding: 1rem 1.1rem;
            border-radius: 17px;
            box-shadow: 0 5px 18px rgba(28, 30, 62, .035);
        }
        [data-testid="stMetricLabel"] p { color: var(--muted) !important; font-size: .82rem; font-weight: 600; }
        [data-testid="stMetricValue"] { color: var(--ink) !important; font-family: 'Manrope', sans-serif; font-weight: 800; }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--line) !important;
            border-radius: 18px !important;
            background: rgba(255,255,255,.94);
            box-shadow: 0 7px 24px rgba(28, 30, 62, .035);
        }
        [data-testid="stProgressBar"] > div > div > div > div {
            background: linear-gradient(90deg, #8069ed, #a18df5);
            border-radius: 999px;
        }
        [data-testid="stProgressBar"] > div { background: #eeedf5; border-radius: 999px; }
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 11px;
            font-weight: 700;
            min-height: 2.65rem;
            transition: transform .15s ease, box-shadow .15s ease;
        }
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
            background: var(--accent);
            border: 1px solid var(--accent);
            color: white;
            box-shadow: 0 5px 13px rgba(115,87,232,.18);
        }
        .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
            background: var(--accent-dark);
            border-color: var(--accent-dark);
            transform: translateY(-1px);
            box-shadow: 0 8px 18px rgba(115,87,232,.22);
        }
        .stTextInput input, .stTextArea textarea, .stNumberInput input {
            border-radius: 11px !important;
            border-color: #e5e6ef !important;
            background: #fff !important;
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #9c8cf0 !important;
            box-shadow: 0 0 0 2px rgba(115,87,232,.12) !important;
        }
        [data-baseweb="tab-list"] { gap: .45rem; border-bottom: 1px solid var(--line); }
        [data-baseweb="tab"] { border-radius: 10px 10px 0 0; font-weight: 700; }
        [aria-selected="true"] { color: var(--accent) !important; }
        div[data-testid="stExpander"] {
            border: 1px solid var(--line);
            border-radius: 13px;
            background: #fff;
        }
        hr { border-color: var(--line) !important; }

        .brand-lockup { display:flex; align-items:center; gap:11px; padding:.25rem .15rem 1.35rem; }
        .brand-mark {
            width:39px; height:39px; display:flex; align-items:center; justify-content:center;
            border-radius:13px; color:white; font-size:1.12rem; font-weight:800;
            background:linear-gradient(145deg,#967fff,#644bdd);
            box-shadow:0 7px 20px rgba(115,87,232,.32);
        }
        .brand-name { color:#fff; font:800 1rem 'Manrope',sans-serif; letter-spacing:-.03em; }
        .brand-sub { color:#9da2bf; font-size:.68rem; margin-top:1px; }
        .side-label { color:#8f95b2; text-transform:uppercase; letter-spacing:.12em; font-size:.66rem; font-weight:800; margin:1.15rem .2rem .5rem; }
        .side-user {
            display:flex; align-items:center; gap:10px; padding:.8rem;
            background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.08);
            border-radius:14px; margin:.45rem 0 .75rem;
        }
        .avatar {
            width:34px; height:34px; display:flex; align-items:center; justify-content:center;
            border-radius:50%; background:#dcd5ff; color:#5843bb; font-weight:800;
        }
        .side-user-name { color:#fff; font-weight:700; font-size:.82rem; }
        .side-user-role { color:#9da2bf; font-size:.7rem; }
        .side-footnote { color:#8f95b2; font-size:.7rem; line-height:1.55; margin-top:.6rem; }

        .eyebrow { color:var(--accent); font-size:.72rem; font-weight:800; letter-spacing:.13em; text-transform:uppercase; margin-bottom:.45rem; }
        .page-description { color:var(--muted); font-size:.96rem; margin-top:-.7rem; margin-bottom:1.6rem; }
        .hero-panel {
            position:relative; overflow:hidden; padding:1.65rem 1.8rem; border-radius:22px;
            color:#fff; background:linear-gradient(112deg,#29234d 0%,#5140a1 54%,#7863d9 100%);
            box-shadow:0 15px 35px rgba(72,55,151,.16); margin:.3rem 0 1.35rem;
        }
        .hero-panel:after {
            content:''; position:absolute; width:260px; height:260px; right:-65px; top:-135px;
            border:1px solid rgba(255,255,255,.16); border-radius:50%;
            box-shadow:0 0 0 28px rgba(255,255,255,.035),0 0 0 58px rgba(255,255,255,.025);
        }
        .hero-kicker { color:#d8d0ff; text-transform:uppercase; letter-spacing:.13em; font-size:.68rem; font-weight:800; }
        .hero-title { color:#fff; font:800 clamp(1.4rem,2.5vw,2rem) 'Manrope',sans-serif; letter-spacing:-.045em; margin:.45rem 0 .3rem; }
        .hero-copy { color:#e2ddff; max-width:760px; font-size:.91rem; line-height:1.6; }
        .hero-chip { display:inline-flex; margin-top:1rem; padding:.38rem .7rem; border:1px solid rgba(255,255,255,.24); border-radius:999px; color:#fff; font-size:.73rem; font-weight:700; background:rgba(255,255,255,.1); }
        .section-heading { display:flex; align-items:center; gap:.6rem; margin:.3rem 0 .15rem; }
        .section-dot { width:8px; height:8px; border-radius:50%; background:var(--accent); box-shadow:0 0 0 5px var(--accent-soft); }
        .task-title { color:var(--ink); font-weight:750; font-size:.98rem; line-height:1.4; }
        .task-meta { color:var(--muted); font-size:.77rem; line-height:1.55; margin-top:.25rem; }
        .status-pill { display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:.35rem .62rem; font-size:.71rem; font-weight:800; white-space:nowrap; }
        .status-done { color:#14795f; background:#e8f7f1; }
        .status-active { color:#8a641c; background:#fff5df; }
        .status-pending { color:#687087; background:#f0f1f6; }
        .info-banner { padding:.85rem 1rem; border:1px solid #e7e2ff; border-radius:13px; background:#f7f5ff; color:#6555a8; font-size:.84rem; line-height:1.55; }
        .feature-card { padding:1.1rem; height:100%; border-radius:17px; background:#fff; border:1px solid var(--line); box-shadow:0 6px 18px rgba(28,30,62,.035); }
        .feature-icon { width:38px; height:38px; display:flex; align-items:center; justify-content:center; border-radius:12px; background:var(--accent-soft); font-size:1.1rem; margin-bottom:.75rem; }
        .feature-title { color:var(--ink); font-weight:800; font-size:.95rem; margin-bottom:.35rem; }
        .feature-copy { color:var(--muted); font-size:.8rem; line-height:1.55; }
        .goal-level { padding:.95rem; border-radius:14px; border:1px solid var(--line); background:#fff; }
        .goal-level-kicker { color:var(--muted); font-size:.68rem; text-transform:uppercase; letter-spacing:.1em; font-weight:800; }
        .goal-level-value { color:var(--ink); font:800 1.55rem 'Manrope',sans-serif; margin:.25rem 0; }
        .calendar-day { min-height:88px; padding:.65rem .5rem; border-radius:13px; text-align:center; border:1px solid rgba(31,36,61,.05); margin-bottom:.55rem; }
        .calendar-day-number { font-size:.72rem; opacity:.78; font-weight:700; }
        .calendar-day-rate { font:800 1.12rem 'Manrope',sans-serif; margin-top:.25rem; }
        .legend-item { display:flex; align-items:center; gap:7px; color:var(--muted); font-size:.76rem; }
        .legend-swatch { width:10px; height:10px; border-radius:3px; }
        .auth-panel { padding:1rem 0 .2rem; }
        .muted-small { color:var(--muted); font-size:.77rem; }
        .profile-grid { display:grid; grid-template-columns:1fr 1fr; gap:.8rem; margin-top:.4rem; }
        .profile-item { padding:.9rem 1rem; border-radius:14px; border:1px solid var(--line); background:var(--surface-soft); }
        .profile-wide { grid-column: span 2; }
        .profile-label { color:var(--muted); font-size:.68rem; text-transform:uppercase; letter-spacing:.1em; font-weight:800; }
        .profile-value { color:var(--ink); font-weight:650; font-size:.93rem; line-height:1.5; margin-top:.3rem; }
        .interest-row { display:flex; flex-wrap:wrap; gap:.45rem; margin-top:.4rem; }
        .interest-chip { padding:.3rem .65rem; border-radius:999px; background:var(--accent-soft); color:#5b42c8; font-size:.76rem; font-weight:700; }
        .survey-step { color:var(--accent); font-size:.72rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }
        @media (max-width: 700px) {
            .profile-grid { grid-template-columns:1fr; }
            .profile-wide { grid-column: auto; }
        }
        @media (max-width: 900px) {
            .block-container { padding-top: 3rem; padding-left:1.2rem; padding-right:1.2rem; }
            [data-testid="stSidebar"] { min-width:245px; max-width:245px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


EXTRA_CSS = """
<style>
.quote-card { padding:1.6rem 1.8rem; border-radius:20px; background:linear-gradient(135deg,#f0edff 0%,#eaf2ff 100%);
  border:1px solid #e3ddfb; }
.quote-text { font-family:'Manrope',sans-serif; font-size:1.25rem; font-weight:700; color:#20243a; line-height:1.5; }
.quote-author { margin-top:.7rem; color:#6550cb; font-size:.85rem; font-weight:800; }
.dream-footer { margin-top:2.2rem; padding:1.4rem; text-align:center; border-radius:18px; background:#20243a; color:#ffffff;
  font-family:'Manrope',sans-serif; font-size:1.15rem; font-weight:700; letter-spacing:.01em; }
.task-duration { display:inline-block; padding:.32rem .75rem; border-radius:999px; background:#20243a; color:#ffffff;
  font-size:.8rem; font-weight:800; white-space:nowrap; letter-spacing:.01em; }
.task-board-head { padding:1.2rem 1.4rem; border-radius:18px; background:linear-gradient(135deg,#20243a 0%,#3a2a7a 100%);
  color:#ffffff; margin-bottom:1rem; }
.task-board-title { font-family:'Manrope',sans-serif; font-size:1.05rem; font-weight:800; }
.task-board-sub { color:#c9cde4; font-size:.85rem; margin-top:.25rem; }
.task-bar { height:10px; background:rgba(255,255,255,.18); border-radius:99px; margin-top:.9rem; overflow:hidden; }
.task-bar-fill { height:10px; border-radius:99px; background:linear-gradient(90deg,#7357e8,#22c55e); }
.task-chip { display:inline-block; padding:.25rem .6rem; border-radius:999px; font-size:.74rem; font-weight:800; white-space:nowrap; }
.task-chip-todo { background:#fff4e5; color:#b77b22; }
.task-chip-done { background:#dff5eb; color:#167456; }
.task-chip-optional { background:#eef0ff; color:#5b42c8; }
.task-goal { color:#6550cb; font-size:.78rem; font-weight:700; margin-top:.15rem; }
[data-testid="stCheckbox"] label p { font-size:1.02rem !important; font-weight:700 !important; color:#20243a !important; }
.note-card { padding:1rem 1.2rem; border-radius:16px; border:1px solid #e9eaf2; background:#ffffff; margin-bottom:.6rem; }
.important-badge { display:inline-block; padding:.15rem .55rem; border-radius:999px; background:#fff4e5; color:#b77b22;
  font-size:.72rem; font-weight:800; margin-left:.4rem; }
</style>
"""


def apply_theme() -> None:
    inject_styles()
    st.markdown(EXTRA_CSS, unsafe_allow_html=True)


def page_heading(eyebrow: str, title: str, description: str) -> None:
    st.markdown(
        f'<div class="eyebrow">{escape(eyebrow)}</div>'
        f'<h1 style="margin:0 0 .8rem">{escape(title)}</h1>'
        f'<div class="page-description">{escape(description)}</div>',
        unsafe_allow_html=True,
    )


def section(title: str, dot: bool = True) -> None:
    dot_html = '<span class="section-dot"></span>' if dot else ""
    st.markdown(
        f'<div class="section-heading">{dot_html}<h2 style="margin:0">{escape(title)}</h2></div>',
        unsafe_allow_html=True,
    )
