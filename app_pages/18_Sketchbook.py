"""
app_pages/18_Sketchbook.py

Every page you've finished, like flipping back through a sketchbook. No reviewing needed: they just
pile up. The first and latest takes sit together at the top for when you fancy comparing them.
"""

import datetime as dt
from pathlib import Path

import streamlit as st

from modules import practice as P
from modules import practice_store as store
from modules.settings import render_sidebar_settings

st.set_page_config(page_title="Sketchbook", page_icon=":material/auto_stories:", layout="centered")
render_sidebar_settings()

st.title("Sketchbook")

if not store.password_gate():
    st.stop()

pages = P.finished_pages()
if not pages:
    st.info("No pages yet. Finish one small thing on the **Practice** page and it lands here.",
            icon=":material/auto_stories:")
    st.page_link("app_pages/0_Practice.py", label="Go to Practice", icon=":material/timer:")
    st.stop()


def plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def listen(page: dict) -> None:
    take = page["take"]
    if take.startswith("http"):
        st.link_button("Listen", take, icon=":material/play_arrow:")
    elif take and Path(take).exists():
        st.audio(take)


takes = [p for p in pages if p["take"]]
st.caption(f"{plural(len(pages), 'page')} · {plural(len(takes), 'take')}")

if len(takes) >= 2:
    with st.container(border=True):
        st.markdown("**Then and now**")
        for name, page in (("First take", takes[-1]), ("Latest take", takes[0])):
            with st.container(horizontal=True, vertical_alignment="center"):
                st.markdown(f":gray[{name}]  \n{page['title']}", width="stretch")
                listen(page)

month = None
for page in pages:
    day = dt.date.fromisoformat(page["finished"][:10])
    if f"{day:%B %Y}" != month:
        month = f"{day:%B %Y}"
        st.subheader(month)
    with st.container(border=True, horizontal=True, vertical_alignment="center"):
        st.markdown(f"**{page['title']}**  \n:gray[:small[{day.day} {day:%b}]]", width="stretch")
        listen(page)

with st.expander(":material/edit_note: Remove a page"):
    st.caption("For anything logged by mistake. A bad take is still a page, so it can stay. "
               "Recordings stay in your Drive folder.")
    for page in pages[:15]:
        with st.container(horizontal=True, vertical_alignment="center"):
            st.markdown(f"{page['title']}  \n:gray[:small[{page['finished'][:10]}]]", width="stretch")
            if st.session_state.get("confirm_remove") == page["id"]:
                if st.button("Confirm", key=f"yes_{page['id']}", type="primary", icon=":material/delete:"):
                    P.delete_page(page["id"])
                    st.session_state.pop("confirm_remove", None)
                    st.rerun()
                if st.button("Keep", key=f"no_{page['id']}"):
                    st.session_state.pop("confirm_remove", None)
                    st.rerun()
            elif st.button("Remove", key=f"del_{page['id']}", icon=":material/delete:"):
                st.session_state.confirm_remove = page["id"]
                st.rerun()
