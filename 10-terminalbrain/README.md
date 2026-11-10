# TerminalBrain — Day 10

Run a short command through a terminal interface. When the command exits with an error, TerminalBrain sends its output to a local AI model and displays a suggested explanation and fix. You review the suggestion, edit your code yourself, and rerun the command.

New to Python? Read the [general beginner guide](../BEGINNER_GUIDE.md) for installing tools, using Terminal, saving files, environments, and GitHub uploads.

## What this version does

- Runs commands entered at its own `Brain >` prompt.
- Collects the command's normal output and error output together.
- Checks the exit code: zero means success; a nonzero value triggers an AI explanation.
- Streams the AI response from Ollama running on the same computer.
- Maps `python` and `python3` to the Python interpreter used to launch TerminalBrain.

It does not monitor other Terminal windows, apply suggested fixes, or read your source files automatically. The AI receives the command, exit code, and the last 5,000 characters of captured output. It may need more context than that to diagnose the actual cause.

## Before starting

You need:

- Python 3.12 and uv.
- Ollama installed and running locally.
- The downloaded local model `qwen2.5:0.5b`.
- Internet for initial tool and model downloads. The supplied local AI model can run offline afterward.

There are no third-party Python dependencies to install. The program uses Python's standard library, so no `requirements.txt` is needed. Ollama is a separate application, not a Python package.

If you completed Day 8, reuse its Ollama installation and downloaded model. On macOS, Ollama currently requires macOS 14 Sonoma or newer; Intel Macs use CPU inference and may respond slowly. See the [official requirements](https://docs.ollama.com/macos) and [model page](https://ollama.com/library/qwen2.5:0.5b).

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Command runner and local AI error explanation |
| `broken_demo.py` | Small list-index example, already corrected in this repository |
| `README.md` | Setup, usage, tests, and limitations |
| `.venv/` | Local environment; excluded from Git |

Despite its filename, the committed `broken_demo.py` currently works. Its final line uses `numbers[2]`, the third item in a three-item list. The error-and-fix exercise below explains how to reproduce the original mistake.

## First-time setup

### 1. Open Ollama and check the model

Install [Ollama](https://ollama.com/download) if necessary, open the application, and complete its Terminal-command setup. Then run these commands in your normal Terminal:

```bash
ollama --version
ollama list
```

If `qwen2.5:0.5b` is missing, download it while connected to the internet:

```bash
ollama pull qwen2.5:0.5b
```

Keep Ollama running while using TerminalBrain. A paid cloud API or API key is not required for this configuration.

### 2. Prepare the Python environment

These commands assume the repository is at `~/Documents/GitHub/30daychallenge`. Substitute its actual location if you cloned it elsewhere.

```bash
cd ~/Documents/GitHub/30daychallenge/10-terminalbrain
uv venv --python 3.12
```

Skip environment creation if the project's `.venv` already exists. The source files are included when you clone this repository. When building manually, save them directly inside `10-terminalbrain`, outside `.venv`.

## Start TerminalBrain

In your normal Terminal:

```bash
cd ~/Documents/GitHub/30daychallenge/10-terminalbrain
.venv/bin/python main.py
```

Expected startup includes the model name, the project folder, help text, and:

```text
Brain >
```

The `Brain >` prompt belongs to the Python app. Type the command after it; do not include `Brain >` itself.

At this prompt, run:

```text
python broken_demo.py
```

With the committed, corrected demo, expect:

```text
The first number is: 10
The third number is: 30
Command finished successfully.
```

A successful command does not request an AI explanation.

## Try the complete error-and-fix workflow

1. Open `broken_demo.py` in VS Code.
2. Temporarily change its final line to `print("The fourth number is:", numbers[3])`.
3. Save with **⌘S**.
4. At `Brain >`, run `python broken_demo.py`.
5. Confirm that the output contains `IndexError: list index out of range` and a nonzero exit code.
6. Wait for the local model's explanation after `TerminalBrain is thinking...`.
7. Review the suggestion. The actual problem is that `[10, 20, 30]` has positions 0, 1, and 2; position 3 is outside the list.
8. Restore the line to `print("The third number is:", numbers[2])`, save, and rerun the same command.
9. Confirm that it now finishes successfully.

The model's wording and suggested fix can vary. It may suggest the wrong change because it sees output rather than the whole program. Use the observed error and your code to check its advice.

For a quick failure that does not require editing a file, enter this at `Brain >`:

```text
python -c "raise ValueError('Demo error for TerminalBrain')"
```

## Commands and supported behavior

| Input at `Brain >` | Result |
| --- | --- |
| `python broken_demo.py` | Run the demo with this project's Python |
| `python -c "print('Hello')"` | Run a short Python expression |
| `ls` | On macOS, list files in the project folder |
| `/help` | Show help |
| `/quit` | Exit TerminalBrain |
| Control+C | Interrupt the current operation and exit the main loop |

Commands execute with `10-terminalbrain` as their working folder, even if the client was launched from elsewhere. Quoted arguments are parsed with `shlex.split`. There is no shell interpretation: `cd`, pipes, redirection, `&&`, wildcard expansion, and shell environment-variable expansion are not supported.

Use only short commands that finish without input. Child programs receive no interactive input, and have a 60-second runtime limit. Their output appears after they finish, rather than live while they run. The AI explanation is streamed separately.

The runner executes the commands you type with your user permissions; it is not an isolated environment. Review commands before entering them. AI suggestions are displayed as text and are never automatically executed.

## Restarting and offline use

To reopen the app later, open Ollama and repeat the two launch commands. You do not need to reinstall Python or recreate the environment each session.

After the model has downloaded, you can turn off Wi-Fi and repeat the error exercise to check local AI explanations. Commands you choose to run may themselves need internet; the supplied local-model request goes to `127.0.0.1:11434`, meaning this computer. See Ollama's [chat API documentation](https://docs.ollama.com/api/chat).

TerminalBrain does not explicitly save transcripts, command logs, or AI suggestions to disk. The commands you run can still create or change files. Downloaded Ollama model files live outside this repository.

## Settings and limitations

Edit `main.py`, save, quit TerminalBrain, and restart it to apply changes.

| Setting | Default and effect |
| --- | --- |
| `MODEL` | `qwen2.5:0.5b`; another tag must be downloaded before use |
| `output[-5000:]` | Sends only the end of the captured output to the model |
| `num_ctx` | 2,048-token context allocation; long commands/output may exceed it |
| `num_predict` | Up to 350 generated reply tokens |
| `temperature` | 0.2; lower variability does not guarantee a correct diagnosis |
| Command `timeout` | 60 seconds before a timed-out child process is stopped |
| HTTP `timeout` | 180-second socket timeout for communicating with Ollama |

This is a small debugging prototype. It detects failure by exit code, not by reading every output line for the word “error.” A command that prints an error but exits with zero is treated as successful. Missing executables and command timeouts produce a local message rather than an AI explanation. Each AI request is independent; there is no conversation history.

This client does not implement process-group cleanup for commands that launch additional processes. Use simple scripts for the exercise rather than long-running services. Closing TerminalBrain also does not quit Ollama.

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| `ollama: command not found` | Complete Ollama setup and reopen Terminal. |
| Could not connect to Ollama | Open the Ollama application and check whether the local model works with `ollama run qwen2.5:0.5b` in a normal Terminal. Type `/bye` to leave that test. |
| HTTP 404 | Check the exact model tag with `ollama list`; download it if missing. The client also reports 404 for an unavailable endpoint. |
| Slow or incomplete AI reply | Wait for the small CPU model, use shorter error output, or check whether the reply reached its generation limit. |
| Demo succeeds instead of failing | The committed demo is already fixed. Follow the temporary-edit exercise above. |
| Command seems stuck | Captured output is shown only when it finishes. The client stops a timed-out command after 60 seconds. |
| Program asks for input or exits immediately | Interactive child programs are unsupported in this version. |
| `cd` or a pipe does not work | Use your normal Terminal for shell operations; `Brain >` is a command runner, not a full shell. |
| Could not read the command | Check matching quotation marks. |
| `can't open file ... main.py` | Check the folder and filename with `pwd` and `ls` in your normal Terminal. |
| `.venv/bin/python` is missing | Enter the correct project folder and create its environment if needed. |
| A Python import fails in a command you run | `python` uses TerminalBrain's environment. Other projects may need their own interpreter and dependencies. |

## What I practiced and checked

Built with AI guidance: subprocess execution, exit codes, capturing output, JSON requests, streamed local-model replies, and checking a suggested fix by rerunning the program.

The builder reported that the app works. Documentation checks cover Python syntax, help/exit controls, and command success/failure handling. Model accuracy and every possible child command are not guaranteed.
