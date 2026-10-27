"""Generate original synthetic sounds and timelines, with no external assets."""

from array import array
import json
import math
from pathlib import Path
import random
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "custom_components/boocue/assets"
RATE = 22050


def pulse(t, center, width):
    return math.exp(-((t - center) / width) ** 2)


def generate(kind, duration, seed):
    rng = random.Random(seed)
    samples = []
    low = 0.0
    for i in range(round(RATE * duration)):
        t = i / RATE
        noise = rng.uniform(-1, 1)
        low = 0.985 * low + 0.015 * noise
        if kind == "thunder":
            env = sum(pulse(t, c, w) for c, w in [(0.5, .06), (.9, .12), (2.8, .3), (3.3, .12)])
            value = noise * env * .32 + low * (1 - t / duration) * 5
        elif kind == "wind":
            value = low * (2 + math.sin(t * 1.4)) + math.sin(t * (420 + 40 * math.sin(t))) * .06
        elif kind == "heartbeat":
            env = sum(pulse(t % 1.15, c, .045) for c in [.13, .34])
            value = (math.sin(2 * math.pi * 62 * t) + low) * env * .8
        elif kind == "bells":
            value = 0
            for at, freq in [(0.1, 523.25), (1.3, 622.25), (2.5, 739.99), (3.7, 493.88), (5.2, 523.25)]:
                age = t - at
                if age >= 0:
                    value += (math.sin(2 * math.pi * freq * age)
                              + .3 * math.sin(2 * math.pi * freq * 2.71 * age)) * math.exp(-age * 1.4) * .4
        elif kind == "door":
            frequency = 120 + 55 * math.sin(t * 1.5) + 8 * math.sin(t * 45)
            value = (math.sin(2 * math.pi * frequency * t) * .2 + low * 3) * math.sin(math.pi * t / duration) ** 2
        elif kind == "steps":
            env = sum(pulse(t, center, .045) for center in [.5, 1.3, 2.1, 2.9, 3.7, 4.5])
            value = (low * 5 + math.sin(2 * math.pi * 85 * t) * .3 + noise * .13) * env
        elif kind == "electric":
            env = .15 + .7 * (math.sin(t * 29) > .8) + .2 * (math.sin(t * 11) > .7)
            value = (noise * .2 + math.sin(2 * math.pi * 110 * t) * .15) * env
        else:
            value = low * 3 + (noise if rng.random() < .002 else 0) * .5
        fade = min(1, t / .03, (duration - t) / .12)
        samples.append(value * max(0, fade))
    peak = max(abs(x) for x in samples) or 1
    pcm = array("h", (round(x / peak * 27000) for x in samples))
    if sys.byteorder != "little":
        pcm.byteswap()
    return pcm.tobytes()


def cue(at, hue, saturation, brightness, transition=.15):
    return dict(at=at, hue=hue, saturation=saturation, brightness=brightness, transition=transition)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "audio").mkdir(exist_ok=True)
    specs = [
        ("thunder-roll", "Thunder roll", "A low rumble with cold flashes.", "weather-lightning", "thunder", 7),
        ("ghost-wind", "Ghost wind", "A whispering wind and slow violet light.", "weather-windy", "wind", 12),
        ("heartbeat", "Heartbeat", "A double heartbeat in deep red.", "heart-pulse", "heartbeat", 8),
        ("haunted-bells", "Haunted bells", "Uneasy chimes with little pools of color.", "bell-ring-outline", "bells", 8),
        ("creaking-door", "Creaking door", "A door opens into a green glow.", "door-open", "door", 5),
        ("footsteps", "Footsteps", "Someone is getting closer.", "shoe-print", "steps", 6),
        ("electric-flicker", "Electric flicker", "An old neon light refuses to settle.", "lightning-bolt-outline", "electric", 7),
        ("campfire", "Campfire", "Warm crackles and a gentle amber shimmer.", "campfire", "fire", 18),
    ]
    catalog_path = OUT / "pack.json"
    pack = (json.loads(catalog_path.read_text()) if catalog_path.exists()
            else dict(version=1, id="boocue-builtins", title="BooCue sounds", effects=[]))
    original_ids = {spec[0] for spec in specs}
    preserved = [e for e in pack["effects"] if e["id"] not in original_ids]
    effects = []
    for index, (effect_id, title, description, icon, kind, duration) in enumerate(specs):
        audio = OUT / "audio" / (effect_id + ".wav")
        with wave.open(str(audio), "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(RATE)
            f.writeframes(generate(kind, duration, index + 100))
        rng = random.Random(index)
        if kind == "thunder":
            cues = [cue(0, 225, .8, .04), cue(.5, 210, .1, 1, 0), cue(.75, 230, .8, .08),
                    cue(1, 215, .1, .8, 0), cue(1.35, 230, .8, .1, .5),
                    cue(2.8, 210, .05, 1, 0), cue(3.15, 230, .8, .03),
                    cue(3.5, 215, .1, .7, 0), cue(4, 235, .7, .06, 1), cue(6, 235, .7, 0, 1)]
        elif kind == "heartbeat":
            cues = [cue(0, 355, 1, .02)]
            for b in range(7):
                for offset, power in [(.13, .9), (.29, .08), (.36, .7), (.53, .02)]:
                    at = b * 1.15 + offset
                    if at < duration:
                        cues.append(cue(round(at, 3), 355, 1, power, .05))
        elif kind == "bells":
            cues = [cue(0, 270, .6, .04)]
            for i, at in enumerate([.1, 1.3, 2.5, 3.7, 5.2]):
                cues.extend([cue(at, [280, 165, 35][i % 3], .7, .75),
                             cue(at + .5, 265, .7, .05, .8)])
        elif kind == "steps":
            cues = [cue(0, 28, .85, .03)]
            for at in [.5, 1.3, 2.1, 2.9, 3.7, 4.5]:
                cues.extend([cue(at, 28, .85, .75, .04), cue(at + .25, 28, .85, .04, .2)])
        elif kind == "electric":
            cues = [cue(round(i * .3, 3), 160, .15, rng.choice([.03, .2, .9]), 0)
                    for i in range(int(duration / .3))]
        elif kind == "door":
            cues = [cue(0, 120, .8, .01), cue(1, 120, .9, .12, 1),
                    cue(2.5, 110, .9, .7, 1.5), cue(4, 110, .9, .05, .8)]
        else:
            cues = [cue(i * .6, 27 + rng.uniform(-8, 8) if kind == "fire" else 265 + rng.uniform(-25, 25),
                        .85 if kind == "fire" else .65, rng.uniform(.12, .7), .5)
                    for i in range(int(duration / .6))]
        effects.append(dict(id=effect_id, title=title, description=description,
                            category="moods" if kind in {"wind", "fire"} else "effects",
                            duration=duration, audio=f"audio/{effect_id}.wav", icon=f"mdi:{icon}",
                            source="BooCue Originals", license="MIT", cues=cues))
    pack["effects"] = effects + preserved
    catalog_path.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n")
    print(f"Generated {len(effects)} original demo effects")


if __name__ == "__main__":
    main()
