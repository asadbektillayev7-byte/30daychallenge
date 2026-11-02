# 30daychallenge

My Python learning journey through the [BuildCored Orcas curriculum](https://buildcored.com/projects/): one hour of learning and building each day, with all projects in this repository.

## Projects

| Project | Folder | Progress |
| --- | --- | --- |
| Setup | [00-setup](00-setup/) | First Python program run and uploaded |
| 01 — RockLook | [01-rocklook](01-rocklook/) | Webcam preview uploaded; head-tracking and music prototype built locally, awaiting upload |
| 02 — AirCanvas | `02-aircanvas/` | Next project |

## Project 01 — RockLook

RockLook uses a webcam to estimate head movement and control a local audio file.

The local prototype:
- Detects face landmarks and shows the webcam feed.
- Calibrates a neutral head position when **C** is pressed.
- Plays music when the head tilts down.
- Pauses music when the head returns to a straight/up position or no face is detected.
- Resumes paused music without restarting the track.
- Closes the camera and audio when **Q** is pressed.

**Source status:** the GitHub copy currently contains the initial webcam preview. The newer head-tracking/music version is saved locally and still needs to be committed and pushed. The controls below describe that newer version.

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

## Next — AirCanvas

Draw using the webcam: pinch the thumb and index finger together to draw, and separate them to lift the pen. We will build it in `02-aircanvas/` inside this repository.

Reference: [Samira Ikromova's Day 2 AirCanvas example](https://github.com/samiraikromova/AirCanvas-BuildCored-Orcas-Day2).
