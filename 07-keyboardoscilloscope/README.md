# KeyboardOscilloscope — Day 7

Play tones with the keyboard and explore how sine waves combine into chords. Built as part of my 30-day Python learning challenge.

## Setup

Use Python 3.12 and uv. From this project folder:

```bash
uv venv --python 3.12
uv pip install -r requirements.txt
```

For download connection errors, try `uv --native-tls pip install -r requirements.txt`.

## Run

```bash
cd ~/Documents/GitHub/30daychallenge/07-keyboardoscilloscope
.venv/bin/python main.py
```

Click inside the app window before pressing keys. No camera, microphone, or music file is required.

## Controls

| Key | Approximate note | Frequency |
| --- | --- | --- |
| Q | C4 | 262 Hz |
| W | E4 | 330 Hz |
| E | G4 | 392 Hz |
| R | C5 | 524 Hz |

Hold a key to play its tone and release it to stop. Hold several keys to play a chord. Active cards turn green, and the graph shows the sum of the selected sine waves. Press **Esc** or close the window to quit. Switching away from the window stops all notes.

## Try it

1. Hold Q and inspect the smooth sine wave.
2. Hold R instead and compare how many cycles fit in the same time window.
3. Hold Q, W, and E together to hear a chord and see a more complex waveform.
4. Release the keys to return to silence and a flat line.

## How it works

NumPy generates one-second sine-wave buffers at 44,100 samples per second. Pygame loops each selected tone on a separate audio channel. Integer frequencies let each buffer contain complete cycles. The graph displays a fixed 20-millisecond mathematical preview of the selected frequencies, rather than measuring speaker output or matching the current playback phase. Frequencies approximate musical notes; they are rounded rather than exact concert tuning.

## Troubleshooting

- **Keys do nothing:** click inside the app window to give it keyboard focus.
- **No sound:** check the Mac volume, mute setting, and selected audio output.
- **Some combinations do not register:** try another combination; keyboards can limit simultaneous key detection.
- **Missing main.py:** save it directly inside the project folder, outside `.venv`.

## What I practiced

Sine waves, frequency, NumPy arrays, audio sampling, keyboard events, simultaneous playback, and drawing a waveform with Pygame.
