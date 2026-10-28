"""Shared BooCue values."""

DOMAIN = "boocue"
VERSION = "1.1.4"
EVENT_STATE = "boocue_state"
CHANNELS = ("effect", "mood")
RUNTIME_KEYS = {"lights", "output", "speakers", "volume", "brightness", "speed",
                "offset_ms", "routing", "repeat", "restore", "interval_ms", "audio_mode", "duck_mood"}
DEFAULT_SETTINGS = {
    "enabled": True,
    "lights": [], "output": "browser", "speakers": [], "volume": 0.6,
    "brightness": 0.8, "speed": 1.0, "offset_ms": 0, "routing": "all",
    "repeat": False, "restore": True, "interval_ms": 250, "audio_mode": "auto", "duck_mood": 0.35, "favorites": [],
    "mood": {"effect_id": None, "lights": [], "output": "speakers", "speakers": [],
             "volume": 0.3, "brightness": 0.5, "speed": 1.0, "offset_ms": 0,
             "routing": "all", "repeat": True, "restore": True, "interval_ms": 500, "audio_mode": "auto", "duck_mood": 0.35},
    "effect_routes": {}, "automatic_enabled": False, "motion_rules": [], "queues": [],
    "scare_spots": [], "spot_concurrency": "single",
    "spot_show": {"spot_ids": [], "mode": "random", "repeat": True, "gap_min": 4, "gap_max": 15},
}
