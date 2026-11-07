"""
app_pages/15_Song_Breakdown.py

Your notebook for songs you're working out by ear: write down the chords you hear in each section,
see how they relate to the key, and note what makes it interesting.
"""

import streamlit as st

from modules import practice as P
from modules import practice_store as store
from modules.audio import generate_chord_sequence_wav
from modules.chord_analysis import KEYS, analyse, parse_progression, suggest_keys
from modules.settings import render_sidebar_settings

st.set_page_config(page_title="Song Breakdown", page_icon=":material/edit_note:", layout="centered")
render_sidebar_settings()

st.title("Song Breakdown")
st.caption("Work it out by ear first, then write down what you hear. This shows how it fits the key; "
           "the listening is yours.")

if not store.password_gate():
    st.stop()


@st.cache_data(show_spinner=False)
def progression_audio(chords: tuple[tuple[int, tuple[int, ...]], ...]) -> bytes:
    return generate_chord_sequence_wav(chords)


def show_analysis(row: dict) -> None:
    chords, unread = parse_progression(row["chords"])
    if unread:
        st.warning("Couldn't read: " + ", ".join(unread) + ". Try forms like Am, F#m7, Cmaj7, Dsus4 or G/B.",
                   icon=":material/help:")
    if not chords:
        return
    result = analyse(chords, row["key"])
    with st.container(horizontal=True, gap="small"):
        for c in result:
            with st.container(border=True, width="content", gap=None):
                st.markdown(f"**{c['numeral']}**" if c["in_key"] else f":orange[**{c['numeral']}**]")
                st.caption(c["symbol"])
    for symbol, why in dict((c["symbol"], c["why"]) for c in result if c["why"]).items():
        st.markdown(f":orange[:material/lightbulb:] **{symbol}:** {why}")
    fits = suggest_keys(chords)
    if row["key"] not in fits:
        st.caption(f"Not sure about {row['key']}? These chords fit {' or '.join(fits)} best.")
    st.audio(progression_audio(tuple((c["semitone"], c["tones"]) for c in chords)), format="audio/wav")
    with st.expander("Notes in each chord"):
        st.dataframe([{"Chord": c["symbol"], "Numeral": c["numeral"], "Notes": " ".join(c["notes"]),
                       "Interval from the key": " ".join(c["intervals"])} for c in result], hide_index=True)


def section_form(song_id: str, row: dict | None, default_key: str) -> None:
    with st.form(f"section_{row['id'] if row else 'new'}", clear_on_submit=row is None, border=row is None):
        c1, c2 = st.columns(2)
        name = c1.text_input("Section", value=row["section"] if row else "", placeholder="Verse, chorus, solo…")
        key = c2.selectbox("Key", KEYS, index=KEYS.index(row["key"] if row else default_key))
        chords = st.text_input("Chords you hear", value=row["chords"] if row else "",
                               placeholder="Am F C G (leave empty for a solo or a general note)")
        notes = st.text_area("What makes it interesting?", value=row["notes"] if row else "", height=100,
                             placeholder="What you noticed: a surprising chord, where the solo lands, the rhythm…")
        if st.form_submit_button("Save" if row else "Add section", type="primary"):
            if name.strip() or chords.strip() or notes.strip():
                P.save_breakdown_section({"id": row["id"] if row else "", "song_id": song_id,
                                          "section": name.strip(), "key": key, "chords": chords.strip(),
                                          "notes": notes.strip()})
                st.rerun()


songs = sorted(P.songs(), key=lambda s: s["title"].lower())
names = {s["id"]: s["title"] + (f" – {s['artist']}" if s["artist"] else "") for s in songs}

# Arriving from a song's card on the Pathway page, or from adding a song below.
chosen = st.session_state.pop("breakdown_new_song", None) or st.query_params.pop("song", None)
if chosen in names:
    st.session_state.breakdown_song = chosen

song_id = st.selectbox("Song", list(names), format_func=names.get, key="breakdown_song", index=None,
                       placeholder="Pick a song")

with st.expander(":material/add: Add a song"):
    with st.form("breakdown_add_song", clear_on_submit=True, border=False):
        c1, c2 = st.columns(2)
        title = c1.text_input("Title")
        artist = c2.text_input("Artist")
        if st.form_submit_button("Add song") and title.strip():
            st.session_state.breakdown_new_song = P.add_song(title, artist, status="Wishlist")
            st.rerun()

if not song_id:
    st.stop()

sections = P.breakdown_sections(song_id)
for row in sections:
    with st.container(border=True):
        st.markdown(f"**{row['section'] or 'Untitled'}**" + (f"  :gray[· {row['key']}]" if row["chords"] else ""))
        show_analysis(row)
        if row["notes"]:
            st.markdown(row["notes"])
        with st.expander("Edit"):
            section_form(song_id, row, row["key"])
            if st.session_state.get("breakdown_delete") == row["id"]:
                if st.button("Confirm delete", key=f"yes_{row['id']}", type="primary", icon=":material/delete:"):
                    P.delete_breakdown_section(row["id"])
                    st.session_state.pop("breakdown_delete")
                    st.rerun()
            elif st.button("Delete section", key=f"del_{row['id']}", icon=":material/delete:"):
                st.session_state.breakdown_delete = row["id"]
                st.rerun()

st.markdown("**Add a section**")
section_form(song_id, None, sections[-1]["key"] if sections else "C major")
