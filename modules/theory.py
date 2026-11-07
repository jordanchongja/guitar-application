"""
modules/theory.py

Core music-theory engine for the Guitar Learning App.
Everything here is pure Python (no Streamlit imports) so it can be unit
tested and reused by every page: note math, scales, diatonic chords,
common progressions, and interval names for ear training.
"""

from __future__ import annotations

import random

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
    "5": [0, 7],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "7sus4": [0, 5, 7, 10],
    "6": [0, 4, 7, 9],
    "m6": [0, 3, 7, 9],
    "add9": [0, 4, 7, 14],
    "madd9": [0, 3, 7, 14],
    "mmaj7": [0, 3, 7, 11],
    "9": [0, 4, 7, 10, 14],
    "maj9": [0, 4, 7, 11, 14],
    "m9": [0, 3, 7, 10, 14],
}

QUALITY_SUFFIX = {
    "maj": "",
    "min": "m",
    "dim": "dim",
    "aug": "aug",
    "maj7": "maj7",
    "min7": "m7",
    "dom7": "7",
    "dim7": "dim7",
    "m7b5": "m7b5",
    "5": "5",
    "sus2": "sus2",
    "sus4": "sus4",
    "7sus4": "7sus4",
    "6": "6",
    "m6": "m6",
    "add9": "add9",
    "madd9": "madd9",
    "mmaj7": "mMaj7",
    "9": "9",
    "maj9": "maj9",
    "m9": "m9",
}


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
# Functional Ear Trainer (Alain Benbassat method)
# ---------------------------------------------------------------------------
#
# Unlike the interval trainer above (two notes -> name the gap between them),
# this establishes a tonal center with a short cadence, then plays a single
# note -- the listener identifies that note's *scale degree* (its function
# within the key), not an interval distance. Movable-do solfege names the 12
# chromatic scale degrees; "raised" syllables (di, ri, fi, si, li) cover the
# passing tones between the 7 diatonic degrees.

CHROMATIC_SOLFEGE = ["Do", "Di", "Re", "Ri", "Mi", "Fa", "Fi", "So", "Si", "La", "Li", "Ti"]
CHROMATIC_NUMBERS = ["1", "#1", "2", "#2", "3", "4", "#4", "5", "#5", "6", "#6", "7"]

FUNCTIONAL_EAR_LEVELS = {
    "Simple (1, 3, 5)": [0, 4, 7],
    "Diatonic (1-7)": [0, 2, 4, 5, 7, 9, 11],
    "Chromatic (all 12)": list(range(12)),
}

_MAJOR_SCALE_OFFSETS = set(SCALE_INTERVALS["Major"])


def get_resolve_path(target_offset: int) -> list[int]:
    """
    A stepwise line (semitone offsets from the key root) from a scale degree
    back to the tonic, moving only through the *other diatonic* degrees in
    between -- e.g. Fa resolves down through Mi and Re to Do; So and every
    degree above it resolves up through the degrees above to Do an octave
    up. A chromatic (non-diatonic) target still resolves through whichever
    diatonic degrees lie between it and the tonic in that direction.
    """
    if target_offset < 7:
        path = sorted((o for o in _MAJOR_SCALE_OFFSETS if o <= target_offset), reverse=True)
    else:
        path = sorted(o for o in _MAJOR_SCALE_OFFSETS if o >= target_offset) + [12]

    if not path or path[0] != target_offset:
        path = [target_offset] + path
    return path


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


# ---------------------------------------------------------------------------
# CAGED scale shapes
# ---------------------------------------------------------------------------
#
# The five major-scale boxes, written out in C for standard tuning: frets per string, low E first.
# Other keys slide these up the neck. Pentatonics and minor scales are the same boxes with some
# notes dropped: a minor scale uses the boxes of its relative major (A minor uses C major's).

CAGED_SHAPES = {
    "C": [(0, 1, 3), (0, 2, 3), (0, 2, 3), (0, 2), (0, 1, 3), (0, 1, 3)],
    "A": [(3, 5), (2, 3, 5), (2, 3, 5), (2, 4, 5), (3, 5, 6), (3, 5)],
    "G": [(5, 7, 8), (5, 7, 8), (5, 7), (4, 5, 7), (5, 6, 8), (5, 7, 8)],
    "E": [(7, 8, 10), (7, 8, 10), (7, 9, 10), (7, 9, 10), (8, 10), (7, 8, 10)],
    "D": [(10, 12, 13), (10, 12), (9, 10, 12), (9, 10, 12), (10, 12, 13), (10, 12, 13)],
}

# Minor pentatonic boxes are numbered from the shape that starts on the root.
MINOR_PENTATONIC_BOXES = ["G", "E", "D", "C", "A"]

INTERVAL_LABELS = ["1", "b2", "2", "b3", "3", "4", "b5", "5", "b6", "6", "b7", "7"]


def interval_label(root: str, note: str) -> str:
    return INTERVAL_LABELS[(note_index(note) - note_index(root)) % 12]


# ---------------------------------------------------------------------------
# Interval shapes on the neck (for the Interval Tester)
# ---------------------------------------------------------------------------


def string_pitches(tuning: list[str]) -> list[int]:
    """Semitones above the lowest string for each open string, low to high. Each string is taken
    to be within an octave above the one before it, which holds for every preset tuning."""
    pitches = [0]
    for lower, higher in zip(tuning, tuning[1:]):
        pitches.append(pitches[-1] + (note_index(higher) - note_index(lower)) % 12)
    return pitches


def interval_positions(tuning: list[str], root_string: int, root_fret: int, semitones: int,
                       max_fret: int) -> list[tuple[int, int]]:
    """Every (string, fret) up to `max_fret` that sounds `semitones` above the root."""
    pitches = string_pitches(tuning)
    num_strings = len(tuning)
    target = pitches[num_strings - root_string] + root_fret + semitones
    positions = []
    for i, pitch in enumerate(pitches):
        fret = target - pitch
        if 0 <= fret <= max_fret:
            positions.append((num_strings - i, fret))
    return positions


def shape_shift(tuning: list[str], string_a: int, string_b: int) -> int:
    """How many frets higher a shape between two strings sits than it would if every string pair
    were a 4th apart. It's 1 for any pair crossing G-B in standard tuning."""
    pitches = string_pitches(tuning)
    num_strings = len(tuning)
    lower, higher = sorted((num_strings - string_a, num_strings - string_b))
    return 5 * (higher - lower) - (pitches[higher] - pitches[lower])


def make_interval_question(tuning: list[str], semitone_options: list[int], root_strings: list[int], max_fret: int,
                           max_gap: int, rng: random.Random | None = None) -> dict | None:
    """Pick an interval, a fretted root and a note on the same or a thinner string, at most
    `max_gap` strings away. Returns None if the options leave nothing to ask."""
    rng = rng or random
    for semitones in rng.sample(semitone_options, k=len(semitone_options)):
        pairs = []
        for root_string in root_strings:
            for root_fret in range(1, max_fret + 1):
                for string_number, fret in interval_positions(tuning, root_string, root_fret, semitones, max_fret):
                    if 0 <= root_string - string_number <= max_gap:
                        pairs.append(((root_string, root_fret), (string_number, fret)))
        if pairs:
            root, target = rng.choice(pairs)
            return {"semitones": semitones, "root": root, "target": target}
    return None


def interval_choices(semitones: int, rng: random.Random | None = None) -> list[int]:
    """The answer plus three of the nearest intervals, since those are the ones to confuse."""
    rng = rng or random
    nearby = sorted((s for s in range(1, 13) if s != semitones), key=lambda s: abs(s - semitones))
    choices = rng.sample(nearby[:5], k=3) + [semitones]
    rng.shuffle(choices)
    return choices


def get_caged_shape(key: str, scale_type: str, shape: str) -> dict[tuple[int, int], str]:
    """{(string_number, fret): note} for one CAGED box, placed as low on the neck as it fits."""
    parent = transpose(key, 3) if "Minor" in scale_type else key
    shift = note_index(parent)
    frets_by_string = CAGED_SHAPES[shape]
    if min(min(frets) for frets in frets_by_string) + shift >= 12:
        shift -= 12
    scale_notes = get_scale_notes(key, scale_type)
    tuning = TUNING_PRESETS[DEFAULT_TUNING_NAME]
    found = {}
    for i, frets in enumerate(frets_by_string):
        for fret in frets:
            note = note_at_fret(tuning[i], fret + shift)
            if note in scale_notes:
                found[(len(tuning) - i, fret + shift)] = note
    return found


# ---------------------------------------------------------------------------
# Three-Notes-Per-String scale shapes
# ---------------------------------------------------------------------------
#
# Only well-defined for 7-note scales (Major / Natural Minor) -- a 5-note
# pentatonic scale isn't conventionally played 3-per-string. Walks the low
# string upward collecting 3 ascending scale-tone frets, then figures out
# where to pick up the same run on the next string by computing that
# string-pair's tuning interval directly from the note names (so it works
# for any tuning, not just standard), rather than a hard-coded fret offset.

def get_three_nps_pattern(key: str, scale_type: str, tuning: list[str],
                           start_fret: int = 0, num_frets: int = 22) -> dict[tuple[int, int], str]:
    if scale_type not in ("Major", "Natural Minor"):
        raise ValueError("Three-notes-per-string patterns only apply to Major or Natural Minor scales")

    scale_pitch_classes = {note_index(n) for n in get_scale_notes(key, scale_type)}
    num_strings = len(tuning)
    pattern: dict[tuple[int, int], str] = {}

    search_from = max(0, start_fret)
    for string_number in range(num_strings, 0, -1):  # low string (6) up to high string (1)
        open_note = tuning[num_strings - string_number]
        found = []
        fret = search_from
        while len(found) < 3 and fret <= num_frets:
            if (note_index(open_note) + fret) % 12 in scale_pitch_classes:
                found.append(fret)
            fret += 1
        if len(found) < 3:
            break  # ran out of neck before completing this string's group

        for f in found:
            pattern[(string_number, f)] = note_at_fret(open_note, f)

        if string_number > 1:
            next_open = tuning[num_strings - (string_number - 1)]
            # How many frets up *this* string reach the next string's open
            # pitch -- i.e. how much lower that same pitch sits on the next
            # (higher-pitched) string.
            interval = (note_index(next_open) - note_index(open_note)) % 12
            same_pitch_fret_on_next = found[-1] - interval
            search_from = same_pitch_fret_on_next + 1

    return pattern


# ---------------------------------------------------------------------------
# Arpeggios
# ---------------------------------------------------------------------------

ARPEGGIO_INTERVALS = {
    "Major": [0, 4, 7],
    "Minor": [0, 3, 7],
    "Major 7": [0, 4, 7, 11],
    "Minor 7": [0, 3, 7, 10],
    "Dominant 7": [0, 4, 7, 10],
    "Diminished 7": [0, 3, 6, 9],
    # Extended chords (9/11/13), common in jazz/neo-soul/funk. These list the
    # full stacked-thirds chord tones -- a 6-string guitar can't voice all of
    # them uniquely at once, so real voicings use a subset. This page shows
    # every occurrence of every chord tone across the neck (not one fixed
    # voicing), which is exactly what's useful for outlining these chords
    # while soloing, regardless of how you end up voicing them for comping.
    "Major 9": [0, 4, 7, 11, 14],
    "Minor 9": [0, 3, 7, 10, 14],
    "Dominant 9": [0, 4, 7, 10, 14],
    "Dominant 11": [0, 4, 7, 10, 14, 17],
    "Minor 11": [0, 3, 7, 10, 14, 17],
    "Dominant 13": [0, 4, 7, 10, 14, 17, 21],
}


def get_arpeggio_notes(root: str, arpeggio_type: str, prefer_flat: bool = False) -> list[str]:
    return [transpose(root, i, prefer_flat=prefer_flat) for i in ARPEGGIO_INTERVALS[arpeggio_type]]


# ---------------------------------------------------------------------------
# Circle of Fifths
# ---------------------------------------------------------------------------

# 12 positions around the circle, starting at C (12 o'clock) and moving
# clockwise in ascending fifths. `signature` is the count of sharps (+) or
# flats (-) in that major key's key signature.
CIRCLE_OF_FIFTHS = [
    {"major": "C", "minor": "Am", "signature": 0},
    {"major": "G", "minor": "Em", "signature": 1},
    {"major": "D", "minor": "Bm", "signature": 2},
    {"major": "A", "minor": "F#m", "signature": 3},
    {"major": "E", "minor": "C#m", "signature": 4},
    {"major": "B", "minor": "G#m", "signature": 5},
    {"major": "F#", "minor": "D#m", "signature": 6},
    {"major": "Db", "minor": "Bbm", "signature": -5},
    {"major": "Ab", "minor": "Fm", "signature": -4},
    {"major": "Eb", "minor": "Cm", "signature": -3},
    {"major": "Bb", "minor": "Gm", "signature": -2},
    {"major": "F", "minor": "Dm", "signature": -1},
]


def key_signature_label(signature: int) -> str:
    if signature == 0:
        return "No sharps or flats"
    if signature > 0:
        return f"{signature} sharp{'s' if signature != 1 else ''}"
    return f"{-signature} flat{'s' if signature != -1 else ''}"


# ---------------------------------------------------------------------------
# Chord identification (reverse lookup, for the Chord Dictionary)
# ---------------------------------------------------------------------------

CHORD_QUALITY_LABELS = {
    "maj": "Major",
    "min": "Minor",
    "dim": "Diminished",
    "aug": "Augmented",
    "maj7": "Major 7th",
    "min7": "Minor 7th",
    "dom7": "Dominant 7th",
    "dim7": "Diminished 7th",
    "m7b5": "Half-Diminished (m7b5)",
    "5": "Power Chord",
    "sus2": "Suspended 2nd",
    "sus4": "Suspended 4th",
    "7sus4": "Dominant 7th Suspended 4th",
    "6": "Major 6th",
    "m6": "Minor 6th",
    "add9": "Major Add 9",
    "madd9": "Minor Add 9",
    "mmaj7": "Minor Major 7th",
    "9": "Dominant 9th",
    "maj9": "Major 9th",
    "m9": "Minor 9th",
}


def identify_chord(note_names: set[str], prefer_flat: bool = False) -> list[dict]:
    """
    Given a set of note names (any octave/order, duplicates ignored), return
    every root/quality combination whose interval formula produces exactly
    that set of pitch classes. If none does, chords of four or more notes that
    match once their perfect 5th is left out, which guitar voicings often do.
    Empty list means no standard chord matches.
    """
    if len(note_names) < 2:
        return []

    given = {note_index(n) for n in note_names}
    matches, without_fifth = [], []
    for root_idx in range(12):
        root_name = NOTES_FLAT[root_idx] if prefer_flat else NOTES_SHARP[root_idx]
        for quality, intervals in CHORD_INTERVALS.items():
            match = {
                "root": root_name,
                "quality": quality,
                "label": CHORD_QUALITY_LABELS[quality],
                "symbol": root_name + QUALITY_SUFFIX.get(quality, f"({quality})"),
            }
            expected = {(root_idx + i) % 12 for i in intervals}
            if expected == given:
                matches.append(match)
            elif len(intervals) >= 4 and 7 in intervals and expected - {(root_idx + 7) % 12} == given:
                without_fifth.append({**match, "label": f"{match['label']}, no 5th"})
    return matches or without_fifth


# ---------------------------------------------------------------------------
# Randomized Practice Generator
# ---------------------------------------------------------------------------

EXERCISE_LIBRARY = {
    "Warm-Up": [
        "Play a chromatic 1-2-3-4 exercise up and down each string, focusing on even timing and minimal finger movement.",
        "Stretch your fretting hand, then play a slow scale run at half your normal tempo before anything technical.",
        "Play open chords softly for 2 minutes, focusing purely on clean fretting and even string volume.",
    ],
    "Scales": [
        "Play the Major scale in 2 different keys, ascending and descending.",
        "Practice the Minor Pentatonic scale across all 5 neck positions.",
        "Play the Natural Minor scale slowly with a metronome at 60bpm.",
        "Improvise a short melodic phrase using only the Major Pentatonic scale.",
        "Play a scale across the ENTIRE neck in one key, low E to high E, without stopping -- rather than staying inside one box.",
        "Try a Three-Notes-Per-String pattern on the Scale Reference page and shift it up the neck one position at a time (diagonal 'staircase' movement).",
        "Constraint improvisation: improvise for 2 minutes using only 3 notes from the scale.",
        "Constraint improvisation: improvise without repeating the same note twice within any 4-beat span.",
        "Practice moving smoothly between two adjacent scale positions without pausing at the shift.",
    ],
    "Chords & Harmony": [
        "Practice switching cleanly between open C, G, D, Em, and Am chords.",
        "Play through the diatonic chords of a randomly chosen key.",
        "Practice barre chords (E-shape and A-shape) moving up the neck.",
        "Strum a I-V-vi-IV progression in a new key.",
        "Play a triad (root, 3rd, 5th) on strings 1-2-3, then find the SAME triad again on strings 2-3-4, then 3-4-5 -- notice how the shape changes.",
        "Practice all 3 inversions (root position, 1st inversion, 2nd inversion) of a triad on one set of adjacent strings.",
        "Use the Arpeggio Visualizer to explore a 9th, 11th, or 13th chord shape and try outlining it over a static chord.",
        "Pick a random root note and try to sing or hum a Major 3rd above it before checking yourself on the guitar.",
    ],
    "Fretboard Knowledge": [
        "Name every note on the low E string, low to high, without looking.",
        "Find every occurrence of your favorite note across the whole neck in under 60 seconds.",
        "Play the Fretboard Tester quiz and try to beat your best score.",
        "Map out one octave shape starting from each string.",
    ],
    "Ear Training": [
        "Practice identifying Major vs Minor 3rds by ear.",
        "Sing the root note of a chord immediately after strumming it.",
        "Play the Ear Training interval quiz for a few rounds.",
        "Try to find a melody you know by ear, one phrase at a time.",
        "Play a few rounds of the Functional Ear Trainer -- it trains scale-degree recognition (the do/re/mi function of a note) rather than raw interval distance.",
    ],
    "Technique": [
        "Practice alternate picking on a chromatic exercise, slow and clean.",
        "Practice string-skipping exercises across 3 strings.",
        "Play a simple riff cleanly at 3 different tempos.",
        "Legato: pick one note, then play 3-4 hammer-ons/pull-offs in a row without picking again. Make the last note as loud as the first.",
        "Vibrato: fret any note and hold it 4 seconds -- 2 seconds slow & wide, then 2 seconds fast & narrow. Notice the difference.",
        "String bending: pick a note, bend it up a half step, then a whole step, then a step-and-a-half, checking each against the actual fretted target note.",
        "Slides: slide between two frets exactly on the beat with a metronome -- the slide itself should be audible and land precisely on time.",
        "Muting: play a descending scale and use your fretting-hand fingers to mute every string you're not actively playing.",
    ],
    "Rhythm & Groove": [
        "Play a scale in straight 8th notes on the Metronome page, locking every note to the click.",
        "Practice a syncopated 16th-note strumming pattern, deliberately accenting the off-beats.",
        "Play along with a backing or drum track and focus on locking your strums in with the kick and snare, not just 'staying in time'.",
        "Only increase the metronome tempo by 5 BPM once you can play a passage cleanly 3 times in a row at the current one.",
    ],
}


def generate_practice_routine(total_minutes: int, categories: list[str] | None = None,
                               rng: random.Random | None = None) -> list[dict]:
    """Pick a handful of exercises from `categories` and allot minutes to fill `total_minutes`."""
    rng = rng or random
    categories = categories or list(EXERCISE_LIBRARY.keys())
    categories = [c for c in categories if c in EXERCISE_LIBRARY] or list(EXERCISE_LIBRARY.keys())

    pool = [(cat, ex) for cat in categories for ex in EXERCISE_LIBRARY[cat]]
    rng.shuffle(pool)

    num_items = max(2, min(6, total_minutes // 5)) if total_minutes >= 4 else 1
    chosen = pool[:num_items] if len(pool) >= num_items else pool
    if not chosen:
        return []

    base = total_minutes // len(chosen)
    remainder = total_minutes - base * len(chosen)
    routine = []
    for i, (cat, ex) in enumerate(chosen):
        minutes = base + (1 if i < remainder else 0)
        routine.append({"category": cat, "exercise": ex, "minutes": max(minutes, 1)})
    return routine


# ---------------------------------------------------------------------------
# Daily Challenge / "Riff of the Day"
# ---------------------------------------------------------------------------

def generate_challenge_from_seed(seed: str) -> dict:
    """Build a challenge dict deterministically from any string seed."""
    rng = random.Random(seed)
    key = rng.choice(ALL_KEYS)
    kind = rng.choice([
        "progression", "note_hunt", "scale_position", "interval", "arpeggio",
        "technique", "rhythm", "warmup", "three_nps", "functional_ear", "triad_geometry",
    ])

    if kind == "progression":
        pattern_name = rng.choice(list(COMMON_PROGRESSIONS.keys()))
        scale_type = rng.choice(["Major", "Natural Minor"])
        chords = generate_progression(key, scale_type, pattern_name)
        symbols = " - ".join(c["symbol"] for c in chords)
        return {
            "title": "Progression Practice",
            "description": f"Play the **{pattern_name}** progression in **{key} {scale_type}**: {symbols}",
        }
    if kind == "note_hunt":
        note = rng.choice(ALL_KEYS)
        return {
            "title": "Note Hunt",
            "description": f"Find every **{note}** note on the fretboard in under 30 seconds.",
        }
    if kind == "scale_position":
        scale_type = rng.choice(list(SCALE_INTERVALS.keys()))
        position = rng.randint(1, 5)
        return {
            "title": "Position Practice",
            "description": f"Play the **{key} {scale_type}** scale in Position {position} on the Scale Reference page.",
        }
    if kind == "interval":
        interval_name = rng.choice(list(INTERVAL_NAMES.values()))
        return {
            "title": "Ear Training Focus",
            "description": f"Score 5 correct **{interval_name}** identifications in a row on the Ear Training page.",
        }
    if kind == "arpeggio":
        arpeggio_type = rng.choice(list(ARPEGGIO_INTERVALS.keys()))
        return {
            "title": "Arpeggio Practice",
            "description": f"Practice the **{key} {arpeggio_type}** arpeggio shape up and down the neck.",
        }
    if kind == "technique":
        note = rng.choice(ALL_KEYS)
        title, description = rng.choice([
            ("Legato Focus",
             "Pick one note, then play 3-4 hammer-ons/pull-offs in a row without picking again. "
             "Focus on making the last note just as loud as the first."),
            ("Vibrato Focus",
             "Fret any note and hold it for 4 seconds: 2 seconds of slow, wide vibrato, "
             "then 2 seconds of fast, narrow vibrato."),
            ("Bending Focus",
             f"Fret a **{note}** anywhere on the neck and bend it up a whole step until it matches "
             f"**{transpose(note, 2)}** -- check the pitch against that note played normally."),
            ("Slide Focus",
             "Pick a note and slide up 3 frets exactly on the beat, in time with a metronome -- "
             "the slide should be audible and land precisely on the beat."),
            ("Muting Focus",
             "Play a descending scale and use your fretting-hand fingers to mute every string "
             "you're not actively playing."),
        ])
        return {"title": title, "description": description}
    if kind == "rhythm":
        bpm = rng.choice([60, 70, 80, 90, 100, 110, 120])
        description = rng.choice([
            f"Use the Metronome page at **{bpm} BPM** and play the **{key} Major** scale in straight "
            "8th notes, locking every note to the click.",
            "Practice a syncopated 16th-note strumming pattern, deliberately accenting the off-beats.",
            "Play along with any backing or drum track and focus on locking your strums in with the "
            "kick and snare, not just 'staying in time'.",
            f"Set the Metronome to **{bpm} BPM** and only increase the tempo by 5 BPM once you can "
            "play a passage cleanly 3 times in a row.",
        ])
        return {"title": "Rhythm & Groove", "description": description}
    if kind == "warmup":
        description = rng.choice(EXERCISE_LIBRARY["Warm-Up"])
        return {"title": "Warm-Up", "description": description}
    if kind == "three_nps":
        scale_type = rng.choice(["Major", "Natural Minor"])
        start_fret = rng.choice([0, 2, 4, 5, 7, 9])
        return {
            "title": "3-Notes-Per-String Practice",
            "description": (
                f"On the Scale Reference page, set up a **{key} {scale_type}** Three-Notes-Per-String "
                f"pattern starting around fret {start_fret}, then shift it up 2 frets at a time -- "
                "practice moving smoothly across the whole neck instead of staying in one box."
            ),
        }
    if kind == "functional_ear":
        level = rng.choice(list(FUNCTIONAL_EAR_LEVELS.keys()))
        return {
            "title": "Functional Ear Training",
            "description": (
                f"Play 10 rounds of the Functional Ear Trainer at the **{level}** level -- focus on "
                "hearing each note's function (its scale degree) rather than its raw pitch."
            ),
        }
    # triad_geometry
    quality = rng.choice(["Major", "Minor"])
    return {
        "title": "Triad Geometry",
        "description": (
            f"Find a **{key} {quality}** triad (root, 3rd, 5th) on strings 1-2-3, then find the same "
            "triad again on strings 2-3-4, then 3-4-5 -- use the Arpeggio Visualizer to check your work."
        ),
    }


def generate_daily_challenge(date) -> dict:
    """
    Deterministic-per-day challenge: seeded on the ISO date string so every
    visitor sees the same challenge on a given day, and it changes at midnight.
    """
    return generate_challenge_from_seed(date.isoformat())
