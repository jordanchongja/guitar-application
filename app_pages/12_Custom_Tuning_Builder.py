"""
app_pages/12_Custom_Tuning_Builder.py

Additional feature: Custom Tuning Builder.

Lets the user pick the open note for each string individually, instead of
only choosing from presets. Saving here selects "Custom" as the active
global tuning (see modules/settings.py) so every other page picks it up.
"""

import streamlit as st

from modules.fretboard import draw_fretboard
from modules.settings import CUSTOM_TUNING_LABEL, render_sidebar_settings
from modules.theory import NOTES_SHARP, TUNING_PRESETS

st.set_page_config(page_title="Custom Tuning Builder", page_icon="🎛️", layout="wide")

# Streamlit forbids writing to a widget-bound session_state key after that
# widget has been instantiated in the same run. Since the sidebar's "Tuning"
# selectbox (key="tuning_name") is created inside render_sidebar_settings(),
# any switch to "Custom" requested by the Save button below has to be applied
# here, before that widget exists, and take effect on the following rerun.
if "_pending_tuning_switch" in st.session_state:
    st.session_state.tuning_name = st.session_state.pop("_pending_tuning_switch")

settings = render_sidebar_settings()

st.title("🎛️ Custom Tuning Builder")
st.write("Pick the open-string note for each string, low (6) to high (1), to build your own tuning.")

if st.session_state.pop("custom_tuning_just_saved", False):
    st.success(f"Custom tuning saved ({' '.join(settings['tuning'])}) and set as your active tuning.")

st.session_state.setdefault("custom_tuning_notes", list(TUNING_PRESETS["Standard (E A D G B E)"]))
working_tuning = list(st.session_state["custom_tuning_notes"])

string_labels = ["String 6 (lowest)", "String 5", "String 4", "String 3", "String 2", "String 1 (highest)"]
cols = st.columns(6)
new_tuning = []
for i, (label, col) in enumerate(zip(string_labels, cols)):
    with col:
        default_note = working_tuning[i] if i < len(working_tuning) else "E"
        default_index = NOTES_SHARP.index(default_note) if default_note in NOTES_SHARP else 0
        note = st.selectbox(label, options=NOTES_SHARP, index=default_index, key=f"custom_string_{i}")
        new_tuning.append(note)

st.subheader("Preview")
fig = draw_fretboard(tuning=new_tuning, num_frets=15, left_handed=settings["left_handed"])
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

if st.button("💾 Save & Use This Tuning", type="primary"):
    st.session_state.custom_tuning_notes = new_tuning
    st.session_state._pending_tuning_switch = CUSTOM_TUNING_LABEL
    st.session_state.custom_tuning_just_saved = True
    st.rerun()
