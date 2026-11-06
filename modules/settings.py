"""
modules/settings.py

Shared sidebar controls (Left-Handed Mode, Tuning) that every page renders
so the choices stay in sync and persist across page navigation via
st.session_state.
"""

from __future__ import annotations

import streamlit as st

from modules.theory import DEFAULT_TUNING_NAME, NUM_FRETS, TUNING_PRESETS

CUSTOM_TUNING_LABEL = "Custom (built on Custom Tuning Builder page)"


def init_global_state() -> None:
    st.session_state.setdefault("left_handed", False)
    st.session_state.setdefault("tuning_name", DEFAULT_TUNING_NAME)
    st.session_state.setdefault("num_frets", NUM_FRETS)
    st.session_state.setdefault("custom_tuning_notes", list(TUNING_PRESETS[DEFAULT_TUNING_NAME]))


def render_sidebar_settings(floating_practice: bool = True) -> dict:
    """Render the shared settings widgets in the sidebar and return their values. Also draws the
    floating Practice button, unless the page turns it off."""
    init_global_state()

    tuning_options = list(TUNING_PRESETS.keys()) + [CUSTOM_TUNING_LABEL]

    with st.sidebar:
        st.markdown("### ⚙️ Global Settings")
        st.toggle("Left-Handed Mode", key="left_handed")
        st.selectbox("Tuning", options=tuning_options, key="tuning_name")
        st.slider("Frets shown", min_value=12, max_value=24, key="num_frets")
        st.divider()

    if floating_practice:
        from modules.practice_panel import render_floating_practice

        render_floating_practice()

    if st.session_state["tuning_name"] == CUSTOM_TUNING_LABEL:
        tuning = st.session_state["custom_tuning_notes"]
    else:
        tuning = TUNING_PRESETS[st.session_state["tuning_name"]]

    return {
        "left_handed": st.session_state["left_handed"],
        "tuning": tuning,
        "num_frets": st.session_state["num_frets"],
    }
