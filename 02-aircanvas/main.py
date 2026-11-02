import math
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np


COLORS = [
    (0, 0, 255),      # Red
    (0, 255, 0),      # Green
    (255, 0, 0),      # Blue
    (0, 255, 255),    # Yellow
]
COLOR_NAMES = ["Red", "Green", "Blue", "Yellow"]

color_index = 0
previous_point = None
drawing = False
canvas = None

camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

try:
    if not camera.isOpened():
        raise RuntimeError("Could not open the webcam.")

    with mp.solutions.hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    ) as tracker:
        while True:
            success, frame = camera.read()

            if not success:
                print("Could not read the camera.")
                break

            frame = cv2.flip(frame, 1)
            height, width = frame.shape[:2]

            if canvas is None or canvas.shape != frame.shape:
                canvas = np.zeros_like(frame)
                previous_point = None

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = tracker.process(rgb)
            status = "Show one hand"

            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]

                def pixel(index):
                    point = hand.landmark[index]
                    return (
                        int(point.x * width),
                        int(point.y * height),
                    )

                thumb = pixel(4)
                index_tip = pixel(8)
                wrist = pixel(0)
                middle_knuckle = pixel(9)

                # Compare the pinch gap with the size of your hand.
                hand_size = max(math.dist(wrist, middle_knuckle), 1)
                pinch_ratio = math.dist(thumb, index_tip) / hand_size

                if pinch_ratio < 0.30:
                    drawing = True
                elif pinch_ratio > 0.45:
                    drawing = False

                if drawing:
                    if previous_point is not None:
                        cv2.line(
                            canvas,
                            previous_point,
                            index_tip,
                            COLORS[color_index],
                            5,
                        )

                    cv2.circle(
                        canvas, index_tip, 2,
                        COLORS[color_index], -1,
                    )
                    previous_point = index_tip
                    status = "DRAWING"
                else:
                    previous_point = None
                    status = "Pen lifted"

                cv2.circle(
                    frame, index_tip, 9,
                    COLORS[color_index], 2,
                )
                cv2.circle(frame, thumb, 6, (255, 255, 255), 2)

            else:
                # Prevent lines joining across a lost hand detection.
                previous_point = None
                drawing = False

            display = cv2.addWeighted(frame, 0.65, canvas, 1.0, 0)

            cv2.rectangle(display, (0, 0), (width, 85), (30, 30, 30), -1)

            cv2.putText(
                display,
                "1:Red  2:Green  3:Blue  4:Yellow",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (255, 255, 255), 1,
            )

            cv2.putText(
                display,
                f"{status} | Color: {COLOR_NAMES[color_index]}",
                (10, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6, COLORS[color_index], 2,
            )

            cv2.putText(
                display,
                "C: clear | S: save drawing | Q: quit",
                (10, height - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55, (255, 255, 255), 1,
            )

            cv2.imshow("AirCanvas", display)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            elif key == ord("c"):
                canvas.fill(0)
                previous_point = None

            elif ord("1") <= key <= ord("4"):
                color_index = key - ord("1")
                previous_point = None

            elif key == ord("s"):
                output = Path(__file__).with_name("drawing.png")

                if cv2.imwrite(str(output), canvas):
                    print(f"Drawing saved to: {output}")
                else:
                    print("Could not save the drawing.")

finally:
    camera.release()
    cv2.destroyAllWindows()