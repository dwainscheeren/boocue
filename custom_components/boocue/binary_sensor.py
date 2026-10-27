"""A simple active/idle condition for HA automations, including waiting queues."""
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, EVENT_STATE


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([BooCueActive(entry.runtime_data, entry.entry_id)])


class BooCueActive(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = 'Active'
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = 'mdi:play-circle-outline'
    _attr_should_poll = False

    def __init__(self, controller, entry_id):
        self.controller = controller
        self._last_on = None
        self._attr_unique_id = f'{entry_id}_active'
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name='BooCue')

    @property
    def is_on(self):
        return (any(state['playing'] for state in self.controller.channels.values())
                or self.controller.queues.status['playing'] or self.controller.spots.show_status['playing'])

    async def async_added_to_hass(self):
        self.async_on_remove(self.hass.bus.async_listen(EVENT_STATE, self._updated))

    @callback
    def _updated(self, event):
        current = self.is_on
        if current != self._last_on:
            self._last_on = current
            self.async_write_ha_state()
