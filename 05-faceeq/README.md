# FaceEQ — Day 5

A webcam music player controlled with head movements. Turn your face to seek through a song and tilt your head toward a shoulder to change its pitch and playback speed.

## Setup on macOS

Use Python 3.12 and uv. From this project folder:

```bash
uv venv --python 3.12
uv pip install -r requirements.txt
```

Place a playable audio file beside `main.py`, named `music.mp3`, `music.wav`, or `music.m4a`. If more than one exists, the app chooses them in that order. PyAV reads the actual format, including WebM audio stored under the name `music.mp3`. Renaming a file does not convert its format. Music and the virtual environment stay local and are excluded from Git.

## Run

```bash
cd ~/Documents/GitHub/30daychallenge/05-faceeq
.venv/bin/python main.py
```

The app loads the whole song into memory before opening the camera. Allow Terminal camera access when macOS asks. Click inside the camera window before using the keys.

## Controls

| Control | Action |
| --- | --- |
| C while looking straight ahead | Calibrate the neutral head position |
| M | Play or pause |
| Turn your face to either side | Seek forward or backward in two-second steps while playing |
| Return your face to the center | Stop seeking |
| Tilt toward a shoulder | Change pitch, up to six semitones in either direction |
| R | Restart the song |
| Q | Quit and release camera and audio |

The track loops. Seeking past either end wraps around. Pitch changes also change the tempo because this prototype adjusts playback rate. Losing face tracking restores normal playback speed without pausing the song.

## Troubleshooting

- **Download connection error:** retry with `uv --native-tls pip install -r requirements.txt`.
- **Camera unavailable:** close other camera apps and check System Settings → Privacy & Security → Camera for Terminal.
- **Unreadable music:** use another playable audio file. The terminal reports decoding errors before the camera opens.
- **No sound:** click the camera window and press M; check the selected Mac output device and volume.
- **Unexpected movement response:** face the camera and press C again. Lighting, posture, and camera angle affect tracking.

## What I practiced

Face landmarks, calibration, loops and conditions, audio decoding, NumPy interpolation, and sharing playback state between a camera loop and an audio callback.
