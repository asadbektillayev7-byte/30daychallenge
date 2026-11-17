import argparse
import queue
import sys
import time
from pathlib import Path

import numpy as np
import pygame
import sounddevice as sd


# ===== Settings =====
SAMPLE_RATE = 44100      # samples per second from the microphone
CHUNK = 2048             # samples analyzed at once (about 46 ms)
BARS = 32                # number of frequency bars on screen
LOW_HZ = 20
HIGH_HZ = 20000
FLOOR_DB = -90           # quietest level drawn
CEILING_DB = -10         # loudest level drawn
NOTE_MIN_DB = -45        # quieter peaks are ignored for note detection
WIDTH, HEIGHT = 900, 520
SCREENSHOT = Path(__file__).resolve().parent / "audioscope.png"
FPS = 30

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

BACKGROUND = (18, 20, 24)
BAR_COLOR = (225, 229, 233)
PEAK_COLOR = (120, 200, 160)
GRID_COLOR = (40, 44, 52)
TEXT_DIM = (110, 116, 126)


# ===== STEP 1: Sound -> frequencies (the FFT) =====
WINDOW = np.hanning(CHUNK)
FREQS = np.fft.rfftfreq(CHUNK, 1 / SAMPLE_RATE)


def spectrum(samples):
    """Return the loudness in dB of every frequency bin."""
    windowed = samples * WINDOW                       # fade edges to avoid smearing
    magnitude = np.abs(np.fft.rfft(windowed))         # strength of each frequency
    magnitude = magnitude / (WINDOW.sum() / 2)        # a full-scale sine becomes 1.0
    return 20 * np.log10(magnitude + 1e-12)           # convert to decibels


# ===== STEP 2: Group frequency bins into bars =====
EDGES = np.geomspace(LOW_HZ, HIGH_HZ, BARS + 1)       # log spacing, like human hearing


def bar_levels(db):
    levels = np.empty(BARS)
    for i in range(BARS):
        inside = (FREQS >= EDGES[i]) & (FREQS < EDGES[i + 1])
        if inside.any():
            levels[i] = db[inside].max()
        else:
            center = np.sqrt(EDGES[i] * EDGES[i + 1])
            levels[i] = db[np.argmin(np.abs(FREQS - center))]
    return levels


# ===== STEP 3: Find the musical note =====
def detect_note(db):
    """Return (name, frequency, cents) for the strongest pitch, or None."""
    usable = (FREQS >= 60) & (FREQS <= 5000)
    indexes = np.flatnonzero(usable)
    peak = indexes[np.argmax(db[usable])]

    if db[peak] < NOTE_MIN_DB:
        return None

    # Parabolic interpolation: estimate the true peak between two bins.
    left, middle, right = db[peak - 1], db[peak], db[peak + 1]
    shift = 0.5 * (left - right) / (left - 2 * middle + right)
    frequency = (peak + shift) * SAMPLE_RATE / CHUNK

    midi = 69 + 12 * np.log2(frequency / 440)         # 69 is A4 = 440 Hz
    nearest = int(round(midi))
    cents = int(round((midi - nearest) * 100))
    name = f"{NOTE_NAMES[nearest % 12]}{nearest // 12 - 1}"
    return name, frequency, cents


# ===== STEP 4: Where the sound comes from =====
chunks = queue.Queue(maxsize=8)


def microphone_callback(indata, frames, timing, status):
    try:
        chunks.put_nowait(indata[:, 0].copy())
    except queue.Full:
        pass                                          # drop old audio instead of lagging


def demo_chunk(t):
    """A made-up sound: a slowly gliding melody, a bass note, and a little noise."""
    times = t + np.arange(CHUNK) / SAMPLE_RATE
    melody = 440 * 2 ** (np.round(4 * np.sin(t * 0.7)) / 12)
    sound = 0.25 * np.sin(2 * np.pi * melody * times)
    sound += 0.12 * np.sin(2 * np.pi * 110 * times)
    sound += 0.05 * np.sin(2 * np.pi * melody * 3 * times)
    sound += 0.003 * np.random.randn(CHUNK)
    return sound


# ===== STEP 5: Draw everything =====
def to_height(level_db, max_height):
    share = (level_db - FLOOR_DB) / (CEILING_DB - FLOOR_DB)
    return int(np.clip(share, 0, 1) * max_height)


def draw(screen, fonts, shown, peaks, note, source, frozen):
    small, medium, big = fonts
    screen.fill(BACKGROUND)

    top, bottom, side = 90, HEIGHT - 60, 40
    area = bottom - top
    for i in range(1, 4):
        y = top + area * i // 4
        pygame.draw.line(screen, GRID_COLOR, (side, y), (WIDTH - side, y))

    slot = (WIDTH - 2 * side) / BARS
    bar_width = max(4, int(slot * 0.55))
    for i in range(BARS):
        x = int(side + i * slot + (slot - bar_width) / 2)
        height = max(4, to_height(shown[i], area))
        pygame.draw.rect(screen, BAR_COLOR, (x, bottom - height, bar_width, height), border_radius=3)
        peak_y = bottom - to_height(peaks[i], area)
        pygame.draw.line(screen, PEAK_COLOR, (x, peak_y), (x + bar_width, peak_y), 2)

    for hz, label in [(20, "20 Hz"), (200, "200 Hz"), (2000, "2 kHz"), (20000, "20 kHz")]:
        share = np.log(hz / LOW_HZ) / np.log(HIGH_HZ / LOW_HZ)
        x = int(side + share * (WIDTH - 2 * side))
        text = small.render(label, True, TEXT_DIM)
        screen.blit(text, (min(x, WIDTH - side - text.get_width()), bottom + 12))

    screen.blit(medium.render("D·15  AudioScope", True, BAR_COLOR), (side, 24))
    status = f"{source}{'  ·  FROZEN' if frozen else ''}  ·  Space freeze  S save  Q quit"
    screen.blit(small.render(status, True, TEXT_DIM), (side, 56))

    if note:
        name, frequency, cents = note
        color = (240, 210, 90) if abs(cents) <= 20 else (240, 120, 80)
        title = big.render(name, True, color)
        screen.blit(title, (WIDTH - side - title.get_width(), 14))
        detail = small.render(f"{frequency:.1f} Hz  {cents:+d}¢", True, TEXT_DIM)
        screen.blit(detail, (WIDTH - side - detail.get_width(), 66))


# ===== STEP 6: Main loop =====
def run(demo):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("AudioScope — Day 15")
    fonts = (
        pygame.font.SysFont("menlo", 14),
        pygame.font.SysFont("menlo", 22, bold=True),
        pygame.font.SysFont("menlo", 40, bold=True),
    )
    clock = pygame.time.Clock()

    stream = None
    if not demo:
        stream = sd.InputStream(
            channels=1, samplerate=SAMPLE_RATE, blocksize=CHUNK,
            dtype="float32", callback=microphone_callback,
        )
        stream.start()

    shown = np.full(BARS, float(FLOOR_DB))
    peaks = np.full(BARS, float(FLOOR_DB))
    note = None
    frozen = False
    started = time.monotonic()
    source = "DEMO SOUND" if demo else "MICROPHONE"

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        return
                    if event.key == pygame.K_SPACE:
                        frozen = not frozen
                    if event.key == pygame.K_s:
                        pygame.image.save(screen, str(SCREENSHOT))
                        print(f"Saved {SCREENSHOT}")

            samples = None
            if demo:
                samples = demo_chunk(time.monotonic() - started)
            else:
                while not chunks.empty():
                    samples = chunks.get_nowait()     # keep only the newest chunk

            if samples is not None and not frozen:
                db = spectrum(samples)
                levels = bar_levels(db)
                shown = np.maximum(levels, shown - 2.5)   # rise fast, fall slowly
                peaks = np.maximum(levels, peaks - 0.6)   # peak markers fall even slower
                note = detect_note(db)

            draw(screen, fonts, shown, peaks, note, source, frozen)
            pygame.display.flip()
            clock.tick(FPS)
    finally:
        if stream:
            stream.stop()
            stream.close()
        pygame.quit()


# ===== Self-test: check the math without a microphone =====
def tone(frequency, amplitude=0.5):
    return amplitude * np.sin(2 * np.pi * frequency * np.arange(CHUNK) / SAMPLE_RATE)


def self_test():
    checks = []

    db = spectrum(tone(1000))
    checks.append(("1000 Hz tone peaks near 1000 Hz", abs(FREQS[np.argmax(db)] - 1000) < SAMPLE_RATE / CHUNK))
    checks.append(("Full-scale sine reads close to 0 dB", abs(spectrum(tone(1000, 1.0)).max()) < 1.5))

    loudest_bar = int(np.argmax(bar_levels(db)))
    checks.append(("1000 Hz lands in the right bar", EDGES[loudest_bar] <= 1000 < EDGES[loudest_bar + 1]))

    for frequency, expected in [(440, "A4"), (261.63, "C4"), (82.41, "E2"), (1318.5, "E6")]:
        result = detect_note(spectrum(tone(frequency)))
        good = result is not None and result[0] == expected and abs(result[2]) <= 10
        checks.append((f"{frequency} Hz is detected as {expected}", good))

    sharp = detect_note(spectrum(tone(440 * 2 ** (30 / 1200))))
    checks.append(("A4 played 30 cents sharp shows about +30¢", sharp is not None and 20 <= sharp[2] <= 40))

    checks.append(("Silence shows no note", detect_note(spectrum(np.zeros(CHUNK))) is None))

    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
    failures = sum(not passed for _, passed in checks)
    print(f"\n{len(checks) - failures}/{len(checks)} checks passed")
    return failures == 0


def main():
    parser = argparse.ArgumentParser(description="See sound: a live microphone spectrum.")
    parser.add_argument("--demo", action="store_true", help="use a made-up sound instead of the microphone")
    parser.add_argument("--test", action="store_true", help="check the math without a microphone and exit")
    options = parser.parse_args()

    if options.test:
        sys.exit(0 if self_test() else 1)

    try:
        run(options.demo)
    except sd.PortAudioError as error:
        print(f"Microphone error: {error}")
        print("Check microphone permission, or try: .venv/bin/python main.py --demo")


if __name__ == "__main__":
    main()
