"""Master power and independent motion arming for HA dashboards/automations."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, EVENT_STATE


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([BooCueEnabled(entry.runtime_data, entry.entry_id),
                        BooCueAutomatic(entry.runtime_data, entry.entry_id)])


class BooCueSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, controller, entry_id):
        self.controller = controller
        # Keep the pre-master-control identity used by existing automations.
        self._attr_unique_id = f'{entry_id}_{getattr(self, "identity", self.setting)}'
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name='BooCue')

    @property
    def is_on(self):
        return self.controller.settings[self.setting]

    async def _set(self, value):
        try:await self.controller.async_save_settings({self.setting: value})
        except (ValueError, TypeError) as err:raise HomeAssistantError(str(err)) from err

    async def async_turn_on(self, **kwargs):
        await self._set(True)

    async def async_turn_off(self, **kwargs):
        await self._set(False)

    async def async_added_to_hass(self):
        self.async_on_remove(self.hass.bus.async_listen(EVENT_STATE, self._updated))

    @callback
    def _updated(self, event):
        self.async_write_ha_state()


class BooCueEnabled(BooCueSwitch):
    setting = 'enabled'
    _attr_name = 'Enabled'
    _attr_icon = 'mdi:power'


class BooCueAutomatic(BooCueSwitch):
    setting = 'automatic_enabled'
    identity = 'automatic'
    _attr_name = 'Automatic'
    _attr_icon = 'mdi:motion-sensor'

    @property
    def extra_state_attributes(self):
        return {'effective': self.is_on and self.controller.settings['enabled']}
