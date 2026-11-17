# RegisterBot — Day 14

Build a tiny computer inside your computer. RegisterBot is a pretend CPU written in Python. It runs small programs written in its own assembly language, one instruction at a time, and prints a table of every register after each step. An optional local AI narrator makes a sarcastic comment about each instruction.

New to Python? Start with the [general beginner guide](../BEGINNER_GUIDE.md). It explains installing tools, environments, Terminal commands, commits, and pushing work to GitHub.

Inspired by [Botirsherov/RegisterBot](https://github.com/Botirsherov/RegisterBot). This version adds a working Ollama narrator, input checks, a step limit, and a Fibonacci program that also stops correctly when N is 1.

## What it simulates

A real CPU is the chip that runs every program. It only understands tiny steps such as "copy this number", "add these two", or "jump to another line". RegisterBot copies that idea:

| CPU part | In `main.py` | Simple meaning |
| --- | --- | --- |
| Registers R0–R7 | `cpu.registers` | Eight small boxes that each hold one number |
| Program counter (PC) | `cpu.pc` | A finger pointing at the line that runs next |
| Zero flag | `cpu.zero` | A yes/no note: were the last two compared values equal? |
| ALU | `alu()` | The calculator: ADD, SUB, and MUL only |
| Control unit | `execute()` | Reads one instruction and changes the CPU state |

The main loop repeats the **fetch → decode → execute** cycle until the program reaches `HALT`:

1. **Fetch:** read the instruction the program counter points at.
2. **Decode:** work out which command it is.
3. **Execute:** do it, then move the program counter.

This is a teaching simulator, not an emulator of a real chip. Registers hold ordinary Python integers with no 8-bit or 16-bit overflow, there is no RAM or stack, and programs are Python lists inside `main.py`, not separate files.

## Before starting

You need:

- Python 3.12 and uv.
- The `rich` package for the colored tables, listed in `requirements.txt`.
- For the optional narrator: Ollama running with `qwen2.5:0.5b` downloaded.

No webcam, microphone, paid API key, or cloud account is required. Installing `rich` needs internet once. After that, the simulator and the local narrator work offline. The example setup is macOS-first.

## Files

| Item | Purpose |
| --- | --- |
| `main.py` | CPU state, ALU, instruction decoder, programs, optional narrator, and display |
| `requirements.txt` | The `rich` version used when this project was built |
| `.gitignore` | Excludes the environment and Python cache files |
| `.venv/` | Local Python environment |

## First-time setup

### 1. Prepare Python

These commands assume the repository lives at the example path. Substitute your actual location if needed.

```bash
cd ~/Documents/GitHub/30daychallenge/14-registerbot
uv venv --python 3.12
uv pip install -r requirements.txt
```

Skip environment creation if this project's `.venv` exists. Save `main.py` in this folder, outside `.venv`.

### 2. Prepare the optional local model

For narration, open Ollama and leave it running. In Terminal:

```bash
ollama list
```

If `qwen2.5:0.5b` is missing, download it while online:

```bash
ollama pull qwen2.5:0.5b
```

You can reuse the model from earlier days. For Ollama installation help, see the [PocketAgent README](../08-pocketagent/README.md).

## Run RegisterBot

From the Day 14 folder:

```bash
.venv/bin/python main.py factorial
```

The first instruction is `IN R0`, so the program asks:

```
Enter a number from 0 to 20:
```

Type a whole number and press Return. A table then appears after every step, showing R0–R7, the program counter, and the zero flag. The title of each table names the instruction that just ran and what it did. At the end you see:

```
FINAL RESULT (R1): 120 after 30 steps
```

Try the second program:

```bash
.venv/bin/python main.py fibonacci
```

Add the snarky narrator, with Ollama running:

```bash
.venv/bin/python main.py factorial --ai
```

## Options and examples

All options go after `main.py`.

| Option | Meaning |
| --- | --- |
| `factorial` or `fibonacci` | Which program to run; `factorial` is the default |
| `--ai` | Ask the local model for a one-sentence comment after each step |
| `--delay 0` | Seconds to wait between steps; the default is 0.4 |
| `--help` | Show command-line help and exit |

Combine options:

```bash
.venv/bin/python main.py fibonacci --delay 0
.venv/bin/python main.py factorial --ai --delay 1
```

## The two programs

**Factorial** multiplies a number by every whole number below it: 5! = 5 × 4 × 3 × 2 × 1 = 120. By definition, 0! = 1.

**Fibonacci** builds a chain where each number is the sum of the two before it: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55. Input 10 gives the 10th number after the starting 0, which is 55.

Factorial multiplies, so it grows very fast. Fibonacci adds, so it grows more slowly. Both answers end up in **R1**.

### Watch factorial of 3

| Moment | R0 (counter) | R1 (answer) |
| --- | --- | --- |
| Start | 3 | 1 |
| Multiply, count down | 2 | 3 |
| Multiply, count down | 1 | 6 |
| Multiply, count down | 0 | 6 |
| `CMP` finds R0 = 0, `JZ` jumps to `HALT` | 0 | 6 |

The loop is built from two instructions. `CMP` asks whether the counter has reached 0, and `JMP` sends the program counter back up. Every loop in every language is built from this compare-and-jump idea inside the CPU.

### Example results

| Program | Input | R1 result | Steps |
| --- | --- | --- | --- |
| factorial | 0 | 1 | 5 |
| factorial | 5 | 120 | 30 |
| factorial | 10 | 3628800 | 55 |
| fibonacci | 0 | 0 | 6 |
| fibonacci | 1 | 1 | 13 |
| fibonacci | 10 | 55 | 76 |

## Instruction set

| Instruction | Example | Meaning |
| --- | --- | --- |
| `IN` | `IN R0` | Ask for a number from 0 to 20 and store it in R0 |
| `MOV` | `MOV R1 R2` | Copy a number or another register's value into R1 |
| `ADD` | `ADD R2 R1` | R2 = R2 + R1 |
| `SUB` | `SUB R0 1` | R0 = R0 − 1 |
| `MUL` | `MUL R1 R0` | R1 = R1 × R0 |
| `CMP` | `CMP R0 0` | Set the zero flag to True if the two values are equal |
| `JMP` | `JMP 2` | Always jump to line 2 |
| `JZ` | `JZ 7` | Jump to line 7 only if the zero flag is True |
| `HALT` | `HALT` | Stop the CPU |

Line numbers start at 0. Jumps use those line numbers, shown as comments beside each program in `main.py`.

## The AI narrator

With `--ai`, each step sends the instruction and its effect to Ollama at `127.0.0.1:11434`, meaning this computer. The model is told to act as a sarcastic CPU and reply in one short sentence, capped at 40 tokens.

The narrator only comments. It does not run or change the program, and the answer is always calculated by Python. The small 0.5b model's jokes can be odd or wrong about what happened. Each step waits for a reply, so `--ai` makes runs much slower. If Ollama is unreachable, the step prints `(narrator offline: is Ollama running?)` and the simulator keeps going.

## Check that it works

1. Run `--help` and inspect the options.
2. Run `factorial --delay 0` with input 5 and confirm R1 is 120.
3. Run `fibonacci --delay 0` with inputs 0, 1, and 10 and compare them with the results table.
4. Type `abc` or `25` at the prompt and confirm it asks again.
5. Run factorial with input 3 at the normal speed and follow R0, R1, and PC through the loop.
6. Open Ollama and run with `--ai`. Then quit Ollama and confirm the offline message appears instead of a crash.

## Settings and limits

Edit these in `main.py`, save, and rerun:

| Setting | Default | Effect |
| --- | --- | --- |
| `MODEL` | `qwen2.5:0.5b` | Narrator model; `qwen2.5:3b` is usually funnier but slower |
| `MAX_STEPS` | 500 | Safety stop if a program loops forever |
| `--delay` | 0.4 | Speed of the step-by-step display |

Input is limited to 0–20 so runs stay short and results stay readable. If a program you write reaches `MAX_STEPS` before `HALT`, the final result is printed anyway, so check the step count. An unknown instruction, a bad register name, or a jump past the last line stops the program with a Python error.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `ModuleNotFoundError: No module named 'rich'` | Install requirements, then launch with `.venv/bin/python`, not a different Python. |
| `invalid choice` | Use `factorial` or `fibonacci` exactly. |
| Narrator offline | Open Ollama and check `ollama list`. Without `--ai`, Ollama is not needed. |
| Narrator very slow | Expected on an Intel Mac. Run without `--ai` or use a smaller delay. |
| Tables scroll by too fast | Use a larger delay, for example `--delay 1`. |
| Traceback after Control+C | Pressing Control+C stops the program; the error text is normal. |
| Missing source or interpreter | Run `pwd` and `ls -a`; confirm `main.py` is in this folder and create the environment if missing. |

## What I practiced

Built with AI assistance: modeling CPU state with a class, an ALU function, decoding instructions, the fetch-decode-execute loop, loops built from compare-and-jump, input validation, `argparse`, Rich tables, and calling a local Ollama model with Python's standard library.

**Bonus challenge:** add a `DIV` instruction to the ALU, or write a third program that adds the numbers from 1 to N.
