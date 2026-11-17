# EchoKiller — Day 16

Record your voice, add an echo to it, then build a filter that removes the echo. EchoKiller works out the echo's delay and loudness by itself, turns those two numbers into an FIR filter, and shows the clean, echoed, and filtered sound side by side. You also hear all three versions through your speakers.

New to Python? Start with the [general beginner guide](../BEGINNER_GUIDE.md). It explains installing tools, environments, Terminal commands, commits, and pushing work to GitHub.

Inspired by [kenken531/EchoKiller](https://github.com/kenken531/EchoKiller). That version solves a large Wiener filter and runs an adaptive LMS filter. This version is smaller: it finds the echo with autocorrelation and removes it with a two-tap FIR filter, so every step is easy to follow.

## What it does

1. **Record:** capture 4 seconds of your voice from the microphone, or use a made-up voice with `--demo`.
2. **Add an echo:** every sample also hears a quieter copy of the sound from 0.25 seconds earlier. Because the echo feeds back into itself, you hear many repeats, each one quieter.
3. **Find the echo:** autocorrelation slides the sound over a shifted copy of itself. The shift where they match best is the echo delay.
4. **Measure its loudness:** the program calculates how much of the sound from that delay is inside each sample.
5. **Build the filter:** the FIR filter keeps the sound and subtracts the echo at the found delay.
6. **Compare:** print how much the echo dropped in dB, save WAV files, play them, and show a chart.

No AI model is used today. Everything is signal math with NumPy.

**This echo is added by the program, not by your room.** EchoKiller removes an echo whose type it knows: one clean repeat that feeds back. A real bathroom or stairwell has thousands of overlapping reflections, and this simple filter will not remove those. Because the program keeps your clean recording, it can measure exactly how well the filter worked.

## The filter in simple terms

An FIR filter, short for finite impulse response filter, makes each output sample from a weighted sum of recent input samples. The weights are called **taps**.

The echo was made like this:

```
echoed[n] = clean[n] + decay × echoed[n − delay]
```

Rearranging gives the clean sound back:

```
clean[n] = echoed[n] − decay × echoed[n − delay]
```

That is a filter with only two taps: **1** for the current sample and **−decay** for the sample one delay earlier. All the taps between them are 0. This is why one short filter removes all the repeats at once, not only the first one.

## Before starting

You need:

- Python 3.12 and uv.
- A microphone and permission for Terminal or VS Code to use it.
- Speakers or headphones to hear the three versions.
- The packages in `requirements.txt`: NumPy, sounddevice, and matplotlib.

No Ollama, paid API, or cloud account is needed. Installing the packages needs internet once. After that, EchoKiller works offline. The example setup is macOS-first.

## Files

| Item | Purpose |
| --- | --- |
| `main.py` | Recording, echo, echo detection, FIR filter, measurements, playback, and chart |
| `requirements.txt` | Package versions used when this project was built |
| `.gitignore` | Excludes the environment, cache files, WAV recordings, and the chart |
| `.venv/` | Local Python environment |
| `1_clean.wav` | Your clean recording, written on every run |
| `2_echo.wav` | The recording with the echo added |
| `3_filtered.wav` | The recording after the filter |
| `echokiller.png` | The chart, written on every run |

**Each run replaces the previous WAV files and chart.** Rename or copy them first if you want to keep a recording. They contain your voice, so `.gitignore` keeps them out of GitHub.

## First-time setup

These commands assume the repository lives at the example path. Substitute your actual location if needed.

```bash
cd ~/Documents/GitHub/30daychallenge/16-echokiller
uv venv --python 3.12
uv pip install -r requirements.txt
```

Skip environment creation if this project's `.venv` exists. Save `main.py` in this folder, outside `.venv`.

The first recording may trigger a macOS permission prompt. Allow it. If you clicked **Don't Allow** earlier, open **System Settings → Privacy & Security → Microphone**, turn on the app you launch from, such as Terminal or Visual Studio Code, and restart that app.

## Run EchoKiller

From the Day 16 folder:

```bash
.venv/bin/python main.py
```

1. When it prints `Say something now!`, talk for 4 seconds. Counting out loud works well.
2. The results print in Terminal.
3. It plays three versions: **clean voice**, **with echo**, and **after the filter**.
4. A chart window opens. Close it to finish.

Example output from the default settings:

```
Echo added:  delay 250 ms, decay 0.60
Echo found:  delay 250 ms, decay 0.61
Echo level:  -2.5 dB before, -35.9 dB after
Echo reduced by 33.4 dB
```

Without a microphone, use the made-up voice:

```bash
.venv/bin/python main.py --demo
```

## Options and examples

All options go after `main.py`.

| Option | Meaning |
| --- | --- |
| `--demo` | Use a made-up voice instead of the microphone |
| `--seconds 6` | Record for 6 seconds instead of 4 |
| `--delay 0.5` | Echo delay in seconds, from 0.05 to 0.6; default 0.25 |
| `--decay 0.8` | Echo loudness from 0.2 to 0.9; default 0.6 |
| `--no-play` | Skip playback and only show results |
| `--help` | Show command-line help and exit |

Combine options:

```bash
.venv/bin/python main.py --delay 0.5 --decay 0.8
.venv/bin/python main.py --demo --delay 0.1 --decay 0.3 --no-play
```

## Read the results

| Output | Meaning |
| --- | --- |
| Echo added | The delay and decay you chose |
| Echo found | What the program worked out by itself from the echoed sound only |
| Echo level | How loud the difference from your clean voice is, compared with your voice; lower is better |
| Echo reduced by | How many dB the filter removed; every 10 dB means 10 times less echo energy |

The chart has four panels:

| Panel | What it shows |
| --- | --- |
| 1. Clean voice | Your original recording |
| 2. With echo | The messy input, with repeats filling the gaps between words |
| 3. After the FIR filter | The output, which should look like panel 1 again |
| 4. Autocorrelation and filter taps | The gray line peaks at the echo delay; the red stems are the two filter taps, 1 and −decay |

In panel 4 you may see a smaller gray peak at twice the delay. That is the second repeat of the echo.

## Tested results

With the made-up voice:

| Delay | Decay | Found delay | Found decay | Echo reduced |
| --- | --- | --- | --- | --- |
| 0.05 s | 0.5 | 50 ms | 0.46 | 16.4 dB |
| 0.1 s | 0.3 | 100 ms | 0.29 | 33.4 dB |
| 0.25 s | 0.6 | 250 ms | 0.61 | 33.4 dB |
| 0.3 s | 0.2 | 300 ms | 0.18 | 19.9 dB |
| 0.6 s | 0.9 | 600 ms | 0.89 | 36.9 dB |

A real microphone recording on a MacBook Air with the default settings found 250 ms and decay 0.60, and reduced the echo by about 43 dB.

Very short or quiet echoes are hardest, because the voice itself can look similar to an echo. That is why decay starts at 0.2.

## Check that it works

1. Run `--help` and inspect the options.
2. Run `--demo --no-play` and confirm the found delay matches 250 ms.
3. Run with the microphone and listen: the third version should sound like the first.
4. Try `--delay 0.5 --decay 0.8` and confirm the found values follow your settings.
5. Open `echokiller.png` and compare panels 1 and 3.

## Settings you can change

Edit these near the top of `main.py`, save, and rerun:

| Setting | Default | Effect |
| --- | --- | --- |
| `SAMPLE_RATE` | 16000 | Samples per second for recording and playback |
| `MIN_DELAY`, `MAX_DELAY` | 0.05, 0.6 | Allowed range for `--delay` |
| `SEARCH_FROM`, `SEARCH_TO` | 0.03, 0.7 | Where the program looks for the echo, a little wider than the allowed range |

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `the recording is almost silent` | Check microphone permission and the input device in **System Settings → Sound → Input**, then speak closer. Try `--demo`. |
| Echo found at the wrong delay | Speak more and leave fewer long silences, use a louder `--decay`, or a longer `--seconds`. |
| Reduction is small or negative | The echo was probably found at the wrong delay; see the line above. |
| No sound plays | Check the output device and volume. Use `--no-play` and open the WAV files instead. |
| Chart window doesn't appear | Look behind other windows or in the Dock. The chart is also saved as `echokiller.png`. |
| Program seems stuck after playback | The chart window is open. Close it to finish. |
| `ModuleNotFoundError` | Install requirements, then launch with `.venv/bin/python`. |
| Missing source or interpreter | Run `pwd` and `ls -a`; confirm `main.py` is in this folder and create the environment if missing. |

## What I practiced

Built with AI assistance: recording and playing audio with sounddevice, simulating a feedback echo, autocorrelation computed with the FFT, least-squares estimation of the echo loudness, designing an FIR filter from its taps, filtering by convolution, measuring results in dB, writing WAV files with Python's `wave` module, and plotting with matplotlib.
