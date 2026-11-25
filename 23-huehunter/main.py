"""HueHunter — Day 23: point the camera at a colored object, your code tracks it live.

Click an object to teach HueHunter its color. Every frame it finds the pixels with
that color, picks the biggest blob, follows its center, draws a trail, measures
speed, predicts where it went when it hides, and says how a robot should turn
to keep it in the middle.

Run:  .venv/bin/python main.py           (webcam)
      .venv/bin/python main.py --demo    (moving ball, no camera needed)
      .venv/bin/python main.py --test    (check the math)
"""

import argparse
import math
import os
import sys
import time
from collections import deque

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- settings you can change ----------------
CAMERA_INDEX = 0
WIDTH, HEIGHT = 960, 540
MIRROR = True             # flip the webcam like a mirror
HUE_TOL = 10              # how far the hue may differ (OpenCV hue is 0..179)
MIN_SAT, MIN_VAL = 70, 50 # ignore grey and dark pixels
MIN_AREA = 250            # blobs smaller than this (pixels) are ignored
SMOOTH = 0.45             # 0 = jumpy, 1 = frozen; how much the center is smoothed
TRAIL = 60                # points in the trail
PREDICT_FRAMES = 20       # how long to guess where a hidden object went
DEADZONE = 0.08           # "CENTERED" if closer than 8% of the frame to the middle

PRESETS = {               # key: (name, hue)
    ord("1"): ("red", 0),
    ord("2"): ("green", 60),
    ord("3"): ("blue", 110),
    ord("4"): ("yellow", 28),
}

GREEN = (140, 230, 120)
WHITE = (235, 235, 235)
DIM = (140, 140, 140)
AMBER = (60, 190, 255)
RED = (80, 80, 240)


# ---------------- color math (tested) ----------------
def hue_ranges(hue, tol=HUE_TOL, min_s=MIN_SAT, min_v=MIN_VAL):
    """One or two HSV ranges around a hue. Red sits at both ends (0 and 179), so it wraps."""
    lo, hi = hue - tol, hue + tol
    ranges = []
    if lo < 0:
        ranges += [((0, min_s, min_v), (hi, 255, 255)), ((180 + lo, min_s, min_v), (179, 255, 255))]
    elif hi > 179:
        ranges += [((lo, min_s, min_v), (179, 255, 255)), ((0, min_s, min_v), (hi - 180, 255, 255))]
    else:
        ranges.append(((lo, min_s, min_v), (hi, 255, 255)))
    return [(np.array(a, np.uint8), np.array(b, np.uint8)) for a, b in ranges]


def sample_color(hsv, x, y, r=6):
    """Average color of a small square around a click. Hue is averaged on a circle (so 178 and 2 -> 0)."""
    h, w = hsv.shape[:2]
    patch = hsv[max(0, y - r):min(h, y + r + 1), max(0, x - r):min(w, x + r + 1)].reshape(-1, 3).astype(float)
    ang = patch[:, 0] / 180 * 2 * math.pi
    hue = (math.degrees(math.atan2(np.sin(ang).mean(), np.cos(ang).mean())) / 2) % 180
    return int(round(hue)) % 180, int(patch[:, 1].mean()), int(patch[:, 2].mean())


def make_mask(hsv, ranges):
    mask = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in ranges:
        mask |= cv2.inRange(hsv, lo, hi)
    k = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)     # remove specks
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)    # fill small holes
    return mask


def find_blob(mask, min_area=MIN_AREA):
    """Biggest blob: center, box, area, and how sure we are (0..1)."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    if area < min_area:
        return None
    m = cv2.moments(c)
    cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
    x, y, w, h = cv2.boundingRect(c)
    perimeter = cv2.arcLength(c, True) or 1
    round_ = min(1.0, 4 * math.pi * area / perimeter ** 2)          # 1 = perfect circle
    solid = area / max(1.0, cv2.contourArea(cv2.convexHull(c)))     # 1 = no dents
    total = int(mask.sum() // 255)
    share = area / max(1, total)                                     # 1 = no other blobs of this color
    confidence = max(0.0, min(1.0, 0.4 * solid + 0.3 * round_ + 0.3 * share))
    return {"center": (cx, cy), "box": (x, y, w, h), "area": area, "confidence": confidence}


def steer(center, size, deadzone=DEADZONE):
    """How a camera robot should turn: error from the middle (-1..1) and words."""
    (cx, cy), (w, h) = center, size
    ex, ey = (cx - w / 2) / (w / 2), (cy - h / 2) / (h / 2)
    words = []
    if ex < -deadzone:
        words.append("LEFT")
    elif ex > deadzone:
        words.append("RIGHT")
    if ey < -deadzone:
        words.append("UP")
    elif ey > deadzone:
        words.append("DOWN")
    return ex, ey, " ".join(words) or "CENTERED"


class Tracker:
    """Smooths the center, keeps a trail, measures speed, and predicts when the object hides."""

    def __init__(self, smooth=SMOOTH):
        self.smooth = smooth
        self.pos = None
        self.vel = (0.0, 0.0)          # pixels per second
        self.trail = deque(maxlen=TRAIL)
        self.missing = 0
        self.state = "SEARCHING"

    def update(self, center, dt):
        dt = max(dt, 1e-3)
        if center is not None:
            if self.pos is None:
                new = center
            else:
                a = self.smooth
                new = (a * self.pos[0] + (1 - a) * center[0], a * self.pos[1] + (1 - a) * center[1])
                v = ((new[0] - self.pos[0]) / dt, (new[1] - self.pos[1]) / dt)
                self.vel = (0.7 * self.vel[0] + 0.3 * v[0], 0.7 * self.vel[1] + 0.3 * v[1])
            self.pos, self.missing, self.state = new, 0, "TRACK"
            self.trail.append(new)
        elif self.pos is not None:
            self.missing += 1
            if self.missing <= PREDICT_FRAMES:
                self.pos = (self.pos[0] + self.vel[0] * dt, self.pos[1] + self.vel[1] * dt)
                self.vel = (self.vel[0] * 0.9, self.vel[1] * 0.9)
                self.state = "PREDICT"
            else:
                self.pos, self.vel, self.state = None, (0.0, 0.0), "LOST"
        return self.pos

    def speed(self):
        return math.hypot(*self.vel)

    def clear(self):
        self.trail.clear()


# ---------------- demo scene ----------------
def demo_frame(t, w=WIDTH, h=HEIGHT, rng=np.random.default_rng(1)):
    """Dark room, a few distractions, an orange ball on a loop that hides behind a box."""
    y = np.linspace(40, 20, h, dtype=np.float32)[:, None, None]
    frame = np.broadcast_to(y, (h, w, 3)).copy()
    frame += rng.normal(0, 6, frame.shape).astype(np.float32)
    frame = np.clip(frame, 0, 255).astype(np.uint8)
    cv2.circle(frame, (int(w * 0.85), int(h * 0.2)), 18, (200, 120, 40), -1)      # blue dot
    cv2.rectangle(frame, (int(w * 0.1), int(h * 0.75)), (int(w * 0.16), int(h * 0.85)), (60, 160, 60), -1)
    bx = w / 2 + w * 0.32 * math.sin(t * 0.9)
    by = h / 2 + h * 0.28 * math.sin(t * 1.8 + 0.6)
    cv2.circle(frame, (int(bx), int(by)), 34, (20, 110, 245), -1)                  # orange ball
    cv2.circle(frame, (int(bx) - 10, int(by) - 12), 9, (120, 190, 255), -1)        # shine
    cv2.rectangle(frame, (int(w * 0.72), int(h * 0.3)), (int(w * 0.86), int(h * 0.75)), (70, 70, 72), -1)
    return frame


# ---------------- drawing ----------------
def corners(img, x, y, w, h, color, k=14, t=2):
    for (px, py), (dx, dy) in (((x, y), (1, 1)), ((x + w, y), (-1, 1)), ((x, y + h), (1, -1)), ((x + w, y + h), (-1, -1))):
        cv2.line(img, (px, py), (px + dx * k, py), color, t, cv2.LINE_AA)
        cv2.line(img, (px, py), (px, py + dy * k), color, t, cv2.LINE_AA)


def label(img, text, org, fg=(20, 20, 20), bg=WHITE, scale=0.45):
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
    x, y = org
    cv2.rectangle(img, (x, y - th - 6), (x + tw + 8, y + 2), bg, -1)
    cv2.putText(img, text, (x + 4, y - 3), cv2.FONT_HERSHEY_SIMPLEX, scale, fg, 1, cv2.LINE_AA)


def draw(frame, mask, blob, tracker, target, fps, show_mask, tol):
    h, w = frame.shape[:2]
    if show_mask:
        out = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    else:
        out = (frame * 0.85).astype(np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX

    # frame corners and center cross
    for px, py in ((12, 12), (w - 12, 12), (12, h - 12), (w - 12, h - 12)):
        cv2.drawMarker(out, (px, py), DIM, cv2.MARKER_CROSS, 10, 1)
    cv2.drawMarker(out, (w // 2, h // 2), DIM, cv2.MARKER_CROSS, 22, 1)

    # dotted, fading trail
    pts = list(tracker.trail)
    for i in range(1, len(pts), 2):
        fade = i / len(pts)
        cv2.circle(out, (int(pts[i][0]), int(pts[i][1])), 2, tuple(int(c * fade) for c in WHITE), -1, cv2.LINE_AA)

    if blob is not None:
        x, y, bw, bh = blob["box"]
        corners(out, x, y, bw, bh, WHITE)
        label(out, f"TRACK - {blob['confidence'] * 100:.0f}%", (x, y - 6))
    if tracker.pos is not None:
        cx, cy = int(tracker.pos[0]), int(tracker.pos[1])
        color = GREEN if tracker.state == "TRACK" else AMBER
        cv2.circle(out, (cx, cy), 5, color, -1, cv2.LINE_AA)
        if tracker.state == "PREDICT":
            cv2.circle(out, (cx, cy), 30, AMBER, 1, cv2.LINE_AA)
            label(out, "PREDICT", (cx - 30, cy - 36), bg=AMBER)
        vx, vy = tracker.vel
        if tracker.speed() > 20:
            cv2.arrowedLine(out, (cx, cy), (int(cx + vx * 0.25), int(cy + vy * 0.25)), color, 2, cv2.LINE_AA, tipLength=0.25)
        # steering: line from the middle to the object
        ex, ey, words = steer(tracker.pos, (w, h))
        cv2.line(out, (w // 2, h // 2), (cx, cy), (90, 90, 90), 1, cv2.LINE_AA)
        cv2.putText(out, f"STEER  {words}", (w - 300, h - 46), font, 0.7, color, 2, cv2.LINE_AA)
        cv2.putText(out, f"error x {ex:+.2f}  y {ey:+.2f}", (w - 300, h - 20), font, 0.5, DIM, 1, cv2.LINE_AA)

    # top-left readout
    if target:
        hh, ss, vv = target
        cv2.putText(out, f"target HSV ({hh * 2}deg, {ss * 100 // 255}%, {vv * 100 // 255}%)  tol {tol}",
                    (24, 34), font, 0.5, WHITE, 1, cv2.LINE_AA)
        swatch = cv2.cvtColor(np.uint8([[[hh, max(ss, 150), max(vv, 150)]]]), cv2.COLOR_HSV2BGR)[0, 0]
        cv2.rectangle(out, (24, 44), (54, 60), tuple(int(c) for c in swatch), -1)
    else:
        cv2.putText(out, "Click a colored object (or press 1 red, 2 green, 3 blue, 4 yellow)",
                    (24, 34), font, 0.55, AMBER, 1, cv2.LINE_AA)
    state_color = {"TRACK": GREEN, "PREDICT": AMBER}.get(tracker.state, RED)
    cv2.putText(out, tracker.state, (64, 58), font, 0.5, state_color, 1, cv2.LINE_AA)
    if tracker.pos is not None:
        cv2.putText(out, f"x {tracker.pos[0]:.0f}  y {tracker.pos[1]:.0f}   speed {tracker.speed():.0f} px/s",
                    (24, 82), font, 0.5, DIM, 1, cv2.LINE_AA)
    cv2.putText(out, f"{fps:.0f} fps", (w - 80, 34), font, 0.5, DIM, 1, cv2.LINE_AA)

    # small mask preview
    if not show_mask:
        small = cv2.resize(mask, (w // 6, h // 6))
        out[h - h // 6 - 14:h - 14, 14:14 + w // 6] = cv2.cvtColor(small, cv2.COLOR_GRAY2BGR)
        cv2.rectangle(out, (14, h - h // 6 - 14), (14 + w // 6, h - 14), DIM, 1)
        cv2.putText(out, "mask", (18, h - h // 6 - 20), font, 0.4, DIM, 1, cv2.LINE_AA)
    cv2.putText(out, "click pick  1-4 presets  [ ] tolerance  M mask  C clear  S save  Q quit",
                (w // 6 + 30, h - 20), font, 0.42, DIM, 1, cv2.LINE_AA)
    return out


# ---------------- main loop ----------------
def run(args):
    cap = None
    if not args.demo:
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            sys.exit("Could not open the camera. Allow Terminal in System Settings → Privacy & Security → Camera, "
                     "or try --demo.")

    state = {"target": None, "click": None}
    tol = HUE_TOL
    if args.demo:
        state["target"] = (12, 230, 240)          # orange, so the demo starts tracking right away

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            state["click"] = (x, y)

    cv2.namedWindow("HueHunter")
    cv2.setMouseCallback("HueHunter", on_mouse)
    tracker = Tracker()
    show_mask = False
    last = time.time()
    fps = 0.0
    start = last
    while True:
        if args.demo:
            frame = demo_frame(time.time() - start)
        else:
            ok, frame = cap.read()
            if not ok:
                continue
            frame = cv2.resize(frame, (WIDTH, HEIGHT))
            if MIRROR:
                frame = cv2.flip(frame, 1)
        hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (5, 5), 0), cv2.COLOR_BGR2HSV)

        if state["click"]:
            state["target"] = sample_color(hsv, *state["click"])
            state["click"] = None
            tracker = Tracker()
            print(f"Picked HSV {state['target']}")

        now = time.time()
        dt, last = now - last, now
        fps = 0.9 * fps + 0.1 / max(dt, 1e-3)
        if state["target"]:
            mask = make_mask(hsv, hue_ranges(state["target"][0], tol))
            blob = find_blob(mask)
        else:
            mask, blob = np.zeros(frame.shape[:2], np.uint8), None
        tracker.update(blob["center"] if blob else None, dt)

        out = draw(frame, mask, blob, tracker, state["target"], fps, show_mask, tol)
        cv2.imshow("HueHunter", out)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        if key in PRESETS:
            name, hue = PRESETS[key]
            state["target"] = (hue, 200, 200)
            tracker = Tracker()
            print(f"Preset: {name}")
        elif key == ord("]"):
            tol = min(40, tol + 2)
        elif key == ord("["):
            tol = max(2, tol - 2)
        elif key == ord("m"):
            show_mask = not show_mask
        elif key == ord("c"):
            tracker.clear()
        elif key == ord("s"):
            cv2.imwrite(os.path.join(HERE, "huehunter.png"), out)
            print("Saved huehunter.png")
        if args.seconds and now - start > args.seconds:
            break

    if cap:
        cap.release()
    cv2.destroyAllWindows()


# ---------------- self test ----------------
def self_test():
    checks = []

    def check(name, ok):
        checks.append(bool(ok))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    print("HueHunter self-test")
    check("green makes one range around 60", len(hue_ranges(60)) == 1 and hue_ranges(60)[0][0][0] == 50)
    r = hue_ranges(2)
    check("red wraps around: two ranges (0..12 and 172..179)",
          len(r) == 2 and r[0][1][0] == 12 and r[1][0][0] == 172)

    img = np.zeros((200, 300, 3), np.uint8)
    cv2.circle(img, (200, 80), 30, (0, 0, 255), -1)          # red ball
    cv2.circle(img, (60, 150), 10, (0, 0, 255), -1)          # small red dot
    cv2.circle(img, (80, 60), 30, (255, 0, 0), -1)           # blue ball
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    check("clicking the red ball picks hue 0", sample_color(hsv, 200, 80)[0] in (0, 179))
    mask = make_mask(hsv, hue_ranges(0))
    blob = find_blob(mask)
    check("finds the biggest red blob, not the blue one or the small dot",
          blob and abs(blob["center"][0] - 200) < 1.5 and abs(blob["center"][1] - 80) < 1.5)
    check("a clean round ball gets high confidence", blob["confidence"] > 0.85)
    check("nothing of that color -> no blob", find_blob(make_mask(hsv, hue_ranges(60))) is None)

    t = Tracker(smooth=0.5)
    t.update((0, 0), 0.1)
    t.update((10, 0), 0.1)
    check("smoothing moves halfway: 0 -> 10 gives 5", t.pos == (5.0, 0.0))
    t2 = Tracker(smooth=0)
    for i in range(10):
        t2.update((i * 10.0, 0.0), 0.1)
    check("speed of 10 px per 0.1 s is close to 100 px/s", 80 < t2.speed() <= 100)
    x_before = t2.pos[0]
    t2.update(None, 0.1)
    check("hidden object: PREDICT keeps moving it forward", t2.state == "PREDICT" and t2.pos[0] > x_before)
    for _ in range(PREDICT_FRAMES + 1):
        t2.update(None, 0.1)
    check("hidden too long -> LOST", t2.state == "LOST" and t2.pos is None)

    check("object left and up -> steer LEFT UP", steer((100, 50), (1000, 500))[2] == "LEFT UP")
    check("object in the middle -> CENTERED", steer((505, 252), (1000, 500))[2] == "CENTERED")

    f = demo_frame(0.0)
    b = find_blob(make_mask(cv2.cvtColor(f, cv2.COLOR_BGR2HSV), hue_ranges(12)))
    check("demo: finds the orange ball", b is not None and b["area"] > 2000)

    passed = sum(checks)
    print(f"\n{passed}/{len(checks)} checks passed")
    return passed == len(checks)


def main():
    p = argparse.ArgumentParser(description="HueHunter — track a colored object with your webcam")
    p.add_argument("--demo", action="store_true", help="moving ball, no camera needed")
    p.add_argument("--seconds", type=float, default=0, help="quit after N seconds")
    p.add_argument("--test", action="store_true", help="run the checks and exit")
    a = p.parse_args()
    if a.test:
        sys.exit(0 if self_test() else 1)
    run(a)


if __name__ == "__main__":
    main()
