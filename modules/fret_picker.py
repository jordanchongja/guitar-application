"""
modules/fret_picker.py

A fretboard you can tap or drag across to pick a chord shape. Plotly charts only report whole
selections, so this draws its own neck and follows the pointer in the browser. Picks go back to
Python when the finger or mouse lifts, not on every move, so dragging never waits for a rerun.
"""

from __future__ import annotations

import streamlit as st

from modules.fretboard import (DOUBLE_DOT_FRETS, FRET_LINE_COLOR, NECK_COLOR, NOTE_COLOR, NUT_COLOR, SINGLE_DOT_FRETS,
                               STRING_COLOR)
from modules.theory import note_at_fret

_HTML = """
<div class="picker">
  <svg id="neck" role="group" aria-label="Fretboard"></svg>
  <button id="clear" type="button">Clear</button>
</div>
"""

_CSS = """
.picker { font-family: var(--st-font); color: var(--st-text-color); }
#neck { display: block; width: 100%; touch-action: none; user-select: none; -webkit-user-select: none; cursor: pointer; }
#clear {
  font: inherit; font-size: .875rem; height: 2.25rem; margin-top: .5rem; padding: 0 .8rem; cursor: pointer;
  color: inherit; background: var(--st-secondary-background-color); border: 1px solid transparent;
  border-radius: var(--st-base-radius);
}
"""

_JS = """
const boards = new WeakMap()
const LABEL = 28, NUT = 36, ROW = 38, TOP = 6, BOTTOM = 22

const dot = (x, y, r, fill, extra = "") => `<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" ${extra}/>`
const line = (x1, y1, x2, y2, color, width) =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${width}"/>`

function metrics(board) {
  const { strings, frets, left_handed: mirrored } = board.data
  const width = Math.max(board.svg.parentNode.clientWidth, 280)
  const cell = (width - LABEL - NUT) / frets
  const flip = x => (mirrored ? width - x : x)
  return {
    width, cell, flip, mirrored,
    height: TOP + strings.length * ROW + BOTTOM,
    fretX: fret => flip(LABEL + NUT + fret * cell),
    noteX: fret => flip(fret === 0 ? LABEL + NUT / 2 : LABEL + NUT + (fret - 0.5) * cell),
    rowY: row => TOP + (row + 0.5) * ROW,
  }
}

function draw(board) {
  const { strings, frets, colors, single_dots: single, double_dots: double } = board.data
  const m = metrics(board)
  const top = TOP, bottom = TOP + strings.length * ROW
  const mid = (top + bottom) / 2
  let out = `<rect x="${Math.min(m.fretX(0), m.fretX(frets))}" y="${top}" width="${frets * m.cell}"
             height="${bottom - top}" fill="${colors.neck}"/>`

  for (let fret = 1; fret <= frets; fret++) {
    const x = m.noteX(fret)
    if (single.includes(fret)) out += dot(x, mid, 5, colors.inlay)
    if (double.includes(fret)) out += dot(x, mid - ROW, 5, colors.inlay) + dot(x, mid + ROW, 5, colors.inlay)
    out += line(m.fretX(fret), top, m.fretX(fret), bottom, colors.fret, 2)
    out += `<text x="${x}" y="${bottom + 15}" text-anchor="middle" font-size="11" fill="currentColor" opacity=".6">${fret}</text>`
  }
  out += line(m.fretX(0), top, m.fretX(0), bottom, colors.nut, 6)

  const radius = Math.min(m.cell * 0.42, 15)
  strings.forEach((string, row) => {
    const y = m.rowY(row)
    out += line(m.fretX(0), y, m.fretX(frets), y, colors.string, 1 + (string.number - 1) * 0.35)
    out += `<text x="${m.flip(14)}" y="${y + 4}" text-anchor="middle" font-size="12" font-weight="600"
            fill="currentColor">${string.open}</text>`
    for (let fret = 0; fret <= frets; fret++) {
      const x = m.noteX(fret)
      const isOn = board.selected.get(string.number) === fret
      const isHover = board.hover && board.hover.number === string.number && board.hover.fret === fret
      if (isOn) {
        out += dot(x, y, radius, colors.note, `stroke="#fff" stroke-width="1.5"`)
        out += `<text x="${x}" y="${y + 4}" text-anchor="middle" font-size="${Math.min(11, radius)}" font-weight="600"
                fill="#fff">${string.notes[fret]}</text>`
      } else if (isHover) {
        out += dot(x, y, radius, colors.note, `opacity=".35"`)
        out += `<text x="${x}" y="${y + 4}" text-anchor="middle" font-size="${Math.min(11, radius)}"
                fill="${colors.nut}">${string.notes[fret]}</text>`
      } else {
        out += dot(x, y, 3.5, colors.note, `opacity=".3"`)
      }
    }
  })
  board.svg.setAttribute("viewBox", `0 0 ${m.width} ${m.height}`)
  board.svg.setAttribute("height", m.height)
  board.svg.innerHTML = out
}

// The nearest spot to the pointer, so the whole fretboard is a target rather than just the dots.
function spotAt(board, event) {
  const { strings, frets } = board.data
  const m = metrics(board)
  const rect = board.svg.getBoundingClientRect()
  const x = m.mirrored ? rect.right - event.clientX : event.clientX - rect.left
  const row = Math.min(strings.length - 1, Math.max(0, Math.floor((event.clientY - rect.top - TOP) / ROW)))
  const fret = Math.min(frets, Math.max(0, Math.ceil((x - LABEL - NUT) / m.cell)))
  return { row, fret, number: strings[row].number }
}

function apply(board, row, fret) {
  const number = board.data.strings[row].number
  if (board.mode === "add") board.selected.set(number, fret)   // one note per string, like a real hand
  else if (board.selected.get(number) === fret) board.selected.delete(number)
}

// Quick drags jump several cells between events, so fill in the ones passed over.
function paintTo(board, spot) {
  const steps = Math.max(Math.abs(spot.row - board.last.row), Math.abs(spot.fret - board.last.fret))
  for (let step = 1; step <= steps; step++) {
    apply(board,
      Math.round(board.last.row + (spot.row - board.last.row) * step / steps),
      Math.round(board.last.fret + (spot.fret - board.last.fret) * step / steps))
  }
  board.last = spot
}

function send(board) {
  const picked = [...board.selected].sort((a, b) => a[0] - b[0])
  const value = JSON.stringify(picked)
  if (value !== board.sent) {
    board.sent = value
    board.setStateValue("selected", picked)
  }
}

function listen(board) {
  const svg = board.svg
  svg.onpointerdown = event => {
    event.preventDefault()
    svg.setPointerCapture(event.pointerId)
    const spot = spotAt(board, event)
    board.mode = board.selected.get(spot.number) === spot.fret ? "remove" : "add"
    board.last = spot
    apply(board, spot.row, spot.fret)
    draw(board)
  }
  svg.onpointermove = event => {
    const spot = spotAt(board, event)
    if (board.mode) paintTo(board, spot)
    else if (board.hover && board.hover.number === spot.number && board.hover.fret === spot.fret) return
    board.hover = event.pointerType === "mouse" ? spot : null
    draw(board)
  }
  svg.onpointerleave = () => {
    board.hover = null
    if (!board.mode) draw(board)
  }
  svg.onpointerup = svg.onpointercancel = () => {
    board.mode = null
    send(board)
  }
}

export default function ({ data, parentElement, setStateValue }) {
  const $ = id => parentElement.querySelector("#" + id)
  let board = boards.get(parentElement)
  if (!board) {
    board = { svg: $("neck"), selected: new Map(data.selected), sent: JSON.stringify(data.selected), mode: null, hover: null, data }
    boards.set(parentElement, board)
    board.resize = new ResizeObserver(() => draw(board))
    board.resize.observe(board.svg.parentNode)
    listen(board)
  }
  board.data = data
  board.setStateValue = setStateValue
  $("clear").onclick = () => {
    board.selected.clear()
    draw(board)
    send(board)
  }
  if (!board.mode) draw(board)
}
"""

_PICKER = st.components.v2.component("guitar_fret_picker", html=_HTML, css=_CSS, js=_JS)


def fret_picker(tuning: list[str], num_frets: int, left_handed: bool, key: str) -> list[tuple[int, int]]:
    """Draw the neck and return the (string number, fret) spots picked, at most one per string."""
    num_strings = len(tuning)
    strings = [{"number": num_strings - i, "open": open_note,
                "notes": [note_at_fret(open_note, fret) for fret in range(num_frets + 1)]}
               for i, open_note in reversed(list(enumerate(tuning)))]
    result = _PICKER(
        key=key,
        data={
            "strings": strings,
            "frets": num_frets,
            "left_handed": left_handed,
            "selected": (st.session_state.get(key) or {}).get("selected") or [],
            "single_dots": sorted(SINGLE_DOT_FRETS),
            "double_dots": sorted(DOUBLE_DOT_FRETS),
            "colors": {"neck": NECK_COLOR, "fret": FRET_LINE_COLOR, "nut": NUT_COLOR, "string": STRING_COLOR,
                       "note": NOTE_COLOR, "inlay": "#c9b896"},
        },
        on_selected_change=lambda: None,
    )
    # A spot can drop off the neck when the fret slider or tuning changes.
    return [(string, fret) for string, fret in (result.selected or [])
            if 1 <= string <= num_strings and fret <= num_frets]
