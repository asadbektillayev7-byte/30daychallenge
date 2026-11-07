# Start here: a beginner’s guide to the 30-day challenge

You can start this challenge without previous Python experience. The aim is to spend about one hour each day building, testing, and understanding a small project. A working app is one result; being able to explain what you changed is another.

This guide explains the setup and routine you reuse throughout the challenge. Each project’s README supplies its particular dependencies, files, controls, and limitations.

**The main instructions use macOS**, matching the computer used to build this repository. [Windows differences](#windows-differences) are listed at the end. Some projects control macOS features and need code changes on another operating system.

## Contents

- [What the tools do](#what-the-tools-do)
- [Before the first day](#before-the-first-day)
- [Set up one repository for all 30 projects](#set-up-one-repository-for-all-30-projects)
- [Understand files, folders, and commands](#understand-files-folders-and-commands)
- [The routine for every project](#the-routine-for-every-project)
- [Restart a project another day](#restart-a-project-another-day)
- [Use AI as a learning partner](#use-ai-as-a-learning-partner)
- [Use your one hour](#use-your-one-hour)
- [Write documentation someone else can follow](#write-documentation-someone-else-can-follow)
- [Troubleshooting](#troubleshooting)
- [Daily checklist](#daily-checklist)
- [Windows differences](#windows-differences)

## What the tools do

| Tool or term | Plain-language meaning |
| --- | --- |
| Python | The program that reads and runs your Python code. |
| VS Code | The editor where you create files and write code. |
| Python extension by Microsoft | Adds Python support to VS Code. It does **not** install Python itself. |
| Terminal | A place to type commands that navigate folders, install tools, and run programs. |
| uv | A tool that installs Python versions and manages project packages. |
| Package, library, or dependency | Reusable code your app needs, such as NumPy or Pygame. |
| Virtual environment (`.venv`) | A project’s own Python and package collection, kept separate from other projects. |
| Git | Records versions of your files so you can see and recover previous work. |
| Repository, or repo | The main project folder together with its Git history. This repo contains all the daily projects. |
| GitHub | The website that stores a shared online copy of your repository. |
| GitHub Desktop | An app for reviewing, committing, and uploading changes without learning Git commands first. |
| README | A text document explaining a project. GitHub displays Markdown files such as `README.md` with headings and links. |
| AI assistant | A helper you can ask to explain, plan, or debug. Its suggestions still need checking. |

A **file** is a saved item such as `main.py`. A **folder** (also called a directory) contains files or other folders. A **path** tells the computer where an item lives, and a **command** is an instruction you type into Terminal.

## Before the first day

### Prepare your computer

Have a laptop, an internet connection for setup, and space for tools and packages. Check the requirements for the particular project before downloading anything large. Some projects need a webcam, microphone, speakers, or a local audio file; others use none of them.

The early projects here were built on an Intel MacBook Air with 8 GB RAM. That does not guarantee that every later AI model or service will run on the same machine. Check each project separately.

On a Mac, choose **Apple menu → About This Mac** to see the chip and operating system. When a download offers Intel and Apple silicon editions, choose the one matching your Mac.

### Install the editor

1. Download [Visual Studio Code](https://code.visualstudio.com/download) for your computer.
2. On macOS, move the app into **Applications** and open it.
3. Open the **Extensions** panel in the left sidebar.
4. Search for **Python** and install the extension published by **Microsoft**.

You do not need every extension with “Python” in its name. The editor, its Python extension, and the Python interpreter are separate pieces; see the [official VS Code explanation](https://code.visualstudio.com/docs/python/python-tutorial#_understand-the-python-setup).

### Install uv and Python 3.12

Open **Terminal** using Spotlight: press **⌘Space**, type `Terminal`, and press Return.

Paste this command and press Return. It downloads and runs uv’s official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Close and reopen Terminal so it can find the newly installed tool. Then run:

```bash
uv --version
```

You should see a version number. Next run:

```bash
uv python install 3.12
```

Check the chosen Python version and run a small test:

```bash
uv run --no-project --python 3.12 python --version
uv run --no-project --python 3.12 python -c 'print("Python is ready!")'
```

Expected results include `Python 3.12...` and `Python is ready!`. The last command is a quick check; the daily projects will use their own environments.

Use Python 3.12 for these examples unless a project explicitly requires another version. A newer Python version can be incompatible with an older library. You do not need to uninstall another Python version or change your Mac’s system Python.

This installation route does not require a separate Python download, Homebrew, or Anaconda. See the official [uv installer instructions](https://docs.astral.sh/uv/getting-started/installation/) and [Python installation guide](https://docs.astral.sh/uv/guides/install-python/).

### Prepare GitHub

1. Create an account at [GitHub](https://github.com/) if you do not have one.
2. Download [GitHub Desktop](https://desktop.github.com/download/) for your computer.
3. Open it and sign in to your GitHub account.
4. Finish its Git identity setup. This name and email identify your commits; GitHub’s private email option can be used if you prefer.

GitHub Desktop handles the Git workflow used in this guide. A separate Git command-line setup is optional.

### Choose an AI helper, if you want one

An AI chat assistant is enough to follow the learning routine below. Choose one you already have access to; check its usage limits and any costs. Editor integrations and paid subscriptions are optional.

You do not need API keys, local language models, or every possible project library before Day 1. Add those only if a later project requires them.

## Set up one repository for all 30 projects

**Use one main repository with one folder per project.** You do not need 30 repositories. Each project folder has its own environment, but shares the main repository’s history.

Choose one of these starting routes:

### Route A: start your own challenge from an empty repository

1. On GitHub, choose **New repository**.
2. Name it `30daychallenge`, or another name you will use consistently.
3. Choose public if you want people to see your work, or private if you prefer.
4. Enable **Add README** and select the **Python** `.gitignore` template.
5. Create the repository.
6. In GitHub Desktop, choose **File → Clone Repository**, select your repository, and clone it.

For consistency with this guide, choose a local destination that produces this path:

```text
~/Documents/GitHub/30daychallenge
```

That is a **folder location, not a command**. If you choose another name or location, adjust later `cd` commands to match it.

### Route B: use the existing code as a reference

For your own editable GitHub copy, fork this repository on GitHub, then clone **your fork** in GitHub Desktop. Cloning the original directly gives you a local copy, but does not give you permission to upload changes to someone else’s repository. You can also use an existing repository you already own.

If you clone completed projects, their source files are already present. You still create their local environments and install the required packages. Do not overwrite an existing `main.py` just to repeat setup.

GitHub documents [cloning and forking with Desktop](https://docs.github.com/en/desktop/adding-and-cloning-repositories/cloning-and-forking-repositories-from-github-desktop).

### Open the same folder in VS Code

In GitHub Desktop, select the repository and choose **Repository → Open in Visual Studio Code**. Alternatively, use **VS Code → File → Open Folder** and select the local repository folder.

Your VS Code Explorer should show `30daychallenge` at the top, with the main `README.md` below it. If the editor opens your entire home folder, open the repository folder instead.

### Understand the layout

This is an illustration of the folder structure. **Do not paste it into Terminal.**

```text
30daychallenge/
├── README.md                 main index
├── BEGINNER_GUIDE.md         this guide
├── .gitignore               files Git should leave out
├── 01-project-name/
│   ├── main.py              program code
│   ├── README.md            project instructions
│   ├── requirements.txt     package list, when provided
│   └── .venv/               local environment, not uploaded
├── 02-project-name/
└── ...                      more project folders over time
```

The project names above are illustrative. Keep all numbered folders directly under `30daychallenge`, not inside the previous day’s folder. Do not create another Git repository inside each daily folder.

## Understand files, folders, and commands

**There are three places you work:**

| Place | What belongs there |
| --- | --- |
| VS Code editor | Python code in `.py` files; documentation in `.md` files; package names in `requirements.txt`. |
| Terminal | Commands such as `cd`, `uv pip install`, and `.venv/bin/python main.py`. |
| GitHub Desktop | Review changed files, write a commit summary, commit, and push. |

In a tutorial, a `bash` code block normally contains Terminal commands. A `python` block contains code to save in a Python file. The labels and the triple backtick fences are formatting; do not copy them into your file or Terminal.

### Terminal works inside one folder at a time

Run these commands to see your current location and its files:

```bash
pwd
ls
```

- `pwd` prints the current folder’s full location.
- `ls` lists its visible files and folders.
- `ls -a` also shows hidden items such as `.venv`.
- `cd` changes the current folder.
- `~` means your home folder, such as `/Users/your-name`.

For example, this command returns to the repository root from anywhere:

```bash
cd ~/Documents/GitHub/30daychallenge
```

Run commands one at a time when learning. If `cd` reports an error, stop and fix the path before running the next command. Otherwise, the next command could run in the wrong folder.

Text such as `your-name@MacBook ~ %` is the Terminal **prompt**, not something you type. Seeing the prompt again normally means the command finished. A running app may keep Terminal busy until you quit it.

### Saving a file is part of running it

Creating a folder does not create its program. Installing packages does not create `main.py`. A file must exist on disk before Python can run it.

Create files in VS Code’s Explorer, give them the exact name requested, paste the code, and press **⌘S**. Check that `main.py` is not accidentally named `main.py.txt`, and that it sits beside `.venv`, not inside it.

VS Code may show `project/.venv` together on one line when it compacts nested folders. Those are still two folders; put your code in the project folder.

## The routine for every project

The following uses **`08-my-project` as a reusable example**, not the curriculum’s actual Day 8 title. Substitute your real numbered folder wherever this example appears. For an existing project, use its folder and files instead of creating duplicates.

### 1. Define the smallest thing you want working

Read the day’s idea and describe one observable result: “A key plays a tone,” or “The camera window shows my face.” Then identify its inputs, output, dependencies, and required files.

Check the project README for operating-system requirements, Python version, entry filename, and any assets or accounts. `main.py` is our usual entry filename, but follow a different filename if the project specifies one.

### 2. Start from the repository root

For a new project, run each line in order:

```bash
cd ~/Documents/GitHub/30daychallenge
mkdir -p 08-my-project
cd 08-my-project
pwd
```

The final path should end in `/30daychallenge/08-my-project`. This check prevents creating today’s work inside yesterday’s folder.

### 3. Create its Python environment once

Inside that project folder:

```bash
uv venv --python 3.12
```

This creates `.venv`. Do this for a new project or if its environment is missing, rather than recreating it every time you run the app. A cloned repository normally does not include `.venv`.

The guide uses the environment’s Python directly, so **activation is not required**. Closing Terminal does not delete the environment. See [uv’s environment guide](https://docs.astral.sh/uv/pip/environments/).

### 4. Install only that project’s dependencies

If the project includes `requirements.txt`, run:

```bash
uv pip install --python .venv/bin/python -r requirements.txt
```

This tells uv exactly which environment to install into. Run it from the project folder. `requirements.txt` must exist there first; the command does not create it.

If there is no requirements file, use the package installation command given in the project’s README or build instructions. Ask for the exact package names and compatible versions if they are unclear. Do not install every challenge library at the start.

When documenting a new project, create `requirements.txt` in VS Code and list the packages it needs, one per line, using the versions you tested. Ask AI to help identify them from the code and your installation results. Keep this file with the source so someone else can recreate the setup.

For example, `pygame==2.6.1` means “install this specific version of Pygame.” Version pins help recreate the setup used by the project. Installing the newest version of everything may break older code.

Standard-library modules such as `time`, `math`, and `pathlib` are included with Python. Import names do not always match package names: for example, `cv2` comes from an OpenCV package. Check the requirements rather than guessing an installation command from the import.

### 5. Create and save the program

In VS Code, right-click the daily project folder → **New File**, name it `main.py`, and write or paste the code there. Press **⌘S**.

If using VS Code’s Run button, select the matching interpreter first: open the Command Palette with **⌘ShiftP**, choose **Python: Select Interpreter**, and select that project’s `.venv/bin/python`. Use **Enter interpreter path** if it is not listed.

The explicit Terminal command below is the clearest first run because it shows which Python you are using and leaves errors visible.

### 6. Add any required files or permissions

If the app needs music, an image, or a model, place the file where the code expects it and use the exact filename. Keep it outside `.venv`. Some files are deliberately not included in the GitHub repository, so a new reader must provide their own.

Changing `song.webm` to `music.mp3` changes its name, not its audio format. On macOS, this command can identify a file named `music.mp3` in your current folder:

```bash
file music.mp3
```

Use the project’s supported formats or ask for a conversion based on that result. A missing or unreadable asset can stop an app before its window opens.

Allow camera or microphone access when a project needs it. On macOS, review **System Settings → Privacy & Security → Camera or Microphone** for the app running Python, such as Terminal or VS Code.

### 7. Run and check one feature at a time

From a new Terminal, an example launch is:

```bash
cd ~/Documents/GitHub/30daychallenge/08-my-project
.venv/bin/python main.py
```

The second line means “use this project’s Python to run this file.” It works independently of which Python version the plain `python3` command chooses.

First confirm the app starts. Then test its main input and output, then its extra controls, and finally quitting. Click inside a graphical app before using its keyboard shortcuts. A terminal-only app will not necessarily open a separate window.

Keep the Terminal window open while the program runs. Use the documented quit key, close the app window, or use **Control+C in Terminal**. Stop the previous copy before launching another copy, especially when it uses the camera or microphone.

After changing code, save and restart the app. Most plain Python scripts do not reload edits automatically.

### 8. Document what actually happened

Update the project README with its setup, launch command, controls, expected result, and known limitations. Record whether you tested a feature or merely implemented it. Add its link to the main README’s project table.

### 9. Save a version and upload it

These are separate actions:

```text
Save in VS Code → Commit in GitHub Desktop → Push to GitHub
```

- **Save:** writes your current edits to your computer.
- **Commit:** records a named version in the local repository’s history.
- **Push:** uploads committed versions to GitHub.

In GitHub Desktop:

1. Select the correct repository and branch. For this solo challenge, the examples use `main`.
2. Click **Fetch origin** and review any incoming changes. If asked to pull, bring those changes into your local copy before pushing; ask for help if a conflict appears.
3. In **Changes**, inspect the files and select only the intended ones.
4. Enter a meaningful summary, such as `Add keyboard tone controls and setup guide`.
5. Click **Commit to main**.
6. Click **Push origin**.
7. Open your repository in a browser, refresh it, and check the new folder and README.

**Changes** shows edits that have not been committed. Once committed, those files appear in **History** instead. An upward arrow with a number beside **Push origin** means commits are still waiting to upload. “No local changes” does not prove that a push succeeded.

You can run a local app before committing or pushing it. GitHub is not required to start your Python program. See GitHub’s [guide to pushing from Desktop](https://docs.github.com/en/desktop/making-changes-in-a-branch/pushing-changes-to-github-from-github-desktop).

### What belongs in GitHub?

Upload the source code, instructions, package lists, and appropriate example assets. Usually leave out `.venv`, generated caches, private credentials, and personal media files. Share only media you have permission to distribute.

The root `.gitignore` tells Git which untracked files to leave out. For a new challenge repository, its Python template should include `.venv/` and `__pycache__/`. Add `.DS_Store` for Finder metadata. If a particular project uses a local song, add its specific path to `.gitignore` before committing that file.

Ignoring a file does not remove it from a previous commit. If a file is already tracked and should stop being shared, ask how to untrack it while retaining your local copy.

## Restart a project another day

You do not need the AI chat to remain open. Saved files and installed packages remain on your computer.

1. Open Terminal.
2. Change to the existing project folder.
3. Run its existing program with its environment’s Python.

For the same illustrative folder:

```bash
cd ~/Documents/GitHub/30daychallenge/08-my-project
.venv/bin/python main.py
```

If you downloaded or cloned the repository onto a new computer, recreate `.venv` and install that project’s dependencies first. Install again when its dependencies change. If a package is already installed in the correct environment, you do not need to reinstall it every session.

## Use AI as a learning partner

Give the assistant enough context to avoid guessing: your operating system, chip, RAM, Python version, exact project folder, intended behavior, and current code or README. An assistant in a new chat may not know what you built yesterday.

### A reusable starting prompt

Copy this into your AI chat and replace the bracketed details. **This is a chat prompt, not a Terminal command.**

> I am a complete Python beginner doing a 30-day challenge, about one hour per day. My computer is [operating system, chip, RAM]. I use VS Code, GitHub Desktop, uv, and Python [version]. All daily projects live inside one repository at [local path]. Today’s project is [name and plain-language goal]. I want to create and edit the files myself. Do not run commands or create files for me. Explain unfamiliar terms. Separate Terminal commands from Python code. Give the exact folder, filename, save step, run command, and expected result. Start with the smallest working version, then help me add features. Use compatible dependency versions and explain what each dependency does.

If you prefer one complete answer, add: “Give me the complete instructions in one message, with numbered steps and a complete file to paste.” If you prefer checkpoints, add: “Give me one step at a time and wait for my result.”

### Learn from working code

Before running unfamiliar code, ask what input it reads, what output it produces, whether it saves files, and what packages it needs. After it works, use questions such as:

- “Explain the main loop in plain language, then ask me a question to check my understanding.”
- “Which variable controls this behavior? Predict what will happen if I change it.”
- “Give me one small improvement I can implement myself. Start with a hint.”
- “Review my explanation of this function and correct misunderstandings.”

Change one small thing, predict the result, run it, and compare. That connects copied code to understanding. You do not need to understand the entire library to explain the part your app uses.

### Ask for debugging help with evidence

Instead of only saying “it doesn’t work,” provide this information:

```text
Project and operating system:
What I expected:
What happened instead:
Exact command I ran:
Current folder (output of pwd):
Complete error message:
Relevant code or the file I changed:
What I already tried:
```

Ask the assistant to identify the likely cause and explain the proposed fix before suggesting a rewrite. Apply one fix at a time. If it is unsure about an audio format or filename, provide the diagnostic result instead of repeatedly renaming or reinstalling things.

Before sharing your work, you can ask: “Read my code and README as if you have never seen this project. Identify missing setup steps, required assets, unclear controls, and claims that the code does not support. Distinguish what you checked from what still needs testing on my computer.”

### Keep control of the work

AI can suggest broken code, outdated package names, or commands for a different operating system. Ask it to verify uncertain installation instructions against official documentation. Do not paste passwords, API keys, or private recordings into a chat or repository.

Keep a working Git commit before a large change. If you authorize an assistant to edit or push, specify the files and ask for a summary of changes and checks. “Syntax passed” means Python can parse the file; it does not prove that the camera, sound, or gestures work on your computer.

Describe contributions honestly. For example: “Built with AI assistance; I tested the controls and adjusted the thresholds.” If you reuse someone else’s code or assets, keep the required notices and acknowledge the source. Rewording a README does not change where reused code came from.

## Use your one hour

Treat this as a flexible routine, not a deadline to rush past errors:

| Time | Focus |
| --- | --- |
| 0–5 minutes | Read the goal and define the smallest observable result. |
| 5–15 minutes | Open the correct folder, prepare dependencies, and check inputs. |
| 15–35 minutes | Build and run the smallest version. |
| 35–45 minutes | Test controls, fix one issue, or make one small change. |
| 45–55 minutes | Explain what you learned and update the README. |
| 55–60 minutes | Review files, commit, push, and note the next step. |

The initial tool installation may take an extra setup session. Download speeds and debugging can also exceed the schedule. At the end of an unfinished session, record what works, the exact blocker, and the next step. Commit useful progress with an accurate message instead of claiming the project is finished.

## Write documentation someone else can follow

A useful project README answers these questions without relying on your AI conversation:

1. **What does it do?** One plain-language paragraph and, when useful, a screenshot.
2. **What must I already have?** Operating system, Python version, hardware, accounts, and any OS-specific restrictions.
3. **How do I prepare it?** Exact folder, environment, and package installation steps.
4. **What files do I supply?** Filenames, supported formats, locations, and which assets are not included.
5. **How do I start and stop it?** A copyable launch command, permission prompts, controls, and expected output.
6. **How do I check it works?** A short, observable sequence someone can repeat.
7. **What might fail?** Common errors and fixes based on actual experience.
8. **What are its limits?** Experimental behavior, missing features, and what was actually tested.
9. **What did I learn or reuse?** Main concepts, references, required notices, and any AI assistance worth explaining.

Link this general guide near the top of each README when editing it. Keep project-specific setup in the project README so a reader does not need to infer which packages, permissions, or assets apply.

## Troubleshooting

Start with the final error line, but keep the full message when asking for help. Warnings and informational messages do not always mean the program failed.

| Symptom | What to check first |
| --- | --- |
| `command not found: uv` | Close and reopen Terminal after installation. If necessary, follow the installer’s PATH instructions. |
| `can't open file ... main.py` | The file is absent from that location. Check `pwd` and `ls`, save it in the right project folder, and verify its exact name. |
| `no such file or directory: .venv/bin/python` | You are in the wrong folder or that project has no environment yet. Check `pwd` and `ls -a`, then create its environment if missing. |
| `ModuleNotFoundError` | Install the project’s requirements into the same environment used to run it. Check VS Code’s interpreter if the Run button behaves differently. |
| A new feature does not appear | Save the file with ⌘S, stop the previous app, and rerun the correct file. |
| Camera or microphone unavailable | Check permission for the app running Python, the selected device, and whether another app is using it. |
| No music or window | Read Terminal first; missing assets or decoding errors can stop the app before it opens a window. |
| A file called `.mp3` cannot be decoded | Inspect its actual format. Renaming is not conversion. |
| Keyboard controls do nothing | Click the app window first and check whether its quit key differs from its action keys. |
| An installation download fails | Check the connection, retry, and capture the error. A package download failure is not necessarily a code problem. |
| A dependency cannot be built or resolved | Check Python, operating system, architecture, and pinned versions before installing compilers or changing many packages. |
| Day’s files disappeared from **Changes** | Look in **History**; they may already be committed. |
| GitHub still shows old files | Push committed changes, refresh the correct repository and branch, and check whether the push actually succeeded. |
| Hundreds of environment files appear in GitHub Desktop | Check `.gitignore` and whether `.venv` was already tracked. Upload the source and requirements, not the environment. |

For an installation certificate problem on macOS, uv can try the system certificate store. With the requirements file present and from the project folder:

```bash
uv --system-certs pip install --python .venv/bin/python -r requirements.txt
```

This is an option to try, not a fix for every connection error; see [uv’s certificate documentation](https://docs.astral.sh/uv/concepts/authentication/certificates/). Keep certificate verification enabled. A failed GitHub push leaves your local commit intact; it still needs uploading after the connection problem is resolved.

## Daily checklist

- [ ] I know the one thing this project should demonstrate.
- [ ] I am in the correct daily folder directly under my repository.
- [ ] The environment exists and contains the required packages.
- [ ] My program is saved with the correct filename outside `.venv`.
- [ ] Required files and permissions are ready.
- [ ] I tested startup, the main feature, and quitting—or documented what is blocked.
- [ ] I can explain at least one part of the code and one change I made.
- [ ] My README matches what the program actually does.
- [ ] I reviewed the files, committed useful progress, and checked the push result.
- [ ] I left a note about the next step if the project is unfinished.

## Windows differences

The learning routine is the same, but use **PowerShell** for commands and **Ctrl+S** to save in VS Code. Download the Windows versions of VS Code and GitHub Desktop. Install uv using a Windows method in the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/), then reopen PowerShell and run `uv python install 3.12`.

If you clone the repository under your Windows Documents folder, substitute its actual path. For example:

```powershell
cd "$HOME\Documents\GitHub\30daychallenge\08-my-project"
uv venv --python 3.12
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

This assumes the example folder and requirements file already exist. Windows installations using OneDrive may put Documents elsewhere; use the path shown in GitHub Desktop. Use `Get-Location` and `Get-ChildItem -Force` to inspect the folder. The macOS `file` command is not included by default.

Permissions are managed in Windows Settings. macOS automation code, including `osascript`, will need a Windows-specific replacement. The repository’s projects have not all been verified on Windows.
