"""BooCue: a local sound-and-light soundboard for Home Assistant."""

from pathlib import Path
import hashlib

import voluptuous as vol

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.exceptions import HomeAssistantError, Unauthorized
from homeassistant.helpers import config_validation as cv

from .api import async_register_api
from .const import DOMAIN, VERSION
from .controller import BooCueController

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def frontend_revision():
    root = Path(__file__).parent / "frontend"
    files = sorted(p for p in root.iterdir() if p.suffix in {'.js', '.css'})
    return hashlib.sha256(b''.join(p.name.encode() + p.read_bytes() for p in files)).hexdigest()[:12]


def register_card_module(hass, data, revision):
    """Keep one current resource in HA's native UrlManager."""
    old_module = data.get('card_module_url')
    if old_module:hass.data[frontend.DATA_EXTRA_MODULE_URL].remove(old_module)
    card_module = f'/boocue_frontend/boocue-card.js?v={VERSION}&build={revision}'
    frontend.add_extra_js_url(hass, card_module)
    data['card_module_url'] = card_module


def remove_card_module(hass, data):
    card_module = data.pop('card_module_url', None)
    if card_module:hass.data[frontend.DATA_EXTRA_MODULE_URL].remove(card_module)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data.setdefault(DOMAIN, {})
    c = BooCueController(hass)
    await c.async_load()
    data["controller"] = c
    entry.runtime_data = c

    async def stopping(event):
        await c.async_close()

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stopping))
    if not data.get("registered"):
        await hass.http.async_register_static_paths([
            StaticPathConfig("/boocue_frontend", str(Path(__file__).parent / "frontend"), False),
        ])
        async_register_api(hass)
        data["registered"] = True
    revision = await hass.async_add_executor_job(frontend_revision)
    # Native frontend module registration also works with YAML dashboards/resources.
    register_card_module(hass, data, revision)
    await panel_custom.async_register_panel(
        hass, "boocue", "boocue-panel", sidebar_title="BooCue", sidebar_icon="mdi:ghost",
        module_url=f"/boocue_frontend/boocue-panel.js?v={VERSION}&build={revision}", require_admin=True,
        config={"version": VERSION}, config_panel_domain=DOMAIN,
    )

    async def require_admin(call: ServiceCall):
        if call.context.user_id:
            user = await hass.auth.async_get_user(call.context.user_id)
            if not user or not user.is_admin:
                raise Unauthorized(context=call.context)

    async def play(call: ServiceCall):
        await require_admin(call)
        try:
            settings = {k: v for k, v in call.data.items() if k not in {"effect_id", "channel", "if_idle"}}
            return await c.async_play(call.data["effect_id"], settings, call.context,
                                      channel=call.data.get("channel", "effect"), if_idle=call.data.get("if_idle", False))
        except (ValueError, TypeError) as err:
            raise HomeAssistantError(str(err)) from err

    async def stop(call: ServiceCall):
        await require_admin(call)
        await c.async_stop(channel=call.data.get("channel"), disarm=not call.data.get("channel"))

    async def automatic(call: ServiceCall):
        await require_admin(call)
        await c.async_save_settings({"automatic_enabled": call.data["enabled"]})

    async def enabled(call: ServiceCall):
        await require_admin(call)
        await c.async_save_settings({'enabled': call.data['enabled']})

    async def queue_start(call: ServiceCall):
        await require_admin(call)
        try:
            return await c.queues.start(call.data['queue_id'],call.data.get('settings',{}),call.context,if_idle=call.data.get('if_idle',False))
        except (ValueError,TypeError) as err:raise HomeAssistantError(str(err)) from err

    async def queue_next(call: ServiceCall):
        await require_admin(call)
        try:return await c.queues.next(call.data.get('queue_id'),call.context)
        except (ValueError,TypeError) as err:raise HomeAssistantError(str(err)) from err

    async def queue_stop(call: ServiceCall):
        await require_admin(call)
        await c.queues.stop()

    hass.services.async_register(DOMAIN,'queue_start',queue_start,schema=vol.Schema({
        vol.Required('queue_id'):cv.string,vol.Optional('settings',default={}):dict,
        vol.Optional('if_idle',default=False):cv.boolean}),supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN,'queue_next',queue_next,schema=vol.Schema({vol.Optional('queue_id'):cv.string}),supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN,'queue_stop',queue_stop,schema=vol.Schema({}))
    hass.services.async_register(DOMAIN, "play", play, schema=vol.Schema({
        vol.Required("effect_id"): cv.string,
        vol.Optional("channel"): vol.In(["effect", "mood"]),
        vol.Optional("if_idle", default=False): cv.boolean,
        vol.Optional("lights"): cv.entity_ids,
        vol.Optional("output"): cv.string,
        vol.Optional("speakers"): cv.entity_ids,
        vol.Optional("volume"): vol.Coerce(float),
        vol.Optional("brightness"): vol.Coerce(float),
        vol.Optional("speed"): vol.Coerce(float),
        vol.Optional("offset_ms"): vol.Coerce(float),
        vol.Optional("routing"): cv.string,
        vol.Optional("repeat"): cv.boolean,
        vol.Optional("restore"): cv.boolean,
        vol.Optional("interval_ms"): vol.Coerce(float),
        vol.Optional("audio_mode"): vol.In(["auto","separate"]),
        vol.Optional("duck_mood"):vol.Coerce(float),
    }), supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, "stop", stop, schema=vol.Schema({vol.Optional("channel"): vol.In(["effect", "mood"])}))
    hass.services.async_register(DOMAIN, "set_automatic", automatic,
                                 schema=vol.Schema({vol.Required("enabled"): cv.boolean}))
    hass.services.async_register(DOMAIN, 'set_enabled', enabled,
                                 schema=vol.Schema({vol.Required('enabled'): cv.boolean}))
    platforms = ['sensor', 'switch', 'button', 'binary_sensor'] + (['light'] if entry.data.get('demo_lights') else [])
    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    c = entry.runtime_data
    await c.async_close()
    platforms = ['sensor', 'switch', 'button', 'binary_sensor'] + (['light'] if entry.data.get('demo_lights') else [])
    if not await hass.config_entries.async_unload_platforms(entry, platforms):
        return False
    frontend.async_remove_panel(hass, "boocue")
    remove_card_module(hass, hass.data[DOMAIN])
    for service in ["play", "stop", "set_automatic", 'set_enabled', "queue_start", "queue_next", "queue_stop"]:
        hass.services.async_remove(DOMAIN, service)
    hass.data[DOMAIN].pop("controller", None)
    return True
