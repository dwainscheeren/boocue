"""Scare-spot routing, parallel ownership, motion and cancellable loops."""
import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from test_playback import PlaybackFixture


class SpotTests(PlaybackFixture):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        fast = patch.object(self.module, 'START_DELAY_SECONDS', .01)
        fast.start(); self.addCleanup(fast.stop)
        self.definitions = [self.spot('clown', 'light.a', 'media_player.two'),
                            self.spot('witch', 'light.b', 'media_player.three')]
        await self.c.async_save_settings({'scare_spots': self.definitions, 'spot_concurrency': 'parallel'})

    def spot(self, sid, lamp, speaker):
        return {'id': sid, 'name': sid.capitalize(), 'enabled': True, 'effects': ['fx', 'fx2'],
                'mode': 'sequence', 'sensors': ['binary_sensor.' + sid], 'match': 'any', 'cooldown': 30,
                'settings': {'lights': [lamp], 'output': 'speakers', 'speakers': [speaker], 'volume': .7}}

    async def wait_for(self, predicate):
        async with asyncio.timeout(2):
            while not predicate(): await asyncio.sleep(.005)

    async def test_mood_and_two_spots_run_on_their_own_speakers_and_lights(self):
        await self.c.async_play('mood', {'output':'speakers','speakers':['media_player.one'],'lights':[]}, channel='mood')
        a = await self.c.spots.trigger('clown')
        b = await self.c.spots.trigger('witch')
        self.assertEqual(a['lights'], ['light.a']); self.assertEqual(a['speakers'], ['media_player.two'])
        self.assertEqual(b['lights'], ['light.b']); self.assertEqual(b['speakers'], ['media_player.three'])
        await self.wait_for(lambda:len(self.played()) == 3)
        self.assertCountEqual(self.played(), ['media_player.one','media_player.two','media_player.three'])
        await self.c.spots.stop_spot('clown')
        self.assertTrue(self.c.channels['spot:witch']['playing'])
        self.assertTrue(self.c.channels['mood']['playing'])

    async def test_single_mode_skips_another_spot_without_consuming_its_effect(self):
        await self.c.async_save_settings({'spot_concurrency':'single'})
        await self.c.spots.trigger('clown')
        self.assertIsNone(await self.c.spots.trigger('witch'))
        await self.c.spots.stop_spot('clown')
        state = await self.c.spots.trigger('witch')
        self.assertEqual(state['effect_id'], 'fx')

    async def test_same_lights_are_protected_even_in_parallel_mode(self):
        definitions = deepcopy(self.definitions)
        definitions[1]['settings']['lights'] = ['light.a']
        await self.c.async_save_settings({'scare_spots':definitions})
        first = await self.c.spots.trigger('clown')
        self.assertIsNone(await self.c.spots.trigger('witch'))
        self.assertEqual(self.c.channels['spot:clown']['run_id'], first['run_id'])

    async def test_overlapping_speaker_groups_are_protected(self):
        old=self.states['media_player.two']
        self.states[old.entity_id]=self.State(old.entity_id,old.state,{**old.attributes,'group_members':['media_player.two','media_player.three']})
        await self.c.spots.trigger('clown')
        self.assertIsNone(await self.c.spots.trigger('witch'))

    async def test_shared_mood_lamps_resume_then_restore_after_both_spots_stop(self):
        original = {k:self.states[k] for k in ['light.a','light.b']}
        await self.c.async_play('mood', {'lights':['light.a','light.b'],'output':'none'}, channel='mood')
        await self.c.spots.trigger('clown'); await self.c.spots.trigger('witch')
        await asyncio.sleep(.04)
        await self.c.spots.stop_spot('clown')
        self.assertTrue(self.c.channels['mood']['playing'])
        self.assertEqual(self.states['light.a'].attributes['hs_color'][0], 80)
        await self.c.spots.stop_spot('witch')
        await self.c.async_stop(channel='mood')
        self.assertEqual(self.states['light.a'], original['light.a'])
        self.assertEqual(self.states['light.b'], original['light.b'])

    async def test_motion_requires_arming_and_honors_each_spots_cooldown(self):
        self.assertIsNone(await self.c.spots.trigger('clown', source='motion'))
        await self.c.async_save_settings({'automatic_enabled':True})
        self.assertIsNotNone(await self.c.spots.trigger('clown', source='motion'))
        await self.c.spots.stop_spot('clown')
        self.assertIsNone(await self.c.spots.trigger('clown', source='motion'))
        self.assertEqual(self.c.spots.events['clown']['state'], 'cooldown')
        self.assertIsNotNone(await self.c.spots.trigger('witch', source='motion'))

    async def test_motion_event_all_match_and_unavailable_recovery(self):
        definitions=deepcopy(self.definitions)
        definitions[0].update(sensors=['binary_sensor.clown','binary_sensor.other'],match='all')
        await self.c.async_save_settings({'scare_spots':definitions,'automatic_enabled':True})
        off=self.State('binary_sensor.clown','off');on=self.State('binary_sensor.clown','on')
        self.states['binary_sensor.other']=self.State('binary_sensor.other','off')
        self.c._motion_changed(SimpleNamespace(data={'old_state':off,'new_state':on},context=self.Context()))
        await asyncio.sleep(.02)
        self.assertNotIn('spot:clown', self.c._runs)
        self.states['binary_sensor.other']=self.State('binary_sensor.other','on')
        unknown=self.State('binary_sensor.clown','unavailable')
        self.c._motion_changed(SimpleNamespace(data={'old_state':unknown,'new_state':on},context=self.Context()))
        self.assertNotIn('spot:clown', self.c._runs)
        self.c._motion_changed(SimpleNamespace(data={'old_state':off,'new_state':on},context=self.Context()))
        await self.wait_for(lambda:'spot:clown' in self.c._runs)

    async def test_loop_visits_selected_spots_and_stop_keeps_mood_running(self):
        await self.c.async_play('mood', {'lights':[],'output':'speakers','speakers':['media_player.one']}, channel='mood')
        await self.c.async_save_settings({'spot_show':{'spot_ids':['clown','witch'],'mode':'sequence','repeat':True,'gap_min':0,'gap_max':0}})
        await self.c.spots.start_show()
        await self.wait_for(lambda:self.c.spots.show_status['step'] >= 2 and self.c.spots.show_status['spot_id']=='witch')
        await self.c.spots.stop_show()
        self.assertFalse(self.c.spots.show_status['playing'])
        self.assertFalse(self.c.channels['spot:witch']['playing'])
        self.assertTrue(self.c.channels['mood']['playing'])
        count=len(self.played()); await asyncio.sleep(.05)
        self.assertEqual(len(self.played()), count)

    async def test_master_off_cancels_loop_and_all_spots_and_blocks_starts(self):
        await self.c.spots.start_show()
        await self.wait_for(lambda:bool(self.c._runs))
        await self.c.async_save_settings({'enabled':False})
        self.assertFalse(self.c.spots.show_status['playing'])
        self.assertFalse(any(s['playing'] for s in self.c.channels.values()))
        with self.assertRaisesRegex(ValueError, 'uit'):
            await self.c.spots.trigger('clown')

    async def test_stale_stop_does_not_stop_a_new_spot_run(self):
        first=await self.c.spots.trigger('clown')
        await self.c.spots.stop_spot('clown')
        second=await self.c.spots.trigger('clown')
        await self.c.spots.stop_spot('clown',first['run_id'])
        self.assertEqual(self.c.channels['spot:clown']['run_id'],second['run_id'])
        self.assertTrue(self.c.channels['spot:clown']['playing'])

    async def test_disabled_or_removed_spot_stops_and_metadata_is_bounded(self):
        await self.c.spots.trigger('clown')
        await self.c.async_save_settings({'scare_spots':[self.definitions[1]]})
        self.assertNotIn('spot:clown', self.c.channels)
        self.assertNotIn('clown',self.c.spots.events)
        with self.assertRaises(ValueError):await self.c.spots.trigger('clown')

    async def test_invalid_spot_settings_do_not_erase_existing_configuration(self):
        for change in [{'effects':[]},{'settings':{'output':'browser'}},{'sensors':['light.a']},{'mode':'bad'}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                await self.c.async_save_settings({'scare_spots':[{**self.definitions[0],**change}]})
            self.assertEqual(len(self.c.settings['scare_spots']),2)

    async def test_pending_spot_start_cannot_pass_a_later_stop(self):
        for stop in ['spot', 'all', 'global']:
            with self.subTest(stop=stop):
                await self.c._lock.acquire()
                pending=asyncio.create_task(self.c.spots.trigger('clown'))
                await asyncio.sleep(.01)
                if stop=='spot':stopping=asyncio.create_task(self.c.spots.stop_spot('clown'))
                elif stop=='all':stopping=asyncio.create_task(self.c.spots.stop_all())
                else:stopping=asyncio.create_task(self.c.async_stop())
                await asyncio.sleep(.01)
                self.c._lock.release()
                self.assertIsNone(await pending)
                await stopping
                self.assertFalse(self.c.channels.get('spot:clown',{}).get('playing',False))

    async def test_disabled_spot_is_not_started_by_an_explicit_loop_subset(self):
        definitions=deepcopy(self.definitions);definitions[0]['enabled']=False
        await self.c.async_save_settings({'scare_spots':definitions,'spot_show':{'spot_ids':['clown','witch'],'mode':'sequence','repeat':False,'gap_min':0,'gap_max':0}})
        await self.c.spots.start_show()
        await self.wait_for(lambda:'spot:witch' in self.c._runs)
        self.assertNotIn('spot:clown',self.c._runs)

    async def test_integration_unload_removes_every_spot_action(self):
        import custom_components.boocue as integration
        from unittest.mock import AsyncMock
        removed=[]
        self.hass.config_entries=SimpleNamespace(async_unload_platforms=AsyncMock(return_value=True))
        self.hass.services.async_remove=lambda domain,service:removed.append(service)
        self.hass.data={'boocue':{'controller':self.c}}
        entry=SimpleNamespace(runtime_data=self.c,entry_id='test',data={})
        with patch.object(integration.frontend,'async_remove_panel'):
            self.assertTrue(await integration.async_unload_entry(self.hass,entry))
        self.assertTrue({'spot_play','spot_stop','spot_show_start','spot_show_stop'} <= set(removed))
