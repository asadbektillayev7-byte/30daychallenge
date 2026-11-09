# WhisperDesk — Day 9

Speak a short English sentence into your microphone and see its transcription in Terminal. This prototype records six seconds at a time and uses a local Whisper model to turn the recording into text.

It currently prints text in Terminal. It does not yet type into other applications, copy text to the clipboard, or listen continuously.

New to Python? Start with the [general beginner guide](../BEGINNER_GUIDE.md) for tool installation, folders, Terminal commands, virtual environments, and GitHub uploads.

## What you need

- Python 3.12 and uv.
- A working microphone and permission for the app running Python to use it.
- An internet connection to install dependencies and download the model on the first run.
- Space for the Python environment and downloaded speech model.

The supplied settings use the small, English-only `tiny.en` model on the CPU with 8-bit computation. They were chosen for an Intel MacBook Air with 8 GB RAM. Transcription time depends on your computer. Ollama from Day 8 is not required.

The project uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Its audio decoding dependency bundles FFmpeg libraries, so this setup does not require a separate FFmpeg installation.

## Files and dependencies

| Item | Purpose |
| --- | --- |
| `main.py` | Recording loop and local transcription |
| `requirements.txt` | Versions of the direct Python dependencies installed for this project |
| `.venv/` | Local Python environment, excluded from Git |
| Downloaded model | Reused from the Hugging Face cache; not stored in the repository |

`faster-whisper` runs the speech model, `sounddevice` records the microphone, and `numpy` handles the audio samples. Additional supporting packages are installed automatically.

## First-time setup

The commands below assume the repository is cloned into `~/Documents/GitHub/30daychallenge`. If you chose another location, substitute that path.

Run each line in Terminal:

```bash
cd ~/Documents/GitHub/30daychallenge/09-whisperdesk
uv venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```

If `.venv` already exists, you can skip creating it. If a download fails because of a certificate problem, try using the system certificate store:

```bash
uv --system-certs pip install --python .venv/bin/python -r requirements.txt
```

The source file is included when you clone the repository. If building manually, save it as `main.py` directly inside `09-whisperdesk`, outside `.venv`.

## Run

```bash
cd ~/Documents/GitHub/30daychallenge/09-whisperdesk
.venv/bin/python main.py
```

Keep internet on during the first run. Loading `tiny.en` can download model files before the recording prompt appears. Later runs reuse those files when they remain in the local cache. Wait for:

```text
Ready! This version transcribes English.
Press Enter to record six seconds.
```

Allow microphone access if macOS asks. If access is blocked, check **System Settings → Privacy & Security → Microphone** for the app running Python, such as Terminal or VS Code.

## Record and transcribe

1. At `Enter to record, or /quit:`, press **Return/Enter without typing anything**.
2. Wait for `Recording now — speak normally!`.
3. Say a short English sentence during the six-second recording.
4. Wait for `Recording finished. Transcribing...` and then `You said:` followed by the recognized text.
5. Press Enter again for a new recording, or type `/quit` and press Enter to stop.

For example, try: “Today I am building my ninth Python project.” The output may differ from your exact words; inspect it rather than assuming it is correct.

The app uses the default microphone selected by your system. On a Mac, check **System Settings → Sound → Input** if the wrong microphone is active. This is a Terminal app; it does not open a camera or separate window.

## Controls

| Input | Action |
| --- | --- |
| Enter at the prompt | Record a new six-second clip, then transcribe it |
| `/quit` followed by Enter | Exit at the prompt |
| Control+C | Interrupt the program |

Each clip is transcribed independently. The program does not save an audio recording or transcript to disk. After quitting, reopen it with the same run commands; reinstalling packages is unnecessary unless the environment is missing or dependencies change.

## Check offline use

After the initial model download and one successful transcription, leave the cached model files in place, turn off Wi-Fi, and repeat a short recording. Recognition should use the local model. The script still calls the model loader at startup, so a missing or incomplete cache can require internet again.

Do not claim an offline test succeeded until you have repeated it on your own computer. The documentation and Python syntax can be checked without verifying microphone capture or transcription accuracy.

## Adjust the prototype

Edit `main.py`, save it, quit the running program, and start it again.

- `RECORD_SECONDS = 6` controls the recording length. Try a modest increase if your sentence is cut off.
- `tiny.en` and `language="en"` configure English-only recognition. Supporting another language requires an appropriate multilingual model and language setting; changing only the printed instructions will not do it.
- Larger models may improve recognition but take more storage, memory, and processing time.

The almost-silent audio check is a simple volume threshold, not a speech detector. Noise or silence can still produce incorrect or invented words.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Hugging Face warning about unauthenticated requests | This warning alone is not a failure. Public model downloads can proceed without a token, subject to rate limits. Wait for download completion. If a rate-limit or connection error follows, read that error separately. |
| Stuck at model loading | Check the internet connection on the first run. Model loading can take time; capture the full error if it fails. |
| Could not load the model | A download may have failed or the local setup may be incompatible. Share the complete error before changing packages. |
| Almost-silent microphone message | Check microphone permissions and selected input device, speak closer, and try again. |
| Recording or transcription failed | Read the full error. Check that your microphone supports the requested 16 kHz input setting and is available. |
| Speech is missing or incorrect | Speak clearly in English, reduce background noise, and finish within the recording period. The small model can still make mistakes. |
| `can't open file ... main.py` | Confirm the file is saved in the correct project folder. Use `pwd` and `ls` to check. |
| `.venv/bin/python` does not exist | Change to the correct folder and create its Python environment if missing. |
| `ModuleNotFoundError` | Install the requirements into the same `.venv` used to run the program. |

A Hugging Face account token is optional for this public-model setup. If you choose to use one for download access or rate limits, keep it out of your source code and Git commits.

## What I practiced

Microphone recording, NumPy audio arrays, local model loading, iterating over transcription segments, command-line interaction, and handling errors. The project was built with AI guidance and is intended for learning and experimentation.
