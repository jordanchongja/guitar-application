"""
app_pages/10_Sight_Reading_Trainer.py

Additional feature: Sight-Reading Trainer.

Displays a note on a treble-clef staff and asks the user to find it on the
fretboard, via multiple-choice fret coordinates. After answering, the
correct coordinate is revealed on the fretboard diagram.

Scope note: natural notes only (C4-F5), see `modules/notation.py`.
"""

import random

import streamlit as st

from modules.fretboard import ROOT_COLOR, draw_fretboard
from modules.notation import draw_staff_svg, natural_note_choices
from modules.settings import render_sidebar_settings
from modules.theory import note_at_fret

st.set_page_config(page_title="Sight-Reading Trainer", page_icon="🎼", layout="wide")
settings = render_sidebar_settings()
tuning = settings["tuning"]
num_strings = len(tuning)

st.title("🎼 Sight-Reading Trainer")
st.write("Read the note on the staff, then find a matching position on the fretboard.")

defaults = {
    "sr_score": 0,
    "sr_total": 0,
    "sr_question": None,
    "sr_choices": None,
    "sr_answered": False,
    "sr_last_correct": None,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


def new_question():
    letter, octave = random.choice(natural_note_choices())

    # Find every (string, fret) within the first 12 frets that plays this
    # note, so the multiple-choice coordinates are guaranteed reachable.
    candidates = []
    for i, open_note in enumerate(tuning):
        string_number = num_strings - i
        for fret in range(0, 13):
            if note_at_fret(open_note, fret) == letter:
                candidates.append((string_number, fret))

    if not candidates:
        # Shouldn't happen for natural notes on a standard-ish tuning, but
        # fall back to a re-roll just in case of an unusual custom tuning.
        return new_question()

    correct = random.choice(candidates)

    all_positions = [(s, f) for s in range(1, num_strings + 1) for f in range(0, 13)]
    wrong_pool = [p for p in all_positions if note_at_fret(tuning[num_strings - p[0]], p[1]) != letter]
    distractors = random.sample(wrong_pool, k=min(3, len(wrong_pool)))
    choices = distractors + [correct]
    random.shuffle(choices)

    st.session_state.sr_question = {"letter": letter, "octave": octave, "correct": correct}
    st.session_state.sr_choices = choices
    st.session_state.sr_answered = False
    st.session_state.sr_last_correct = None


if st.session_state.sr_question is None:
    new_question()

question = st.session_state.sr_question

col_score, col_reset = st.columns([3, 1])
with col_score:
    st.metric("Score", f"{st.session_state.sr_score} / {st.session_state.sr_total}")
with col_reset:
    if st.button("Reset Score"):
        st.session_state.sr_score = 0
        st.session_state.sr_total = 0
        new_question()
        st.rerun()

staff_col, board_col = st.columns([1, 2])
with staff_col:
    svg = draw_staff_svg(question["letter"], question["octave"])
    st.markdown(svg, unsafe_allow_html=True)
    st.caption("Which fretboard position plays this note?")

with board_col:
    if st.session_state.sr_answered:
        s, f = question["correct"]
        highlights = {(s, f): {"color": ROOT_COLOR, "label": question["letter"]}}
        fig = draw_fretboard(tuning=tuning, num_frets=12, highlights=highlights, left_handed=settings["left_handed"])
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    else:
        fig = draw_fretboard(tuning=tuning, num_frets=12, left_handed=settings["left_handed"])
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

btn_cols = st.columns(4)
for i, (s, f) in enumerate(st.session_state.sr_choices):
    with btn_cols[i]:
        if st.button(f"String {s}, Fret {f}", key=f"sr_choice_{i}_{question['letter']}_{question['octave']}",
                     disabled=st.session_state.sr_answered, width="stretch"):
            st.session_state.sr_answered = True
            st.session_state.sr_total += 1
            is_correct = (s, f) == question["correct"]
            st.session_state.sr_last_correct = is_correct
            if is_correct:
                st.session_state.sr_score += 1
            st.rerun()

if st.session_state.sr_answered:
    if st.session_state.sr_last_correct:
        st.success("Correct! ✅")
    else:
        cs, cf = question["correct"]
        st.error(f"Incorrect — a valid spot was **String {cs}, Fret {cf}**.")
    if st.button("Next Note ➜"):
        new_question()
        st.rerun()
