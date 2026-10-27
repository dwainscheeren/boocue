"""Native stop and queue transport buttons for HA dashboards and automations."""
from homeassistant.components.button import ButtonEntity
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, EVENT_STATE

BUTTONS = {
    'stop_all': ('Stop all', 'mdi:stop-circle-outline'),
    'stop_effect': ('Stop effect', 'mdi:stop'),
    'stop_mood': ('Stop mood', 'mdi:music-off'),
    'stop_queue': ('Stop queue', 'mdi:playlist-remove'),
    'next_queue': ('Next queue', 'mdi:skip-next'),
}


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([BooCueButton(entry.runtime_data, entry.entry_id, key) for key in BUTTONS])


class BooCueButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, controller, entry_id, key):
        self.controller, self.key = controller, key
        self._attr_unique_id = f'{entry_id}_{key}'
        self._attr_name, self._attr_icon = BUTTONS[key]
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name='BooCue')

    @property
    def available(self):
        return self.key != 'next_queue' or (self.controller.settings['enabled'] and self.controller.queues.status['playing'])

    async def async_press(self):
        try:
            if self.key == 'next_queue':await self.controller.queues.next()
            elif self.key == 'stop_queue':await self.controller.queues.stop()
            else:await self.controller.async_stop(channel={'stop_effect':'effect','stop_mood':'mood'}.get(self.key),disarm=self.key=='stop_all')
        except (ValueError, TypeError) as err:raise HomeAssistantError(str(err)) from err

    async def async_added_to_hass(self):
        if self.key == 'next_queue':
            self._last_available = self.available
            self.async_on_remove(self.hass.bus.async_listen(EVENT_STATE, self._updated))

    @callback
    def _updated(self, event):
        current = self.available
        if current != self._last_available:
            self._last_available = current
            self.async_write_ha_state()
