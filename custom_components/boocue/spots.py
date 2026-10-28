"""Named scare spots pair physical speakers, lights and an effect pool."""

from copy import deepcopy
import asyncio
import random
import time
import uuid

from .const import RUNTIME_KEYS
from .models import SAFE_ID, number
from .sequence import QueueCursor
from .props import validate_props


def validate_spots(raw, effect_ids, runtime_validator, entity_validator, runtime_base):
    if not isinstance(raw, list) or len(raw) > 32:
        raise ValueError("Kies maximaal 32 schrikplekken")
    result, seen = [], set()
    allowed = {"id", "name", "enabled", "effects", "mode", "settings", "sensors", "match", "cooldown", "props"}
    for item in raw:
        if not isinstance(item, dict) or set(item) - allowed:
            raise ValueError("Ongeldige schrikplek")
        spot_id, name = item.get("id"), item.get("name", "")
        if not isinstance(spot_id, str) or not SAFE_ID.fullmatch(spot_id) or spot_id in seen:
            raise ValueError("Geef elke schrikplek een unieke id")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            raise ValueError("Geef de schrikplek een naam")
        effects = item.get("effects")
        if (not isinstance(effects, list) or not 1 <= len(effects) <= 50
                or any(not isinstance(e, str) or e not in effect_ids for e in effects)):
            raise ValueError("Kies 1 tot 50 bestaande effecten voor de schrikplek")
        mode, enabled = item.get("mode", "random"), item.get("enabled", True)
        if mode not in {"random", "sequence"} or not isinstance(enabled, bool):
            raise ValueError("Ongeldige afspeelvolgorde voor de schrikplek")
        overrides = item.get("settings", {})
        if not isinstance(overrides, dict) or set(overrides) - RUNTIME_KEYS:
            raise ValueError("Ongeldige instellingen voor de schrikplek")
        settings = runtime_validator({**runtime_base, **overrides})
        props = validate_props(item.get('props', []))
        if settings["output"] == "browser":
            raise ValueError("Kies HA-speakers of geen geluid voor een schrikplek")
        if settings["output"] == "speakers" and not settings["speakers"]:
            raise ValueError("Kies minstens één speaker voor de schrikplek")
        if settings["output"] == "none" and not settings["lights"] and not props:
            raise ValueError("Kies lampen, speakers of schrikapparaten voor de schrikplek")
        settings.update(speed=1., repeat=False)
        sensors = entity_validator(item.get("sensors", []), "binary_sensor", 16)
        match = item.get("match", "any")
        if match not in {"any", "all"}:
            raise ValueError("Kies OR of AND voor de bewegingssensoren")
        result.append({"id": spot_id, "name": name.strip(), "enabled": enabled,
                       "effects": list(dict.fromkeys(effects)), "mode": mode,
                       "settings": settings, "sensors": sensors, "match": match, "props": props,
                       "cooldown": number(item.get("cooldown", 30), 0, 3600, "cooldown")})
        seen.add(spot_id)
    return result


def validate_spot_show(raw, spot_ids):
    allowed = {"spot_ids", "mode", "repeat", "gap_min", "gap_max"}
    if not isinstance(raw, dict) or set(raw) - allowed:
        raise ValueError("Ongeldige instellingen voor de schrikplekkenlus")
    selected = raw.get("spot_ids", [])
    if (not isinstance(selected, list) or len(selected) > 32
            or any(not isinstance(s, str) or s not in spot_ids for s in selected)):
        raise ValueError("Kies bestaande schrikplekken voor de lus")
    mode, repeat = raw.get("mode", "random"), raw.get("repeat", True)
    if mode not in {"random", "sequence"} or not isinstance(repeat, bool):
        raise ValueError("Kies willekeurig of vaste volgorde voor de schrikplekken")
    low = number(raw.get("gap_min", 4), 0, 3600, "gap_min")
    high = number(raw.get("gap_max", 15), low, 3600, "gap_max")
    return {"spot_ids": list(dict.fromkeys(selected)), "mode": mode,
            "repeat": repeat, "gap_min": low, "gap_max": high}


def idle_show():
    return {"playing": False, "run_id": None, "spot_id": None, "spot_name": None,
            "waiting": None, "next_at": None, "error": None, "step": 0}


class SpotManager:
    def __init__(self, controller):
        self.c = controller
        self.lock = asyncio.Lock()
        self.show_lock = asyncio.Lock()
        self.cursors, self.last_motion, self.events = {}, {}, {}
        self.show_status = idle_show()
        self.task = None
        self.last_spot = None
        self.generation = 0
        self.stop_generations = {}
        self._definitions = []

    def invalidate_pending(self):
        self.generation += 1

    def definition(self, spot_id):
        spot = next((s for s in self.c.settings["scare_spots"] if s["id"] == spot_id and s["enabled"]), None)
        if not spot:
            raise ValueError("Kies een bestaande, ingeschakelde schrikplek")
        return deepcopy(spot)

    def motion_armed(self, spot_id):
        return (not self.c._closed and self.c.settings["enabled"] and self.c.settings["automatic_enabled"]
                and any(s["id"] == spot_id and s["enabled"] and s["sensors"] for s in self.c.settings["scare_spots"]))

    def status(self):
        return {s["id"]: {**deepcopy(self.c.channels.get("spot:" + s["id"], {"playing": False})),
                           "name": s["name"], "event": deepcopy(self.events.get(s["id"], {}))}
                for s in self.c.settings["scare_spots"]}

    async def trigger(self, spot_id=None, context=None, *, source="manual", show_token=None):
        try:
            return await self._trigger(spot_id, context, source=source, show_token=show_token)
        except ValueError as err:
            if source != "motion":
                raise
            self.events[spot_id] = {"state": "error", "at": time.time(), "error": str(err)[:250]}
            self.c._notify()
            return None

    async def _trigger(self, spot_id=None, context=None, *, source="manual", show_token=None):
        self.c.ensure_enabled()
        generation, stopped = self.generation, self.stop_generations.copy()
        choices = [spot_id] if spot_id else [s["id"] for s in self.c.settings["scare_spots"] if s["enabled"]]
        if not choices:
            raise ValueError("Maak eerst een schrikplek met speakers of lampen")
        if not spot_id:
            random.shuffle(choices)
            choices.sort(key=lambda s: s == self.last_spot)
        async with self.lock:
            for selected in choices:
                spot = self.definition(selected)
                if source == "motion" and not self.motion_armed(selected):
                    return None
                if show_token and self.show_status.get("run_id") != show_token:
                    return None
                now = time.monotonic()
                if source == "motion" and now - self.last_motion.get(selected, -float("inf")) < spot["cooldown"]:
                    self.events[selected] = {"state": "cooldown", "at": time.time()}
                    self.c._notify()
                    continue
                cursor_key = (tuple(spot["effects"]), spot["mode"])
                stored = self.cursors.get(selected)
                cursor = deepcopy(stored[1]) if stored and stored[0] == cursor_key else QueueCursor(spot["effects"], spot["mode"], True)
                effect_id = cursor.next()[1]
                effect = self.c.effects.get(effect_id)
                if not effect or effect.category == "moods":
                    raise ValueError("Kies losse effecten voor de schrikplek; sfeer speelt op het eigen kanaal")
                channel = "spot:" + selected
                state = await self.c.async_play(effect_id, spot["settings"], context, channel=channel,
                                               if_idle=True, spot_motion=source == "motion", spot_show_token=show_token,
                                               spot_generation=(generation, stopped.get(selected, 0)))
                self.events[selected] = {"state": "played" if state else "busy", "at": time.time(),
                                         "effect_id": effect_id if state else self.events.get(selected, {}).get("effect_id")}
                if state:
                    self.cursors[selected] = (cursor_key, cursor)
                    if source == "motion":
                        self.last_motion[selected] = now
                    self.last_spot = selected
                    self.c._notify()
                    return state
                self.c._notify()
        return None

    async def start_show(self, context=None):
        async with self.show_lock:
            return await self._start_show(context)

    async def _start_show(self, context=None):
        self.c.ensure_enabled()
        config = deepcopy(self.c.settings["spot_show"])
        enabled = {s["id"] for s in self.c.settings["scare_spots"] if s["enabled"]}
        selected = [s for s in config["spot_ids"] if s in enabled] if config["spot_ids"] else [s["id"] for s in self.c.settings["scare_spots"] if s["enabled"]]
        if not selected:
            raise ValueError("Kies minstens één ingeschakelde schrikplek voor de lus")
        for spot_id in selected:
            spot = self.definition(spot_id)
            for effect_id in spot["effects"]:
                if self.c.effects[effect_id].category == "moods":
                    raise ValueError("Een schrikplek gebruikt losse effecten, geen achtergrondsfeer")
                prepared = self.c.prepare_playback(effect_id, spot["settings"], "spot:" + spot_id)
                self.c.check_audio_overlap("spot:" + spot_id, prepared[3], prepared[4], prepared[1])
        await self._stop_show()
        self.c.ensure_enabled()
        self.show_status = {**idle_show(), "playing": True, "run_id": uuid.uuid4().hex}
        self.task = self.c.hass.async_create_task(self._worker(config, selected, context, self.show_status), "BooCue scare spot loop")
        self.c._notify()
        return deepcopy(self.show_status)

    async def _worker(self, config, selected, context, status):
        cursor = QueueCursor(selected, config["mode"], config["repeat"])
        try:
            while self.show_status is status and status["playing"]:
                item = cursor.next()
                if item is None:
                    break
                spot_id = item[1]
                available = {s["id"]:s for s in self.c.settings["scare_spots"] if s["enabled"]}
                if spot_id not in available:
                    if not set(selected) & available.keys():break
                    continue
                spot = available[spot_id]
                status.update(waiting=None, next_at=None, spot_id=spot_id, spot_name=spot["name"], step=item[3])
                state = await self.trigger(spot_id, context, source="loop", show_token=status["run_id"])
                self.c._notify()
                run = self.c._runs.get("spot:" + spot_id)
                if state and run and run.status["run_id"] == state["run_id"]:
                    await run.finished.wait()
                    if run.status.get("error"):
                        raise ValueError(run.status["error"])
                if not config["repeat"] and not cursor.remaining:
                    break
                gap = random.uniform(config["gap_min"], config["gap_max"])
                if not state:
                    gap = max(1., gap)
                status.update(waiting="delay", next_at=time.time() + gap)
                self.c._notify()
                await asyncio.sleep(gap)
        except asyncio.CancelledError:
            raise
        except Exception as err:
            status["error"] = str(err)[:250]
        finally:
            if self.show_status is status:
                status.update(playing=False, waiting=None, next_at=None)
                self.task = None
                self.c._notify()

    async def stop_show(self, *, stop_effect=True, expected_run_id=None):
        async with self.show_lock:
            await self._stop_show(stop_effect=stop_effect, expected_run_id=expected_run_id)

    async def _stop_show(self, *, stop_effect=True, expected_run_id=None):
        status, task = self.show_status, self.task
        if expected_run_id and status.get("run_id") != expected_run_id:
            return
        self.show_status = {**status, "playing": False, "waiting": None, "next_at": None, "run_id": None}
        self.task = None
        if task and task is not asyncio.current_task() and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        if stop_effect and status.get("spot_id"):
            channel = "spot:" + status["spot_id"]
            state = self.c.channels.get(channel, {})
            if state.get("spot_show_run_id") == status.get("run_id") and state.get("playing"):
                await self.c.async_stop(state["run_id"], channel=channel)
        self.c._notify()

    async def stop_spot(self, spot_id, expected_run_id=None):
        channel = "spot:" + spot_id
        if expected_run_id and self.c.channels.get(channel, {}).get("run_id") != expected_run_id:
            return
        if not expected_run_id:
            self.stop_generations[spot_id] = self.stop_generations.get(spot_id, 0) + 1
        if self.show_status["playing"] and self.show_status.get("spot_id") == spot_id:
            await self.stop_show(stop_effect=False)
        if channel in self.c.channels:
            await self.c.async_stop(expected_run_id, channel=channel)

    async def stop_all(self):
        self.invalidate_pending()
        await self.stop_show(stop_effect=False)
        for channel in list(self.c.channels):
            if channel.startswith("spot:"):
                await self.c.async_stop(channel=channel)
        async with self.c._lock:
            await self.c.props.retry_pending()

    async def settings_changed(self):
        if self._definitions != self.c.settings["scare_spots"]:
            self.invalidate_pending()
            self._definitions = deepcopy(self.c.settings["scare_spots"])
        existing = {s["id"] for s in self.c.settings["scare_spots"]}
        for mapping in (self.cursors, self.last_motion, self.events, self.stop_generations):
            for spot_id in set(mapping) - existing:
                mapping.pop(spot_id, None)
        enabled = {s["id"] for s in self.c.settings["scare_spots"] if s["enabled"]}
        if self.show_status["playing"] and self.show_status.get("spot_id") not in enabled:
            await self.stop_show()
        for channel in list(self.c.channels):
            if channel.startswith("spot:") and channel[5:] not in enabled:
                await self.c.async_stop(channel=channel)
                self.c.channels.pop(channel, None)
        if self.c.settings["spot_concurrency"] == "single":
            foreground = [r for r in self.c._runs.values() if r.channel != "mood"]
            for run in foreground[1:]:
                await self.c.async_stop(run.status["run_id"], channel=run.channel)
