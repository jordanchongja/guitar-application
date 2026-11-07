"""
modules/practice_panel.py

The floating Practice button shown in the corner of every page except Practice itself. It keeps
your current work one tap away (songs and skills in progress, wishlist) and lets you start, pause,
jot notes on a session and run the metronome without leaving the page you're on. Ending a session, recordings and
history stay on the Practice page.
"""

from __future__ import annotations

import streamlit as st

from modules import practice as P
from modules import practice_store as store
from modules.metronome import render_metronome

_CSS = """
<style>
/* bottom: sits above Streamlit Cloud's "Manage app" button, which takes that corner */
.st-key-practice_fab { position: fixed; right: 1.25rem; bottom: 4.5rem; width: auto; z-index: 999990; }
.st-key-practice_fab button { border-radius: 999px; box-shadow: 0 4px 14px rgba(0, 0, 0, .3); }
[data-testid="stPopoverBody"]:has(.st-key-practice_panel) {
    width: min(23rem, calc(100vw - 2rem));
    max-height: min(36rem, calc(100vh - 9rem));
    overflow-y: auto;
}
</style>
"""


def _toggle_tag(item_id: str) -> None:
    s = P.active_session()
    if s is None:
        return
    items = list(s.get("items", []))
    P.set_active_items([i for i in items if i != item_id] if item_id in items else items + [item_id])
    # the Practice page's tag widgets redraw from the saved list when this changes
    st.session_state.chip_ver = st.session_state.get("chip_ver", 0) + 1


def _save_notes() -> None:
    text = st.session_state.panel_notes.strip()
    P.set_active_notes(text)
    st.session_state.panel_notes_seen = text


def _details(r: dict) -> str:
    bits = [P.ago(r["last_practiced"]) if r["last_practiced"] else "",
            f"{r['bpm']} bpm" if r.get("bpm") else "",
            f":material/flag: *{r['next_note']}*" if r.get("next_note") else "",
            f"[Tab]({r['url']})" if r.get("url") else ""]
    return " · ".join(b for b in bits if b)


def render_current_work(active: dict | None = None) -> None:
    """Songs and skills in progress, then the wishlist. Pass the running session to get a tick box
    per item for tagging it."""
    work = P.in_progress()
    wish = P.wishlist()
    groups = [("Songs", [r for r in work if r["_kind"] == "Song"]),
              ("Skills", [r for r in work if r["_kind"] != "Song"]),
              ("Wishlist songs", wish)]
    ver = st.session_state.get("chip_ver", 0)
    tagged = active.get("items", []) if active else []
    for title, rows in groups:
        if not rows:
            continue
        st.markdown(f":small[:gray[**{title.upper()}**]]")
        for r in rows:
            with st.container(gap=None):     # keeps the details tight under their own title
                if active:
                    st.checkbox(f"**{r['_label']}**", value=r["id"] in tagged, key=f"panel_tag_{ver}_{r['id']}",
                                on_change=_toggle_tag, args=(r["id"],))
                else:
                    st.markdown(f"**{r['_label']}**")
                sub = _details(r)
                if sub:
                    st.caption(sub)
    if not (work or wish):
        st.caption("Nothing in progress yet. Pick something from the Pathway page.")
    other = len(set(tagged) - {r["id"] for r in work + wish})
    if other:
        st.caption(f"Plus {other} more tagged on the Practice page.")


def _session_controls(active: dict) -> None:
    paused = bool(active.get("paused_at"))
    with st.container(horizontal=True, vertical_alignment="center"):
        if paused:
            st.metric(":material/pause_circle: Paused", P.fmt_clock(P.elapsed_seconds(active)))
            st.button("Resume", type="primary", icon=":material/play_arrow:",
                      on_click=P.resume_session)
        else:
            @st.fragment(run_every="1s")
            def clock():
                st.metric("Practising", P.fmt_clock(P.elapsed_seconds(active)))

            clock()
            st.button("Pause", icon=":material/pause:", on_click=P.pause_session)

    # Notes can also change on the Practice page, and Streamlit drops this box's value whenever the
    # panel closes or you change page: reload it from the saved session in both cases.
    saved = active.get("notes", "")
    if "panel_notes" not in st.session_state or st.session_state.get("panel_notes_seen") != saved:
        st.session_state.panel_notes = saved
        st.session_state.panel_notes_seen = saved
    st.text_area("What are you practising?", key="panel_notes", height=90, on_change=_save_notes,
                 placeholder="Saved when you tap away from the box.")


@st.fragment
def _floating_button() -> None:
    try:
        active = P.active_session()
    except Exception:   # an optional extra: if the Sheet can't be reached, the page shows without it
        return
    with st.container(key="practice_fab", horizontal=True, vertical_alignment="center", gap="small"):
        if active:     # beside the button, not in its label: a new label would close the open panel
            paused = active.get("paused_at")
            st.badge("Paused" if paused else "Practising", color="gray" if paused else "green",
                     icon=":material/pause:" if paused else ":material/graphic_eq:")
        popover = st.popover("Practice", icon=":material/music_note:", type="primary", on_change="rerun")
    if not popover.open:   # keeps closed-panel page loads free of extra Sheet reads
        return
    with popover, st.container(key="practice_panel"):
        if active:
            _session_controls(active)
        else:
            st.button("Start practising", type="primary", icon=":material/play_arrow:", width="stretch",
                      on_click=P.start_session)
        st.markdown("**Metronome**")
        render_metronome("panel_metronome", active.get("bpm") if active else None)
        render_current_work(active)
        with st.container(horizontal=True):
            st.page_link("app_pages/0_Practice.py", label="End session" if active else "Practice page",
                         icon=":material/stop_circle:" if active else ":material/timer:")
            st.page_link("app_pages/0_Pathway.py", label="Pathway", icon=":material/route:")


def render_floating_practice() -> None:
    """Draw the corner button. Hidden while logging is locked."""
    if store.unlocked():
        st.html(_CSS)
        _floating_button()
