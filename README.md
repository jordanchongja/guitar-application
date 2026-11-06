# 🎸 Guitar Practice App

I wanted one place for the stuff I actually use when practicing guitar: a
fretboard/scale reference so I don't have to picture it in my head, some
quizzes to check whether I actually know what I think I know, ear training
that goes beyond plain interval drills (the functional/scale-degree method
below is the one I actually use), and something to track practice time and
push me toward practicing things I tend to skip — technique, rhythm, all the
stuff that isn't just "play a scale."

I also wanted an excuse to build something real with
[Claude Code](https://claude.com/claude-code) instead of a toy example. More
on that further down.

## Try it

**[guitar-application.streamlit.app](https://guitar-application.streamlit.app/Scale_Reference)**

Everything works if you just click around: scales, the fretboard quiz, chord
tools, both ear trainers, the metronome, sight-reading, the daily challenge,
custom tunings. One honest caveat — the "log practice" and "save score"
buttons write to *my* Google Sheet, not yours. I'm not collecting anyone's
data on purpose, it's just a personal tool and there's no per-visitor account
system. Click those buttons if you're curious how they behave, just don't
expect the numbers to be "yours" afterward. Everything else is genuinely
usable start to finish.

## Practice tracker (Practice + Pathway pages)

- **Practice:** press Start, play whatever you feel like, tap what you touched, then End and leave a
  one-line *next time* note per item (and optionally record a take). The timer survives your phone
  locking: the start time is saved, elapsed time is computed from it. The page opens with *Last time*,
  what's in progress and what's getting rusty, so coming back after a break is easy.
- **Floating Practice button:** the corner button on every other page shows what you're working on, and
  starts, pauses and tags a session without leaving the page. Saving a session happens on Practice.
- **Pathway:** a map of what's worth learning (fretboard, scales, chords, rhythm, technique, theory &
  ear, application) with a concrete "done when" goal and practice tip per item, *ready to start* and
  *rusty* hints, links into the app's tools, and your songs. Edit it freely in the app.
- Data lives in the same Google Sheet (`pathway`, `songs`, `sessions`, `session_items`,
  `practice_state`); recordings go to a Google Drive folder. Logging and editing need `app_password`.
  `tools/export_practice.py` dumps everything as JSON (used to mirror practice into Obsidian).

## What's in it

- **Reference** — scale/CAGED/3-notes-per-string fretboard views, a chord
  dictionary that names whatever notes you click, circle of fifths, an
  arpeggio + extended-chord (9/11/13) visualizer, a chord progression
  generator, a custom tuning builder
- **Quizzes** — a fretboard note-finding quiz, interval ear training, a
  [Functional Ear Trainer](#functional-ear-trainer) (scale-degree
  recognition, not raw interval distance), sight-reading
- **Practice tools** — a randomized practice-routine generator, a daily
  challenge seeded by the date, a metronome with tap tempo, and a progress
  dashboard

## Built with Claude

Claude Code did most of the actual implementation here — I described what I
wanted a page at a time, it wrote the code, and for a good chunk of it that
meant genuinely testing what got built (installing a browser and clicking
through the running app, not just reading its own code back to itself)
rather than assuming it worked. That caught a handful of real bugs along the
way, including a couple that would've been embarrassing to ship quietly — a
note that silently never rendered on the sight-reading staff, a literal
"undefined" showing up above every fretboard chart. I'm mentioning this
mostly because it's genuinely how the app came together and felt worth being
upfront about, not as a pitch for anything.

## Functional Ear Trainer

`pages/13_Functional_Ear_Trainer.py` follows the Alain Benbassat method (the
approach behind the well-known "Functional Ear Trainer" app and
tonedear.com's functional/solfege exercise) — different from
`pages/4_Ear_Training.py`, which drills the raw distance between two notes.
Here, a short I-IV-V-I cadence establishes a key, then a single note plays;
you identify that note's *scale degree* — its function within the key — via
movable-do solfege, at three levels (Simple: 1/3/5, Diatonic: 1-7,
Chromatic: all 12). There's also a "hear it resolve to Do" button that plays
the stepwise line from that degree back to the tonic, so a Fa resolves
Fa-Mi-Re-Do and a So resolves So-La-Ti-Do (up).

## Running your own copy

Everything below is for anyone who wants their own private instance with
their own persistent tracking, rather than clicking around the shared one
above.

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
  1_Scale_Reference.py         # key/scale/CAGED-position/3-notes-per-string browser
  2_Fretboard_Tester.py        # note-finding quiz
  3_Chord_Progressions.py      # diatonic chords + progression generator
  4_Ear_Training.py            # interval ear training
  5_Progress_Dashboard.py      # practice minutes + quiz score history
  6_Chord_Dictionary.py        # click frets, app names the chord
  7_Circle_of_Fifths.py        # interactive circle of fifths
  8_Arpeggio_Visualizer.py     # arpeggio + extended chord shapes on the neck
  9_Practice_Generator.py      # randomized timed practice routine
  10_Sight_Reading_Trainer.py  # staff note -> fretboard position quiz
  11_Daily_Challenge.py        # "Riff of the Day", seeded per date
  12_Custom_Tuning_Builder.py  # build a tuning string-by-string
  13_Functional_Ear_Trainer.py # Alain Benbassat method: cadence + scale-degree ID
  14_Metronome.py              # click-track generator with tap tempo
requirements.txt
.streamlit/config.toml         # App theme
```

### Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run

```powershell
streamlit run main.py
```

Streamlit auto-discovers the `pages/` directory and builds the sidebar
navigation for you. With no extra setup, practice logs and quiz scores are
stored in a local SQLite file (`guitar_app.db`, created automatically on
first run) — fine for local use, but see below before deploying.

### Deploying your own instance (Streamlit Community Cloud)

1. Push this repo to GitHub (private or public, your call).
2. Sign in to [share.streamlit.io](https://share.streamlit.io) with that
   GitHub account, click "New app," and point it at your repo / branch /
   `main.py`. It picks up `requirements.txt` automatically.
3. If you want it private, go to the deployed app's Settings -> Sharing and
   restrict viewers to specific email addresses instead of "public" — anyone
   not on that list hits a login wall even with the URL.
4. Before or after deploying, set up Google Sheets persistence (next
   section) and paste the same secrets into the app's Settings -> Secrets box.

### Persistent storage (Google Sheets)

A hosted Streamlit app's local filesystem isn't durable — every redeploy or
idle-recycle wipes it, taking `guitar_app.db` with it. The app switches from
local SQLite to Google Sheets automatically the moment it finds Sheets
credentials in `st.secrets`, so practice history survives redeploys once
this is set up. No page code changes either way — see `modules/database.py`.

One-time setup:

1. **Create a Google Cloud project** (or reuse one) at
   [console.cloud.google.com](https://console.cloud.google.com).
2. **Enable the Google Sheets API** for that project (APIs & Services ->
   Enable APIs and Services -> search "Google Sheets API" -> Enable).
3. **Create a service account** (APIs & Services -> Credentials -> Create
   Credentials -> Service Account). Any name is fine; no special roles needed.
4. **Create a JSON key** for that service account (on its page: Keys -> Add
   Key -> Create new key -> JSON) and download it.
5. **Create a Google Sheet** (any name) and **share it** with the service
   account's email address (the `client_email` in the JSON, looks like
   `...@...iam.gserviceaccount.com`) as **Editor**. The app creates the
   `practice_logs` and `quiz_scores` tabs itself on first use.
6. **Copy the spreadsheet ID** from its URL:
   `https://docs.google.com/spreadsheets/d/THIS_PART/edit`.
7. Copy [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example)
   to `.streamlit/secrets.toml` and fill in the values from the JSON key plus
   the spreadsheet ID. For the deployed app, paste the same TOML into
   Settings -> Secrets instead (`secrets.toml` is gitignored either way, so
   it never gets pushed).

That's it — `log_practice`, `log_quiz_score`, and the dashboard's reads all
route to the sheet automatically once those secrets are present, and fall
straight back to local SQLite if they're ever removed.

## Notes on approximations / limitations

- **CAGED positions**: true CAGED shapes are five specific open-chord
  fingerings moved up the neck. This approximates them as ~4-fret "position
  windows" anchored on every occurrence of the root note across the strings
  (see `get_position_windows` in `modules/theory.py`) — musically useful for
  practice zones, but not literally the C/A/G/E/D fingering geometry.
- **3-notes-per-string shapes** (`get_three_nps_pattern`) are derived
  algorithmically from the actual tuning rather than hard-coded, so they
  work for any tuning, including custom ones.
- **Extended chords (9/11/13)** in the Arpeggio Visualizer list the full
  stacked-thirds chord tones. A 6-string guitar can't voice all of them
  uniquely at once, so real voicings use a subset — this shows every
  occurrence of every chord tone across the neck, useful for outlining the
  chord while soloing rather than one fixed practical voicing.
- **Technique exercises** (legato, vibrato, bending, slides, muting,
  strumming, playing in the pocket) are precise written prompts, not graded.
  Verifying bend pitch accuracy, vibrato quality, or clean muting needs real
  audio input and pitch detection, which is out of scope for a browser
  reference app with no microphone access.
- **Backing tracks**: `YOUTUBE_BACKING_TRACKS` in `modules/theory.py`
  currently points at a YouTube search query per key rather than specific
  videos — swap in real URLs if you have jam tracks you like.

## Roadmap

See [claude_prompts_and_plan.md](claude_prompts_and_plan.md) for the
original plan this was built from. All four original phases and every
"Additional Feature Suggestion" in it are implemented. Beyond that plan, the
app also grew a Functional Ear Trainer, a metronome with tap tempo, real
3-notes-per-string scale shapes, extended (9/11/13) chords, and a much
larger practice-routine / daily-challenge content library covering
technique, rhythm, and fretboard-geometry work.
