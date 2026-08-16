# 🎸 Guitar Learning App

A Streamlit-based guitar learning app: scale reference, fretboard note-finding
quiz, chord progression generator, interval ear-training, and a practice
progress dashboard backed by SQLite. Built following the phased plan in
[claude_prompts_and_plan.md](claude_prompts_and_plan.md).

## Project Structure

```
main.py                        # Home page + shared skeleton / global settings
modules/
  theory.py                    # Notes, scales, diatonic chords, progressions, intervals
  fretboard.py                 # Reusable Plotly fretboard renderer
  audio.py                     # Dynamic sine-wave tone generation for ear training
  database.py                  # SQLite persistence (practice logs, quiz scores)
  settings.py                  # Shared sidebar controls (Left-Handed Mode, Tuning)
pages/
  1_Scale_Reference.py         # Task 1
  2_Fretboard_Tester.py        # Task 2
  3_Chord_Progressions.py      # Task 3
  4_Ear_Training.py            # Task 4
  5_Progress_Dashboard.py      # Task 5
requirements.txt
.streamlit/config.toml         # App theme
```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
streamlit run main.py
```

Streamlit will auto-discover the `pages/` directory and build the sidebar
navigation for you. `guitar_app.db` (SQLite) is created automatically on
first run in the project root.

## Notes on approximations

- **CAGED positions**: true CAGED shapes are five specific open-chord
  fingerings moved up the neck. This app approximates them as ~4-fret
  "position windows" anchored on every occurrence of the root note across
  the strings (see `get_position_windows` in `modules/theory.py`). It's
  musically useful for practice zones, but isn't literally the C/A/G/E/D
  fingering geometry — worth revisiting if you want the exact shapes.
- **Backing tracks**: `YOUTUBE_BACKING_TRACKS` in `modules/theory.py` currently
  points at a YouTube search query per key. Swap in real video URLs whenever
  you have specific jam tracks you like.

## Roadmap

See [claude_prompts_and_plan.md](claude_prompts_and_plan.md) for the full
phase breakdown and future ideas (Arpeggio Visualizer, Sight-Reading Trainer,
Daily Challenge, Custom Tuning Builder, etc.).
