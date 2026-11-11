# MoodSynth — Advanced · Day 11

Describe a mood in Terminal and hear an ambient sound designed from that description. A local AI model chooses synthesis parameters, and Python continuously generates stereo audio from them. Enter a new mood to transition to another sound, or export a 20-second WAV file.

New to coding? Start with the [general beginner guide](../BEGINNER_GUIDE.md). It explains installing tools, opening the correct folder, creating environments, saving files, and uploading changes.

## What is different in this version?

The earlier prototype selected one of four fixed profiles and played a generated 12-second loop through Pygame. The advanced version replaces that workflow:

- The AI chooses the waveform and numerical settings rather than selecting a fixed profile.
- Five waveform types provide different tonal characters.
- Audio is generated continuously through sounddevice.
- Tone layering, brightness filtering, volume movement, rhythmic pulses, and feedback delays shape the sound.
- The existing sound keeps playing while a new AI request runs.
- A successful new sound fades in over about 0.6 seconds while the previous one fades out.
- WAV export creates a fresh 20-second rendering of the current settings.

This is procedural sound synthesis guided by AI. The language model does not generate an audio recording, recognize your emotions, or compose a complete song. It interprets the description you type. It can choose similar settings for different descriptions or choose settings that sound unlike what you expected.

## Before starting

You need:

- Python 3.12 and uv.
- NumPy, sounddevice, and SciPy from this folder's `requirements.txt`.
- Ollama running locally with `qwen2.5:0.5b` downloaded.
- Speakers or headphones and a working audio output device.
- Internet for initial package and model downloads. Local generation can work offline afterward.

There is no camera, microphone, input song, or paid cloud API involved. You can reuse the Ollama setup from Day 8. Pygame is no longer used by this version.

Ollama's macOS app requires macOS 14 Sonoma or newer and supports Intel Macs through CPU inference. The small model is intended to keep this exercise manageable on the builder's Intel MacBook Air with 8 GB RAM; latency and audio performance still depend on available resources. See the [official macOS requirements](https://docs.ollama.com/macos) and [model details](https://ollama.com/library/qwen2.5:0.5b).

## Files

| Item | Purpose |
| --- | --- |
| `main.py` | AI settings request, continuous synthesis, playback controls, and WAV export |
| `requirements.txt` | Direct Python dependencies pinned to the installed versions |
| `.venv/` | Local environment, excluded from Git |
| `mood.wav` | Local audio export created by `/save`, also excluded from Git |

Ollama stores its model separately from the source repository. Cloning this repository does not include either the model or the Python environment.

## First-time setup

### 1. Open Ollama and check the model

Download [Ollama](https://ollama.com/download) if necessary, open it, and complete its Terminal-command setup. Leave the application running.

In your normal Terminal:

```bash
ollama list
```

If the configured model is missing, download it while connected to the internet:

```bash
ollama pull qwen2.5:0.5b
```

You can check it independently with `ollama run qwen2.5:0.5b`. Type `/bye` when finished with that test. Downloading a different model does not automatically change MoodSynth's `MODEL` setting.

### 2. Prepare the Python environment

The commands below assume this repository is cloned into `~/Documents/GitHub/30daychallenge`. Substitute its actual location if yours differs.

```bash
cd ~/Documents/GitHub/30daychallenge/11-moodsynth
uv venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```

If this project's `.venv` already exists, skip recreating it and install the updated requirements into it. Older environments may still contain Pygame; the advanced program simply does not use it.

The source is included when you clone the repository. If building manually, save `main.py` directly inside `11-moodsynth`, outside `.venv`, before running it.

### 3. If a dependency download fails

A connection or certificate failure is different from a Python code error. To try your system's certificate store:

```bash
uv --system-certs pip install --python .venv/bin/python -r requirements.txt
```

If you previously installed the exact dependencies for other projects and they remain in uv's local cache, you can try:

```bash
uv pip install --offline --python .venv/bin/python -r requirements.txt
```

Offline installation only works when the needed package files and resolution information are cached. A new computer generally needs an internet connection. This project uses SciPy 1.17.1, which was already cached on the builder's machine and is compatible with the pinned NumPy version. There is no need to download the older 1.13.1 suggested during initial development.

## Start MoodSynth

Keep Ollama open, then run:

```bash
cd ~/Documents/GitHub/30daychallenge/11-moodsynth
.venv/bin/python main.py
```

You should see `MoodSynth — Advanced`, the configured model name, commands, and a `Mood >` prompt. This is a terminal app; it does not open a separate graphical window. Start with your computer's listening volume low.

Type a description after the prompt and press Return:

```text
calm rainy night, soft dark pad, slow and spacious
```

Wait for the AI response. The program prints its chosen waveform and parameter bars, then starts playing. It sends at most the first 500 characters of each mood description.

Try another description:

```text
energetic electronic thriller, buzzy saw, fast strong pulse
```

The old sound continues while the model thinks. When valid new settings arrive, playback transitions to the new sound. Typing remains blocked during the request; this version is not a graphical app with independently responsive controls.

## Controls

| Input at `Mood >` | Result |
| --- | --- |
| A mood description | Ask the local model for new settings and start that sound |
| `/stop` | Pause playback |
| `/play` | Resume the current sound, if one has been generated |
| `/save` | Render a fresh 20-second WAV from the current settings |
| `/help` | List commands |
| `/quit` | Close MoodSynth and release its audio stream |
| Control+C | Interrupt the current operation and close the app |

A new valid mood starts playback even if it was paused. An invalid AI response produces an error rather than silently substituting the same default sound. Any previous sound is left unchanged. `/play` requires settings from at least one successful request.

## What the AI controls

The program requests a JSON object through Ollama's [local chat API](https://docs.ollama.com/api/chat). Numeric fields are checked and clamped to these ranges:

| Setting | Range or choices | Audible role |
| --- | --- | --- |
| `waveform` | `sine`, `pad`, `saw`, `square`, `noise` | Basic tone or texture |
| `tempo` | 20–160 BPM | Speed of amplitude movement and rhythmic pulses |
| `base_freq` | 40–700 Hz | Root pitch for tonal waveforms |
| `brightness` | 0–1 | Low values remove more high-frequency content |
| `density` | 0–1 | Adds tonal voices at discrete thresholds, from one to four |
| `rhythm` | 0–1 | Strength of the rhythmic volume pulse |
| `reverb` | 0–1 | Amount of the feedback-delay texture mixed into the output |
| `description` | Short text | AI label displayed in Terminal; it does not affect synthesis |

The waveforms are synthesized approximations: sine is clean, pad combines slightly detuned sines, saw and square use limited harmonic sums, and noise uses random stereo samples. The square approximation uses odd harmonics.

Density and root pitch affect tonal waveforms. The noise branch does not use those two settings; brightness, tempo, rhythm, and reverb still affect it. The reverb is a simple delay-based effect, not a simulation of a particular room. Descriptions such as “rain” or “forest” guide the parameters; the engine does not contain recordings or dedicated realistic rain, thunder, or bird generators.

There is no fixed 12-second playback buffer anymore. The engine retains its timing, filter state, and delay buffers between audio blocks. It does not generate a changing melody or chord progression; repeated or similar AI settings can still produce similar sounds.

## Export and offline use

After generating a sound, type `/save`. It writes `mood.wav` beside `main.py` as 20-second, 44.1 kHz, stereo, 16-bit PCM audio, with fades at its beginning and end. Saving again replaces the same file, so rename or copy an export before saving another if you want to keep both.

Export starts a fresh engine using the selected settings. It is not a recording of the live speaker output. Noise is generated randomly, so a noise-based export will differ from the live sound. The exported clip is faded for listening, not designed as a seamless loop.

You can pause with `/stop` before exporting to reduce simultaneous processing. Rendering can briefly occupy the interface. The existing `mood.wav` from an older version remains on disk until you export again.

After setup and model download, turn off Wi-Fi and try another mood with Ollama still running to check offline use. The AI request goes to `127.0.0.1:11434`, which means this computer. You do not need a cloud API key. The script does not save your mood descriptions or model replies; only `/save` writes an audio file.

## Check that it works

1. Confirm the heading is `MoodSynth — Advanced`.
2. Generate a calm description and wait for parameter bars and playback.
3. Use `/stop` and `/play` to check pausing and resuming.
4. Try a tense, rhythmic description. Compare the displayed parameters as well as the sound.
5. Try a noise-based description to compare a different waveform family.
6. Check that audio continues while the next AI request runs and transitions when it succeeds.
7. Pause and use `/save`; open the WAV in an audio player and check the duration.
8. With the model downloaded, repeat generation with Wi-Fi off to check local operation.
9. Use `/quit` and confirm playback ends and the normal Terminal prompt returns.

These are listening and interaction checks for your own computer. Automated synthesis checks do not establish that the AI interpreted a mood well or that your speakers are working.

## Settings you can change

Open `main.py`, change one setting at a time, save with **⌘S**, quit the old process, and rerun it.

- `MODEL`: Ollama model tag. Download that tag before selecting it. A larger model may interpret prompts better but can use more memory and CPU time.
- `VOLUME`: output amplitude scaling, initially 0.20 after soft limiting. It is not the Mac's speaker-volume setting.
- `BLOCK`: audio block size, initially 1,024 samples. Try 2,048 if playback crackles. Keep it below the shortest delay buffer (4,983 samples) with the current engine implementation.
- `FADE_SECONDS`: transition duration, initially 0.6 seconds. Keep it positive.
- AI options: context allocation 2,048 tokens, response cap 260 tokens, two inference threads, and temperature 0.4.

This is a Python learning prototype rather than a guaranteed real-time audio system. During a transition it renders two engines, and export adds further processing. A busy CPU can cause audio dropouts. Soft limiting bounds the digital samples but does not guarantee a comfortable listening level on every output device.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Heading or messages still mention fixed profiles | Save the advanced source and stop the old process before restarting. |
| `Unknown profile returned by AI: rainy` | That message belongs to the earlier fixed-profile version, not this engine. Check which saved file is running. |
| Missing `sounddevice`, `scipy`, or `numpy` | Install this folder's updated requirements into the same environment used for launch. |
| SciPy download fails with `InvalidContentType` | Try the connection troubleshooting steps above. If the exact version is cached, try the offline command; do not keep rerunning the same failed download. |
| Could not open audio output | Check the Mac's default output device, reconnect headphones if necessary, and restart the app. |
| Could not generate new settings | Keep Ollama running, check `ollama list`, and read the full error. The small model may return missing fields, an invalid waveform, or incomplete JSON; retry with a short description. |
| Several moods sound similar | Compare all printed settings. The model can choose similar parameters, and tonal layers follow the same interval pattern. Try explicit contrasting sound descriptions. |
| Sound is quiet | Check system volume and output. Low pitch and low brightness may be hard to hear on laptop speakers. |
| Playback crackles | Close unnecessary CPU-heavy apps, avoid exporting while listening, and try `BLOCK = 2048`. Restart after changing it. |
| Controls do not respond while AI is thinking | Input waits for the model request to finish. Control+C can interrupt it and close the app. |
| No audio after a callback error | Read the reported error and restart. Callback errors are checked between input iterations. |
| Export fails | Check the error, free disk space, and whether the project folder is writable. |
| `main.py` or `.venv/bin/python` not found | Use `pwd` and `ls -a` to confirm the project folder, saved filename, and environment. |

## Learning and implementation

Built with AI guidance: structured model output, validating numeric settings, harmonic synthesis, stereo mixing, stateful filtering, feedback delays, audio callbacks, thread-safe parameter handoff, crossfading, and WAV export.

The advanced code was written separately while studying the feature set of [kenken531's MoodSynth](https://github.com/kenken531/MoodSynth). Its local-model interpretation and procedural-audio approach informed the exercise. This repository's implementation and controls differ.
