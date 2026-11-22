"""WaveCast — Day 21: send sensor data over the network, watch it on an oscilloscope.

Two programs in one file:
  sender  makes a signal (sine, square, saw, noise, or your mic) and sends it as UDP packets
  scope   receives the packets and draws them like a real oscilloscope

Run (two Terminal windows, both inside 21-wavecast):
  .venv/bin/python main.py scope
  .venv/bin/python main.py send --wave sine
Or both at once:
  .venv/bin/python main.py --demo
Check the math:
  .venv/bin/python main.py --test
"""

import argparse
import math
import os
import random
import socket
import struct
import sys
import threading
import time
from collections import deque

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- settings you can change ----------------
PORT = 5005
SAMPLE_RATE = 1000           # samples per second the sender makes
PACKET_SAMPLES = 50          # samples per packet -> 20 packets per second
BUFFER_SECONDS = 4           # how much signal the scope remembers
WIDTH, HEIGHT = 1100, 720
FPS = 60
TIME_DIVS = [5, 10, 20, 50, 100, 200, 500]       # ms per grid square
VOLT_DIVS = [0.1, 0.2, 0.5, 1.0, 2.0]            # units per grid square

# packet = header + float32 samples
MAGIC = b"WCST"
HEADER = struct.Struct("<4sIdHH")   # magic, sequence number, send time, sample rate, count

# colors
BG = (12, 14, 17)
SCREEN = (8, 10, 12)
GRID = (30, 34, 40)
AXIS = (52, 58, 68)
TRACE = (120, 240, 170)
TEXT = (232, 236, 240)
DIM = (120, 128, 140)
WARN = (240, 90, 80)
PACKET = (230, 232, 236)


# ---------------- packets (tested) ----------------
def pack(seq, samples, rate=SAMPLE_RATE, sent=None):
    samples = np.asarray(samples, dtype="<f4")
    sent = time.time() if sent is None else sent
    return HEADER.pack(MAGIC, seq, sent, rate, len(samples)) + samples.tobytes()


def unpack(data):
    """bytes -> (seq, sent_time, rate, samples) or None if it is not our packet."""
    if len(data) < HEADER.size:
        return None
    magic, seq, sent, rate, count = HEADER.unpack_from(data)
    if magic != MAGIC or len(data) != HEADER.size + count * 4:
        return None
    samples = np.frombuffer(data, dtype="<f4", offset=HEADER.size, count=count)
    return seq, sent, rate, samples


class LossCounter:
    """Uses sequence numbers to notice packets that never arrived."""

    def __init__(self):
        self.expected = None
        self.received = 0
        self.lost = 0
        self.late = 0

    def add(self, seq):
        if self.expected is None or seq == self.expected:
            self.received += 1
        elif seq > self.expected:
            self.lost += seq - self.expected
            self.received += 1
        else:                       # older than expected: arrived out of order
            self.late += 1
            self.lost = max(0, self.lost - 1)
            self.received += 1
            return
        self.expected = seq + 1

    def loss_percent(self):
        total = self.received + self.lost
        return 100 * self.lost / total if total else 0.0


# ---------------- signals (tested) ----------------
def wave(kind, t, freq=5.0, amp=1.0):
    """Value of a wave at time t (seconds)."""
    phase = (t * freq) % 1.0
    if kind == "sine":
        return amp * math.sin(2 * math.pi * phase)
    if kind == "square":
        return amp if phase < 0.5 else -amp
    if kind == "saw":
        return amp * (2 * phase - 1)
    if kind == "triangle":
        return amp * (4 * abs(phase - 0.5) - 1)
    if kind == "noise":
        return amp * (0.6 * math.sin(2 * math.pi * phase) + random.uniform(-0.4, 0.4))
    raise ValueError(f"unknown wave {kind}")


def find_trigger(samples, level=0.0):
    """Index where the signal crosses `level` going up (so the picture stands still)."""
    s = np.asarray(samples)
    hits = np.where((s[:-1] < level) & (s[1:] >= level))[0]
    return int(hits[0]) + 1 if len(hits) else None


def measure_freq(samples, rate):
    """Frequency from the distance between upward zero crossings."""
    s = np.asarray(samples) - np.mean(samples)
    hits = np.where((s[:-1] < 0) & (s[1:] >= 0))[0]
    if len(hits) < 2:
        return 0.0
    return rate / float(np.mean(np.diff(hits)))


# ---------------- sender ----------------
class MicSource:
    def __init__(self, rate):
        import sounddevice as sd
        self.queue = deque(maxlen=rate * 2)
        self.stream = sd.InputStream(channels=1, samplerate=rate, blocksize=PACKET_SAMPLES,
                                     callback=lambda d, f, t, s: self.queue.extend(d[:, 0] * 4))
        self.stream.start()

    def take(self, n):
        while len(self.queue) < n:
            time.sleep(0.002)
        return [self.queue.popleft() for _ in range(n)]


def send(host, wave_kind, freq, amp, drop, stop=None, quiet=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    mic = MicSource(SAMPLE_RATE) if wave_kind == "mic" else None
    if not quiet:
        print(f"Sending {wave_kind} to {host}:{PORT} — {SAMPLE_RATE} samples/s, "
              f"{SAMPLE_RATE // PACKET_SAMPLES} packets/s. Ctrl+C to stop.")
    seq, n = 0, 0
    start = time.time()
    try:
        while stop is None or not stop.is_set():
            if mic:
                samples = mic.take(PACKET_SAMPLES)
            else:
                samples = [wave(wave_kind, (n + i) / SAMPLE_RATE, freq, amp)
                           for i in range(PACKET_SAMPLES)]
            n += PACKET_SAMPLES
            if random.random() >= drop:             # pretend the network lost it
                sock.sendto(pack(seq, samples), (host, PORT))
            seq += 1
            if not quiet and seq % 20 == 0:
                print(f"\r  packet #{seq}   {len(pack(0, samples))} bytes each", end="", flush=True)
            if not mic:
                wait = start + n / SAMPLE_RATE - time.time()
                if wait > 0:
                    time.sleep(wait)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        sock.close()


# ---------------- scope ----------------
class Receiver:
    def __init__(self, port=PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", port))
        self.sock.settimeout(0.2)
        self.buffer = deque(maxlen=SAMPLE_RATE * BUFFER_SECONDS)
        self.rate = SAMPLE_RATE
        self.loss = LossCounter()
        self.arrivals = deque(maxlen=200)
        self.latency_ms = 0.0
        self.sender = "—"
        self.last_bytes = b""
        self.last_seq = -1
        self.last_time = 0.0
        self.lock = threading.Lock()
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(65535)
            except (socket.timeout, OSError):
                continue
            got = unpack(data)
            if got is None:
                continue
            seq, sent, rate, samples = got
            now = time.time()
            with self.lock:
                self.loss.add(seq)
                self.buffer.extend(samples.tolist())
                self.rate = rate
                self.arrivals.append(now)
                self.latency_ms = 0.9 * self.latency_ms + 0.1 * max(0, (now - sent) * 1000)
                self.sender = f"{addr[0]}:{addr[1]}"
                self.last_bytes = data[:12]
                self.last_seq = seq
                self.last_time = now

    def packets_per_second(self):
        now = time.time()
        return sum(1 for t in self.arrivals if now - t < 1.0)

    def snapshot(self):
        with self.lock:
            return np.array(self.buffer, dtype=np.float32), self.rate

    def close(self):
        self.running = False
        self.sock.close()


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def scope(seconds=0, demo_label=""):
    import pygame

    rx = Receiver()
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("WaveCast scope — Day 21")
    clock = pygame.time.Clock()
    big = pygame.font.SysFont("helveticaneue,arial", 22, bold=True)
    mono = pygame.font.SysFont("menlo,consolas,monospace", 14)
    tiny = pygame.font.SysFont("menlo,consolas,monospace", 11)

    t_index, v_index = 3, 3          # 50 ms/div, 1.0/div
    trigger = True
    frozen = None
    flash, flash_until = "", 0.0
    flying = []                      # packet boxes animating across the top
    last_seen = -1
    started = time.time()
    ip = local_ip()

    sx, sy, sw, sh = 40, 190, WIDTH - 80, HEIGHT - 270     # scope screen box
    cols, rows = 10, 8

    running = True
    while running:
        now = time.time()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif e.key == pygame.K_RIGHT:
                    t_index = min(len(TIME_DIVS) - 1, t_index + 1)
                elif e.key == pygame.K_LEFT:
                    t_index = max(0, t_index - 1)
                elif e.key == pygame.K_UP:
                    v_index = max(0, v_index - 1)
                elif e.key == pygame.K_DOWN:
                    v_index = min(len(VOLT_DIVS) - 1, v_index + 1)
                elif e.key == pygame.K_t:
                    trigger = not trigger
                elif e.key == pygame.K_SPACE:
                    frozen = None if frozen is not None else rx.snapshot()
                elif e.key == pygame.K_s:
                    pygame.image.save(screen, os.path.join(HERE, "wavecast.png"))
                    flash, flash_until = "Saved wavecast.png", now + 2.5

        data, rate = frozen if frozen is not None else rx.snapshot()
        ms_div, v_div = TIME_DIVS[t_index], VOLT_DIVS[v_index]
        window = max(2, int(rate * ms_div * cols / 1000))

        # pick what part of the buffer to show
        view = None
        if len(data) >= window:
            if trigger:
                search = data[-(window * 2):-window] if len(data) >= window * 2 else data[:-window]
                k = find_trigger(search) if len(search) > 1 else None
                if k is not None:
                    begin = len(data) - len(search) - window + k
                    view = data[begin:begin + window]
            if view is None:
                view = data[-window:]

        # ---- draw ----
        screen.fill(BG)
        screen.blit(big.render("WaveCast", True, TEXT), (40, 22))
        status = "FROZEN" if frozen is not None else ("LIVE" if now - rx.last_time < 1 else "WAITING")
        screen.blit(mono.render(status + demo_label, True, WARN if status == "WAITING" else DIM), (150, 28))
        screen.blit(mono.render(f"listening on {ip}:{PORT}", True, DIM), (WIDTH - 300, 28))

        # sender -> scope pipe with flying packets
        py = 100
        for label, x in (("sender", 40), ("scope.py", WIDTH - 180)):
            pygame.draw.rect(screen, (24, 27, 33), (x, py - 30, 140, 60), border_radius=8)
            pygame.draw.rect(screen, AXIS, (x, py - 30, 140, 60), 1, border_radius=8)
            t = mono.render(label, True, TEXT)
            screen.blit(t, (x + 70 - t.get_width() // 2, py - 8))
        for dx in range(190, WIDTH - 190, 10):
            pygame.draw.line(screen, AXIS, (dx, py), (dx + 4, py))
        if rx.last_seq != last_seen and frozen is None:
            last_seen = rx.last_seq
            if last_seen % 4 == 0:                  # draw every 4th so they don't pile up
                flying.append([now, f"#{last_seen}"])
        flying = [f for f in flying if now - f[0] < 0.6]
        for born, label in flying:
            x = 190 + (now - born) / 0.6 * (WIDTH - 420)
            pygame.draw.rect(screen, PACKET, (x, py - 10, 70, 20), border_radius=4)
            screen.blit(tiny.render(label, True, BG), (x + 7, py - 6))
        screen.blit(tiny.render(f"last header: {rx.last_bytes.hex(' ')}", True, DIM), (190, py + 22))

        # scope screen + grid
        pygame.draw.rect(screen, SCREEN, (sx, sy, sw, sh), border_radius=8)
        for c in range(1, cols):
            x = sx + c * sw / cols
            pygame.draw.line(screen, AXIS if c == cols // 2 else GRID, (x, sy), (x, sy + sh))
        for r in range(1, rows):
            y = sy + r * sh / rows
            pygame.draw.line(screen, AXIS if r == rows // 2 else GRID, (sx, y), (sx + sw, y))
        pygame.draw.rect(screen, AXIS, (sx, sy, sw, sh), 1, border_radius=8)

        if view is not None and len(view) > 1:
            mid = sy + sh / 2
            xs = np.linspace(sx, sx + sw, len(view))
            ys = np.clip(mid - view / v_div * (sh / rows), sy + 2, sy + sh - 2)
            pygame.draw.lines(screen, TRACE, False, list(zip(xs.tolist(), ys.tolist())), 2)
        else:
            msg = mono.render("No packets yet — run:  .venv/bin/python main.py send", True, DIM)
            screen.blit(msg, (sx + sw / 2 - msg.get_width() / 2, sy + sh / 2 - 8))

        # readouts
        recent = data[-rate:] if len(data) else data
        freq = measure_freq(recent, rate) if len(recent) > 10 else 0.0
        vpp = float(recent.max() - recent.min()) if len(recent) else 0.0
        loss = rx.loss.loss_percent()
        stats = [
            f"{ms_div} ms/div",
            f"{v_div} /div",
            f"trig {'ON' if trigger else 'off'}",
            f"freq {freq:.1f} Hz",
            f"Vpp {vpp:.2f}",
            f"{rx.packets_per_second()} pkt/s",
            f"lost {loss:.1f}%",
            f"delay {rx.latency_ms:.1f} ms",
        ]
        x = sx
        for s in stats:
            color = WARN if s.startswith("lost") and loss > 1 else TEXT
            img = mono.render(s, True, color)
            screen.blit(img, (x, sy + sh + 14))
            x += img.get_width() + 26
        help_text = "←/→ time   ↑/↓ volts   T trigger   Space freeze   S screenshot   Q quit"
        if now < flash_until:
            help_text = flash
        screen.blit(mono.render(help_text, True, DIM), (sx, HEIGHT - 34))
        screen.blit(tiny.render(f"from {rx.sender}", True, DIM), (WIDTH - 260, HEIGHT - 32))

        pygame.display.flip()
        clock.tick(FPS)
        if seconds and now - started >= seconds:
            running = False

    rx.close()
    pygame.quit()


# ---------------- self test ----------------
def self_test():
    checks = []

    def check(name, ok):
        checks.append(bool(ok))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    print("WaveCast self-test")
    data = pack(7, [0.5, -1.0, 2.0], sent=123.0)
    got = unpack(data)
    check("packet round trip keeps seq, time, rate, samples",
          got and got[0] == 7 and got[1] == 123.0 and got[2] == SAMPLE_RATE
          and np.allclose(got[3], [0.5, -1.0, 2.0]))
    check("header is 20 bytes, each sample 4 bytes", len(data) == 20 + 3 * 4)
    check("strangers' packets are ignored", unpack(b"HELLO" * 10) is None and unpack(data[:-2]) is None)

    lc = LossCounter()
    for s in (0, 1, 2, 5, 6):
        lc.add(s)
    check("sequence gap 3→5 counts 2 lost packets", lc.lost == 2 and lc.received == 5)
    lc.add(3)
    check("a late packet is counted as late, not lost", lc.late == 1 and lc.lost == 1)

    check("sine: 0 at start, 1 at a quarter period", abs(wave("sine", 0)) < 1e-9 and abs(wave("sine", 0.05, 5) - 1) < 1e-9)
    check("square is only +1 or -1", {wave("square", i / 100, 5) for i in range(100)} == {1.0, -1.0})
    check("saw goes from -1 up to almost +1", wave("saw", 0, 5) == -1 and wave("saw", 0.199, 5) > 0.98)

    t = np.arange(1000) / 1000
    sig = np.sin(2 * np.pi * 5 * t)
    check("measures 5 Hz from samples", abs(measure_freq(sig, 1000) - 5) < 0.05)
    k = find_trigger(np.sin(2 * np.pi * 5 * (t + 0.03)))
    check("trigger finds the upward zero crossing", k is not None and abs(k - 170) <= 1)

    # real UDP on this computer
    rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rx.bind(("127.0.0.1", 0))
    rx.settimeout(1)
    tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tx.sendto(pack(42, sig[:PACKET_SAMPLES]), rx.getsockname())
    try:
        got = unpack(rx.recvfrom(65535)[0])
    except socket.timeout:
        got = None
    rx.close()
    tx.close()
    check("a real UDP packet travels through localhost", got and got[0] == 42 and len(got[3]) == PACKET_SAMPLES)

    passed = sum(checks)
    print(f"\n{passed}/{len(checks)} checks passed")
    return passed == len(checks)


def main():
    p = argparse.ArgumentParser(description="WaveCast — UDP oscilloscope")
    p.add_argument("mode", nargs="?", choices=["scope", "send"], default="scope")
    p.add_argument("--host", default="127.0.0.1", help="where to send (the scope computer's IP)")
    p.add_argument("--wave", default="sine", choices=["sine", "square", "saw", "triangle", "noise", "mic"])
    p.add_argument("--freq", type=float, default=5.0, help="wave frequency in Hz")
    p.add_argument("--amp", type=float, default=1.0, help="wave height")
    p.add_argument("--drop", type=float, default=0.0, help="pretend to lose this share of packets, e.g. 0.1")
    p.add_argument("--demo", action="store_true", help="run sender and scope together")
    p.add_argument("--seconds", type=float, default=0, help="quit the scope after N seconds")
    p.add_argument("--test", action="store_true", help="run the checks and exit")
    a = p.parse_args()

    if a.test:
        sys.exit(0 if self_test() else 1)
    if a.demo:
        stop = threading.Event()
        threading.Thread(target=send, args=("127.0.0.1", a.wave, a.freq, a.amp, a.drop, stop, True),
                         daemon=True).start()
        scope(a.seconds, f" · DEMO {a.wave}")
        stop.set()
    elif a.mode == "send":
        send(a.host, a.wave, a.freq, a.amp, a.drop)
    else:
        scope(a.seconds)


if __name__ == "__main__":
    main()