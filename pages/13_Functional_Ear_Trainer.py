"""
pages/13_Functional_Ear_Trainer.py

Functional Ear Trainer, following the Alain Benbassat method (the approach
behind the well-known "Functional Ear Trainer" app / tonedear.com's
functional/solfege exercise).

This is deliberately different from pages/4_Ear_Training.py: that page plays
two notes and asks for the interval (the raw distance) between them. This
page establishes a tonal center with a short I-IV-V-I cadence, then plays a
single note, and the listener identifies that note's *scale degree* -- its
function within the key -- using movable-do solfege. The same note sounds
different depending on the key it's heard in, which is the whole point:
this trains hearing tonal function rather than absolute pitch or interval
distance.
"""

import random

import streamlit as st

from modules.audio import generate_cadence_and_tone_wav, generate_scale_run_wav
from modules.database import log_quiz_score
from modules.settings import render_sidebar_settings
from modules.theory import CHROMATIC_NUMBERS, CHROMATIC_SOLFEGE, FUNCTIONAL_EAR_LEVELS, get_resolve_path

st.set_page_config(page_title="Functional Ear Trainer", page_icon="🎯", layout="wide")
render_sidebar_settings()

st.title("🎯 Functional Ear Trainer")
st.write(
    "Based on the Alain Benbassat method. A short cadence establishes a key, then a single "
    "note plays -- identify that note's **scale degree** (its function within the key), not "
    "an interval distance. The same pitch will sound different depending on the key."
)

# --- Options -----------------------------------------------------------
opt1, opt2, opt3 = st.columns(3)
with opt1:
    level = st.selectbox("Level", options=list(FUNCTIONAL_EAR_LEVELS.keys()), index=1)
with opt2:
    fixed_key = st.checkbox("Fixed key (always C)", value=False,
                             help="Off = a random key every question, which is closer to real "
                                  "functional hearing. Turn this on early if random keys feel too hard.")
with opt3:
    numbers_only = st.checkbox("Numbers only (hide solfege)", value=False)

defaults = {
    "fet_score": 0,
    "fet_total": 0,
    "fet_question": None,
    "fet_answered": False,
    "fet_last_correct": None,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


def new_question():
    degree_pool = FUNCTIONAL_EAR_LEVELS[level]
    key_root = 0 if fixed_key else random.randint(-9, 2)  # keeps the cadence in a comfortable register
    target_offset = random.choice(degree_pool)
    wav_bytes = generate_cadence_and_tone_wav(key_root, target_offset)

    st.session_state.fet_question = {
        "key_root": key_root,
        "target_offset": target_offset,
        "degree_pool": degree_pool,
        "wav": wav_bytes,
    }
    st.session_state.fet_answered = False
    st.session_state.fet_last_correct = None


# A change of level/key-mode mid-session should start a fresh question with
# the new settings rather than silently keep quizzing on the old ones.
state_key = (level, fixed_key)
if st.session_state.fet_question is None or st.session_state.get("fet_state_key") != state_key:
    st.session_state.fet_state_key = state_key
    new_question()

question = st.session_state.fet_question

col_score, col_reset = st.columns([3, 1])
with col_score:
    st.metric("Score", f"{st.session_state.fet_score} / {st.session_state.fet_total}")
with col_reset:
    if st.button("Reset Score"):
        st.session_state.fet_score = 0
        st.session_state.fet_total = 0
        new_question()
        st.rerun()

st.audio(question["wav"], format="audio/wav")
st.caption("Cadence (I - IV - V - I) establishes the key, then a single target note plays.")

labels = CHROMATIC_NUMBERS if numbers_only else CHROMATIC_SOLFEGE
degree_pool = question["degree_pool"]
num_cols = min(len(degree_pool), 7)
rows = [degree_pool[i:i + num_cols] for i in range(0, len(degree_pool), num_cols)]
for row in rows:
    cols = st.columns(len(row))
    for offset, col in zip(row, cols):
        with col:
            if st.button(labels[offset], key=f"fet_choice_{offset}_{question['key_root']}",
                         disabled=st.session_state.fet_answered, width="stretch"):
                st.session_state.fet_answered = True
                st.session_state.fet_total += 1
                is_correct = offset == question["target_offset"]
                st.session_state.fet_last_correct = is_correct
                if is_correct:
                    st.session_state.fet_score += 1
                st.rerun()

if st.session_state.fet_answered:
    correct_label = labels[question["target_offset"]]
    if st.session_state.fet_last_correct:
        st.success(f"Correct! That was **{correct_label}**. ✅")
    else:
        st.error(f"Incorrect, that was **{correct_label}**.")

    replay_col1, replay_col2, next_col = st.columns([1, 1, 2])
    with replay_col1:
        if st.button("🔁 Replay"):
            st.rerun()
    with replay_col2:
        if st.button("🎯 Hear It Resolve to Do"):
            # A stepwise line through the diatonic degrees between the
            # target and the tonic -- e.g. Fa resolves down through Mi, Re
            # to Do; So and everything above resolves up to Do an octave up.
            path = get_resolve_path(question["target_offset"])
            run = generate_scale_run_wav(question["key_root"], path, note_duration=0.4, gap=0.06)
            st.session_state.fet_resolve_wav = run
    with next_col:
        if st.button("Next Note ➜", type="primary"):
            st.session_state.pop("fet_resolve_wav", None)
            new_question()
            st.rerun()

    if st.session_state.get("fet_resolve_wav"):
        st.audio(st.session_state.fet_resolve_wav, format="audio/wav")

st.divider()
save_col1, save_col2 = st.columns([1, 3])
with save_col1:
    if st.button("💾 Finish & Save Score", disabled=st.session_state.fet_total == 0):
        log_quiz_score(f"Functional Ear Trainer ({level})", st.session_state.fet_score, st.session_state.fet_total)
        st.session_state.fet_score = 0
        st.session_state.fet_total = 0
        new_question()
        st.success("Score saved to your Progress Dashboard!")
with save_col2:
    st.caption("Saves your current score to the database and starts a fresh session.")
