# Day 04 — BlinkLock

A webcam experiment that counts blinks and uses a wink to unlock a covered application window.

## How it works

MediaPipe tracks facial landmarks. The program estimates each eye’s openness relative to its width and compares it with an open-eye baseline. Three blinks within 2.5 seconds cover the app window; after a short delay, a wink brings the camera view back. The camera continues running while the window is covered to detect the wink.

**This is an in-app demonstration. It does not lock or unlock macOS and is not a security mechanism.** Press Q to exit at any time.

## Setup on macOS

Install uv, then from the repository root run:

```bash
cd 04-blinklock
uv venv --python 3.12
uv pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python main.py
```

Allow camera access when prompted. Click the camera window, look straight with both eyes open, and press **C** to calibrate. Blink three times quickly, then wait a second and wink one eye to restore the view. Press **Q** to quit.

## Troubleshooting

- **Blinks not counted:** look straight with both eyes open and press C again. Try deliberate blinks and improve lighting.
- **Wink not detected:** wait a second after locking and hold one eye closed briefly while keeping the other open.
- **Camera unavailable:** close other apps using the webcam and check macOS camera permissions.
- **Detection varies:** the thresholds are estimates and depend on lighting, camera angle, frame rate, and the individual. The displayed eye values can help diagnose detection.

## Learning notes

Face landmarks, eye-openness ratios, calibration, timed event counting, state changes, and real-time webcam input.
