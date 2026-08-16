# 🎸 Guitar Learning App

A Streamlit-based guitar learning app: scale reference, fretboard note-finding
quiz, chord progression generator, interval ear-training, and a practice
progress dashboard backed by SQLite. Built following the phased plan in
[claude_prompts_and_plan.md](claude_prompts_and_plan.md).

## Project Structure

```
main.py                        # Home page + shared skeleton / global settings
modules/
  theory.py                    # Notes, scales, chords, progressions, arpeggios, circle of fifths,
                                #   chord identification, practice/daily-challenge generators
  fretboard.py                 # Reusable Plotly fretboard renderer (static + clickable)
  audio.py                     # Dynamic sine-wave tone generation for ear training
  notation.py                  # Minimal treble-clef staff renderer (inline SVG)
  database.py                  # SQLite persistence (practice logs, quiz scores)
  settings.py                  # Shared sidebar controls (Left-Handed Mode, Tuning)
pages/
  1_Scale_Reference.py         # Phase 1 - key/scale/CAGED-position browser
  2_Fretboard_Tester.py        # Phase 2 - note-finding quiz
  3_Chord_Progressions.py      # Phase 3 - diatonic chords + progression generator
  4_Ear_Training.py            # Phase 4 - interval ear training
  5_Progress_Dashboard.py      # Phase 2 - practice log + quiz score history
  6_Chord_Dictionary.py        # Phase 2 - click frets, app names the chord
  7_Circle_of_Fifths.py        # Phase 3 - interactive circle of fifths
  8_Arpeggio_Visualizer.py     # Phase 3 - Maj/min/7th arpeggio shapes on the neck
  9_Practice_Generator.py      # Phase 3 - randomized timed practice routine
  10_Sight_Reading_Trainer.py  # Extra - staff note -> fretboard position quiz
  11_Daily_Challenge.py        # Extra - "Riff of the Day", seeded per date
  12_Custom_Tuning_Builder.py  # Extra - build a tuning string-by-string
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

See [claude_prompts_and_plan.md](claude_prompts_and_plan.md) for the original
phase breakdown. All phases (1-4) and every "Additional Feature Suggestion"
from that plan are now implemented, including the Arpeggio Visualizer,
Sight-Reading Trainer, Daily Challenge, and Custom Tuning Builder.

## Notes on the Sight-Reading Trainer

Staff notation is scoped to natural notes (no accidentals) across C4-F5, one
octave plus a bit -- enough for first-position reading practice. The staff
always displays a canonical octave for a given note letter; the multiple-choice
fretboard positions test the pitch *class* (any octave), not the exact
notated pitch, to keep the quiz well-defined. See `modules/notation.py`.
