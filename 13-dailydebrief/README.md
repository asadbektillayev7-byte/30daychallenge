# DailyDebrief · Day 13

Run one command and a local AI model writes a short summary of your day from your git commits. DailyDebrief reads your recent commits, counts the files and lines you changed, and asks a small model running on your own computer for a three-part debrief: what you built, a sensible next step, and a one-line summary.

> **New to coding?** Start with [the general beginner guide](https://github.com/asadbektillayev7-byte/30daychallenge/blob/main/BEGINNER_GUIDE.md) . It explains installing tools, opening the correct folder, creating environments, saving files, and uploading changes.

## How it works

1. Python runs `git log` and `git status` on a repository.
2. It collects the commits from the chosen time window: the time, the message, the files changed, and the lines added and removed.
3. It shortens that data so the small model can handle it.
4. Ollama's local model `qwen2.5:0.5b` returns a debrief as JSON.
5. The program checks the reply and prints a report in the terminal.

This is a summary of git metadata, not a code review. The model only sees commit messages, file names, folder names and line counts. It does not read your code, so it cannot explain how anything works, and it cannot know about work you did not commit.

## Before starting

You need:

- Python 3.12 and `uv` (the same setup as the earlier days).
- Git, with at least one commit in the window you are checking.
- Ollama running locally with `qwen2.5:0.5b` downloaded.
- Internet only for the first model download. After that it works offline.

There is nothing to install from PyPI. The program uses only Python's standard library, so no `requirements.txt` is needed. There is no cloud API, account or key. Your commit messages and file names are sent to the model on this computer only (`127.0.0.1:11434`) and are not uploaded anywhere.

## Files

| Item | Purpose |
| --- | --- |
| `main.py` | Reads git history, builds the model request, validates the reply, and prints the report |
| `.gitignore` | Keeps the environment and saved reports out of Git |
| `.venv/` | Local environment, excluded from Git |
| `debrief.txt` | Local report created by `--save`, also excluded from Git |

Cloning this repository does not include the Ollama model or the Python environment.

## First-time setup

### 1. Open Ollama and check the model

Open the Ollama app and leave it running. In Terminal:

```bash
ollama list
```

If the model is missing, download it while connected to the internet:

```bash
ollama pull qwen2.5:0.5b
```

### 2. Check git and your commits

```bash
git --version
git -C ~/Documents/GitHub/30daychallenge log --since="48 hours ago" --oneline
```

You should see a list of recent commits. If the list is empty, DailyDebrief has nothing to read, so make a commit first or use a longer window.

### 3. Prepare the project folder

The commands below assume this repository is cloned into `~/Documents/GitHub/30daychallenge`. Substitute its actual location if yours differs.

```bash
cd ~/Documents/GitHub/30daychallenge
mkdir -p 13-dailydebrief
cd 13-dailydebrief
uv venv --python 3.12
```

The source is included when you clone the repository. If building manually, save `main.py` directly inside `13-dailydebrief`, outside `.venv`, before running it. If the `.venv` already exists, skip `uv venv`; running it again asks whether to replace the existing environment.

## Start DailyDebrief

Keep Ollama open, then run:

```bash
cd ~/Documents/GitHub/30daychallenge/13-dailydebrief
.venv/bin/python main.py
```

By default it reads the git repository that contains this folder, looks back 24 hours, and asks the AI for a debrief. This is a terminal program. It prints a report and exits.

## Options

| Option | Result |
| --- | --- |
| `--hours 72` | Look back 72 hours instead of 24 |
| `--repo ~/path/to/project` | Read a different repository (any folder inside it works) |
| `--no-ai` | Show the git statistics and commit list without calling Ollama |
| `--save` | Also save the report as `debrief.txt` beside `main.py` |

Options can be combined:

```bash
.venv/bin/python main.py --hours 72 --save
.venv/bin/python main.py --repo ~/Documents/GitHub/another-project --no-ai
```

Saving again replaces the same file, so rename or copy `debrief.txt` first if you want to keep an earlier one.

## What the report shows

- Repository name, time window and the time of the report.
- Number of commits, files changed, and lines added and removed.
- Number of uncommitted changed files, counted from `git status`.
- The most touched top-level folders, for example `12-snapannotator (6)`.
- Your ten most recent commits.
- The AI debrief:
  - **BUILT** describes what was worked on.
  - **NEXT** suggests a next step based on the data.
  - **ONE-LINER** summarizes the day in one sentence.

If the AI request fails, or the model returns an invalid reply, the program prints the git summary without the debrief. The statistics are calculated by Python, not by the model, so they do not depend on the AI.

## Limits and what to expect

- The request is shortened to fit a 2,048-token context. At most 30 commits, six files per commit and about 3,500 characters are sent. Extra commits are counted in the statistics but not shown to the model.
- Line counts come from git. Binary files such as images do not have line counts, so they are skipped in the totals.
- Merge commits can show fewer file changes than regular commits.
- Only committed work is summarized. Uncommitted changes are counted but not described.
- `qwen2.5:0.5b` is a very small model. Its summary can be generic, repetitive or slightly wrong, and it may not understand a vague commit message such as "update". Always compare it with the commit list printed above it.
- Time is shown in your computer's local time zone, using the commit date.
- Better commit messages produce better debriefs.

## Check that it works

1. Run `ollama list` and confirm `qwen2.5:0.5b` is installed.
2. Run `.venv/bin/python main.py --no-ai` and confirm that you see commit counts, folders and your recent commits.
3. Compare the commit count with `git log --since="24 hours ago" --oneline` in the same repository.
4. Run `.venv/bin/python main.py` with Ollama open and wait for the AI debrief.
5. Check that BUILT mentions work that appears in the commit list.
6. Run `.venv/bin/python main.py --hours 1` in a quiet period and confirm you see the "No commits" message instead of an error.
7. Run it with `--save` and open `debrief.txt`.
8. Quit Ollama and run it again to confirm you see the `Could not reach Ollama` message, followed by the git summary.

These are interaction checks for your own computer. They do not establish that the AI's wording is accurate.

## Settings you can change

Open `main.py`, change one setting at a time, save with ⌘S, and run it again.

- `MODEL`: the Ollama model tag. Download that tag before selecting it. A larger model can write better summaries, but it uses more memory and CPU time.
- `MAX_COMMITS`: how many commits are sent to the model.
- `MAX_FILES_PER_COMMIT`: how many file names are listed for each commit.
- `MAX_CONTEXT_CHARS`: the size limit for the request.
- `--hours`: the default is 24, set in the argument parser.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `Git was not found` | Install git, then open a new Terminal window. |
| `is not inside a git repository` | Use `--repo` with a folder inside a git project, or run it from one. |
| `No commits in the last 24 hours` | Make a commit, or use a longer window, for example `--hours 72`. |
| `Could not reach Ollama` | Open the Ollama app and try again. |
| `Ollama HTTP error 404` | The model is missing. Run `ollama pull qwen2.5:0.5b`. |
| `Could not get an AI debrief` | The small model returned incomplete or invalid JSON. Run it again, or use a larger model. |
| The AI summary is vague or wrong | Compare it with the commit list. Use clearer commit messages, or try a larger model. |
| The report shows fewer commits than expected | Check the time window with `--hours`, and check that you are reading the right repository. |
| The AI request is slow | The first request loads the model into memory. Later requests are faster. Close other heavy apps. |
| `can't open file main.py` | Use `pwd` and `ls -a` to check the folder and the filename. |
| `debrief.txt` appears in Git | Check that `.gitignore` is in the project folder and lists `debrief.txt`. |

## Privacy

Commit messages, file names and folder names are sent to the model on your own computer. Nothing is uploaded. Reports are saved only when you use `--save`. If your commit messages or file names contain private information, remember that `debrief.txt` repeats them, which is why it is kept out of Git.

## Learning and implementation

Built with AI guidance: running git from Python with `subprocess`, parsing `git log --numstat` output, counting with `collections.Counter`, shortening data for a small model's context window, requesting structured JSON from Ollama, validating the reply, handling errors without crashing, and adding command-line options with `argparse`.

The project idea comes from the BuildCored challenge: AI reads your git commits and writes a summary of your day. This repository's implementation is a small version of that idea and uses git only.

