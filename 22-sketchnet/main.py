"""SketchNet — Day 22: draw a circuit on paper, photograph it, AI reads it.

A local vision model (Ollama) turns your drawing into a parts list. SketchNet then
redraws it as a clean schematic, writes a SPICE netlist, and solves the circuit:
the voltage at every point and the current through every part.

Run:  .venv/bin/python main.py --demo              (built-in drawing, no AI needed)
      .venv/bin/python main.py my_circuit.jpg      (read a photo)
      .venv/bin/python main.py --camera            (snap with the webcam)
      .venv/bin/python main.py --json circuit.json (re-solve a fixed parts list, no AI)
      .venv/bin/python main.py --test              (check the math)
"""

import argparse
import base64
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- settings you can change ----------------
MODEL = "qwen2.5vl:3b"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
CAMERA_INDEX = 0
LED_DROP = 2.0         # volts an LED "eats" when it is on
DIODE_DROP = 0.7
DEFAULTS = {"resistor": 1000, "battery": 9, "led": LED_DROP, "diode": DIODE_DROP,
            "lamp": 100, "capacitor": 1e-6, "inductor": 1e-3, "switch": 0}
UNITS = {"resistor": "ohm", "battery": "V", "led": "V", "diode": "V",
         "lamp": "ohm", "capacitor": "F", "inductor": "H", "switch": ""}

PROMPT = """You are reading a hand-drawn electronic circuit in this photo.
List every component. Reply with JSON only, like this:
{"layout": "series", "components": [
  {"id": "V1", "type": "battery", "value": "5V", "from": "N1", "to": "0"},
  {"id": "R1", "type": "resistor", "value": "220 ohm", "from": "N1", "to": "0"}
]}
Rules:
- layout is "series" if every part sits on ONE single loop of wire, otherwise "parallel".
- List the parts in the order you meet them walking along the wire, starting at the battery's + side.
- type is one of: battery, resistor, led, diode, capacitor, switch, lamp, inductor.
- Every wire junction is a node. Parts touching the same wire share the same node name (N1, N2, ...).
- The wire on the battery's minus side is node "0".
- For a battery, "from" is the + side. For an LED or diode, "from" is the triangle's flat side (anode).
- Copy values written on the paper (220, 1k, 5V). If no value is written, use a typical one and add "guessed": true.
"""

# colors (BGR)
PAPER = (232, 236, 238)
INK = (60, 60, 62)
DARK = (22, 19, 17)
LINE = (225, 228, 232)
DIM = (130, 125, 120)
GREEN = (140, 230, 120)
AMBER = (80, 200, 250)
RED = (90, 90, 240)


# ---------------- reading values (tested) ----------------
PREFIX = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "μ": 1e-6, "m": 1e-3,
          "k": 1e3, "K": 1e3, "M": 1e6, "meg": 1e6}


def parse_value(text, default=0.0):
    """'4.7k' -> 4700, '2k2' -> 2200, '10uF' -> 1e-5, '5V' -> 5."""
    if isinstance(text, (int, float)):
        return float(text)
    s = str(text or "").strip()
    m = re.match(r"^(\d+)([pnuµμmkKM])(\d+)", s)          # European style 2k2
    if m:
        s = f"{m.group(1)}.{m.group(3)}{m.group(2)}"
    m = re.search(r"(\d*\.?\d+)\s*(meg|[pnuµμmkKM])?", s)
    if not m:
        return float(default)
    return float(m.group(1)) * PREFIX.get(m.group(2) or "", 1.0)


def fmt(x, unit=""):
    """4700, 'ohm' -> '4.7k ohm'"""
    if x == 0:
        return f"0 {unit}".strip()
    for p, f in (("M", 1e6), ("k", 1e3), ("", 1), ("m", 1e-3), ("u", 1e-6), ("n", 1e-9), ("p", 1e-12)):
        if abs(x) >= f:
            return f"{x / f:.3g}{p} {unit}".strip()
    return f"{x:.3g} {unit}".strip()


def extract_json(text):
    """Find the JSON object inside a model reply, even with ```fences``` or chatter."""
    text = re.sub(r"```(json)?", "", text)
    start = text.find("{")
    depth = 0
    for i in range(start, len(text)) if start >= 0 else []:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        if depth == 0:
            return json.loads(text[start:i + 1])
    raise ValueError("no JSON found in the model reply")


# ---------------- cleaning the parts list (tested) ----------------
TYPE_WORDS = {
    "resistor": ["resistor", "res", "r"], "battery": ["battery", "cell", "source", "voltage", "v", "dc"],
    "led": ["led", "light emitting"], "diode": ["diode"], "capacitor": ["capacitor", "cap", "c"],
    "switch": ["switch", "sw", "button"], "lamp": ["lamp", "bulb", "light"], "inductor": ["inductor", "coil", "l"],
}
ID_PREFIX = {"resistor": "R", "battery": "V", "led": "LED", "diode": "D", "capacitor": "C",
             "switch": "S", "lamp": "X", "inductor": "L"}
GROUND_NAMES = {"0", "GND", "GROUND", "N0", "-", "MINUS"}


def kind_of(word):
    w = str(word or "").lower().strip()
    for kind, words in TYPE_WORDS.items():
        if w in words or any(len(x) > 2 and x in w for x in words):
            return kind
    return None


def node_name(n):
    n = str(n).strip().upper()
    return "0" if n in GROUND_NAMES else n


def normalize(raw):
    """Model JSON -> clean list of parts with id, type, value, from, to."""
    items = raw.get("components", raw if isinstance(raw, list) else [])
    parts, counts = [], {}
    for item in items:
        kind = kind_of(item.get("type"))
        if kind is None:
            continue
        counts[kind] = counts.get(kind, 0) + 1
        pid = str(item.get("id") or f"{ID_PREFIX[kind]}{counts[kind]}").upper()
        value = parse_value(item.get("value"), DEFAULTS[kind])
        if kind == "switch":
            value = 0 if "open" in str(item.get("value", "")).lower() else 1
        if kind in ("resistor", "lamp", "battery") and value <= 0:
            value = DEFAULTS[kind]
        a, b = item.get("from"), item.get("to")
        parts.append({"id": pid, "type": kind, "value": value,
                      "from": node_name(a) if a not in (None, "") else None,
                      "to": node_name(b) if b not in (None, "") else None,
                      "guessed": bool(item.get("guessed"))})

    # one loop (the model said so, or gave no wiring): battery, then a chain in drawing order
    series = isinstance(raw, dict) and str(raw.get("layout", "")).lower() == "series"
    if series or any(p["from"] is None or p["to"] is None or p["from"] == p["to"] for p in parts):
        parts.sort(key=lambda p: p["type"] != "battery")
        k = len(parts)
        for i, p in enumerate(parts):
            if i == 0:
                p["from"], p["to"] = "N1", "0"
            else:
                p["from"] = f"N{i}"
                p["to"] = "0" if i == k - 1 else f"N{i + 1}"
    # make sure there is a ground node
    nodes = {p["from"] for p in parts} | {p["to"] for p in parts}
    if parts and "0" not in nodes:
        bat = next((p for p in parts if p["type"] == "battery"), parts[0])
        old = bat["to"]
        for p in parts:
            p["from"] = "0" if p["from"] == old else p["from"]
            p["to"] = "0" if p["to"] == old else p["to"]
    return parts


# ---------------- solving the circuit (tested) ----------------
def _solve_once(parts, off):
    nodes = []

    def ni(name):
        if name == "0":
            return -1
        if name not in nodes:
            nodes.append(name)
        return nodes.index(name)

    res, src = [], []        # (a, b, ohms, id) and (a, b, volts, id, kind)
    for p in parts:
        a, b, t, v = ni(p["from"]), ni(p["to"]), p["type"], p["value"]
        if t in ("resistor", "lamp"):
            res.append((a, b, max(v, 1e-6), p["id"]))
        elif t == "inductor" or (t == "switch" and v):
            res.append((a, b, 1e-3, p["id"]))
        elif t == "battery":
            src.append((a, b, v, p["id"], t))
        elif t in ("led", "diode") and p["id"] not in off:
            inner = ni(p["id"] + "#")
            src.append((a, inner, v, p["id"], t))
            res.append((inner, b, 10.0 if t == "led" else 1.0, p["id"] + "#"))
        # capacitors and open switches: no DC current, nothing to add

    n, m = len(nodes), len(src)
    A = np.zeros((n + m, n + m))
    z = np.zeros(n + m)
    for i in range(n):
        A[i, i] += 1e-12                        # tiny leak so floating wires don't crash
    for a, b, r, _ in res:
        g = 1 / r
        if a >= 0:
            A[a, a] += g
        if b >= 0:
            A[b, b] += g
        if a >= 0 and b >= 0:
            A[a, b] -= g
            A[b, a] -= g
    for k, (a, b, e, _, _) in enumerate(src):
        r = n + k
        if a >= 0:
            A[a, r] += 1
            A[r, a] += 1
        if b >= 0:
            A[b, r] -= 1
            A[r, b] -= 1
        z[r] = e
    notes = []
    try:
        x = np.linalg.solve(A, z)
    except np.linalg.LinAlgError:
        x = np.linalg.lstsq(A, z, rcond=None)[0]
        notes.append("Two batteries fight each other directly; numbers may be wrong")

    volts = {"0": 0.0}
    volts.update({name: float(x[i]) for i, name in enumerate(nodes)})
    current, power = {p["id"]: 0.0 for p in parts}, {p["id"]: 0.0 for p in parts}
    for a, b, r, pid in res:
        if pid.endswith("#"):
            continue
        i = ((x[a] if a >= 0 else 0) - (x[b] if b >= 0 else 0)) / r
        current[pid], power[pid] = float(i), float(i * i * r)
    for k, (a, b, e, pid, t) in enumerate(src):
        i = float(x[n + k])
        if t == "battery":
            current[pid], power[pid] = -i, -i * e      # current leaving the + side
        else:
            current[pid], power[pid] = i, i * e + i * i * (10.0 if t == "led" else 1.0)
    for pid in current:                         # hide the leak's nano-amps
        if abs(current[pid]) < 1e-7:
            current[pid], power[pid] = 0.0, 0.0
    return {"volts": {k: v for k, v in volts.items() if not k.endswith("#")},
            "current": current, "power": power, "notes": notes}


def solve(parts):
    """Modified nodal analysis. LEDs that would run backwards are switched off and re-solved."""
    off = set()
    for _ in range(len(parts) + 1):
        out = _solve_once(parts, off)
        backwards = [p["id"] for p in parts if p["type"] in ("led", "diode")
                     and p["id"] not in off and out["current"][p["id"]] < -1e-6]
        if not backwards:
            break
        off.update(backwards)
    for pid in sorted(off):
        out["notes"].append(f"{pid} points the wrong way, so no current flows through it")
    for p in parts:
        if p["type"] == "led" and 0 < out["current"][p["id"]] and out["current"][p["id"]] > 0.03:
            out["notes"].append(f"{p['id']} gets {fmt(out['current'][p['id']], 'A')}: too much, add a bigger resistor")
        if p["guessed"]:
            out["notes"].append(f"{p['id']} value was guessed by the AI")
    return out


def to_spice(parts):
    lines = ["* SketchNet netlist"]
    for p in parts:
        a, b, v, t = p["from"], p["to"], p["value"], p["type"]
        if t == "battery":
            lines.append(f"{p['id']} {a} {b} DC {v:g}")
        elif t == "resistor":
            lines.append(f"{p['id']} {a} {b} {v:g}")
        elif t == "capacitor":
            lines.append(f"{p['id']} {a} {b} {v:g}")
        elif t == "inductor":
            lines.append(f"{p['id']} {a} {b} {v:g}")
        elif t in ("led", "diode"):
            lines.append(f"D{p['id']} {a} {b} {t.upper()}")
        elif t == "lamp":
            lines.append(f"R{p['id']} {a} {b} {v:g} ; lamp")
        elif t == "switch":
            lines.append(f"R{p['id']} {a} {b} {'1e-3' if v else '1e12'} ; switch {'closed' if v else 'open'}")
    if any(p["type"] == "led" for p in parts):
        lines.append(".model LED D(Is=1e-20 N=1.8)")
    if any(p["type"] == "diode" for p in parts):
        lines.append(".model DIODE D")
    lines += [".op", ".end"]
    return "\n".join(lines) + "\n"


# ---------------- AI ----------------
def ask_model(image, model):
    h, w = image.shape[:2]
    scale = 1024 / max(h, w)
    if scale < 1:
        image = cv2.resize(image, (int(w * scale), int(h * scale)))
    ok, jpg = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    body = {"model": model, "stream": False, "format": "json", "options": {"temperature": 0},
            "messages": [{"role": "user", "content": PROMPT,
                          "images": [base64.b64encode(jpg.tobytes()).decode()]}]}
    req = urllib.request.Request(OLLAMA_URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.load(r)["message"]["content"]
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="ignore")
        if "not found" in detail:
            sys.exit(f"Model {model} is not downloaded. Run:  ollama pull {model}")
        sys.exit(f"Ollama error: {detail}")
    except urllib.error.URLError:
        sys.exit("Ollama is not running. Start it in another window:  ollama serve")


# ---------------- pictures ----------------
def demo_photo(size=560):
    """A fake 'phone photo' of a hand-drawn circuit: 5V battery, 220 ohm resistor, red LED."""
    rng = np.random.default_rng(3)
    img = np.full((size, size, 3), PAPER, np.uint8)
    for y in range(30, size, 28):
        cv2.line(img, (0, y), (size, y), (215, 222, 228), 1)

    def wobbly(p, q):
        pts = [np.array(p) + (np.array(q) - np.array(p)) * t + rng.normal(0, 1.2, 2) for t in np.linspace(0, 1, 12)]
        cv2.polylines(img, [np.int32(pts)], False, INK, 3, cv2.LINE_AA)

    L, R, T, B = 110, 450, 140, 420
    wobbly((L, T), (230, T))                                    # top wire to resistor
    zig = [(230 + i * 12, T + (0 if i % 2 == 0 else (-14 if i % 4 == 1 else 14))) for i in range(9)]
    cv2.polylines(img, [np.int32(zig)], False, INK, 3, cv2.LINE_AA)
    wobbly((326, T), (R, T))
    wobbly((R, T), (R, 250))                                    # right side down to LED
    tri = np.int32([(R - 22, 250), (R + 22, 250), (R, 290)])
    cv2.polylines(img, [tri], True, INK, 3, cv2.LINE_AA)
    cv2.line(img, (R - 22, 292), (R + 22, 292), INK, 3, cv2.LINE_AA)
    for k in (0, 16):
        cv2.arrowedLine(img, (R + 28, 262 + k), (R + 48, 248 + k), INK, 2, cv2.LINE_AA, tipLength=0.4)
    wobbly((R, 292), (R, B))
    wobbly((R, B), (L, B))                                      # bottom wire
    wobbly((L, B), (L, 300))                                    # left side up to battery
    cv2.line(img, (L - 14, 300), (L + 14, 300), INK, 3, cv2.LINE_AA)       # short plate (-)
    cv2.line(img, (L - 28, 284), (L + 28, 284), INK, 3, cv2.LINE_AA)       # long plate (+)
    wobbly((L, 284), (L, T))
    font = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX
    cv2.putText(img, "+", (L - 50, 280), font, 1.0, INK, 2, cv2.LINE_AA)
    cv2.putText(img, "5V", (L - 85, 320), font, 1.1, INK, 2, cv2.LINE_AA)
    cv2.putText(img, "R = 220", (215, T - 30), font, 1.1, INK, 2, cv2.LINE_AA)
    cv2.putText(img, "LED", (R + 30, 320), font, 1.0, INK, 2, cv2.LINE_AA)
    noise = rng.normal(0, 4, img.shape)
    img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return cv2.GaussianBlur(img, (3, 3), 0)


DEMO_PARTS = {"components": [
    {"id": "V1", "type": "battery", "value": "5V", "from": "N1", "to": "0"},
    {"id": "R1", "type": "resistor", "value": "220", "from": "N1", "to": "N2"},
    {"id": "LED1", "type": "led", "value": "", "from": "N2", "to": "0"},
]}


def snap_camera():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        sys.exit("Could not open the camera. Allow Terminal in System Settings → Privacy & Security → Camera.")
    shot = None
    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        view = frame.copy()
        cv2.putText(view, "Hold the drawing flat.  SPACE = snap   Q = quit", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow("SketchNet camera", view)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(" "):
            shot = frame
            break
        if key in (ord("q"), 27):
            break
    cap.release()
    cv2.destroyAllWindows()
    if shot is None:
        sys.exit("No photo taken.")
    return shot


def node_positions(names, x, y, w, h):
    """Spread nodes around a rectangle, like a hand-drawn loop."""
    k = len(names)
    if k == 1:
        return {names[0]: (x + w / 2, y + h / 2)}
    if k == 2:
        return {names[0]: (x + w / 2, y), names[1]: (x + w / 2, y + h)}
    per = 2 * (w + h)
    pos = {}
    for i, name in enumerate(names):
        d = i * per / k
        if d < w:
            p = (x + d, y)
        elif d < w + h:
            p = (x + w, y + d - w)
        elif d < 2 * w + h:
            p = (x + w - (d - w - h), y + h)
        else:
            p = (x, y + h - (d - 2 * w - h))
        pos[name] = p
    return pos


def loop_layout(parts, x, y, w, h):
    """If the circuit is one simple loop, place parts around a rectangle like a drawing.
    Returns (segments, plain_wires, node_points) or None."""
    degree = {}
    for p in parts:
        for n in (p["from"], p["to"]):
            degree[n] = degree.get(n, 0) + 1
    if not parts or any(d != 2 for d in degree.values()) or len(degree) != len(parts):
        return None
    first = next((p for p in parts if p["type"] == "battery"), parts[0])
    walk, used, node = [(first, first["to"], first["from"])], {id(first)}, first["from"]
    while len(walk) < len(parts):
        nxt = next((p for p in parts if id(p) not in used and node in (p["from"], p["to"])), None)
        if nxt is None:
            return None                      # two separate loops
        used.add(id(nxt))
        out = nxt["to"] if nxt["from"] == node else nxt["from"]
        walk.append((nxt, node, out))
        node = out
    TL, TR, BR, BL = (x, y), (x + w, y), (x + w, y + h), (x, y + h)
    rest = len(walk) - 1
    counts = [rest // 3 + (1 if i < rest % 3 else 0) for i in range(3)]
    spots = [(BL, TL)]                       # battery on the left side, + at the top
    plain = []
    for (a, b), c in zip(((TL, TR), (TR, BR), (BR, BL)), counts):
        if c == 0:
            plain.append((a, b))
        for k in range(c):
            pa = (a[0] + (b[0] - a[0]) * k / c, a[1] + (b[1] - a[1]) * k / c)
            pb = (a[0] + (b[0] - a[0]) * (k + 1) / c, a[1] + (b[1] - a[1]) * (k + 1) / c)
            spots.append((pa, pb))
    segs, points = [], {}
    for (part, enter, out), (pa, pb) in zip(walk, spots):
        points.setdefault(enter, pa)
        points.setdefault(out, pb)
        A, B = (pa, pb) if part["from"] == enter else (pb, pa)
        segs.append((part, A, B))
    return segs, plain, points


def ip(p):
    return int(round(p[0])), int(round(p[1]))


def draw_symbol(img, A, B, part, amps, center):
    A, B = np.array(A, float), np.array(B, float)
    L = np.linalg.norm(B - A)
    if L < 1:
        return
    u = (B - A) / L
    v = np.array([-u[1], u[0]])
    c = (A + B) / 2

    def P(s, t):
        return ip(c + u * s + v * t)

    t = part["type"]
    half = 30 if L > 80 else L / 3
    cv2.line(img, ip(A), P(-half, 0), LINE, 2, cv2.LINE_AA)
    cv2.line(img, P(half, 0), ip(B), LINE, 2, cv2.LINE_AA)
    lit = amps > 1e-3
    if t == "resistor":
        pts = [P(-half + i * (2 * half / 8), 0 if i in (0, 8) else (9 if i % 2 else -9)) for i in range(9)]
        cv2.polylines(img, [np.int32(pts)], False, LINE, 2, cv2.LINE_AA)
    elif t == "battery":
        cv2.line(img, P(-half, 0), P(-5, 0), LINE, 2, cv2.LINE_AA)
        cv2.line(img, P(5, 0), P(half, 0), LINE, 2, cv2.LINE_AA)
        cv2.line(img, P(-5, -16), P(-5, 16), LINE, 2, cv2.LINE_AA)       # long plate = +
        cv2.line(img, P(5, -8), P(5, 8), LINE, 3, cv2.LINE_AA)
        cv2.putText(img, "+", P(-18, -20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, LINE, 1, cv2.LINE_AA)
    elif t in ("led", "diode"):
        tri = np.int32([P(-12, -12), P(-12, 12), P(10, 0)])
        cv2.line(img, P(-half, 0), P(-12, 0), LINE, 2, cv2.LINE_AA)
        cv2.line(img, P(10, 0), P(half, 0), LINE, 2, cv2.LINE_AA)
        if t == "led" and lit:
            cv2.fillPoly(img, [tri], GREEN)
        cv2.polylines(img, [tri], True, LINE, 2, cv2.LINE_AA)
        cv2.line(img, P(10, -12), P(10, 12), LINE, 2, cv2.LINE_AA)
        if t == "led":
            for k in (-4, 6):
                cv2.arrowedLine(img, P(k, -14), P(k + 8, -24), GREEN if lit else DIM, 1, cv2.LINE_AA, tipLength=0.4)
    elif t == "capacitor":
        cv2.line(img, P(-half, 0), P(-5, 0), LINE, 2, cv2.LINE_AA)
        cv2.line(img, P(5, 0), P(half, 0), LINE, 2, cv2.LINE_AA)
        cv2.line(img, P(-5, -13), P(-5, 13), LINE, 2, cv2.LINE_AA)
        cv2.line(img, P(5, -13), P(5, 13), LINE, 2, cv2.LINE_AA)
    elif t == "switch":
        cv2.circle(img, P(-18, 0), 3, LINE, -1)
        cv2.circle(img, P(18, 0), 3, LINE, -1)
        cv2.line(img, P(-half, 0), P(-18, 0), LINE, 2, cv2.LINE_AA)
        cv2.line(img, P(18, 0), P(half, 0), LINE, 2, cv2.LINE_AA)
        cv2.line(img, P(-18, 0), P(16, 0 if part["value"] else -16), LINE, 2, cv2.LINE_AA)
    elif t == "lamp":
        if lit:
            cv2.circle(img, P(0, 0), 14, AMBER, -1)
        cv2.circle(img, P(0, 0), 14, LINE, 2, cv2.LINE_AA)
        cv2.line(img, P(-10, -10), P(10, 10), LINE, 2, cv2.LINE_AA)
        cv2.line(img, P(-10, 10), P(10, -10), LINE, 2, cv2.LINE_AA)
    elif t == "inductor":
        for k in range(4):
            cv2.ellipse(img, P(-22 + k * 15, 0), (7, 7), math.degrees(math.atan2(u[1], u[0])), 180, 360, LINE, 2, cv2.LINE_AA)
    # label on the outside
    side = 1 if np.dot(v, c - np.array(center)) >= 0 else -1
    out = v * side                            # direction pointing away from the middle
    label = [part["id"] + ("?" if part["guessed"] else "")]
    if t != "switch":
        label.append(fmt(part["value"], UNITS[t]))
    label.append(fmt(abs(amps), "A"))
    block = 15 * len(label)
    for i, text in enumerate(label):
        tw = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)[0][0]
        if abs(out[0]) > abs(out[1]):         # part is vertical: text beside it
            x = c[0] + out[0] * 40 - (tw if out[0] < 0 else 0)
            y = c[1] - block / 2 + 11 + i * 15
        else:                                 # part is horizontal: text above or below
            x = c[0] - tw / 2
            y = c[1] + out[1] * 34 + (-block + 11 if out[1] < 0 else 0) + i * 15
        cv2.putText(img, text, ip((x, y)), cv2.FONT_HERSHEY_SIMPLEX, 0.42,
                    LINE if i < len(label) - 1 else GREEN, 1, cv2.LINE_AA)


def render(photo, parts, result):
    W, H = 1200, 660
    img = np.full((H, W, 3), (14, 12, 11), np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    # left: the photo
    box = 560
    ph, pw = photo.shape[:2]
    s = box / max(ph, pw)
    small = cv2.resize(photo, (int(pw * s), int(ph * s)))
    left = np.full((box, box, 3), PAPER, np.uint8)
    oy, ox = (box - small.shape[0]) // 2, (box - small.shape[1]) // 2
    left[oy:oy + small.shape[0], ox:ox + small.shape[1]] = small
    img[60:60 + box, 20:20 + box] = left
    cv2.putText(img, "HAND-DRAWN", (20, 45), font, 0.45, DIM, 1, cv2.LINE_AA)
    # right: the digital schematic
    rx, ry, rw, rh = 620, 60, 560, 560
    cv2.rectangle(img, (rx, ry), (rx + rw, ry + rh), DARK, -1)
    cv2.rectangle(img, (rx, ry), (rx + rw, ry + rh), (70, 66, 62), 1)
    cv2.circle(img, (rx + 6, 41), 3, GREEN, -1)
    cv2.putText(img, "DIGITAL - parsed", (rx + 16, 45), font, 0.45, DIM, 1, cv2.LINE_AA)
    cv2.putText(img, "SketchNet", (W - 130, 45), font, 0.6, LINE, 1, cv2.LINE_AA)

    names = []
    for p in parts:
        for n in (p["from"], p["to"]):
            if n not in names:
                names.append(n)
    if "0" in names:
        names.remove("0")
        names.append("0")
    gx, gy, gw, gh = rx + 120, ry + 90, rw - 240, rh - 300
    center = (gx + gw / 2, gy + gh / 2)
    loop = loop_layout(parts, gx, gy, gw, gh)
    if loop:
        segs, plain, pos = loop
        for a, b in plain:
            cv2.line(img, ip(a), ip(b), LINE, 2, cv2.LINE_AA)
        for p, A, B in segs:
            draw_symbol(img, A, B, p, result["current"][p["id"]], center)
        groups = {}
    else:
        pos = node_positions(names, gx, gy, gw, gh)
        groups = {}
        for p in parts:
            groups.setdefault(frozenset((p["from"], p["to"])), []).append(p)
    for group in groups.values():
        g = len(group)
        ends = sorted((group[0]["from"], group[0]["to"]))      # same side order for every part
        d = np.array(pos[ends[1]]) - np.array(pos[ends[0]])
        n = np.array([-d[1], d[0]]) / (np.linalg.norm(d) or 1)
        for j, p in enumerate(group):
            a, b = np.array(pos[p["from"]]), np.array(pos[p["to"]])
            off = n * (j - (g - 1) / 2) * 150
            a2, b2 = a + off, b + off
            if g > 1:
                cv2.line(img, ip(a), ip(a2), LINE, 2, cv2.LINE_AA)
                cv2.line(img, ip(b2), ip(b), LINE, 2, cv2.LINE_AA)
            draw_symbol(img, a2, b2, p, result["current"][p["id"]], center)
    for name, p in pos.items():
        cv2.circle(img, ip(p), 5, LINE, -1, cv2.LINE_AA)
        v = result["volts"].get(name, 0.0)
        tag = f"{'GND' if name == '0' else name}  {v:.2f}V"
        dx = 10 if p[0] >= center[0] else -10 - cv2.getTextSize(tag, font, 0.4, 1)[0][0]
        dy = -10 if p[1] <= center[1] else 20
        cv2.putText(img, tag, (int(p[0] + dx), int(p[1] + dy)), font, 0.4, AMBER, 1, cv2.LINE_AA)

    # summary under the schematic
    vals = "   ".join(f"{p['id']} = {fmt(p['value'], UNITS[p['type']])}" for p in parts if p["type"] != "switch")
    y = ry + rh - 120
    cv2.putText(img, vals[:70], (rx + 24, y), font, 0.5, LINE, 1, cv2.LINE_AA)
    bat = [p for p in parts if p["type"] == "battery"]
    if bat:
        i = result["current"][bat[0]["id"]]
        total_p = sum(result["power"][p["id"]] for p in bat)
        cv2.putText(img, f"battery current {fmt(i, 'A')}    power {fmt(total_p, 'W')}", (rx + 24, y + 26),
                    font, 0.5, GREEN, 1, cv2.LINE_AA)
    for k, note in enumerate(result["notes"][:2]):
        cv2.putText(img, "! " + note[:72], (rx + 24, y + 52 + k * 20), font, 0.42, RED, 1, cv2.LINE_AA)
    cv2.putText(img, f"NETLIST GENERATED - {len(names)} nodes - {len(parts)} parts", (rx + 24, ry + rh - 16),
                font, 0.38, DIM, 1, cv2.LINE_AA)
    return img


# ---------------- report ----------------
def report(parts, result):
    print("\nParts found")
    print(f"  {'id':<6}{'type':<11}{'value':<12}{'from':<6}{'to':<6}{'current':<12}{'power'}")
    for p in parts:
        print(f"  {p['id'] + ('?' if p['guessed'] else ''):<6}{p['type']:<11}"
              f"{fmt(p['value'], UNITS[p['type']]) if p['type'] != 'switch' else ('closed' if p['value'] else 'open'):<12}"
              f"{p['from']:<6}{p['to']:<6}{fmt(abs(result['current'][p['id']]), 'A'):<12}"
              f"{fmt(abs(result['power'][p['id']]), 'W')}")
    print("\nVoltage at each point")
    for name, v in result["volts"].items():
        print(f"  {'GND' if name == '0' else name:<6}{v:7.3f} V")
    for note in result["notes"]:
        print(f"  ! {note}")


# ---------------- self test ----------------
def self_test():
    checks = []

    def check(name, ok):
        checks.append(bool(ok))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    def near(a, b, tol=1e-3):
        return abs(a - b) <= tol * max(1, abs(b))

    print("SketchNet self-test")
    check("reads 220, 4.7k, 2k2, 1M, 10uF, 5V",
          np.allclose([parse_value(x) for x in ("220 ohm", "4.7k", "2k2", "1M", "10uF", "5V")],
                      [220, 4700, 2200, 1e6, 1e-5, 5]))
    check("formats 4700 ohm as 4.7k ohm and 0.0227 A as 22.7m A",
          fmt(4700, "ohm") == "4.7k ohm" and fmt(0.0227, "A") == "22.7m A")
    reply = 'Sure! Here it is:\n```json\n{"components": [{"type": "Resistor", "value": "1k"}]}\n```'
    check("finds JSON inside a chatty reply", extract_json(reply)["components"][0]["value"] == "1k")

    loop = normalize({"components": [{"type": "resistor", "value": "220"}, {"type": "9V battery"}]})
    check("no wiring given -> battery first, one loop",
          loop[0]["type"] == "battery" and loop[0]["from"] == "N1" and loop[1]["to"] == "0" and loop[0]["id"] == "V1")

    def circuit(*items):
        return normalize({"components": [dict(zip(("type", "value", "from", "to"), it)) for it in items]})

    r = solve(circuit(("battery", "5V", "N1", "0"), ("resistor", "220", "N1", "0")))
    check("5 V across 220 ohm -> 22.7 mA (Ohm's law)", near(r["current"]["R1"], 5 / 220))
    r = solve(circuit(("battery", "10", "A", "GND"), ("resistor", "1k", "A", "B"), ("resistor", "1k", "B", "GND")))
    check("two equal resistors split 10 V into 5 V", near(r["volts"]["B"], 5.0))
    r = solve(circuit(("battery", "6", "A", "0"), ("resistor", "1k", "A", "0"), ("resistor", "1k", "A", "0")))
    check("two 1k in parallel draw 12 mA from 6 V", near(r["current"]["V1"], 0.012))
    r = solve(normalize(DEMO_PARTS))
    check("demo: 5 V, 220 ohm, LED -> about 13 mA, LED lit",
          0.012 < r["current"]["LED1"] < 0.014 and near(r["current"]["R1"], r["current"]["LED1"]))
    r = solve(circuit(("battery", "5", "A", "0"), ("resistor", "220", "A", "B"), ("led", "", "0", "B")))
    check("backwards LED -> no current and a warning",
          abs(r["current"]["LED1"]) < 1e-6 and any("wrong way" in n for n in r["notes"]))
    r = solve(circuit(("battery", "9", "A", "0"), ("capacitor", "10u", "A", "B"), ("resistor", "1k", "B", "0")))
    check("capacitor blocks DC: no current", abs(r["current"]["R1"]) < 1e-6)
    net = to_spice(normalize(DEMO_PARTS))
    check("SPICE netlist lines look right", "V1 N1 0 DC 5" in net and "R1 N1 N2 220" in net and net.endswith(".end\n"))
    parts = normalize(DEMO_PARTS)
    wrong = normalize({"layout": "series", "components": [
        {"type": "battery", "value": "10V", "from": "N1", "to": "0"},
        {"type": "resistor", "value": "220", "from": "N1", "to": "0"},
        {"type": "led", "from": "0", "to": "N1"}]})
    check("layout 'series' rebuilds one loop: 10 V, 220 ohm, LED -> 35 mA",
          [p["type"] for p in wrong] == ["battery", "resistor", "led"]
          and wrong[2]["to"] == "0" and abs(solve(wrong)["current"]["LED1"] - 8 / 230) < 1e-4)
    lay = loop_layout(parts, 0, 0, 100, 100)
    check("simple loop is laid out as a rectangle, battery on the left",
          lay is not None and lay[0][0][0]["type"] == "battery" and lay[0][0][1] == (0, 0))
    img = render(demo_photo(), parts, solve(parts))
    check("picture is drawn (1200 x 660)", img.shape == (660, 1200, 3))

    passed = sum(checks)
    print(f"\n{passed}/{len(checks)} checks passed")
    return passed == len(checks)


def main():
    p = argparse.ArgumentParser(description="SketchNet — photo of a hand-drawn circuit -> schematic, netlist, and answers")
    p.add_argument("image", nargs="?", help="photo of your drawing (jpg or png)")
    p.add_argument("--camera", action="store_true", help="take the photo with the webcam")
    p.add_argument("--demo", action="store_true", help="use the built-in drawing, no AI needed")
    p.add_argument("--demo-ai", action="store_true", help="send the built-in drawing to the AI")
    p.add_argument("--json", help="skip the AI and use this parts file (e.g. a fixed circuit.json)")
    p.add_argument("--model", default=MODEL, help=f"Ollama vision model (default {MODEL})")
    p.add_argument("--no-window", action="store_true", help="save files but do not open a window")
    p.add_argument("--test", action="store_true", help="run the checks and exit")
    a = p.parse_args()

    if a.test:
        sys.exit(0 if self_test() else 1)

    if a.demo or a.demo_ai:
        photo = demo_photo()
    elif a.camera:
        photo = snap_camera()
    elif a.image:
        photo = cv2.imread(a.image)
        if photo is None:
            sys.exit(f"Could not open {a.image}")
    elif a.json:
        photo = np.full((560, 560, 3), PAPER, np.uint8)
    else:
        p.print_help()
        sys.exit("\nGive a photo, or use --camera, --demo, or --json.")

    if a.json:
        with open(a.json) as f:
            raw = json.load(f)
    elif a.demo:
        raw = DEMO_PARTS
    else:
        print(f"Asking {a.model} to read the drawing (first run can take a minute)...")
        reply = ask_model(photo, a.model)
        try:
            raw = extract_json(reply)
        except (ValueError, json.JSONDecodeError):
            sys.exit(f"The model did not answer with JSON. It said:\n{reply[:500]}")

    parts = normalize(raw)
    if not parts:
        sys.exit("No circuit parts found. Draw darker lines, write values clearly, and try again.")
    result = solve(parts)
    report(parts, result)

    with open(os.path.join(HERE, "circuit.json"), "w") as f:
        json.dump({"components": [{k: p[k] for k in ("id", "type", "value", "from", "to")} for p in parts]}, f, indent=2)
    with open(os.path.join(HERE, "circuit.cir"), "w") as f:
        f.write(to_spice(parts))
    img = render(photo, parts, result)
    cv2.imwrite(os.path.join(HERE, "sketchnet.png"), img)
    print("\nSaved sketchnet.png, circuit.cir (SPICE netlist), circuit.json (edit it and rerun with --json)")
    if not a.no_window:
        cv2.imshow("SketchNet", img)
        print("Press any key in the window to close.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
