"""Lifecycle and motion regression tests, executed in the native HA image."""
import asyncio
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import AsyncMock, patch


class PlaybackFixture(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        try:
            import custom_components.boocue.controller as module
            from custom_components.boocue.models import Effect, Cue
            from homeassistant.core import State, Context
            from homeassistant.exceptions import HomeAssistantError
            from homeassistant.components.media_player.const import MediaPlayerEntityFeature as MP
        except ModuleNotFoundError as err:
            raise unittest.SkipTest('Run playback checks in the Home Assistant image') from err
        self.module, self.State, self.Context, self.HAError = module, State, Context, HomeAssistantError
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.states={
            'light.a': State('light.a','on',{'brightness':160,'supported_color_modes':['hs'],'hs_color':[40,50]}),
            'light.b': State('light.b','off',{'supported_color_modes':['brightness']}),
        }
        features=int(MP.PLAY_MEDIA|MP.VOLUME_SET|MP.STOP)
        for p,volume in [('one',.2),('two',.4),('three',.6)]:
            self.states['media_player.'+p]=State('media_player.'+p,'idle',{'volume_level':volume,'supported_features':features})
        self.calls=[]
        self.fail_players=set()
        async def call(domain,action,data,**kwargs):
            self.calls.append((domain,action,deepcopy(data)))
            targets=data['entity_id'] if isinstance(data['entity_id'],list) else [data['entity_id']]
            for target in targets:
                old=self.states[target]
                if action=='play_media' and target in self.fail_players:raise HomeAssistantError('Device failed')
                attrs=dict(old.attributes)
                if domain=='light':
                    attrs.update({k:v for k,v in data.items() if k not in ['entity_id','transition']})
                    self.states[target]=State(target,'off' if action=='turn_off' else 'on',attrs)
                elif action=='volume_set':
                    attrs['volume_level']=data['volume_level'];self.states[target]=State(target,old.state,attrs)
        self.hass=SimpleNamespace(
            config=SimpleNamespace(path=lambda *p:str(Path(self.temp.name).joinpath(*p))),
            states=SimpleNamespace(get=self.states.get),
            services=SimpleNamespace(async_call=call),
            bus=SimpleNamespace(async_fire=lambda *a:None),
            async_create_task=lambda coro,name:asyncio.create_task(coro,name=name),
        )
        self.patches=[patch.object(module,'Store',return_value=SimpleNamespace(async_save=AsyncMock())),
            patch.object(module,'async_track_state_change_event',return_value=lambda:None),
            patch.object(module,'get_url',return_value='http://ha.test:8123'),
            patch.object(module,'async_sign_path',side_effect=lambda hass,path,expires:path+'?authSig=test')]
        for p in self.patches:p.start();self.addCleanup(p.stop)
        async def reproduce(hass,states,**kwargs):
            for state in states:self.states[state.entity_id]=state
        self.patches.append(patch.object(module,'async_reproduce_state',side_effect=reproduce))
        self.patches[-1].start();self.addCleanup(self.patches[-1].stop)
        self.c=module.BooCueController(self.hass)
        # Effect constructor's filesystem path is unused by these service tests.
        self.c.effects={
            'fx':Effect('fx','Effect','', 'effects',.35,Path('fx.wav'),[Cue(0,200,1,.9,0),Cue(.2,210,1,.7,0)],source='tests'),
            'fx2':Effect('fx2','Effect 2','', 'effects',.35,Path('fx2.wav'),[Cue(0,20,1,.8,0)],source='tests'),
            'mood':Effect('mood','Mood','', 'moods',.35,Path('mood.wav'),[Cue(0,80,1,.4,0),Cue(.2,90,1,.5,0)],source='tests'),
        }
        self.c.settings['output']='none'
        self.c.settings['lights']=['light.a']

    async def asyncTearDown(self):
        if hasattr(self,'c'):await self.c.async_close()

    async def wait_started(self):
        await asyncio.sleep(.92)

    def played(self):
        return [d['entity_id'] for domain,action,d in self.calls if action=='play_media']



class PlaybackTests(PlaybackFixture):
    async def test_two_channels_and_multiple_speakers_have_independent_stop_and_volume(self):
        await self.c.async_play('mood',{'lights':[],'output':'speakers','speakers':['media_player.one'],'volume':.3},channel='mood')
        await self.c.async_play('fx',{'lights':[],'output':'speakers','speakers':['media_player.two','media_player.three'],'volume':.8})
        await self.wait_started()
        self.assertCountEqual(self.played(),['media_player.one','media_player.two','media_player.three'])
        await self.c.async_stop(channel='effect')
        self.assertTrue(self.c.channels['mood']['playing'])
        self.assertFalse(self.c.channels['effect']['playing'])
        self.assertEqual(self.states['media_player.one'].attributes['volume_level'],.3)
        self.assertEqual(self.states['media_player.two'].attributes['volume_level'],.4)
        self.assertEqual(self.states['media_player.three'].attributes['volume_level'],.6)
        await self.c.async_stop(channel='mood')
        self.assertEqual(self.states['media_player.one'].attributes['volume_level'],.2)

    async def test_speaker_group_conflict_preserves_running_mood(self):
        s=self.states['media_player.one'];self.states[s.entity_id]=self.State(s.entity_id,s.state,{**s.attributes,'group_members':['media_player.one','media_player.two']})
        run=await self.c.async_play('mood',{'lights':[],'output':'speakers','speakers':['media_player.one']},channel='mood')
        with self.assertRaisesRegex(ValueError,'niet tegelijk mengen'):
            await self.c.async_play('fx',{'output':'speakers','speakers':['media_player.two']})
        self.assertEqual(self.c.channels['mood']['run_id'],run['run_id'])
        self.assertTrue(self.c.channels['mood']['playing'])

    async def test_shared_lights_resume_mood_then_restore_original(self):
        original=self.states['light.a']
        await self.c.async_play('mood',{'lights':['light.a'],'output':'none'},channel='mood')
        await self.wait_started()
        self.assertNotEqual(self.states['light.a'].attributes['brightness'],160)
        await self.c.async_play('fx',{'lights':['light.a'],'output':'none'})
        await self.wait_started()
        self.assertEqual(self.states['light.a'].attributes['hs_color'][0],200)
        await self.c.async_stop(channel='effect')
        self.assertIn(self.states['light.a'].attributes['hs_color'][0],[80,90])
        self.assertTrue(self.c.channels['mood']['playing'])
        await self.c.async_stop(channel='mood')
        self.assertEqual(self.states['light.a'].as_dict(),original.as_dict())

    async def test_stop_before_start_and_stale_run_id_do_not_stop_new_show(self):
        old=await self.c.async_play('fx',{'output':'speakers','speakers':['media_player.one']})
        new=await self.c.async_play('fx2',{'output':'speakers','speakers':['media_player.one']})
        await self.c.async_stop(old['run_id'],channel='effect')
        self.assertEqual(self.c.channels['effect']['run_id'],new['run_id'])
        self.assertTrue(self.c.channels['effect']['playing'])
        await self.c.async_stop(channel='effect')
        self.assertFalse(self.played())
        self.assertEqual(self.states['light.a'].attributes['brightness'],160)
        self.assertEqual(self.states['media_player.one'].attributes['volume_level'],.2)

    async def test_browser_audio_only_mood_waits_until_stopped(self):
        await self.c.async_play('mood',{'output':'browser','lights':[]},channel='mood',browser=True)
        await asyncio.sleep(.03)
        self.assertTrue(self.c.channels['mood']['playing'])
        await self.c.async_stop(channel='mood')
        self.assertFalse(self.c.channels['mood']['playing'])

    async def test_failed_speaker_does_not_silence_other_targets(self):
        self.fail_players.add('media_player.one')
        await self.c.async_play('fx',{'lights':[],'output':'speakers','speakers':['media_player.one','media_player.two']})
        await self.wait_started()
        self.assertIn('media_player.two',self.played())
        self.assertEqual(self.c.channels['effect']['warnings'],1)
        self.assertIsNone(self.c.channels['effect']['error'])

    async def test_transient_light_network_error_skips_a_cue_without_aborting_audio(self):
        from aiohttp import ServerDisconnectedError
        original_call = self.hass.services.async_call
        originals = {key: self.states[key] for key in ['light.a', 'light.b']}
        for error in [ServerDisconnectedError('Server disconnected'), TimeoutError()]:
            with self.subTest(error=type(error).__name__):
                attempts = []
                self.calls.clear()

                async def flaky(domain, action, data, **kwargs):
                    if domain == 'light':
                        attempts.append(deepcopy(data))
                        if len(attempts) == 1:
                            raise error
                    return await original_call(domain, action, data, **kwargs)

                self.hass.services.async_call = flaky
                with patch.object(self.module, 'START_DELAY_SECONDS', .01):
                    await self.c.async_play('fx', {'lights': ['light.a', 'light.b'],
                        'output': 'speakers', 'speakers': ['media_player.two'], 'interval_ms': 100})
                await self.c._runs['effect'].task
                state = self.c.channels['effect']
                self.assertIsNone(state['error'])
                self.assertEqual(state['position'], self.c.effects['fx'].duration)
                self.assertEqual(state['warnings'], 1)
                self.assertGreater(len(attempts), 2)
                self.assertTrue(any(data.get('hs_color', [0])[0] == 210 for data in attempts))
                self.assertEqual(self.played(), ['media_player.two'])
                self.assertEqual(self.states['media_player.two'].attributes['volume_level'], .4)
                for key, value in originals.items():
                    self.assertEqual(self.states[key], value)

    async def test_per_effect_route_and_legacy_output_migrate_without_losing_settings(self):
        settings=self.module.validate_settings({'output':'media_player.one','favorites':['fx']},self.c.settings,set(self.c.effects))
        self.assertEqual(settings['output'],'speakers');self.assertEqual(settings['speakers'],['media_player.one'])
        self.assertEqual(settings['favorites'],['fx'])
        self.c.settings['effect_routes']={'fx':{'output':'speakers','speakers':['media_player.two'],'volume':.7}}
        state=await self.c.async_play('fx')
        self.assertEqual(state['speakers'],['media_player.two'])
        self.assertEqual(self.c._runs['effect'].settings['volume'],.7)
        self.assertEqual(self.c.settings['output'],'none')

    async def test_stop_during_inflight_speaker_start_still_stops_the_player(self):
        entered=asyncio.Event()
        original=self.hass.services.async_call
        async def slow(domain,action,data,**kwargs):
            if action=='play_media':
                entered.set()
                await asyncio.Future()
            return await original(domain,action,data,**kwargs)
        self.hass.services.async_call=slow
        await self.c.async_play('fx',{'lights':[],'output':'speakers','speakers':['media_player.one']})
        await asyncio.wait_for(entered.wait(),2)
        await self.c.async_stop(channel='effect')
        self.assertTrue(any(action=='media_stop' for _,action,_ in self.calls))
        self.assertEqual(self.states['media_player.one'].attributes['volume_level'],.2)

    async def test_if_idle_is_atomic_for_simultaneous_automation_calls(self):
        results=await asyncio.gather(self.c.async_play('fx',if_idle=True),self.c.async_play('fx2',if_idle=True))
        self.assertEqual(sum(result is not None for result in results),1)
        self.assertEqual(self.c.channels['effect']['effect_id'],'fx')

    async def test_group_target_is_preferred_to_its_individual_member(self):
        s=self.states['media_player.one']
        self.states[s.entity_id]=self.State(s.entity_id,s.state,{**s.attributes,'group_members':['media_player.one','media_player.two']})
        state=await self.c.async_play('fx',{'output':'speakers','speakers':['media_player.two','media_player.one']})
        self.assertEqual(state['speakers'],['media_player.one'])

    async def test_audio_only_playback_reports_progress(self):
        await self.c.async_play('mood',{'lights':[],'output':'browser'},channel='mood',browser=True)
        await self.wait_started()
        self.assertGreater(self.c.channels['mood']['position'],0)
        self.assertTrue(self.c.channels['mood']['playing'])

    async def test_all_speakers_failing_report_a_useful_error_and_restore(self):
        self.fail_players.update(['media_player.one','media_player.two'])
        await self.c.async_play('fx',{'output':'speakers','speakers':['media_player.one','media_player.two']})
        with self.assertLogs(self.module.LOGGER,level='ERROR'):
            await self.wait_started()
        self.assertFalse(self.c.channels['effect']['playing'])
        self.assertIn('geen van de gekozen speakers',self.c.channels['effect']['error'])
        self.assertEqual(self.states['light.a'].attributes['brightness'],160)

    def rule(self):
        return {'id':'front','name':'Front door','sensor':'binary_sensor.motion','effects':['fx','fx2'],
                'cooldown':30,'mode':'sequence','enabled':True,'output':'none','lights':['light.a']}

    async def test_motion_cooldown_busy_gate_sequence_and_stop_all_disarm(self):
        await self.c.async_save_settings({'motion_rules':[self.rule()],'automatic_enabled':True})
        await self.c._trigger_motion('front',self.Context())
        self.assertEqual(self.c.channels['effect']['effect_id'],'fx')
        await self.c._trigger_motion('front',self.Context())
        self.assertEqual(self.c._auto_events['front']['state'],'cooldown')
        self.c._auto_last.clear()
        await self.c._trigger_motion('front',self.Context())
        self.assertEqual(self.c._auto_events['front']['state'],'busy')
        await self.c.async_stop(channel='effect')
        await self.c._trigger_motion('front',self.Context())
        self.assertEqual(self.c.channels['effect']['effect_id'],'fx2')
        await self.c.async_stop(disarm=True)
        await self.c._trigger_motion('front',self.Context())
        self.assertFalse(self.c.channels['effect']['playing'])
        self.assertFalse(self.c.settings['automatic_enabled'])

    async def test_motion_only_off_to_on_and_disabled_rules_never_trigger(self):
        await self.c.async_save_settings({'motion_rules':[self.rule()],'automatic_enabled':True})
        for old,new in [('unavailable','on'),('on','on'),('off','off')]:
            self.c._motion_changed(SimpleNamespace(data={'old_state':self.State('binary_sensor.motion',old),'new_state':self.State('binary_sensor.motion',new)},context=self.Context()))
        self.assertFalse(self.c._motion_tasks)
        self.c._motion_changed(SimpleNamespace(data={'old_state':self.State('binary_sensor.motion','off'),'new_state':self.State('binary_sensor.motion','on')},context=self.Context()))
        await asyncio.gather(*self.c._motion_tasks)
        self.assertTrue(self.c.channels['effect']['playing'])

    async def test_invalid_motion_browser_and_speaker_targets_are_rejected(self):
        for patch_values in [{'output':'speakers','speakers':[]},{'effects':[]},{'cooldown':-1}]:
            with self.subTest(patch_values=patch_values),self.assertRaises(ValueError):
                self.module.validate_settings({'motion_rules':[{**self.rule(),**patch_values}]},self.c.settings,set(self.c.effects))
        with self.assertRaisesRegex(ValueError,'sfeereffect'):
            await self.c.async_play('fx',{'output':'none'},channel='mood')
