import math
import subprocess
import time
from pathlib import Path

import cv2
import mediapipe as mp
import pygame


def run_applescript(script):
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=3,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Volume command failed.")

    return result.stdout.strip()


def get_volume():
    return int(run_applescript("output volume of (get volume settings)"))


def set_volume(level):
    run_applescript(f"set volume output volume {int(level)}")


music_file = Path(__file__).with_name("music.wav")
if not music_file.is_file():
    raise SystemExit("Put music.wav beside main.py, then run again.")

pygame.mixer.init()
try:
    pygame.mixer.music.load(str(music_file))
    pygame.mixer.music.set_volume(0.5)
except pygame.error as error:
    pygame.mixer.quit()
    raise SystemExit(f"Could not load music.wav: {error}")

music_started = False
music_playing = False

camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

enabled = False
smoothed_level = None
last_update = 0
last_sent = None
fist_frames = 0
notice = ""

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
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = tracker.process(rgb)

            fist = False
            target = None
            status = "Show your hand"

            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]

                def point(index):
                    landmark = hand.landmark[index]
                    return (
                        landmark.x * width,
                        landmark.y * height,
                    )

                wrist = point(0)

                # A folded finger has its tip closer to the wrist
                # than its middle joint. Check all four fingers.
                folded = [
                    math.dist(point(tip), wrist)
                    < math.dist(point(joint), wrist) * 0.95
                    for tip, joint in [(8, 6), (12, 10), (16, 14), (20, 18)]
                ]

                fist = all(folded)
                status = "FIST DETECTED" if fist else "Open hand: volume held"

                mp.solutions.drawing_utils.draw_landmarks(
                    frame,
                    hand,
                    mp.solutions.hands.HAND_CONNECTIONS,
                )

                if fist:
                    palm_y = sum(
                        hand.landmark[i].y for i in [0, 5, 9, 13, 17]
                    ) / 5

                    # Top of the active area = 100%; bottom = 0%.
                    raw_level = (0.85 - palm_y) / 0.70 * 100
                    raw_level = max(0, min(100, raw_level))

                    if smoothed_level is None:
                        smoothed_level = raw_level
                    else:
                        smoothed_level = (
                            0.8 * smoothed_level + 0.2 * raw_level
                        )

                    target = round(smoothed_level)

            if fist:
                fist_frames += 1
            else:
                fist_frames = 0
                smoothed_level = None

            # Require several fist frames and limit volume updates.
            now = time.monotonic()

            if (
                enabled
                and target is not None
                and fist_frames >= 6
                and now - last_update >= 0.3
                and (last_sent is None or abs(target - last_sent) >= 2)
            ):
                try:
                    set_volume(target)
                    last_sent = target
                    notice = ""
                except (RuntimeError, subprocess.TimeoutExpired) as error:
                    print(f"Volume control error: {error}")
                    notice = "Volume command failed - see Terminal"
                    enabled = False

                last_update = now

            mode = "LIVE" if enabled else "PREVIEW"
            level_text = "--" if target is None else str(target)

            cv2.rectangle(
                frame, (0, 0), (width, 150), (25, 25, 25), -1
            )

            lines = [
                f"VolumeKnuckle | {mode}",
                status,
                f"Music: {'PLAYING' if music_playing else 'PAUSED'} | M: play/pause",
                f"Target volume: {level_text}% | E: toggle control | Q: quit",
            ]

            for row, text in enumerate(lines):
                cv2.putText(
                    frame, text, (12, 28 + row * 32),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (255, 255, 255), 1,
                )

            if notice:
                cv2.putText(
                    frame, notice, (12, height - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 200, 255), 1,
                )

            cv2.imshow("VolumeKnuckle", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            elif key == ord("m"):
                if music_playing:
                    pygame.mixer.music.pause()
                    music_playing = False
                else:
                    if not music_started:
                        pygame.mixer.music.play(-1)
                        music_started = True
                    else:
                        pygame.mixer.music.unpause()
                    music_playing = True

            elif key == ord("e"):
                if enabled:
                    enabled = False
                else:
                    try:
                        last_sent = get_volume()
                        enabled = True
                        notice = ""
                    except (
                        RuntimeError,
                        ValueError,
                        subprocess.TimeoutExpired,
                    ) as error:
                        print(f"Could not enable volume control: {error}")
                        notice = "Could not enable - see Terminal"

finally:
    camera.release()
    cv2.destroyAllWindows()
    pygame.mixer.music.stop()
    pygame.mixer.quit()