import math
import time

import cv2
import mediapipe as mp


def eye_openness(points, indices):
    """Compare the eye's height with its width."""
    left, right, top, bottom = [points[i] for i in indices]

    width = math.dist((left.x, left.y), (right.x, right.y))
    height = math.dist((top.x, top.y), (bottom.x, bottom.y))

    return height / max(width, 0.0001)


# Face-landmark numbers for the two eyes.
LEFT_EYE = [33, 133, 159, 145]
RIGHT_EYE = [362, 263, 386, 374]

CLOSED_RATIO = 0.70
BLINK_WINDOW = 2.5

camera = cv2.VideoCapture(0)

locked = False
closed_frames = 0
wink_frames = 0
blink_times = []
locked_at = 0
baseline = None
current_values = None

try:
    if not camera.isOpened():
        raise RuntimeError("Could not open the webcam.")

    with mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as tracker:
        while True:
            success, frame = camera.read()

            if not success:
                print("Could not read the camera.")
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = tracker.process(rgb)

            now = time.monotonic()
            message = "Show your face"

            # Keep only blinks from the last 2.5 seconds.
            blink_times = [
                blink_time
                for blink_time in blink_times
                if now - blink_time <= BLINK_WINDOW
            ]

            current_values = None
            if results.multi_face_landmarks:
                points = results.multi_face_landmarks[0].landmark

                left_value = eye_openness(points, LEFT_EYE)
                right_value = eye_openness(points, RIGHT_EYE)

                current_values = (left_value, right_value)
                if baseline is None:
                    baseline = current_values

                left_closed = left_value < baseline[0] * CLOSED_RATIO
                right_closed = right_value < baseline[1] * CLOSED_RATIO

                if locked:
                    message = "LOCKED - wink to unlock"

                    # Wait briefly after locking so the last blink
                    # is not mistaken for a wink.
                    if now - locked_at > 1:
                        if left_closed != right_closed:
                            wink_frames += 1
                        else:
                            wink_frames = 0

                        if wink_frames >= 3:
                            locked = False
                            wink_frames = 0
                            blink_times.clear()
                else:
                    message = "Blink 3 times quickly to lock"

                    if left_closed and right_closed:
                        closed_frames += 1
                    elif not left_closed and not right_closed:
                        # Count a blink when both eyes reopen.
                        if closed_frames >= 1:
                            blink_times.append(now)

                        closed_frames = 0

                    if len(blink_times) >= 3:
                        locked = True
                        locked_at = now
                        closed_frames = 0
                        blink_times.clear()

                # Values help us adjust detection if necessary.
                cv2.putText(
                    frame,
                    f"Eyes: {left_value:.2f} / {right_value:.2f}",
                    (15, 110),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1,
                )
            else:
                closed_frames = 0
                wink_frames = 0

            if locked:
                # This covers the app view, not the macOS desktop.
                frame[:] = (30, 30, 30)

            cv2.putText(
                frame,
                message,
                (15, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 220, 255),
                2,
            )

            cv2.putText(
                frame,
                f"Blinks: {len(blink_times)}/3 | C: calibrate | Q: quit",
                (15, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1,
            )

            cv2.imshow("BlinkLock", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("c") and current_values is not None:
                baseline = current_values
                closed_frames = 0
                wink_frames = 0
                blink_times.clear()

finally:
    camera.release()
    cv2.destroyAllWindows()