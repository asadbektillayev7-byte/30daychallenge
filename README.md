# 30daychallenge

My 30-day Python learning challenge: one hour of practice each day, building small interactive projects and keeping them together in one repository.

**New to coding? Start with the [complete beginner’s guide](BEGINNER_GUIDE.md).** It covers downloads and setup, one repository for all 30 projects, files and Terminal commands, the daily build-and-upload routine, AI-assisted learning, and common fixes. The main instructions use macOS, with Windows differences included.

Install the tools once, then prepare each project’s own environment and dependencies. Read its README for the exact files, controls, and limitations. You can run projects locally before uploading them to GitHub.

## Projects

| Project | Folder | Progress |
| --- | --- | --- |
| Setup | [00-setup](00-setup/) | First Python program run and uploaded |
| 01 — RockLook | [01-rocklook](01-rocklook/) | Head-tracking and music-control prototype uploaded |
| 02 — AirCanvas | [02-aircanvas](02-aircanvas/) | Pinch-drawing prototype and sample image uploaded |
| 03 — VolumeKnuckle | [03-volumeknuckle](03-volumeknuckle/) | Fist-controlled Mac volume with local music playback |
| 04 — BlinkLock | [04-blinklock](04-blinklock/) | Blink and wink detection prototype |
| 05 — FaceEQ | [05-faceeq](05-faceeq/) | Head-controlled music seeking and playback pitch prototype |
| 06 — BreathClock | [06-breathclock](06-breathclock/) | Microphone sound detection and experimental breathing-rate estimate |
| 07 — KeyboardOscilloscope | [07-keyboardoscilloscope](07-keyboardoscilloscope/) | Keyboard tones, chords, and waveform preview |
| 08 — PocketAgent | [08-pocketagent](08-pocketagent/) | Local Ollama chat with streamed replies and recent conversation history |
| 09 — WhisperDesk | [09-whisperdesk](09-whisperdesk/) | Short microphone recordings transcribed locally in Terminal |
| 10 — TerminalBrain | [10-terminalbrain](10-terminalbrain/) | Command runner with local AI error explanations |
| 11 — MoodSynth | [11-moodsynth](11-moodsynth/) | AI-controlled continuous synthesis, mood transitions, and WAV export |
| 12 — SnapAnnotator | [12-snapannotator](12-snapannotator/) | Webcam snapshots labeled by a local YOLO object detector |
| 13 — DailyDebrief | [13-dailydebrief](13-dailydebrief/) | Git activity statistics and an optional local AI debrief |
| 14 — RegisterBot | [14-registerbot](14-registerbot/) | Tiny CPU simulator with registers, an ALU, and an optional AI narrator |
| 15 — AudioScope | [15-audioscope](15-audioscope/) | Live microphone frequency bars with musical note detection |
| 16 — EchoKiller | [16-echokiller](16-echokiller/) | Voice echo added, detected, and removed with an FIR filter |
| 17 — DutyGlow | [17-dutyglow](17-dutyglow/) | PWM duty-cycle slider, square wave, and a dimming virtual LED |
| 18 — DepthPaint | [18-depthpaint](18-depthpaint/) | Webcam depth estimation with MiDaS, painted like a thermal camera |
| 19 — BusTalk | [19-bustalk](19-bustalk/) | Animated I2C conversations between a master chip and simulated sensors |
| 20 — SenseDeck | [20-sensedeck](20-sensedeck/) | Live dashboard and CSV logger for mic, camera, CPU, and network |
| 21 — WaveCast | [21-wavecast](21-wavecast/) | Send a signal as UDP packets and watch it on a live oscilloscope |
| 22 — SketchNet | [22-sketchnet](22-sketchnet/) | Photo of a hand-drawn circuit → AI parts list, schematic, netlist, and solved currents |

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

## Project 06 — BreathClock

A terminal microphone app that calibrates background noise, counts breath-like sounds, and estimates their rate. See the [BreathClock README](06-breathclock/README.md) for setup, calibration, and detection limitations.

## Project 07 — KeyboardOscilloscope

Hold **Q**, **W**, **E**, and **R** to play tones and combine them into chords. A waveform preview shows the sum of the selected sine waves. See the [KeyboardOscilloscope README](07-keyboardoscilloscope/README.md) for setup, controls, and experiments.

## Project 08 — PocketAgent

A terminal AI assistant powered by a downloaded Ollama model. It streams replies, retains recent conversation history, and works offline after setup. See the [PocketAgent README](08-pocketagent/README.md) for installation, commands, offline checks, and limitations.

## Project 09 — WhisperDesk

Record a six-second English voice clip and display a local Whisper transcription in Terminal. See the [WhisperDesk README](09-whisperdesk/README.md) for setup, the initial model download, microphone permissions, controls, and limitations.

## Project 10 — TerminalBrain

Run a short command and get a local Ollama explanation when it exits with an error. Suggestions are reviewed and applied manually. See the [TerminalBrain README](10-terminalbrain/README.md) for setup, an error-and-fix exercise, controls, and limitations.

## Project 11 — MoodSynth

Describe a mood and let a local Ollama model choose waveform, tempo, pitch, brightness, layering, rhythm, and reverb. Python generates continuous stereo sound with transitions between moods and 20-second WAV export. See the [MoodSynth README](11-moodsynth/README.md) for setup, controls, parameter explanations, export instructions, and limitations.

## Project 12 — SnapAnnotator

Take a webcam snapshot and use YOLOv8n to draw object labels, confidence scores, and boxes. See the [SnapAnnotator README](12-snapannotator/README.md) for setup, controls, image saving, and detection limits.

## Project 13 — DailyDebrief

Read recent local Git commits, calculate activity statistics, and optionally ask Ollama for a short debrief. See the [DailyDebrief README](13-dailydebrief/README.md) for setup, repository selection, report saving, and how to interpret the results.

## Project 14 — RegisterBot

A tiny CPU simulator that runs factorial and Fibonacci programs step by step. See the [RegisterBot README](14-registerbot/README.md).

## Project 15 — AudioScope

A live microphone spectrum that shows sound as 32 frequency bars and names the note you sing or whistle. See the [AudioScope README](15-audioscope/README.md).

## Project 16 — EchoKiller

Records your voice, adds an echo, finds the echo's delay and loudness, and removes it with a two-tap FIR filter. See the [EchoKiller README](16-echokiller/README.md).

## Project 17 — DutyGlow

A PWM simulator: slide the duty cycle, watch the square wave and average voltage change, and see a virtual LED dim, blink in slow motion, or breathe. See the [DutyGlow README](17-dutyglow/README.md).

## Project 18 — DepthPaint

A webcam depth map: the MiDaS neural network estimates what is near and far in every frame, and DepthPaint paints it in thermal-camera colors or as a depth grid. See the [DepthPaint README](18-depthpaint/README.md).

## Project 19 — BusTalk

An I2C simulator: watch a master chip talk to sensors over two wires, with animated bytes, a logic-analyzer timeline, ACK and NACK, and a conversation log. See the [BusTalk README](19-bustalk/README.md).

## Project 20 — SenseDeck

Turn your laptop into a live sensor dashboard: microphone level, camera brightness, CPU load, and network speed with 60-second graphs, alert lines, and CSV recording. See the [SenseDeck README](20-sensedeck/README.md).

## Project 21 — WaveCast

A network oscilloscope: a sender turns waves or your microphone into UDP packets, and the scope draws them live with a trigger, zoom, and lost-packet and delay counters. See the [WaveCast README](21-wavecast/README.md).

## Project 22 — SketchNet

Draw a circuit on paper and photograph it: a local vision model reads the parts, and SketchNet redraws a clean schematic, writes a SPICE netlist, and solves every voltage and current. See the [SketchNet README](22-sketchnet/README.md).
