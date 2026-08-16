"""
modules/theory.py

Core music-theory engine for the Guitar Learning App.
Everything here is pure Python (no Streamlit imports) so it can be unit
tested and reused by every page: note math, scales, diatonic chords,
common progressions, and interval names for ear training.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------

NOTES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTES_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# Map every enharmonic spelling to its chromatic index 0-11.
_NOTE_TO_INDEX = {}
for _i, (_s, _f) in enumerate(zip(NOTES_SHARP, NOTES_FLAT)):
    _NOTE_TO_INDEX[_s] = _i
    _NOTE_TO_INDEX[_f] = _i
# A couple of extra common spellings.
_NOTE_TO_INDEX.update({"E#": 5, "B#": 0, "Cb": 11, "Fb": 4})

ALL_KEYS = NOTES_SHARP  # used to populate "Key" dropdowns (C, C#, D, ...)


def note_index(note: str) -> int:
    """Return the chromatic index (0=C .. 11=B) for a note name."""
    note = note.strip()
    if note not in _NOTE_TO_INDEX:
        raise ValueError(f"Unrecognized note name: {note!r}")
    return _NOTE_TO_INDEX[note]


def transpose(note: str, semitones: int, prefer_flat: bool = False) -> str:
    """Return the note name `semitones` above `note` (mod 12)."""
    idx = (note_index(note) + semitones) % 12
    return NOTES_FLAT[idx] if prefer_flat else NOTES_SHARP[idx]


def note_at_fret(open_note: str, fret: int, prefer_flat: bool = False) -> str:
    """Note sounding at a given fret on a string tuned to `open_note`."""
    return transpose(open_note, fret, prefer_flat=prefer_flat)


# ---------------------------------------------------------------------------
# Tunings
# ---------------------------------------------------------------------------

# Stored low string (6) -> high string (1), matching how a player reads them.
TUNING_PRESETS = {
    "Standard (E A D G B E)": ["E", "A", "D", "G", "B", "E"],
    "Drop D (D A D G B E)": ["D", "A", "D", "G", "B", "E"],
    "Half-Step Down (Eb Ab Db Gb Bb Eb)": ["Eb", "Ab", "Db", "Gb", "Bb", "Eb"],
    "Open G (D G D G B D)": ["D", "G", "D", "G", "B", "D"],
    "Open D (D A D F# A D)": ["D", "A", "D", "F#", "A", "D"],
    "DADGAD": ["D", "A", "D", "G", "A", "D"],
}

DEFAULT_TUNING_NAME = "Standard (E A D G B E)"
NUM_FRETS = 22


# ---------------------------------------------------------------------------
# Scales
# ---------------------------------------------------------------------------

SCALE_INTERVALS = {
    "Major": [0, 2, 4, 5, 7, 9, 11],
    "Natural Minor": [0, 2, 3, 5, 7, 8, 10],
    "Major Pentatonic": [0, 2, 4, 7, 9],
    "Minor Pentatonic": [0, 3, 5, 7, 10],
}

SCALE_DEGREE_NAMES_MAJOR = ["1", "2", "3", "4", "5", "6", "7"]
SCALE_DEGREE_NAMES_MINOR = ["1", "2", "b3", "4", "5", "b6", "b7"]


def get_scale_notes(key: str, scale_type: str, prefer_flat: bool = False) -> list[str]:
    """Return the note names in `scale_type` starting on `key`."""
    intervals = SCALE_INTERVALS[scale_type]
    return [transpose(key, i, prefer_flat=prefer_flat) for i in intervals]


def scale_degree_labels(scale_type: str) -> list[str]:
    if "Minor" in scale_type:
        base = SCALE_DEGREE_NAMES_MINOR
    else:
        base = SCALE_DEGREE_NAMES_MAJOR
    n = len(SCALE_INTERVALS[scale_type])
    if n == 5:
        # Pentatonic: drop the 4th degree label position depending on major/minor
        return base[:n] if n <= len(base) else base
    return base


# ---------------------------------------------------------------------------
# Diatonic chords / progressions
# ---------------------------------------------------------------------------

# Triad quality per scale degree (0-indexed) for major and natural-minor keys.
_MAJOR_QUALITIES = ["maj", "min", "min", "maj", "maj", "min", "dim"]
_MINOR_QUALITIES = ["min", "dim", "maj", "min", "min", "maj", "maj"]

ROMAN_MAJOR = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
ROMAN_MINOR = ["i", "ii°", "III", "iv", "v", "VI", "VII"]

CHORD_INTERVALS = {
    "maj": [0, 4, 7],
    "min": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "dom7": [0, 4, 7, 10],
    "dim7": [0, 3, 6, 9],
    "m7b5": [0, 3, 6, 10],
}

QUALITY_SUFFIX = {"maj": "", "min": "m", "dim": "dim", "aug": "aug"}


def chord_notes(root: str, quality: str, prefer_flat: bool = False) -> list[str]:
    return [transpose(root, i, prefer_flat=prefer_flat) for i in CHORD_INTERVALS[quality]]


def diatonic_chords(key: str, scale_type: str = "Major", prefer_flat: bool = False) -> list[dict]:
    """
    Build the 7 diatonic triads for a Major or Natural Minor key.
    Returns a list of dicts: {roman, root, quality, symbol, notes}
    """
    if scale_type not in ("Major", "Natural Minor"):
        raise ValueError("diatonic_chords only supports 'Major' or 'Natural Minor'")

    scale = get_scale_notes(key, scale_type, prefer_flat=prefer_flat)
    qualities = _MAJOR_QUALITIES if scale_type == "Major" else _MINOR_QUALITIES
    romans = ROMAN_MAJOR if scale_type == "Major" else ROMAN_MINOR

    chords = []
    for degree in range(7):
        root = scale[degree]
        quality = qualities[degree]
        symbol = root + QUALITY_SUFFIX[quality]
        chords.append(
            {
                "roman": romans[degree],
                "root": root,
                "quality": quality,
                "symbol": symbol,
                "notes": chord_notes(root, quality, prefer_flat=prefer_flat),
            }
        )
    return chords


# Common progressions expressed as 0-indexed scale degrees (I=0, ii=1, ...)
COMMON_PROGRESSIONS = {
    "I - IV - V": [0, 3, 4],
    "I - V - vi - IV": [0, 4, 5, 3],
    "I - vi - IV - V": [0, 5, 3, 4],
    "ii - V - I": [1, 4, 0],
    "I - IV - V - IV": [0, 3, 4, 3],
    "vi - IV - I - V": [5, 3, 0, 4],
    "12 Bar Blues (I-IV-V)": [0, 0, 0, 0, 3, 3, 0, 0, 4, 3, 0, 4],
}


def generate_progression(key: str, scale_type: str, pattern_name: str, prefer_flat: bool = False):
    chords = diatonic_chords(key, scale_type, prefer_flat=prefer_flat)
    degrees = COMMON_PROGRESSIONS[pattern_name]
    return [chords[d] for d in degrees]


# Placeholder backing-track links per key, used by the Chord Progression page.
# Swap these for real jam-track URLs whenever you like.
YOUTUBE_BACKING_TRACKS = {
    key: "https://www.youtube.com/results?search_query=" + key.replace("#", "%23") + "+major+backing+track"
    for key in ALL_KEYS
}


# ---------------------------------------------------------------------------
# Intervals (for Ear Training)
# ---------------------------------------------------------------------------

INTERVAL_NAMES = {
    0: "Unison",
    1: "Minor 2nd",
    2: "Major 2nd",
    3: "Minor 3rd",
    4: "Major 3rd",
    5: "Perfect 4th",
    6: "Tritone",
    7: "Perfect 5th",
    8: "Minor 6th",
    9: "Major 6th",
    10: "Minor 7th",
    11: "Major 7th",
    12: "Octave",
}


# ---------------------------------------------------------------------------
# CAGED-style neck positions (approximate)
# ---------------------------------------------------------------------------
#
# NOTE: True CAGED shapes are defined by five specific open-chord fingerings
# (C, A, G, E, D) moved up the neck. Reproducing the exact fingering geometry
# needs a hand-built shape table. As a practical first pass, we instead find
# every fret (within one octave) where the chosen root note lands on each
# string, and use those as anchor points for five ~4-fret-wide "position"
# windows moving up the neck. This gives musically useful, non-overlapping
# practice zones even if the shapes aren't literally labeled C/A/G/E/D.

def get_position_windows(root: str, tuning: list[str]) -> list[tuple[int, int]]:
    anchors = set()
    for open_note in tuning:
        fret = (note_index(root) - note_index(open_note)) % 12
        anchors.add(fret)

    windows = []
    for anchor in sorted(anchors)[:5]:
        start = max(0, anchor - 1)
        end = start + 4
        windows.append((start, end))
    return windows
