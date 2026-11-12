from html import escape

import streamlit as st

from core import repo
from core.common import current_school_year, greeting, now
from core.quotes import random_quote
from core.theme import page_heading, section
from core.widgets import profile_fields, render_personal_info


def _reroll_quote() -> None:
    st.session_state.quote_index, st.session_state.quote = random_quote(st.session_state.get("quote_index"))


if "quote" not in st.session_state:
    _reroll_quote()

name = repo.get_name() or "bạn"
hello = greeting(now().hour)
quote = st.session_state.quote

# ---------- Tiêu đề chào mừng + câu truyền cảm hứng ----------
st.markdown(
    f'<div class="eyebrow">TỔNG QUAN</div>'
    f'<div class="hero-panel">'
    f'<div class="hero-kicker">{escape(hello)}</div>'
    f'<div class="hero-title">Welcome {escape(name)}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

quote_col, btn_col = st.columns([6, 1], vertical_alignment="center")
with quote_col:
    st.markdown(
        f'<div class="quote-card"><div class="quote-text">“{escape(quote["text"])}”</div>'
        f'<div class="quote-author">— {escape(quote["author"])}</div>'
        f'<div class="muted-small" style="margin-top:.5rem">{escape(quote["vi"])}</div></div>',
        unsafe_allow_html=True,
    )
with btn_col:
    st.button("🔄 Câu khác", on_click=_reroll_quote, use_container_width=True)

# ---------- Thông tin cá nhân (theo năm học) ----------
st.markdown("<br>", unsafe_allow_html=True)
section("Thông tin cá nhân")

years = [p["school_year"] for p in repo.list_profile_years()]
current_year = current_school_year()
if not years:
    years = [current_year]

view_year = st.selectbox(
    "Năm học",
    options=years,
    index=0,
    key="overview_view_year",
    help="Xem thông tin của các năm học trước.",
)
profile = repo.get_profile(view_year)

with st.container(border=True):
    render_personal_info(profile)

# ---------- Cập nhật thông tin qua các năm ----------
with st.expander("✏️ Cập nhật thông tin"):
    start_year = int(current_year[:4])
    next_year = f"{start_year + 1}-{start_year + 2}"
    edit_years = sorted(set(years) | {current_year, next_year}, reverse=True)
    edit_year = st.selectbox("Năm học cần cập nhật", options=edit_years,
                             index=edit_years.index(current_year), key="edit_year")

    base = repo.get_profile(edit_year) or repo.latest_profile() or {}
    with st.form(f"edit_profile_{edit_year}"):
        values = profile_fields(f"ed_{edit_year}", base)
        saved = st.form_submit_button("Lưu thông tin", type="primary", use_container_width=True)
    if saved:
        if not values["major"].strip():
            st.warning("Vui lòng nhập ngành học.")
        else:
            repo.save_profile(edit_year, values)
            st.success(f"Đã lưu thông tin cho năm học {edit_year}.")
            st.rerun()

# ---------- Câu nhắn cuối trang ----------
st.markdown(
    '<div class="dream-footer">Đừng bao giờ ngừng theo đuổi ước mơ của mình</div>',
    unsafe_allow_html=True,
)
