# BusTalk — Day 19

Simulate how chips talk to each other and watch the signals animate. BusTalk shows an **I2C** conversation between a main chip and small helper chips, slowed down so you can see every bit travel along the two wires.

New to Python? Start with the [general beginner guide](../BEGINNER_GUIDE.md). It explains installing tools, environments, Terminal commands, commits, and pushing work to GitHub.

Inspired by [Asteria267/I2CPlayground](https://github.com/Asteria267/I2CPlayground). BusTalk is our own pygame version with three simulated chips, a live logic-analyzer timeline, a conversation log, and a self-test.

## What I2C is, in simple terms

Inside almost every gadget there is one main chip, the "brain", plus smaller helper chips: sensors, screens, and memory. The brain has to ask the helpers for data and give them commands.

**I2C** does that with only **two wires**, shared by all the chips:

| Wire | Name | Job |
| --- | --- | --- |
| **SCL** | Serial clock | The brain ticks it on and off like a metronome. Every tick means "next bit now". |
| **SDA** | Serial data | Carries the actual 1s and 0s, one bit per tick. |

Because many chips share the same two wires, each one has an **address**, like a house number. In BusTalk, the IMU lives at 0x68 and the temperature sensor at 0x48.

The brain is called the **master** and the helper chips are called **slaves**. Newer documents also say controller and target.

## How a conversation goes

It works like a phone call:

1. **START:** the master says "attention, everyone".
2. **Address:** "Chip 0x68, I want to talk to you."
3. **ACK:** chip 0x68 answers "I'm here". If no chip has that address, nobody answers, and that is a **NACK**.
4. **Data:** the master sends bytes, or the chip sends bytes back.
5. **STOP:** the call ends.

In BusTalk, **green** means the master is talking and **blue** means a slave is answering. **Orange** marks a NACK from a missing chip.

### A few wire rules you can see

- **START** is the only time SDA falls from high to low while SCL is high.
- **STOP** is the only time SDA rises from low to high while SCL is high.
- During data, SDA changes only while SCL is low, and stays still while SCL is high. That is when the receiving chip reads the bit.
- **ACK** means the receiver pulls SDA low. **NACK** means nobody pulls it, so it stays high.
- The first byte is the 7-bit address plus one extra bit: 0 means write, 1 means read. That is why address 0x68 is sent as 0xD0 for writing and 0xD1 for reading.

## Where I2C is used in real life

- **Phones:** reading the motion sensor that rotates your screen, the light sensor that dims it, and the touch controller.
- **Smartwatches and fitness bands:** reading heart-rate and step sensors.
- **Laptops:** the battery chip that reports your percentage, and temperature sensors.
- **Arduino, ESP32, and Raspberry Pi projects:** small OLED screens, weather sensors, and motion sensors.
- **Cars, game controllers, and smart home devices.**

The IMU in BusTalk is modelled on the real **MPU-6050** motion sensor. It really lives at address 0x68 and really answers 0x68 when asked for its ID in register 0x75, called WHO_AM_I.

## Where you would use it

If you connect a sensor or a small screen to an Arduino, ESP32, or Raspberry Pi, you will use I2C. You connect four wires: power, ground, SDA, and SCL. A library then sends exactly the START, address, ACK, data, and STOP pattern shown in BusTalk.

When something does not work, engineers look at the wires with a tool called a **logic analyzer**. The timeline at the bottom of BusTalk is a simple version of one.

### How it connects to earlier days

| Day | Project | Hardware idea |
| --- | --- | --- |
| 14 | [RegisterBot](../14-registerbot/) | The brain: a tiny CPU with registers |
| 17 | [DutyGlow](../17-dutyglow/) | Controlling an LED from a pin with PWM |
| 19 | BusTalk | How the brain talks to other chips |

Together they are the basics of how real hardware works.

## The simulated chips

| Chip | Address | Registers | Based on |
| --- | --- | --- | --- |
| IMU | 0x68 | 0x75 WHO_AM_I = 0x68, 0x6B power = 0x40, 0x3B = 0x12 | MPU-6050 motion sensor |
| TEMP | 0x48 | 0x00 = 0x19, meaning 25 °C | Common temperature sensors |
| OLED | 0x3C | 0x00 = 0x00 | Small OLED displays |

A **register** is a tiny numbered memory slot inside a chip. Writing to one changes a setting; reading one returns data.

No AI model is used today. Everything is simulated in Python.

## Before starting

You need Python 3.12, uv, and `pygame`, listed in `requirements.txt`. No microphone, webcam, real hardware, Ollama, paid API, or cloud account is needed. Installing pygame needs internet once. After that, BusTalk works offline. The example setup is macOS-first.

## Files

| Item | Purpose |
| --- | --- |
| `main.py` | Simulated chips, I2C signal building, decoding, drawing, controls, and self-test |
| `requirements.txt` | The pygame version used when this project was built |
| `.gitignore` | Excludes the environment, cache files, and saved screenshot |
| `.venv/` | Local Python environment |
| `bustalk.png` | Screenshot written only when you press **S** |

## First-time setup

Paste this in Terminal as one line:

```bash
cd ~/Documents/GitHub/30daychallenge/19-bustalk && uv venv --python 3.12 && uv pip install -r requirements.txt && ls -a
```

The list should show `.venv` and `main.py`. If `.venv` appears at the top level of `30daychallenge` instead, the command ran in the wrong folder.

## Check, then run

This runs the protocol check and then opens the window:

```bash
.venv/bin/python main.py --test && .venv/bin/python main.py
```

The check should end with:

```
11/11 checks passed
```

It confirms the address bits, the read and write bytes, ACK and NACK behavior, the START and STOP rules, and that data bits never change while the clock is high.

When the window opens, a short demo plays by itself: a write, a read, and a read-back.

## Controls

| Key | What happens |
| --- | --- |
| **1** | Master writes 0xA5 into IMU register 0x6B |
| **2** | Master reads the IMU's WHO_AM_I register; the IMU answers 0x68 |
| **3** | Master reads the temperature chip; it answers 0x19, meaning 25 °C |
| **4** | Master reads IMU register 0x6B back, to prove the write from key 1 worked |
| **5** | Master calls 0x50, where no chip lives; nobody answers, so you see a NACK |
| **Space** | Pause or resume |
| **+** / **−** | Faster or slower: 2, 5, 10, 20, or 40 clock pulses per second |
| **S** | Save the screen as `bustalk.png` beside `main.py` |
| **Q** or **Esc** | Quit |

Pressing several number keys queues the conversations; they play one after another. Click the window first if keys do nothing.

## Read the screen

| Part | Meaning |
| --- | --- |
| MASTER and slave boxes | The chips; the one talking right now has a bright outline. The right box shows whichever chip was addressed. |
| SDA line | Solid; turns green or blue when pulled low by the master or a slave |
| SCL line | Dashed; bright when high, dim when low |
| Moving tag | The byte travelling right now, such as `0xA5`, or START, STOP, ACK, NACK. It moves right when the master sends and left when a slave sends. |
| SDA and SCL timeline | The recent signal history, like a logic analyzer |
| LOG | Each step of the conversation in words |

### What a read looks like

Reading takes two steps in one conversation:

1. The master **writes** the register number it wants to read.
2. A **repeated START** turns the line around without letting go of the bus.
3. The master sends the address again with the read bit, and the slave sends the byte.
4. The master answers **NACK**, meaning "that's enough, thanks", then STOP.

## Simplifications

BusTalk shows the protocol, not the electronics:

- Real I2C runs at about 100,000 to 400,000 clock pulses per second, not 2 to 40.
- Real wires use pull-up resistors: chips only pull lines low, and the resistor brings them back high.
- Clock stretching, 10-bit addresses, multiple masters, and arbitration are not simulated.
- Each read returns one byte. Real sensors often send several bytes in a row.
- Chip memory resets every time the program starts.

## Check that it works

1. Run `--test` and confirm 11/11 checks pass.
2. Watch the demo and confirm the log shows START, ACK, register, data, and STOP.
3. Press **2** and confirm the slave sends `0x68`, with the tag moving left in blue.
4. Press **1**, then **4**, and confirm the read-back is `0xA5`.
5. Press **5** and confirm the orange NACK line.
6. Press **−** to slow down and watch SDA change only while SCL is low.

## Settings you can change

Edit these near the top of `main.py`, save, and rerun:

| Setting | Effect |
| --- | --- |
| `SPEEDS` | Clock speeds for the **+** and **−** keys |
| `SLAVES` | Add a chip with a name, address, and registers |
| `ACTIONS` | Change what keys 1 to 5 do, using `write_transaction` and `read_transaction` |
| `WIDTH`, `HEIGHT` | Window size |
| `MASTER_COLOR`, `SLAVE_COLOR` | Colors as red, green, blue values |

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `--test` prints nothing | You ran an empty file in another folder. Run `pwd` and `ls -a`; you should be in `19-bustalk`. |
| `no such file or directory: .venv/bin/python` | The environment is missing from this folder. Run the setup command. |
| `ModuleNotFoundError: No module named 'pygame'` | Install requirements, then launch with `.venv/bin/python`. |
| Keys do nothing | Click the BusTalk window first so it has keyboard focus. |
| Too fast to follow | Press **−** or **Space** to pause. |
| Window does not appear | Look behind other windows or in the Dock. |

## What I practiced

Built with AI assistance: the I2C protocol, addresses and the read/write bit, ACK and NACK, START, STOP, and repeated START, registers inside chips, turning bytes into bits with bit shifting, decoding bits back into bytes, drawing a logic-analyzer timeline, animating data along a wire, queuing actions, and a self-test that checks protocol rules without a window.
