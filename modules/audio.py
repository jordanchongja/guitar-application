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


# ---------------------------------------------------------------------------
# Chords, cadences, and scale runs -- for the Functional Ear Trainer
# ---------------------------------------------------------------------------

_MAJOR_TRIAD = (0, 4, 7)


def _chord_wave(root_semitones: int, intervals: tuple[int, ...], duration: float, fade: float = 0.02) -> np.ndarray:
    """Several sine tones summed and averaged (so more notes don't clip louder)."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave_data = sum(np.sin(2 * np.pi * note_frequency(root_semitones + i) * t) for i in intervals)
    wave_data = (wave_data / len(intervals)) * 0.6

    fade_samples = int(SAMPLE_RATE * fade)
    if fade_samples > 0 and fade_samples * 2 < len(wave_data):
        envelope = np.ones_like(wave_data)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        wave_data *= envelope
    return wave_data


def generate_cadence_and_tone_wav(
    key_root_semitones: int,
    target_offset: int,
    chord_duration: float = 0.45,
    chord_gap: float = 0.04,
    pre_note_gap: float = 0.3,
    note_duration: float = 1.2,
) -> bytes:
    """
    The core stimulus for the Functional Ear Trainer (Alain Benbassat method):
    a I-IV-V-I cadence in a major key to establish the tonal center, then a
    single target tone `target_offset` semitones above the key root. The
    listener's job is to identify that tone's scale degree relative to the
    cadence, not its raw pitch.
    """
    segments = []
    for degree_offset in (0, 5, 7, 0):  # I, IV, V, I (root offsets of each triad)
        segments.append(_chord_wave(key_root_semitones + degree_offset, _MAJOR_TRIAD, chord_duration))
        segments.append(_silence(chord_gap))
    segments.append(_silence(pre_note_gap))
    segments.append(_sine_wave(note_frequency(key_root_semitones + target_offset), note_duration))
    return samples_to_wav_bytes(np.concatenate(segments))


def generate_scale_run_wav(key_root_semitones: int, degree_offsets: list[int],
                            note_duration: float = 0.32, gap: float = 0.02) -> bytes:
    """
    A short stepwise run through `degree_offsets` (semitone offsets from the
    key root, in the order to play them) -- used for "hear it resolve to the
    root" playback, reinforcing a scale degree's function by ear.
    """
    segments = []
    for i, offset in enumerate(degree_offsets):
        segments.append(_sine_wave(note_frequency(key_root_semitones + offset), note_duration))
        if i < len(degree_offsets) - 1:
            segments.append(_silence(gap))
    return samples_to_wav_bytes(np.concatenate(segments))


# ---------------------------------------------------------------------------
# Metronome
# ---------------------------------------------------------------------------

def generate_metronome_click_wav(bpm: int, beats_per_measure: int = 4, duration_seconds: float = 30.0,
                                  accent_first_beat: bool = True) -> bytes:
    """A click track: a short blip on every beat, accented (higher pitch, louder) on beat 1 of each measure."""
    beat_duration = 60.0 / bpm
    total_beats = max(1, int(duration_seconds / beat_duration))
    click_len = min(0.05, beat_duration * 0.4)

    segments = []
    for beat_i in range(total_beats):
        is_accent = accent_first_beat and (beat_i % beats_per_measure == 0)
        freq = 1500 if is_accent else 1000
        amplitude = 0.6 if is_accent else 0.4
        click = _sine_wave(freq, click_len, fade=0.004) * (amplitude / 0.5)
        segments.append(click)
        segments.append(_silence(beat_duration - click_len))
    return samples_to_wav_bytes(np.concatenate(segments))
