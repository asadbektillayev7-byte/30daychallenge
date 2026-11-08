import json
import urllib.error
import urllib.request


MODEL = "qwen2.5:0.5b"
URL = "http://127.0.0.1:11434/api/chat"

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are PocketAgent, a helpful local assistant. "
        "Give short, clear answers in plain language. "
        "When you are unsure, say so."
    ),
}

# Keep recent exchanges to limit memory use.
MAX_EXCHANGES = 4
history = []


def ask_model(question):
    messages = [
        SYSTEM_MESSAGE,
        *history,
        {"role": "user", "content": question},
    ]

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": True,
        "options": {
            "num_ctx": 2048,
            "num_predict": 256,
            "temperature": 0.7,
        },
    }

    request = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    answer_parts = []
    completed = False

    print("\nPocketAgent: ", end="", flush=True)

    # Ollama sends the response in small pieces.
    with urllib.request.urlopen(request, timeout=180) as response:
        for line in response:
            if not line.strip():
                continue

            event = json.loads(line)

            if event.get("error"):
                raise RuntimeError(event["error"])

            text = event.get("message", {}).get("content", "")

            if text:
                print(text, end="", flush=True)
                answer_parts.append(text)

            if event.get("done"):
                completed = True
                break

    print("\n")

    if not completed:
        raise RuntimeError("The connection ended before the reply finished.")

    answer = "".join(answer_parts)

    if not answer.strip():
        raise RuntimeError("The model returned an empty reply.")

    history.extend([
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ])

    # Two messages make one exchange: your question and its answer.
    del history[:-MAX_EXCHANGES * 2]


def show_help():
    print(
        "\nCommands:\n"
        "  /clear  Forget this conversation\n"
        "  /help   Show commands\n"
        "  /quit   Close PocketAgent\n"
    )


def main():
    print("=" * 48)
    print("PocketAgent — Day 8")
    print(f"Local model: {MODEL}")
    print("Keep Ollama running. Type a question to begin.")
    print("Replies may take a while on an Intel Mac.")
    show_help()

    while True:
        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not question:
            continue

        if question.lower() in ("/quit", "/bye", "/exit"):
            print("Goodbye!")
            break

        if question.lower() == "/clear":
            history.clear()
            print("\nConversation cleared.\n")
            continue

        if question.lower() == "/help":
            show_help()
            continue

        if question.startswith("/"):
            print("Unknown command. Type /help.\n")
            continue

        try:
            ask_model(question)

        except urllib.error.HTTPError as error:
            if error.code == 404:
                print(
                    "\nModel or endpoint not found.\n"
                    "Check that Ollama is running and run:\n"
                    f"ollama pull {MODEL}\n"
                )
            else:
                print(f"\nOllama returned HTTP error {error.code}.\n")

        except urllib.error.URLError as error:
            print(
                "\nCould not reach Ollama.\n"
                "Open the Ollama app and try again.\n"
                f"Details: {error.reason}\n"
            )

        except (TimeoutError, OSError) as error:
            print(
                "\nThe local connection failed or timed out.\n"
                "Check Ollama and try a shorter question.\n"
                f"Details: {error}\n"
            )

        except (RuntimeError, ValueError) as error:
            print(f"\nReply failed: {error}\n")

        except KeyboardInterrupt:
            print("\nReply interrupted. Closing PocketAgent.")
            break


if __name__ == "__main__":
    main()