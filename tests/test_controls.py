"""Master control, automation entities, restart migration and concurrent starts."""
import asyncio
from copy import deepcopy
import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from test_playback import PlaybackFixture


class ControlTests(PlaybackFixture):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        fast=patch.object(self.module,'START_DELAY_SECONDS',.01)
        fast.start();self.addCleanup(fast.stop)

    async def until(self,predicate):
        async with asyncio.timeout(3):
            while not predicate():await asyncio.sleep(.005)

    async def queue(self,advance='auto'):
        await self.c.async_save_settings({'queues':[{'id':'show','name':'Show','effects':['fx','fx2'],
            'mode':'sequence','advance':advance,'repeat':True,'gap_min':60,'gap_max':60,'settings':{}}]})

    def rule(self):
        return {'id':'motion','name':'Motion','sensor':'binary_sensor.motion','effects':['fx'],
                'enabled':True,'cooldown':0,'output':'none','lights':['light.a']}

    async def test_off_stops_both_channels_restores_lights_and_blocks_all_starts(self):
        original=deepcopy(self.states)
        await self.c.async_save_settings({'motion_rules':[self.rule()],'automatic_enabled':True})
        await self.c.async_play('mood',{'output':'none','lights':['light.a']},channel='mood')
        await self.c.async_play('fx')
        await asyncio.sleep(.03)
        await self.c.async_save_settings({'enabled':False})
        self.assertFalse(any(s['playing'] for s in self.c.channels.values()))
        self.assertTrue(self.c.settings['automatic_enabled'])
        self.assertFalse(self.c.rule_is_armed('motion'))
        self.assertEqual(self.states['light.a'].as_dict(),original['light.a'].as_dict())
        for channel,eid in [('effect','fx'),('mood','mood')]:
            with self.assertRaisesRegex(ValueError,'BooCue staat uit'):
                await self.c.async_play(eid,channel=channel)
        await self.c._trigger_motion('motion',self.Context())
        self.assertFalse(self.c.channels['effect']['playing'])

    async def test_off_cancels_waiting_queue_and_on_does_not_resume_it(self):
        await self.queue()
        await self.c.queues.start('show')
        await self.until(lambda:self.c.queues.status['waiting']=='delay')
        await self.c.async_save_settings({'enabled':False})
        self.assertFalse(self.c.queues.status['playing'])
        for action in [lambda:self.c.queues.start('show'),lambda:self.c.queues.next('show')]:
            with self.assertRaises(ValueError):await action()
        await self.c.async_save_settings({'enabled':True})
        self.assertFalse(self.c.status['playing'])
        await asyncio.sleep(.03)
        self.assertFalse(self.c.status['playing'])
        self.assertIsNotNone(await self.c.async_play('fx'))

    async def test_concurrent_on_waits_until_off_cleanup_has_finished(self):
        entered,release=asyncio.Event(),asyncio.Event()
        stop=self.c.async_stop
        async def slow_stop(*a,**kw):
            entered.set();await release.wait();return await stop(*a,**kw)
        with patch.object(self.c,'async_stop',side_effect=slow_stop):
            off=asyncio.create_task(self.c.async_save_settings({'enabled':False}))
            await entered.wait()
            on=asyncio.create_task(self.c.async_save_settings({'enabled':True}))
            await asyncio.sleep(.01)
            self.assertFalse(on.done());self.assertFalse(self.c.settings['enabled'])
            release.set();await asyncio.wait_for(asyncio.gather(off,on),2)
        self.assertTrue(self.c.settings['enabled'])
        state=await self.c.async_play('fx');await asyncio.sleep(.03)
        self.assertEqual(self.c.channels['effect']['run_id'],state['run_id'])
        self.assertTrue(self.c.channels['effect']['playing'])

    async def test_disable_while_old_playback_cleanup_awaits_cannot_start_a_new_run(self):
        entered,release=asyncio.Event(),asyncio.Event()
        async def slow_stop(channel):entered.set();await release.wait()
        with patch.object(self.c,'_stop_locked',side_effect=slow_stop):
            play=asyncio.create_task(self.c.async_play('fx'))
            await entered.wait()
            off=asyncio.create_task(self.c.async_save_settings({'enabled':False}))
            await self.until(lambda:not self.c.settings['enabled'])
            release.set()
            with self.assertRaisesRegex(ValueError,'BooCue staat uit'):await play
            await asyncio.wait_for(off,2)
        self.assertFalse(self.c.status['playing']);self.assertFalse(self.calls)

    async def test_disabled_flag_survives_bad_unrelated_stored_preferences(self):
        raw={**deepcopy(self.c.settings),'enabled':False,'volume':10}
        self.c.store.async_load=AsyncMock(return_value=raw)
        with patch.object(self.c,'async_reload_library',new=AsyncMock()),self.assertLogs(self.module.LOGGER,level='WARNING'):
            await self.c.async_load()
        self.assertFalse(self.c.settings['enabled'])
        with self.assertRaises(ValueError):await self.c.async_play('fx')

    async def test_legacy_settings_default_on_but_partial_saves_preserve_off(self):
        legacy=deepcopy(self.c.settings);legacy.pop('enabled')
        checked=self.module.validate_settings(legacy,{},set(self.c.effects))
        self.assertTrue(checked['enabled'])
        await self.c.async_save_settings({'enabled':False})
        await self.c.async_save_settings({'volume':.4})
        self.assertFalse(self.c.settings['enabled'])
        with self.assertRaises(ValueError):await self.c.async_save_settings({'enabled':'off'})

    async def test_native_switches_buttons_and_active_condition(self):
        from custom_components.boocue.switch import BooCueEnabled,BooCueAutomatic
        from custom_components.boocue.button import BooCueButton
        from custom_components.boocue.binary_sensor import BooCueActive
        power=BooCueEnabled(self.c,'entry');automatic=BooCueAutomatic(self.c,'entry');active=BooCueActive(self.c,'entry')
        self.assertEqual(automatic.unique_id,'entry_automatic')
        self.assertEqual(power.unique_id,'entry_enabled')
        self.assertTrue(power.is_on);self.assertFalse(active.is_on)
        await automatic.async_turn_on();self.assertTrue(automatic.extra_state_attributes['effective'])
        await self.queue('motion');await self.c.queues.start('show')
        await self.until(lambda:self.c.queues.status['waiting']=='motion')
        self.assertTrue(active.is_on)
        next_button=BooCueButton(self.c,'entry','next_queue');self.assertTrue(next_button.available)
        await next_button.async_press();await self.until(lambda:self.c.channels['effect']['effect_id']=='fx2')
        await power.async_turn_off()
        self.assertFalse(active.is_on);self.assertFalse(next_button.available)
        self.assertTrue(automatic.is_on);self.assertFalse(automatic.extra_state_attributes['effective'])
        await power.async_turn_on();self.assertFalse(active.is_on)
        stop_sequence=self.c.status['stop_sequence']
        await BooCueButton(self.c,'entry','stop_all').async_press()
        self.assertFalse(automatic.is_on)
        self.assertEqual(self.c.status['stop_sequence'],stop_sequence+1)
        self.assertTrue(power.is_on)

    async def test_status_sensor_throttles_progress_but_publishes_state_and_errors_immediately(self):
        from custom_components.boocue.sensor import BooCuePlaybackSensor
        sensor=BooCuePlaybackSensor(self.c,'entry','effect');sensor.async_write_ha_state=Mock()
        with patch('custom_components.boocue.sensor.time',SimpleNamespace(monotonic=Mock(side_effect=[1,1.1,1.2,2.2]))):
            sensor._updated(None)
            self.c.channels['effect']['position']=.1;sensor._updated(None)
            self.assertEqual(sensor.async_write_ha_state.call_count,1)
            self.c.channels['effect']['error']='Device error';sensor._updated(None)
            self.assertEqual(sensor.async_write_ha_state.call_count,2)
            sensor._updated(None);self.assertEqual(sensor.async_write_ha_state.call_count,3)
        self.assertIn('channels',sensor._unrecorded_attributes)

    async def test_ws_play_cannot_bypass_browser_station_readiness(self):
        from custom_components.boocue import api
        self.hass.data={'boocue':{'controller':self.c}}
        errors=[];results=[]
        conn=SimpleNamespace(context=lambda msg:self.Context(),send_error=lambda *a:errors.append(a),send_result=lambda *a:results.append(a))
        command=inspect.unwrap(api.ws_play)
        await command(self.hass,conn,{'id':1,'effect_id':'fx','channel':'effect','settings':{'output':'browser','lights':[]}})
        self.assertTrue(errors);self.assertFalse(results);self.assertFalse(self.c.status['playing'])
