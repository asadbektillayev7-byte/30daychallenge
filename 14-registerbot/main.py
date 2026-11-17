import argparse
import json
import time
import urllib.request

from rich.console import Console
from rich.table import Table

console = Console()
MODEL = "qwen2.5:0.5b"
API_URL = "http://127.0.0.1:11434/api/chat"
MAX_STEPS = 500


# ===== STEP 1: The CPU's memory =====
class CPU:
    def __init__(self, program):
        self.registers = [0] * 8   # R0..R7, tiny storage boxes
        self.pc = 0                # program counter: which line runs next
        self.zero = False          # flag set by CMP
        self.halted = False
        self.program = program


# ===== STEP 2: The ALU does the math =====
def alu(op, a, b):
    if op == "ADD":
        return a + b
    if op == "SUB":
        return a - b
    if op == "MUL":
        return a * b
    raise ValueError(f"Unknown ALU op: {op}")


def value_of(cpu, arg):
    if arg.startswith("R"):
        return cpu.registers[int(arg[1:])]
    return int(arg)


# ===== STEP 3: Decode and execute one instruction =====
def execute(cpu, instruction):
    op, *args = instruction

    if op == "IN":
        cpu.registers[int(args[0][1:])] = ask_number()
        cpu.pc += 1
        return f"Read your number into {args[0]}"

    if op == "MOV":
        cpu.registers[int(args[0][1:])] = value_of(cpu, args[1])
        cpu.pc += 1
        return f"Copied {args[1]} into {args[0]}"

    if op in ("ADD", "SUB", "MUL"):
        dst = int(args[0][1:])
        cpu.registers[dst] = alu(op, cpu.registers[dst], value_of(cpu, args[1]))
        cpu.pc += 1
        return f"ALU did {op}, result in {args[0]}"

    if op == "CMP":
        cpu.zero = value_of(cpu, args[0]) == value_of(cpu, args[1])
        cpu.pc += 1
        return f"Compared {args[0]} and {args[1]}: equal={cpu.zero}"

    if op == "JMP":
        cpu.pc = int(args[0])
        return f"Jumped to line {args[0]}"

    if op == "JZ":
        cpu.pc = int(args[0]) if cpu.zero else cpu.pc + 1
        return "Jump taken" if cpu.zero else "Jump skipped"

    if op == "HALT":
        cpu.halted = True
        return "Stopped"

    raise ValueError(f"Unknown instruction: {op}")


def ask_number():
    while True:
        text = input("Enter a number from 0 to 20: ").strip()
        if text.isdigit() and int(text) <= 20:
            return int(text)
        print("Please type a whole number from 0 to 20.")


# ===== STEP 4: Programs written in our tiny assembly language =====
FACTORIAL = [
    ["IN", "R0"],          # 0  N
    ["MOV", "R1", "1"],    # 1  result = 1
    ["CMP", "R0", "0"],    # 2  N == 0?
    ["JZ", "7"],           # 3  yes -> finish
    ["MUL", "R1", "R0"],   # 4  result = result * N
    ["SUB", "R0", "1"],    # 5  N = N - 1
    ["JMP", "2"],          # 6  loop
    ["HALT"],              # 7  answer in R1
]

FIBONACCI = [
    ["IN", "R0"],          # 0  N
    ["MOV", "R1", "0"],    # 1  a = 0
    ["MOV", "R2", "1"],    # 2  b = 1
    ["CMP", "R0", "0"],    # 3  N == 0?
    ["JZ", "10"],          # 4  yes -> finish
    ["MOV", "R3", "R2"],   # 5  temp = b
    ["ADD", "R2", "R1"],   # 6  b = a + b
    ["MOV", "R1", "R3"],   # 7  a = temp
    ["SUB", "R0", "1"],    # 8  N = N - 1
    ["JMP", "3"],          # 9  loop
    ["HALT"],              # 10 answer in R1
]

PROGRAMS = {"factorial": FACTORIAL, "fibonacci": FIBONACCI}


# ===== STEP 5: Optional snarky AI narrator =====
def narrate(instruction, effect):
    body = {
        "model": MODEL,
        "stream": False,
        "options": {"num_predict": 40},
        "messages": [
            {"role": "system", "content": "You are a sarcastic CPU. Comment in one short sentence."},
            {"role": "user", "content": f"I just ran {' '.join(instruction)}. {effect}."},
        ],
    }
    request = urllib.request.Request(
        API_URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)["message"]["content"].strip()
    except OSError:
        return "(narrator offline: is Ollama running?)"


# ===== STEP 6: Show the registers =====
def show(cpu, step, instruction, effect):
    table = Table(title=f"Step {step}: {' '.join(instruction)}  ->  {effect}")
    for i in range(8):
        table.add_column(f"R{i}", justify="right")
    table.add_column("PC", justify="right", style="cyan")
    table.add_column("ZERO", style="magenta")
    table.add_row(*[str(r) for r in cpu.registers], str(cpu.pc), str(cpu.zero))
    console.print(table)


# ===== STEP 7: Fetch -> decode -> execute loop =====
def main():
    parser = argparse.ArgumentParser(description="A tiny CPU simulator.")
    parser.add_argument("program", nargs="?", choices=PROGRAMS, default="factorial")
    parser.add_argument("--ai", action="store_true", help="add the snarky Ollama narrator")
    parser.add_argument("--delay", type=float, default=0.4, help="seconds between steps")
    options = parser.parse_args()

    cpu = CPU(PROGRAMS[options.program])
    console.print(f"[bold cyan]RegisterBot is running {options.program}[/bold cyan]")

    step = 0
    while not cpu.halted and step < MAX_STEPS:
        instruction = cpu.program[cpu.pc]      # FETCH
        effect = execute(cpu, instruction)     # DECODE + EXECUTE
        step += 1
        show(cpu, step, instruction, effect)
        if options.ai:
            console.print(f"[yellow]🤖 {narrate(instruction, effect)}[/yellow]")
        time.sleep(options.delay)

    console.print(f"\n[bold green]FINAL RESULT (R1): {cpu.registers[1]}[/bold green] after {step} steps")


if __name__ == "__main__":
    main()
