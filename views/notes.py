import streamlit as st

from core import repo
from core.theme import page_heading

page_heading(
    "GHI CHÚ",
    "Ghi chú quan trọng",
    "Lưu những điều cần nhớ, đường link tham khảo và ảnh minh họa. Ghi chú quan trọng luôn được ghim lên đầu.",
)

IMAGE_TYPES = ["png", "jpg", "jpeg", "webp", "gif"]


def _links_to_text(links: list[dict]) -> str:
    lines = []
    for link in links:
        if link["label"] and link["label"] != link["url"]:
            lines.append(f"{link['label']} | {link['url']}")
        else:
            lines.append(link["url"])
    return "\n".join(lines)


def _save_new_images(files) -> tuple[list[str], list[str]]:
    saved, errors = [], []
    for f in files or []:
        try:
            saved.append(repo.save_image(f.name, f.getvalue()))
        except ValueError as exc:
            errors.append(f"{f.name}: {exc}")
    return saved, errors


# ---------- Tạo ghi chú mới ----------
with st.expander("➕ Ghi chú mới", expanded=False):
    with st.form("new_note_form", clear_on_submit=True):
        title = st.text_input("Tiêu đề", placeholder="VD: Hạn nộp học bổng")
        body = st.text_area(
            "Nội dung",
            height=150,
            placeholder="Viết tự do. Có thể dùng Markdown, ví dụ **in đậm**, - gạch đầu dòng.",
        )
        important = st.checkbox("⭐ Đánh dấu quan trọng")
        links_text = st.text_area(
            "Liên kết (mỗi dòng một link, có thể đặt tên: Tên hiển thị | https://...)",
            height=90,
            placeholder="Học bổng ABC | https://example.com\nhttps://vnexpress.net",
        )
        files = st.file_uploader("Ảnh đính kèm (tối đa 5 MB mỗi ảnh)", type=IMAGE_TYPES,
                                 accept_multiple_files=True)
        submitted = st.form_submit_button("Lưu ghi chú", type="primary", use_container_width=True)

    if submitted:
        if not title.strip():
            st.warning("Vui lòng nhập tiêu đề.")
        else:
            images, errors = _save_new_images(files)
            for err in errors:
                st.error(err)
            repo.create_note(title, body, important, repo.parse_links(links_text), images)
            st.toast("Đã lưu ghi chú.")
            st.rerun()

# ---------- Tìm kiếm & lọc ----------
col_search, col_filter = st.columns([3, 1], vertical_alignment="center")
with col_search:
    search = st.text_input("Tìm trong ghi chú", placeholder="Nhập từ khóa...", label_visibility="collapsed")
with col_filter:
    only_important = st.toggle("Chỉ quan trọng")

notes = repo.list_notes(search=search, important_only=only_important)
st.caption(f"{len(notes)} ghi chú")

if not notes:
    with st.container(border=True):
        st.info("Chưa có ghi chú nào phù hợp.")

for note in notes:
    with st.container(border=True):
        badge = '<span class="important-badge">⭐ Quan trọng</span>' if note["important"] else ""
        st.markdown(f"#### {note['title']}{badge}", unsafe_allow_html=True)
        st.caption(f"Cập nhật: {note['updated_at'] or note['created_at'] or ''}")

        if note["body"]:
            st.markdown(note["body"])

        if note["links"]:
            for link in note["links"]:
                st.markdown(f"🔗 [{link['label']}]({link['url']})")

        if note["images"]:
            loaded = [(name, repo.image_bytes(name)) for name in note["images"]]
            loaded = [(name, data) for name, data in loaded if data]
            for start in range(0, len(loaded), 3):
                cols = st.columns(3)
                for col, (_, data) in zip(cols, loaded[start:start + 3]):
                    with col:
                        st.image(data, use_container_width=True)

        with st.expander("✏️ Sửa ghi chú"):
            nid = note["id"]
            with st.form(f"edit_note_{nid}"):
                e_title = st.text_input("Tiêu đề", value=note["title"], key=f"e_title_{nid}")
                e_body = st.text_area("Nội dung", value=note["body"], height=130, key=f"e_body_{nid}")
                e_important = st.checkbox("⭐ Quan trọng", value=note["important"], key=f"e_imp_{nid}")
                e_links = st.text_area("Liên kết (mỗi dòng: Tên | link)", value=_links_to_text(note["links"]),
                                       height=90, key=f"e_links_{nid}")
                keep_options = list(note["images"])
                keep = st.multiselect(
                    "Ảnh giữ lại (bỏ chọn để xóa ảnh)",
                    options=keep_options,
                    default=keep_options,
                    format_func=lambda n, opts=keep_options: f"Ảnh {opts.index(n) + 1}",
                    key=f"e_keep_{nid}",
                )
                new_files = st.file_uploader("Thêm ảnh", type=IMAGE_TYPES, accept_multiple_files=True,
                                             key=f"e_files_{nid}")
                save = st.form_submit_button("Lưu thay đổi", type="primary", use_container_width=True)

            if save:
                if not e_title.strip():
                    st.warning("Tiêu đề không được để trống.")
                else:
                    for name in keep_options:
                        if name not in keep:
                            repo.delete_image_file(name)
                    added, errors = _save_new_images(new_files)
                    for err in errors:
                        st.error(err)
                    repo.update_note(
                        nid, e_title, e_body, e_important,
                        repo.parse_links(e_links), list(keep) + added,
                    )
                    st.toast("Đã cập nhật ghi chú.")
                    st.rerun()

            if st.button("🗑 Xóa ghi chú", key=f"del_note_{nid}"):
                repo.delete_note(nid)
                st.toast("Đã xóa ghi chú.")
                st.rerun()
