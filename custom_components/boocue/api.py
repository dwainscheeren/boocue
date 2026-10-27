"""Authenticated local UI API and audio streaming."""

from datetime import timedelta
from pathlib import Path
import tempfile
import time

from aiohttp import web
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.http.auth import async_sign_path
from homeassistant.core import callback
from homeassistant.helpers import area_registry, device_registry, entity_registry

from .const import DOMAIN
from .library import MAX_BYTES, import_zip
from .controller import player_can_overlay


def get_controller(hass):
    controller = hass.data.get(DOMAIN, {}).get("controller")
    if not controller:
        raise ValueError("Voeg eerst de BooCue-integratie toe")
    return controller


def entities(hass):
    entity_reg = entity_registry.async_get(hass)
    device_reg = device_registry.async_get(hass)
    areas = area_registry.async_get(hass)
    result = {"lights": [], "players": [], "sensors": []}
    for state in hass.states.async_all():
        domain = state.domain
        if domain not in {"light", "media_player", "binary_sensor"}:
            continue
        entry = entity_reg.async_get(state.entity_id)
        if domain == 'binary_sensor' and entry and entry.platform == DOMAIN:
            continue  # BooCue's own activity state is not a motion input.
        device = device_reg.async_get(entry.device_id) if entry and entry.device_id else None
        area_id = (entry.area_id if entry else None) or (device.area_id if device else None)
        area = areas.async_get_area(area_id) if area_id else None
        modes = state.attributes.get("supported_color_modes") or []
        result[{"light": "lights", "media_player": "players", "binary_sensor": "sensors"}[domain]].append({
            "entity_id": state.entity_id,
            "name": state.name,
            "state": state.state,
            "area": area.name if area else "Overige lampen" if domain == "light" else "Overige",
            "color_modes": list(modes),
            "device_class": state.attributes.get("device_class"),
            "supported_features": state.attributes.get("supported_features", 0),
            "group_members": state.attributes.get("group_members", []),
            "overlay_capable": player_can_overlay(hass,state.entity_id) if domain=="media_player" else False,
        })
    for values in result.values():
        values.sort(key=lambda item: (item["area"], item["name"].casefold()))
    return result


@websocket_api.websocket_command({vol.Required("type"): "boocue/get"})
@websocket_api.require_admin
@callback
def ws_get(hass, connection, msg):
    try:
        c = get_controller(hass)
        connection.send_result(msg["id"], {
            "effects": [e.public() for e in c.effects.values()],
            "settings": c.settings, "status": c.status, "entities": entities(hass),
            "library_errors": c.library_errors, "server_time": time.time(),
        })
    except ValueError as err:
        connection.send_error(msg["id"], "not_ready", str(err))


@websocket_api.websocket_command({vol.Required('type'): 'boocue/dashboard'})
@websocket_api.require_admin
@callback
def ws_dashboard(hass, connection, msg):
    """Bounded card catalog: no complete timelines or home-wide entity inventory."""
    try:
        c = get_controller(hass)
        connection.send_result(msg['id'], {
            'effects': [e.public(compact=True) for e in c.effects.values()],
            'settings': {k: v for k, v in c.settings.items() if k != 'motion_rules'},
            'motion_rule_count': len(c.settings['motion_rules']),
            'status': c.status, 'server_time': time.time(),
        })
    except ValueError as err:
        connection.send_error(msg['id'], 'not_ready', str(err))


@websocket_api.websocket_command({
    vol.Required("type"): "boocue/settings", vol.Required("settings"): dict,
})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_settings(hass, connection, msg):
    try:
        settings = await get_controller(hass).async_save_settings(msg["settings"])
        connection.send_result(msg["id"], settings)
    except (ValueError, TypeError) as err:
        connection.send_error(msg["id"], "invalid_settings", str(err))


@websocket_api.websocket_command({
    vol.Required("type"): "boocue/play", vol.Required("effect_id"): str,
    vol.Optional("settings", default={}): dict,
    vol.Optional("channel", default="effect"): vol.In(["effect", "mood"]),
    vol.Optional("browser_id"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_play(hass, connection, msg):
    try:
        state = await get_controller(hass).async_play(
            msg["effect_id"], msg["settings"], connection.context(msg), channel=msg["channel"], browser_id=msg.get("browser_id"))
        connection.send_result(msg["id"], state)
    except (ValueError, TypeError) as err:
        connection.send_error(msg["id"], "play_failed", str(err))


@websocket_api.websocket_command({vol.Required("type"): "boocue/stop", vol.Optional("run_id"): str,
                                 vol.Optional("channel"): vol.In(["effect", "mood"])})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_stop(hass, connection, msg):
    await get_controller(hass).async_stop(msg.get("run_id"), channel=msg.get("channel"),
        disarm=not msg.get("channel") and not msg.get("run_id"))
    connection.send_result(msg["id"])


@websocket_api.websocket_command({
    vol.Required("type"): "boocue/audio", vol.Required("effect_id"): str,
})
@websocket_api.require_admin
@callback
def ws_audio(hass, connection, msg):
    try:
        effect = get_controller(hass).effects[msg["effect_id"]]
    except (ValueError, KeyError):
        connection.send_error(msg["id"], "not_found", "Dit effect bestaat niet")
        return
    path = async_sign_path(hass, f"/api/boocue/audio/{effect.id}", timedelta(minutes=35))
    connection.send_result(msg["id"], {"url": path})


@websocket_api.websocket_command({vol.Required('type'):'boocue/browser_ready'})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_browser_ready(hass,connection,msg):
    try:
        c=get_controller(hass)
        station_id=await c.async_register_browser(connection)
        @callback
        def closed():
            hass.async_create_task(c.async_release_browser(station_id,connection),'BooCue browser disconnected')
        connection.subscriptions[('boocue_browser',station_id)]=closed
        connection.send_result(msg['id'],{'station_id':station_id})
    except ValueError as err:connection.send_error(msg['id'],'browser_unavailable',str(err))


@websocket_api.websocket_command({vol.Required('type'):'boocue/browser_release',vol.Required('station_id'):str})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_browser_release(hass,connection,msg):
    await get_controller(hass).async_release_browser(msg['station_id'],connection)
    connection.subscriptions.pop(('boocue_browser',msg['station_id']),None)
    connection.send_result(msg['id'])


@websocket_api.websocket_command({vol.Required('type'):'boocue/queue',
    vol.Required('action'):vol.In(['start','next','stop']),vol.Optional('queue_id'):str,
    vol.Optional('settings',default={}):dict,vol.Optional('browser_id'):str,vol.Optional('run_id'):str})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_queue(hass,connection,msg):
    try:
        c=get_controller(hass)
        if msg['action']=='start':
            state=await c.queues.start(msg.get('queue_id'),msg['settings'],connection.context(msg),browser_id=msg.get('browser_id'))
        elif msg['action']=='next':state=await c.queues.next(msg.get('queue_id'),connection.context(msg))
        else:await c.queues.stop(msg.get('run_id'));state=c.queues.status
        connection.send_result(msg['id'],state)
    except (ValueError,TypeError) as err:connection.send_error(msg['id'],'queue_failed',str(err))


class AudioView(HomeAssistantView):
    url = "/api/boocue/audio/{effect_id}"
    name = "api:boocue:audio"
    requires_auth = True

    async def get(self, request, effect_id):
        try:
            effect = get_controller(request.app["hass"]).effects[effect_id]
        except (ValueError, KeyError):
            raise web.HTTPNotFound from None
        return web.FileResponse(effect.audio, headers={"Cache-Control": "private, max-age=3600"})


class ImportView(HomeAssistantView):
    url = "/api/boocue/import"
    name = "api:boocue:import"
    requires_auth = True

    async def post(self, request):
        if not request["hass_user"].is_admin:
            raise web.HTTPForbidden
        hass = request.app["hass"]
        c = get_controller(hass)
        if c.status["playing"]:
            return self.json_message("Stop eerst het actieve effect", 409)
        archive = None
        try:
            reader = await request.multipart()
            part = await reader.next()
            if part is None or part.name != "file":
                raise ValueError("Kies een BooCue-effectpakket (.zip)")
            # File writes run in the executor and every chunk is bounded.
            def new_upload():
                c.private.mkdir(parents=True, exist_ok=True)
                handle = tempfile.NamedTemporaryFile(prefix=".upload-", suffix=".zip", dir=c.private, delete=False)
                name = Path(handle.name)
                handle.close()
                return name
            archive = await hass.async_add_executor_job(new_upload)
            size = 0
            while chunk := await part.read_chunk(256 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError("Het pakket is groter dan 100 MB")
                await hass.async_add_executor_job(_append, archive, chunk)
            async with c._lock:
                if c.status["playing"]:
                    raise ValueError("Stop eerst het actieve effect")
                count = await hass.async_add_executor_job(import_zip, archive, c.private, set(c.effects))
                await c.async_reload_library()
            return self.json({"imported": count})
        except Exception as err:
            # aiohttp body errors and malformed ZIPs are user-facing, never tracebacks.
            return self.json_message(str(err)[:250], 400)
        finally:
            if archive:
                await hass.async_add_executor_job(archive.unlink, True)


def _append(path: Path, chunk: bytes):
    with path.open("ab") as handle:
        handle.write(chunk)


@callback
def async_register_api(hass):
    for command in [ws_get, ws_dashboard, ws_settings, ws_play, ws_stop, ws_audio, ws_browser_ready, ws_browser_release, ws_queue]:
        websocket_api.async_register_command(hass, command)
    hass.http.register_view(AudioView)
    hass.http.register_view(ImportView)
