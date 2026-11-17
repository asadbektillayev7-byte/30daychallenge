import argparse
import math
import sys
import time
from pathlib import Path

import pygame


# ===== Settings =====
VCC = 3.3                                  # supply voltage of a typical microcontroller pin
FREQUENCIES = [1, 2, 5, 100, 1000]         # press F to cycle; slow ones blink for real
BLINK_LIMIT = 10                           # at or below this many Hz, the LED blinks visibly
PERIODS_SHOWN = 8                          # square-wave periods drawn on screen
BREATHE_SECONDS = 4                        # one full fade in and out in breathe mode
WIDTH, HEIGHT = 900, 540
FPS = 60
SCREENSHOT = Path(__file__).resolve().parent / "dutyglow.png"

BACKGROUND = (18, 20, 24)
WHITE = (225, 229, 233)
DIM = (110, 116, 126)
GRID = (40, 44, 52)
ACCENT = (120, 200, 160)
LED_OFF = (70, 74, 82)
LED_ON = (255, 214, 120)


# ===== STEP 1: The PWM math =====
def average_voltage(duty):
    """The pin is only ever 0 V or VCC. Averaged over time it equals VCC × duty."""
    return VCC * duty / 100


def timing(duty, frequency):
    """Return the period, HIGH time and LOW time in microseconds."""
    period = 1_000_000 / frequency
    high = period * duty / 100
    return period, high, period - high


def pin_level(seconds, duty, frequency):
    """Is the pin HIGH or LOW at this moment? Returns VCC or 0."""
    position = (seconds * frequency) % 1          # 0.0 to 1.0 inside the current period
    return VCC if position < duty / 100 else 0.0


# ===== STEP 2: What the LED looks like =====
def led_brightness(duty, frequency, seconds):
    """Fast PWM: your eye averages it, so brightness = duty.
    Slow PWM: your eye sees each flash, so the LED is fully on or fully off."""
    if frequency <= BLINK_LIMIT:
        return 1.0 if pin_level(seconds, duty, frequency) > 0 else 0.0
    return duty / 100


def mix(color_a, color_b, amount):
    return tuple(int(a + (b - a) * amount) for a, b in zip(color_a, color_b))


def draw_led(screen, center, brightness):
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for radius, strength in [(120, 25), (95, 45), (75, 70)]:
        alpha = int(strength * brightness)
        pygame.draw.circle(glow, (*LED_ON, alpha), center, radius)
    screen.blit(glow, (0, 0))

    x, y = center
    pygame.draw.line(screen, DIM, (x - 14, y + 50), (x - 14, y + 105), 3)   # legs
    pygame.draw.line(screen, DIM, (x + 14, y + 50), (x + 14, y + 95), 3)
    pygame.draw.circle(screen, (40, 44, 52), center, 60)                    # rim
    pygame.draw.circle(screen, mix(LED_OFF, LED_ON, brightness), center, 52)
    pygame.draw.circle(screen, mix((150, 155, 165), (255, 250, 230), brightness), (x - 18, y - 18), 10)


# ===== STEP 3: Draw the square wave =====
WAVE_LEFT, WAVE_RIGHT = 60, WIDTH - 40
WAVE_TOP, WAVE_BOTTOM = 300, 420


def volts_to_y(volts):
    return WAVE_BOTTOM - (volts / VCC) * (WAVE_BOTTOM - WAVE_TOP)


def wave_points(duty):
    """Corner points of the square wave across PERIODS_SHOWN periods."""
    width = (WAVE_RIGHT - WAVE_LEFT) / PERIODS_SHOWN
    high, low = volts_to_y(VCC), volts_to_y(0)
    points = [(WAVE_LEFT, low)]
    for i in range(PERIODS_SHOWN):
        start = WAVE_LEFT + i * width
        fall = start + width * duty / 100
        points += [(start, low), (start, high), (fall, high), (fall, low)]
    points.append((WAVE_RIGHT, low))
    return points


def draw_dashed_line(screen, color, y, left, right, dash=10):
    for x in range(int(left), int(right), dash * 2):
        pygame.draw.line(screen, color, (x, y), (min(x + dash, right), y), 2)


def draw_wave(screen, fonts, duty, frequency, seconds):
    small = fonts[0]
    for volts in (0, VCC):
        y = volts_to_y(volts)
        pygame.draw.line(screen, GRID, (WAVE_LEFT, y), (WAVE_RIGHT, y))
        screen.blit(small.render(f"{volts:.1f} V", True, DIM), (8, y - 8))

    pygame.draw.lines(screen, WHITE, False, wave_points(duty), 2)

    average_y = volts_to_y(average_voltage(duty))
    draw_dashed_line(screen, ACCENT, average_y, WAVE_LEFT, WAVE_RIGHT)
    label = small.render(f"average {average_voltage(duty):.2f} V", True, ACCENT)
    spot = (WAVE_RIGHT - label.get_width(), average_y - 24)
    pygame.draw.rect(screen, BACKGROUND, (*spot, label.get_width(), label.get_height()))
    screen.blit(label, spot)

    if frequency <= BLINK_LIMIT:
        # A moving dot shows where "now" is inside the current period.
        width = (WAVE_RIGHT - WAVE_LEFT) / PERIODS_SHOWN
        x = WAVE_LEFT + ((seconds * frequency) % 1) * width
        y = volts_to_y(pin_level(seconds, duty, frequency))
        pygame.draw.circle(screen, LED_ON, (int(x), int(y)), 7)

    title = f"SQUARE WAVE · {frequency} Hz" if frequency < 1000 else "SQUARE WAVE · 1 kHz"
    screen.blit(small.render(title, True, DIM), (WAVE_LEFT, WAVE_TOP - 40))


# ===== STEP 4: The slider =====
SLIDER_LEFT, SLIDER_RIGHT, SLIDER_Y = 60, 460, 150


def slider_to_duty(mouse_x):
    share = (mouse_x - SLIDER_LEFT) / (SLIDER_RIGHT - SLIDER_LEFT)
    return round(min(max(share, 0), 1) * 100)


def draw_slider(screen, fonts, duty):
    small, medium = fonts[0], fonts[1]
    pygame.draw.line(screen, GRID, (SLIDER_LEFT, SLIDER_Y), (SLIDER_RIGHT, SLIDER_Y), 8)
    knob_x = SLIDER_LEFT + (SLIDER_RIGHT - SLIDER_LEFT) * duty / 100
    pygame.draw.line(screen, ACCENT, (SLIDER_LEFT, SLIDER_Y), (knob_x, SLIDER_Y), 8)
    pygame.draw.circle(screen, WHITE, (int(knob_x), SLIDER_Y), 12)
    screen.blit(small.render("0%", True, DIM), (SLIDER_LEFT, SLIDER_Y + 18))
    end = small.render("100%", True, DIM)
    screen.blit(end, (SLIDER_RIGHT - end.get_width(), SLIDER_Y + 18))
    screen.blit(medium.render(f"Duty cycle  {duty}%", True, WHITE), (SLIDER_LEFT, SLIDER_Y - 50))


# ===== STEP 5: Numbers at the bottom =====
def draw_stats(screen, fonts, duty, frequency, breathing):
    small = fonts[0]
    period, high, low = timing(duty, frequency)
    unit, scale = ("ms", 1000) if period >= 10_000 else ("µs", 1)
    line1 = (f"Period {period / scale:.0f} {unit}   HIGH {high / scale:.0f} {unit}   "
             f"LOW {low / scale:.0f} {unit}   Average {average_voltage(duty):.2f} V of {VCC} V")
    if frequency <= BLINK_LIMIT:
        line2 = "SLOW MOTION: the LED really blinks. Press F for fast PWM, where your eye blends it into dimming."
    else:
        line2 = "FAST PWM: too quick for your eye, so you see the average as brightness. Press F for slow motion."
    if breathing:
        line2 = "BREATHE MODE: duty cycle sweeps 0–100% by itself. Press B to stop."
    screen.blit(small.render(line1, True, WHITE), (WAVE_LEFT, 462))
    screen.blit(small.render(line2, True, DIM), (WAVE_LEFT, 490))


# ===== STEP 6: Main loop =====
def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DutyGlow — Day 17")
    fonts = (pygame.font.SysFont("menlo", 14), pygame.font.SysFont("menlo", 22, bold=True))
    clock = pygame.time.Clock()

    duty = 50
    frequency_index = FREQUENCIES.index(1000)
    breathing = False
    dragging = False
    started = time.monotonic()

    while True:
        seconds = time.monotonic() - started
        frequency = FREQUENCIES[frequency_index]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and abs(event.pos[1] - SLIDER_Y) < 25 \
                    and SLIDER_LEFT - 20 <= event.pos[0] <= SLIDER_RIGHT + 20:
                dragging, breathing = True, False
                duty = slider_to_duty(event.pos[0])
            if event.type == pygame.MOUSEBUTTONUP:
                dragging = False
            if event.type == pygame.MOUSEMOTION and dragging:
                duty = slider_to_duty(event.pos[0])
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit()
                    return
                steps = {pygame.K_LEFT: -1, pygame.K_RIGHT: 1, pygame.K_DOWN: -10, pygame.K_UP: 10}
                if event.key in steps:
                    duty = min(max(duty + steps[event.key], 0), 100)
                    breathing = False
                if event.key == pygame.K_f:
                    frequency_index = (frequency_index + 1) % len(FREQUENCIES)
                if event.key == pygame.K_b:
                    breathing = not breathing
                if event.key == pygame.K_s:
                    pygame.image.save(screen, str(SCREENSHOT))
                    print(f"Saved {SCREENSHOT}")

        if breathing:
            duty = round(50 - 50 * math.cos(2 * math.pi * seconds / BREATHE_SECONDS))

        screen.fill(BACKGROUND)
        screen.blit(fonts[1].render("D·17  DutyGlow", True, WHITE), (WAVE_LEFT, 24))
        help_text = "drag slider · ←/→ 1%  ↑/↓ 10% · F frequency · B breathe · S save · Q quit"
        screen.blit(fonts[0].render(help_text, True, DIM), (WAVE_LEFT, 56))
        draw_slider(screen, fonts, duty)
        draw_led(screen, (740, 150), led_brightness(duty, frequency, seconds))
        draw_wave(screen, fonts, duty, frequency, seconds)
        draw_stats(screen, fonts, duty, frequency, breathing)
        pygame.display.flip()
        clock.tick(FPS)


# ===== Self-test: check the math without opening a window =====
def self_test():
    checks = [
        ("25% of 3.3 V averages 0.825 V", math.isclose(average_voltage(25), 0.825)),
        ("0% duty averages 0 V", average_voltage(0) == 0),
        ("100% duty averages the full 3.3 V", math.isclose(average_voltage(100), VCC)),
        ("1 kHz at 25%: period 1000 µs, HIGH 250 µs, LOW 750 µs", timing(25, 1000) == (1000, 250, 750)),
        ("Pin is HIGH at the start of a period", pin_level(0, 50, 1000) == VCC),
        ("Pin is LOW at 0% duty", pin_level(0, 0, 1000) == 0),
        ("Fast PWM LED brightness equals duty", led_brightness(30, 1000, 0.123) == 0.3),
        ("Slow PWM LED is fully on or fully off", led_brightness(30, 1, 0.5) in (0.0, 1.0)),
    ]

    # Simulate the pin 100,000 times and average it: this proves average = VCC × duty.
    for duty in (10, 37, 80):
        samples = [pin_level(i / 100_000 / 1000 * 50, duty, 1000) for i in range(100_000)]
        simulated = sum(samples) / len(samples)
        checks.append((f"Simulated pin at {duty}% averages {average_voltage(duty):.2f} V",
                       abs(simulated - average_voltage(duty)) < 0.01))

    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
    failures = sum(not passed for _, passed in checks)
    print(f"\n{len(checks) - failures}/{len(checks)} checks passed")
    return failures == 0


def main():
    parser = argparse.ArgumentParser(description="Slide a duty cycle and watch a virtual LED dim.")
    parser.add_argument("--test", action="store_true", help="check the math without opening a window")
    options = parser.parse_args()

    if options.test:
        sys.exit(0 if self_test() else 1)
    run()


if __name__ == "__main__":
    main()