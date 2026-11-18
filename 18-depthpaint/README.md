# DepthPaint — Day 18

Your webcam guesses how far away everything is and paints it like a thermal camera. A small neural network called MiDaS looks at each ordinary webcam frame and estimates which parts are near and which are far. DepthPaint shows the camera on the left and the colored depth map on the right: warm red and pink for near, cool blue for far.

New to Python? Start with the [general beginner guide](../BEGINNER_GUIDE.md). It explains installing tools, environments, Terminal commands, commits, and pushing work to GitHub.

Inspired by [Asteria267/DepthMapper](https://github.com/Asteria267/DepthMapper). That version runs MiDaS through PyTorch with a matplotlib dashboard. DepthPaint runs the small official MiDaS model through OpenCV, so it only needs OpenCV and NumPy, and adds a thermal-camera look.

## What the AI does

Real depth sensors, like LiDAR in an iPhone or a self-driving car, measure distance by timing light that bounces back. A normal webcam can't do that. It only sees a flat picture.

**MiDaS** is a neural network trained on many images with known depth. From one flat picture it predicts, for every pixel, how close that spot probably is. This is called **monocular depth estimation**: depth from one camera. It uses clues people also use, like size, overlap, texture, and perspective.

Its answers are **relative**. It knows your hand is closer than the wall, but not that your hand is 40 cm away. DepthPaint never shows meters for this reason.

## What you see

| Part | Meaning |
| --- | --- |
| Left: camera | Your mirrored webcam image |
| Green NEAREST box | The biggest area of very close pixels |
| Right: heatmap | Thermal-style colors, from blue for far to red and pink for near |
| Right: grid | Press **G**: a blocky gray depth map, white for near and black for far |
| Color bar | The color scale, from NEAR on the left to FAR on the right |
| Mouse hover text | Over the right side: "closer than 83% of the scene" means that spot is nearer than 83% of the pixels |
| FPS | Frames per second |

### How the thermal look works

A pure depth map paints your whole face one color, because your face is all about the same distance away. Real thermal cameras show detail because hair, eyes, and glasses are cooler than skin.

DepthPaint copies that look:

```
heat = closeness × (0.55 + 0.45 × camera brightness)
```

- **Closeness** keeps the background blue and you warm.
- **Camera brightness** changes the color inside you: bright skin turns red and pink, while darker hair, eyebrows, and glasses turn yellow and green.
- A contrast boost called CLAHE keeps that detail visible in dim rooms. A small blur makes soft thermal-style patches.

**This is not real temperature.** Your hand looks "hot" because it is close and bright, not because it is warm. The grid mode shows pure depth, with no camera brightness mixed in.

## Before starting

You need:

- Python 3.12 and uv.
- A webcam and permission for Terminal or VS Code to use it.
- The packages in `requirements.txt`: NumPy and OpenCV.
- The MiDaS small model file, about 66 MB, downloaded once.

No PyTorch, Ollama, paid API, or cloud account is needed. Downloads need internet once. After that, DepthPaint works offline. The example setup is macOS-first.

## Files

| Item | Purpose |
| --- | --- |
| `main.py` | Model loading, depth estimation, thermal colors, grid mode, window, and controls |
| `requirements.txt` | Package versions used when this project was built |
| `.gitignore` | Excludes the environment, cache files, the model, and saved screenshots |
| `.venv/` | Local Python environment |
| `model-small.onnx` | MiDaS v2.1 small model; downloaded by you, not stored on GitHub |
| `depthpaint.png` | Screenshot written only when you press **Space** |

**The model is not in this repository.** It is too large for a normal commit and is published by the MiDaS authors. The setup command downloads it from the [official MiDaS release](https://github.com/isl-org/MiDaS/releases/tag/v2_1).

## First-time setup

Paste this in Terminal as one line. It creates the environment, installs the packages, and downloads the model:

```bash
cd ~/Documents/GitHub/30daychallenge/18-depthpaint && uv venv --python 3.12 && uv pip install -r requirements.txt && curl -L -o model-small.onnx https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx && ls -a
```

The list at the end should show `.venv`, `main.py`, and `model-small.onnx`. If `.venv` appears at the top level of `30daychallenge` instead, the command ran in the wrong folder.

The first run may trigger a macOS camera permission prompt. Allow it. If you clicked **Don't Allow** earlier, open **System Settings → Privacy & Security → Camera**, turn on the app you launch from, such as Terminal or Visual Studio Code, and restart that app.

## Run DepthPaint

```bash
.venv/bin/python main.py
```

Try these:

1. **Move your hand toward the camera.** It turns red, then pink, and the NEAREST box jumps to it.
2. **Lean back.** You cool down toward yellow and green.
3. **Hover the mouse** over the right side to read how close each spot is.
4. **Press G** to compare with the pure depth grid.

Without a webcam, use a photo:

```bash
.venv/bin/python main.py --image ../12-snapannotator/snap.jpg
```

Terminal may print a warning mentioning `AVCaptureDeviceTypeExternal` and `Info.plist`. It is a harmless OpenCV message about Mac cameras.

## Controls

| Input | Action |
| --- | --- |
| **G** | Switch between thermal heatmap and depth grid |
| **Space** | Save the window as `depthpaint.png` beside `main.py` |
| Mouse over the right side | Show how close that spot is compared with the rest |
| **Q** or **Esc** | Quit |

Closing the window also quits. Click the window first if keys do nothing.

## Options

| Option | Meaning |
| --- | --- |
| `--image PATH` | Use a photo instead of the webcam |
| `--help` | Show command-line help and exit |

## Speed and limits

On a MacBook Air CPU, DepthPaint runs at about **2 to 3 frames per second**, because the neural network runs for every frame. The original DepthMapper notes the same kind of lag. Smoothing blends each new frame with the previous one, so the picture flickers less but trails slightly when you move fast.

Other limits:

- Depth is relative to each frame. Colors re-stretch every frame, so the nearest thing is always warmest, even if everything moves back.
- The model sees a 256 × 256 version of the image, so fine edges like hair and fingers are soft.
- Mirrors, windows, glossy surfaces, and plain walls can confuse it.
- It is not a distance sensor and should not be used for safety or measurement.

## Check that it works

1. Run with `--image ../12-snapannotator/snap.jpg` and confirm both halves appear.
2. Run with the webcam and confirm the FPS number appears.
3. Move your hand close and confirm it turns red or pink, with the NEAREST box on it.
4. Hover over the background and confirm a low "closer than" percentage.
5. Press **G**, then **Space**, and open `depthpaint.png`.

## Settings you can change

Edit these near the top of `main.py`, save, and rerun:

| Setting | Default | Effect |
| --- | --- | --- |
| `FACE_DETAIL` | 0.45 | 0 = pure distance; higher shows more face detail in the colors |
| `SOFTNESS` | 2 | Higher = softer, blobby patches; 1 = sharper |
| `SMOOTHING` | 0.3 | Higher = calmer but trails more |
| `NEAR_LEVEL` | 0.85 | How close counts for the NEAREST box |
| `GRID_COLUMNS` | 16 | Number of blocks across in grid mode |
| `VIEW_WIDTH` | 480 | Width of each half of the window |
| `THERMAL_STOPS` | navy to pink-white | The color scale, as positions and red, green, blue values |

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `Model file not found` | Run the `curl` download command inside `18-depthpaint`. |
| Model fails to load | The download may be incomplete. Delete `model-small.onnx` and download it again; it should be about 66 MB. |
| `Could not open the webcam` | Check camera permission and close other apps using the camera, or use `--image`. |
| Very slow | Expected on CPU. Close other heavy apps, or lower `VIEW_WIDTH` slightly. |
| Face is one flat color | Raise `FACE_DETAIL` to 0.6. |
| Too noisy or patchy | Lower `FACE_DETAIL` or raise `SOFTNESS`. |
| `no such file or directory: .venv/bin/python` | The environment is missing from this folder. Run the setup command. |
| `ModuleNotFoundError` | Install requirements, then launch with `.venv/bin/python`. |

## What I practiced

Built with AI assistance: running a pretrained neural network with OpenCV's DNN module, preparing images for a model with resizing and normalization, monocular depth estimation, percentile stretching, building a custom color palette and applying it with a lookup table, local contrast with CLAHE, mixing two signals into one picture, finding the nearest object with contours, smoothing between frames, and mouse and keyboard input in OpenCV.

MiDaS was created by Intel ISL researchers and was not trained by this project.
