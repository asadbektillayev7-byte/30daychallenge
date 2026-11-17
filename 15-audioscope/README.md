# AudioScope — Day 15

See sound. AudioScope listens to your microphone, splits the sound into frequencies, and draws them as 32 dancing bars from deep bass to high treble. When you sing, whistle, or play a clear note, it also shows the note name, its exact frequency, and how sharp or flat you are.

New to Python? Start with the [general beginner guide](../BEGINNER_GUIDE.md). It explains installing tools, environments, Terminal commands, commits, and pushing work to GitHub.

Inspired by [Asteria267/AudioScope](https://github.com/Asteria267/AudioScope). This version uses `sounddevice` and `pygame`, the same libraries as [BreathClock](../06-breathclock/) and [KeyboardOscilloscope](../07-keyboardoscilloscope/), instead of PyAudio and matplotlib. It shows one bar view rather than three panels.

## What it does

Every frame, AudioScope follows the same steps as a hardware spectrum analyzer:

1. **Capture:** take 2048 microphone samples, about 46 milliseconds of sound.
2. **Window:** fade the edges of that chunk smoothly to zero so frequencies don't smear into each other.
3. **FFT:** a Fast Fourier Transform turns "air pressure over time" into "how strong each frequency is".
4. **Decibels:** convert each strength to dB, the loudness scale used by audio tools.
5. **Bars:** group the frequencies into 32 bars spaced like human hearing, so bass and treble get fair room.
6. **Smoothing:** bars jump up quickly and fall slowly, so the display is readable.
7. **Peak markers:** a green line above each bar remembers its recent highest level.
8. **Note:** find the strongest pitch between 60 Hz and 5000 Hz and name the nearest musical note.

No AI model is used today. Everything is math with NumPy.

The note reader follows the single loudest frequency. It does not recognize chords, voices, words, or instruments. A low voice can sometimes read as its stronger overtone, one octave higher.

## Before starting

You need:

- Python 3.12 and uv.
- A microphone and permission for Terminal or VS Code to use it.
- The packages in `requirements.txt`: NumPy, sounddevice, and pygame.

No Ollama, paid API, or cloud account is needed. Installing the packages needs internet once. After that, AudioScope works offline. Sound is analyzed live and is never recorded or saved. The example setup is macOS-first.

## Files

| Item | Purpose |
| --- | --- |
| `main.py` | Microphone capture, FFT, bars, note detection, drawing, demo sound, and self-test |
| `requirements.txt` | Package versions used when this project was built |
| `.gitignore` | Excludes the environment, Python cache files, and saved `audioscope.png` |
| `.venv/` | Local Python environment |
| `audioscope.png` | Screenshot written only when you press **S** |

## First-time setup

### 1. Prepare Python

These commands assume the repository lives at the example path. Substitute your actual location if needed.

```bash
cd ~/Documents/GitHub/30daychallenge/15-audioscope
uv venv --python 3.12
uv pip install -r requirements.txt
```

Skip environment creation if this project's `.venv` exists. Save `main.py` in this folder, outside `.venv`.

### 2. Check the math without a microphone

```bash
.venv/bin/python main.py --test
```

This runs 9 automated checks with made-up tones. It confirms the FFT finds the right frequency, the right bar lights up, notes such as A4 and C4 are named correctly, and silence shows no note. You should see:

```
9/9 checks passed
```

### 3. Allow the microphone

The first live run may trigger a macOS permission prompt. Allow it. If you clicked **Don't Allow** earlier, open **System Settings → Privacy & Security → Microphone**, turn on the app you launch from, such as Terminal or Visual Studio Code, and restart that app.

## Run AudioScope

From the Day 15 folder:

```bash
.venv/bin/python main.py
```

A window opens with 32 bars. Try these:

- **Talk normally** and watch the low and middle bars move.
- **Whistle** and watch one tall bar appear, with a note such as `C6` in the top-right corner.
- **Sing one steady note** and try to keep the cents number near 0.
- **Clap or tap the desk** and watch the bars jump across the whole range, then fall slowly.

If you have no working microphone, try the made-up demo sound. It plays a slowly changing melody over a bass note:

```bash
.venv/bin/python main.py --demo
```

The demo makes no sound through the speakers. It only feeds fake samples into the same math.

## Controls

| Key | Action |
| --- | --- |
| **Space** | Freeze or unfreeze the display |
| **S** | Save the current screen as `audioscope.png` beside `main.py` |
| **Q** or **Esc** | Quit |

Closing the window also quits.

## Options

| Option | Meaning |
| --- | --- |
| `--demo` | Use the made-up sound instead of the microphone |
| `--test` | Run the 9 math checks and exit |
| `--help` | Show command-line help and exit |

## Read the screen

| Part | Meaning |
| --- | --- |
| Bars | Loudness of each frequency range, from 20 Hz on the left to 20 kHz on the right |
| Labels 20 Hz, 200 Hz, 2 kHz, 20 kHz | Each label is ten times the previous one, matching how ears hear pitch |
| Green marks | Recent peak level of each bar, falling slowly |
| Grid lines | Loudness steps of 20 dB; the bottom is −90 dB and the top is −10 dB |
| Large note | Nearest musical note to the strongest pitch, such as `A4` |
| Hz and ¢ | The exact frequency and how many cents it is from the true note; 100 cents is one semitone |
| Note color | Yellow when within 20 cents of the note, orange-red when further away |

The note disappears when no peak is louder than −45 dB, so quiet room noise doesn't show random notes.

### Musical notes in numbers

Notes use equal temperament with A4 = 440 Hz. Each semitone multiplies the frequency by the 12th root of 2, about 1.06. An octave doubles it:

| Note | Frequency |
| --- | --- |
| A3 | 220 Hz |
| C4 (middle C) | 261.63 Hz |
| A4 | 440 Hz |
| A5 | 880 Hz |

The FFT only measures every 21.5 Hz, which is the sample rate divided by 2048. AudioScope estimates the true peak between two measurements with a small curve fit called parabolic interpolation. That makes high notes accurate to a few cents. Very low notes, under about 100 Hz, are less precise.

## Check that it works

1. Run `--test` and confirm 9/9 checks pass.
2. Run `--demo` and confirm the bars move and a note appears.
3. Run with the microphone and confirm the bars react to your voice.
4. Whistle or play an online 440 Hz tone and confirm the note reads `A4` near 0¢.
5. Stay quiet and confirm the note disappears.
6. Press **Space** to freeze, then **S** to save, and open `audioscope.png`.

## Settings you can change

Edit these near the top of `main.py`, save, and rerun:

| Setting | Default | Effect |
| --- | --- | --- |
| `BARS` | 32 | Number of bars |
| `CHUNK` | 2048 | Samples per FFT; larger gives finer frequency detail but slower reaction |
| `FLOOR_DB` and `CEILING_DB` | −90 and −10 | Quietest and loudest levels drawn |
| `NOTE_MIN_DB` | −45 | Lower it to detect quieter notes, raise it if random notes appear |
| `WIDTH`, `HEIGHT` | 900, 520 | Window size |

The falling speeds of the bars and peak markers are the numbers 2.5 and 0.6 in the main loop.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Bars stay flat | Check microphone permission and the input device in **System Settings → Sound → Input**. Try `--demo` to confirm the drawing works. |
| `Microphone error` | Another app may be using the microphone, or permission is off. Close it, allow access, and retry. |
| Random notes in a quiet room | Raise `NOTE_MIN_DB`, for example to −40. |
| Your note shows one octave too high | The microphone heard an overtone louder than the base note. Sing a little louder or use a whistle. |
| `ModuleNotFoundError` | Install requirements, then launch with `.venv/bin/python`. |
| Window does not appear | Look behind other windows or in the Dock; pygame opens a separate window. |
| Missing source or interpreter | Run `pwd` and `ls -a`; confirm `main.py` is in this folder and create the environment if missing. |

## What I practiced

Built with AI assistance: reading live microphone audio on a background callback, a queue that drops old chunks instead of lagging, Hann windowing, the FFT with `numpy.fft.rfft`, decibels, logarithmic frequency bands, smoothing and peak hold, note math with logarithms, parabolic interpolation, drawing with pygame, and a self-test that checks the math with known tones.
