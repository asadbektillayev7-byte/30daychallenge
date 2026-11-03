# Day 03 — VolumeKnuckle

Control your Mac’s output volume by raising and lowering a closed fist, with optional local music playback.

## Features

- Tracks one hand through the webcam and detects folded fingers.
- Maps fist height to an output-volume target from 0 to 100 percent.
- Starts in preview mode; volume control is enabled explicitly.
- Holds volume when the hand is open or no longer visible.
- Smooths the target and limits how often volume commands run.
- Plays, pauses, and resumes a looping local music file.

## Setup (macOS)

Install uv, then run from the repository root:

```bash
cd 03-volumeknuckle
uv venv --python 3.12
uv pip install -r requirements.txt
```

Place a genuine WAV audio file named `music.wav` beside `main.py`. Audio files are excluded from Git and must be supplied separately. Renaming an MP3 or M4A file to `.wav` does not convert its format.

## Run

```bash
.venv/bin/python main.py
```

Allow camera access when prompted. Close other apps using the camera, and keep Terminal open while the program runs.

## Controls

Click the camera window before pressing keys. Use lowercase keys without Shift.

| Action | Result |
| --- | --- |
| Close the four fingers into a fist | Show the volume target |
| Raise the fist | Increase the target |
| Lower the fist | Decrease the target |
| Open the hand or move out of view | Hold the current volume |
| E | Toggle preview/live volume control |
| M | Start or pause/resume music |
| Q | Quit and stop playback |

Start with your fist low before enabling live control. Music playback and volume control are independent: M controls playback, while E controls whether gestures change system volume. Quitting leaves the Mac at its last volume setting. System mute remains separate.

## How it works

MediaPipe locates hand landmarks. The program compares fingertip and finger-joint distances from the wrist to estimate whether the hand is closed. The palm’s vertical position becomes a smoothed percentage target. Python calls macOS’s built-in AppleScript volume command to apply that value. Pygame handles the local music track.

## Troubleshooting

- **Missing `.venv/bin/python`:** run the setup commands inside this project folder.
- **Missing `music.wav`:** put the audio file beside `main.py`.
- **Audio decoder error:** use a valid WAV export rather than changing a file extension.
- **Fist not detected:** face the palm toward the webcam, keep the whole hand visible, and improve lighting. Detection is a simple heuristic and may vary with hand angle.
- **Volume does not change:** press E, check that LIVE is displayed, and review Terminal for errors. Some external audio outputs manage volume independently.
- **Music is silent:** press M and check the Mac’s mute state and selected sound output.

## What I practiced

Hand landmarks, distance calculations, smoothing, timed updates, subprocess commands, playback state, and project environments.
