"""
pages/7_Circle_of_Fifths.py

Phase 3: Interactive Circle of Fifths.

- Visual circle of the 12 major keys (outer ring) and their relative minors
  (inner ring), arranged by ascending fifths.
- Click a key (or pick from the dropdown) to see its key signature and
  diatonic chords.
"""

import math

import plotly.graph_objects as go
import streamlit as st

from modules.settings import render_sidebar_settings
from modules.theory import CIRCLE_OF_FIFTHS, diatonic_chords, key_signature_label

st.set_page_config(page_title="Circle of Fifths", page_icon="🎡", layout="wide")
render_sidebar_settings()

st.title("🎡 Circle of Fifths")
st.write("Click a key on the wheel (or use the dropdown) to see its key signature and diatonic chords.")

st.session_state.setdefault("cof_selected_index", 0)

# --- Build the wheel figure ------------------------------------------------
fig = go.Figure()
outer_x, outer_y, outer_text, outer_custom = [], [], [], []
inner_x, inner_y, inner_text, inner_custom = [], [], [], []

for i, entry in enumerate(CIRCLE_OF_FIFTHS):
    angle = math.pi / 2 - (2 * math.pi * i / 12)  # start at top (12 o'clock), clockwise
    outer_x.append(1.0 * math.cos(angle))
    outer_y.append(1.0 * math.sin(angle))
    outer_text.append(entry["major"])
    outer_custom.append(i)

    inner_x.append(0.62 * math.cos(angle))
    inner_y.append(0.62 * math.sin(angle))
    inner_text.append(entry["minor"])
    inner_custom.append(i)

selected = st.session_state.cof_selected_index
outer_colors = ["#e63946" if i == selected else "#457b9d" for i in range(12)]
inner_colors = ["#e63946" if i == selected else "#a8c3d1" for i in range(12)]

fig.add_trace(go.Scatter(
    x=outer_x, y=outer_y, mode="markers+text", text=outer_text, textposition="middle center",
    textfont=dict(size=14, color="white"), marker=dict(size=46, color=outer_colors),
    customdata=outer_custom, hoverinfo="text", hovertext=outer_text, showlegend=False,
))
fig.add_trace(go.Scatter(
    x=inner_x, y=inner_y, mode="markers+text", text=inner_text, textposition="middle center",
    textfont=dict(size=11, color="#2b2118"), marker=dict(size=36, color=inner_colors),
    customdata=inner_custom, hoverinfo="text", hovertext=inner_text, showlegend=False,
))

fig.update_xaxes(visible=False, range=[-1.3, 1.3])
fig.update_yaxes(visible=False, range=[-1.3, 1.3], scaleanchor="x", scaleratio=1)
fig.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", paper_bgcolor="white")

event = st.plotly_chart(fig, on_select="rerun", key="cof_chart", selection_mode="points",
                         config={"displayModeBar": False})

points = event["selection"]["points"] if event and "selection" in event else []
if points and "customdata" in points[0]:
    st.session_state.cof_selected_index = points[0]["customdata"]
    st.rerun()

# --- Dropdown fallback / confirmation ---------------------------------
key_labels = [f"{e['major']} Major / {e['minor']}" for e in CIRCLE_OF_FIFTHS]
chosen_label = st.selectbox("Or pick a key directly:", options=key_labels, index=st.session_state.cof_selected_index)
chosen_index = key_labels.index(chosen_label)
if chosen_index != st.session_state.cof_selected_index:
    st.session_state.cof_selected_index = chosen_index
    st.rerun()

entry = CIRCLE_OF_FIFTHS[st.session_state.cof_selected_index]
st.divider()
st.subheader(f"{entry['major']} Major  /  {entry['minor']} (relative minor)")
st.markdown(f"**Key signature:** {key_signature_label(entry['signature'])}")

tab_major, tab_minor = st.tabs([f"{entry['major']} Major chords", f"{entry['minor']} chords"])
with tab_major:
    chords = diatonic_chords(entry["major"], "Major")
    cols = st.columns(7)
    for c, col in zip(chords, cols):
        with col:
            st.markdown(f"**{c['roman']}**")
            st.markdown(f"### {c['symbol']}")

with tab_minor:
    minor_root = entry["minor"].replace("m", "")
    chords = diatonic_chords(minor_root, "Natural Minor")
    cols = st.columns(7)
    for c, col in zip(chords, cols):
        with col:
            st.markdown(f"**{c['roman']}**")
            st.markdown(f"### {c['symbol']}")
