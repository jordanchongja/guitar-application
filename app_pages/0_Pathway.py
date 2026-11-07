"""
app_pages/0_Pathway.py

The map of things worth learning, by branch. Pick whatever you feel like; the map just shows where
you are, what's ready to start, and what's getting rusty. Songs live here too.
"""

import datetime as dt

import pandas as pd
import streamlit as st

from modules import practice as P
from modules import practice_store as store
from modules.pathway_seed import BRANCH_ICONS, BRANCHES, SONG_STATUSES, STATUSES
from modules.settings import render_sidebar_settings

st.set_page_config(page_title="Pathway", page_icon=":material/route:", layout="centered")
render_sidebar_settings()

st.title("Pathway")
st.caption("A map, not a plan. Pick anything that looks fun; the map keeps track of where you are.")

if not store.password_gate():
    st.stop()

STATUS_BADGE = {"Not started": ("gray", ""), "Working on": ("orange", ":material/construction:"),
                "Comfortable": ("blue", ":material/thumb_up:"), "Solid": ("green", ":material/check_circle:"),
                "Wishlist": ("gray", ""), "Learning": ("orange", ":material/construction:"),
                "Polishing": ("violet", ":material/auto_fix_high:"), "Learned": ("green", ":material/check_circle:"),
                "Paused": ("gray", ":material/pause:")}


def next_song_number(songs: list[dict]) -> int:
    nums = [int(s["id"][4:]) for s in songs if s["id"].startswith("song") and s["id"][4:].isdigit()]
    return max(nums + [0]) + 1


def badge(status: str) -> str:
    color, icon = STATUS_BADGE.get(status, ("gray", ""))
    return f":{color}-badge[{icon} {status}]" if icon else f":{color}-badge[{status}]"


rows = P.pathway()
song_rows = P.songs()
ready = P.ready_to_start(rows)
rusty_ids = {r["id"] for r in P.rusty()}

# ---------------------------------------------------------------- overview strip
done = sum(r["status"] in ("Comfortable", "Solid") for r in rows)
working = sum(r["status"] == "Working on" for r in rows)
with st.container(horizontal=True):
    st.metric("Comfortable or solid", f"{done} / {len(rows)}", border=True)
    st.metric("Working on", working, border=True)
    st.metric("Songs learned", sum(s["status"] == "Learned" for s in song_rows), border=True)

with st.expander(":material/school: How to practise (what the research says)"):
    st.markdown(
        "- **Mix it up.** Touching 2-3 different areas in a session (a scale, a song, some rhythm) tends to "
        "stick better long-term than drilling one thing for an hour, even if it feels less smooth at the time.\n"
        "- **Come back after a gap.** Revisiting things days later beats cramming. That's what *getting rusty* is for.\n"
        "- **Slow and clean, then faster.** For anything with a metronome, nudge the tempo up ~4 bpm once "
        "it's clean 3 times in a row, and log the bpm.\n"
        "- **Isolate the hard bit.** Loop the 1-2 bars that trip you up instead of replaying the parts you know.\n"
        "- **Record yourself.** You can't hear timing and tone properly while playing; a 30-second take shows you.\n"
        "- **Short and often** beats long and rare, especially for barre chords and ear training.")

branch = st.segmented_control("Branch", BRANCHES + ["Songs"], default="Fretboard",
                              format_func=lambda b: f"{BRANCH_ICONS.get(b, ':material/music_note:')} {b}",
                              label_visibility="collapsed") or "Fretboard"
edit = st.toggle("Edit", help="Change statuses and notes, rename, reorder, add or delete items")

# ---------------------------------------------------------------- songs
if branch == "Songs":
    with st.expander(":material/add: Add a song", expanded=not song_rows):
        with st.form("add_song", clear_on_submit=True):
            title = st.text_input("Title")
            c1, c2 = st.columns(2)
            artist = c1.text_input("Artist")
            status = c2.selectbox("Status", SONG_STATUSES, index=1)
            url = st.text_input("Tab link (Ultimate Guitar etc.)")
            c3, c4 = st.columns(2)
            key = c3.text_input("Key")
            capo = c4.text_input("Capo")
            if not title.strip() and "ultimate-guitar.com" in url:
                title, artist = P.parse_song_link(url)[0], artist or P.parse_song_link(url)[1]
            st.caption("Tip: paste an Ultimate Guitar link and leave the title empty: it's filled in for you.")
            if st.form_submit_button("Add song", type="primary") and title.strip():
                n = next_song_number(song_rows)
                store.append("songs", {"id": f"song{n}", "title": title.strip(), "artist": artist.strip(),
                                       "url": url.strip(), "key": key.strip(), "capo": capo.strip(),
                                       "status": status, "added": store.now().date().isoformat()})
                st.rerun()

    if edit and song_rows:
        df = pd.DataFrame(song_rows)
        out = st.data_editor(
            df[["title", "artist", "status", "next_note", "bpm", "key", "capo", "url", "last_practiced", "id", "added"]],
            hide_index=True, num_rows="dynamic", key="songs_editor",
            column_config={"status": st.column_config.SelectboxColumn(options=SONG_STATUSES, required=True),
                           "url": st.column_config.LinkColumn("tab"),
                           "id": None, "added": None, "last_practiced": st.column_config.TextColumn(disabled=True),
                           "next_note": st.column_config.TextColumn("next time", width="large")})
        if st.button("Save songs", type="primary", icon=":material/save:"):
            recs = out.fillna("").to_dict("records")
            n = next_song_number(song_rows) - 1
            for r in recs:
                if not r.get("id"):
                    n += 1
                    r["id"], r["added"] = f"song{n}", store.now().date().isoformat()
            store.write_all("songs", [r for r in recs if str(r.get("title", "")).strip()])
            st.toast("Saved", icon=":material/check_circle:")
            st.rerun()
    else:
        order = {s: i for i, s in enumerate(["Learning", "Polishing", "Wishlist", "Learned", "Paused"])}
        for s in sorted(song_rows, key=lambda s: (order.get(s["status"], 9), s["title"])):
            with st.container(border=True):
                head = f"**{s['title']}**" + (f" · {s['artist']}" if s["artist"] else "")
                st.markdown(f"{head}  {badge(s['status'])}" + ("  :red-badge[rusty]" if s["id"] in rusty_ids else ""))
                bits = [x for x in [f"key {s['key']}" if s["key"] else "", f"capo {s['capo']}" if s["capo"] else "",
                                    f"{s['bpm']} bpm" if s["bpm"] else "", P.ago(s["last_practiced"])
                                    if s["last_practiced"] else ""] if x]
                if bits:
                    st.caption(" · ".join(bits))
                if s["next_note"]:
                    st.markdown(f":material/flag: *{s['next_note']}*")
                tempo = P.tempo_history(s["id"])
                if len(tempo) >= 2:
                    st.markdown(f":material/trending_up: **Tempo** {' → '.join(str(b) for _, b in tempo)} bpm")
                if s["url"]:
                    st.markdown(f"[Open tab]({s['url']})")
    st.stop()

# ---------------------------------------------------------------- a branch
items = [r for r in rows if r["branch"] == branch]

if edit:
    df = pd.DataFrame(items)
    out = st.data_editor(
        df[["order", "name", "status", "next_note", "bpm", "goal", "how", "last_practiced", "id", "branch", "tool"]],
        hide_index=True, num_rows="dynamic", key=f"edit_{branch}",
        column_config={"order": st.column_config.NumberColumn(width="small"),
                       "status": st.column_config.SelectboxColumn(options=STATUSES, required=True),
                       "next_note": st.column_config.TextColumn("next time", width="large"),
                       "goal": st.column_config.TextColumn("done when", width="large"),
                       "last_practiced": st.column_config.TextColumn(disabled=True),
                       "id": None, "branch": None, "tool": None})
    if st.button("Save changes", type="primary", icon=":material/save:"):
        recs = out.fillna("").to_dict("records")
        prefix = "x"
        for r in recs:
            r["branch"] = branch
            if not r.get("id"):
                r["id"] = f"{prefix}{dt.datetime.now():%y%m%d%H%M%S%f}"[:16]
                r["status"] = r.get("status") or "Not started"
        keep = [r for r in rows if r["branch"] != branch] + [r for r in recs if str(r.get("name", "")).strip()]
        store.write_all("pathway", keep)
        st.toast("Saved", icon=":material/check_circle:")
        st.rerun()
    st.stop()

for r in items:
    with st.container(border=True):
        tags = [badge(r["status"])]
        if r["id"] in ready:
            tags.append(":green-badge[:material/arrow_forward: ready to start]")
        if r["id"] in rusty_ids:
            tags.append(":red-badge[rusty]")
        st.markdown(f"**{r['name']}**  " + " ".join(tags))
        if r["goal"]:
            st.markdown(f":material/target: {r['goal']}")
        if r["how"]:
            st.caption(f":material/tips_and_updates: {r['how']}")
        tempo = P.tempo_history(r["id"])
        if len(tempo) >= 2:
            st.markdown(f":material/trending_up: **Tempo** {' → '.join(str(b) for _, b in tempo)} bpm "
                        f":gray[since {tempo[0][0]}]")
        meta = [x for x in [f"{r['bpm']} bpm" if r["bpm"] else "",
                            f"last practised {P.ago(r['last_practiced'])}" if r["last_practiced"] else ""] if x]
        if r["next_note"] or meta:
            st.caption(" · ".join(([f":material/flag: *{r['next_note']}*"] if r["next_note"] else []) + meta))
        if r["tool"]:
            try:
                st.page_link(r["tool"], label="Open the tool for this", icon=":material/open_in_new:")
            except Exception:
                pass
