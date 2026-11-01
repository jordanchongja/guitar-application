"""
pages/0_Practice.py

Start a session, play whatever you feel like, tap what you touched, end it, and leave a note for
next time. The timer survives the phone locking or the app sleeping: the start time is saved the
moment you press Start and elapsed time is always computed from it.
"""

import datetime as dt

import streamlit as st

from modules import practice as P
from modules import practice_store as store
from modules.pathway_seed import BRANCH_ICONS, SONG_STATUSES, STATUSES
from modules.settings import render_sidebar_settings

st.set_page_config(page_title="Practice", page_icon=":material/timer:", layout="centered")
render_sidebar_settings()

st.title("Practice")

if not store.password_gate():
    st.caption("Everything else in the app works without a password.")
    st.stop()

cat = P.catalog()
active = P.active_session()


def label(item_id: str) -> str:
    c = cat.get(item_id)
    if not c:
        return item_id
    icon = ":material/music_note:" if c["kind"] == "Song" else BRANCH_ICONS.get(c["kind"], "")
    return f"{icon} {c['label']}"


def fmt_minutes(m: float) -> str:
    m = int(round(m))
    return f"{m // 60}h {m % 60:02d}m" if m >= 60 else f"{m} min"


# ============================================================================ running session
if active:
    start = dt.datetime.fromisoformat(active["start"])

    @st.fragment(run_every="1s")
    def clock():
        secs = int((store.now() - start).total_seconds())
        h, rem = divmod(max(secs, 0), 3600)
        m, s = divmod(rem, 60)
        with st.container(border=True, horizontal=True, vertical_alignment="center"):
            st.metric("Practising", f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}",
                      help=f"Started {start:%H:%M}")

    clock()

    # what are you working on? quick chips: in-progress things + whatever you already picked
    picked = list(active.get("items", []))
    quick = [r["id"] for r in P.in_progress()][:12]
    options = list(dict.fromkeys(picked + quick))
    st.markdown("**What are you working on?** Tap everything you touch.")
    chosen = st.pills("Items", options, selection_mode="multi", default=picked, format_func=label,
                      key="chips", label_visibility="collapsed") if options else []
    others = [i for i in cat if i not in options]
    extra = st.selectbox("Something else", others, index=None, format_func=label,
                         placeholder="Add something else (search)…")
    chosen = list(dict.fromkeys(list(chosen or []) + ([extra] if extra else [])))
    if chosen != picked:
        P.set_active_items(chosen)
        st.rerun()

    for i in chosen:
        row = cat[i]["row"]
        bits = []
        if row.get("next_note"):
            bits.append(f":material/flag: Last time: *{row['next_note']}*")
        if row.get("bpm"):
            bits.append(f":material/speed: {row['bpm']} bpm")
        if row.get("goal"):
            bits.append(f":material/target: {row['goal']}")
        if row.get("url"):
            bits.append(f"[Tab]({row['url']})")
        if bits:
            st.caption(f"**{cat[i]['label']}** · " + " · ".join(bits))

    st.space("small")
    with st.expander(":material/stop_circle: End session", expanded=False):
        with st.form("end_session"):
            elapsed = max(1, round((store.now() - start).total_seconds() / 60))
            minutes = st.number_input("Minutes", 1, 600, int(elapsed), help="Adjust if you forgot to stop the timer")
            updates = {}
            for i in chosen:
                c = cat[i]
                is_song = c["kind"] == "Song"
                statuses = SONG_STATUSES if is_song else STATUSES
                cur = c["row"].get("status") or statuses[0]
                default = cur
                if not is_song and cur == "Not started":
                    default = "Working on"
                if is_song and cur == "Wishlist":
                    default = "Learning"
                st.markdown(f"**{c['label']}**")
                col1, col2 = st.columns([2, 1])
                status = col1.selectbox("Status", statuses, index=statuses.index(default), key=f"st_{i}",
                                        label_visibility="collapsed")
                bpm = col2.text_input("bpm", value=c["row"].get("bpm", ""), key=f"bpm_{i}",
                                      placeholder="bpm", label_visibility="collapsed")
                note = st.text_input("Next time", key=f"note_{i}",
                                     placeholder="Next time: e.g. bridge bars 17–24 at 60 bpm")
                updates[i] = {"status": status, "note": note.strip(), "bpm": bpm.strip()}
            notes = st.text_area("Session notes (optional)", height=80)
            take = st.audio_input("Record a take (optional)")
            col_a, col_b = st.columns(2)
            save = col_a.form_submit_button("Save session", type="primary", icon=":material/check:",
                                            width="stretch")
            discard = col_b.form_submit_button("Discard", icon=":material/delete:", width="stretch")
        if save:
            if not updates:
                updates = {}
            rec_link = ""
            if take is not None:
                try:
                    rec_link = store.upload_recording(take.getvalue(), f"take-{start:%Y%m%d-%H%M}.wav")
                except RuntimeError as e:
                    st.warning(f"{e} The session is still saved.")
            P.save_session(start, int(minutes), updates, notes.strip(), rec_link)
            st.toast(f"Saved {fmt_minutes(minutes)} of practice", icon=":material/check_circle:")
            st.rerun()
        if discard:
            P.cancel_session()
            st.rerun()
    st.stop()


# ============================================================================ not practising
if st.button("Start practising", type="primary", icon=":material/play_arrow:", width="stretch"):
    P.start_session()
    st.rerun()

sess = P.sessions()
items = P.session_items()

# --- where you left off
if sess:
    last = sess[0]
    last_items = [r for r in items if r["session_id"] == last["id"]]
    with st.container(border=True):
        st.markdown(f"**Last time** · {P.ago(last['start'])} · {fmt_minutes(float(last['minutes'] or 0))}")
        for r in last_items:
            row = cat.get(r["item_id"], {}).get("row", {})
            nxt = r["note"] or row.get("next_note", "")
            st.markdown(f"- {label(r['item_id'])}" + (f"  \n  :material/flag: *{nxt}*" if nxt else ""))
        if last.get("notes"):
            st.caption(last["notes"])
        if last.get("recording"):
            st.markdown(f":material/mic: [Your last recording]({last['recording']})"
                        if last["recording"].startswith("http") else f":material/mic: {last['recording']}")
else:
    st.info("No sessions yet. Press **Start practising**, play whatever you feel like, "
            "and tap what you worked on. Browse the **Pathway** page for ideas.", icon=":material/lightbulb:")

# --- what's in progress / getting rusty
prog = P.in_progress()
if prog:
    st.subheader("In progress")
    for r in prog[:8]:
        sub = " · ".join(x for x in [P.ago(r["last_practiced"]),
                                     f"{r['bpm']} bpm" if r.get("bpm") else "",
                                     f"*{r['next_note']}*" if r.get("next_note") else ""] if x)
        st.markdown(f"{label(r['id'])}  \n:gray[{sub}]")

rust = P.rusty()
if rust:
    st.subheader("Getting rusty")
    st.caption("Coming back to things after a gap is one of the best ways to make them stick.")
    st.markdown("  \n".join(f"{label(r['id'])} :gray[· {r['_days']} days]" for r in rust[:6]))

# --- balance + numbers
if sess:
    st.subheader("Last 30 days")
    days = [s["start"][:10] for s in sess]
    month_cut = (store.now().date() - dt.timedelta(days=30)).isoformat()
    week_cut = (store.now().date() - dt.timedelta(days=7)).isoformat()
    with st.container(horizontal=True):
        st.metric("This week", fmt_minutes(sum(float(s["minutes"] or 0) for s in sess if s["start"][:10] >= week_cut)),
                  border=True)
        st.metric("30 days", fmt_minutes(sum(float(s["minutes"] or 0) for s in sess if s["start"][:10] >= month_cut)),
                  border=True)
        st.metric("Streak", f"{P.streak(days)} day" + ("" if P.streak(days) == 1 else "s"), border=True)
    split = P.minutes_by_kind(30)
    if split:
        import pandas as pd
        df = pd.DataFrame({"Area": list(split), "Minutes": list(split.values())}).sort_values("Minutes")
        st.bar_chart(df, x="Area", y="Minutes", horizontal=True, height=220)
        untouched = [b for b in BRANCH_ICONS if b not in split]
        if untouched:
            st.caption("Not touched in 30 days: " + ", ".join(untouched)
                       + ". Mixing a couple of areas per session tends to help things stick.")

with st.expander("Forgot to start the timer? Log a past session"):
    with st.form("past"):
        day = st.date_input("Day", store.now().date())
        mins = st.number_input("Minutes", 1, 600, 20)
        what = st.multiselect("What did you work on?", list(cat), format_func=label)
        note = st.text_input("Note (optional)")
        if st.form_submit_button("Log it"):
            start = dt.datetime.combine(day, dt.time(12, 0))
            P.save_session(start, int(mins), {i: {"status": "", "note": ""} for i in what}, note)
            st.toast("Logged", icon=":material/check_circle:")
            st.rerun()
