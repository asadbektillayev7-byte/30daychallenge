# 30daychallenge

My 30-day Python learning challenge: one hour of practice each day, building small interactive projects and keeping them together in one repository.

## Projects

| Project | Folder | Progress |
| --- | --- | --- |
| Setup | [00-setup](00-setup/) | First Python program run and uploaded |
| 01 — RockLook | [01-rocklook](01-rocklook/) | Head-tracking and music-control prototype uploaded |
| 02 — AirCanvas | [02-aircanvas](02-aircanvas/) | Pinch-drawing prototype and sample image uploaded |
| 03 — VolumeKnuckle | [03-volumeknuckle](03-volumeknuckle/) | Fist-controlled Mac volume with local music playback |
| 04 — BlinkLock | [04-blinklock](04-blinklock/) | Blink and wink detection prototype |
| 05 — FaceEQ | [05-faceeq](05-faceeq/) | Head-controlled music seeking and playback pitch prototype |

## Project 01 — RockLook

RockLook uses a webcam to estimate head movement and control a local audio file.

Features:
- Detects face landmarks and shows the webcam feed.
- Calibrates a neutral head position when **C** is pressed.
- Plays music when the head tilts down.
- Pauses music when the head returns to a straight/up position or no face is detected.
- Resumes paused music without restarting the track.
- Closes the camera and audio when **Q** is pressed.

### Tools

Python 3.12, OpenCV, MediaPipe 0.10.21, NumPy, and Pygame. The pinned MediaPipe version supports the face-tracking interface used by this project.

### Setup and run

From the repository folder:

```bash
cd 01-rocklook
uv venv --python 3.12
uv pip install "mediapipe==0.10.21" "opencv-contrib-python==4.11.0.86" "numpy==1.26.4" "pygame==2.6.1"
```

For the music-control version, put a WAV audio file named `music.wav` beside `main.py`. The audio file and `.venv` stay on the local computer and should be ignored by Git.

```bash
.venv/bin/python main.py
```

Allow camera access if macOS asks. Keep the terminal open while the program runs.

### Controls

| Action | Result |
| --- | --- |
| Look straight and press **C** in the camera window | Calibrate the normal head position |
| Tilt the head down | Play or resume music |
| Return to looking straight/up | Pause music |
| Move out of the camera view | Pause music |
| Press **Q** in the camera window | Quit |

This is a simple head-movement prototype, not eye-gaze tracking. Lighting, camera angle, and posture can affect detection; press **C** again to recalibrate.

### What I practiced

- Running Python files in the correct folder.
- Using a separate Python environment for a project.
- Reading webcam frames and face landmarks.
- Using variables, conditions, loops, and smoothing.
- Connecting a detected movement to audio playback.
- Saving progress with Git commits and GitHub pushes.

## Project 02 — AirCanvas

A hand-controlled drawing app. Pinch the thumb and index fingertips together to draw, then separate them to move without leaving a line.

- Four brush colors, selected with **1–4**.
- **C** clears the drawing.
- **S** saves the canvas as `drawing.png`.
- **Q** closes the app.

Run from the repository root:

```bash
cd 02-aircanvas
.venv/bin/python main.py
```

See the [AirCanvas README](02-aircanvas/README.md) for installation, gesture instructions, troubleshooting, and an example drawing.

## Project 03 — VolumeKnuckle

Raise a closed fist to increase your Mac’s output volume and lower it to decrease it. The app starts in preview mode. Press **E** to enable gesture control, **M** to play or pause your local music, and **Q** to quit.

See the [VolumeKnuckle README](03-volumeknuckle/README.md) for setup, audio-file requirements, controls, and troubleshooting.

## Project 04 — BlinkLock

An in-app demonstration that counts three quick blinks to cover its window and detects a wink to restore it. See the [BlinkLock README](04-blinklock/README.md) for setup, controls, and limitations.

## Project 05 — FaceEQ

Turn your face to seek through a local song and tilt your head to change pitch and playback speed. Press **C** to calibrate, **M** to play or pause, **R** to restart, and **Q** to quit. See the [FaceEQ README](05-faceeq/README.md) for setup, audio formats, controls, and troubleshooting.
