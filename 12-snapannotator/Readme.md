# SnapAnnotator · Day 12

Press a key and your webcam takes a photo. A small AI model looks at the photo and draws a labeled box around each everyday object it recognizes, with a confidence score such as `cup - 91%`. It saves the annotated photo and prints the list in Terminal.

> **New to coding?** Start with the general beginner guide. It explains installing tools, opening the correct folder, creating environments, saving files, and uploading changes.

## What is different in this project?

Days 10 and 11 used a local language model through Ollama. That model, `qwen2.5:0.5b`, only reads and writes text, so it cannot look at a photo. SnapAnnotator uses a different kind of AI:

- **YOLOv8n** is a small object-detection model. It takes an image and returns a list of objects, each with a name, a confidence score and a box.
- **OpenCV** opens the webcam, shows the live preview, draws the boxes and saves the images.
- Ollama is **not used** in this project.

This is object detection, not a model that understands a scene. It matches objects to a fixed list of 80 everyday categories. It does not describe what is happening in the photo, read text, or recognize who someone is.

## Before starting

You need:

- Python 3.12 and `uv`.
- OpenCV, NumPy and Ultralytics from this folder's `requirements.txt`.
- A working webcam and permission for Terminal to use it.
- Internet for the first package download and the first model download. Detection works offline afterward.

There is no microphone, paid cloud API or account involved. The photo is analyzed on your computer and is not uploaded anywhere.

The install is large, roughly 1 GB, because Ultralytics brings in PyTorch. On the builder's Intel MacBook Air, detection runs on the CPU, so it can take a moment after you press SPACE.

## Files

| Item | Purpose |
| --- | --- |
| `main.py` | Webcam preview, object detection, box drawing, and saving |
| `requirements.txt` | Direct Python dependencies pinned to the installed versions |
| `.gitignore` | Keeps the environment, photos and model file out of Git |
| `.venv/` | Local environment, excluded from Git |
| `snap.jpg` | The latest original photo, created after you press SPACE |
| `snap_annotated.jpg` | The latest photo with labeled boxes |
| `yolov8n.pt` | The model file, downloaded automatically on the first run (about 6 MB) |

The photos and model file are created on your computer and are excluded from Git. Cloning this repository does not include them, or the Python environment.

## First-time setup

### 1. Prepare the Python environment

The commands below assume this repository is cloned into `~/Documents/GitHub/30daychallenge`. Substitute its actual location if yours differs.

```bash
cd ~/Documents/GitHub/30daychallenge
mkdir -p 12-snapannotator
cd 12-snapannotator
uv venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```

If this project's `.venv` already exists, skip `uv venv` and install the requirements into it. Running `uv venv` again asks whether to replace the existing environment.

The source is included when you clone the repository. If building manually, save `main.py` directly inside `12-snapannotator`, outside `.venv`, before running it.

### 2. If a dependency download fails

A connection or certificate failure is different from a Python code error. To try your system's certificate store:

```bash
uv --system-certs pip install --python .venv/bin/python -r requirements.txt
```

On a slow or unstable connection, ask `uv` to wait longer and download one file at a time:

```bash
UV_HTTP_TIMEOUT=300 UV_CONCURRENT_DOWNLOADS=1 uv --system-certs pip install --python .venv/bin/python -r requirements.txt
```

Errors such as `dns error`, `Failed to download torch` or `InvalidContentType` mean the download was interrupted. Check your connection, switch networks if necessary, and run the same command again. `uv` keeps files that finished downloading, so each attempt can continue from where the previous one stopped.

### 3. Why NumPy is pinned

PyTorch 2.2.2 does not work with NumPy 2.x. If the installer picks NumPy 2.x, the program can start and open the camera, but detection fails with `Numpy is not available`. This project pins NumPy 1.26.4 and OpenCV 4.10.0.84 to avoid that. Check the version with:

```bash
.venv/bin/python -c "import numpy; print(numpy.__version__)"
```

It should print `1.26.4`.

## Start SnapAnnotator

```bash
cd ~/Documents/GitHub/30daychallenge/12-snapannotator
.venv/bin/python main.py
```

On the first run, macOS asks whether Terminal (or VS Code) may use the camera. Click **Allow**. The program also downloads `yolov8n.pt`, so connect to the internet for that run.

You should see `SnapAnnotator - Day 12`, then `Camera ready`, and a video window opens. If you cannot see it, check behind other windows. Click the video window so it receives your key presses.

1. Hold up an object, such as a cup, bottle, phone, laptop or book.
2. Press **SPACE**.
3. Wait for the detector. The annotated photo appears and the list prints in Terminal.
4. Press any key to return to the live view, or **Q** to quit.

## Controls

Keys are read from the video window, not from Terminal.

| Key | Result |
| --- | --- |
| SPACE | Save a photo and run detection |
| Any key (after a snap) | Return to the live preview |
| Q | Close the camera and quit |
| Control+C in Terminal | Interrupt the app and close it |

The window is busy while detection runs, and it may not respond for a moment.

## What the detector does

Each detection has a label, a confidence score and a rectangle. Terminal prints the list, and the image shows the same information:

```
Found 2 object(s):
  cup: 91%
  laptop: 84%
```

YOLOv8n is trained on 80 common object categories, such as person, cup, bottle, laptop, cell phone, chair, book and keyboard. It cannot name objects outside that list. A lamp or a plant pot may be missed or given a similar label. The confidence score is the model's own estimate, not a guarantee that the label is correct, and wrong labels are possible. Dim light, motion blur, small objects and unusual angles reduce accuracy.

The program only shows objects scoring at least `CONFIDENCE`, initially 0.35. Raise it for fewer, surer labels, or lower it to see more guesses.

## Output and privacy

After each snap, the program saves two images beside `main.py`:

- `snap.jpg`, the original photo.
- `snap_annotated.jpg`, the same photo with boxes and labels.

Taking another photo replaces both files, so copy or rename them first if you want to keep a photo.

The photos show your room and anything near the camera. They are kept out of Git by `.gitignore`. Check before you upload any image to a public repository.

## Check that it works

1. Confirm the first line says `SnapAnnotator - Day 12`.
2. Wait for `Camera ready` and the live video window.
3. Hold up a common object and press SPACE.
4. Confirm that Terminal lists at least one detection, and the window shows boxes with labels.
5. Press a key to return to the live view and take a second photo with a different object.
6. Hold up nothing recognizable, or cover the lens, and confirm you see `Nothing recognized`.
7. Quit with Q and confirm the video window closes and the normal Terminal prompt returns.
8. With the model already downloaded, turn off Wi-Fi and repeat steps 2 to 4 to check offline use.

These are interaction checks for your own computer and camera. They do not establish that every label is accurate.

## Settings you can change

Open `main.py`, change one setting at a time, save with ⌘S, quit the running app, and run it again.

- `CONFIDENCE`: minimum score for a detection to appear. The default is `0.35`.
- `MODEL_FILE`: model path. Using a larger YOLO model can improve accuracy, but it takes longer to download and run.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `Could not open the webcam` | Open System Settings > Privacy & Security > Camera and allow Terminal (or VS Code). Close other apps using the camera, such as video calls, then run again. |
| `Could not analyze the photo: Numpy is not available` | PyTorch found NumPy 2.x. Reinstall the pinned versions from `requirements.txt`. |
| A warning about NumPy 1.x and 2.x | Same cause. Check that NumPy prints `1.26.4`. |
| `dns error`, `Failed to download torch` or `InvalidContentType` | The download was interrupted. Check your connection, use a different network or a hotspot, and run the install command again. |
| `Could not load the model` | The first run needs internet to download `yolov8n.pt`. Connect and try again. |
| `can't open file main.py` | You are in the wrong folder, or the file is missing. Use `pwd` and `ls -a` to check the folder and the filename. |
| The video window does not appear | Look behind other windows, and check Terminal for an error message. |
| Keys do nothing | Click the video window first. Keys are read from that window, not from Terminal. |
| `Nothing recognized` | Use better light, move the object closer, and hold it still. You can lower `CONFIDENCE`. |
| Wrong or surprising labels | The detector knows only 80 categories and can be wrong. Compare the confidence score and retake the photo. |
| Slow detection | PyTorch runs on the CPU here. Close CPU-heavy apps and wait for the result. |
| Photos appear in Git | Check that `.gitignore` is in the project folder and lists the photo filenames. |

## Learning and implementation

Built with AI guidance: reading webcam frames with OpenCV, running an object-detection model, converting model output into boxes, labels and scores, drawing text and rectangles on an image, handling keyboard input, and solving a NumPy version conflict between PyTorch and the installer.

The detection model is YOLOv8n from Ultralytics. It is a pretrained model and was not trained or modified in this project.
