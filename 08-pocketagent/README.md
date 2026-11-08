# PocketAgent — Day 8

A local AI chat assistant you use from Terminal. Type a question, watch the answer appear as it is generated, and ask follow-up questions using recent conversation history.

New to Python or GitHub? Read the [general beginner guide](../BEGINNER_GUIDE.md) first. It explains installing the tools, creating environments, saving files, and uploading changes.

## What you need

- Python 3.12 and uv.
- Ollama installed and running on the same computer.
- The local model `qwen2.5:0.5b` downloaded through Ollama.
- Internet access for the initial downloads. The downloaded local model can answer offline afterward.

The macOS Ollama application currently requires macOS 14 Sonoma or newer. Intel Macs use CPU inference; Apple silicon supports CPU and GPU inference. See the [official macOS requirements](https://docs.ollama.com/macos). This project was reported working by its builder on an Intel MacBook Air with 8 GB RAM; response speed depends on available memory and CPU load.

The chosen model is small: its Ollama download is about 398 MB, with additional memory required to run it. Its answers are less capable than those of larger models. See the [model page](https://ollama.com/library/qwen2.5:0.5b).

## How the parts fit together

```text
Your question in Terminal
        ↓
main.py sends the question and recent conversation
        ↓
Ollama at 127.0.0.1:11434 runs the downloaded model
        ↓
The response streams back into Terminal
```

`127.0.0.1` means this computer. The Python client calls Ollama's [local chat API](https://docs.ollama.com/api/chat). It does not use a paid cloud API or require an API key. This version is a chat assistant: it does not browse the web, execute commands, or edit files.

## First-time setup

### 1. Install and open Ollama

Download [Ollama](https://ollama.com/download), move it to Applications on macOS, and open it. Complete setup so the `ollama` command is available in Terminal. Keep the app running.

Open a new Terminal after installation and run:

```bash
ollama --version
ollama pull qwen2.5:0.5b
```

Wait for the model download to finish. You only need to download it once unless it is removed or you choose another model.

To test Ollama independently of this Python project:

```bash
ollama run qwen2.5:0.5b
```

Ask a short question. After the response, type `/bye` to return to the normal Terminal prompt.

### 2. Prepare the Python environment

The following assumes you have cloned this repository into `~/Documents/GitHub/30daychallenge`. If your repository is elsewhere, substitute its actual path.

```bash
cd ~/Documents/GitHub/30daychallenge/08-pocketagent
uv venv --python 3.12
```

No third-party Python packages are required. The code uses `json`, `urllib`, and other Python standard-library functionality. There is no `requirements.txt` to install. Ollama and its model are separate prerequisites, not Python packages.

`main.py` is already included when you clone this repository. If building manually, save it directly inside `08-pocketagent`, outside `.venv`, before running it.

## Start PocketAgent

Keep Ollama running, then run:

```bash
cd ~/Documents/GitHub/30daychallenge/08-pocketagent
.venv/bin/python main.py
```

You should see the PocketAgent heading, the model name, available commands, and a `You:` prompt. Type a question and press Return. The answer appears after `PocketAgent:`. Loading the model and beginning a reply can take time on an Intel Mac.

This is a terminal application; it does not open a browser, camera, or separate chat window.

## Commands

| Input | Result |
| --- | --- |
| A question followed by Return | Generate a reply using recent conversation history |
| `/clear` | Clear the Python client's conversation history |
| `/help` | Show available commands |
| `/quit`, `/bye`, or `/exit` | Close the Python client |
| Control+C | Exit; during generation, interrupt the reply and close the client |

An empty message is ignored. Unknown slash commands show a help hint. Closing PocketAgent does not quit the Ollama application.

## Check that it works

1. Start the program with Ollama running.
2. Type `My name is Asadbek.` and wait for the complete reply.
3. Ask `What is my name?` to check whether the model uses the previous message.
4. Run `/help` and check that the commands are listed.
5. Run `/clear` to start a fresh conversation.
6. With the model already downloaded, turn off Wi-Fi and ask a new, short question. This checks offline use on your computer.
7. Type `/quit` and check that the normal Terminal prompt returns.

Model-generated answers are not deterministic. A wrong answer does not necessarily mean the client failed; a small model can misunderstand even when the local connection works. Asking about a name after clearing is also not a definitive memory test because the model may guess.

The builder reported that the app works. The checklist above describes checks readers can repeat; it is not a claim that every model response or platform has been validated.

## Conversation memory and local files

The client retains up to four completed question-and-answer exchanges in Python memory. It sends these with the next question, then drops older exchanges as new replies complete. `/clear` empties that history, and quitting loses it. This script does not save transcripts to disk.

The model's context is limited to 2,048 tokens, which must accommodate instructions, history, and generation. Four very long exchanges may not fit. Replies are capped at 256 generated tokens and may end before a long explanation is complete. Use shorter questions or clear the conversation if needed.

Ollama stores its model files separately, normally under `~/.ollama` on macOS. They are not placed inside this repository or uploaded with the project. The `.venv` folder is also excluded from Git.

## Change the settings

Edit `main.py` in VS Code, save with **⌘S**, stop the running client, and launch it again.

| Setting | What it changes |
| --- | --- |
| `MODEL` | The Ollama model tag; download that exact model before selecting it |
| `MAX_EXCHANGES` | The number of recent completed exchanges retained by the client |
| `SYSTEM_MESSAGE` | The instructions sent to guide the assistant's style |
| `num_ctx` | The model's context allocation; larger values can require more memory |
| `num_predict` | The maximum number of generated reply tokens |
| `temperature` | Generation variability; changing it does not guarantee correct answers |

Start with the supplied settings. Changing one at a time makes it easier to understand the effect.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| `ollama: command not found` | Finish Ollama setup and reopen Terminal. Check that its Terminal command was installed. |
| Could not reach Ollama | Open the Ollama application. The local service must be running even when Wi-Fi is off. |
| Model or endpoint not found | Run `ollama list`, then download the exact configured tag with `ollama pull qwen2.5:0.5b`. |
| `can't open file ... main.py` | Check the current folder and confirm the code is saved directly in `08-pocketagent`. |
| `.venv/bin/python` does not exist | Change to the correct project folder and create its environment with `uv venv --python 3.12`. |
| Slow or timed-out response | Keep prompts short, close unnecessary apps, and check that the small local model works with `ollama run qwen2.5:0.5b`. The client uses a 180-second socket timeout. |
| Reply stops partway through | The generation cap or a connection interruption may have ended it. Ask for a shorter answer or a continuation. |
| Assistant forgets earlier messages | Only recent exchanges are retained, and long conversations can exceed the context allocation. |
| New code changes do not appear | Save the file, quit the previous client, and rerun the correct `main.py`. |

If setup fails, share the exact command and complete Terminal error when asking for help. A download needs internet access; local chat does not retrieve current web information. Responses can be incorrect, so verify important facts independently.

## What I practiced

- Connecting Python to a local HTTP service.
- Sending and reading JSON.
- Streaming a response line by line.
- Storing and trimming conversation history.
- Handling commands and connection errors.
- Building with AI guidance, then running and checking the result locally.
