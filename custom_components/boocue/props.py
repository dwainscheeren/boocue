"""Timed, owned switch pulses and single button presses at scare spots."""

import asyncio
import logging
import re
import time

from aiohttp import ClientError
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry

from .const import DOMAIN
from .models import number

LOGGER = logging.getLogger(__name__)
SERVICE_TIMEOUT = 10
PROP_ENTITY = re.compile(r'^(switch|button)\.[a-z0-9_]+$')


def validate_props(raw):
    if not isinstance(raw, list) or len(raw) > 16:
        raise ValueError("Kies maximaal 16 schakelaars of knoppen per schrikplek")
    result, seen = [], set()
    for item in raw:
        if not isinstance(item, dict) or set(item) - {"entity_id", "delay", "duration"}:
            raise ValueError("Ongeldige schakelactie")
        entity_id = item.get("entity_id")
        if (not isinstance(entity_id, str) or len(entity_id) > 255 or not PROP_ENTITY.fullmatch(entity_id)
                or entity_id in seen):
            raise ValueError("Kies elke switch- of button-entiteit maximaal één keer")
        action = {"entity_id": entity_id, "delay": number(item.get('delay', 0), 0, 3600, 'delay')}
        if entity_id.startswith('switch.'):
            action['duration'] = number(item.get('duration', 3), .1, 120, 'duration')
        elif 'duration' in item:
            raise ValueError("Een knop wordt één keer ingedrukt en heeft geen aan-tijd")
        result.append(action)
        seen.add(entity_id)
    return result


class PropManager:
    def __init__(self, controller, store):
        self.c = controller
        self.pending = set()
        self.store = store
        self.lock = asyncio.Lock()

    def prepare(self, actions):
        """Expand switch groups before claiming resources or changing any device."""
        if not actions:
            return []
        registry = entity_registry.async_get(self.c.hass)
        result, visited = {}, set()

        def visit(action, path):
            entity_id = action['entity_id']
            if entity_id in path or len(path) > 8:
                raise ValueError("Ongeldige of te diep geneste schakelgroep")
            entry = registry.async_get(entity_id)
            if entry and entry.platform == DOMAIN:
                raise ValueError("Gebruik BooCue's eigen bediening niet als schrikapparaat")
            state = self.c.hass.states.get(entity_id)
            members = state.attributes.get('entity_id') if state and entity_id.startswith('switch.') else None
            if isinstance(members, (list, tuple)) and members:
                for member in members:
                    if not isinstance(member, str) or not member.startswith('switch.'):
                        raise ValueError("Een schakelgroep mag alleen schakelaars bevatten")
                    visit({**action, 'entity_id': member}, path | {entity_id})
            elif entity_id in result and result[entity_id] != action:
                raise ValueError("Overlappende schakelgroepen hebben verschillende tijden")
            else:
                result[entity_id] = action
            visited.add(entity_id)
            if len(visited) > 64:
                raise ValueError("Kies maximaal 64 afzonderlijke schrikapparaten")

        for action in validate_props(actions):
            visit(action, set())
        return list(result.values())

    async def load(self):
        data = await self.store.async_load()
        if isinstance(data, dict) and isinstance(data.get('switches'), list):
            self.pending = {e for e in data['switches'] if isinstance(e, str) and e.startswith('switch.') and PROP_ENTITY.fullmatch(e)}
        await self.retry_pending()

    async def _remember(self, entity_id):
        async with self.lock:
            self.pending.add(entity_id)
            await self.store.async_save({'switches': sorted(self.pending)})

    async def _forget(self, entity_id):
        async with self.lock:
            remaining = self.pending - {entity_id}
            await self.store.async_save({'switches': sorted(remaining)})
            self.pending = remaining

    async def _call(self, domain, action, entity_id, context):
        async def invoke():
            async with asyncio.timeout(SERVICE_TIMEOUT):
                await self.c.hass.services.async_call(domain, action, {'entity_id': entity_id}, blocking=True, context=context)
        task = asyncio.create_task(invoke())
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            # Finish an already dispatched command before cleanup sends Off.
            await asyncio.gather(task, return_exceptions=True)
            raise

    async def _off(self, entity_id, context=None):
        for attempt in range(2):
            try:
                await self._call('switch', 'turn_off', entity_id, context)
                await self._forget(entity_id)
                return True
            except (HomeAssistantError, ClientError, TimeoutError, OSError):
                if attempt == 0:
                    await asyncio.sleep(.1)
        LOGGER.warning("Could not turn off BooCue switch %s; keeping it for cleanup retry", entity_id)
        return False

    async def retry_pending(self):
        active = {entity_id for run in self.c._runs.values() for entity_id in run.prop_switches}
        await asyncio.gather(*(self._off(e) for e in list(self.pending - active)))

    def ensure_released(self, actions):
        if any(a['entity_id'] in self.pending for a in actions):
            raise ValueError("Een schakelaar wacht nog op uitschakelen. Controleer het apparaat en druk op Stop alles om opnieuw te proberen.")

    async def play(self, run):
        epoch = asyncio.get_running_loop().time() + run.status['start_at'] - time.time()
        end = epoch + run.effect.duration

        async def action(item):
            entity_id, delay = item['entity_id'], item['delay']
            if delay >= run.effect.duration:
                self.c._warn(run, f"Schakelactie valt buiten dit effect: {entity_id}")
                return
            await asyncio.sleep(max(0, epoch + delay - asyncio.get_running_loop().time()))
            if run.stopping or self.c._closed or not self.c.settings['enabled']:
                return
            if asyncio.get_running_loop().time() >= end:
                self.c._warn(run, f"Schakelactie kwam te laat voor dit effect: {entity_id}")
                return
            state = self.c.hass.states.get(entity_id)
            if not state or state.state == 'unavailable' or entity_id.startswith('switch.') and state.state not in {'on', 'off'}:
                self.c._warn(run, f"Schrikapparaat is niet beschikbaar: {entity_id}")
                return
            try:
                if entity_id.startswith('button.'):
                    await self._call('button', 'press', entity_id, run.context)
                    return
                if state.state == 'on':
                    self.c._warn(run, f"Schakelaar stond al aan en is overgeslagen: {entity_id}")
                    return
                run.prop_switches.add(entity_id)
                await self._remember(entity_id)
                if run.stopping or self.c._closed or not self.c.settings['enabled'] or asyncio.get_running_loop().time() >= end:
                    return
                await self._call('switch', 'turn_on', entity_id, run.context)
                deadline = min(end, epoch + delay + item['duration'])
                await asyncio.sleep(max(0, deadline - asyncio.get_running_loop().time()))
                if await self._off(entity_id, run.context):
                    run.prop_switches.discard(entity_id)
                else:
                    self.c._warn(run, f"Schakelaar kon niet uit: {entity_id}. Controleer het apparaat en probeer Stop alles.")
            except (HomeAssistantError, ClientError, TimeoutError, OSError):
                self.c._warn(run, f"Schakelactie kon niet worden uitgevoerd: {entity_id}")
                if entity_id in run.prop_switches and await self._off(entity_id, run.context):
                    run.prop_switches.discard(entity_id)

        async with asyncio.TaskGroup() as group:
            for item in run.prop_actions:
                group.create_task(action(item))

    async def cleanup(self, run):
        async def finish(entity_id):
            if await self._off(entity_id, run.context):
                run.prop_switches.discard(entity_id)
            else:
                self.c._warn(run, f"Schakelaar kon niet uit: {entity_id}. Controleer het apparaat en probeer Stop alles.")
        await asyncio.gather(*(finish(e) for e in list(run.prop_switches)))
