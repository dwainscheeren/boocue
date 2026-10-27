"""Validated, hardware-independent effect format. Times are seconds."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import re
from typing import Any

from .presentation import presentation_for

SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")
MAX_EFFECTS = 200
MAX_CUES = 10000


def number(value: Any, minimum: float, maximum: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return result


def safe_file(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("Invalid audio path")
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Audio must stay inside its effect pack")
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()) or not result.is_file():
        raise ValueError(f"Audio file does not exist: {name}")
    if result.suffix.lower() not in {".mp3", ".wav", ".ogg", ".flac", ".m4a"}:
        raise ValueError("Unsupported audio type")
    return result


@dataclass(frozen=True, slots=True)
class Cue:
    at: float
    hue: float
    saturation: float
    brightness: float
    transition: float = 0.0


@dataclass(frozen=True, slots=True)
class Effect:
    id: str
    title: str
    description: str
    category: str
    duration: float
    audio: Path
    cues: tuple[Cue, ...]
    icon: str = "mdi:ghost"
    source: str = "BooCue"

    def public(self, *, compact=False) -> dict:
        result = {
            "id": self.id, "title": self.title, "description": self.description,
            "category": self.category, "duration": self.duration,
            **presentation_for(self.id, self.title, self.description, self.icon), "source": self.source,
        }
        count = min(18, len(self.cues))
        cues = [self.cues[i * len(self.cues) // count] for i in range(count)] if compact else self.cues
        result['cue_blocks' if compact else 'cues'] = [
            {'at': c.at, 'hue': c.hue, 'saturation': c.saturation,
             'brightness': c.brightness, 'transition': c.transition} for c in cues]
        return result


def parse_effect(raw: dict, root: Path) -> Effect:
    if not isinstance(raw, dict) or not SAFE_ID.fullmatch(str(raw.get("id", ""))):
        raise ValueError("An effect needs a safe unique id")
    title = raw.get("title")
    if not isinstance(title, str) or not 1 <= len(title) <= 120:
        raise ValueError("An effect needs a title of at most 120 characters")
    duration = number(raw.get("duration"), 0.1, 1800, "duration")
    frames = raw.get("cues")
    if not isinstance(frames, list) or not 1 <= len(frames) <= MAX_CUES:
        raise ValueError("An effect needs 1–10000 light cues")
    cues = []
    for frame in frames:
        if not isinstance(frame, dict):
            raise ValueError("Invalid cue")
        cues.append(Cue(
            number(frame.get("at"), 0, duration, "at"),
            number(frame.get("hue", 0), 0, 360, "hue"),
            number(frame.get("saturation", 0), 0, 1, "saturation"),
            number(frame.get("brightness", 0), 0, 1, "brightness"),
            number(frame.get("transition", 0), 0, 30, "transition"),
        ))
    if any(a.at > b.at for a, b in zip(cues, cues[1:])):
        raise ValueError("Cues must be in time order")
    category = raw.get("category", "effects")
    if category not in {"effects", "moods"}:
        raise ValueError("category must be effects or moods")
    description = str(raw.get("description", ""))[:300]
    icon = str(raw.get("icon", "mdi:ghost"))
    if not re.fullmatch(r"mdi:[a-z0-9-]{1,60}", icon):
        icon = "mdi:ghost"
    return Effect(raw["id"], title, description, category, duration,
                  safe_file(root, raw.get("audio")), tuple(cues), icon,
                  str(raw.get("source", "Eigen effect"))[:100])
