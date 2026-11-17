import argparse
import wave
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd


# ===== Settings =====
SAMPLE_RATE = 16000                       # samples per second
FOLDER = Path(__file__).resolve().parent
MIN_DELAY = 0.05                          # shortest echo you can choose (seconds)
MAX_DELAY = 0.6                           # longest echo you can choose (seconds)
SEARCH_FROM = 0.03                        # the detective starts looking a bit earlier
SEARCH_TO = 0.7                           # ... and stops a bit later


# ===== STEP 1: Get a clean voice =====
def record(seconds):
    print(f"Recording for {seconds} seconds. Say something now!")
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    print("Done recording.")
    return audio[:, 0].astype(np.float64)


def demo_voice(seconds):
    """A made-up voice: short 'syllables' of buzzing tones with gaps between them."""
    rng = np.random.default_rng(7)
    audio = np.zeros(int(seconds * SAMPLE_RATE))
    start = 0.2
    while start < seconds - 0.4:
        length = rng.uniform(0.12, 0.3)
        times = np.arange(int(length * SAMPLE_RATE)) / SAMPLE_RATE
        start_pitch, end_pitch = rng.uniform(100, 250, size=2)
        pitch = start_pitch + (end_pitch - start_pitch) * times / length   # pitch glides like speech
        phase = 2 * np.pi * np.cumsum(pitch) / SAMPLE_RATE
        syllable = sum(np.sin(k * phase) / k for k in range(1, 6))
        syllable *= np.sin(np.pi * times / length)            # fade in and out
        begin = int(start * SAMPLE_RATE)
        audio[begin:begin + len(syllable)] += 0.3 * syllable
        start += length + rng.uniform(0.15, 0.5)
    return audio


# ===== STEP 2: Add an echo =====
def add_echo(clean, delay, decay):
    """Each sample also hears itself from `delay` seconds ago, quieter by `decay`.
    Because the echo is fed back, you hear many repeats: decay, decay², decay³ ..."""
    d = int(delay * SAMPLE_RATE)
    echoed = clean.copy()
    for n in range(d, len(echoed)):
        echoed[n] += decay * echoed[n - d]
    return echoed


# ===== STEP 3: Detective work: find the echo's delay and loudness =====
def find_echo(echoed):
    """Autocorrelation: compare the sound with shifted copies of itself.
    The shift where it matches best is the echo delay."""
    centered = echoed - echoed.mean()
    size = 1 << (2 * len(centered) - 1).bit_length()
    spectrum = np.fft.rfft(centered, size)
    correlation = np.fft.irfft(spectrum * np.conj(spectrum), size)[:len(centered)]

    low, high = int(SEARCH_FROM * SAMPLE_RATE), int(SEARCH_TO * SAMPLE_RATE)
    d = low + int(np.argmax(correlation[low:high]))

    # Best decay: how much of the sound from d samples ago is inside each sample.
    now, before = echoed[d:], echoed[:-d]
    decay = float(np.dot(now, before) / np.dot(before, before))
    return d, decay, correlation


# ===== STEP 4: Build the FIR filter and use it =====
def build_filter(d, decay):
    """FIR filter taps: keep the sound (1), subtract the echo d samples later (-decay)."""
    taps = np.zeros(d + 1)
    taps[0] = 1.0
    taps[d] = -decay
    return taps


def apply_filter(signal, taps):
    """FIR filtering = convolution: every output is a weighted sum of recent inputs."""
    return np.convolve(signal, taps)[:len(signal)]


# ===== STEP 5: Measure, save, play, show =====
def echo_level_db(clean, other):
    """How loud the leftover difference from the clean voice is, in dB (lower is better)."""
    leftover = np.sum((other - clean) ** 2)
    return 10 * np.log10(leftover / np.sum(clean ** 2) + 1e-12)


def save_wav(name, audio):
    peak = np.max(np.abs(audio)) or 1.0
    data = (audio / peak * 0.9 * 32767).astype(np.int16)
    with wave.open(str(FOLDER / name), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(SAMPLE_RATE)
        file.writeframes(data.tobytes())


def play(label, audio):
    print(f"Playing: {label}")
    peak = np.max(np.abs(audio)) or 1.0
    sd.play((audio / peak * 0.8).astype(np.float32), SAMPLE_RATE)
    sd.wait()


def show(clean, echoed, filtered, taps, correlation, d):
    times = np.arange(len(clean)) / SAMPLE_RATE
    figure, axes = plt.subplots(4, 1, figsize=(10, 9))
    figure.suptitle("EchoKiller — Day 16", fontweight="bold")

    axes[0].plot(times, clean, linewidth=0.6)
    axes[0].set_title("1. Clean voice")
    axes[1].plot(times, echoed, linewidth=0.6, color="tab:orange")
    axes[1].set_title("2. With echo (the input)")
    axes[2].plot(times, filtered, linewidth=0.6, color="tab:green")
    axes[2].set_title("3. After the FIR filter (the output)")
    for axis in axes[:3]:
        axis.set_xlabel("seconds")

    lags = np.arange(len(correlation)) / SAMPLE_RATE * 1000
    shown = lags <= SEARCH_TO * 1000
    axes[3].plot(lags[shown], correlation[shown] / correlation[0], linewidth=0.8, color="gray")
    axes[3].stem([0, d / SAMPLE_RATE * 1000], [taps[0], taps[-1]], linefmt="tab:red", markerfmt="o", basefmt=" ")
    axes[3].set_title(f"4. Autocorrelation (gray) and filter taps (red): echo found at {d / SAMPLE_RATE * 1000:.0f} ms")
    axes[3].set_xlabel("delay in milliseconds")

    figure.tight_layout()
    figure.savefig(FOLDER / "echokiller.png", dpi=110)
    print("Saved echokiller.png")
    plt.show()


# ===== STEP 6: Run everything in order =====
def main():
    parser = argparse.ArgumentParser(description="Add an echo to your voice, then remove it with an FIR filter.")
    parser.add_argument("--demo", action="store_true", help="use a made-up voice instead of the microphone")
    parser.add_argument("--seconds", type=float, default=4, help="recording length")
    parser.add_argument("--delay", type=float, default=0.25, help="echo delay in seconds (0.05 to 0.6)")
    parser.add_argument("--decay", type=float, default=0.6, help="echo loudness from 0.2 to 0.9")
    parser.add_argument("--no-play", action="store_true", help="skip playing the sounds")
    options = parser.parse_args()

    if not MIN_DELAY <= options.delay <= MAX_DELAY:
        parser.error("--delay must be between 0.05 and 0.6")
    if not 0.2 <= options.decay <= 0.9:
        parser.error("--decay must be between 0.2 and 0.9")

    clean = demo_voice(options.seconds) if options.demo else record(options.seconds)
    if np.max(np.abs(clean)) < 0.01:
        print("Warning: the recording is almost silent. Check microphone permission or try --demo.")

    echoed = add_echo(clean, options.delay, options.decay)
    d, decay, correlation = find_echo(echoed)
    taps = build_filter(d, decay)
    filtered = apply_filter(echoed, taps)

    print()
    print(f"Echo added:  delay {options.delay * 1000:.0f} ms, decay {options.decay:.2f}")
    print(f"Echo found:  delay {d / SAMPLE_RATE * 1000:.0f} ms, decay {decay:.2f}")
    before = echo_level_db(clean, echoed)
    after = echo_level_db(clean, filtered)
    print(f"Echo level:  {before:.1f} dB before, {after:.1f} dB after")
    print(f"Echo reduced by {before - after:.1f} dB")
    print()

    save_wav("1_clean.wav", clean)
    save_wav("2_echo.wav", echoed)
    save_wav("3_filtered.wav", filtered)
    print("Saved 1_clean.wav, 2_echo.wav, 3_filtered.wav")

    if not options.no_play:
        play("clean voice", clean)
        play("with echo", echoed)
        play("after the filter", filtered)

    show(clean, echoed, filtered, taps, correlation, d)


if __name__ == "__main__":
    main()