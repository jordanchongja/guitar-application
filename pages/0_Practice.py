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
from modules.practice_panel import render_current_work
from modules.settings import render_sidebar_settings

st.set_page_config(page_title="Practice", page_icon=":material/timer:", layout="centered")
render_sidebar_settings(floating_practice=False)

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
    paused = bool(active.get("paused_at"))

    with st.container(border=True, horizontal=True, vertical_alignment="center"):
        if paused:   # frozen clock, no need to tick
            st.metric(":material/pause_circle: Paused", P.fmt_clock(P.elapsed_seconds(active)),
                      help=f"Started {start:%H:%M}. Paused time isn't counted.")
        else:
            @st.fragment(run_every="1s")
            def clock():
                st.metric("Practising", P.fmt_clock(P.elapsed_seconds(active)), help=f"Started {start:%H:%M}")

            clock()
        if paused:
            if st.button("Resume", type="primary", icon=":material/play_arrow:"):
                P.resume_session()
                st.rerun()
        elif st.button("Pause", icon=":material/pause:"):
            P.pause_session()
            st.rerun()

    # What you practised, in your own words: the main log. Saved as you go (when you tap away
    # from the box), so it survives the phone sleeping just like the timer.
    st.text_area(
        "What are you practising?",
        value=active.get("notes", ""),
        key="session_notes",
        height=130,
        placeholder="e.g. Everything chorus solo, slides still sloppy. 10 min minor pentatonic box 1 "
                    "at 70 bpm. Noodled over a blues backing track.",
        on_change=lambda: P.set_active_notes(st.session_state.session_notes.strip()),
    )

    picked = list(active.get("items", []))
    ver = st.session_state.setdefault("chip_ver", 0)   # bumped on every change -> fresh widgets
    song_ids = [i for i, c in cat.items() if c["kind"] == "Song"]
    picked_songs = [i for i in picked if i in song_ids]
    picked_map = [i for i in picked if i not in song_ids]
    # what each widget started with this version (so external changes aren't read as deselections);
    # tied to this session so a new one doesn't inherit the last session's tags
    init_songs = st.session_state.setdefault(f"init_songs_{active['start']}_{ver}", picked_songs)
    init_map = st.session_state.setdefault(f"init_map_{active['start']}_{ver}", picked_map)

    # --- Songs: pick ones you've played before; add new ones with a song + artist field below
    sel_songs = st.multiselect(
        "Songs", song_ids, default=[i for i in init_songs if i in song_ids], format_func=lambda i: cat[i]["label"],
        key=f"songs_{ver}", placeholder="Pick a song you've played before…" if song_ids else "No songs yet: add one below")
    new_song_ids = list(sel_songs)

    with st.form(f"new_song_{ver}", border=False):     # new keys after each add -> empty boxes
        c1, c2, c3 = st.columns([5, 4, 2], vertical_alignment="bottom")
        new_title = c1.text_input("New song", placeholder="Song (or paste an Ultimate Guitar link)",
                                  key=f"new_title_{ver}")
        new_artist = c2.text_input("Artist", placeholder="Artist", key=f"new_artist_{ver}")
        if c3.form_submit_button("Add", icon=":material/add:", width="stretch") and new_title.strip():
            is_link = "ultimate-guitar.com" in new_title
            title, artist = P.parse_song_link(new_title) if is_link else (new_title.strip(), "")
            sid = P.add_song(title or new_title.strip(), new_artist.strip() or artist,
                             new_title.strip() if is_link else "")
            P.set_active_items(list(dict.fromkeys(picked + [sid])))
            st.session_state.chip_ver = ver + 1
            st.rerun()

    # --- Map items: optional tags (give per-item "next time" notes, tempo history, rusty tracking)
    st.markdown("**Tag skills from your map** :gray[(optional)]")
    quick = [r["id"] for r in P.in_progress() if r["id"] not in song_ids][:10]
    if len(quick) < 4:   # fresh map: suggest the first ready-to-start item in each branch
        rows = P.pathway()
        ready = P.ready_to_start(rows)
        firsts = {}
        for r in rows:
            if r["id"] in ready and r["branch"] not in firsts:
                firsts[r["branch"]] = r["id"]
        quick += [i for i in firsts.values() if i not in quick]
    top = list(dict.fromkeys(init_map + picked_map + quick))
    sel_top = st.pills("Suggestions", top, selection_mode="multi", default=init_map, format_func=label,
                       key=f"chips_top_{ver}", label_visibility="collapsed")
    area = st.segmented_control("Browse an area", list(BRANCH_ICONS), key="browse_area",
                                format_func=lambda b: f"{BRANCH_ICONS[b]} {b}")
    sel_area = []
    if area:
        in_area = [i for i, c in cat.items() if c["kind"] == area and i not in top]
        if in_area:
            sel_area = st.pills("In this area", in_area, selection_mode="multi", format_func=label,
                                key=f"chips_{area}_{ver}", label_visibility="collapsed")
        else:
            st.caption("Nothing else here yet.")

    # apply only what changed on this page, so edits from another tab/device aren't overwritten
    removed = (set(init_songs) - set(new_song_ids)) | (set(init_map) - set(sel_top or []))
    added = [i for i in new_song_ids + list(sel_top or []) + list(sel_area or []) if i not in picked]
    chosen = list(dict.fromkeys([i for i in picked if i not in removed] + added))
    if chosen != picked:
        P.set_active_items(chosen)
        # picked items move into the selected lists: new widget keys so they redraw from the saved list
        st.session_state.chip_ver = ver + 1
        st.rerun()

    with st.expander(":material/queue_music: What you're working on"):
        render_current_work()

    # --- Metronome: loops while you play; its tempo pre-fills the bpm boxes when you end the session
    with st.expander(":material/timer_play: Metronome" + (f" · {active['bpm']} bpm" if active.get("bpm") else "")):
        c1, c2 = st.columns([2, 1])
        bpm_now = c1.number_input("Tempo (bpm)", 30, 260, int(active.get("bpm") or 80), step=2, key="metro_bpm",
                                  on_change=lambda: P.set_active_field("bpm", int(st.session_state.metro_bpm)))
        beats = c2.selectbox("Beats", [2, 3, 4, 6], index=2, key="metro_beats")
        from modules.audio import generate_metronome_click_wav

        bars = 4
        st.audio(generate_metronome_click_wav(int(bpm_now), beats, bars * beats * 60 / bpm_now + 1e-6),
                 format="audio/wav", loop=True)
        st.caption("Press play: it loops until you stop it. Accented click on beat 1.")

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
            st.caption("Minutes are taken from the timer when you press Save (paused time excluded).")
            adjust = st.checkbox("Adjust minutes (e.g. forgot to pause)")
            manual_minutes = st.number_input("Minutes practised", 1, 600,
                                             max(1, round(P.elapsed_seconds(active) / 60)),
                                             help="Only used when 'Adjust minutes' is ticked")
            metro = active.get("bpm")
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
                bpm = col2.text_input("bpm", value=str(metro or c["row"].get("bpm", "")), key=f"bpm_{i}",
                                      placeholder="bpm", label_visibility="collapsed",
                                      help="Pre-filled from the metronome. Clear it if you didn't play this to a click.")
                note = st.text_input("Next time", key=f"note_{i}",
                                     placeholder="Next time: e.g. bridge bars 17–24 at 60 bpm")
                updates[i] = {"status": status, "note": note.strip(), "bpm": bpm.strip()}
            notes = st.text_area("What you practised",
                                 value=st.session_state.get("session_notes", active.get("notes", "")),
                                 height=100)
            take = st.audio_input("Record a take (optional)")
            col_a, col_b = st.columns(2)
            save = col_a.form_submit_button("Save session", type="primary", icon=":material/check:",
                                            width="stretch")
            discard = col_b.form_submit_button("Discard", icon=":material/delete:", width="stretch")
        if save:
            # minutes from the timer at the moment you press Save, unless you chose to adjust
            minutes = int(manual_minutes) if adjust else max(
                1, round(P.elapsed_seconds(P.active_session() or active) / 60))
            rec_link = ""
            if take is not None:
                fname = f"take-{start:%Y%m%d-%H%M}.wav"
                try:
                    rec_link = store.upload_recording(take.getvalue(), fname)
                except RuntimeError as e:
                    # never lose a take: keep it in this browser session with a download button
                    st.session_state.unsaved_take = {"name": fname, "data": take.getvalue(), "error": str(e)}
            P.save_session(start, int(minutes), updates, notes.strip(), rec_link)
            st.toast(f"Saved {fmt_minutes(minutes)} of practice", icon=":material/check_circle:")
            st.rerun()
        if discard:
            P.cancel_session()
            st.rerun()
    st.stop()


# ============================================================================ not practising
if st.session_state.get("unsaved_take"):
    t = st.session_state.unsaved_take
    with st.container(border=True):
        st.warning(f"Your session was saved, but the recording couldn't be uploaded: {t['error']}",
                   icon=":material/mic_off:")
        c1, c2 = st.columns(2)
        c1.download_button("Download the take", t["data"], t["name"], "audio/wav",
                           icon=":material/download:", width="stretch")
        if c2.button("Dismiss", width="stretch"):
            del st.session_state.unsaved_take
            st.rerun()

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
        if last.get("notes"):
            st.markdown("  \n".join("> " + line for line in last["notes"].splitlines()))
        for r in last_items:
            row = cat.get(r["item_id"], {}).get("row", {})
            nxt = r["note"] or row.get("next_note", "")
            st.markdown(f"- {label(r['item_id'])}" + (f"  \n  :material/flag: *{nxt}*" if nxt else ""))
        if last.get("recording"):
            st.markdown(f":material/mic: [Your last recording]({last['recording']})"
                        if last["recording"].startswith("http") else f":material/mic: {last['recording']}")
else:
    st.info("No sessions yet. Press **Start practising**, play whatever you feel like, "
            "and tap what you worked on. Browse the **Pathway** page for ideas.", icon=":material/lightbulb:")

# --- what's in progress / getting rusty
st.subheader("What you're working on")
render_current_work()

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

with st.expander(":material/edit_note: Manage past sessions"):
    if not sess:
        st.caption("No sessions yet.")
    st.caption("Deleting a session removes it everywhere (log, Progress Dashboard) and resets each item's "
               "'last practised' date. Recordings stay in your Drive folder.")
    for s in sess[:15]:
        names = [r["item"] for r in items if r["session_id"] == s["id"]]
        with st.container(border=True, horizontal=True, vertical_alignment="center"):
            st.markdown(f"**{s['start'][:16].replace('T', ' ')}** · {fmt_minutes(float(s['minutes'] or 0))}"
                        + (f"  \n:gray[{', '.join(names)}]" if names else "  \n:gray[nothing tagged]"))
            pending = st.session_state.get("confirm_delete") == s["id"]
            if pending:
                if st.button("Confirm", key=f"yes_{s['id']}", type="primary", icon=":material/delete:"):
                    P.delete_session(s["id"])
                    st.session_state.pop("confirm_delete", None)
                    st.toast("Session deleted", icon=":material/delete:")
                    st.rerun()
                if st.button("Keep", key=f"no_{s['id']}"):
                    st.session_state.pop("confirm_delete", None)
                    st.rerun()
            elif st.button("Delete", key=f"del_{s['id']}", icon=":material/delete:"):
                st.session_state.confirm_delete = s["id"]
                st.rerun()
    if len(sess) > 15:
        st.caption(f"Showing the latest 15 of {len(sess)}.")
    url = P.sheet_url()
    if url:
        st.link_button("Open the Google Sheet", url, icon=":material/table:")
