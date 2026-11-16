# DailyDebrief — Day 13

Turn recent Git commits into a short report about your programming work. Python calculates repository statistics, then an optional local AI model writes three short sections: **BUILT**, **NEXT**, and **ONE-LINER**.

New to Python or Git? Start with the [general beginner guide](../BEGINNER_GUIDE.md). It explains installing tools, repositories, environments, commits, and pushing work to GitHub.

## What it can tell you

DailyDebrief runs `git log` and `git status` locally. It reads commit subjects, timestamps, changed paths, and added/deleted line counts. It shortens those details and sends them to Ollama on your own computer.

It does not inspect source contents, code diffs, browser activity, or a record of your day. Uncommitted work is counted but not described. A summary of a commit named `update` will have much less useful evidence than one named `Add snapshot keyboard controls`.

This is a single-run Terminal report, not a background watcher, scheduled job, or interactive chat. The AI's next step is a suggestion, not a task the app performs.

## Before starting

You need:

- Python 3.12 and uv.
- **Command-line Git**, available as `git` in the Terminal used to run Python.
- A local Git repository with commits reachable from its current checkout.
- For AI text: Ollama running with `qwen2.5:0.5b` downloaded.

No third-party Python packages or `requirements.txt` are needed. The app uses the standard library. `--no-ai` works without Ollama and still produces the repository statistics.

The supplied local model does not require a paid API key. Downloads need internet initially; reading a local repository and using the downloaded model can work offline. The example setup is macOS-first. On an Intel Mac, AI generation may be slow.

## Files

| Item | Purpose |
| --- | --- |
| `main.py` | Git commands, statistics, optional AI request, and report output |
| `.gitignore` | Excludes the environment, cache files, and local `debrief.txt` |
| `.venv/` | Local Python environment |
| `debrief.txt` | Report written only when `--save` reaches the report-saving step |

## First-time setup

### 1. Check command-line Git

In Terminal:

```bash
git --version
```

GitHub Desktop being installed does not guarantee that a standalone `git` command is available to this Python process. If macOS prompts you to install developer command-line tools, complete that setup and reopen Terminal. See [Git's macOS installation options](https://git-scm.com/downloads/mac).

Check that your repository has history:

```bash
git -C ~/Documents/GitHub/30daychallenge log -5 --oneline
```

If this is a new, empty repository, create a meaningful commit before expecting a report. You do not have to push a commit to GitHub for this app to read it.

### 2. Prepare Python

These commands assume the repository lives at the example path. Substitute your actual location if needed.

```bash
cd ~/Documents/GitHub/30daychallenge/13-dailydebrief
uv venv --python 3.12
```

Skip environment creation if this project's `.venv` exists. There is no package-installation step. The repository already includes `main.py`; when building manually, save it in this folder, outside `.venv`.

### 3. Prepare the optional local model

For AI output, open Ollama and leave it running. In Terminal:

```bash
ollama list
```

If needed, download the exact configured model while online:

```bash
ollama pull qwen2.5:0.5b
```

You can reuse the model from earlier days. For Ollama installation help, see the [PocketAgent README](../08-pocketagent/README.md).

## Start with the statistics-only report

This checks Git and the repository without waiting for an AI reply:

```bash
cd ~/Documents/GitHub/30daychallenge/13-dailydebrief
.venv/bin/python main.py --no-ai --hours 72
```

The app prints a report and exits. If there are no commits in that window, it prints a short no-commits message instead. Increase the window if your latest work was earlier.

## Add the AI debrief

With Ollama running:

```bash
cd ~/Documents/GitHub/30daychallenge/13-dailydebrief
.venv/bin/python main.py
```

By default it looks back **24 hours** in the Git repository containing the script's folder. It shows `AI is writing your debrief. Please wait...`, then displays the report with:

- **BUILT:** a short interpretation of the committed work.
- **NEXT:** a proposed next step based on that metadata.
- **ONE-LINER:** a short summary.

If the model connection or JSON reply fails, the program normally still prints the calculated Git report without AI text. Compare any generated claims against the commit list; the small model can invent details despite its instructions.

## Options and examples

All options go after `main.py`. The program does not have a separate command prompt.

| Option | Meaning |
| --- | --- |
| `--hours 72` | Use a rolling 72-hour window instead of 24; must be an integer of at least 1 |
| `--repo PATH` | Analyze the local Git repository containing that path |
| `--no-ai` | Skip Ollama and show only calculated information |
| `--save` | Write the completed report to `debrief.txt` beside this script |
| `--help` | Show command-line help and exit |

From the Day 13 folder, combine options:

```bash
.venv/bin/python main.py --hours 72 --save
.venv/bin/python main.py --hours 168 --no-ai
```

To select another repository, pass an actual existing folder, not a GitHub URL. For example, replace the following path with one you own:

```bash
.venv/bin/python main.py --repo "$HOME/Documents/GitHub/another-project" --no-ai
```

**Changing Terminal's current folder does not change the default repository.** Without `--repo`, the default stays the folder containing `main.py`. A nested project folder also resolves to the enclosing Git repository's root, not just that one subfolder. It does not scan all repositories on your computer.

## Understand the numbers

| Report field | What the code counts |
| --- | --- |
| Commits | Entries returned by `git log` in the selected window on the current checkout's reachable history |
| Files | Unique path strings in the returned per-commit file lists |
| Added / removed lines | Sums from `git log --numstat` over those commits; not the final net diff or a measure of productivity |
| Uncommitted changed files | Nonempty lines from `git status --porcelain`; a collapsed untracked directory may count as one entry rather than every file inside it |
| Most touched folders | Up to five top-level path groups, counted by file appearances across commits; `(root)` represents root-level files |
| Recent commits | Up to ten subjects and timestamps in the printed report |

A file edited in several commits contributes several times to the change totals. Binary files have no numeric line counts in `--numstat`, so their lines are not added to the totals. Merge commits may appear without ordinary file statistics. These are Git activity indicators, not an assessment of code quality or all time spent learning.

The window follows Git's `--since` behavior and the local clock. Printed commit timestamps use the author date formatted by Git; the report heading uses the computer's current date and time. This is a rolling-hour window, not automatically a midnight-to-midnight calendar day.

## Limits on the AI request

Statistics are calculated from all returned commits, but the model gets a shortened context:

- At most 30 recent commits, with up to six paths per commit.
- Commit subjects shortened to 120 characters in the request.
- The assembled context cut to 3,500 characters, potentially truncating its final entry.
- A requested 2,048-token model context and 260-token generation cap.
- Each returned AI field must be nonempty text and is limited to 400 characters by the client.

Character limits do not guarantee that every possible filename or language fits the token context. The model can miss work excluded by truncation. It receives a fresh request for each run, without conversation history.

## Saving and offline use

Use `--save` to write `13-dailydebrief/debrief.txt`. This destination remains beside the script even when `--repo` selects another repository. Saving again replaces the same file. Copy it elsewhere first if you want an archive.

If no commits are found, the program returns before report creation: **it does not write or refresh `debrief.txt`, even with `--save`**. An older report can remain on disk. If AI fails but Git data exists, the statistics-only report can still be saved.

No report is explicitly saved without `--save`. The local `.gitignore` excludes `debrief.txt`; renamed reports are not automatically covered by that filename rule.

The Git commands read local data without fetching, pushing, or editing the repository. For the supplied model tag, AI requests go to `127.0.0.1:11434`, meaning this computer. Commit subjects and file paths are sent to that local service, not to GitHub by this script. Saved reports may repeat sensitive filenames or messages, so review them before sharing.

For an offline check, first run `--no-ai` with Wi-Fi off. Then, with the model already downloaded and Ollama running, repeat without `--no-ai` to check local AI generation.

## Check that it works

1. Run `--help` and inspect the available options.
2. Run `--no-ai --hours 168` to cover recent activity.
3. Compare the commit list with `git log --since="168 hours ago" --oneline` in the selected repository. The printed report lists at most ten commits.
4. Run without `--no-ai`, inspect BUILT/NEXT/ONE-LINER, and check their claims against Git data.
5. Run with `--save`; open `debrief.txt` and check its timestamp and repository name.
6. Try a real second repository with `--repo` and confirm the heading changes.
7. For a no-commits test, use a repository/window you know is empty. A one-hour window will not be empty if you just made a commit.
8. Repeat local statistics and AI checks offline if you want to verify both paths.

The program exits on completion; use Control+C to interrupt a long-running request. Git commands have a 30-second timeout and the Ollama request uses a 180-second socket timeout.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `Git was not found` | Install command-line Git and reopen the Terminal used to run Python. |
| `is not inside a git repository` | Pass a real local path inside a cloned or initialized repository with `--repo`. Changing directories alone does not replace the default. |
| No commits found | Check the selected repository and branch; use a longer `--hours` value. Unsaved or uncommitted work does not create a Git log entry. |
| No saved report after `--save` | The no-commits branch does not save; otherwise check the printed path and write error. An old file may remain. |
| Could not reach Ollama | Open Ollama, check the configured local model, or use `--no-ai`. |
| HTTP 404 | Check the model tag with `ollama list`; the endpoint may also be unavailable. |
| Invalid AI debrief | The small model may return incomplete JSON or missing fields. Retry, use `--no-ai`, or deliberately select a suitable downloaded model. |
| AI summary is vague or wrong | Check the commit subjects and truncation limits. Clearer commit messages provide more evidence, but cannot guarantee accurate AI text. |
| Counts differ from expectation | Check the time window, current checkout, repeated edits, merge entries, and binary files. |
| Missing source or interpreter | Confirm the saved filename and project path with `pwd` and `ls -a`; create its environment if missing. |

## Settings and learning

Edit `MODEL`, `MAX_COMMITS`, `MAX_FILES_PER_COMMIT`, or `MAX_CONTEXT_CHARS` in `main.py`, save, and rerun. Changing a model requires downloading that tag first; larger models use more resources.

Built with AI assistance: subprocess calls, Git metadata parsing, `Counter`, request-size limits, structured local-model output, validation, error handling, and `argparse`. The statistics are computed by Python; the prose is model-generated and still needs review.
