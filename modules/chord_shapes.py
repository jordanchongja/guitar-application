"""
modules/chord_shapes.py

Works out how to play a chord on the guitar: which frets, which strings to mute, and which fingers
to use. The shapes are searched for rather than stored, so they work for every root, chord type and
custom tuning. Voicings are lists running low string to high, each entry a fret (0 = open) or None
for a muted string.
"""

from __future__ import annotations

from itertools import product

from modules.chord_analysis import spell_note
from modules.theory import CHORD_INTERVALS, QUALITY_SUFFIX, identify_chord, note_at_fret, note_index

# What the Chord Finder offers, most commonly played first: (button label, quality in modules.theory,
# interval formula).
CHORD_TYPES = [
    ("Major", "maj", "1 3 5"),
    ("Minor", "min", "1 b3 5"),
    ("7", "dom7", "1 3 5 b7"),
    ("m7", "min7", "1 b3 5 b7"),
    ("maj7", "maj7", "1 3 5 7"),
    ("5 (power)", "5", "1 5"),
    ("sus4", "sus4", "1 4 5"),
    ("sus2", "sus2", "1 2 5"),
    ("add9", "add9", "1 3 5 9"),
    ("6", "6", "1 3 5 6"),
    ("m6", "m6", "1 b3 5 6"),
    ("7sus4", "7sus4", "1 4 5 b7"),
    ("9", "9", "1 3 5 b7 9"),
    ("m9", "m9", "1 b3 5 b7 9"),
    ("maj9", "maj9", "1 3 5 7 9"),
    ("m(add9)", "madd9", "1 b3 5 9"),
    ("dim", "dim", "1 b3 b5"),
    ("dim7", "dim7", "1 b3 b5 bb7"),
    ("m7b5", "m7b5", "1 b3 b5 b7"),
    ("aug", "aug", "1 3 #5"),
    ("mMaj7", "mmaj7", "1 b3 5 7"),
]

FINGER_NAMES = {1: "Index", 2: "Middle", 3: "Ring", 4: "Pinky"}
_FRET_SPAN = 4          # frets a hand comfortably covers
_MAX_ROOT_FRET = 12     # the neck repeats from here


def chord_symbol(root: str, quality: str) -> str:
    return root + QUALITY_SUFFIX[quality]


def chord_tone_names(root: str, quality: str) -> list[str]:
    return [spell_note(root, i) for i in CHORD_INTERVALS[quality]]


def assign_fingers(voicing: list[int | None]) -> dict | None:
    """{'fingers': {string index: finger}, 'barre': {'fret', 'first', 'last'} or None}, or None if a
    hand can't play it. Fretted notes take fingers from the lowest fret up. The index only barres
    when there are more notes than fingers."""
    fretted = sorted((fret, i) for i, fret in enumerate(voicing) if fret)
    if not fretted:
        return {"fingers": {}, "barre": None}
    if len(fretted) <= 4:
        return {"fingers": {i: finger for finger, (_, i) in enumerate(fretted, start=1)}, "barre": None}

    lowest = fretted[0][0]
    on_lowest = [i for fret, i in fretted if fret == lowest]
    first, last = on_lowest[0], on_lowest[-1]
    # A barre presses every string it crosses, so nothing under it can ring open or be muted.
    if len(on_lowest) < 2 or not all(voicing[i] for i in range(first, last + 1)):
        return None
    above = [(fret, i) for fret, i in fretted if fret != lowest]
    if len(above) > 3:
        return None
    fingers = {i: 1 for i in on_lowest}
    fingers.update({i: finger for finger, (_, i) in enumerate(above, start=2)})
    return {"fingers": fingers, "barre": {"fret": lowest, "first": first, "last": last}}


def _score(voicing: list[int | None], pitch_classes: list[int], root: int, intervals: set[int], hand: dict) -> float:
    """Lower is easier and better sounding, which puts the familiar open shapes first."""
    sounded = [i for i, fret in enumerate(voicing) if fret is not None]
    frets = [fret for fret in voicing if fret]
    interior_mutes = sum(voicing[i] is None for i in range(sounded[0], sounded[-1] + 1))
    played = [(pitch_classes[i] + voicing[i] - root) % 12 for i in sounded]
    doubled = sum(played.count(t) - 1 for t in set(played) if t not in (0, 7))
    open_strings = voicing.count(0)

    # Bigger chords sound fuller. A power chord only needs its lowest few strings.
    fullness = min(len(sounded), 3) if len(intervals) == 2 else len(sounded)
    score = -3.0 * fullness + 6 * interior_mutes + doubled + len(set(hand["fingers"].values()))
    score += 3 * (7 in intervals and 7 not in played)
    if hand["barre"]:
        score += 1.5
    if frets:
        score += 0.5 * (max(frets) - min(frets)) ** 2 + min(frets)
        # Open strings suit shapes near the nut. Higher up they're a stretch away from the rest of the hand.
        score += -open_strings if max(frets) <= 3 else 4 * (open_strings > 0)
    return score


def find_voicings(tuning: list[str], root: str, quality: str, limit: int = 6) -> list[dict]:
    """Playable shapes with the root in the bass, easiest first: one per place the root can sit, plus
    a closed version where the best shape there uses open strings. Each is {'frets', 'fingers',
    'barre', 'low_fret', 'bass_string'}."""
    intervals = {i % 12 for i in CHORD_INTERVALS[quality]}
    root_pc = note_index(root)
    tones = {(root_pc + i) % 12 for i in intervals}
    # The 5th adds little to a chord of four or more notes, so it can go when a shape needs it to.
    required = tones - ({(root_pc + 7) % 12} if len(tones) >= 4 and 7 in intervals else set())
    fewest_strings = len(required) if len(tones) < 3 else max(4, len(required))
    pitch_classes = [note_index(n) for n in tuning]
    num_strings = len(tuning)

    def options(string: int, lo: int) -> list[int | None]:
        frets = [f for f in range(lo, lo + _FRET_SPAN) if (pitch_classes[string] + f) % 12 in tones]
        return [None] + ([0] if pitch_classes[string] in tones else []) + frets

    seen, best = set(), {}
    for bass in range(num_strings):
        for bass_fret in range(_MAX_ROOT_FRET):
            if (pitch_classes[bass] + bass_fret) % 12 != root_pc:
                continue
            windows = range(max(1, bass_fret - _FRET_SPAN + 1), bass_fret + 1) if bass_fret else range(1, 10)
            for lo in windows:
                for upper in product(*(options(s, lo) for s in range(bass + 1, num_strings))):
                    voicing = [None] * bass + [bass_fret] + list(upper)
                    key = tuple(voicing)
                    if key in seen:
                        continue
                    seen.add(key)
                    sounded = [i for i, fret in enumerate(voicing) if fret is not None]
                    played = {(pitch_classes[i] + voicing[i]) % 12 for i in sounded}
                    frets = [fret for fret in voicing if fret]
                    if len(sounded) < fewest_strings or not required <= played:
                        continue
                    if frets and max(frets) - min(frets) >= _FRET_SPAN:
                        continue
                    # Open strings only suit shapes near the nut. Past that they sound odd and are a reach.
                    if frets and 0 in voicing and max(frets) > 5:
                        continue
                    if sum(voicing[i] is None for i in range(sounded[0], sounded[-1] + 1)) > 1:
                        continue
                    hand = assign_fingers(voicing)
                    if hand is None:
                        continue
                    score = _score(voicing, pitch_classes, root_pc, intervals, hand)
                    group = (bass, bass_fret, any(fret == 0 for fret in voicing))
                    if group not in best or score < best[group][0]:
                        best[group] = (score, voicing, hand)

    ranked = sorted(best.items(), key=lambda item: item[1][0])
    return [{"frets": voicing, **hand, "low_fret": min((f for f in voicing if f), default=0),
             "bass_string": num_strings - bass}
            for (bass, _, _), (_, voicing, hand) in ranked[:limit]]


def shape_title(voicing: dict) -> str:
    if voicing["barre"]:
        return f"Barre at fret {voicing['barre']['fret']}"
    if 0 in voicing["frets"]:
        return "Open shape"
    return f"Fret {voicing['low_fret']} shape"


def shape_steps(voicing: dict) -> list[str]:
    """Plain instructions for making the shape. Strings go by their usual numbers, 1 being the highest."""
    frets = voicing["frets"]
    count = len(frets)
    steps = []
    barre = voicing["barre"]
    if barre:
        steps.append(f"Index: barre strings {count - barre['first']} to {count - barre['last']} at fret {barre['fret']}")
    for i, finger in sorted(voicing["fingers"].items(), key=lambda item: (item[1], item[0])):
        if not (barre and finger == 1):
            steps.append(f"{FINGER_NAMES[finger]}: string {count - i}, fret {frets[i]}")
    open_strings = [str(count - i) for i, fret in enumerate(frets) if fret == 0]
    muted = [str(count - i) for i, fret in enumerate(frets) if fret is None]
    if open_strings:
        steps.append(f"Let ring open: string{'s' if len(open_strings) > 1 else ''} {', '.join(open_strings)}")
    if muted:
        steps.append(f"Don't play: string{'s' if len(muted) > 1 else ''} {', '.join(muted)}")
    return steps


def pattern(frets: list[int | None]) -> str:
    """Low string to high, like x32010. Frets of 10 and up need spaces between them to read."""
    marks = ["x" if fret is None else str(fret) for fret in frets]
    return (" " if any(len(m) > 1 for m in marks) else "").join(marks)


def name_voicing(tuning: list[str], positions: list[tuple[int, int]]) -> dict:
    """Name a shape from (string number, fret) pairs: {'notes' low to high, 'frets', 'matches'}. Names
    with the lowest note as their root come first, and the others read as slash chords."""
    num_strings = len(tuning)
    frets: list[int | None] = [None] * num_strings
    for string_number, fret in positions:
        frets[num_strings - string_number] = fret
    notes = [note_at_fret(tuning[i], fret) for i, fret in enumerate(frets) if fret is not None]
    matches = []
    if notes:
        bass = notes[0]
        for match in identify_chord(set(notes)):
            slash = "" if match["root"] == bass else f"/{bass}"
            matches.append({**match, "symbol": match["symbol"] + slash})
        matches.sort(key=lambda m: "/" in m["symbol"])
    return {"notes": notes, "frets": frets, "matches": matches}
