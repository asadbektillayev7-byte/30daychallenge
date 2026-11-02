import math
from pathlib import Path

import cv2
import mediapipe as mp
import pygame


# Load the music file from the same folder as this script.
music_file = Path(__file__).with_name("music.wav")

if not music_file.is_file():
    raise SystemExit("Put music.wav in the same folder as main.py.")

pygame.mixer.init()
pygame.mixer.music.load(str(music_file))
pygame.mixer.music.set_volume(0.4)

camera = cv2.VideoCapture(0)

baseline = None
smooth_score = None
looking_down = False
music_started = False
music_playing = False

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
            height, width = frame.shape[:2]

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = tracker.process(rgb)

            message = "No face detected"
            current_score = None
            change = None
            face_detected = bool(results.multi_face_landmarks)

            if face_detected:
                points = results.multi_face_landmarks[0].landmark

                left = (
                    points[33].x * width,
                    points[33].y * height,
                )
                right = (
                    points[263].x * width,
                    points[263].y * height,
                )
                nose = (
                    points[1].x * width,
                    points[1].y * height,
                )

                eye_y = (left[1] + right[1]) / 2
                eye_distance = max(math.dist(left, right), 1)
                score = (nose[1] - eye_y) / eye_distance

                if smooth_score is None:
                    smooth_score = score
                else:
                    smooth_score = 0.8 * smooth_score + 0.2 * score

                current_score = smooth_score

                for x, y in (left, right, nose):
                    cv2.circle(
                        frame,
                        (int(x), int(y)),
                        5,
                        (0, 255, 0),
                        -1,
                    )

                if baseline is None:
                    message = "Look straight, then press C"
                else:
                    change = current_score - baseline

                    if change > 0.12:
                        looking_down = True
                    elif change < 0.06:
                        looking_down = False

                    if looking_down:
                        message = "LOOKING DOWN"
                    else:
                        message = "STRAIGHT / UP"
            else:
                looking_down = False
                smooth_score = None

            # Play only when calibrated and looking down.
            should_play = (
                face_detected
                and baseline is not None
                and looking_down
            )

            if should_play and not music_playing:
                if not music_started:
                    pygame.mixer.music.play(-1)
                    music_started = True
                else:
                    pygame.mixer.music.unpause()

                music_playing = True

            elif not should_play and music_playing:
                pygame.mixer.music.pause()
                music_playing = False

            music_status = "PLAYING" if music_playing else "PAUSED"

            cv2.putText(
                frame, message, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75, (0, 255, 0), 2,
            )

            cv2.putText(
                frame, f"Music: {music_status}", (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (255, 255, 255), 2,
            )

            cv2.putText(
                frame, "C: calibrate | Q: quit", (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (255, 255, 255), 2,
            )

            if change is not None:
                cv2.putText(
                    frame, f"Change: {change:.2f}", (20, 145),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (255, 255, 255), 2,
                )

            cv2.imshow("RockLook", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            elif key == ord("c") and current_score is not None:
                baseline = current_score
                looking_down = False
                pygame.mixer.music.pause()
                music_playing = False

finally:
    camera.release()
    cv2.destroyAllWindows()
    pygame.mixer.music.stop()
    pygame.mixer.quit()