import queue
import time
from collections import deque

import numpy as np
import sounddevice as sd


levels = queue.Queue()
BLOCK_SECONDS = 0.05


def listen(indata, frames, timing, status):
    volume = float(np.sqrt(np.mean(indata ** 2)))
    levels.put(volume)


def next_level():
    return levels.get(timeout=3)


try:
    with sd.InputStream(
        channels=1,
        dtype="float32",
        blocksize=800,
        samplerate=16000,
        callback=listen,
    ):
        print("BreathClock")
        print("Stay quiet for 5 seconds: measuring background noise.")

        background = []
        end = time.monotonic() + 5

        while time.monotonic() < end:
            background.append(next_level())

        noise = float(np.percentile(background, 95))

        print("\nBreathe normally near the microphone for 10 seconds.")
        print("Keep the microphone position steady.")

        breathing = []
        end = time.monotonic() + 10

        while time.monotonic() < end:
            breathing.append(next_level())

        peak = float(np.percentile(breathing, 90))
        difference = peak - noise

        if difference < max(noise * 0.3, 0.0001):
            raise SystemExit(
                "\nBreathing was too quiet compared with background noise.\n"
                "Try a quieter room or move the microphone closer, then restart."
            )

        high = noise + difference * 0.55
        low = noise + difference * 0.25

        smoothing = deque(maxlen=4)
        events = deque(maxlen=8)
        active = False
        started = 0.0
        last_event = -100.0
        count = 0
        last_display = 0.0

        print("\nListening! Stay quiet and breathe normally.")
        print("Press Control+C to stop.\n")

        while True:
            volume = next_level()
            now = time.monotonic()

            smoothing.append(volume)
            average = sum(smoothing) / len(smoothing)

            # A sustained sound starts a possible breath event.
            if not active and average > high:
                active = True
                started = now

            # Count the event when the sound returns below the threshold.
            elif active and average < low:
                active = False
                length = now - started

                if 0.2 <= length <= 4.0 and started - last_event >= 2.0:
                    count += 1
                    events.append(started)
                    last_event = started

            # Discard long sounds such as speech or continuous noise.
            if active and now - started > 4:
                active = False

            if now - last_display >= 0.1:
                last_display = now

                if len(events) >= 4 and now - events[-1] < 15:
                    intervals = np.diff(list(events))
                    bpm = 60 / float(np.median(intervals))
                    rate = f"{bpm:.1f} breaths/min"
                else:
                    rate = "Waiting for several breaths..."

                bars = min(int(average / max(high, 0.0001) * 12), 30)
                meter = "#" * bars + "-" * (30 - bars)

                line = f"[{meter}] Count: {count} | {rate}"
                print("\r" + line.ljust(100), end="", flush=True)

except KeyboardInterrupt:
    print("\nBreathClock stopped.")

except queue.Empty:
    print("\nNo microphone data received. Check your input device.")

except Exception as error:
    print(f"\nError: {error}")