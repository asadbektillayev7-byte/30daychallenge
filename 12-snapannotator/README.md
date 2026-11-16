# SnapAnnotator — Day 12

Take a webcam photo and label recognized objects with boxes and confidence scores. The app shows a live preview, runs a local object detector when you press Space, and saves the original and annotated images.

New to Python? Read the [general beginner guide](../BEGINNER_GUIDE.md) first. It explains downloads, VS Code, Terminal, environments, saving files, and GitHub uploads. The instructions here use macOS and the repository's existing folder layout.

## What the AI does

This project uses **YOLOv8n**, a pretrained object detector from Ultralytics, rather than the text model used in the earlier Ollama projects. It finds objects belonging to 80 COCO categories and returns a name, score, and bounding box. OpenCV handles the camera, display, drawing, and image saving. See the [YOLOv8 documentation](https://docs.ultralytics.com/models/yolov8/).

It does not describe an entire scene, read text, recognize a person's identity, or learn new categories from your photos. Objects outside its categories can be missed or mislabeled. Ollama is not needed.

## Before starting

You need Python 3.12, uv, a webcam, permission to use it, and the packages listed in `requirements.txt`. Downloading the packages needs internet. The PyTorch installation is substantial; allow time and disk space rather than expecting just the small model download.

The pinned requirements reproduce the versions found in the builder's Intel Mac environment. They are not a promise that the same wheels work on every operating system or architecture. CPU detection may pause the preview while a photo is analyzed.

No microphone, input music file, paid API, or cloud account is required for this configuration.

## Files and what is actually shared

| File | Purpose |
| --- | --- |
| `main.py` | Camera preview, snapshot detection, annotation, and saving |
| `requirements.txt` | Packages pinned to the inspected environment |
| `yolov8n.pt` | Pretrained model weights, currently included in this repository |
| `snap.jpg` | Latest original photo; an existing example is currently tracked in Git |
| `snap_annotated.jpg` | Latest annotated photo; an existing example is currently tracked in Git |
| `.venv/` | Local Python environment, excluded from Git |

**The photos and model are already tracked in this repository.** A clone includes their committed versions. Taking a new photo replaces your local copies and can make them appear in GitHub Desktop's Changes tab. Review those images before deciding whether to commit them. Do not assume they are automatically private or ignored.

## First-time setup

Clone the repository and open it in VS Code as described in the general guide. If it lives somewhere other than the example path, substitute its actual location.

In Terminal:

```bash
cd ~/Documents/GitHub/30daychallenge/12-snapannotator
uv venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```

If this project's `.venv` already exists, skip recreating it and just install the requirements. `main.py` is included in the repository; if building manually, save it directly in this folder, outside `.venv`.

For a certificate-related download failure, try:

```bash
uv --system-certs pip install --python .venv/bin/python -r requirements.txt
```

For a slow connection on macOS, you can also try allowing more time and limiting concurrent downloads:

```bash
UV_HTTP_TIMEOUT=300 UV_CONCURRENT_DOWNLOADS=1 uv --system-certs pip install --python .venv/bin/python -r requirements.txt
```

These commands cannot fix every network error. Read the full message before changing Python or package versions. Completed package downloads may be cached, but an interrupted download is not guaranteed to resume from its last byte.

### Why these versions are pinned

The inspected environment uses Ultralytics 8.4.211, OpenCV 4.10.0.84, NumPy 1.26.4, PyTorch 2.2.2, and torchvision 0.17.2. Keeping that combination avoids silently choosing newer packages that may not work together on the builder's Intel Mac.

In particular, this older PyTorch environment needs NumPy 1.x for its NumPy bridge. If NumPy 2.x was installed and detection reports `Numpy is not available`, reinstall the listed requirements in the correct environment. You do not need to replace packages used by other daily projects.

The inspected environment also contains a supporting-package conflict: `contourpy 1.4.0` requires NumPy 2. A dry-run of the requirements install resolves this by selecting `contourpy 1.3.3` instead. The documentation update does not alter the installed environment. To apply that resolution yourself, run the requirements installation above, then check:

```bash
uv pip check --python .venv/bin/python
```

This should report compatible packages after the installation succeeds. A successful dependency check still does not test the webcam or detection accuracy.

## Run and take a photo

```bash
cd ~/Documents/GitHub/30daychallenge/12-snapannotator
.venv/bin/python main.py
```

The code prints a first-download message whenever it loads the detector, even if the weights already exist. With the included valid `yolov8n.pt`, it should load the local file. If the weights are missing, Ultralytics may need internet to obtain them.

Allow camera access when macOS asks. If blocked, check **System Settings → Privacy & Security → Camera** for the app running Python, such as Terminal or VS Code.

1. Wait for `Camera ready` and the live video window.
2. Click inside the video window so it receives your key presses.
3. Place a common object such as a cup or book in view and hold it still.
4. Press **Space**. The app analyzes that frame, lists detections in Terminal, and shows the annotated photo.
5. Press a key to return to live preview, or **Q** to quit.

Detection happens on the captured frame, not continuously on every preview frame. The interface can pause while inference runs.

## Controls

| Key or action | Result |
| --- | --- |
| Space in live preview | Capture, detect, draw labels, and save both images |
| Any key on the result screen, except Q | Return to live preview |
| Q in either screen | Exit |
| Control+C in Terminal | Interrupt and release the camera |

Keys belong in the video window. After a result is shown, pressing Space returns to live preview; press it again there to take another photo.

## Read the result

An example Terminal result could look like:

```text
Found 2 object(s):
  cup: 91%
  laptop: 84%
```

This is an illustration, not a guaranteed result or a measurement from your camera. The confidence score expresses the detector's confidence in a label; it is not a calibrated guarantee of correctness.

The default threshold is `CONFIDENCE = 0.35`. Detections below that score are not displayed. Raising it can remove weaker guesses; it does not make every remaining label correct. Poor light, blur, distance, and unusual angles can affect results.

## Saved photos and offline use

Each successful analysis writes `snap.jpg` and `snap_annotated.jpg` beside `main.py`. A new snapshot replaces the previous images. Copy them elsewhere first if you want to keep several results.

The original photo is written before detection, so an analysis failure can leave a new `snap.jpg` beside an older annotated image. The code does not check OpenCV's image-write return values; if no files appear despite the saved message, check folder permissions, space, and the filenames in Finder.

The application code runs inference locally and does not explicitly upload webcam frames. Photos can still be shared if you commit and push them. After dependencies and weights are available, test offline behavior by turning off Wi-Fi and repeating a snapshot.

## Check that it works

1. Launch and confirm a live preview appears.
2. Press Space with a recognizable object visible; inspect the boxes and Terminal list.
3. Return to preview and try a different object.
4. Inspect both saved files and compare their modification times.
5. Try a scene with few recognizable objects. An empty detection list is possible, but not guaranteed even with a covered lens.
6. Repeat with Wi-Fi off after setup to check local operation.
7. Quit with Q and confirm the camera window closes.

These checks concern your computer and scene. Syntax and package checks alone do not verify detection accuracy or camera behavior.

## Settings and troubleshooting

Edit `main.py`, save with **⌘S**, stop the running app, and restart it.

- `CONFIDENCE`: the minimum displayed score, initially 0.35.
- `MODEL_FILE`: path to compatible detection weights. Another model may require extra downloads or more memory.
- `PHOTO_PATH` and `ANNOTATED_PATH`: where snapshots are written.

| Problem | What to check |
| --- | --- |
| Camera unavailable or lost image | Check permissions and the selected camera index; close other camera apps and restart. |
| `Numpy is not available` or a NumPy compatibility warning | Check the environment and reinstall the pinned requirements, especially NumPy 1.26.4. |
| Model load fails | Check that `yolov8n.pt` is present and valid; read the full error. Missing weights may require internet. |
| Keys do nothing | Click the video window; input in Terminal is not read as camera controls. |
| No objects recognized | Improve light, hold still, or try a larger object from the detector's known categories. |
| Wrong labels | Recognition is approximate; retake the image and inspect the score. |
| Photos appear in GitHub Desktop | They are already tracked in this repository. Review them before committing; adding an ignore rule alone would not untrack them. |
| Missing source or interpreter | Run `pwd` and `ls -a`; save `main.py` in the correct folder or create its environment. |
| Missing packages | Install requirements with the same `.venv/bin/python` used to launch. |

## What I practiced

Built with AI assistance: reading webcam frames, using a pretrained detector, extracting boxes and scores, drawing annotations, handling window controls, and resolving package compatibility. YOLOv8n is an existing Ultralytics model; it was not trained by this project.
