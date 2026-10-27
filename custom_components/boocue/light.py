"""Optional clearly named virtual lights for trying BooCue without hardware."""

from homeassistant.components.light import ColorMode, LightEntity, LightEntityFeature
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        BooCueDemoLight(entry.entry_id, "color_one", "Demo color one", ColorMode.HS, True),
        BooCueDemoLight(entry.entry_id, "color_two", "Demo color two", ColorMode.HS, False),
        BooCueDemoLight(entry.entry_id, "dimmer", "Demo dimmer", ColorMode.BRIGHTNESS, True),
        BooCueDemoLight(entry.entry_id, "switch", "Demo on/off", ColorMode.ONOFF, False),
    ])


class BooCueDemoLight(LightEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry_id, key, name, mode, is_on):
        self._attr_unique_id = f"{entry_id}_demo_{key}"
        self._attr_name = name
        self._attr_color_mode = mode
        self._attr_supported_color_modes = {mode}
        self._attr_is_on = is_on
        self._attr_brightness = 160 if mode != ColorMode.ONOFF else None
        self._attr_hs_color = (32, 70) if mode == ColorMode.HS else None
        self._attr_supported_features = LightEntityFeature.TRANSITION if mode != ColorMode.ONOFF else LightEntityFeature(0)
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)})

    async def async_turn_on(self, **kwargs):
        self._attr_is_on = True
        if "brightness" in kwargs and self.color_mode != ColorMode.ONOFF:
            self._attr_brightness = kwargs["brightness"]
        if "hs_color" in kwargs and self.color_mode == ColorMode.HS:
            self._attr_hs_color = kwargs["hs_color"]
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._attr_is_on = False
        self.async_write_ha_state()
