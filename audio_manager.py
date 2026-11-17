"""Original procedural audio loops and effects; no external tracks are required."""

import logging
import math
import random
import struct
import wave
from pathlib import Path

from ursina import Audio


logger = logging.getLogger(__name__)
SAMPLE_RATE = 22_050
AUDIO_DIR = Path(__file__).parent / "user_data" / "audio"


def _write_wave(path, duration, sample_at):
    count = int(SAMPLE_RATE * duration)
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for index in range(count):
            sample = max(-1.0, min(1.0, sample_at(index / SAMPLE_RATE)))
            frames.extend(struct.pack("<h", int(sample * 32767)))
        stream.writeframes(frames)


def _loop_envelope(t, duration):
    return min(1.0, t / 0.025, (duration - t) / 0.025)


def _synthesize_assets():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    duration = 4.0
    for filename, variant in (("club_loop.wav", 0), ("dj_loop.wav", 1)):
        path = AUDIO_DIR / filename
        if path.exists():
            continue

        def music_sample(t, variant=variant):
            beat = t % 0.5
            chord = int(t // 1) % 4
            roots = (55.0, 65.4, 73.4, 49.0)
            root = roots[chord]
            bass = 0.16 * math.sin(math.tau * root * t)
            pad = 0.065 * sum(
                math.sin(math.tau * root * multiplier * t)
                for multiplier in (2.0, 2.5, 3.0)
            ) / 3
            kick = 0.42 * math.sin(math.tau * (52 + 110 * math.exp(-beat * 18)) * beat) * math.exp(-beat * 15)
            hat = 0.025 * math.sin(math.tau * 6700 * t) if beat < 0.035 else 0
            wobble = 0.025 * math.sin(math.tau * (root * 4.01) * t) if variant else 0
            return (bass + pad + kick + hat + wobble) * _loop_envelope(t, duration)

        _write_wave(path, duration, music_sample)

    crowd_path = AUDIO_DIR / "crowd_loop.wav"
    if not crowd_path.exists():
        rng = random.Random(127)
        noise = [rng.uniform(-1, 1) for _ in range(SAMPLE_RATE // 10)]

        def crowd_sample(t):
            bed = noise[int(t * SAMPLE_RATE) % len(noise)] * 0.035
            murmur = 0.025 * math.sin(math.tau * 165 * t) * (0.5 + 0.5 * math.sin(math.tau * 0.7 * t))
            return (bed + murmur) * _loop_envelope(t, duration)

        _write_wave(crowd_path, duration, crowd_sample)

    bar_path = AUDIO_DIR / "bar_loop.wav"
    if not bar_path.exists():
        def bar_sample(t):
            phase = t % 1.3
            clink = 0.1 * math.sin(math.tau * 1450 * phase) * math.exp(-phase * 22) if phase < 0.16 else 0
            hum = 0.018 * math.sin(math.tau * 118 * t)
            return (clink + hum) * _loop_envelope(t, duration)

        _write_wave(bar_path, duration, bar_sample)

    effects = {
        "door.wav": (0.22, lambda t: 0.24 * math.sin(math.tau * (170 - 90 * t) * t) * math.exp(-t * 13)),
        "ui.wav": (0.12, lambda t: 0.16 * math.sin(math.tau * 660 * t) * math.exp(-t * 24)),
        "purchase.wav": (0.34, lambda t: (
            0.15 * math.sin(math.tau * 523.25 * t) * math.exp(-t * 7)
            + 0.12 * math.sin(math.tau * 783.99 * max(0, t - 0.08)) * math.exp(-max(0, t - 0.08) * 9)
        )),
    }
    for filename, (duration, sample_at) in effects.items():
        path = AUDIO_DIR / filename
        if not path.exists():
            _write_wave(path, duration, sample_at)


class AudioManager:
    def __init__(self):
        self.music_volume = 0.28
        self.sfx_volume = 0.65
        self.muted = False
        self.music_tracks = []
        self.ambient_tracks = []
        self.effects = {}
        try:
            _synthesize_assets()
        except OSError as error:
            logger.error("Could not create original audio files in %s: %s", AUDIO_DIR, error)
            return

        try:
            for name in ("club_loop.wav", "dj_loop.wav"):
                audio = Audio(AUDIO_DIR / name, loop=True, autoplay=False, volume=self.music_volume, group="music")
                if audio.clip:
                    self.music_tracks.append(audio)
                    audio.play()
            crowd = Audio(AUDIO_DIR / "crowd_loop.wav", loop=True, autoplay=False, volume=0.15, group="ambient")
            if crowd.clip:
                self.ambient_tracks.append(crowd)
                crowd.play()
            bar = Audio(AUDIO_DIR / "bar_loop.wav", loop=True, autoplay=False, volume=0.055, group="ambient")
            if bar.clip:
                self.ambient_tracks.append(bar)
                bar.play()
            for name in ("door", "ui", "purchase"):
                audio = Audio(AUDIO_DIR / f"{name}.wav", autoplay=False, volume=self.sfx_volume, group="sfx")
                if audio.clip:
                    self.effects[name] = audio
        except (OSError, RuntimeError, AttributeError) as error:
            logger.warning("Audio output is unavailable; continuing without sound: %s", error)
            self.music_tracks.clear()
            self.ambient_tracks.clear()
            self.effects.clear()

    def play_effect(self, name):
        effect = self.effects.get(name)
        if effect and not self.muted:
            effect.volume = self.sfx_volume
            effect.play()

    def set_music_volume(self, value):
        self.music_volume = max(0.0, min(1.0, value))
        for track in self.music_tracks:
            track.volume = 0 if self.muted else self.music_volume
        for track in self.ambient_tracks:
            track.volume = 0 if self.muted else self.music_volume * 0.55

    def set_sfx_volume(self, value):
        self.sfx_volume = max(0.0, min(1.0, value))
        for effect in self.effects.values():
            effect.volume = 0 if self.muted else self.sfx_volume

    def toggle_mute(self):
        self.muted = not self.muted
        self.set_music_volume(self.music_volume)
        self.set_sfx_volume(self.sfx_volume)
        return self.muted

    def open_settings(self, ui):
        def change_music(amount):
            self.set_music_volume(self.music_volume + amount)
            self.open_settings(ui)

        def change_sfx(amount):
            self.set_sfx_volume(self.sfx_volume + amount)
            self.open_settings(ui)

        def toggle():
            muted = self.toggle_mute()
            ui.notify("Audio muted." if muted else "Audio unmuted.")
            self.open_settings(ui)

        ui.open_menu(
            "AUDIO SETTINGS",
            [
                (f"Music volume  {self.music_volume:.0%}  -", lambda: change_music(-0.1)),
                (f"Music volume  {self.music_volume:.0%}  +", lambda: change_music(0.1)),
                (f"Effects volume  {self.sfx_volume:.0%}  -", lambda: change_sfx(-0.1)),
                (f"Effects volume  {self.sfx_volume:.0%}  +", lambda: change_sfx(0.1)),
                ("Unmute audio" if self.muted else "Mute audio", toggle),
                ("Close", lambda: None),
            ],
            footer="M adjusts audio settings  |  Esc to close"
        )
