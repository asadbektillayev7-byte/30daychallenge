"""HexHound — Day 25: load a firmware file, find hidden patterns in the raw bytes, patch it.

HexHound looks for magic numbers, repeated byte patterns, hidden text, empty padding,
and an ending CRC32 checksum. It draws an entropy map, shows a colored hex dump,
asks a local AI to explain what it found, and can patch bytes or text safely.

Run:  .venv/bin/python main.py --demo                      (make and scan demo_firmware.bin)
      .venv/bin/python main.py firmware.bin                (scan any file)
      .venv/bin/python main.py firmware.bin --hex 0x40     (hex dump from an offset)
      .venv/bin/python main.py firmware.bin --replace "v1.0.3=v1.0.4"
      .venv/bin/python main.py firmware.bin --patch 0x44=DEADBEEF
      .venv/bin/python main.py --test
"""

import argparse
import json
import math
import os
import re
import struct
import sys
import urllib.error
import urllib.request
import zlib
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- settings you can change ----------------
MODEL = "qwen2.5:3b"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
PATTERN_LEN = 4            # bytes per repeated pattern
MIN_REPEATS = 3            # a pattern must appear this often
MIN_STRING = 6             # shortest text worth showing
PAD_MIN = 32               # shortest run of FF or 00 counted as padding
BLOCK = 256                # bytes per entropy block
MAX_ROWS = 16              # hex dump rows

MAGIC = {                  # bytes -> what they usually mean
    b"\x7fELF": "ELF program (Linux / embedded executable)",
    b"\x1f\x8b\x08": "gzip compressed data",
    b"PK\x03\x04": "ZIP archive",
    b"\x89PNG": "PNG image",
    b"\xff\xd8\xff": "JPEG image",
    b"\x27\x05\x19\x56": "U-Boot uImage header (routers, Linux boards)",
    b"hsqs": "SquashFS filesystem (router firmware)",
    b"\xd0\x0d\xfe\xed": "Device tree blob (Linux hardware description)",
    b"\xcf\xfa\xed\xfe": "Mach-O 64-bit program (macOS)",
    b"\xca\xfe\xba\xbe": "Mach-O universal binary / Java class",
    b"\xde\xad\xbe\xef": "DEADBEEF: classic debug / placeholder value",
    b"MZ": "Windows executable (MZ header)",
    b"\x7a\x3c\xe1\x01": "HexHound demo boot header",
}


# ---------------- analysis (tested) ----------------
def entropy(data):
    """0 = all the same byte, 8 = perfectly random (compressed or encrypted)."""
    if not data:
        return 0.0
    n = len(data)
    return -sum(c / n * math.log2(c / n) for c in Counter(data).values())


def entropy_kind(e, data):
    if e < 0.5:
        return "pad" if data and data[0] in (0x00, 0xFF) else "flat"
    if e < 5.0:
        return "text/data"
    if e < 6.9:
        return "code"
    return "packed"


def find_repeats(data, n=PATTERN_LEN, min_count=MIN_REPEATS, top=8):
    """n-byte sequences that appear at least min_count times (ignoring boring ones like 00 00 00 00)."""
    seen = {}
    for i in range(len(data) - n + 1):
        chunk = data[i:i + n]
        if len(set(chunk)) <= 1:
            continue
        seen.setdefault(chunk, []).append(i)
    found = []
    for chunk, offs in seen.items():
        clean = [o for o in offs]
        # drop overlapping hits (like in A B A B A B)
        keep = []
        for o in clean:
            if not keep or o >= keep[-1] + n:
                keep.append(o)
        if len(keep) >= min_count:
            found.append((chunk, keep))
    found.sort(key=lambda x: (-len(x[1]), x[1][0]))
    # hide patterns that are just a slice of a bigger repeated block found earlier
    result = []
    for chunk, offs in found:
        if any(set(offs) <= {o + d for o in big for d in range(-n + 1, n)} and c != chunk for c, big in result):
            continue
        result.append((chunk, offs))
        if len(result) >= top:
            break
    return result


def find_magic(data):
    hits = []
    for sig, meaning in MAGIC.items():
        start = 0
        while True:
            i = data.find(sig, start)
            if i < 0:
                break
            if len(sig) >= 3 or i == 0:          # 2-byte signatures only count at the start
                hits.append((i, sig, meaning))
            start = i + 1
    return sorted(hits)


WORDY = re.compile(r"[a-z]{3}|[A-Z]{4}|\d\.\d")


def find_strings(data, min_len=MIN_STRING):
    """Printable runs that look like real words (random code bytes often look like 'pGFpF')."""
    runs = ((m.start(), m.group().decode("ascii")) for m in re.finditer(rb"[\x20-\x7e]{%d,}" % min_len, data))
    return [(o, s) for o, s in runs if WORDY.search(s)]


def find_padding(data, min_len=PAD_MIN):
    return [(m.start(), m.end() - m.start(), m.group()[0]) for m in re.finditer(rb"\xff{%d,}|\x00{%d,}" % (min_len, min_len), data)]


def arm_vectors(data):
    """ARM Cortex-M chips start with: stack pointer (in RAM, 0x2000_0000+), then reset address (odd = Thumb)."""
    if len(data) < 8:
        return None
    sp, reset = struct.unpack_from("<II", data, 0)
    if 0x20000000 <= sp <= 0x20100000 and reset & 1 and (reset < 0x00100000 or 0x08000000 <= reset < 0x08200000):
        return sp, reset
    return None


def crc_status(data):
    """Many firmwares end with a CRC32 of everything before it. Returns (stored, computed, ok) or None."""
    if len(data) < 8:
        return None
    stored = struct.unpack_from("<I", data, len(data) - 4)[0]
    computed = zlib.crc32(data[:-4]) & 0xFFFFFFFF
    return stored, computed, stored == computed


def analyze(data):
    blocks = [data[i:i + BLOCK] for i in range(0, len(data), BLOCK)]
    ents = [entropy(b) for b in blocks]
    return {
        "size": len(data),
        "entropy": entropy(data),
        "blocks": [(e, entropy_kind(e, b)) for e, b in zip(ents, blocks)],
        "magic": find_magic(data),
        "repeats": find_repeats(data),
        "strings": find_strings(data),
        "padding": find_padding(data),
        "arm": arm_vectors(data),
        "crc": crc_status(data),
    }


# ---------------- patching (tested) ----------------
def parse_patch(text):
    """'0x44=DEADBEEF' -> (0x44, b'\\xde\\xad\\xbe\\xef')"""
    off, _, hexpart = text.partition("=")
    value = bytes.fromhex(hexpart.replace(" ", ""))
    if not value:
        raise ValueError("no bytes given")
    return int(off, 0), value


def apply_patches(data, patches, text_swaps, fix_crc):
    out = bytearray(data)
    log = []
    for old, new in text_swaps:
        if len(old) != len(new):
            raise ValueError(f"'{old}' and '{new}' must be the same length, or every byte after them moves")
        hits = [m.start() for m in re.finditer(re.escape(old.encode()), bytes(out))]
        if not hits:
            raise ValueError(f"text '{old}' not found")
        for h in hits:
            out[h:h + len(old)] = new.encode()
        log.append(f"replaced '{old}' -> '{new}' at {', '.join(hex(h) for h in hits)}")
    for off, value in patches:
        if off < 0 or off + len(value) > len(out):
            raise ValueError(f"offset {hex(off)} is outside the file")
        before = bytes(out[off:off + len(value)]).hex(" ").upper()
        out[off:off + len(value)] = value
        log.append(f"{hex(off)}: {before} -> {value.hex(' ').upper()}")
    if fix_crc:
        new_crc = zlib.crc32(bytes(out[:-4])) & 0xFFFFFFFF
        out[-4:] = struct.pack("<I", new_crc)
        log.append(f"CRC32 at the end updated to {new_crc:08X}")
    return bytes(out), log


# ---------------- demo firmware ----------------
def demo_firmware():
    """A fake 4 KB microcontroller firmware: vector table, header magic, code, text, padding, CRC."""
    rng = __import__("random").Random(25)
    fw = bytearray(b"\xff" * 4096)
    fw[0:8] = struct.pack("<II", 0x20005000, 0x08000101)                       # stack + reset
    for i in range(8, 0x40, 4):
        fw[i:i + 4] = struct.pack("<I", 0x08000141 + i * 2)                   # more vectors
    fw[0x40:0x44] = b"\x7a\x3c\xe1\x01"                                         # boot header magic
    fw[0x44:0x60] = b"HXHD" + b"v1.0.3\x00\x00" + struct.pack("<II", 0x08000400, 3072) + bytes(8)
    opcodes = [rng.randrange(256) for _ in range(70)]                           # a "vocabulary" of instructions
    code = bytes(rng.choice(opcodes) for _ in range(0x600))
    fw[0x100:0x700] = code
    for off in (0x79 + 0x200, 0x95 + 0x400):                                    # magic hidden in code too
        fw[off:off + 4] = b"\x7a\x3c\xe1\x01"
    texts = [b"Copyright (c) 2026 Orca Devices", b"WIFI_SSID=OrcaLab-2G", b"WIFI_PASS=changeme123",
             b"http://update.orca-devices.example/fw", b"ERROR: sensor not found", b"boot ok, version v1.0.3"]
    pos = 0x800
    for t in texts:
        fw[pos:pos + len(t)] = t
        pos += len(t) + 1 + rng.randint(2, 9)
    fw[0xA00:0xC00] = bytes(rng.getrandbits(8) for _ in range(0x200))          # "encrypted" key area
    fw[-4:] = struct.pack("<I", zlib.crc32(bytes(fw[:-4])) & 0xFFFFFFFF)
    return bytes(fw)


# ---------------- output ----------------
KIND_STYLE = {"pad": ("·", "grey35"), "flat": ("_", "grey50"), "text/data": ("▃", "cyan"),
              "code": ("▅", "green"), "packed": ("█", "magenta")}


def hexdump(console, data, start, rows, highlights):
    from rich.text import Text
    start -= start % 16
    for r in range(rows):
        off = start + r * 16
        if off >= len(data):
            break
        line = Text(f"0x{off:06X}  ", style="grey50")
        chunk = data[off:off + 16]
        for i, b in enumerate(chunk):
            style = highlights.get(off + i)
            if style is None:
                style = "grey35" if b in (0x00, 0xFF) else "white"
            line.append(f"{b:02X}", style=style)
            line.append(" " if i != 7 else "  ")
        line.append("   " * (16 - len(chunk)))
        line.append(" " + "".join(chr(b) if 32 <= b < 127 else "." for b in chunk), style="grey62")
        console.print(line)


def report(console, name, data, info):
    from rich.panel import Panel
    from rich.text import Text

    size = info["size"]
    head = (f"{size:,} bytes ({size / 1024:.1f} KB)    overall entropy {info['entropy']:.2f} / 8\n"
            f"first bytes: {data[:16].hex(' ').upper()}")
    console.print(Panel(head, title=f"HexHound · {name}", border_style="green", title_align="left"))

    # entropy map
    bar = Text()
    for e, kind in info["blocks"]:
        ch, style = KIND_STYLE[kind]
        bar.append(ch, style=style)
    legend = Text("  · padding  ", style="grey50")
    for kind in ("text/data", "code", "packed"):
        ch, style = KIND_STYLE[kind]
        legend.append(f"{ch} {kind}  ", style=style)
    console.print(Text(f"Entropy map ({BLOCK} bytes per block)", style="bold"))
    console.print(bar)
    console.print(legend)
    console.print()

    if info["arm"]:
        sp, reset = info["arm"]
        console.print(f"[bold]ARM Cortex-M vector table[/bold]  stack pointer [cyan]0x{sp:08X}[/cyan]  "
                      f"reset handler [cyan]0x{reset:08X}[/cyan] (odd = Thumb code)")
    crc = info["crc"]
    if crc and crc[2]:
        console.print(f"[bold]CRC32 at the end[/bold]  [green]valid[/green] ({crc[0]:08X}). "
                      "Patching will update it.")
    console.print()

    if info["magic"]:
        console.print("[bold]Magic numbers[/bold]")
        for off, sig, meaning in info["magic"][:10]:
            console.print(f"  0x{off:06X}  [yellow]{sig.hex(' ').upper():<12}[/yellow] {meaning}")
        console.print()

    if info["repeats"]:
        console.print("[bold]Repeated patterns[/bold]")
        for chunk, offs in info["repeats"][:6]:
            where = ", ".join(f"0x{o:04X}" for o in offs[:5]) + (" ..." if len(offs) > 5 else "")
            console.print(f"  [magenta]{chunk.hex(' ').upper()}[/magenta]  x{len(offs)}  at {where}")
        console.print()

    if info["padding"]:
        total = sum(n for _, n, _ in info["padding"])
        console.print(f"[bold]Padding[/bold]  {len(info['padding'])} empty runs, {total:,} bytes "
                      f"({total * 100 / max(1, size):.0f}% of the file) — free space, usually erased flash (FF)")
        console.print()

    if info["strings"]:
        console.print(f"[bold]Hidden text[/bold]  {len(info['strings'])} strings")
        flag = re.compile(r"pass|pwd|key|secret|token|ssid|http|ftp|telnet|root|admin", re.I)
        for off, s in info["strings"][:14]:
            style = "red" if flag.search(s) else "white"
            console.print(f"  0x{off:06X}  [{style}]{s[:70]}[/{style}]")
        if any(flag.search(s) for _, s in info["strings"]):
            console.print("  [red]red = may be a password, key, or network address[/red]")
        console.print()


def highlight_map(info):
    hl = {}
    for chunk, offs in info["repeats"][:3]:
        for o in offs:
            for k in range(len(chunk)):
                hl[o + k] = "black on magenta"
    for off, sig, _ in info["magic"]:
        for k in range(len(sig)):
            hl[off + k] = "black on yellow"
    return hl


def ai_explain(console, name, info, model):
    summary = {
        "file": name, "size": info["size"], "entropy": round(info["entropy"], 2),
        "blocks": Counter(k for _, k in info["blocks"]),
        "arm_vector_table": [hex(x) for x in info["arm"]] if info["arm"] else None,
        "crc32_at_end_valid": bool(info["crc"] and info["crc"][2]),
        "magic": [(hex(o), m) for o, _, m in info["magic"][:8]],
        "repeats": [(c.hex(" "), len(o), [hex(x) for x in o[:4]]) for c, o in info["repeats"][:5]],
        "strings": [s[:60] for _, s in info["strings"][:15]],
        "padding_bytes": sum(n for _, n, _ in info["padding"]),
    }
    prompt = ("You are a friendly firmware reverse-engineering tutor. Here is an automatic scan of a binary file:\n"
              + json.dumps(summary, default=str) +
              "\nIn 5 short bullet points, explain to a beginner what this file probably is, what the repeated "
              "patterns and magic numbers likely mean, anything that looks like a security risk, and one idea "
              "for what to look at next. Only use facts from the scan; say 'probably' when guessing.")
    body = {"model": model, "stream": True, "options": {"temperature": 0.2},
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(OLLAMA_URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    console.print(f"[bold]AI notes[/bold] [dim]({model})[/dim]")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            for line in r:
                part = json.loads(line)
                console.print(part.get("message", {}).get("content", ""), end="", highlight=False)
                if part.get("done"):
                    break
        console.print("\n")
    except urllib.error.HTTPError as e:
        console.print(f"[yellow]Ollama error: {e.read().decode(errors='ignore')[:200]}[/yellow]\n")
    except urllib.error.URLError:
        console.print("[yellow]Ollama is not running, so no AI notes. Start it with: open -a Ollama[/yellow]\n")


# ---------------- self test ----------------
def self_test():
    checks = []

    def check(name, ok):
        checks.append(bool(ok))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    print("HexHound self-test")
    check("entropy: all zeros = 0, every byte once = 8", entropy(bytes(256)) == 0 and abs(entropy(bytes(range(256))) - 8) < 1e-9)
    data = b"\x00" * 10 + b"\x7a\x3c\xe1\x01" + b"abc" * 7 + b"\x7a\x3c\xe1\x01" + b"\x11\x22" + b"\x7a\x3c\xe1\x01"
    reps = find_repeats(data)
    check("finds 7A 3C E1 01 three times at the right offsets",
          any(c == b"\x7a\x3c\xe1\x01" and o == [10, 35, 41] for c, o in reps))
    check("ignores boring runs like 00 00 00 00", all(len(set(c)) > 1 for c, _ in reps))
    check("magic: finds ELF at the start and DEADBEEF inside",
          [m for _, _, m in find_magic(b"\x7fELF" + bytes(8) + b"\xde\xad\xbe\xef")][:2] ==
          [MAGIC[b"\x7fELF"], MAGIC[b"\xde\xad\xbe\xef"]])
    check("2-byte 'MZ' only counts at the start", find_magic(b"xxMZxx") == [])
    check("finds hidden text, skips short and random-looking runs",
          find_strings(b"\x01\x02admin1\x00ab\x00pGFpFK\x00pass=1234\xff") == [(2, "admin1"), (19, "pass=1234")])
    check("finds a 40-byte FF padding run", find_padding(b"\x01" + b"\xff" * 40 + b"\x02") == [(1, 40, 0xFF)])

    fw = demo_firmware()
    info = analyze(fw)
    check("demo: ARM vector table found (stack 0x20005000, reset 0x08000101)", info["arm"] == (0x20005000, 0x08000101))
    check("demo: CRC32 at the end is valid", info["crc"][2])
    check("demo: entropy map has padding, code, and packed blocks",
          {"pad", "code", "packed"} <= {k for _, k in info["blocks"]})
    check("demo: boot header magic appears 3 times",
          sum(1 for _, s, _ in info["magic"] if s == b"\x7a\x3c\xe1\x01") == 3)

    check("patch text '0x44=DEADBEEF' is read correctly", parse_patch("0x44=DE AD BE EF") == (0x44, b"\xde\xad\xbe\xef"))
    patched, log = apply_patches(fw, [(0x50, b"\x01\x02")], [("v1.0.3", "v1.0.4")], fix_crc=True)
    check("patch: bytes changed, version text changed in both places, CRC still valid",
          patched[0x50:0x52] == b"\x01\x02" and patched.count(b"v1.0.4") == 2 and crc_status(patched)[2])
    broken, _ = apply_patches(fw, [(0x50, b"\x01")], [], fix_crc=False)
    check("patch without fixing CRC -> CRC no longer valid", not crc_status(broken)[2])
    try:
        apply_patches(fw, [], [("v1.0.3", "v1.0.30")], fix_crc=True)
        ok = False
    except ValueError:
        ok = True
    check("text of a different length is refused (it would shift every byte)", ok)

    passed = sum(checks)
    print(f"\n{passed}/{len(checks)} checks passed")
    return passed == len(checks)


def main():
    p = argparse.ArgumentParser(description="HexHound — find hidden patterns in firmware and patch it")
    p.add_argument("file", nargs="?", help="firmware or any binary file")
    p.add_argument("--demo", action="store_true", help="write demo_firmware.bin and scan it")
    p.add_argument("--hex", help="hex dump from this offset, e.g. 0x40")
    p.add_argument("--rows", type=int, default=MAX_ROWS, help="hex dump rows")
    p.add_argument("--patch", action="append", default=[], help="OFFSET=HEXBYTES, e.g. 0x44=DEADBEEF (repeatable)")
    p.add_argument("--replace", action="append", default=[], help="OLD=NEW or OLD->NEW text of the same length (repeatable)")
    p.add_argument("--no-crc", action="store_true", help="do not update the CRC32 when patching")
    p.add_argument("--no-ai", action="store_true", help="skip the AI notes")
    p.add_argument("--model", default=MODEL)
    p.add_argument("--test", action="store_true", help="run the checks and exit")
    a = p.parse_args()
    if a.test:
        sys.exit(0 if self_test() else 1)

    from rich.console import Console
    console = Console()
    if a.demo:
        path = os.path.join(HERE, "demo_firmware.bin")
        with open(path, "wb") as f:
            f.write(demo_firmware())
        console.print(f"[dim]wrote {path}[/dim]")
    elif a.file:
        path = a.file
    else:
        p.print_help()
        sys.exit("\nGive a file, or use --demo.")
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        sys.exit(f"Could not open {path}: {e}")
    if not data:
        sys.exit("The file is empty.")
    if len(data) > 64 * 1024 * 1024:
        sys.exit("File is bigger than 64 MB; HexHound is made for firmware-sized files.")

    name = os.path.basename(path)
    if a.patch or a.replace:
        crc = crc_status(data)
        fix = bool(crc and crc[2]) and not a.no_crc
        try:
            patched, log = apply_patches(data, [parse_patch(x) for x in a.patch],
                                         [tuple(x.split("->", 1) if "->" in x else x.split("=", 1))
                                          for x in a.replace], fix)
        except ValueError as e:
            sys.exit(f"Patch refused: {e}")
        root, ext = os.path.splitext(path)
        out = f"{root}_patched{ext or '.bin'}"
        with open(out, "wb") as f:
            f.write(patched)
        for line in log:
            console.print(f"  [green]✔[/green] {line}")
        if not fix:
            console.print("  [dim]no valid CRC32 at the end, so none was updated[/dim]")
        console.print(f"Saved [bold]{out}[/bold]  (the original is unchanged)")
        return

    info = analyze(data)
    if a.hex:
        start = int(a.hex, 0)
        console.print(f"[bold]Hex dump from 0x{start:X}[/bold]  [yellow]yellow = magic[/yellow]  "
                      "[magenta]magenta = repeated pattern[/magenta]")
        hexdump(console, data, start, a.rows, highlight_map(info))
        return
    report(console, name, data, info)
    first = (info["magic"][0][0] if info["magic"] else info["repeats"][0][1][0] if info["repeats"] else 0)
    console.print(f"[bold]Hex dump around 0x{first:X}[/bold]  [yellow]yellow = magic[/yellow]  "
                  "[magenta]magenta = repeated pattern[/magenta]")
    hexdump(console, data, max(0, first - 32), 8, highlight_map(info))
    console.print()
    if not a.no_ai:
        ai_explain(console, name, info, a.model)


if __name__ == "__main__":
    main()
