"""
modules/settings.py

Shared sidebar controls (Left-Handed Mode, Tuning) that every page renders
so the choices stay in sync and persist across page navigation via
st.session_state.
"""

from __future__ import annotations

import streamlit as st

from modules.theory import DEFAULT_TUNING_NAME, NUM_FRETS, TUNING_PRESETS


def init_global_state() -> None:
    st.session_state.setdefault("left_handed", False)
    st.session_state.setdefault("tuning_name", DEFAULT_TUNING_NAME)
    st.session_state.setdefault("num_frets", NUM_FRETS)


def render_sidebar_settings() -> dict:
    """Render the shared settings widgets in the sidebar and return their values."""
    init_global_state()

    with st.sidebar:
        st.markdown("### ⚙️ Global Settings")
        st.toggle("Left-Handed Mode", key="left_handed")
        st.selectbox("Tuning", options=list(TUNING_PRESETS.keys()), key="tuning_name")
        st.slider("Frets shown", min_value=12, max_value=24, key="num_frets")
        st.divider()

    return {
        "left_handed": st.session_state["left_handed"],
        "tuning": TUNING_PRESETS[st.session_state["tuning_name"]],
        "num_frets": st.session_state["num_frets"],
    }
