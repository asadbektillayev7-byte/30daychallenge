"""PinPoint — Day 24: ask questions about hardware datasheets, get answers with page numbers.

Put PDF (or .txt / .md) datasheets in the datasheets/ folder. PinPoint reads every page,
finds the passages that match your question (BM25 search), and asks a local Ollama
model to answer only from those passages, citing file, section, and page.

Run:  .venv/bin/python main.py                       (chat)
      .venv/bin/python main.py --ask "max GPIO current?"
      .venv/bin/python main.py --no-ai               (search only, no model)
      .venv/bin/python main.py --test                (check the search math)
"""

import argparse
import hashlib
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- settings you can change ----------------
DOCS_DIR = os.path.join(HERE, "datasheets")
CACHE_DIR = os.path.join(HERE, ".cache")
MODEL = "qwen2.5:3b"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
CHUNK_CHARS = 900          # size of one searchable passage
OVERLAP = 150              # passages overlap so sentences aren't cut in half
TOP_K = 4                  # passages given to the AI
K1, B = 1.5, 0.75          # BM25 tuning

SYSTEM = """You are a hardware teaching assistant. Answer the question using ONLY the numbered
datasheet excerpts. Rules:
- Be short: 1 to 4 sentences. Always give numbers with units.
- After each fact, cite the excerpt like [1] or [2].
- If the excerpts do not contain the answer, reply exactly: Not found in the datasheets.
- Never invent numbers."""

STOP = set("""a an the of to in on for and or is are be was were by with as at from that this it its
what which how why when where who whom do does did can could should would will may might than then
there their these those into about over under value values much many i me my
you your we our""".split())
SYNONYMS = {"max": "maximum", "min": "minimum", "freq": "frequency", "temp": "temperature",
            "volt": "voltage", "volts": "voltage", "amps": "current", "pins": "pin", "io": "gpio"}


# ---------------- reading files ----------------
PAGE_MARK = re.compile(r"^=+\s*page\s+(\d+)\s*=+\s*$", re.I | re.M)
HEADING = re.compile(r"^\s*((?:\d+\.){1,3}\d+|\d+)\s+([A-Z][A-Za-z0-9 ,/()\-]{3,70})\s*$", re.M)


def read_text_pages(text):
    """Text with '=== Page N ===' lines -> [(page, text)]. Without marks: one page."""
    marks = list(PAGE_MARK.finditer(text))
    if not marks:
        return [(1, text)]
    pages = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        pages.append((int(m.group(1)), text[m.end():end]))
    return pages


def read_pdf_pages(path):
    from pypdf import PdfReader
    reader = PdfReader(path)
    return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]


def file_key(path):
    st = os.stat(path)
    return hashlib.md5(f"{path}|{st.st_size}|{st.st_mtime}".encode()).hexdigest()


def load_pages(path, log=print):
    """Read a file's pages, using a cache so big PDFs are only read once."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache = os.path.join(CACHE_DIR, file_key(path) + ".json")
    if os.path.exists(cache):
        with open(cache) as f:
            return [tuple(p) for p in json.load(f)]
    if path.lower().endswith(".pdf"):
        log(f"  reading {os.path.basename(path)} (first time only)...")
        pages = read_pdf_pages(path)
    else:
        with open(path, encoding="utf-8", errors="ignore") as f:
            pages = read_text_pages(f.read())
    with open(cache, "w") as f:
        json.dump(pages, f)
    return pages


# ---------------- chunking (tested) ----------------
def chunk_pages(doc, pages, size=CHUNK_CHARS, overlap=OVERLAP):
    """Split pages into overlapping passages; remember the latest section heading."""
    chunks, section = [], ""
    for page, text in pages:
        text = re.sub(r"[ \t]+", " ", text)
        heads = [(m.start(), m.group(1), m.group(2).strip()) for m in HEADING.finditer(text)]
        start = 0
        while start < max(1, len(text)):
            end = min(len(text), start + size)
            if end < len(text):                       # end at a sentence or line if possible
                cut = max(text.rfind(". ", start, end), text.rfind("\n", start, end))
                if cut > start + size // 2:
                    end = cut + 1
            for pos, num, title in heads:
                if pos < end:
                    section = f"§{num} {title}"
            body = text[start:end].strip()
            if len(body) > 40:
                chunks.append({"doc": doc, "page": page, "section": section, "text": body})
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
    return chunks


# ---------------- BM25 search (tested) ----------------
def tokenize(text):
    words = re.findall(r"[a-z]+|\d+(?:\.\d+)?", text.lower())
    out = []
    for w in words:
        w = SYNONYMS.get(w, w)
        if w in STOP:
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]                                # pins -> pin, limits -> limit
        out.append(w)
    return out


class Index:
    """BM25: rare words that match count a lot; common words count little; long passages are not favored."""

    def __init__(self, chunks):
        self.chunks = chunks
        self.tokens = [tokenize(c["text"] + " " + c["section"]) for c in chunks]
        self.tf = [Counter(t) for t in self.tokens]
        self.avg = sum(len(t) for t in self.tokens) / max(1, len(self.tokens))
        df = Counter()
        for t in self.tokens:
            df.update(set(t))
        n = len(chunks)
        self.idf = {w: math.log(1 + (n - d + 0.5) / (d + 0.5)) for w, d in df.items()}

    def search(self, query, k=TOP_K):
        q = tokenize(query)
        scored = []
        for i, tf in enumerate(self.tf):
            length = len(self.tokens[i])
            s = 0.0
            for w in q:
                f = tf.get(w, 0)
                if f:
                    s += self.idf[w] * f * (K1 + 1) / (f + K1 * (1 - B + B * length / self.avg))
            if s > 0:
                scored.append((s, i))
        scored.sort(reverse=True)
        return [(s, self.chunks[i]) for s, i in scored[:k]]


def cite(chunk):
    name = os.path.splitext(chunk["doc"])[0]
    sec = chunk["section"].split(" ", 1)[0] if chunk["section"] else ""
    return " · ".join(x for x in (name, sec, f"pg {chunk['page']}") if x)


def build_prompt(question, hits):
    parts = [f"[{n}] ({cite(c)}{' — ' + c['section'] if c['section'] else ''})\n{c['text']}"
             for n, (_, c) in enumerate(hits, 1)]
    return "Datasheet excerpts:\n\n" + "\n\n".join(parts) + f"\n\nQuestion: {question}"


def used_citations(answer, count):
    nums = sorted({int(n) for n in re.findall(r"\[(\d+)\]", answer)})
    return [n for n in nums if 1 <= n <= count]


# ---------------- AI ----------------
def ask_model(question, hits, model, on_token):
    body = {"model": model, "stream": True, "options": {"temperature": 0.1},
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": build_prompt(question, hits)}]}
    req = urllib.request.Request(OLLAMA_URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    text = ""
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            for line in r:
                part = json.loads(line)
                token = part.get("message", {}).get("content", "")
                text += token
                on_token(token)
                if part.get("done"):
                    break
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="ignore")
        if "not found" in detail:
            sys.exit(f"Model {model} is not downloaded. Run:  ollama pull {model}")
        sys.exit(f"Ollama error: {detail}")
    except urllib.error.URLError:
        sys.exit("Ollama is not running. Open the Ollama app or run:  ollama serve")
    return text


# ---------------- app ----------------
def build_index(console):
    if not os.path.isdir(DOCS_DIR):
        os.makedirs(DOCS_DIR)
    files = sorted(f for f in os.listdir(DOCS_DIR) if f.lower().endswith((".pdf", ".txt", ".md")))
    if not files:
        sys.exit(f"No datasheets found. Put PDF files in {DOCS_DIR}")
    chunks, summary = [], []
    for name in files:
        try:
            pages = load_pages(os.path.join(DOCS_DIR, name), log=console.print)
        except Exception as e:
            console.print(f"  [red]skipped {name}: {e}[/red]")
            continue
        c = chunk_pages(name, pages)
        chunks += c
        summary.append((name, len(pages), len(c)))
    if not chunks:
        sys.exit("The datasheets had no readable text (scanned PDFs need OCR).")
    return Index(chunks), summary


def answer(console, index, question, model, no_ai, show_sources):
    from rich.panel import Panel
    from rich.text import Text

    hits = index.search(question)
    if not hits:
        console.print("[yellow]No matching passages. Try other words, like the exact term from the datasheet.[/yellow]")
        return
    if no_ai:
        for n, (score, c) in enumerate(hits, 1):
            console.print(Panel(c["text"][:600], title=f"[{n}] {cite(c)}", subtitle=f"score {score:.1f}",
                                border_style="green", title_align="left"))
        return

    console.print(f"[dim]searching {len(index.chunks)} passages → best {len(hits)} → {model}[/dim]")
    console.print()
    reply = ask_model(question, hits, model, lambda t: console.print(t, end="", highlight=False))
    console.print("\n")
    used = used_citations(reply, len(hits)) or ([] if "not found" in reply.lower() else [1])
    line = Text()
    for n in used:
        line.append(f" [{n}] {cite(hits[n - 1][1])} ", style="bold green on grey11")
        line.append("  ")
    if used:
        console.print(line)
    docs = len({c["doc"] for _, c in hits})
    console.print(f"[dim]sourced from {docs} datasheet{'s' if docs != 1 else ''}"
                  f"{' · type :sources to see the passages' if not show_sources else ''}[/dim]\n")
    if show_sources:
        for n, (_, c) in enumerate(hits, 1):
            console.print(Panel(c["text"][:600], title=f"[{n}] {cite(c)}", border_style="dim", title_align="left"))


def main():
    p = argparse.ArgumentParser(description="PinPoint — datasheet question answering with page citations")
    p.add_argument("--ask", help="ask one question and exit")
    p.add_argument("--no-ai", action="store_true", help="only show the best matching passages")
    p.add_argument("--sources", action="store_true", help="always print the passages used")
    p.add_argument("--model", default=MODEL, help=f"Ollama model (default {MODEL})")
    p.add_argument("--test", action="store_true", help="run the checks and exit")
    a = p.parse_args()
    if a.test:
        sys.exit(0 if self_test() else 1)

    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    index, summary = build_index(console)
    rows = "\n".join(f"  {n}  [dim]{pg} pages · {ch} passages[/dim]" for n, pg, ch in summary)
    console.print(Panel(rows, title="PinPoint · datasheets loaded", border_style="green", title_align="left"))

    if a.ask:
        answer(console, index, a.ask, a.model, a.no_ai, a.sources)
        return
    console.print("[dim]Ask about your chips. Commands: :sources (show passages of last answer), "
                  ":docs, quit[/dim]\n")
    last = None
    while True:
        try:
            q = console.input("[bold green]ask ›[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        if q.lower() in ("quit", "exit", "q"):
            break
        if q == ":docs":
            console.print(rows)
            continue
        if q == ":sources":
            if last:
                answer(console, index, last, a.model, True, False)
            continue
        last = q
        answer(console, index, q, a.model, a.no_ai, a.sources)


# ---------------- self test ----------------
def self_test():
    checks = []

    def check(name, ok):
        checks.append(bool(ok))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    print("PinPoint self-test")
    check("tokenizer drops filler, keeps numbers, folds plurals and synonyms",
          tokenize("What is the max current of the GPIO pins at 3.3 V?") == ["maximum", "current", "gpio", "pin", "3.3", "v"])
    pages = read_text_pages("=== Page 3 ===\nhello there\n=== Page 4 ===\nsecond page")
    check("'=== Page N ===' marks split text into pages", [p for p, _ in pages] == [3, 4] and "second" in pages[1][1])

    sample = [
        (12, "6.3 Electrical characteristics\nGeneral info about the supply.\n"
             "6.3.16 I/O port characteristics\nEach GPIO pin can source or sink up to 25 mA. "
             "The total current sourced by all pins of one port must not exceed 120 mA."),
        (13, "More text about the same section continues here without a heading at all."),
        (20, "7.2 Clock tree\nThe internal RC oscillator runs at 16 MHz. The PLL can multiply it up to 168 MHz."),
        (31, "9.1 Analog to digital converter\nThe ADC has 12-bit resolution and samples at up to 2.4 MSPS."),
    ]
    chunks = chunk_pages("demo-mcu.pdf", sample, size=200, overlap=30)
    check("chunks remember page numbers", {c["page"] for c in chunks} == {12, 13, 20, 31})
    check("chunks remember the latest section, even on the next page",
          any(c["page"] == 13 and c["section"].startswith("§6.3.16") for c in chunks))
    long_text = [(1, ("Sentence number one is here. " * 80))]
    lc = chunk_pages("x", long_text, size=300, overlap=50)
    check("long pages are split into overlapping passages",
          len(lc) > 5 and all(len(c["text"]) <= 300 for c in lc) and lc[0]["text"][-20:] in lc[1]["text"] + lc[0]["text"])

    index = Index(chunks)
    top = index.search("max GPIO source current")[0][1]
    check("search: 'max GPIO source current' finds the 25 mA passage", "25 mA" in top["text"])
    check("search: 'PLL clock frequency' finds the clock page", index.search("PLL clock frequency")[0][1]["page"] == 20)
    check("search: 'ADC resolution bits' finds the ADC page", index.search("ADC resolution bits")[0][1]["page"] == 31)
    check("search: unrelated words find nothing", index.search("banana smoothie") == [])
    check("citation looks like: demo-mcu · §6.3.16 · pg 12", cite(top) == "demo-mcu · §6.3.16 · pg 12")
    prompt = build_prompt("max current?", index.search("GPIO current"))
    check("prompt numbers the excerpts [1], [2]... and ends with the question",
          prompt.count("\n[") >= 1 and "[1] (demo-mcu" in prompt and prompt.endswith("Question: max current?"))
    check("finds which excerpts the answer cited", used_citations("25 mA [1]. Port max 120 mA [1][3]. [9]", 4) == [1, 3])

    passed = sum(checks)
    print(f"\n{passed}/{len(checks)} checks passed")
    return passed == len(checks)


if __name__ == "__main__":
    main()
