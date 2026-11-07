"""
modules/chord_analysis.py

Turns chords you've written down, like "Am F C G" or "Cmaj7 | D7 G", into their relationship with a
key: Roman numerals, which ones sit outside the key, and why that might be. This never works out
what a song's chords are; that part is your ears.
"""

from __future__ import annotations

import re

from modules.theory import INTERVAL_LABELS, SCALE_INTERVALS, note_index, transpose

KEY_ROOTS = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
KEY_MODES = ["major", "minor"]
KEYS = [f"{root} {mode}" for mode in KEY_MODES for root in KEY_ROOTS]

# Everything after the root note -> (tones as semitones from the root, family, suffix on the numeral).
# The family sets the numeral's case: lower case for minor and diminished chords.
_MIN = (0, 3, 7)
_MAJ = (0, 4, 7)
_QUALITIES = {
    "": (_MAJ, "major", ""), "maj": (_MAJ, "major", ""),
    "m": (_MIN, "minor", ""), "min": (_MIN, "minor", ""),
    "5": ((0, 7), "other", "5"),
    "6": (_MAJ + (9,), "major", "6"), "m6": (_MIN + (9,), "minor", "6"),
    "7": (_MAJ + (10,), "major", "7"),
    "maj7": (_MAJ + (11,), "major", "maj7"), "M7": (_MAJ + (11,), "major", "maj7"),
    "m7": (_MIN + (10,), "minor", "7"), "min7": (_MIN + (10,), "minor", "7"),
    "mmaj7": (_MIN + (11,), "minor", "maj7"),
    "9": (_MAJ + (10, 14), "major", "9"), "maj9": (_MAJ + (11, 14), "major", "maj9"),
    "m9": (_MIN + (10, 14), "minor", "9"),
    "11": (_MAJ + (10, 14, 17), "major", "11"), "m11": (_MIN + (10, 14, 17), "minor", "11"),
    "13": (_MAJ + (10, 14, 21), "major", "13"),
    "add9": (_MAJ + (14,), "major", "add9"), "madd9": (_MIN + (14,), "minor", "add9"),
    "sus2": ((0, 2, 7), "other", "sus2"), "sus4": ((0, 5, 7), "other", "sus4"), "sus": ((0, 5, 7), "other", "sus4"),
    "7sus4": ((0, 5, 7, 10), "other", "7sus4"),
    "dim": ((0, 3, 6), "dim", "°"), "°": ((0, 3, 6), "dim", "°"),
    "dim7": ((0, 3, 6, 9), "dim", "°7"), "°7": ((0, 3, 6, 9), "dim", "°7"),
    "m7b5": ((0, 3, 6, 10), "dim", "ø7"), "ø": ((0, 3, 6, 10), "dim", "ø7"), "ø7": ((0, 3, 6, 10), "dim", "ø7"),
    "aug": ((0, 4, 8), "major", "+"), "+": ((0, 4, 8), "major", "+"),
}

# Written relative to the key's own scale, so III in a minor key has no flat.
_DEGREES = {
    "major": ["I", "bII", "II", "bIII", "III", "IV", "#IV", "V", "bVI", "VI", "bVII", "VII"],
    "minor": ["I", "bII", "II", "III", "#III", "IV", "#IV", "V", "VI", "#VI", "VII", "#VII"],
}

_LETTERS = "CDEFGAB"
# How many letter names above the root each interval sits, so Fm spells as F Ab C, not F G# C.
_LETTER_STEPS = [0, 1, 1, 2, 2, 3, 4, 4, 4, 5, 6, 6]


def parse_chord(symbol: str) -> dict | None:
    """{'symbol', 'root', 'semitone', 'tones', 'family', 'suffix', 'bass'}, or None if it isn't a chord."""
    m = re.fullmatch(r"([A-Ga-g])([#b]?)(.*?)(?:/([A-Ga-g][#b]?))?", symbol.strip())
    if not m:
        return None
    root = m.group(1).upper() + m.group(2)
    quality = _QUALITIES.get(m.group(3))
    if quality is None:
        return None
    bass = m.group(4)
    return {"symbol": root + m.group(3) + (f"/{bass[0].upper()}{bass[1:]}" if bass else ""), "root": root,
            "semitone": note_index(root), "tones": quality[0], "family": quality[1], "suffix": quality[2],
            "bass": note_index(bass[0].upper() + bass[1:]) if bass else None}


def parse_progression(text: str) -> tuple[list[dict], list[str]]:
    """Chords from free text, plus anything that couldn't be read. Bar lines, commas and repeats like
    x2 are ignored."""
    chords, unread = [], []
    for token in re.split(r"[\s,|]+", text.replace("(", " ").replace(")", " ")):
        if not token or token in ("-", "–") or re.fullmatch(r"[xX]\d+", token):
            continue
        chord = parse_chord(token)
        if chord:
            chords.append(chord)
        else:
            unread.append(token)
    return chords, unread


def _split_key(key: str) -> tuple[str, str]:
    root, mode = key.split()
    return root, mode


def _scale(root_semitone: int, mode: str) -> set[int]:
    steps = SCALE_INTERVALS["Major" if mode == "major" else "Natural Minor"]
    return {(root_semitone + s) % 12 for s in steps}


def _tones(chord: dict) -> set[int]:
    return {(chord["semitone"] + t) % 12 for t in chord["tones"]}


def _numeral(chord: dict, tonic: int, mode: str) -> str:
    degree = _DEGREES[mode][(chord["semitone"] - tonic) % 12]
    if chord["family"] in ("minor", "dim"):
        degree = degree.lower()
    return degree + chord["suffix"]


def spell_note(root: str, interval: int) -> str:
    """The name of the note `interval` semitones above `root`, spelled as a stacked chord tone."""
    letter = _LETTERS[(_LETTERS.index(root[0]) + _LETTER_STEPS[interval % 12]) % 7]
    offset = (note_index(root) + interval - note_index(letter) + 6) % 12 - 6
    if abs(offset) > 1:     # would need a double flat or sharp
        return transpose(root, interval)
    return letter + {0: "", 1: "#", -1: "b"}[offset]


def _why_outside(chord: dict, next_chord: dict | None, key: str) -> str:
    """A likely reason for a chord outside the key, or just the notes that don't belong."""
    root, mode = _split_key(key)
    tonic = note_index(root)
    degree = (chord["semitone"] - tonic) % 12
    has_major_third = 4 in chord["tones"]
    scale = _scale(tonic, mode)

    if mode == "minor" and degree == 7 and has_major_third:
        return "Major V: the raised 7th from harmonic minor pulls strongly back to i."
    if mode == "minor" and degree == 11 and chord["family"] == "dim":
        return "Leading-tone chord from harmonic minor: it pulls up to i."
    if next_chord and has_major_third and (chord["semitone"] - next_chord["semitone"]) % 12 == 7 \
            and next_chord["semitone"] in scale:
        return f"Secondary dominant: it acts as the V of {_numeral(next_chord, tonic, mode)}, pushing into that chord."
    other = "minor" if mode == "major" else "major"
    if _tones(chord) <= _scale(tonic, other):
        return f"Borrowed from {root} {other}, the parallel key."
    outside = [spell_note(chord["root"], t) for t in chord["tones"] if (chord["semitone"] + t) % 12 not in scale]
    return f"Outside the key: {', '.join(outside)} {'is' if len(outside) == 1 else 'are'} not in {key}."


def analyse(chords: list[dict], key: str) -> list[dict]:
    """Each chord against the key: {'symbol', 'numeral', 'in_key', 'why', 'notes', 'intervals'}."""
    root, mode = _split_key(key)
    tonic = note_index(root)
    scale = _scale(tonic, mode)
    out = []
    for i, chord in enumerate(chords):
        semitones = [(chord["semitone"] + t) % 12 for t in chord["tones"]]
        in_key = set(semitones) <= scale
        why = "" if in_key else _why_outside(chord, chords[i + 1] if i + 1 < len(chords) else None, key)
        if chord["bass"] is not None:
            bass = INTERVAL_LABELS[(chord["bass"] - tonic) % 12]
            why = " ".join(x for x in (why, f"The {bass} of the key is in the bass.") if x)
        out.append({"symbol": chord["symbol"], "numeral": _numeral(chord, tonic, mode), "in_key": in_key, "why": why,
                    "notes": [spell_note(chord["root"], t) for t in chord["tones"]],
                    "intervals": [INTERVAL_LABELS[(s - tonic) % 12] for s in semitones]})
    return out


def suggest_keys(chords: list[dict], limit: int = 2) -> list[str]:
    """The keys that fit best, for when you're not sure. Starting or ending on a key's tonic counts
    for extra."""
    if not chords:
        return []
    scored = []
    for key in KEYS:
        root, mode = _split_key(key)
        tonic = note_index(root)
        scale = _scale(tonic, mode)
        score = sum(_tones(c) <= scale for c in chords) * 2
        for c in (chords[0], chords[-1]):
            if c["semitone"] == tonic and c["family"] == mode:
                score += 1
        scored.append((-score, KEYS.index(key), key))
    return [key for _, _, key in sorted(scored)[:limit]]
