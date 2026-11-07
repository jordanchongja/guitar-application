"""
app_pages/6_Chord_Dictionary.py

Phase 2 (remaining): Chord Dictionary.

- Click (or box/lasso-select) dots on the fretboard to build a chord voicing.
- The app calculates and displays the resulting chord name(s) from the
  selected notes, using `modules.theory.identify_chord`.
"""

import streamlit as st

from modules.fretboard import draw_clickable_fretboard
from modules.settings import render_sidebar_settings
from modules.theory import identify_chord, note_at_fret

st.set_page_config(page_title="Chord Dictionary", page_icon="📖", layout="wide")
settings = render_sidebar_settings()
tuning = settings["tuning"]
num_strings = len(tuning)

st.title("📖 Chord Dictionary")
st.write(
    "Build a chord by selecting fret positions on the neck below, and this page will "
    "calculate what chord it is."
)
st.caption(
    "Click a dot to select just that note. To select several dots at once and build a "
    "full voicing, use the **Box Select** or **Lasso Select** tool in the chart's toolbar "
    "(top-right of the chart) and drag over the dots you want."
)

frets_to_show = st.slider("Frets to show", min_value=5, max_value=settings["num_frets"], value=12)

st.session_state.setdefault("chord_dict_reset_counter", 0)
chart_key = f"chord_dict_chart_{st.session_state.chord_dict_reset_counter}"

if st.button("🔄 Clear Selection"):
    st.session_state.chord_dict_reset_counter += 1
    st.rerun()

fig = draw_clickable_fretboard(tuning=tuning, num_frets=frets_to_show, left_handed=settings["left_handed"])
event = st.plotly_chart(
    fig,
    on_select="rerun",
    key=chart_key,
    selection_mode=("points", "box", "lasso"),
    # This is the one chart in the app where the mode bar earns its keep:
    # box/lasso select is the only way to grab several notes at once, and
    # without a visible toolbar there's no way to reach it. Trim it down to
    # just the selection + reset tools so it doesn't invite zoom/pan, which
    # would fight with the click-to-select interaction the rest of the page
    # relies on.
    config={
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["zoom2d", "pan2d", "zoomIn2d", "zoomOut2d", "autoScale2d"],
    },
)

points = event["selection"]["points"] if event and "selection" in event else []
selected_coords = sorted({tuple(p["customdata"]) for p in points if "customdata" in p})

if not selected_coords:
    st.info("No frets selected yet — click or box-select a few dots above to build a chord.")
else:
    st.subheader("Selected Notes")
    rows = []
    note_names = set()
    for string_number, fret in selected_coords:
        i = num_strings - string_number
        note = note_at_fret(tuning[i], fret)
        note_names.add(note)
        rows.append(f"String {string_number}, Fret {fret} → **{note}**")
    st.markdown("  \n".join(rows))

    st.subheader("Resulting Chord")
    matches = identify_chord(note_names)
    if matches:
        for m in matches:
            st.success(f"**{m['symbol']}** — {m['root']} {m['label']}")
    else:
        st.warning(
            "No standard triad/7th chord matches this exact note selection. "
            "Try selecting a root, 3rd, and 5th (e.g. C, E, G for C Major)."
        )
