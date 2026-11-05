import math
import threading
import time
from pathlib import Path

import av
import cv2
import mediapipe as mp
import numpy as np
import sounddevice as sd


FOLDER = Path(__file__).resolve().parent
SAMPLE_RATE = 44100

# Find your music beside this Python file.
music_path = next(
    (
        FOLDER / name
        for name in ("music.mp3", "music.wav", "music.m4a")
        if (FOLDER / name).is_file()
    ),
    None,
)

if music_path is None:
    raise SystemExit("Put music.mp3 beside main.py, then run again.")

# Decode the actual audio format, regardless of its filename.
print("Loading music...")
chunks = []

try:
    with av.open(str(music_path)) as container:
        resampler = av.AudioResampler(
            format="fltp",
            layout="stereo",
            rate=SAMPLE_RATE,
        )

        for frame in container.decode(audio=0):
            for converted in resampler.resample(frame):
                chunks.append(converted.to_ndarray().T.copy())

        for converted in resampler.resample(None):
            chunks.append(converted.to_ndarray().T.copy())

    if not chunks:
        raise ValueError("The file contains no readable audio.")

    audio = np.ascontiguousarray(
        np.concatenate(chunks), dtype=np.float32
    )
    audio = np.clip(audio, -1, 1) * 0.5

except Exception as error:
    raise SystemExit(
        f"Could not read {music_path.name}: {error}\n"
        "Try another playable audio file. Renaming a file does not convert it."
    )

duration = len(audio) / SAMPLE_RATE
position = 0.0
speed = 1.0
playing = False
state_lock = threading.Lock()


def play_audio(outdata, frames, timing, status):
    global position

    outdata.fill(0)

    with state_lock:
        if not playing:
            return

        indices = (
            position + np.arange(frames) * speed
        ) % len(audio)

        left = indices.astype(np.int64)
        right = (left + 1) % len(audio)
        fraction = (indices - left)[:, None]

        outdata[:] = (
            audio[left] * (1 - fraction)
            + audio[right] * fraction
        )

        position = (position + frames * speed) % len(audio)


camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not camera.isOpened():
    camera.release()
    raise SystemExit("Camera unavailable. Close other camera apps and try again.")

tracker = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

stream = None
neutral_turn = None
neutral_tilt = None
pitch = 0.0
last_seek = 0.0

print("Ready! Click the camera window to use the keyboard controls.")

try:
    stream = sd.OutputStream(
        samplerate=SAMPLE_RATE,
        channels=2,
        dtype="float32",
        callback=play_audio,
    )
    stream.start()

    while True:
        success, frame = camera.read()
        if not success:
            print("Camera stopped sending frames.")
            break

        frame = cv2.flip(frame, 1)
        height, width = frame.shape[:2]
        result = tracker.process(
            cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        )

        current_turn = None
        current_tilt = None
        message = "Show your face"

        if result.multi_face_landmarks:
            points = result.multi_face_landmarks[0].landmark

            eyes = sorted(
                [points[33], points[263]],
                key=lambda point: point.x,
            )
            left_eye, right_eye = eyes
            nose = points[1]

            eye_width = max(right_eye.x - left_eye.x, 0.001)
            center_x = (left_eye.x + right_eye.x) / 2

            current_turn = (nose.x - center_x) / eye_width
            current_tilt = math.degrees(
                math.atan2(
                    (right_eye.y - left_eye.y) * height,
                    (right_eye.x - left_eye.x) * width,
                )
            )

            for point in (left_eye, right_eye, nose):
                cv2.circle(
                    frame,
                    (int(point.x * width), int(point.y * height)),
                    5,
                    (0, 255, 0),
                    -1,
                )

            if neutral_turn is None:
                message = "Look straight ahead. Press C to calibrate."
            else:
                turn = current_turn - neutral_turn
                target_pitch = float(
                    np.clip((current_tilt - neutral_tilt) / 5, -6, 6)
                )
                pitch = 0.8 * pitch + 0.2 * target_pitch
                now = time.monotonic()
                message = "Face tracking ready"

                with state_lock:
                    speed = 2 ** (pitch / 12)

                    if abs(turn) > 0.12:
                        message = (
                            "Seeking forward" if turn > 0
                            else "Seeking backward"
                        )

                        if playing and now - last_seek > 0.5:
                            direction = 1 if turn > 0 else -1
                            position = (
                                position + direction * 2 * SAMPLE_RATE
                            ) % len(audio)
                            last_seek = now
        else:
            pitch = 0.0
            with state_lock:
                speed = 1.0

        with state_lock:
            seconds = position / SAMPLE_RATE
            is_playing = playing

        lines = [
            message,
            f"{'PLAYING' if is_playing else 'PAUSED'}",
            f"Time: {seconds:.1f} / {duration:.1f} seconds",
            f"Pitch: {pitch:+.1f} semitones",
            "C: calibrate | M: play/pause",
            "R: restart song | Q: quit",
        ]

        for index, text in enumerate(lines):
            y = 30 + index * 29
            cv2.putText(
                frame, text, (15, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (0, 0, 0), 4,
            )
            cv2.putText(
                frame, text, (15, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (255, 255, 255), 1,
            )

        cv2.imshow("FaceEQ", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        elif key == ord("c") and current_turn is not None:
            neutral_turn = current_turn
            neutral_tilt = current_tilt
            pitch = 0.0
            with state_lock:
                speed = 1.0

        elif key == ord("m"):
            with state_lock:
                playing = not playing

        elif key == ord("r"):
            with state_lock:
                position = 0.0

finally:
    if stream is not None:
        stream.stop()
        stream.close()

    camera.release()
    tracker.close()
    cv2.destroyAllWindows()
