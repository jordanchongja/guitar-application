"""
modules/today_page.py

The "today's page" card on the Practice page. A page is one small thing you can actually finish, so
a session has an ending: pick it before you play, finish it, keep the take, and finishing saves the
session so you really can stop there. Whatever isn't finished simply waits for next time. The pages you finish collect on the Sketchbook page.
"""

from __future__ import annotations

import datetime as dt
import re

import streamlit as st

from modules import practice as P
from modules import practice_store as store

_LABEL = ":small[:gray[**TODAY'S PAGE**]]"


def _short(text: str, n: int = 42) -> str:
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def _use_suggestion(options: dict) -> None:
    picked = options.get(st.session_state.get("page_pick"))
    st.session_state.page_title = picked["title"] if picked else ""
    st.session_state.page_src = picked


def _edit_page(page: dict) -> None:
    """Move the plan back into the boxes, keeping what was typed."""
    st.session_state.page_title = page["title"]
    st.session_state.page_goal = page["done_when"]
    st.session_state.page_src = page
    P.clear_next_page()


def commit_typed() -> bool:
    """Whatever's typed in the boxes becomes the plan. False when nothing's typed."""
    title = st.session_state.get("page_title", "").strip()
    if not title:
        return False
    src = st.session_state.get("page_src") or {}
    if src.get("title") != title:   # rewritten into something else: no longer that idea or song
        src = {}
    P.set_next_page(title, st.session_state.get("page_goal", ""), src.get("idea_id", ""), src.get("item_id", ""))
    for key in ("page_title", "page_goal", "page_src", "page_pick"):
        st.session_state.pop(key, None)
    # the page may have tagged a song: the Practice page's tag widgets redraw from the saved list
    st.session_state.chip_ver = st.session_state.get("chip_ver", 0) + 1
    return True


def _picker() -> None:
    st.session_state.setdefault("page_goal", P.DEFAULT_DONE)
    suggestions = P.page_suggestions()
    if suggestions:
        options = {s["key"]: s for s in suggestions}
        icons = {"idea": ":material/lightbulb:", "item": ":material/music_note:"}
        st.pills("Waiting for you", list(options), key="page_pick",
                 format_func=lambda k: f"{icons[k.split(':')[0]]} {_short(options[k]['title'])}",
                 on_change=_use_suggestion, args=(options,))
    st.text_input("One small thing you can finish", key="page_title",
                  placeholder="e.g. First 4 bars of Blackbird")
    st.text_input("Done when", key="page_goal",
                  help="Finishing doesn't mean perfect. Decide what's enough before you play.")


def _show_page(page: dict) -> None:
    st.markdown(_LABEL)
    st.markdown(f"#### {page['title']}")
    st.caption(f":material/flag: Done when: {page['done_when']}")
    item = P.catalog().get(page.get("item_id"), {}).get("row", {})
    bits = [f":material/history: Last time: *{item['next_note']}*" if item.get("next_note") and item["next_note"] not in page["title"] else "",
            f":material/speed: {item['bpm']} bpm" if item.get("bpm") else "",
            f"[Tab]({item['url']})" if item.get("url") else ""]
    if any(bits):
        st.caption(" · ".join(b for b in bits if b))


def render_plan() -> None:
    """Before you play: the page waiting for you, or a quick way to choose one."""
    number = st.session_state.get("just_finished")
    if number:
        with st.container(border=True):
            st.markdown(f"#### :material/check_circle: Page {number} is in your sketchbook")
            st.markdown("Session saved. You can stop here.")
    page = P.next_page()
    with st.container(border=True):
        if page:
            _show_page(page)
            st.button("Change page", icon=":material/edit:", on_click=_edit_page, args=(page,))
            return
        st.markdown(":small[:gray[**NEXT PAGE (OPTIONAL)**]]" if number else _LABEL)
        _picker()
        if st.button("Save for later", icon=":material/bookmark:"):
            if commit_typed():
                st.rerun()
            st.toast("Type what you'd like to finish first.", icon=":material/edit:")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


def _finish(active: dict, page: dict, take) -> int:
    """Save the page and its take. Returns the page's number."""
    link = ""
    failed = None
    if take is not None:
        name = f"page-{store.now():%Y%m%d-%H%M}-{_slug(page['title'])}.wav"
        try:
            with st.spinner("Saving your take..."):
                link = store.upload_recording(take.getvalue(), name)
        except RuntimeError as e:
            # never lose a take: keep it in this browser session to retry or download
            failed = {"name": name, "data": take.getvalue(), "error": str(e)}
    saved = P.finish_page(page, active, link)
    if failed:
        st.session_state.unsaved_take = failed | {"page_id": saved["id"]}
    st.session_state.page_take_ver = st.session_state.get("page_take_ver", 0) + 1
    return saved["number"]


def end_session_now(active: dict) -> None:
    """Save the session from the timer, keeping whatever's tagged. Anything you've now played moves
    on from the wishlist or "not started"."""
    start = dt.datetime.fromisoformat(active["start"])
    live = P.active_session() or active
    minutes = max(1, round(P.elapsed_seconds(live) / 60))
    notes = st.session_state.get("session_notes", live.get("notes", "")).strip()
    cat = P.catalog()
    begun = {"Not started": "Working on", "Wishlist": "Learning"}
    updates = {i: {"status": begun.get(cat[i]["row"].get("status"), ""), "note": "", "bpm": str(live.get("bpm") or "")}
               for i in live.get("items", []) if i in cat}
    P.save_session(start, minutes, updates, notes)


def render_session(active: dict) -> None:
    """While you play: the page and how to finish it."""
    page = P.next_page()
    if not page:
        # stays open after "Change page", so the text you're editing doesn't look lost
        with st.expander(":material/menu_book: Pick a page to finish", expanded="page_title" in st.session_state):
            _picker()
            if st.button("Use this page", type="primary", icon=":material/check:"):
                if commit_typed():
                    st.rerun()
                st.toast("Type what you'd like to finish first.", icon=":material/edit:")
        return
    with st.container(border=True):
        _show_page(page)
        take = st.audio_input("Record your take", key=f"page_take_{st.session_state.get('page_take_ver', 0)}")
        if st.button("Finish page and stop", type="primary", icon=":material/check:", width="stretch"):
            st.session_state.just_finished = _finish(active, page, take)
            end_session_now(active)
            st.rerun()
        c1, c2 = st.columns(2)
        if c1.button("Finish, keep playing", icon=":material/play_arrow:", width="stretch"):
            number = _finish(active, page, take)
            st.toast(f"Page {number} is in your sketchbook", icon=":material/check_circle:")
            st.rerun()
        if c2.button("Change page", icon=":material/edit:", width="stretch"):
            _edit_page(page)
            st.rerun()


def render_ideas() -> None:
    """Everything you've saved, newest first."""
    ideas = P.ideas()
    can_use = P.next_page() is None
    with st.expander(f":material/lightbulb: Ideas ({len(ideas)})"):
        with st.form("add_idea", border=False, clear_on_submit=True):
            c1, c2 = st.columns([5, 1], vertical_alignment="bottom")
            text = c1.text_input("Add an idea", placeholder="That riff at 1:20 in…")
            if c2.form_submit_button("Add", width="stretch") and text.strip():
                P.add_idea(text.strip())
                st.rerun()
        for idea in ideas:
            with st.container(horizontal=True, vertical_alignment="center"):
                st.markdown(f"{idea['text']}  \n:gray[:small[{P.ago(idea['added'])}]]", width="stretch")
                if can_use and st.button("Use", key=f"use_{idea['id']}"):
                    P.use_idea(idea)
                    st.rerun()
                if st.button("Drop", key=f"drop_{idea['id']}"):
                    P.drop_idea(idea["id"])
                    st.rerun()


def render_unsaved_take() -> None:
    t = st.session_state.get("unsaved_take")
    if not t:
        return
    with st.container(border=True):
        st.warning(f"Your practice was saved, but the recording couldn't be uploaded: {t['error']}",
                   icon=":material/mic_off:")
        c1, c2, c3 = st.columns(3)
        if c1.button("Try again", type="primary", icon=":material/refresh:", width="stretch"):
            try:
                with st.spinner("Saving your take..."):
                    P.set_page_take(t["page_id"], store.upload_recording(t["data"], t["name"]))
            except RuntimeError as e:
                t["error"] = str(e)
                st.rerun()
            del st.session_state.unsaved_take
            st.toast("Take saved", icon=":material/check_circle:")
            st.rerun()
        c2.download_button("Download", t["data"], t["name"], "audio/wav", icon=":material/download:", width="stretch")
        if c3.button("Dismiss", width="stretch"):
            del st.session_state.unsaved_take
            st.rerun()
