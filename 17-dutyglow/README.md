# DutyGlow — Day 17

Slide a control, watch a square wave change, and see a virtual LED dim. DutyGlow simulates **PWM**, pulse-width modulation: the trick microcontrollers use to dim LEDs and slow motors with a pin that can only be fully on or fully off.

New to Python? Start with the [general beginner guide](../BEGINNER_GUIDE.md). It explains installing tools, environments, Terminal commands, commits, and pushing work to GitHub.

Inspired by [PWMSimulator](https://github.com/adhamollanazarov-cmyk/BuildCored_Orcas). That version is a matplotlib window with two channels. DutyGlow is a pygame window with one channel, plus a slow-motion mode where the LED really blinks and a breathe mode where it fades by itself.

## What PWM is

A microcontroller pin, like the ones on an Arduino or ESP32, has only two states:

- **HIGH:** full voltage, 3.3 V here.
- **LOW:** 0 V.

It cannot output "half" a voltage. To fake it, the pin switches on and off very fast:

| Term | Meaning |
| --- | --- |
| Period | Time for one full on-and-off cycle; 1 ms at 1000 Hz |
| Frequency | Cycles per second, in Hz |
| Duty cycle | The percentage of each period the pin is HIGH |
| Average voltage | 3.3 V × duty cycle |

At 25% duty, the pin is on for 0.25 ms and off for 0.75 ms, again and again. The average is 3.3 × 0.25 = 0.825 V. An LED blinking 1000 times a second is too fast for your eye, so you see a steady glow at about a quarter brightness.

The same trick controls motor speed, servo positions, speaker tones, and screen backlights.

No AI model is used today. Everything is simple math and drawing.

## What you see

| Part | What it shows |
| --- | --- |
| Duty cycle slider | The setting from 0% to 100% |
| Virtual LED | The brightness your eye would see, with a glow around it |
| Square wave | The pin's voltage over 8 periods: up at 3.3 V, down at 0 V |
| Green dashed line | The average voltage |
| Bottom numbers | Period, HIGH time, LOW time, and average voltage |
| Yellow dot | In slow motion, where "now" is inside the current period |

## Before starting

You need Python 3.12, uv, and `pygame`, listed in `requirements.txt`. No microphone, webcam, Ollama, paid API, or cloud account is needed. Installing pygame needs internet once. After that, DutyGlow works offline. The example setup is macOS-first.

## Files

| Item | Purpose |
| --- | --- |
| `main.py` | PWM math, LED, square wave, slider, controls, and self-test |
| `requirements.txt` | The pygame version used when this project was built |
| `.gitignore` | Excludes the environment, cache files, and saved screenshot |
| `.venv/` | Local Python environment |
| `dutyglow.png` | Screenshot written only when you press **S** |

## First-time setup

These commands assume the repository lives at the example path. Substitute your actual location if needed.

```bash
cd ~/Documents/GitHub/30daychallenge/17-dutyglow && uv venv --python 3.12 && uv pip install -r requirements.txt
```

**Run these commands inside `17-dutyglow`.** If `.venv` and `main.py` appear at the top level of `30daychallenge` instead, the commands ran in the wrong folder. Delete those two misplaced items and run the setup again from this folder.

Skip environment creation if this project's `.venv` exists.

## Check the math first

```bash
.venv/bin/python main.py --test
```

This runs 11 checks without opening a window. It confirms the average-voltage formula, the timing numbers, and the LED behavior. It also simulates the pin 100,000 times and confirms the real average equals 3.3 V × duty cycle. You should see:

```
11/11 checks passed
```

If nothing prints at all, you are probably running an empty `main.py` from a different folder. Run `pwd` and confirm you are in `17-dutyglow`.

## Run DutyGlow

```bash
.venv/bin/python main.py
```

Try these in order:

1. **Drag the slider.** The wave's HIGH parts get wider or thinner, and the LED gets brighter or dimmer.
2. **Press F until it shows 1 Hz.** The LED really blinks, and a yellow dot runs along the wave. At 70%, it is on for 0.7 s and off for 0.3 s.
3. **Press F again to reach 1 kHz.** The same blinking, 1000 times faster, now looks like a steady dim glow.
4. **Press B.** Breathe mode sweeps the duty cycle up and down by itself, like a sleeping laptop's light.

## Controls

| Input | Action |
| --- | --- |
| Drag the slider | Set the duty cycle |
| **←** / **→** | Change the duty cycle by 1% |
| **↑** / **↓** | Change the duty cycle by 10% |
| **F** | Cycle the frequency: 1, 2, 5, 100, 1000 Hz |
| **B** | Turn breathe mode on or off |
| **S** | Save the screen as `dutyglow.png` beside `main.py` |
| **Q** or **Esc** | Quit |

Moving the slider or pressing an arrow key also stops breathe mode.

## Slow motion and fast PWM

| Frequency | What the LED does | Why |
| --- | --- | --- |
| 1, 2, 5 Hz | Fully on, then fully off | Each flash is slow enough for your eye to see |
| 100, 1000 Hz | Steady glow at duty-cycle brightness | Too fast to see; your eye averages the light |

The wave always shows 8 periods, so its shape looks the same at every frequency. Only the time labels change: 1 Hz has a 1000 ms period and 1000 Hz has a 1000 µs period.

This simulation is simplified. The program switches at 10 Hz between "blinking" and "averaged", while real eyes blend flicker gradually, often somewhere above 50–90 Hz. Brightness is also drawn as directly proportional to duty cycle. Real eyes are more sensitive to changes in dim light, so real LED projects often apply a curve, called gamma correction, to make fading look smooth.

## Check that it works

1. Run `--test` and confirm 11/11 checks pass.
2. Set 0% and confirm the LED is dark and the average is 0.00 V.
3. Set 100% and confirm the wave is a flat line at 3.3 V.
4. Set 25% at 1 kHz and confirm the numbers read period 1000 µs, HIGH 250 µs, LOW 750 µs, average 0.82 V.
5. Switch to 1 Hz and confirm the LED blinks in time with the yellow dot.
6. Press **B**, then **S**, and open `dutyglow.png`.

## Settings you can change

Edit these near the top of `main.py`, save, and rerun:

| Setting | Default | Effect |
| --- | --- | --- |
| `VCC` | 3.3 | Pin voltage; try 5.0 for an Arduino Uno |
| `FREQUENCIES` | 1, 2, 5, 100, 1000 | Choices for the **F** key |
| `BLINK_LIMIT` | 10 | At or below this frequency the LED blinks visibly |
| `PERIODS_SHOWN` | 8 | Number of periods drawn |
| `BREATHE_SECONDS` | 4 | Length of one breathe fade in and out |
| `LED_ON` | warm yellow | LED color as red, green, blue values |

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `--test` prints nothing | You ran an empty file in another folder. Run `pwd` and `ls -a`; you should be in `17-dutyglow`. |
| `no such file or directory: .venv/bin/python` | The environment is missing from this folder. Run the setup command above. |
| `ModuleNotFoundError: No module named 'pygame'` | Install requirements, then launch with `.venv/bin/python`. |
| Keys do nothing | Click the DutyGlow window first so it has keyboard focus. |
| Slider doesn't move | Click on or near the slider line, then drag. |
| Window does not appear | Look behind other windows or in the Dock. |

## What I practiced

Built with AI assistance: duty cycle, period, and frequency; why average voltage equals VCC × duty cycle; proving that formula by simulation; persistence of vision; mapping values to screen coordinates; drawing a square wave as a list of corner points; mouse dragging and keyboard input in pygame; transparent glow effects; and a self-test that checks the math without a window.
