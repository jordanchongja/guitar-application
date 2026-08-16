"""
modules/audio.py

Dynamic sine-wave tone generation for Ear Training, so the app doesn't need
any bundled audio assets. Uses numpy to synthesize samples and the stdlib
`wave` module to package them as an in-memory WAV file that st.audio can play.
"""

from __future__ import annotations

import io
import wave

import numpy as np

SAMPLE_RATE = 44100
A4_FREQ = 440.0
A4_INDEX = 57  # MIDI-style semitone index of A4 relative to C0, used only as a fixed reference


def note_frequency(semitones_from_a4: int) -> float:
    """Frequency in Hz for a note `semitones_from_a4` semitones away from A4 (440Hz)."""
    return A4_FREQ * (2 ** (semitones_from_a4 / 12))


def _sine_wave(freq: float, duration: float, fade: float = 0.015) -> np.ndarray:
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave_data = 0.5 * np.sin(2 * np.pi * freq * t)

    # Short fade in/out to avoid audible clicks at note boundaries.
    fade_samples = int(SAMPLE_RATE * fade)
    if fade_samples > 0 and fade_samples * 2 < len(wave_data):
        envelope = np.ones_like(wave_data)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        wave_data *= envelope
    return wave_data


def _silence(duration: float) -> np.ndarray:
    return np.zeros(int(SAMPLE_RATE * duration))


def samples_to_wav_bytes(samples: np.ndarray) -> bytes:
    audio_int16 = np.clip(samples, -1.0, 1.0)
    audio_int16 = (audio_int16 * 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()


def generate_tone_wav(semitones_from_a4: int, duration: float = 1.0) -> bytes:
    """A single tone, e.g. for playing a root note by itself."""
    freq = note_frequency(semitones_from_a4)
    return samples_to_wav_bytes(_sine_wave(freq, duration))


def generate_interval_wav(root_semitones_from_a4: int, interval_semitones: int,
                           note_duration: float = 0.9, gap: float = 0.5) -> bytes:
    """
    Root note, then a short gap, then the second note -- concatenated into a
    single WAV clip so it plays as one sequence from a single st.audio widget.
    """
    root = _sine_wave(note_frequency(root_semitones_from_a4), note_duration)
    second = _sine_wave(note_frequency(root_semitones_from_a4 + interval_semitones), note_duration)
    combined = np.concatenate([root, _silence(gap), second])
    return samples_to_wav_bytes(combined)
