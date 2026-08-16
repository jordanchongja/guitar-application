"""
modules/notation.py

Minimal treble-clef staff renderer (inline SVG) for the Sight-Reading Trainer.
Scope is intentionally small: natural notes only, from middle C (C4, one
ledger line below the staff) up to the top line (F5) -- the range most
useful for reading first-position guitar notation. Accidentals, note
durations, and stems/beams are out of scope for this first pass.
"""

from __future__ import annotations

# (letter, octave, slot) - slot 0 is the bottom staff line (E4), each step is
# half a line-spacing; even slots sit ON a line, odd slots sit in a space.
STAFF_NOTES = [
    ("C", 4, -2),
    ("D", 4, -1),
    ("E", 4, 0),
    ("F", 4, 1),
    ("G", 4, 2),
    ("A", 4, 3),
    ("B", 4, 4),
    ("C", 5, 5),
    ("D", 5, 6),
    ("E", 5, 7),
    ("F", 5, 8),
]

_LETTER_TO_SLOT = {(letter, octave): slot for letter, octave, slot in STAFF_NOTES}

_LINE_SPACING = 16  # px between adjacent staff lines
_STAFF_BOTTOM_Y = 130  # y-coordinate of the bottom staff line (E4, slot 0)


def _slot_y(slot: int) -> float:
    return _STAFF_BOTTOM_Y - slot * (_LINE_SPACING / 2)


def draw_staff_svg(letter: str, octave: int, width: int = 220, height: int = 170) -> str:
    """Return a self-contained inline SVG string showing one note on a treble staff."""
    slot = _LETTER_TO_SLOT.get((letter, octave))
    if slot is None:
        raise ValueError(f"No staff position defined for {letter}{octave}")

    lines_svg = []
    for line_slot in (0, 2, 4, 6, 8):
        y = _slot_y(line_slot)
        lines_svg.append(f'<line x1="40" y1="{y}" x2="{width - 20}" y2="{y}" stroke="currentColor" stroke-width="1.5" />')

    note_x = width / 2 + 10
    note_y = _slot_y(slot)

    ledger_svg = ""
    if slot <= -2 or slot >= 10:
        # Only C4 (slot -2) needs a ledger line in this note range.
        ledger_svg = (
            f'<line x1="{note_x - 14}" y1="{note_y}" x2="{note_x + 14}" y2="{note_y}" '
            f'stroke="currentColor" stroke-width="1.5" />'
        )

    stem_up = slot < 4
    if stem_up:
        stem_svg = f'<line x1="{note_x + 8}" y1="{note_y}" x2="{note_x + 8}" y2="{note_y - 34}" stroke="currentColor" stroke-width="1.5" />'
    else:
        stem_svg = f'<line x1="{note_x - 8}" y1="{note_y}" x2="{note_x - 8}" y2="{note_y + 34}" stroke="currentColor" stroke-width="1.5" />'

    svg = f"""
<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg"
     style="color:#2b2118; background:#fff8ec; border-radius:8px;">
  {''.join(lines_svg)}
  <text x="8" y="{_slot_y(4) + 16}" font-size="46" font-family="serif">&#119070;</text>
  {ledger_svg}
  <ellipse cx="{note_x}" cy="{note_y}" rx="8" ry="6" fill="currentColor" />
  {stem_svg}
</svg>
"""
    return svg


def natural_note_choices() -> list[tuple[str, int]]:
    return [(letter, octave) for letter, octave, _slot in STAFF_NOTES]
