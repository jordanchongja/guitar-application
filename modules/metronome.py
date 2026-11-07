"""
modules/metronome.py

The metronome shared by the floating Practice panel and the Practice page. The clicks are scheduled
in the browser with Web Audio and the engine lives on `window`, so it keeps time through Streamlit
reruns, the panel closing and page changes. Audio inside the app's own elements would stop at each
of those.
"""

from __future__ import annotations

import streamlit as st

from modules import practice as P

_HTML = """
<div class="metro">
  <button id="down" type="button" aria-label="Slower">&minus;</button>
  <label><input id="bpm" type="number" min="30" max="260" aria-label="Tempo in bpm"> bpm</label>
  <button id="up" type="button" aria-label="Faster">+</button>
  <select id="beats" aria-label="Beats per bar">
    <option value="2">2/4</option><option value="3">3/4</option>
    <option value="4">4/4</option><option value="6">6/8</option>
  </select>
  <button id="go" type="button"></button>
</div>
"""

_CSS = """
.metro { display: flex; align-items: center; gap: .4rem; font-family: var(--st-font); color: var(--st-text-color); }
.metro label { display: flex; align-items: center; gap: .25rem; font-size: .875rem; }
.metro input, .metro select, .metro button {
  font: inherit; font-size: .875rem; height: 2.25rem; box-sizing: border-box; color: inherit;
  background: var(--st-secondary-background-color); border: 1px solid transparent;
  border-radius: var(--st-base-radius);
}
.metro input { width: 3.4rem; text-align: center; -moz-appearance: textfield; }
.metro input::-webkit-inner-spin-button { display: none; }
.metro button { min-width: 2.25rem; cursor: pointer; }
.metro #go { margin-left: auto; padding: 0 .8rem; background: var(--st-primary-color); color: #fff; }
.metro #go.on { background: transparent; color: inherit; border-color: var(--st-border-color); }
"""

_JS = """
function engine() {
  if (window.__guitarMetronome) return window.__guitarMetronome
  const m = { bpm: null, beats: 4, running: false, clicks: 0, ctx: null, out: null, timer: null, beat: 0, next: 0 }

  function click(when, accent) {
    const osc = m.ctx.createOscillator(), gain = m.ctx.createGain()
    osc.frequency.value = accent ? 1500 : 1000
    gain.gain.setValueAtTime(accent ? 0.9 : 0.6, when)
    gain.gain.exponentialRampToValueAtTime(0.001, when + 0.05)
    osc.connect(gain).connect(m.out)
    osc.start(when)
    osc.stop(when + 0.05)
    m.clicks++
  }

  // Browsers slow timers in hidden tabs to about once a second, so plan further ahead there.
  function schedule() {
    const ahead = document.hidden ? 2 : 0.15
    while (m.next < m.ctx.currentTime + ahead) {
      click(m.next, m.beat % m.beats === 0)
      m.next += 60 / m.bpm
      m.beat++
    }
  }

  m.start = () => {
    m.ctx = m.ctx || new (window.AudioContext || window.webkitAudioContext)()
    m.ctx.resume()
    m.out = m.ctx.createGain()
    m.out.connect(m.ctx.destination)
    m.beat = 0
    m.next = m.ctx.currentTime + 0.05
    m.running = true
    schedule()
    m.timer = setInterval(schedule, 50)
  }
  m.stop = () => {
    clearInterval(m.timer)
    m.out.disconnect()   // also silences clicks already planned ahead
    m.running = false
  }
  window.__guitarMetronome = m
  return m
}

export default function ({ data, parentElement, setTriggerValue }) {
  const m = engine()
  if (m.bpm === null) m.bpm = data.bpm || 80
  const $ = id => parentElement.querySelector("#" + id)
  const report = () => {
    clearTimeout(m.report)
    m.report = setTimeout(() => setTriggerValue("tempo", m.bpm), 800)
  }
  const draw = () => {
    if (parentElement.activeElement !== $("bpm")) $("bpm").value = m.bpm
    $("beats").value = m.beats
    $("go").textContent = m.running ? "Stop" : "Start"
    $("go").classList.toggle("on", m.running)
  }
  const setBpm = value => {
    if (!(value >= 30 && value <= 260)) return draw()
    m.bpm = Math.round(value)
    if (m.running) report()
    draw()
  }
  $("down").onclick = () => setBpm(m.bpm - 2)
  $("up").onclick = () => setBpm(m.bpm + 2)
  $("bpm").onchange = e => { setBpm(Number(e.target.value)); e.target.blur(); draw() }
  $("beats").onchange = e => { m.beats = Number(e.target.value) }
  $("go").onclick = () => {
    if (m.running) m.stop()
    else { m.start(); report() }
    draw()
  }
  draw()
}
"""

_METRONOME = st.components.v2.component("guitar_metronome", html=_HTML, css=_CSS, js=_JS)


def render_metronome(key: str, bpm: int | str | None = None) -> None:
    """Draw the controls. `bpm` is the starting tempo until one has been chosen in this browser.
    The tempo played goes on the running session, to pre-fill the bpm boxes when it ends."""

    def save_tempo() -> None:
        tempo = st.session_state[key].tempo
        if tempo:
            P.set_active_field("bpm", int(tempo))

    _METRONOME(data={"bpm": int(bpm) if bpm else None}, key=key, on_tempo_change=save_tempo)
