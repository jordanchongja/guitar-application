"""
app_pages/16_Interval_Tester.py

Quiz for interval shapes on the neck, from the root to each interval up to the octave.

- Name it: root and a second note are shown; pick the interval from 4 choices.
- Find it: root and an interval name are given; click a fret where that interval is.
- The answer shows every place that note sits, plays the interval, and flags shapes that shift
  because they cross a string pair tuned differently (G-B in standard tuning).
"""

import random

import streamlit as st

from modules.audio import generate_interval_wav
from modules.database import log_quiz_score
from modules.fretboard import NOTE_COLOR, QUESTION_COLOR, ROOT_COLOR, draw_clickable_fretboard, draw_fretboard
from modules.settings import render_sidebar_settings
from modules.theory import (
    INTERVAL_NAMES,
    interval_choices,
    interval_positions,
    make_interval_question,
    note_at_fret,
    note_index,
    shape_shift,
)

st.set_page_config(page_title="Interval Tester", page_icon="📐", layout="wide")
settings = render_sidebar_settings()
tuning = settings["tuning"]
num_strings = len(tuning)

MODE_NAME = "Name it"
MODE_FIND = "Find it"
INTERVALS = {name: semitones for semitones, name in INTERVAL_NAMES.items() if semitones > 0}

st.title("📐 Interval Tester")
st.write("Learn the shape of each interval from the root, so you can see it without counting frets.")

# --- Quiz options -----------------------------------------------------
with st.expander("Quiz options", expanded=True):
    mode = st.radio("Mode", [MODE_NAME, MODE_FIND], horizontal=True,
                    captions=["See two notes, name the interval", "See the root, click the interval"])
    picked = st.multiselect("Intervals", options=list(INTERVALS), default=list(INTERVALS),
                            help="To work on one interval a week, keep just that one and its neighbours.")
    opt1, opt2, opt3 = st.columns(3)
    with opt1:
        limit_frets_12 = st.checkbox("Limit to frets 1–12", value=True)
    with opt2:
        string_labels = [f"String {n}" for n in range(1, num_strings + 1)]
        root_labels = st.multiselect("Root on strings", options=string_labels, default=string_labels)
    with opt3:
        max_gap = st.slider("Strings between root and note", 0, 3, 2,
                            help="0 keeps both notes on one string, 1 uses the next string, and so on.")

semitone_options = [INTERVALS[name] for name in picked] or list(INTERVALS.values())
root_strings = sorted({int(s.split()[-1]) for s in root_labels} or set(range(1, num_strings + 1)))
max_fret = 12 if limit_frets_12 else settings["num_frets"]

# --- Session state init -------------------------------------------------
for key, value in {"it_score": 0, "it_total": 0, "it_question": None, "it_answered": False, "it_correct": None,
                   "it_picked": None, "it_number": 0, "it_setup": None}.items():
    st.session_state.setdefault(key, value)


def new_question(setup):
    question = make_interval_question(tuning, semitone_options, root_strings, max_fret, max_gap)
    if question:
        root_note = note_at_fret(tuning[num_strings - question["root"][0]], question["root"][1])
        # Keep the clip in a comfortable range, at the real note names.
        root_from_a4 = (note_index(root_note) - note_index("A") + 6) % 12 - 6
        question["root_note"] = root_note
        question["answers"] = interval_positions(tuning, *question["root"], question["semitones"], max_fret)
        question["choices"] = interval_choices(question["semitones"])
        question["wav"] = generate_interval_wav(root_from_a4, question["semitones"])
    st.session_state.it_question = question
    st.session_state.it_answered = False
    st.session_state.it_correct = None
    st.session_state.it_picked = None
    st.session_state.it_number += 1
    st.session_state.it_setup = setup


def record_answer(is_correct, picked_position=None):
    st.session_state.it_answered = True
    st.session_state.it_correct = is_correct
    st.session_state.it_picked = picked_position
    st.session_state.it_total += 1
    st.session_state.it_score += int(is_correct)
    st.rerun()


setup = (tuple(tuning), mode, tuple(semitone_options), tuple(root_strings), max_fret, max_gap)
if st.session_state.it_question is None or st.session_state.it_setup != setup:
    new_question(setup)

question = st.session_state.it_question
if question is None:
    st.warning("No questions fit those options. Allow more strings or frets.")
    st.stop()

name = INTERVAL_NAMES[question["semitones"]]
root_label = f"**{question['root_note']}** on string {question['root'][0]}, fret {question['root'][1]}"

col_score, col_reset = st.columns([3, 1])
with col_score:
    st.metric("Score", f"{st.session_state.it_score} / {st.session_state.it_total}")
with col_reset:
    if st.button("Reset Score"):
        st.session_state.it_score = 0
        st.session_state.it_total = 0
        new_question(setup)
        st.rerun()


def answer_highlights():
    highlights = {question["root"]: {"color": ROOT_COLOR, "label": question["root_note"]}}
    for string_number, fret in question["answers"]:
        note = note_at_fret(tuning[num_strings - string_number], fret)
        highlights[(string_number, fret)] = {"color": NOTE_COLOR, "label": note}
    if st.session_state.it_picked and not st.session_state.it_correct:
        highlights[st.session_state.it_picked] = {"color": QUESTION_COLOR, "label": "✗"}
    return highlights


def show_neck(highlights):
    fig = draw_fretboard(tuning=tuning, num_frets=max_fret, highlights=highlights, left_handed=settings["left_handed"])
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


# --- The question -------------------------------------------------------
if st.session_state.it_answered:
    show_neck(answer_highlights())
elif mode == MODE_NAME:
    show_neck({question["root"]: {"color": ROOT_COLOR, "label": "R"},
               question["target"]: {"color": QUESTION_COLOR, "label": "?"}})
    st.write(f"The root is {root_label}. What interval is the **?** above it?")

    btn_cols = st.columns(4)
    for i, semitones in enumerate(question["choices"]):
        with btn_cols[i]:
            if st.button(INTERVAL_NAMES[semitones], key=f"it_choice_{st.session_state.it_number}_{i}", width='stretch'):
                record_answer(semitones == question["semitones"])
else:
    st.write(f"The root is {root_label}. Click the **{name}** above it.")
    fig = draw_clickable_fretboard(tuning=tuning, num_frets=max_fret, selected={question["root"]},
                                   left_handed=settings["left_handed"])
    fig.update_traces(hoverinfo="none")  # the tooltip would name the note under the cursor
    event = st.plotly_chart(fig, on_select="rerun", key=f"it_neck_{st.session_state.it_number}",
                            selection_mode="points", config={"displayModeBar": False})
    points = event.selection.points if event and event.selection else []
    if points:
        string_number, fret = points[-1]["customdata"]
        position = (int(string_number), int(fret))
        if position != question["root"]:
            record_answer(position in question["answers"], position)

# --- Feedback -----------------------------------------------------------
if st.session_state.it_answered:
    if st.session_state.it_correct:
        st.success(f"Correct! That's a {name} above {question['root_note']}. ✅")
    else:
        st.error(f"Not quite, that was a **{name}** above {question['root_note']}.")

    position = st.session_state.it_picked if st.session_state.it_correct else None
    string_number = (position or question["target"])[0]
    shift = shape_shift(tuning, question["root"][0], string_number)
    if shift:
        direction = "higher" if shift > 0 else "lower"
        frets = "fret" if abs(shift) == 1 else "frets"
        st.info(f"This shape sits {abs(shift)} {frets} {direction} than on other strings, because it crosses "
                "a string pair that isn't tuned a 4th apart (G to B in standard tuning).")

    st.audio(question["wav"], format="audio/wav")
    st.caption("Blue dots show everywhere this note sits. Play them on your guitar and listen for the same sound.")
    if st.button("Next Question ➜"):
        new_question(setup)
        st.rerun()

st.divider()
save_col1, save_col2 = st.columns([1, 3])
with save_col1:
    if st.button("💾 Finish & Save Score", disabled=st.session_state.it_total == 0):
        log_quiz_score("Interval Tester", st.session_state.it_score, st.session_state.it_total)
        st.session_state.it_score = 0
        st.session_state.it_total = 0
        new_question(setup)
        st.success("Score saved to Quiz Scores!")
with save_col2:
    st.caption("Saves your current score to the database and starts a fresh session.")
