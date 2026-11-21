"""SenseDeck — Day 20: your laptop as a live sensor dashboard.

Four live panels: microphone level, camera brightness, CPU load, network speed.
Press R to record everything to a CSV file.

Run:   .venv/bin/python main.py           (real sensors)
       .venv/bin/python main.py --demo    (fake sensors, no hardware needed)
       .venv/bin/python main.py --test    (check the math)
"""

import argparse
import csv
import math
import os
import random
import sys
import threading
import time
from collections import deque
from datetime import datetime

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- settings you can change ----------------
WIDTH, HEIGHT = 1100, 720
FPS = 30
SAMPLE_RATE_HZ = 10          # how many readings per second
HISTORY_SECONDS = 60         # how much the graphs remember
LOG_EVERY = 0.5              # seconds between CSV rows while recording
MIC_FLOOR_DB = -60.0         # this quiet (dBFS) = level 0
SLOW_WINDOW = 0.5            # CPU and network are measured over this many seconds
CAMERA_INDEX = 0

# name, unit, graph min, graph max, alert above
PANELS = [
    ("mic",    "MIC · level",         "%",    0, 100, 80),
    ("camera", "CAMERA · brightness", "/255", 0, 255, None),
    ("cpu",    "CPU · load",          "%",    0, 100, 85),
    ("net",    "NETWORK · speed",     "kB/s", 0, None, None),   # None max = auto scale
]

# colors
BG = (14, 16, 20)
PANEL = (22, 25, 31)
EDGE = (44, 48, 58)
TEXT = (236, 238, 242)
DIM = (128, 134, 146)
ALERT = (239, 83, 80)
ACCENTS = {
    "mic": (102, 217, 160),
    "camera": (250, 200, 90),
    "cpu": (110, 170, 255),
    "net": (200, 140, 255),
}


# ---------------- pure math (tested) ----------------
def rms(samples):
    samples = np.asarray(samples, dtype=np.float64)
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples ** 2)))


def to_db(value):
    """Loudness in dBFS: 1.0 = 0 dB, quieter = negative."""
    return 20 * math.log10(max(value, 1e-9))


def db_to_level(db, floor=MIC_FLOOR_DB):
    """Map dBFS to 0..100 so humans can read it."""
    return max(0.0, min(100.0, (db - floor) / -floor * 100))


def luminance(frame_bgr):
    """Average brightness 0..255 using the standard eye weights."""
    f = frame_bgr.astype(np.float32)
    y = 0.114 * f[..., 0] + 0.587 * f[..., 1] + 0.299 * f[..., 2]
    return float(y.mean())


def rate(prev_bytes, now_bytes, seconds):
    """Bytes counter difference -> kB per second."""
    if seconds <= 0:
        return 0.0
    return max(0, now_bytes - prev_bytes) / 1024 / seconds


class History:
    """Rolling memory of one sensor."""

    def __init__(self, size):
        self.values = deque(maxlen=size)

    def add(self, v):
        self.values.append(v)

    def stats(self):
        if not self.values:
            return 0.0, 0.0, 0.0
        v = list(self.values)
        return min(v), sum(v) / len(v), max(v)


def graph_points(values, x, y, w, h, lo, hi):
    """Turn values into screen points inside a box (newest on the right)."""
    values = list(values)
    if len(values) < 2:
        return []
    span = (hi - lo) or 1
    step = w / (len(values) - 1)
    pts = []
    for i, v in enumerate(values):
        t = max(0.0, min(1.0, (v - lo) / span))
        pts.append((x + i * step, y + h - t * h))
    return pts


# ---------------- sensors ----------------
class MicSensor:
    def __init__(self):
        self.level = 0.0
        self.ok = False
        try:
            import sounddevice as sd
            self.stream = sd.InputStream(channels=1, samplerate=44100,
                                         blocksize=2048, callback=self._cb)
            self.stream.start()
            self.ok = True
        except Exception as e:
            print(f"[mic] off: {e}")

    def _cb(self, data, frames, t, status):
        self.level = db_to_level(to_db(rms(data[:, 0])))

    def read(self):
        return self.level

    def close(self):
        if self.ok:
            self.stream.stop()
            self.stream.close()


class CameraSensor:
    def __init__(self):
        self.value = 0.0
        self.ok = False
        self.running = True
        try:
            import cv2
            self.cap = cv2.VideoCapture(CAMERA_INDEX)
            self.ok = self.cap.isOpened()
        except Exception as e:
            print(f"[camera] off: {e}")
        if self.ok:
            threading.Thread(target=self._loop, daemon=True).start()
        else:
            print("[camera] off: could not open camera")

    def _loop(self):
        while self.running:
            got, frame = self.cap.read()
            if got:
                small = frame[::8, ::8]
                self.value = luminance(small)
            time.sleep(0.05)

    def read(self):
        return self.value

    def close(self):
        self.running = False
        if self.ok:
            time.sleep(0.1)
            self.cap.release()


class CpuSensor:
    def __init__(self):
        import psutil
        self.psutil = psutil
        psutil.cpu_percent(interval=None)   # first call primes it
        self.value = 0.0
        self.last = time.time()
        self.ok = True

    def read(self):
        # macOS updates CPU counters in steps; reading too often gives fake 0s
        now = time.time()
        if now - self.last >= SLOW_WINDOW:
            self.value = self.psutil.cpu_percent(interval=None)
            self.last = now
        return self.value

    def close(self):
        pass


class NetSensor:
    def __init__(self):
        import psutil
        self.psutil = psutil
        self.prev = self._total()
        self.prev_t = time.time()
        self.value = 0.0
        self.ok = True

    def _total(self):
        c = self.psutil.net_io_counters()
        return c.bytes_sent + c.bytes_recv

    def read(self):
        t = time.time()
        if t - self.prev_t >= SLOW_WINDOW:
            now = self._total()
            self.value = rate(self.prev, now, t - self.prev_t)
            self.prev, self.prev_t = now, t
        return self.value

    def close(self):
        pass


class FakeSensor:
    """Smooth random signal for --demo."""

    def __init__(self, kind):
        self.kind = kind
        self.t0 = time.time() + random.random() * 10
        self.ok = True

    def read(self):
        t = time.time() - self.t0
        if self.kind == "mic":
            base = 35 + 20 * math.sin(t * 0.7) + random.uniform(-8, 8)
            if int(t) % 9 == 0:
                base += 45                  # a loud clap now and then
            return max(0, min(100, base))
        if self.kind == "camera":
            return 130 + 60 * math.sin(t * 0.25) + random.uniform(-4, 4)
        if self.kind == "cpu":
            return max(0, min(100, 25 + 15 * math.sin(t * 0.4) + random.uniform(0, 30)))
        return max(0, 300 + 250 * math.sin(t * 0.9) + random.uniform(-80, 200))

    def close(self):
        pass


class FakeOff:
    ok = False

    def read(self):
        return 0.0

    def close(self):
        pass


def make_sensors(demo, no_mic, no_camera):
    if demo:
        return {k: FakeSensor(k) for k in ("mic", "camera", "cpu", "net")}
    return {
        "mic": FakeOff() if no_mic else MicSensor(),
        "camera": FakeOff() if no_camera else CameraSensor(),
        "cpu": CpuSensor(),
        "net": NetSensor(),
    }


# ---------------- CSV recorder ----------------
class Recorder:
    def __init__(self):
        self.file = None
        self.writer = None
        self.path = None
        self.rows = 0
        self.last = 0.0

    @property
    def on(self):
        return self.file is not None

    def start(self, folder=HERE):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(folder, f"sensedeck_{stamp}.csv")
        self.file = open(self.path, "w", newline="")
        self.writer = csv.writer(self.file)
        self.writer.writerow(["time", "mic_level", "camera_brightness", "cpu_percent", "net_kBps"])
        self.rows = 0
        self.last = 0.0
        print(f"[rec] recording -> {self.path}")

    def write(self, reading, now=None):
        now = time.time() if now is None else now
        if not self.on or now - self.last < LOG_EVERY:
            return
        self.last = now
        self.writer.writerow([datetime.fromtimestamp(now).isoformat(timespec="milliseconds")] +
                             [f"{reading[k]:.2f}" for k in ("mic", "camera", "cpu", "net")])
        self.rows += 1

    def stop(self):
        if self.on:
            self.file.close()
            print(f"[rec] saved {self.rows} rows -> {self.path}")
        self.file = None


# ---------------- dashboard ----------------
def run(args):
    import pygame

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SenseDeck — Day 20")
    clock = pygame.time.Clock()
    big = pygame.font.SysFont("helveticaneue,arial", 64, bold=True)
    mid = pygame.font.SysFont("helveticaneue,arial", 22, bold=True)
    small = pygame.font.SysFont("menlo,consolas,monospace", 14)

    sensors = make_sensors(args.demo, args.no_mic, args.no_camera)
    size = HISTORY_SECONDS * SAMPLE_RATE_HZ
    history = {k: History(size) for k in sensors}
    reading = {k: 0.0 for k in sensors}
    recorder = Recorder()
    paused = False
    last_sample = 0.0
    started = time.time()
    flash = ""
    flash_until = 0.0

    def note(msg):
        nonlocal flash, flash_until
        flash, flash_until = msg, time.time() + 2.5
        print(msg)

    running = True
    while running:
        now = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    if recorder.on:
                        recorder.stop()
                        note(f"Saved {os.path.basename(recorder.path)}")
                    else:
                        recorder.start()
                        note("Recording…")
                elif event.key == pygame.K_c:
                    for h in history.values():
                        h.values.clear()
                elif event.key == pygame.K_s:
                    pygame.image.save(screen, os.path.join(HERE, "sensedeck.png"))
                    note("Saved sensedeck.png")

        if not paused and now - last_sample >= 1 / SAMPLE_RATE_HZ:
            last_sample = now
            for k, s in sensors.items():
                reading[k] = float(s.read())
                history[k].add(reading[k])
            recorder.write(reading, now)

        # ---- draw ----
        screen.fill(BG)
        title = mid.render("SenseDeck", True, TEXT)
        screen.blit(title, (32, 22))
        status = "PAUSED" if paused else "LIVE" + (" · DEMO" if args.demo else "")
        screen.blit(small.render(status, True, DIM), (32 + title.get_width() + 14, 30))
        if recorder.on:
            if int(now * 2) % 2 == 0:
                pygame.draw.circle(screen, ALERT, (WIDTH - 190, 35), 7)
            screen.blit(small.render(f"REC  {recorder.rows} rows", True, ALERT), (WIDTH - 176, 27))

        pad, top = 24, 70
        pw = (WIDTH - pad * 3) // 2
        ph = (HEIGHT - top - pad * 2 - 40) // 2
        for i, (key, label, unit, lo, hi, alert) in enumerate(PANELS):
            px = pad + (i % 2) * (pw + pad)
            py = top + (i // 2) * (ph + pad)
            color = ACCENTS[key]
            value = reading[key]
            mn, avg, mx = history[key].stats()
            hot = alert is not None and value >= alert
            pygame.draw.rect(screen, PANEL, (px, py, pw, ph), border_radius=14)
            pygame.draw.rect(screen, ALERT if hot else EDGE, (px, py, pw, ph),
                             width=2 if hot else 1, border_radius=14)

            screen.blit(small.render(label.upper(), True, DIM), (px + 20, py + 16))
            if not sensors[key].ok:
                screen.blit(mid.render("off", True, DIM), (px + 20, py + 48))
                continue
            shown = f"{value:.0f}" if value >= 10 or key != "net" else f"{value:.1f}"
            num = big.render(shown, True, ALERT if hot else TEXT)
            screen.blit(num, (px + 18, py + 36))
            screen.blit(small.render(unit, True, DIM), (px + 24 + num.get_width(), py + 76))
            screen.blit(small.render(f"min {mn:.0f}   avg {avg:.0f}   max {mx:.0f}", True, DIM),
                        (px + pw - 250, py + 16))

            gx, gy, gw, gh = px + 20, py + 118, pw - 40, ph - 138
            top_val = hi if hi is not None else max(50.0, mx * 1.2)
            pygame.draw.line(screen, EDGE, (gx, gy + gh), (gx + gw, gy + gh))
            if alert is not None:
                ay = gy + gh - (alert - lo) / (top_val - lo) * gh
                for dx in range(0, gw, 12):
                    pygame.draw.line(screen, (90, 50, 52), (gx + dx, ay), (gx + dx + 6, ay))
            pts = graph_points(history[key].values, gx, gy, gw, gh, lo, top_val)
            if len(pts) >= 2:
                fill = [(x - gx, y - gy) for x, y in pts] + [(pts[-1][0] - gx, gh), (pts[0][0] - gx, gh)]
                layer = pygame.Surface((gw + 1, gh + 1), pygame.SRCALPHA)
                pygame.draw.polygon(layer, (*color, 40), fill)
                screen.blit(layer, (gx, gy))
                pygame.draw.lines(screen, color, False, pts, 2)
                pygame.draw.circle(screen, color, (int(pts[-1][0]), int(pts[-1][1])), 4)

        help_text = "R record CSV   Space pause   C clear   S screenshot   Q quit"
        if time.time() < flash_until:
            help_text = flash
        screen.blit(small.render(help_text, True, DIM), (32, HEIGHT - 34))

        pygame.display.flip()
        clock.tick(FPS)
        if args.seconds and now - started >= args.seconds:
            running = False

    recorder.stop()
    for s in sensors.values():
        s.close()
    pygame.quit()


# ---------------- self test ----------------
def self_test():
    import tempfile
    checks = []

    def check(name, ok):
        checks.append(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    print("SenseDeck self-test")
    check("RMS of a full sine wave ≈ 0.707", abs(rms(np.sin(np.linspace(0, 2 * np.pi, 10000))) - 0.7071) < 0.01)
    check("full scale = 0 dB", abs(to_db(1.0)) < 1e-9)
    check("half volume ≈ -6 dB", abs(to_db(0.5) + 6.02) < 0.01)
    check("silence -> level 0", db_to_level(to_db(0.0)) == 0)
    check("0 dB -> level 100, -30 dB -> 50", db_to_level(0) == 100 and abs(db_to_level(-30) - 50) < 1e-9)
    white = np.full((4, 4, 3), 255, np.uint8)
    black = np.zeros((4, 4, 3), np.uint8)
    check("white frame = 255, black frame = 0", abs(luminance(white) - 255) < 0.01 and luminance(black) == 0)
    green = np.zeros((4, 4, 3), np.uint8); green[..., 1] = 255
    blue = np.zeros((4, 4, 3), np.uint8); blue[..., 0] = 255
    check("green looks brighter than blue", luminance(green) > luminance(blue))
    check("2048 bytes in 2 s = 1 kB/s", rate(0, 2048, 2) == 1.0)
    h = History(3)
    for v in (5, 1, 9, 3):
        h.add(v)
    mn, avg, mx = h.stats()
    check("history keeps last 3 and gives min/avg/max", (mn, mx) == (1, 9) and abs(avg - 13 / 3) < 1e-9)
    pts = graph_points([0, 50, 100], 0, 0, 100, 100, 0, 100)
    check("graph: 0 at bottom, 100 at top, spread across width",
          pts == [(0, 100), (50, 50), (100, 0)])
    with tempfile.TemporaryDirectory() as tmp:
        r = Recorder()
        r.start(tmp)
        for i in range(5):
            r.write({"mic": 1, "camera": 2, "cpu": 3, "net": 4}, now=1000 + i * 0.3)
        r.stop()
        with open(r.path) as f:
            rows = list(csv.reader(f))
        check("CSV has header + a row every 0.5 s", rows[0][1] == "mic_level" and len(rows) == 1 + 3)
    fakes = [FakeSensor(k).read() for k in ("mic", "cpu") for _ in range(50)]
    check("demo sensors stay in 0..100", all(0 <= v <= 100 for v in fakes))

    passed = sum(checks)
    print(f"\n{passed}/{len(checks)} checks passed")
    return passed == len(checks)


def main():
    p = argparse.ArgumentParser(description="SenseDeck — live laptop sensor dashboard")
    p.add_argument("--demo", action="store_true", help="fake sensors, no hardware needed")
    p.add_argument("--test", action="store_true", help="run the math checks and exit")
    p.add_argument("--no-mic", action="store_true", help="turn the microphone panel off")
    p.add_argument("--no-camera", action="store_true", help="turn the camera panel off")
    p.add_argument("--seconds", type=float, default=0, help="quit automatically after N seconds")
    args = p.parse_args()
    if args.test:
        sys.exit(0 if self_test() else 1)
    run(args)


if __name__ == "__main__":
    main()