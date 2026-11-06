# BreathClock — Day 6

A terminal app that listens through the microphone, detects breath-like sounds, and estimates their rate per minute. Built as part of my 30-day Python learning challenge.

## Setup

Use Python 3.12, uv, and a working microphone. From this project folder:

```bash
uv venv --python 3.12
uv pip install -r requirements.txt
```

If a download connection fails, try `uv --native-tls pip install -r requirements.txt`.

## Run

```bash
cd ~/Documents/GitHub/30daychallenge/06-breathclock
.venv/bin/python main.py
```

Allow microphone access if macOS asks. The app runs in Terminal; it does not open a camera or separate window.

1. Stay quiet for five seconds while the app measures background noise.
2. Breathe normally near the microphone for ten seconds to calibrate sound levels.
3. Keep the microphone position steady and continue breathing normally.
4. Read the sound-level bars, detected-event count, and estimated rate in Terminal.
5. Press **Control+C** to stop.

The rate appears after at least four accepted events. Restart the program to recalibrate.

## How it works

The microphone supplies mono audio at 16 kHz. NumPy calculates the RMS sound level, and a short moving average smooths it. Separate start and end thresholds identify sound bursts. The app accepts bursts lasting 0.2–4 seconds with at least two seconds between accepted start times. It estimates the rate from the median interval between recent accepted events, using up to eight events. After 15 seconds without a recent event, it shows the waiting message again.

## Limitations

This prototype detects sound bursts rather than identifying complete breathing cycles. It may count inhalation and exhalation separately, miss quiet breaths, or count speech and background noise. The displayed breaths-per-minute value is experimental and is not a medical measurement. Breathe normally rather than trying to match the number. No audio recording is saved or uploaded by this script.

## Troubleshooting

- **Microphone permission:** check System Settings → Privacy & Security → Microphone and enable the app running Python, such as Terminal.
- **Breathing too quiet:** reduce background noise or bring the microphone closer, then restart calibration.
- **No microphone data:** check the Mac's selected input device and reconnect an external microphone if needed.
- **Unstable counts:** keep the microphone in the same position and avoid talking, music, or blowing directly into it.
- **Missing main.py:** save the file directly inside `06-breathclock`, outside `.venv`.

## What I practiced

Microphone input, callbacks and queues, RMS sound levels, calibration, thresholds, timing, moving averages, and a live terminal display.
