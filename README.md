# 🎸 Guitar Learning App

A Streamlit-based guitar learning app: scale reference, fretboard note-finding
quiz, chord progression generator, interval ear-training, and a practice
progress dashboard. Built following the phased plan in
[claude_prompts_and_plan.md](claude_prompts_and_plan.md).

## Project Structure

```
main.py                        # Home page + shared skeleton / global settings
modules/
  theory.py                    # Notes, scales, chords, progressions, arpeggios, circle of fifths,
                                #   chord identification, practice/daily-challenge generators
  fretboard.py                 # Reusable Plotly fretboard renderer (static + clickable)
  audio.py                     # Dynamic sine-wave tone/chord/cadence/click-track generation
  notation.py                  # Minimal treble-clef staff renderer (inline SVG)
  database.py                  # Practice logs + quiz scores: Google Sheets when
                                #   configured, local SQLite fallback otherwise
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
  13_Functional_Ear_Trainer.py # Extra - Alain Benbassat method: cadence + scale-degree ID
  14_Metronome.py              # Extra - click-track generator with tap tempo
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
navigation for you. With no extra setup, practice logs and quiz scores are
stored in a local SQLite file (`guitar_app.db`, created automatically on
first run) -- fine for local use, but see below before deploying.

## Deploying privately (Streamlit Community Cloud)

1. Push this repo to GitHub as a **private** repository.
2. Sign in to [share.streamlit.io](https://share.streamlit.io) with that
   GitHub account, click "New app," and point it at this repo / branch /
   `main.py`. It picks up `requirements.txt` automatically.
3. In the deployed app's Settings -> Sharing, restrict viewers to specific
   email addresses instead of "public" -- anyone not on that list hits a
   login wall even with the URL.
4. Before (or after) deploying, set up Google Sheets persistence (next
   section) and paste the same secrets into the app's Settings -> Secrets box.

## Persistent storage (Google Sheets)

**Important:** a hosted Streamlit app's local filesystem is not durable --
every redeploy or idle-recycle wipes it, taking `guitar_app.db` with it. The
app automatically switches from local SQLite to Google Sheets the moment it
finds Sheets credentials in `st.secrets`, so practice history survives
redeploys once this is set up. No page code needs to change either way --
see `modules/database.py`.

One-time setup:

1. **Create a Google Cloud project** (or reuse one) at
   [console.cloud.google.com](https://console.cloud.google.com).
2. **Enable the Google Sheets API** for that project (APIs & Services ->
   Enable APIs and Services -> search "Google Sheets API" -> Enable).
3. **Create a service account** (APIs & Services -> Credentials -> Create
   Credentials -> Service Account). Give it any name; no special roles
   needed.
4. **Create a JSON key** for that service account (on the service account's
   page: Keys -> Add Key -> Create new key -> JSON) and download it.
5. **Create a Google Sheet** (any name, e.g. "Guitar App Data") and **share
   it** with the service account's email address (found in the JSON as
   `client_email`, looks like `...@...iam.gserviceaccount.com`) as **Editor**.
   The app creates the `practice_logs` and `quiz_scores` tabs itself on first
   use -- you don't need to add anything inside the sheet.
6. **Copy the spreadsheet ID** from its URL:
   `https://docs.google.com/spreadsheets/d/THIS_PART/edit`.
7. Copy [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example)
   to `.streamlit/secrets.toml` and fill in the values from the JSON key plus
   the spreadsheet ID. For the deployed app, paste the same TOML into
   Settings -> Secrets instead (or in addition -- `secrets.toml` is
   gitignored either way, so it never gets pushed).

That's it -- `log_practice`, `log_quiz_score`, and the dashboard's reads all
route to the sheet automatically once those secrets are present, and fall
straight back to local SQLite if they're ever removed.

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
- **Extended chords (9/11/13)** in the Arpeggio Visualizer list the full
  stacked-thirds chord tones. A 6-string guitar can't voice all of them
  uniquely at once, so real voicings use a subset -- this page shows every
  occurrence of every chord tone across the neck (useful for outlining the
  chord while soloing), rather than one fixed practical voicing.
- **Technique exercises** (legato, vibrato, bending, slides, muting,
  strumming, playing in the pocket) are given as precise written prompts,
  not graded. Verifying bend pitch accuracy, vibrato quality, or clean
  muting needs real audio input + pitch detection, which is out of scope for
  a browser reference app with no microphone access.

## Functional Ear Trainer

`pages/13_Functional_Ear_Trainer.py` implements the Alain Benbassat method
(the approach behind the well-known "Functional Ear Trainer" app and
tonedear.com's functional/solfege exercise) -- distinct from
`pages/4_Ear_Training.py`, which drills raw interval distance between two
notes. Here, a short I-IV-V-I cadence establishes a key, then a single note
plays; you identify that note's *scale degree* (its function within the
key) via movable-do solfege, at three levels (Simple: 1/3/5, Diatonic:
1-7, Chromatic: all 12). See `generate_cadence_and_tone_wav` in
`modules/audio.py` and `FUNCTIONAL_EAR_LEVELS` in `modules/theory.py`.

## Roadmap

See [claude_prompts_and_plan.md](claude_prompts_and_plan.md) for the original
phase breakdown. All phases (1-4) and every "Additional Feature Suggestion"
from that plan are now implemented, including the Arpeggio Visualizer,
Sight-Reading Trainer, Daily Challenge, and Custom Tuning Builder. Beyond
that original plan, the app now also has a Functional Ear Trainer, a
Metronome with tap tempo, real 3-notes-per-string scale shapes, extended
(9/11/13) chords, and a much larger Practice Generator / Daily Challenge
content library covering technique, rhythm, and fretboard-geometry work.

## Notes on the Sight-Reading Trainer

Staff notation is scoped to natural notes (no accidentals) across C4-F5, one
octave plus a bit -- enough for first-position reading practice. The staff
always displays a canonical octave for a given note letter; the multiple-choice
fretboard positions test the pitch *class* (any octave), not the exact
notated pitch, to keep the quiz well-defined. See `modules/notation.py`.
