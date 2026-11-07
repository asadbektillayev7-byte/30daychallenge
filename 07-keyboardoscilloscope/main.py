import numpy as np
import pygame


SAMPLE_RATE = 44100
WIDTH, HEIGHT = 1000, 650

# These frequencies complete whole cycles in a one-second loop.
NOTES = {
    pygame.K_q: ("Q", "C4", 262),
    pygame.K_w: ("W", "E4", 330),
    pygame.K_e: ("E", "G4", 392),
    pygame.K_r: ("R", "C5", 524),
}

pygame.mixer.pre_init(
    frequency=SAMPLE_RATE,
    size=-16,
    channels=2,
    buffer=512,
)
pygame.init()

if pygame.mixer.get_init() is None:
    pygame.quit()
    raise SystemExit("Audio unavailable. Check your Mac's sound output.")

pygame.mixer.set_num_channels(8)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("KeyboardOscilloscope — Day 7")
clock = pygame.time.Clock()

font = pygame.font.Font(None, 32)
small_font = pygame.font.Font(None, 25)
title_font = pygame.font.Font(None, 46)

BACKGROUND = (16, 20, 25)
GRID = (37, 45, 53)
WHITE = (230, 236, 240)
MUTED = (150, 163, 176)
GREEN = (90, 225, 160)

sounds = {}
channels = {}
active = set()

# Create a one-second sine-wave sound for each key.
sample_times = np.arange(SAMPLE_RATE) / SAMPLE_RATE

for key, (_, _, frequency) in NOTES.items():
    wave = np.sin(2 * np.pi * frequency * sample_times)

    # Keep enough headroom for all four notes together.
    mono = (wave * 0.12 * 32767).astype(np.int16)
    stereo = np.column_stack((mono, mono)).copy()
    sounds[key] = pygame.sndarray.make_sound(stereo)


def stop_all():
    for channel in channels.values():
        channel.stop()
    channels.clear()
    active.clear()


running = True

try:
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.WINDOWFOCUSLOST:
                stop_all()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key in NOTES and event.key not in active:
                    channel = sounds[event.key].play(loops=-1)

                    if channel is not None:
                        channels[event.key] = channel
                        active.add(event.key)

            elif event.type == pygame.KEYUP:
                if event.key in active:
                    channels.pop(event.key).stop()
                    active.remove(event.key)

        screen.fill(BACKGROUND)

        screen.blit(
            title_font.render("KeyboardOscilloscope", True, WHITE),
            (35, 25),
        )
        screen.blit(
            small_font.render(
                "Hold Q, W, E or R. Combine keys to play chords.",
                True,
                MUTED,
            ),
            (35, 78),
        )

        # Draw the four keyboard cards.
        for index, (key, (label, note, frequency)) in enumerate(NOTES.items()):
            box = pygame.Rect(35 + index * 240, 125, 220, 85)
            selected = key in active

            pygame.draw.rect(
                screen,
                (26, 65, 51) if selected else (25, 31, 39),
                box,
                border_radius=10,
            )
            pygame.draw.rect(
                screen,
                GREEN if selected else GRID,
                box,
                width=2,
                border_radius=10,
            )

            screen.blit(
                font.render(f"{label} — {note}", True, WHITE),
                (box.x + 15, box.y + 12),
            )
            screen.blit(
                small_font.render(f"{frequency} Hz", True, MUTED),
                (box.x + 15, box.y + 48),
            )

        # Show a 20-millisecond window of the generated signal.
        plot = pygame.Rect(35, 250, 930, 285)

        for x in range(plot.left, plot.right + 1, 93):
            pygame.draw.line(
                screen, GRID, (x, plot.top), (x, plot.bottom)
            )

        for y in range(plot.top, plot.bottom + 1, 57):
            pygame.draw.line(
                screen, GRID, (plot.left, y), (plot.right, y)
            )

        pygame.draw.line(
            screen,
            MUTED,
            (plot.left, plot.centery),
            (plot.right, plot.centery),
            1,
        )

        times = np.linspace(0, 0.020, plot.width)
        combined = np.zeros(plot.width)

        for key in active:
            frequency = NOTES[key][2]
            combined += np.sin(2 * np.pi * frequency * times)

        # A fixed scale lets chords appear larger than single notes.
        vertical_scale = plot.height * 0.11
        points = [
            (plot.left + index, int(plot.centery - value * vertical_scale))
            for index, value in enumerate(combined)
        ]
        pygame.draw.lines(screen, GREEN, False, points, 2)

        labels = [NOTES[key][1] for key in NOTES if key in active]
        message = " + ".join(labels) if labels else "Hold a key to begin"

        screen.blit(
            font.render(message, True, GREEN),
            (35, 560),
        )
        screen.blit(
            small_font.render(
                "20 ms waveform preview | Release keys to stop | Esc to quit",
                True,
                MUTED,
            ),
            (35, 605),
        )

        pygame.display.flip()
        clock.tick(60)

finally:
    stop_all()
    pygame.quit()