import argparse
import sys
from pathlib import Path

import pygame


# ===== Settings =====
WIDTH, HEIGHT = 1000, 600
FPS = 60
SPEEDS = [2, 5, 10, 20, 40]                # clock pulses per second; press + or - to change
SCREENSHOT = Path(__file__).resolve().parent / "bustalk.png"

BACKGROUND = (18, 20, 24)
WHITE = (225, 229, 233)
DIM = (110, 116, 126)
GRID = (40, 44, 52)
MASTER_COLOR = (120, 200, 160)             # green: the master is talking
SLAVE_COLOR = (120, 170, 240)              # blue: a slave is talking
ERROR_COLOR = (240, 120, 80)


# ===== STEP 1: The slave chips and their registers =====
class Slave:
    def __init__(self, name, address, registers):
        self.name = name
        self.address = address                 # 7-bit address, like a house number on the bus
        self.registers = dict(registers)       # tiny memory slots inside the chip


SLAVES = [
    Slave("IMU", 0x68, {0x75: 0x68, 0x6B: 0x40, 0x3B: 0x12}),   # 0x75 = WHO_AM_I
    Slave("TEMP", 0x48, {0x00: 0x19}),                          # 0x19 = 25 °C
    Slave("OLED", 0x3C, {0x00: 0x00}),
]


def find_slave(address):
    return next((slave for slave in SLAVES if slave.address == address), None)


# ===== STEP 2: Turn a conversation into wire signals =====
# Each symbol is a list of (SCL, SDA) levels, one per quarter of a clock pulse.
# "who" says which chip is pulling SDA: M for master, S for slave.
def start():
    return {"kind": "START", "who": "M", "levels": [(1, 1), (1, 0), (0, 0), (0, 0)]}


def repeated_start():
    return {"kind": "START", "who": "M", "levels": [(0, 1), (1, 1), (1, 0), (0, 0)]}


def stop():
    return {"kind": "STOP", "who": "M", "levels": [(0, 0), (1, 0), (1, 1), (1, 1)]}


def bit(value, who):
    """SDA is set while SCL is low, and must stay still while SCL is high."""
    return {"kind": "BIT", "who": who, "value": value,
            "levels": [(0, value), (1, value), (1, value), (0, value)]}


def byte_symbols(value, who, label):
    symbols = [bit((value >> shift) & 1, who) for shift in range(7, -1, -1)]   # most significant bit first
    symbols[-1]["label"] = label
    return symbols


def answer(acknowledged, who):
    """ACK = receiver pulls SDA low (0). NACK = nobody pulls it, so it stays high (1)."""
    symbol = bit(0 if acknowledged else 1, who)
    symbol["kind"] = "ACK" if acknowledged else "NACK"
    return symbol


def address_byte(address, read):
    return (address << 1) | (1 if read else 0)     # 7 address bits + 1 read/write bit


def write_transaction(address, register, value):
    """Master writes `value` into a register of the chip at `address`."""
    slave = find_slave(address)
    symbols = [start()]
    symbols += byte_symbols(address_byte(address, False), "M", f"START · 0x{address:02X} · WRITE")
    if slave is None:
        symbols += [answer(False, "S"), stop()]
        symbols[-2]["label"] = f"NACK · nobody at 0x{address:02X}"
        return symbols, None
    symbols += [answer(True, "S")]
    symbols += byte_symbols(register, "M", f"register 0x{register:02X}") + [answer(True, "S")]
    symbols += byte_symbols(value, "M", f"0x{value:02X}") + [answer(True, "S")]
    slave.registers[register] = value
    symbols.append(stop())
    symbols[-1]["label"] = "STOP"
    return symbols, value


def read_transaction(address, register):
    """Master points at a register, then reads one byte back."""
    slave = find_slave(address)
    symbols = [start()]
    symbols += byte_symbols(address_byte(address, False), "M", f"START · 0x{address:02X} · WRITE")
    if slave is None:
        symbols += [answer(False, "S"), stop()]
        symbols[-2]["label"] = f"NACK · nobody at 0x{address:02X}"
        return symbols, None
    symbols += [answer(True, "S")]
    symbols += byte_symbols(register, "M", f"register 0x{register:02X}") + [answer(True, "S")]
    symbols += [repeated_start()]
    symbols += byte_symbols(address_byte(address, True), "M", f"RESTART · 0x{address:02X} · READ")
    symbols += [answer(True, "S")]
    value = slave.registers.get(register, 0xFF)
    symbols += byte_symbols(value, "S", f"slave sends 0x{value:02X}")
    symbols += [answer(False, "M")]            # master NACKs: "that's enough, thanks"
    symbols[-1]["label"] = "master NACK · done reading"
    symbols.append(stop())
    symbols[-1]["label"] = "STOP"
    return symbols, value


def decode(symbols):
    """Read the bits back off the wire, like a logic analyzer would."""
    data, current = [], []
    for symbol in symbols:
        if symbol["kind"] == "BIT":
            current.append(symbol["value"])
            if len(current) == 8:
                data.append(int("".join(map(str, current)), 2))
                current = []
        elif symbol["kind"] in ("ACK", "NACK"):
            data.append(symbol["kind"])
    return data


# ===== STEP 3: The demo conversations (keys 1 to 5) =====
ACTIONS = {
    pygame.K_1: ("Write 0xA5 to IMU register 0x6B", lambda: write_transaction(0x68, 0x6B, 0xA5)),
    pygame.K_2: ("Read IMU WHO_AM_I (register 0x75)", lambda: read_transaction(0x68, 0x75)),
    pygame.K_3: ("Read temperature from 0x48", lambda: read_transaction(0x48, 0x00)),
    pygame.K_4: ("Read IMU register 0x6B back", lambda: read_transaction(0x68, 0x6B)),
    pygame.K_5: ("Call 0x50, where no chip lives", lambda: write_transaction(0x50, 0x00, 0x01)),
}


# ===== STEP 4: Drawing =====
def draw_chip(screen, fonts, rect, title, subtitle, active):
    small, medium = fonts[0], fonts[1]
    pygame.draw.rect(screen, (24, 27, 32), rect, border_radius=8)
    pygame.draw.rect(screen, WHITE if active else GRID, rect, 2, border_radius=8)
    for i in range(6):
        y = rect.top + 14 + i * (rect.height - 28) // 5
        pygame.draw.line(screen, DIM, (rect.left - 8, y), (rect.left, y), 3)
        pygame.draw.line(screen, DIM, (rect.right, y), (rect.right + 8, y), 3)
    text = medium.render(title, True, WHITE)
    screen.blit(text, text.get_rect(center=(rect.centerx, rect.centery - 10)))
    sub = small.render(subtitle, True, DIM)
    screen.blit(sub, sub.get_rect(center=(rect.centerx, rect.centery + 16)))


def draw_bus(screen, fonts, symbol, quarter, progress, tag):
    small = fonts[0]
    left, right = 230, 760
    sda_y, scl_y = 150, 190
    scl, sda = symbol["levels"][quarter] if symbol else (1, 1)
    talker = SLAVE_COLOR if symbol and symbol["who"] == "S" else MASTER_COLOR

    pygame.draw.line(screen, talker if not sda else WHITE, (left, sda_y), (right, sda_y), 3 if not sda else 2)
    for x in range(left, right, 12):
        pygame.draw.line(screen, WHITE if scl else DIM, (x, scl_y), (x + 6, scl_y), 2)
    screen.blit(small.render(f"SDA {'HIGH' if sda else 'LOW'}", True, DIM), (left + 4, sda_y - 22))
    screen.blit(small.render(f"SCL {'HIGH' if scl else 'LOW'}", True, DIM), (left + 4, scl_y + 8))

    if tag and symbol:
        going_right = symbol["who"] == "M"
        share = progress if going_right else 1 - progress
        x = int(left + 40 + share * (right - left - 120))
        box = pygame.Rect(x, sda_y - 12, 70, 24)
        pygame.draw.rect(screen, talker, box, border_radius=4)
        text = small.render(tag, True, BACKGROUND)
        screen.blit(text, text.get_rect(center=box.center))


def draw_timing(screen, fonts, symbols, position):
    """Logic-analyzer view of the last pulses on SDA and SCL."""
    small = fonts[0]
    left, right, top = 60, WIDTH - 40, 270
    rows = {"SDA": top, "SCL": top + 60}
    for name, y in rows.items():
        screen.blit(small.render(name, True, DIM), (16, y + 6))
        pygame.draw.line(screen, GRID, (left, y + 30), (right, y + 30))

    quarter_width = 7
    visible = (right - left) // quarter_width
    done = [(level, symbol["who"]) for symbol in symbols[:position[0]] for level in symbol["levels"]]
    if position[0] < len(symbols):
        current = symbols[position[0]]
        done += [(level, current["who"]) for level in current["levels"][:position[1] + 1]]
    done = done[-visible:]

    for index, row in enumerate(("SCL", "SDA")):
        y = rows[row]
        previous = None
        for i, ((scl, sda), who) in enumerate(done):
            level = scl if row == "SCL" else sda
            color = WHITE if row == "SCL" else (SLAVE_COLOR if who == "S" else MASTER_COLOR)
            x = left + i * quarter_width
            level_y = y + (4 if level else 26)
            if previous is not None and previous != level_y:
                pygame.draw.line(screen, color, (x, previous), (x, level_y), 2)
            pygame.draw.line(screen, color, (x, level_y), (x + quarter_width, level_y), 2)
            previous = level_y


def draw_log(screen, fonts, log):
    small = fonts[0]
    screen.blit(small.render("LOG", True, DIM), (60, 410))
    for i, (line, color) in enumerate(log[-7:]):
        screen.blit(small.render(f">  {line}", True, color), (60, 436 + i * 22))


def draw_help(screen, fonts, speed, paused):
    small = fonts[0]
    lines = ["1 write 0xA5    2 read WHO_AM_I    3 read temp    4 read back    5 missing chip",
             f"SPACE {'resume' if paused else 'pause'}    +/- speed ({speed} pulses/s)    S save    Q quit"]
    for i, line in enumerate(lines):
        screen.blit(small.render(line, True, DIM), (60, 24 + i * 22))


# ===== STEP 5: Main loop =====
def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("BusTalk — Day 19")
    fonts = (pygame.font.SysFont("menlo", 14), pygame.font.SysFont("menlo", 18, bold=True))
    clock = pygame.time.Clock()

    symbols, position = [], [0, 0]
    log = [("Press 1 to start a conversation on the bus.", DIM)]
    speed_index, paused, timer = 1, False, 0.0
    queue = [pygame.K_1, pygame.K_2, pygame.K_4]          # play a short demo first

    while True:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit()
                    return
                if event.key in ACTIONS:
                    queue.append(event.key)
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    speed_index = min(speed_index + 1, len(SPEEDS) - 1)
                if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed_index = max(speed_index - 1, 0)
                if event.key == pygame.K_s:
                    pygame.image.save(screen, str(SCREENSHOT))
                    print(f"Saved {SCREENSHOT}")

        if position[0] >= len(symbols) and queue:
            title, make = ACTIONS[queue.pop(0)]
            symbols, _ = make()
            position = [0, 0]
            log.append((f"--- {title}", WHITE))

        if not paused and position[0] < len(symbols):
            timer += dt * SPEEDS[speed_index] * 4
            while timer >= 1 and position[0] < len(symbols):
                timer -= 1
                symbol = symbols[position[0]]
                position[1] += 1
                if position[1] >= 4:
                    if "label" in symbol:
                        color = ERROR_COLOR if symbol["kind"] == "NACK" and "nobody" in symbol["label"] \
                            else (SLAVE_COLOR if symbol["who"] == "S" else MASTER_COLOR)
                        log.append((symbol["label"], color))
                    if symbol["kind"] in ("ACK", "NACK") and "label" not in symbol:
                        log.append((f"{symbol['kind']} from {'slave' if symbol['who'] == 'S' else 'master'}",
                                    ERROR_COLOR if symbol["kind"] == "NACK" else SLAVE_COLOR))
                    position = [position[0] + 1, 0]

        current = symbols[position[0]] if position[0] < len(symbols) else None
        tag, progress = current_tag(symbols, position)

        screen.fill(BACKGROUND)
        draw_help(screen, fonts, SPEEDS[speed_index], paused)
        addressed = addressed_slave(symbols)
        draw_chip(screen, fonts, pygame.Rect(60, 110, 160, 110), "MASTER", "MCU", current is not None and current["who"] == "M")
        name, sub = (addressed.name, f"0x{addressed.address:02X}") if addressed else ("SLAVE", "?")
        draw_chip(screen, fonts, pygame.Rect(770, 110, 160, 110), name, sub, current is not None and current["who"] == "S")
        draw_bus(screen, fonts, current, position[1] if current else 0, progress, tag)
        draw_timing(screen, fonts, symbols, position)
        draw_log(screen, fonts, log)
        pygame.display.flip()


def addressed_slave(symbols):
    """The chip named in the first byte of the conversation."""
    bits = [s["value"] for s in symbols if s["kind"] == "BIT"][:7]
    if len(bits) < 7:
        return None
    address = int("".join(map(str, bits)), 2)
    return find_slave(address) or Slave("NOBODY", address, {})


def current_tag(symbols, position):
    """The byte travelling along the wire right now, and how far along it is (0 to 1)."""
    if position[0] >= len(symbols):
        return "", 0.0
    symbol = symbols[position[0]]
    if symbol["kind"] in ("START", "STOP"):
        return symbol["kind"], 0.5
    if symbol["kind"] in ("ACK", "NACK"):
        return symbol["kind"], 0.5
    start = position[0]
    while start > 0 and symbols[start - 1]["kind"] == "BIT":
        start -= 1
    end = start
    while end < len(symbols) and symbols[end]["kind"] == "BIT":
        end += 1
    bits = [s["value"] for s in symbols[start:end]]
    value = int("".join(map(str, bits)), 2) if bits else 0
    done = (position[0] - start + position[1] / 4) / max(end - start, 1)
    return f"0x{value:02X}", done


# ===== Self-test: check the protocol without opening a window =====
def self_test():
    write, _ = write_transaction(0x68, 0x6B, 0xA5)
    read, value = read_transaction(0x68, 0x75)
    missing, nothing = write_transaction(0x50, 0x00, 0x01)
    first_bits = [s["value"] for s in write if s["kind"] == "BIT"][:8]

    checks = [
        ("Address 0x68 + WRITE becomes bits 1101000 0", first_bits == [1, 1, 0, 1, 0, 0, 0, 0]),
        ("Address byte for 0x68 READ is 0xD1", address_byte(0x68, True) == 0xD1),
        ("Write sends address, register, data", decode(write) == [0xD0, "ACK", 0x6B, "ACK", 0xA5, "ACK"]),
        ("Write really changes the register", find_slave(0x68).registers[0x6B] == 0xA5),
        ("Read WHO_AM_I returns 0x68", value == 0x68),
        ("Read ends with master NACK", decode(read)[-1] == "NACK"),
        ("Missing chip answers NACK", decode(missing) == [0xA0, "NACK"] and nothing is None),
        ("Conversations start with START and end with STOP",
         all(s[0]["kind"] == "START" and s[-1]["kind"] == "STOP" for s in (write, read, missing))),
        ("START: SDA falls while SCL is high", start()["levels"][:2] == [(1, 1), (1, 0)]),
        ("STOP: SDA rises while SCL is high", stop()["levels"][1:3] == [(1, 0), (1, 1)]),
        ("Data bits never change while SCL is high",
         all(s["levels"][1][1] == s["levels"][2][1] for s in read if s["kind"] in ("BIT", "ACK", "NACK"))),
    ]
    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
    failures = sum(not passed for _, passed in checks)
    print(f"\n{len(checks) - failures}/{len(checks)} checks passed")
    return failures == 0


def main():
    parser = argparse.ArgumentParser(description="Watch chips talk over an I2C bus.")
    parser.add_argument("--test", action="store_true", help="check the protocol without opening a window")
    options = parser.parse_args()
    if options.test:
        sys.exit(0 if self_test() else 1)
    run()


if __name__ == "__main__":
    main()