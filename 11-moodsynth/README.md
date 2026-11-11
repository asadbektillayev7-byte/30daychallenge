# MoodSynth — Day 11

Describe a mood in Terminal and hear a matching ambient loop. A local AI model chooses a sound profile; Python generates its tones and wind-like noise, and Pygame plays the result. You can stop playback, replay the latest loop, or export it as a WAV file.

New to coding? Read the [general beginner guide](../BEGINNER_GUIDE.md) for downloading tools, creating environments, saving files, running programs, and uploading to GitHub.

## What AI does here

Ollama's local `qwen2.5:0.5b` model selects **peaceful**, **dreamy**, **bright**, or **stormy** and supplies a short explanation. The synthesizer then uses the selected profile's fixed settings. The AI does not generate an audio recording or independently choose every numerical setting.

The sound combines four sine-wave notes, a quiet second harmonic, stereo positioning, volume swells, and smoothed random noise. The result is a 12-second loop, not a composed song. Different descriptions can choose the same profile and sound similar. The random noise layer can vary between generations.

## What you need

- Python 3.12 and uv.
- NumPy 1.26.4 and Pygame 2.6.1, listed in `requirements.txt`.
- Ollama running locally with `qwen2.5:0.5b` already downloaded.
- Speakers or headphones and a working audio output device.
- Internet for initial installation and model downloads; the local model can run offline afterward.

No camera, microphone, input music file, paid cloud API, or API key is required for this configuration. If you completed Day 8, reuse the same Ollama installation and model.

The macOS Ollama application currently requires macOS 14 Sonoma or newer. Intel Macs use CPU inference and may take time to choose a profile. See the [official macOS requirements](https://docs.ollama.com/macos) and [model details](https://ollama.com/library/qwen2.5:0.5b).

## Files

| Item | Purpose |
| --- | --- |
| `main.py` | Mood input, local AI request, synthesis, playback, and export |
| `requirements.txt` | Direct Python dependency versions |
| `.venv/` | Local Python environment, excluded from Git |
| `mood.wav` | Created only when you use `/save`; kept local and ignored by Git |

## First-time setup

### 1. Open Ollama

Launch the Ollama application and leave it running. In your normal Terminal, check the downloaded model:

```bash
ollama list
```

If `qwen2.5:0.5b` is missing, connect to the internet and download it:

```bash
ollama pull qwen2.5:0.5b
```

The model is stored by Ollama separately from this repository. You do not need to download it for every project.

### 2. Prepare the Python environment

These commands assume you cloned the repository into `~/Documents/GitHub/30daychallenge`. Substitute your actual path if you used another location.

```bash
cd ~/Documents/GitHub/30daychallenge/11-moodsynth
uv venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```

Skip creating `.venv` if it already exists. If installation fails because of a certificate problem, you can try:

```bash
uv --system-certs pip install --python .venv/bin/python -r requirements.txt
```

`main.py` is included when you clone the repository. When building manually, save it directly inside `11-moodsynth`, outside `.venv`.

## Start the app

Keep Ollama running, lower your speaker volume for the first test, and run:

```bash
cd ~/Documents/GitHub/30daychallenge/11-moodsynth
.venv/bin/python main.py
```

You should see the MoodSynth heading, help instructions, and a `Mood >` prompt. The app runs in Terminal and does not open a separate graphical window.

At the prompt, type a description and press Enter:

```text
peaceful evening beside the sea
```

Wait for the AI profile selection. The app prints the profile, root tone, noise amount, pulse rate, and explanation, then creates and plays a loop. The AI response is collected before displaying the settings, so a quiet wait on an Intel Mac is possible.

## Controls

| Input at `Mood >` | Action |
| --- | --- |
| A mood description | Stop playback, ask the AI for a profile, and generate a new loop |
| `/stop` | Stop playback without discarding the latest loop |
| `/play` | Play the latest generated loop from the beginning |
| `/save` | Save the latest loop beside `main.py` as `mood.wav` |
| `/help` | Show instructions |
| `/quit` | Stop audio and close the app |
| Control+C | Interrupt the program and clean up audio output |

Blank input is ignored. `/play` and `/save` ask you to create a sound first if none exists. If a new generation fails, the previous successful sound remains available through `/play` or `/save`.

## Export and reopen your audio

Type `/save` after generating a sound. The app prints the full destination path. The file is a **12-second, stereo, 44,100 Hz, 16-bit PCM WAV** containing one loop, even though live playback repeats it.

Find `mood.wav` in the project folder using Finder and open it in an audio player. Saving another loop replaces the same file. To keep multiple exports, copy or rename an existing export before saving again. Only `mood.wav` is ignored by this project's Git rule; review renamed files before committing.

Audio stays in memory until you export it. Closing the program discards the in-memory loop; `/play` does not automatically reload a WAV from an earlier session. Mood descriptions and AI explanations are not explicitly saved by this script.

## Compare the profiles

| Profile | Root tone | Noise amount | Requested pulse rate | Character |
| --- | --- | --- | --- | --- |
| Peaceful | 130 Hz | 0.01 | 0.15 Hz | Gentle harmony and very little noise |
| Dreamy | 330 Hz | 0.12 | 0.35 Hz | Higher, spacious harmony with a soft texture |
| Bright | 220 Hz | 0.02 | 1.8 Hz | Major harmony and faster swells |
| Stormy | 65 Hz | 0.9 | 0.7 Hz | Low, tense harmony with prominent noise |

The pulse rate controls amplitude swells rather than song tempo. The code rounds frequencies and pulse rates to whole cycles within the 12-second loop. It fades the first and last 80 milliseconds to reduce clicks, so you may hear a brief dip at the loop boundary.

The generated buffer is normalized to 30% of full digital peak amplitude. Actual listening volume still depends on your system output and speakers.

## Check that it works

1. Generate `peaceful evening` and wait for playback.
2. Run `/stop` and confirm it stops.
3. Run `/play` and confirm the same loop starts again.
4. Try `stormy night`. Read the selected profile as well as listening; the small model may misclassify a description.
5. Run `/save` and open the exported WAV in a separate audio player.
6. After the model has downloaded, turn off Wi-Fi and try another mood with Ollama still running to check offline generation.
7. Run `/quit` and confirm the app exits and its playback stops.

The intended differences are fixed in `PROFILES`; the local model decides which one to select. A mood being classified unexpectedly is different from an audio device or connection failing.

## Change the settings

Open `main.py` in VS Code, edit one setting, save with **⌘S**, quit the running app, and start it again.

- `PROFILES`: change each profile's `root_hz`, `noise`, `pulse_hz`, or musical `intervals`.
- `SECONDS`: change the generated loop length. Longer loops use more memory and take more work to generate.
- `MODEL`: choose another Ollama model only after downloading that exact tag.
- AI request options: the current context is 2,048 tokens, response cap 150 tokens, and temperature 0.2. These settings affect profile selection, not direct audio generation.

Adding a fifth profile also requires updating the AI instructions so it knows that choice exists. A small model may still return an invalid response; the code validates the selected profile and reports an error.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| Could not reach Ollama | Open the Ollama app and check that the model is available. |
| HTTP 404 | Check `ollama list` and download the configured model tag if missing. |
| AI returns an unknown or invalid profile | Try a short description such as `peaceful`. Check that model instructions match `PROFILES`. |
| Waiting with no sound | The old loop stops before the AI request. Wait for the settings and `Playing!` message, or inspect any reported error. |
| Could not open audio output | Check the Mac's selected output device, reconnect headphones if necessary, and restart the app. |
| Playing message but no audible sound | Check system volume, mute, and output device. Low tones may be harder to hear on small speakers. |
| Profiles sound similar | Check the profile printed by the app; different prompts can select the same preset. |
| `/save` fails | Check the error and whether the project folder is writable. |
| Missing `main.py` or `.venv/bin/python` | Check the folder with `pwd` and `ls -a`, save the source, or create the environment if missing. |
| Missing NumPy or Pygame | Install requirements into the same `.venv` used to launch the program. |

## What I practiced

Local AI classification, JSON parsing and validation, sine waves and harmonics, NumPy audio arrays, stereo mixing, looping playback, WAV export, and handling errors. Built with AI guidance as a learning prototype.

Validation can check synthesis, file format, and controls without proving that a particular mood sounds appropriate. Sound quality and AI choices still need listening and review on your own computer.
