# PinPoint — Day 24

Ask questions about hardware datasheets and get short answers **with the exact page**. Put PDF datasheets in a folder, ask "What's the max GPIO current?", and PinPoint finds the right passages, lets a local AI answer only from them, and shows where the answer came from: `file · §section · pg N`.

New to Python? Start with the [general beginner guide](../BEGINNER_GUIDE.md). It explains installing tools, environments, Terminal commands, commits, and pushing work to GitHub.

Inspired by [KMechanic/HardwareTA](https://github.com/KMechanic/HardwareTA). PinPoint is our own version with BM25 search written from scratch, section-aware chunking, page citations, a page cache, a search-only mode, a fictional demo datasheet, and a self-test.

## Example

```
ask › What's the max GPIO source current?
searching 8 passages → best 4 → qwen2.5:3b

The max GPIO source current is 25 mA. [1]

 [1] orca-m4-demo · §6.3.16 · pg 14
sourced from 1 datasheet · type :sources to see the passages

ask › What is the bluetooth range?

Not found in the datasheets.
```

The second answer matters: the demo chip has no Bluetooth, so PinPoint says so instead of inventing a number.

## What it is, in simple terms

A **datasheet** is the official manual of a chip. It can be 100 to 2000 pages long, full of tables of voltages, currents, timings, and pins. Engineers search them every day.

A small AI model does not know what is inside your datasheet, and if you just ask it, it may **make up** numbers. PinPoint uses a technique called **RAG**, Retrieval-Augmented Generation:

| Step | What happens |
| --- | --- |
| **1. Read** | Every page of every PDF is turned into text and cached, so big files are read only once |
| **2. Chunk** | Pages are cut into passages of about 900 characters that overlap a little; each remembers its file, page, and latest section heading such as `6.3.16` |
| **3. Search** | Your question is compared with every passage using **BM25**, and the best 4 are picked |
| **4. Answer** | The 4 passages and your question go to the local AI, which must answer only from them and cite `[1]`, `[2]` |
| **5. Cite** | PinPoint shows the file, section, and page for every passage the AI cited |

### BM25, in simple terms

BM25 is the classic search-engine scoring formula. For each word in your question:

- **Rare words count a lot.** "GPIO" appears on a few pages, so a match matters. Common words like "the" are thrown away.
- **Repeats help, but less and less.** A word appearing 5 times is better than once, but not 5 times better.
- **Long passages are not favored** just because they contain more words.

PinPoint also folds plurals and short forms: `pins` → `pin`, `max` → `maximum`, `freq` → `frequency`.

## Where it is used in real life

- **Engineers** search datasheets and reference manuals for limits before they connect anything.
- **Company help bots** answer from manuals and policies with links to the source.
- **Lawyers, doctors, and students** use RAG tools to search long documents with citations.
- **"Chat with your PDF"** apps work exactly like this.

### How it connects to earlier days

| Day | Project | Link |
| --- | --- | --- |
| 13 | [DailyDebrief](../13-dailydebrief/) | Also asks a local Ollama model, about Git commits |
| 17 | [DutyGlow](../17-dutyglow/) | GPIO pins driving an LED; PinPoint tells you how much current they can give |
| 19 | [BusTalk](../19-bustalk/) | I2C; PinPoint can tell you which pull-up resistor to use |
| 22 | [SketchNet](../22-sketchnet/) | Solving circuits; datasheets give the limits those circuits must respect |
| 24 | PinPoint | Looking up the real numbers |

## Before starting

You need Python 3.12, uv, `pypdf`, and `rich`, listed in `requirements.txt`, plus **Ollama** with the model **qwen2.5:3b**. The search-only mode `--no-ai` works without Ollama. The example setup is macOS-first.

## Files

| Item | Purpose |
| --- | --- |
| `main.py` | Reading files, chunking, BM25 search, prompt, Ollama streaming, chat, and self-test |
| `datasheets/` | Put your PDF, `.txt`, or `.md` datasheets here |
| `datasheets/orca-m4-demo.txt` | A **fictional** demo chip, so PinPoint works before you download anything; do not use its numbers for real hardware |
| `requirements.txt` | Package versions used when this project was built |
| `.gitignore` | Excludes the environment, the page cache, and downloaded PDFs |
| `.cache/` | Extracted page text, made automatically |
| `.venv/` | Local Python environment |

## First-time setup

Paste this in Terminal as one line. It starts with `cd`, so it works from any folder:

```bash
cd ~/Documents/GitHub/30daychallenge/24-pinpoint && uv venv --python 3.12 && uv pip install -r requirements.txt && pwd
```

If you see `operation timed out`, the internet dropped for a moment, which often happens on a phone hotspot; run the command again.

Download the model once, if you do not have it:

```bash
ollama pull qwen2.5:3b
```

## Check

```bash
cd ~/Documents/GitHub/30daychallenge/24-pinpoint && .venv/bin/python main.py --test
```

The check should end with:

```
12/12 checks passed
```

It checks the tokenizer, page marks, page and section tracking, overlapping chunks, that BM25 finds the right passage for three questions and nothing for unrelated words, the citation format, the prompt, and reading citations from an answer. It does not need Ollama.

## Run

Start Ollama first, by opening the app or running this:

```bash
open -a Ollama
```

Then chat:

```bash
cd ~/Documents/GitHub/30daychallenge/24-pinpoint && .venv/bin/python main.py
```

| Command | What it does |
| --- | --- |
| `.venv/bin/python main.py` | Chat |
| `.venv/bin/python main.py --ask "How fast can the ADC sample?"` | One question, then exit |
| `.venv/bin/python main.py --no-ai` | Show the best passages only; no AI needed |
| `.venv/bin/python main.py --sources` | Always print the passages under each answer |
| `.venv/bin/python main.py --model qwen2.5:0.5b` | Use another Ollama model |

Inside the chat:

| Type | What happens |
| --- | --- |
| A question | Search, then answer with citations |
| `:sources` | Show the passages behind the last answer |
| `:docs` | List loaded datasheets |
| `quit` | Exit |

Questions to try on the demo chip:

- `What's the max GPIO source current?`
- `What pull-up resistor do I need for I2C at 400 kHz?`
- `How much current does standby mode use?`
- `What happens if I put 5V on a normal pin?`

## Add real datasheets

1. In your browser, search for a chip's datasheet PDF, for example **ATmega328P datasheet**, the chip on an Arduino Uno, from the maker's website.
2. Save the PDF into `24-pinpoint/datasheets/`.
3. Restart PinPoint. The first load of a big PDF takes a few seconds; after that it is cached.

PDFs are not uploaded to GitHub, because `.gitignore` excludes them. Scanned PDFs that are only pictures have no text, so they cannot be searched.

## Settings you can change

Edit these near the top of `main.py`, save, and rerun:

| Setting | Effect |
| --- | --- |
| `MODEL` | Ollama model |
| `TOP_K` | How many passages the AI sees |
| `CHUNK_CHARS`, `OVERLAP` | Passage size and overlap |
| `K1`, `B` | BM25 tuning: repeat bonus and length penalty |
| `SYSTEM` | The rules given to the AI |
| `SYNONYMS`, `STOP` | Word folding and ignored words |
| `DOCS_DIR` | Where datasheets are read from |

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `Ollama is not running` | Run `open -a Ollama`, or `ollama serve` in another window. |
| `Model qwen2.5:3b is not downloaded` | Run `ollama pull qwen2.5:3b`. |
| `operation timed out` while installing | Internet dropped; run the command again. |
| `No datasheets found` | Put a PDF, `.txt`, or `.md` file in `datasheets/`. |
| `Not found in the datasheets` but it is there | Use the datasheet's own words, try `--no-ai` to see what search finds, or raise `TOP_K`. |
| Wrong numbers | Check `:sources`; the answer should match the passage. Smaller models make mistakes. |
| A PDF is skipped or empty | It may be scanned images; it needs OCR first. |
| Answers changed after editing a PDF | Delete `.cache/` to read it again. |

## What I practiced

Built with AI assistance: Retrieval-Augmented Generation, extracting text from PDFs with pypdf, caching with file hashes, splitting text into overlapping chunks while tracking pages and section headings, tokenizing with stop words, plurals, and synonyms, writing BM25 search from scratch, building a prompt with numbered sources, streaming answers from the Ollama API, checking which sources the AI cited, refusing to answer without evidence, a terminal chat with rich, and a self-test that checks search quality without the AI.
