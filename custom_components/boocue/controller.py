"""Independent mood/effect playback, resource ownership and motion rules."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import timedelta
import json
import logging
from pathlib import Path
import random
import time
import uuid

from aiohttp import ClientError
from homeassistant.components.http.auth import async_sign_path
from homeassistant.components.media_player.const import MediaPlayerEntityFeature as MP
from homeassistant.core import Context, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.network import get_url, NoURLAvailableError
from homeassistant.helpers.state import async_reproduce_state
from homeassistant.helpers.storage import Store

from .const import CHANNELS, DEFAULT_SETTINGS, DOMAIN, EVENT_STATE, RUNTIME_KEYS
from .engine import play_timeline
from .library import load_library
from .models import Cue, number
from .sequence import validate_queues
from .queue_manager import QueueManager
from .spots import SpotManager, validate_spots, validate_spot_show
from .props import PropManager

LOGGER = logging.getLogger(__name__)
COLOR_MODES = {"hs", "rgb", "rgbw", "rgbww", "xy"}
DIM_MODES = COLOR_MODES | {"brightness", "color_temp", "white"}
START_DELAY_SECONDS = .85


def entity_list(values, domain, limit):
    if (not isinstance(values, list) or len(values) > limit or
            any(not isinstance(v, str) or not v.startswith(domain + ".") or
                len(v) > 255 or v.count(".") != 1 or not v.split(".")[1] for v in values)):
        raise ValueError(f"Kies maximaal {limit} geldige {domain}-entiteiten")
    return list(dict.fromkeys(values))


def validate_runtime(raw):
    result = {k: deepcopy(raw.get(k, DEFAULT_SETTINGS[k])) for k in RUNTIME_KEYS}
    result["lights"] = entity_list(result["lights"], "light", 32)
    result["speakers"] = entity_list(result["speakers"], "media_player", 16)
    for key, lo, hi in [("volume", 0, 1), ("brightness", .01, 1), ("speed", .5, 2),
                        ("offset_ms", -2000, 3000), ("interval_ms", 100, 2000), ("duck_mood", 0, 1)]:
        result[key] = number(result[key], lo, hi, key)
    if result["routing"] not in {"all", "alternate", "random"}:
        raise ValueError("Ongeldige lampverdeling")
    for key in ("repeat", "restore"):
        if not isinstance(result[key], bool):
            raise ValueError(f"{key} moet ja of nee zijn")
    if result["audio_mode"] not in {"auto", "separate"}:
        raise ValueError("Kies automatisch mengen of aparte speakers")
    output = result["output"]
    if isinstance(output, str) and output.startswith("media_player."):
        result["speakers"] = entity_list([output], "media_player", 16)
        result["output"] = "speakers"  # Migrate the original single-player format.
    elif output not in {"browser", "none", "speakers"}:
        raise ValueError("Ongeldige geluidsuitgang")
    return result


def validate_settings(raw: dict, current: dict, effect_ids: set[str]) -> dict:
    if not isinstance(raw, dict) or set(raw) - set(DEFAULT_SETTINGS):
        raise ValueError("Onbekende instelling")
    result = {**deepcopy(DEFAULT_SETTINGS), **deepcopy(current), **deepcopy(raw)}
    result.update(validate_runtime(result))
    favorites = result["favorites"]
    if not isinstance(favorites, list) or len(favorites) > 600 or not all(isinstance(v, str) for v in favorites):
        raise ValueError("Ongeldige favorieten")
    result["favorites"] = [v for v in dict.fromkeys(favorites) if v in effect_ids]
    mood = result["mood"]
    if not isinstance(mood, dict) or set(mood) - (RUNTIME_KEYS | {"effect_id"}):
        raise ValueError("Ongeldige sfeerinstellingen")
    mood = {**deepcopy(DEFAULT_SETTINGS["mood"]), **mood}
    result["mood"] = {**validate_runtime(mood), "effect_id": mood["effect_id"]}
    if mood["effect_id"] is not None and mood["effect_id"] not in effect_ids:
        raise ValueError("Kies een bestaand sfeereffect")
    result["mood"].update(speed=1., repeat=True)
    routes = result["effect_routes"]
    if not isinstance(routes, dict) or len(routes) > 600:
        raise ValueError("Ongeldige effectinstellingen")
    result["effect_routes"] = {}
    for effect_id, route in routes.items():
        if effect_id not in effect_ids:
            continue
        if not isinstance(route, dict) or set(route) - {"output", "speakers", "volume"}:
            raise ValueError("Een effect kan eigen speakers en volume bewaren")
        checked = validate_runtime({**result, **route})
        result["effect_routes"][effect_id] = {k: checked[k] for k in ("output", "speakers", "volume")}
    if not isinstance(result["enabled"], bool):
        raise ValueError("BooCue moet aan of uit zijn")
    if not isinstance(result["automatic_enabled"], bool):
        raise ValueError("Automatisch moet aan of uit zijn")
    result["queues"] = validate_queues(result["queues"], effect_ids, validate_runtime, {k: result[k] for k in RUNTIME_KEYS})
    result["scare_spots"] = validate_spots(result["scare_spots"], effect_ids, validate_runtime,
                                         entity_list, {k: result[k] for k in RUNTIME_KEYS})
    if result["spot_concurrency"] not in {"single", "parallel"}:
        raise ValueError("Kies één schrikplek tegelijk of meerdere tegelijk")
    result["spot_show"] = validate_spot_show(result["spot_show"], {s["id"] for s in result["scare_spots"]})
    queue_ids = {q["id"] for q in result["queues"]}
    rules = result["motion_rules"]
    if not isinstance(rules, list) or len(rules) > 20:
        raise ValueError("Kies maximaal 20 bewegingsregels")
    result["motion_rules"] = []
    seen = set()
    allowed = {"id", "name", "sensor", "sensors", "match", "action", "queue_id", "effects", "cooldown", "mode", "enabled"} | RUNTIME_KEYS
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) - allowed:
            raise ValueError("Ongeldige bewegingsregel")
        rid, name = rule.get("id"), rule.get("name", "")
        if not isinstance(rid, str) or not 1 <= len(rid) <= 64 or rid in seen:
            raise ValueError("Een bewegingsregel heeft een unieke id nodig")
        seen.add(rid)
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            raise ValueError("Geef de bewegingsregel een naam")
        sensors = entity_list(rule.get("sensors", [rule.get("sensor")]), "binary_sensor", 16)
        if not sensors:raise ValueError("Kies minstens één bewegingssensor")
        match, action = rule.get("match", "any"), rule.get("action", "effect")
        if match not in {"any", "all"} or action not in {"effect", "start_queue", "next_queue"}:
            raise ValueError("Ongeldige sensorcombinatie of actie")
        queue_id = rule.get("queue_id")
        if action != "effect" and queue_id not in queue_ids:
            raise ValueError("Kies een bestaande wachtrij voor de bewegingsregel")
        effects = rule.get("effects", [])
        if (not isinstance(effects, list) or len(effects) > 50 or (action == "effect" and not effects) or
                any(not isinstance(e, str) or e not in effect_ids for e in effects)):
            raise ValueError("Kies 1 tot 50 bestaande effecten")
        mode = rule.get("mode", "random")
        enabled = rule.get("enabled", True)
        if mode not in {"random", "sequence"} or not isinstance(enabled, bool):
            raise ValueError("Ongeldige bewegingsregel")
        runtime = validate_runtime({**result, **{k: rule[k] for k in RUNTIME_KEYS if k in rule}})
        if action == "effect" and runtime["output"] == "speakers" and not runtime["speakers"]:
            raise ValueError("Kies speakers voor de bewegingsregel")
        if action == "effect" and runtime["output"] == "none" and not runtime["lights"]:
            raise ValueError("Kies lampen of speakers voor de bewegingsregel")
        runtime.update(speed=1., repeat=False)
        result["motion_rules"].append({**runtime, "id": rid, "name": name.strip(), "sensor": sensors[0], "sensors": sensors, "match": match, "action": action, "queue_id": queue_id if action != "effect" else None,
            "effects": list(dict.fromkeys(effects)), "cooldown": number(rule.get("cooldown", 30), 0, 3600, "cooldown"),
            "mode": mode, "enabled": enabled})
    return result


def expand_lights(hass: HomeAssistant, selected: list[str]) -> list[str]:
    """Expand nested light groups and preserve individual restoration."""
    result, visited = [], set()

    def visit(entity_id, depth):
        if entity_id in visited or depth > 8:
            return
        visited.add(entity_id)
        state = hass.states.get(entity_id)
        if not state or not entity_id.startswith("light."):
            return
        members = state.attributes.get("entity_id")
        if isinstance(members, (list, tuple)) and members:
            for member in members:
                if isinstance(member, str):
                    visit(member, depth + 1)
        elif state.state not in {"unknown", "unavailable"}:
            result.append(entity_id)
    for selected_id in selected:
        visit(selected_id, 0)
    if len(result) > 64:
        raise ValueError("Kies maximaal 64 afzonderlijke lampen")
    return result


def player_resources(hass, entity_id, visited=None):
    """Account for existing groups without changing the user's group membership."""
    visited = set() if visited is None else visited
    if entity_id in visited or len(visited) > 64:
        return visited
    visited.add(entity_id)
    state = hass.states.get(entity_id)
    if state:
        for key in ("group_members", "entity_id"):
            members = state.attributes.get(key, [])
            if isinstance(members, (list, tuple)):
                for member in members:
                    if isinstance(member, str) and member.startswith("media_player."):
                        player_resources(hass, member, visited)
    return visited


def player_can_overlay(hass, player):
    """Only Sonos' documented announcement overlay promises continuous background."""
    state = hass.states.get(player)
    if not state or not state.attributes.get("supported_features", 0) & MP.MEDIA_ANNOUNCE:
        return False
    entry = entity_registry.async_get(hass).async_get(player)
    return bool(entry and entry.platform == "sonos")


def light_command(state, cue: Cue, scale: float, speed: float) -> tuple[str, dict]:
    brightness = max(0, min(1, cue.brightness * scale))
    data = {"transition": cue.transition / speed} if state.attributes.get("supported_features", 0) & 32 else {}
    if brightness <= 0:
        return "turn_off", data
    modes = set(state.attributes.get("supported_color_modes", []))
    if modes & DIM_MODES:
        data["brightness"] = max(1, round(brightness * 255))
    if modes & COLOR_MODES:
        data["hs_color"] = [cue.hue, cue.saturation * 100]
    return "turn_on", data


def idle_status():
    return {"playing": False, "effect_id": None, "position": 0, "cycle": 0, "error": None, "warnings": 0, "notes": []}


def preview_light(state, cue, scale, active=True):
    """Describe the intended command using the same capability mapping as playback."""
    action, data = light_command(state, cue, scale, 1)
    hs = data.get('hs_color', [0, 0])
    return {'id': state.entity_id, 'name': state.name, 'hue': hs[0], 'saturation': hs[1] / 100,
            'brightness': data.get('brightness', 255) / 255 if action == 'turn_on' else 0,
            'active': active}


@dataclass
class Playback:
    channel: str
    effect: object
    settings: dict
    context: Context
    lights: list
    players: list
    resources: set
    audio_base: str | None
    delay: float
    status: dict
    task: asyncio.Task | None = None
    stopping: bool = False
    volumes: dict = field(default_factory=dict)
    started: set = field(default_factory=set)
    desired: dict = field(default_factory=dict)
    last_progress: float = 0
    finished: asyncio.Event = field(default_factory=asyncio.Event)
    announcements: set = field(default_factory=set)
    preview_cue: Cue | None = None
    prop_actions: list = field(default_factory=list)
    prop_switches: set = field(default_factory=set)


class BooCueController:
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.private = Path(hass.config.path(DOMAIN, "packs"))
        self.builtin = Path(__file__).parent / "assets"
        self.effects, self.library_errors = {}, []
        self.settings = deepcopy(DEFAULT_SETTINGS)
        self.store = Store(hass, 1, DOMAIN)
        self.channels = {name: idle_status() for name in CHANNELS}
        self._runs = {}
        self._light_snapshots = {}
        self._lock, self._settings_lock, self._auto_lock = asyncio.Lock(), asyncio.Lock(), asyncio.Lock()
        self._power_lock = asyncio.Lock()
        self._stop_sequence = 0
        self._settings_revision = 0
        self._library_revision = 0
        self._motion_unsub = None
        self._auto_last, self._auto_index, self._auto_events = {}, {}, {}
        self._motion_tasks = set()
        self._closed = False
        self._browser_station = None
        self.queues = QueueManager(self)
        self.spots = SpotManager(self)
        self.props = PropManager(self, Store(hass, 1, DOMAIN + '_props'))

    @property
    def status(self):
        channels = deepcopy(self.channels)
        foreground_lights = {p for r in self._runs.values() if r.channel != 'mood' for p in r.lights}
        for name, run in self._runs.items():
            samples = []
            for entity_id, cue in run.desired.items():
                state = self.hass.states.get(entity_id)
                if state and state.state not in {'unknown', 'unavailable'}:
                    active = not (name == 'mood' and entity_id in foreground_lights)
                    samples.append(preview_light(state, cue, run.settings['brightness'], active))
            if not run.lights and run.preview_cue:
                cue = run.preview_cue
                samples = [{'id': 'cue', 'name': '', 'hue': cue.hue, 'saturation': cue.saturation,
                            'brightness': cue.brightness * run.settings['brightness'], 'active': True}]
            channels[name].update(light_preview=samples, preview_kind='commands' if run.lights else 'timeline')
        priority = [c for c in self.channels if c != 'mood'] + ['mood']
        active = next((self.channels[c] for c in priority if self.channels[c]["playing"]),
                      next((self.channels[c] for c in CHANNELS if self.channels[c].get("error")), self.channels["effect"]))
        return {**active, "playing": any(s["playing"] for s in self.channels.values()) or self.queues.status["playing"] or self.spots.show_status['playing'],
                "channels": channels, "enabled": self.settings['enabled'], "automatic_enabled": self.settings["automatic_enabled"],
                "motion": deepcopy(self._auto_events), "queue": deepcopy(self.queues.status),
                "stop_sequence": self._stop_sequence,
                "settings_revision": self._settings_revision, "library_revision": self._library_revision,
                "scare_spots": self.spots.status(), "spot_show": deepcopy(self.spots.show_status),
                "prop_cleanup_pending": sorted(self.props.pending - {e for run in self._runs.values() for e in run.prop_switches}),
                "browser_ready": bool(self._browser_station), "browser_station_id": self.browser_id}

    async def async_load(self):
        await self.async_reload_library()
        stored = await self.store.async_load()
        if isinstance(stored, dict):
            try:
                self.settings = validate_settings(stored, DEFAULT_SETTINGS, set(self.effects))
            except (ValueError, TypeError):
                LOGGER.warning("BooCue settings were invalid; using defaults")
                # A damaged unrelated preference must not bypass a persisted master Off.
                if stored.get('enabled') is False:self.settings['enabled'] = False
        await self.props.load()
        self._bind_motion()

    async def async_reload_library(self):
        self.effects, self.library_errors = await self.hass.async_add_executor_job(load_library, self.builtin, self.private)
        self._library_revision += 1

    async def async_save_settings(self, values):
        if isinstance(values, dict) and 'enabled' in values:
            # Serialize Off cleanup with a later On, so old cleanup cannot stop a new show.
            async with self._power_lock:
                return await self._save_settings(values)
        return await self._save_settings(values)

    async def _save_settings(self, values):
        async with self._settings_lock:
            settings = validate_settings(values, self.settings, set(self.effects))
            await self.store.async_save(settings)
            if settings != self.settings:self._settings_revision += 1
            self.settings = settings
            self._bind_motion()
        if values.get('enabled') is False:
            await self.async_stop(disarm=False)
        if self.queues.run and self.queues.run.definition['id'] not in {q['id'] for q in self.settings['queues']}:
            await self.queues.stop()
        await self.spots.settings_changed()
        self._notify()
        return deepcopy(self.settings)

    def _notify(self):
        self.hass.bus.async_fire(EVENT_STATE, {**self.status, "server_time": time.time()})

    @property
    def browser_id(self):
        return self._browser_station['id'] if self._browser_station else None

    def rule_is_armed(self, rule_id):
        return not self._closed and self.settings['enabled'] and self.settings['automatic_enabled'] and any(r['id']==rule_id and r['enabled'] for r in self.settings['motion_rules'])

    def ensure_enabled(self):
        if self._closed:raise ValueError('BooCue wordt afgesloten')
        if not self.settings['enabled']:raise ValueError('BooCue staat uit. Zet eerst de globale BooCue-schakelaar aan.')

    async def async_register_browser(self, owner):
        old=self._browser_station
        if old and old['owner'] is owner:return old['id']
        if old and (any(s['playing'] and s.get('browser_id')==old['id'] for s in self.channels.values()) or self.queues.status.get('browser_id')==old['id'] and self.queues.status['playing']):
            raise ValueError('Een ander apparaat speelt het browsergeluid. Stop dat eerst om dit apparaat te kiezen.')
        self._browser_station={'id':uuid.uuid4().hex,'owner':owner}
        self._notify()
        return self.browser_id

    async def async_release_browser(self, station_id, owner):
        if not self._browser_station or self._browser_station['id']!=station_id or self._browser_station['owner'] is not owner:return
        self._browser_station=None
        if self.queues.status.get('browser_id')==station_id:
            await self.queues.stop()
        for channel in CHANNELS:
            state=self.channels[channel]
            if state.get('browser_id')==station_id:
                await self.async_stop(state.get('run_id'),channel=channel,include_queue=False)
        self._notify()

    def _bind_motion(self):
        if self._motion_unsub:self._motion_unsub();self._motion_unsub=None
        sensors={sensor for r in self.settings['motion_rules'] if r['enabled'] for sensor in r['sensors']} if self.settings['enabled'] else set()
        if self.settings['enabled']:
            sensors.update(sensor for spot in self.settings['scare_spots'] if spot['enabled'] for sensor in spot['sensors'])
        if sensors and not self._closed:
            self._motion_unsub=async_track_state_change_event(self.hass,sensors,self._motion_changed)

    @callback
    def _motion_changed(self,event):
        old,new=event.data.get('old_state'),event.data.get('new_state')
        if not self.settings['enabled'] or not self.settings['automatic_enabled'] or not old or not new or old.state!='off' or new.state!='on' or self._closed:return
        for spot in self.settings['scare_spots']:
            if not spot['enabled'] or new.entity_id not in spot['sensors']:continue
            states=[new if sensor==new.entity_id else self.hass.states.get(sensor) for sensor in spot['sensors']]
            if spot['match']=='all' and not all(s and s.state=='on' for s in states):continue
            task=self.hass.async_create_task(self.spots.trigger(spot['id'],event.context,source='motion'),'BooCue scare spot motion')
            self._motion_tasks.add(task);task.add_done_callback(self._motion_tasks.discard)
        for rule in self.settings['motion_rules']:
            if not rule['enabled'] or new.entity_id not in rule['sensors']:continue
            if rule['match']=='all':
                states=[new if sensor==new.entity_id else self.hass.states.get(sensor) for sensor in rule['sensors']]
                if not all(state and state.state=='on' for state in states):continue
            task=self.hass.async_create_task(self._trigger_motion(rule['id'],event.context),'BooCue motion')
            self._motion_tasks.add(task);task.add_done_callback(self._motion_tasks.discard)

    async def _trigger_motion(self,rule_id,context):
        async with self._auto_lock:
            rule=next((r for r in self.settings['motion_rules'] if r['id']==rule_id),None)
            if not rule or not self.rule_is_armed(rule_id):return
            now=time.monotonic();event={'at':time.time(),'state':'cooldown'}
            if now-self._auto_last.get(rule_id,-float('inf'))>=rule['cooldown']:
                index=self._auto_index.get(rule_id,0)
                try:
                    if rule['action']=='start_queue':
                        state=await self.queues.start(rule['queue_id'],context=context,automatic_rule=rule_id,if_idle=True)
                    elif rule['action']=='next_queue':
                        state=await self.queues.next(rule['queue_id'],context,automatic_rule=rule_id)
                    else:
                        previous=self._auto_events.get(rule_id,{}).get('effect_id')
                        choices=[eid for eid in rule['effects'] if eid!=previous] or rule['effects']
                        effect=random.choice(choices) if rule['mode']=='random' else rule['effects'][index%len(rule['effects'])]
                        state=await self.async_play(effect,{k:rule[k] for k in RUNTIME_KEYS},context,if_idle=True,automatic_rule=rule_id)
                        event['effect_id']=effect if state else previous
                    event['state']='played' if state else 'busy'
                    if state:self._auto_last[rule_id]=now;self._auto_index[rule_id]=index+1
                except (ValueError,HomeAssistantError) as err:event.update(state='error',error=str(err)[:250])
            if 'effect_id' not in event and self._auto_events.get(rule_id,{}).get('effect_id'):
                event['effect_id']=self._auto_events[rule_id]['effect_id']
            self._auto_events[rule_id]=event;self._notify()

    async def async_close(self):
        self._closed = True
        self._browser_station = None
        await self.queues.stop()
        if self._motion_unsub:
            self._motion_unsub()
            self._motion_unsub = None
        for task in list(self._motion_tasks):
            task.cancel()
        await asyncio.gather(*self._motion_tasks, return_exceptions=True)
        await self.async_stop(disarm=False)

    async def _stop_locked(self, channel):
        run = self._runs.get(channel)
        if not run:
            return
        run.stopping = True
        if run.task and not run.task.done():
            run.task.cancel()
            try:
                await run.task
            except asyncio.CancelledError:
                pass
        await self._cleanup_locked(run)

    async def async_stop(self, expected_run_id=None, *, channel=None, disarm=False, include_queue=True):
        if channel is not None and channel not in self.channels:
            raise ValueError("Kies effect of mood")
        if channel is None and not expected_run_id:
            self.spots.invalidate_pending()
            await self.spots.stop_show(stop_effect=False)
        if disarm and not expected_run_id:
            await self.async_save_settings({"automatic_enabled": False})
        if include_queue and channel in {None,'effect'} and not expected_run_id:
            await self.queues.stop()
        async with self._lock:
            for name in ([channel] if channel else list(self.channels)):
                if expected_run_id and self.channels[name].get("run_id") != expected_run_id:
                    continue
                await self._stop_locked(name)
            if channel is None and not expected_run_id:
                await self.props.retry_pending()
        if channel is None and not expected_run_id:
            # Also cancel local previews/pending decodes in connected panels.
            # Publish after cleanup so old channel state cannot restart browser audio.
            self._stop_sequence += 1
            self._notify()

    def playback_settings(self, effect_id, channel, overrides):
        base = self.settings["mood"] if channel == "mood" else self.settings
        values = {k: deepcopy(base[k]) for k in RUNTIME_KEYS}
        if channel == "effect":
            values.update(self.settings["effect_routes"].get(effect_id, {}))
        if not isinstance(overrides, dict) or set(overrides) - RUNTIME_KEYS:
            raise ValueError("Onbekende afspeelinstelling")
        values.update(overrides)
        values = validate_runtime(values)
        if channel == "mood":
            values.update(repeat=True, speed=1.)
        return values

    def prepare_playback(self,effect_id,settings,channel,browser_id=None,browser=False):
        spot = next((s for s in self.settings['scare_spots'] if channel=='spot:'+s['id'] and s['enabled']), None)
        if (channel not in CHANNELS and not spot) or effect_id not in self.effects:
            raise ValueError("Kies een bestaand effect en kanaal")
        effect = self.effects[effect_id]
        if channel == "mood" and effect.category != "moods":
            raise ValueError("Kies een sfeereffect voor de doorlopende sfeer")
        if spot and effect.category == 'moods':
            raise ValueError("Kies losse effecten voor een schrikplek; sfeer speelt op het eigen kanaal")
        settings = validate_runtime(settings)
        lights = expand_lights(self.hass, settings["lights"])
        output = settings["output"]
        if not lights and output == "none" and not (spot and spot.get('props')):
            raise ValueError("Kies minstens één beschikbare lamp of geluidsuitgang")
        if output == "browser" and not browser and (not browser_id or browser_id != self.browser_id):
            raise ValueError("Schakel eerst automatisch browsergeluid in op het BooCue-paneel, of kies HA-speakers.")
        if settings["speed"] != 1 and output == "speakers":
            raise ValueError("De afspeelsnelheid kan alleen op dit apparaat of zonder geluid worden aangepast")
        players, resources, audio_base = [], set(), None
        if output == "speakers":
            if not settings["speakers"]:
                raise ValueError("Kies minstens één HA-speaker")
            candidates = sorted(settings["speakers"], key=lambda p: -len(player_resources(self.hass, p)))
            for player_id in candidates:
                state = self.hass.states.get(player_id)
                if not state or state.state in {"unknown", "unavailable"}:
                    raise ValueError(f"Speaker {player_id} is niet beschikbaar")
                if not state.attributes.get("supported_features", 0) & MP.PLAY_MEDIA:
                    raise ValueError(f"{state.name} ondersteunt geen media afspelen")
                members = player_resources(self.hass, player_id)
                if members <= resources:
                    continue  # Selecting a player plus its existing group must not double-play.
                if members & resources:
                    raise ValueError("Kies speakergroepen zonder overlappende leden")
                resources |= members
                players.append(player_id)
            try:
                audio_base = get_url(self.hass, allow_external=False, allow_cloud=False).rstrip("/")
            except NoURLAvailableError as err:
                raise ValueError("Stel een bereikbaar intern Home Assistant-adres in bij Instellingen → Systeem → Netwerk") from err
        return effect,settings,lights,players,resources,audio_base

    def check_audio_overlap(self,channel,players,resources,settings):
        announcements={p for p in players if channel!='mood' and settings['audio_mode']=='auto' and player_can_overlay(self.hass,p)}
        for other in self._runs.values():
            if other.channel==channel or not resources & other.resources:continue
            if channel!='mood' and other.channel=='mood':
                shared=[p for p in players if player_resources(self.hass,p)&other.resources]
                allowed=all(p in announcements for p in shared)
            elif channel=='mood' and other.channel!='mood':
                shared=[p for p in other.players if player_resources(self.hass,p)&resources]
                allowed=all(p in other.announcements for p in shared)
            else:
                raise ValueError('Deze speakers worden al door een ander effect gebruikt. Kies aparte speakers of wacht tot het effect klaar is.')
            if not allowed:
                raise ValueError('Deze HA-speaker kan sfeer en effecten niet tegelijk mengen. Gebruik aparte speakers, dit apparaat, of geschikte Sonos-speakers met aankondigingen.')
        return announcements

    def foreground_busy(self, channel, lights, resources, prop_actions=()):
        if channel=='mood':return False
        for other in self._runs.values():
            if other.channel in {channel,'mood'}:continue
            if (channel.startswith('spot:') or other.channel.startswith('spot:')) and self.settings['spot_concurrency']=='single':return True
            if set(lights)&set(other.lights) or resources&other.resources:return True
            if {a['entity_id'] for a in prop_actions} & {a['entity_id'] for a in other.prop_actions}:return True
        return False

    async def async_play(self,effect_id,overrides=None,context=None,*,browser=False,browser_id=None,
                         channel='effect',if_idle=False,automatic_rule=None,queue_token=None,
                         spot_motion=False,spot_show_token=None,spot_generation=None):
        self.ensure_enabled()
        browser_id=browser_id or self.browser_id
        settings=self.playback_settings(effect_id,channel,overrides or {})
        effect,settings,lights,players,resources,audio_base=self.prepare_playback(effect_id,settings,channel,browser_id,browser)
        spot = next((s for s in self.settings['scare_spots'] if channel == 'spot:' + s['id']), None)
        prop_actions = self.props.prepare(spot.get('props', [])) if spot else []
        output=settings['output']
        if self.foreground_busy(channel,lights,resources,prop_actions):
            if if_idle:return None
            raise ValueError('Een andere schrikplek gebruikt deze lampen of speakers, of één plek tegelijk staat aan. Wacht of kies meerdere tegelijk met aparte apparaten.')
        self.check_audio_overlap(channel,players,resources,settings)
        if channel=='effect' and not queue_token:
            if if_idle and self.queues.run:return None
            if not if_idle:await self.queues.stop()
        async with self._lock:
            self.ensure_enabled()
            if spot_generation is not None and spot_generation != (self.spots.generation, self.spots.stop_generations.get(channel.removeprefix('spot:'),0)):return None
            if spot_motion and not self.spots.motion_armed(channel.removeprefix('spot:')):return None
            if spot_show_token and self.spots.show_status.get('run_id')!=spot_show_token:return None
            if channel.startswith('spot:') and not any(channel=='spot:'+s['id'] and s['enabled'] for s in self.settings['scare_spots']):return None
            if queue_token and (not self.queues.run or self.queues.run.status['run_id']!=queue_token):return None
            if automatic_rule:
                rule = next((r for r in self.settings["motion_rules"] if r["id"] == automatic_rule and r["enabled"]), None)
                if not self.settings["automatic_enabled"] or not rule:
                    return None
            if if_idle and self.channels.get(channel,{}).get("playing"):
                return None
            if self.foreground_busy(channel,lights,resources,prop_actions):
                if if_idle:return None
                raise ValueError('Een andere schrikplek gebruikt deze apparaten of één plek tegelijk staat aan.')
            announcements=self.check_audio_overlap(channel,players,resources,settings)
            await self._stop_locked(channel)
            self.ensure_enabled()
            self.props.ensure_released(prop_actions)
            for entity_id in lights:
                if entity_id not in self._light_snapshots:
                    self._light_snapshots[entity_id] = self.hass.states.get(entity_id)
            delay = START_DELAY_SECONDS + max(0, -settings["offset_ms"] / 1000)
            status = {**idle_status(), "playing": True, "run_id": uuid.uuid4().hex, "channel": channel,
                      "effect_id": effect.id, "title": effect.title, "duration": effect.duration,
                      "start_at": time.time() + delay, "speed": settings["speed"], "repeat": settings["repeat"],
                      "output": output, "speakers": players, "lights": lights,
                      "browser_id": browser_id if output=="browser" else None,"queue_run_id":queue_token,
                      "duck_mood":settings["duck_mood"],"volume":settings["volume"],"announcements":sorted(announcements)}
            status.update(brightness=settings['brightness'], offset_ms=settings['offset_ms'], routing=settings['routing'])
            if channel.startswith('spot:'):
                spot=next(s for s in self.settings['scare_spots'] if channel=='spot:'+s['id'])
                status.update(spot_id=spot['id'],spot_name=spot['name'],spot_show_run_id=spot_show_token)
            run = Playback(channel, effect, settings, context or Context(), lights, players, resources,
                           audio_base, delay, status)
            run.announcements=announcements
            run.prop_actions=prop_actions
            status['prop_entities']=[a['entity_id'] for a in prop_actions]
            self._runs[channel] = run
            self.channels[channel] = status
            run.task = self.hass.async_create_task(self._run(run), f"BooCue {channel}")
            self._notify()
            return {**deepcopy(status), "server_time": time.time()}

    def _warn(self, run, text):
        run.status["warnings"] += 1
        if text not in run.status["notes"]:
            run.status["notes"] = (run.status["notes"] + [text])[-8:]

    async def _command_lights(self, run, commands):
        groups = defaultdict(list)
        for entity_id, cue in commands.items():
            state = self.hass.states.get(entity_id)
            if not state or state.state in {"unknown", "unavailable"}:
                continue
            action, data = light_command(state, cue, run.settings["brightness"], run.settings["speed"])
            groups[(action, json.dumps(data, sort_keys=True))].append(entity_id)
        for (action, serialized), targets in groups.items():
            try:
                await self.hass.services.async_call("light", action,
                    {"entity_id": targets, **json.loads(serialized)}, blocking=True, context=run.context)
            except (HomeAssistantError, ClientError, TimeoutError):
                # Some light integrations expose transport errors directly. Drop
                # this cue; the absolute-time scheduler will use the latest next
                # cue without interrupting audio or replaying missed flashes.
                self._warn(run, "Een lichtcommando kon niet worden uitgevoerd")

    async def _remote_audio(self, run):
        if not run.players:
            if run.settings["output"] == "browser":
                if run.settings["repeat"]:
                    await asyncio.Future()
                else:
                    await asyncio.sleep(run.delay + run.effect.duration / run.settings["speed"])
            return
        start = time.monotonic() + run.status["start_at"] - time.time()
        async def prepare(player):
            state = self.hass.states.get(player)
            if not state:
                self._warn(run, f"Speaker is niet meer beschikbaar: {player}")
                return
            if player not in run.announcements and state.attributes.get("supported_features", 0) & MP.VOLUME_SET:
                old = state.attributes.get("volume_level")
                if isinstance(old, (int, float)):
                    run.volumes[player] = old
                try:
                    await self.hass.services.async_call("media_player", "volume_set",
                        {"entity_id": player, "volume_level": run.settings["volume"]}, blocking=True, context=run.context)
                except HomeAssistantError:
                    self._warn(run, f"Volume kon niet worden ingesteld: {state.name}")
        await asyncio.gather(*(prepare(p) for p in run.players))
        cycle = 0
        while True:
            await asyncio.sleep(max(0, start + cycle * run.effect.duration - time.monotonic()))
            signed = async_sign_path(self.hass, f"/api/boocue/audio/{run.effect.id}", timedelta(minutes=35))
            async def play(player):
                was_started = player in run.started
                try:
                    # A stop during an in-flight service call must still stop the speaker.
                    run.started.add(player)
                    data={"entity_id":player,"media_content_id":run.audio_base+signed,"media_content_type":"music"}
                    if player in run.announcements:data.update(announce=True,extra={'volume':round(run.settings['volume']*100)})
                    await self.hass.services.async_call('media_player','play_media',data,blocking=True,context=run.context)
                except HomeAssistantError:
                    if not was_started:
                        run.started.discard(player)
                    self._warn(run, f"Audio kon niet starten: {player}")
            await asyncio.gather(*(play(p) for p in run.players))
            if not run.started:
                raise HomeAssistantError("Audio kon op geen van de gekozen speakers starten")
            cycle = max(cycle + 1, int((time.monotonic() - start) // run.effect.duration) + 1)
            if not run.settings["repeat"]:
                await asyncio.sleep(max(0, start + run.effect.duration - time.monotonic()))
                return

    async def _run(self, run):
        randomizer = random.Random()
        async def emit(cue, step):
            run.preview_cue = cue
            targets = run.lights
            if targets and run.settings["routing"] != "all":
                targets = [targets[step % len(targets)]] if run.settings["routing"] == "alternate" else [randomizer.choice(targets)]
            run.desired.update({entity_id: cue for entity_id in targets})
            hidden = {p for r in self._runs.values() if r.channel!='mood' for p in r.lights} if run.channel=='mood' else set()
            await self._command_lights(run, {p: cue for p in targets if p not in hidden})
        def progress(position, cycle):
            run.status.update(position=position, cycle=cycle)
            now = time.monotonic()
            if now - run.last_progress >= .25:
                run.last_progress = now
                self._notify()
        try:
            async with asyncio.TaskGroup() as group:
                group.create_task(play_timeline(run.effect, emit, progress,
                    start_delay=run.delay + run.settings["offset_ms"] / 1000, speed=run.settings["speed"],
                    interval=run.settings["interval_ms"] / 1000, repeat=run.settings["repeat"]))
                group.create_task(self._remote_audio(run))
                if run.prop_actions:
                    group.create_task(self.props.play(run))
        except asyncio.CancelledError:
            raise
        except Exception as err:
            LOGGER.exception("BooCue %s playback failed", run.channel)
            while isinstance(err, BaseExceptionGroup):
                err = err.exceptions[0]
            run.status["error"] = str(err)[:250]
        finally:
            if not run.stopping:
                async with self._lock:
                    await self._cleanup_locked(run)

    async def _cleanup_locked(self, run):
        if self._runs.get(run.channel) is not run:
            return
        await self.props.cleanup(run)
        # Keep ownership until stop/volume restoration has completed.
        async def finish(player):
            state = self.hass.states.get(player)
            features = state.attributes.get("supported_features", 0) if state else 0
            if player in run.started and player in run.announcements:
                if run.stopping:self._warn(run,'Een Sonos-aankondiging kan uitspelen; de achtergrond wordt niet gestopt.')
            if player in run.started and player not in run.announcements:
                action = "media_stop" if features & MP.STOP else "media_pause" if features & MP.PAUSE else None
                if action:
                    try:
                        await self.hass.services.async_call("media_player", action, {"entity_id": player}, blocking=True, context=run.context)
                    except HomeAssistantError:
                        self._warn(run, f"Speaker kon niet stoppen: {player}")
                else:
                    self._warn(run, f"Deze speaker ondersteunt geen stoppen: {player}")
            if player in run.volumes:
                try:
                    await self.hass.services.async_call("media_player", "volume_set", {
                        "entity_id": player, "volume_level": run.volumes[player]}, blocking=True, context=run.context)
                except HomeAssistantError:
                    self._warn(run, f"Speakervolume kon niet worden hersteld: {player}")
        await asyncio.gather(*(finish(p) for p in run.players))
        del self._runs[run.channel]
        others = list(self._runs.values())
        restore = []
        for entity_id in run.lights:
            if any(entity_id in other.lights for other in others):
                continue
            snapshot = self._light_snapshots.pop(entity_id, None)
            if snapshot and run.settings["restore"]:
                restore.append(snapshot)
        if restore:
            try:
                await async_reproduce_state(self.hass, restore, context=run.context)
            except Exception:
                LOGGER.exception("Could not restore BooCue lights")
                run.status["error"] = "Niet alle lampstanden konden worden hersteld; controleer je lampen."
        mood=self._runs.get('mood')
        if run.channel != 'mood' and mood:
            hidden={p for other in others if other.channel!='mood' for p in other.lights}
            await self._command_lights(mood, {p: cue for p, cue in mood.desired.items() if p in run.lights and p not in hidden})
        run.status["playing"] = False
        run.finished.set()
        self._notify()
