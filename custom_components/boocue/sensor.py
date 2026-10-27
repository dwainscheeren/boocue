"""Playback status for dashboards and automations."""
import time
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, EVENT_STATE, VERSION
from .presentation import presentation_for


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([BooCuePlaybackSensor(entry.runtime_data, entry.entry_id, channel)
                        for channel in (None, 'effect', 'mood', 'queue')])


class BooCuePlaybackSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = 'mdi:ghost'
    _unrecorded_attributes = frozenset({'position', 'cycle', 'channels', 'motion', 'light_preview', 'server_time'})

    def __init__(self, controller, entry_id, channel=None):
        self.controller, self.channel = controller, channel
        self._last_publish = 0
        self._last_key = None
        self._attr_name = channel.capitalize() if channel else 'Playback'
        self._attr_unique_id = f'{entry_id}_{channel or "playback"}'
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name='BooCue',
            manufacturer='BooCue', model='Sound & light soundboard', sw_version=VERSION)

    @property
    def status(self):
        if self.channel=='queue':return self.controller.queues.status
        return self.controller.channels[self.channel] if self.channel else self.controller.status

    @property
    def native_value(self):
        if self.status['playing']:return 'playing'
        return 'error' if self.status.get('error') else 'idle'

    @property
    def extra_state_attributes(self):
        return {k:v for k,v in self.status.items() if k!='playing'}

    @property
    def icon(self):
        if self.channel == 'queue':return 'mdi:playlist-play'
        effect = self.controller.effects.get(self.status.get('effect_id'))
        if effect and self.status['playing']:
            return presentation_for(effect.id,effect.title,effect.description,effect.icon)['icon']
        return 'mdi:music-circle-outline' if self.channel == 'mood' else 'mdi:ghost'

    async def async_added_to_hass(self):
        self.async_on_remove(self.hass.bus.async_listen(EVENT_STATE, self._updated))

    @callback
    def _updated(self, event):
        status = self.status
        queue = status.get('queue', {})
        key = (status['playing'], status.get('run_id'), status.get('effect_id'), status.get('error'),
               status.get('warnings'), status.get('enabled'), status.get('automatic_enabled'),
               status.get('waiting'), status.get('step'), queue.get('run_id'), queue.get('waiting'), queue.get('step'))
        now = time.monotonic()
        if key != self._last_key or now - self._last_publish >= 1:
            self._last_key, self._last_publish = key, now
            self.async_write_ha_state()
