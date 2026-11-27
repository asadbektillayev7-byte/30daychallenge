# HexHound — Day 25

Load a firmware file and sniff out what is hidden in its raw bytes: magic numbers, repeated patterns, text such as passwords and URLs, empty padding, an ARM vector table, and the CRC32 checksum. HexHound draws an entropy map, shows a colored hex dump, asks a local AI to explain the findings, and can **patch** bytes or text while keeping the checksum valid.

New to Python? Start with the [general beginner guide](../BEGINNER_GUIDE.md). It explains installing tools, environments, Terminal commands, commits, and pushing work to GitHub.

Inspired by the BuildCored **FirmwarePatcher** project card by Adham. HexHound is our own version with pattern and magic-number search, entropy mapping, string hunting with risk flags, ARM and CRC detection, safe same-length patching with automatic CRC repair, a demo firmware generator, AI notes, and a self-test.

## Example

```
╭─ HexHound · demo_firmware.bin ─────────────────────────────╮
│ 4,096 bytes (4.0 KB)    overall entropy 4.38 / 8           │
│ first bytes: 00 50 00 20 01 01 00 08 51 01 00 08 59 01 ... │
╰────────────────────────────────────────────────────────────╯
Entropy map (256 bytes per block)
▃▅▅▅▅▅▅·▃·██····
  · padding  ▃ text/data  ▅ code  █ packed

ARM Cortex-M vector table  stack pointer 0x20005000  reset handler 0x08000101
CRC32 at the end  valid. Patching will update it.

Magic numbers
  0x000040  7A 3C E1 01  HexHound demo boot header
  0x000279  7A 3C E1 01  HexHound demo boot header
  0x000495  7A 3C E1 01  HexHound demo boot header

Hidden text  8 strings
  0x000822  WIFI_SSID=OrcaLab-2G
  0x00083D  WIFI_PASS=changeme123          (red: may be a password)
  0x000855  http://update.orca-devices.example/fw
```

## What it is, in simple terms

**Firmware** is the program stored inside a device's chip: a router, a smartwatch, a microwave, an Arduino. It is saved as a `.bin` file, which is nothing but bytes, written in hexadecimal like `7A 3C E1 01`. There are no labels, so you have to find the structure yourself.

| HexHound looks for | Why it matters |
| --- | --- |
| **Magic numbers** | Known byte signatures reveal what is inside: `7F 45 4C 46` is an ELF program, `1F 8B` is gzip, `68 73 71 73` is a SquashFS filesystem in router firmware |
| **Repeated patterns** | The same 4 bytes many times often mark headers, tables, or section starts |
| **Hidden text** | Version numbers, error messages, URLs, and sometimes passwords left in by mistake |
| **Padding** | Long runs of `FF` are erased, unused flash memory; `00` runs are often empty space too |
| **ARM vector table** | Microcontrollers start with the stack address (in RAM, `0x2000…`) and the reset address (in flash, an odd number) |
| **CRC32 at the end** | A checksum of the whole file; if one byte changes without updating it, the device refuses the firmware |

### Entropy, in simple terms

**Entropy** measures how unpredictable the bytes are, from 0 to 8:

| Entropy | Symbol | Usually |
| --- | --- | --- |
| near 0 | `·` | Padding: the same byte again and again |
| below 5 | `▃` | Text, tables, and settings |
| 5 to 6.9 | `▅` | Program code |
| above 6.9 | `█` | Compressed or encrypted data: it looks random |

So one line of symbols shows the layout of the whole file at a glance.

### Patching, in simple terms

You can change bytes at an offset, or swap text for text of the **same length**. Different lengths are refused, because every byte after the change would move and break the program. If the file ends with a valid CRC32, HexHound calculates the new one and writes it, so the patched firmware still passes its check. The original file is never changed; the result is saved as `name_patched.bin`.

## Where it is used in real life

- **Security research:** checking router, camera, and smart-home firmware for hard-coded passwords and secret URLs.
- **Repair and modding:** fixing or unlocking old devices, changing settings that have no menu.
- **Before release:** engineers check that no debug passwords or test servers were left in.
- **Malware analysis and forensics:** finding what an unknown binary contains.
- **Tools that do this professionally:** binwalk, Ghidra, and hex editors.

Only analyze and patch firmware you own or have permission to work on. A bad patch flashed to a real device can stop it from starting.

### How it connects to earlier days

| Day | Project | Link |
| --- | --- | --- |
| 14 | [RegisterBot](../14-registerbot/) | The CPU that runs firmware like this |
| 19 | [BusTalk](../19-bustalk/) | Bytes travelling between chips |
| 21 | [WaveCast](../21-wavecast/) | Packing numbers into bytes with a header and magic label |
| 24 | [PinPoint](../24-pinpoint/) | Reading the datasheet of the chip the firmware runs on |
| 25 | HexHound | Reading the firmware itself |

## Before starting

You need Python 3.12, uv, and `rich`, listed in `requirements.txt`. For the AI notes, you need **Ollama** with **qwen2.5:3b**; without it, everything else still works. The example setup is macOS-first.

## Files

| Item | Purpose |
| --- | --- |
| `main.py` | Analysis, hex dump, patching, demo firmware, AI notes, and self-test |
| `requirements.txt` | Package versions used when this project was built |
| `.gitignore` | Excludes the environment, cache files, and all `.bin` files |
| `demo_firmware.bin` | Fake 4 KB firmware, written by `--demo` |
| `*_patched.bin` | Patched copies |

## First-time setup

Paste this in Terminal as one line. It starts with `cd`, so it works from any folder:

```bash
cd ~/Documents/GitHub/30daychallenge/25-hexhound && uv venv --python 3.12 && uv pip install -r requirements.txt && pwd
```

## Check

```bash
cd ~/Documents/GitHub/30daychallenge/25-hexhound && .venv/bin/python main.py --test
```

The check should end with:

```
15/15 checks passed
```

It checks entropy, repeated patterns, magic numbers, string hunting, padding, the ARM vector table, the CRC, the demo layout, reading patch text, patching with CRC repair, a broken CRC without repair, and refusing text of a different length.

## Run

Open Ollama first if you want AI notes:

```bash
open -a Ollama
```

Make and scan the demo firmware:

```bash
cd ~/Documents/GitHub/30daychallenge/25-hexhound && .venv/bin/python main.py --demo
```

Look at the bytes from an offset:

```bash
cd ~/Documents/GitHub/30daychallenge/25-hexhound && .venv/bin/python main.py demo_firmware.bin --hex 0x800
```

Replace the leaked Wi-Fi password, with the same length of 11 characters. Use **single quotes**: in zsh, `!` inside double quotes causes `event not found`.

```bash
cd ~/Documents/GitHub/30daychallenge/25-hexhound && .venv/bin/python main.py demo_firmware.bin --replace 'changeme123->S3cure!Pass'
```

Check the patched file; the CRC should still say **valid**:

```bash
cd ~/Documents/GitHub/30daychallenge/25-hexhound && .venv/bin/python main.py demo_firmware_patched.bin --no-ai
```

Sniff a real file on your Mac:

```bash
cd ~/Documents/GitHub/30daychallenge/25-hexhound && .venv/bin/python main.py /bin/ls --no-ai
```

It finds `CA FE BA BE`, a universal binary, with two `CF FA ED FE` Mach-O programs inside: one for Intel and one for Apple Silicon. PNG, JPEG, and ZIP files are recognized by their magic bytes even if renamed.

## Options

| Option | What it does |
| --- | --- |
| `--demo` | Write `demo_firmware.bin` and scan it |
| `--hex 0x40` | Hex dump starting at an offset |
| `--rows 32` | Rows in the hex dump |
| `--patch 0x44=DEADBEEF` | Write bytes at an offset; can be repeated |
| `--replace 'old->new'` | Swap text of the same length; `old=new` also works |
| `--no-crc` | Do not update the CRC32 when patching |
| `--no-ai` | Skip the AI notes |
| `--model NAME` | Another Ollama model |
| `--test` | Run the checks |

## Read the report

| Part | Meaning |
| --- | --- |
| Entropy map | One symbol per 256 bytes, from the start of the file to the end |
| Magic numbers | Offset, bytes, and what they usually mean |
| Repeated patterns | Bytes, how many times, and where |
| Padding | Empty space and its share of the file |
| Hidden text, red | Might be a password, key, SSID, or network address |
| Hex dump, yellow | Magic number bytes |
| Hex dump, magenta | Repeated pattern bytes |
| Right column of the dump | The same bytes as letters; `.` means not printable |
| AI notes | A beginner-friendly explanation; the AI only sees the scan summary, not the raw file |

## Settings you can change

Edit these near the top of `main.py`, save, and rerun:

| Setting | Effect |
| --- | --- |
| `MAGIC` | Add your own signatures and meanings |
| `PATTERN_LEN`, `MIN_REPEATS` | Pattern size and how often it must repeat |
| `MIN_STRING` | Shortest text shown |
| `PAD_MIN` | Shortest padding run |
| `BLOCK` | Bytes per entropy block |
| `MODEL` | Ollama model for AI notes |

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `zsh: event not found` | You used `!` inside double quotes. Use single quotes. |
| `Patch refused: ... must be the same length` | Make the new text exactly as long as the old; pad with spaces if needed. |
| `text '...' not found` | Check spelling and capitals; look at the "Hidden text" list. |
| `offset ... is outside the file` | The offset is larger than the file size. |
| `no valid CRC32 at the end` | This file has no ending CRC32, so nothing needed updating. |
| `Ollama is not running` | Run `open -a Ollama`, or use `--no-ai`. |
| Lots of junk text | Normal for code; raise `MIN_STRING`. |

## What I practiced

Built with AI assistance: reading binary files, hexadecimal, little-endian numbers with `struct`, Shannon entropy, searching for repeated byte patterns, magic numbers and file signatures, printable string hunting with regular expressions, the ARM Cortex-M vector table, CRC32 checksums with `zlib`, safe patching that keeps lengths and checksums correct, generating a realistic test firmware, a colored hex dump with rich, AI explanations from a scan summary, and a self-test.
