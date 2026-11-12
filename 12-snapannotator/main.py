import sys
from pathlib import Path

import cv2
from ultralytics import YOLO


FOLDER = Path(__file__).resolve().parent
MODEL_FILE = FOLDER / "yolov8n.pt"
CONFIDENCE = 0.35
WINDOW = "SnapAnnotator"

PHOTO_PATH = FOLDER / "snap.jpg"
ANNOTATED_PATH = FOLDER / "snap_annotated.jpg"


def load_model():
    print("Loading the detector. The first run downloads about 6 MB...")

    try:
        return YOLO(str(MODEL_FILE))
    except Exception as error:
        print(f"Could not load the model: {error}")
        print("Check your internet connection for the first download.")
        return None


def open_camera():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Could not open the webcam.")
        print("On macOS, open System Settings > Privacy & Security > Camera")
        print("and allow Terminal (or VS Code), then run this again.")
        return None

    # The first frames are often dark while the camera adjusts.
    for _ in range(5):
        camera.read()

    return camera


def detect_objects(model, frame):
    results = model(frame, conf=CONFIDENCE, verbose=False)[0]
    detections = []

    for box in results.boxes:
        x1, y1, x2, y2 = (int(value) for value in box.xyxy[0].tolist())
        confidence = float(box.conf[0])
        label = results.names[int(box.cls[0])]
        detections.append((label, confidence, x1, y1, x2, y2))

    return detections


def draw_detections(frame, detections):
    annotated = frame.copy()
    height = annotated.shape[0]

    # Scale the text with the image size.
    font_scale = max(0.5, height / 900)
    thickness = max(1, height // 400)
    font = cv2.FONT_HERSHEY_SIMPLEX

    for label, confidence, x1, y1, x2, y2 in detections:
        text = f"{label} - {confidence * 100:.0f}%"

        cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 255, 255), thickness)

        (text_width, text_height), baseline = cv2.getTextSize(
            text, font, font_scale, thickness
        )

        # Put the label above the box, or inside it near the top edge.
        label_top = y1 - text_height - baseline - 6
        if label_top < 0:
            label_top = y1

        cv2.rectangle(
            annotated,
            (x1, label_top),
            (x1 + text_width + 8, label_top + text_height + baseline + 6),
            (255, 255, 255),
            -1,
        )
        cv2.putText(
            annotated,
            text,
            (x1 + 4, label_top + text_height + 2),
            font,
            font_scale,
            (20, 20, 20),
            thickness,
            cv2.LINE_AA,
        )

    return annotated


def add_hint(frame, text):
    preview = frame.copy()
    cv2.putText(
        preview,
        text,
        (15, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return preview


def snap_and_annotate(model, frame):
    cv2.imwrite(str(PHOTO_PATH), frame)
    print("\nPhoto taken. The AI is looking...")

    try:
        detections = detect_objects(model, frame)
    except Exception as error:
        print(f"Could not analyze the photo: {error}\n")
        return None

    if not detections:
        print("Nothing recognized. Try better light or a closer object.\n")
    else:
        print(f"Found {len(detections)} object(s):")
        for label, confidence, *_ in detections:
            print(f"  {label}: {confidence * 100:.0f}%")
        print()

    annotated = draw_detections(frame, detections)
    cv2.imwrite(str(ANNOTATED_PATH), annotated)

    print(f"Saved: {PHOTO_PATH.name} and {ANNOTATED_PATH.name}")
    print("Saving again replaces these files.\n")

    return annotated


def main():
    print("SnapAnnotator - Day 12")
    print("SPACE = snap a photo, Q = quit")
    print("Everything runs on your laptop. Nothing is uploaded.\n")

    model = load_model()
    if model is None:
        return

    camera = open_camera()
    if camera is None:
        return

    print("Camera ready. Click the video window, then press SPACE.\n")

    try:
        while True:
            success, frame = camera.read()

            if not success:
                print("Lost the camera image.")
                break

            cv2.imshow(WINDOW, add_hint(frame, "SPACE = snap   Q = quit"))
            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), ord("Q")):
                break

            if key == ord(" "):
                annotated = snap_and_annotate(model, frame)

                if annotated is not None:
                    cv2.imshow(
                        WINDOW,
                        add_hint(annotated, "Any key = continue   Q = quit"),
                    )
                    key = cv2.waitKey(0) & 0xFF

                    if key in (ord("q"), ord("Q")):
                        break

    except KeyboardInterrupt:
        print("\nStopping SnapAnnotator.")

    finally:
        camera.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)
        print("Goodbye!")


if __name__ == "__main__":
    sys.exit(main())