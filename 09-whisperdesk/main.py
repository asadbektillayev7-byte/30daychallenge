import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


SAMPLE_RATE = 16000
RECORD_SECONDS = 6

print("WhisperDesk — Day 9")
print("Loading the speech model...")
print("The first run needs internet to download the model.\n")

try:
    model = WhisperModel(
        "tiny.en",
        device="cpu",
        compute_type="int8",
    )
except Exception as error:
    raise SystemExit(f"Could not load the model: {error}")

print("Ready! This version transcribes English.")
print("Press Enter to record six seconds.")
print("Type /quit and press Enter to close.\n")

try:
    while True:
        command = input("Enter to record, or /quit: ").strip()

        if command.lower() == "/quit":
            break

        if command:
            print("Press Enter without typing to start recording.\n")
            continue

        print("Recording now — speak normally!")

        try:
            recording = sd.rec(
                int(RECORD_SECONDS * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
            )
            sd.wait()

            audio = recording[:, 0].copy()
            level = float(np.sqrt(np.mean(audio ** 2)))

            if level < 0.0001:
                print(
                    "The microphone was almost silent. "
                    "Check your input device and try again.\n"
                )
                continue

            print("Recording finished. Transcribing...")

            segments, info = model.transcribe(
                audio,
                language="en",
                beam_size=1,
                condition_on_previous_text=False,
            )

            text = " ".join(
                segment.text.strip() for segment in segments
            ).strip()

            if text:
                print(f"\nYou said: {text}\n")
            else:
                print("\nNo text detected. Try speaking closer to the mic.\n")

        except Exception as error:
            print(f"\nRecording or transcription failed: {error}\n")

except (KeyboardInterrupt, EOFError):
    print("\nStopping WhisperDesk.")

finally:
    sd.stop()
    print("Goodbye!")