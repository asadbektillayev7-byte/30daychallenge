import argparse
import time
from pathlib import Path

import cv2
import numpy as np


# ===== Settings =====
FOLDER = Path(__file__).resolve().parent
MODEL_PATH = FOLDER / "model-small.onnx"
MODEL_URL = "https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx"
INPUT_SIZE = 256                  # the model looks at a 256 x 256 image
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
VIEW_WIDTH = 480                  # width of each half of the window
PANEL = 64                        # height of the info strip at the bottom
SMOOTHING = 0.3                   # 0 = jumpy, closer to 1 = calm but slow
FACE_DETAIL = 0.45                # 0 = distance only, higher = more face detail in the colors
SOFTNESS = 2                      # blur of the color patches; higher looks more like a thermal camera
GRID_COLUMNS = 16                 # blocks across in grid mode
NEAR_LEVEL = 0.85                 # how close counts as "nearest object"
WINDOW = "DepthPaint - Day 18"
FONT = cv2.FONT_HERSHEY_SIMPLEX
GREEN = (160, 200, 120)           # OpenCV colors are blue, green, red
WHITE = (233, 229, 225)
DIM = (126, 116, 110)

# Thermal-camera colors from cold to hot. Each stop is (position from 0 to 1, (red, green, blue)).
THERMAL_STOPS = [
    (0.00, (0, 0, 80)),           # navy
    (0.15, (0, 40, 220)),         # blue
    (0.30, (0, 160, 255)),        # light blue
    (0.42, (0, 220, 180)),        # cyan
    (0.55, (120, 230, 0)),        # green
    (0.66, (255, 230, 0)),        # yellow
    (0.78, (255, 140, 0)),        # orange
    (0.88, (240, 20, 20)),        # red
    (0.96, (230, 0, 140)),        # magenta
    (1.00, (255, 200, 255)),      # pink-white, only the very hottest
]

# Boosts light and dark areas locally, so a face has visible detail even in dim light.
CONTRAST = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))


# ===== STEP 1: Load the depth model =====
def load_model():
    if not MODEL_PATH.exists():
        print("Model file not found. Download it inside this folder with:")
        print(f"curl -L -o model-small.onnx {MODEL_URL}")
        raise SystemExit(1)
    return cv2.dnn.readNet(str(MODEL_PATH))


# ===== STEP 2: Ask the model how close every pixel is =====
def estimate_closeness(net, image):
    """MiDaS returns bigger numbers for closer things. They are relative, not meters."""
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    small = cv2.resize(rgb, (INPUT_SIZE, INPUT_SIZE), interpolation=cv2.INTER_CUBIC)
    small = (small.astype(np.float32) / 255 - MEAN) / STD
    blob = small.transpose(2, 0, 1)[np.newaxis].astype(np.float32)
    net.setInput(blob)
    closeness = net.forward().reshape(INPUT_SIZE, INPUT_SIZE)
    return cv2.resize(closeness, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_CUBIC)


def stretch(values, low_percent=1, high_percent=99.5):
    """Rescale to 0..1 so the colors use their full range."""
    low, high = np.percentile(values, (low_percent, high_percent))
    return np.clip((values - low) / (high - low + 1e-6), 0, 1).astype(np.float32)


# ===== STEP 3: Thermal colors =====
def make_palette():
    """Blend smoothly between the color stops to make 256 colors."""
    positions = [position for position, _ in THERMAL_STOPS]
    palette = np.zeros((1, 256, 3), np.uint8)
    for channel in range(3):                       # red, green, blue
        values = [color[channel] for _, color in THERMAL_STOPS]
        palette[0, :, 2 - channel] = np.interp(np.linspace(0, 1, 256), positions, values)
    return palette                                 # stored as blue, green, red for OpenCV


PALETTE = make_palette()


def colorize(levels):
    """Turn 0..255 gray levels into thermal colors."""
    return cv2.LUT(cv2.cvtColor(levels, cv2.COLOR_GRAY2BGR), PALETTE)


# ===== STEP 4: Paint the depth map =====
def paint_heatmap(near, view):
    """Color = closeness x camera light.
    Far things stay blue. On close things, bright skin turns red and darker hair,
    eyes and glasses turn yellow and green, like a real thermal camera."""
    gray = CONTRAST.apply(cv2.cvtColor(view, cv2.COLOR_BGR2GRAY))
    light = cv2.GaussianBlur(gray.astype(np.float32) / 255, (0, 0), SOFTNESS)
    heat = near * ((1 - FACE_DETAIL) + FACE_DETAIL * light)
    return colorize((stretch(heat) * 255).astype(np.uint8))


def paint_grid(near):
    height, width = near.shape
    rows = max(1, round(GRID_COLUMNS * height / width))
    cells = cv2.resize(near, (GRID_COLUMNS, rows), interpolation=cv2.INTER_AREA)
    blocks = cv2.resize((cells * 255).astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST)
    image = cv2.cvtColor(blocks, cv2.COLOR_GRAY2BGR)
    for column in range(1, GRID_COLUMNS):
        x = column * width // GRID_COLUMNS
        cv2.line(image, (x, 0), (x, height), (20, 20, 20), 1)
    for row in range(1, rows):
        y = row * height // rows
        cv2.line(image, (0, y), (width, y), (20, 20, 20), 1)
    return image


def nearest_box(near):
    """Find the biggest blob of very close pixels and return its rectangle."""
    mask = (near > NEAR_LEVEL).astype(np.uint8)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    biggest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(biggest) < near.size * 0.01:
        return None
    return cv2.boundingRect(biggest)


def legend(width, mode):
    ramp = (np.linspace(1, 0, width) * 255).astype(np.uint8)[np.newaxis].repeat(12, axis=0)
    if mode == "heat":
        return colorize(ramp)
    return cv2.cvtColor(ramp, cv2.COLOR_GRAY2BGR)


# ===== STEP 5: Put everything in one window =====
def resize_view(image):
    height = int(image.shape[0] * VIEW_WIDTH / image.shape[1])
    return cv2.resize(image, (VIEW_WIDTH, height))


def compose(view, near, mode, fps, mouse):
    height, width = view.shape[:2]
    camera = view.copy()
    box = nearest_box(near)
    if box:
        x, y, w, h = box
        cv2.rectangle(camera, (x, y), (x + w, y + h), GREEN, 2)
        cv2.putText(camera, "NEAREST", (x, max(y - 8, 16)), FONT, 0.5, GREEN, 1, cv2.LINE_AA)

    painted = paint_heatmap(near, view) if mode == "heat" else paint_grid(near)
    canvas = np.full((height + PANEL, width * 2, 3), (24, 20, 18), np.uint8)
    canvas[:height, :width] = camera
    canvas[:height, width:] = painted

    bar = legend(width - 40, mode)
    canvas[height + 12:height + 24, width + 20:width + 20 + bar.shape[1]] = bar
    cv2.putText(canvas, "NEAR", (width + 20, height + 42), FONT, 0.4, DIM, 1, cv2.LINE_AA)
    cv2.putText(canvas, "FAR", (2 * width - 50, height + 42), FONT, 0.4, DIM, 1, cv2.LINE_AA)

    cv2.putText(canvas, "G grid/heatmap   SPACE save   Q quit", (16, height + 22), FONT, 0.45, DIM, 1, cv2.LINE_AA)
    status = f"{fps:.1f} FPS" if fps else "photo"
    cv2.putText(canvas, status, (16, height + 48), FONT, 0.45, DIM, 1, cv2.LINE_AA)

    if mouse:
        mx, my = mouse
        if width <= mx < 2 * width and my < height:
            value = near[my, mx - width]
            share = (near < value).mean() * 100
            cv2.circle(canvas, (mx, my), 6, WHITE, 2)
            text = f"closer than {share:.0f}% of the scene"
            cv2.putText(canvas, text, (150, height + 48), FONT, 0.5, WHITE, 1, cv2.LINE_AA)
    return canvas


# ===== STEP 6: Main loop =====
def run(net, image_path):
    camera, still = None, None
    if image_path:
        still = cv2.imread(str(image_path))
        if still is None:
            print(f"Could not open the image: {image_path}")
            return
    else:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("Could not open the webcam. Check camera permission, or try --image photo.jpg")
            return

    mouse = {"pos": None}
    cv2.namedWindow(WINDOW)
    cv2.setMouseCallback(WINDOW, lambda event, x, y, flags, param: mouse.update(pos=(x, y)))

    mode, smoothed, view, fps = "heat", None, None, 0.0
    last = time.monotonic()

    while True:
        if camera is not None:
            ok, frame = camera.read()
            if not ok:
                print("Could not read from the webcam.")
                break
            view = resize_view(cv2.flip(frame, 1))            # mirror, like a selfie
            near = stretch(estimate_closeness(net, view))
            smoothed = near if smoothed is None else SMOOTHING * smoothed + (1 - SMOOTHING) * near
            now = time.monotonic()
            fps = 0.9 * fps + 0.1 / max(now - last, 1e-6)
            last = now
        elif smoothed is None:
            view = resize_view(still)
            smoothed = stretch(estimate_closeness(net, view))

        canvas = compose(view, smoothed, mode, fps, mouse["pos"])
        cv2.imshow(WINDOW, canvas)

        key = cv2.waitKey(1 if camera is not None else 30) & 0xFF
        if key in (ord("q"), 27):
            break
        if key == ord("g"):
            mode = "grid" if mode == "heat" else "heat"
        if key == ord(" "):
            path = FOLDER / "depthpaint.png"
            cv2.imwrite(str(path), canvas)
            print(f"Saved {path}")
        if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
            break

    if camera is not None:
        camera.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Paint a depth map from your webcam.")
    parser.add_argument("--image", type=Path, help="use a photo instead of the webcam")
    options = parser.parse_args()
    run(load_model(), options.image)


if __name__ == "__main__":
    main()