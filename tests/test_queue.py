"""Queue cancellation, motion combinations and audio ownership in the HA runtime."""
import asyncio
from copy import deepcopy
import random
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_core import package
from boocue_test_core.sequence import QueueCursor
from test_playback import PlaybackFixture


class CursorTests(unittest.TestCase):
    def test_order_preserves_duplicate_rows_and_stops(self):
        cursor=QueueCursor(['a','b','a'])
        self.assertEqual([cursor.next()[1] for _ in range(3)],['a','b','a'])
        self.assertIsNone(cursor.next())

    def test_shuffle_plays_every_row_once_and_avoids_repeat_across_cycles(self):
        cursor=QueueCursor(['a','b','c'],'random',True,random.Random(5))
        rows=[cursor.next() for _ in range(30)]
        for offset in range(0,30,3):
            self.assertEqual({r[0] for r in rows[offset:offset+3]},{0,1,2})
        self.assertTrue(all(a[1]!=b[1] for a,b in zip(rows,rows[1:])))


class QueueTests(PlaybackFixture):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        fast=patch.object(self.module,'START_DELAY_SECONDS',.01)
        fast.start();self.addCleanup(fast.stop)

    async def until(self,predicate):
        async with asyncio.timeout(3):
            while not predicate():await asyncio.sleep(.005)

    def definition(self,**values):
        return {'id':'test','name':'Test queue','effects':['fx','fx2'],'mode':'sequence',
                'advance':'auto','repeat':False,'gap_min':0,'gap_max':0,'settings':{},**values}

    async def save_queue(self,**values):
        await self.c.async_save_settings({'queues':[self.definition(**values)]})

    def rule(self,**values):
        return {'id':'front','name':'Front door','sensors':['binary_sensor.one','binary_sensor.two'],
                'match':'any','action':'effect','effects':['fx'],'cooldown':0,'enabled':True,
                'output':'none','lights':['light.a'],**values}

    async def edge(self,sensor,old='off',new='on'):
        self.states[sensor]=self.State(sensor,new)
        self.c._motion_changed(SimpleNamespace(data={'old_state':self.State(sensor,old),'new_state':self.states[sensor]},context=self.Context()))
        await asyncio.gather(*self.c._motion_tasks)

    async def test_ordered_queue_finishes_and_restores_lights(self):
        await self.save_queue()
        seen=[]
        original=self.c.async_play
        async def play(eid,*args,**kwargs):
            seen.append(eid)
            return await original(eid,*args,**kwargs)
        with patch.object(self.c,'async_play',side_effect=play):
            await self.c.queues.start('test')
            await self.until(lambda:not self.c.queues.status['playing'])
        self.assertEqual(seen,['fx','fx2'])
        self.assertIsNone(self.c.queues.status['error'])
        self.assertEqual(self.states['light.a'].attributes['brightness'],160)

    async def test_motion_wait_next_and_stop_during_gap(self):
        await self.save_queue(advance='motion')
        await self.c.queues.start('test')
        await self.until(lambda:self.c.queues.status['waiting']=='motion')
        self.assertFalse(self.c.channels['effect']['playing'])
        await self.c.queues.next()
        await self.until(lambda:self.c.channels['effect']['effect_id']=='fx2')
        await self.c.async_stop()
        await self.save_queue(repeat=True,gap_min=60,gap_max=60)
        await self.c.queues.start('test')
        await self.until(lambda:self.c.queues.status['waiting']=='delay')
        step=self.c.queues.status['step']
        await self.c.async_stop(disarm=True)
        await asyncio.sleep(.05)
        self.assertFalse(self.c.queues.status['playing'])
        self.assertEqual(self.c.queues.status['step'],step)
        self.assertFalse(self.c.channels['effect']['playing'])

    async def test_next_interrupts_clip_and_manual_play_preempts_queue(self):
        await self.save_queue(gap_min=60,gap_max=60)
        await self.c.queues.start('test')
        await self.until(lambda:self.c.channels['effect']['playing'])
        await self.c.queues.next()
        await self.until(lambda:self.c.channels['effect']['effect_id']=='fx2')
        manual=await self.c.async_play('fx',{'repeat':True})
        self.assertFalse(self.c.queues.status['playing'])
        await asyncio.sleep(.05)
        self.assertEqual(self.c.channels['effect']['run_id'],manual['run_id'])

    async def test_stale_queue_stop_does_not_stop_replacement(self):
        await self.save_queue()
        first=await self.c.queues.start('test')
        second=await self.c.queues.start('test')
        await self.c.queues.stop(first['run_id'])
        self.assertEqual(self.c.queues.status['run_id'],second['run_id'])
        self.assertTrue(self.c.queues.status['playing'])

    async def test_queue_snapshots_routes_settings_and_action_precedence(self):
        await self.save_queue(settings={'volume':.25},advance='motion')
        self.c.settings['effect_routes']={'fx':{'output':'none','speakers':[],'volume':.7}}
        await self.c.queues.start('test',{'brightness':.5})
        self.assertEqual(self.c.queues.run.plans[0]['volume'],.7)
        self.assertEqual(self.c.queues.run.plans[1]['volume'],.25)
        self.assertEqual(self.c.queues.run.plans[1]['brightness'],.5)
        self.c.settings['volume']=.99
        self.assertEqual(self.c.queues.run.plans[1]['volume'],.25)

    async def test_invalid_queue_never_stops_running_effect(self):
        state=await self.c.async_play('fx',{'repeat':True})
        await self.save_queue(settings={'output':'browser'})
        with self.assertRaises(ValueError):await self.c.queues.start('test')
        self.assertEqual(self.c.channels['effect']['run_id'],state['run_id'])
        for values in [{'effects':[]},{'gap_min':5,'gap_max':4},{'effects':['missing']},{'mode':'bad'}]:
            with self.subTest(values=values),self.assertRaises(ValueError):await self.save_queue(**values)

    async def test_browser_release_stops_owned_queue_and_mood_only(self):
        owner=object();station=await self.c.async_register_browser(owner)
        await self.save_queue(settings={'output':'browser','lights':[]})
        await self.c.async_play('mood',{'output':'browser','lights':[]},channel='mood',browser_id=station)
        await self.c.queues.start('test',browser_id=station)
        await self.until(lambda:self.c.channels['effect']['playing'])
        await self.c.async_release_browser(station,object())
        self.assertTrue(self.c.channels['mood']['playing'])
        await self.c.async_release_browser(station,owner)
        self.assertIsNone(self.c.browser_id)
        self.assertFalse(self.c.queues.status['playing'])
        self.assertFalse(any(s['playing'] for s in self.c.channels.values()))

    async def test_multi_sensor_all_requires_both_active_and_any_accepts_either(self):
        await self.c.async_save_settings({'motion_rules':[self.rule(match='all')],'automatic_enabled':True})
        await self.edge('binary_sensor.one')
        self.assertFalse(self.c.channels['effect']['playing'])
        await self.edge('binary_sensor.two')
        self.assertTrue(self.c.channels['effect']['playing'])
        await self.c.async_stop(channel='effect')
        await self.c.async_save_settings({'motion_rules':[self.rule(match='any')]})
        await self.edge('binary_sensor.two')
        self.assertTrue(self.c.channels['effect']['playing'])

    async def test_legacy_sensor_migrates_and_unavailable_recovery_does_not_trigger(self):
        rule=self.rule();rule.pop('sensors');rule['sensor']='binary_sensor.one'
        await self.c.async_save_settings({'motion_rules':[rule],'automatic_enabled':True})
        self.assertEqual(self.c.settings['motion_rules'][0]['sensors'],['binary_sensor.one'])
        await self.edge('binary_sensor.one','unavailable','on')
        self.assertFalse(self.c.channels['effect']['playing'])

    async def test_motion_next_starts_inactive_queue_then_advances(self):
        await self.save_queue(advance='motion')
        await self.c.async_save_settings({'motion_rules':[self.rule(action='next_queue',queue_id='test')],'automatic_enabled':True})
        await self.edge('binary_sensor.one')
        await self.until(lambda:self.c.queues.status['waiting']=='motion')
        await self.edge('binary_sensor.two')
        await self.until(lambda:self.c.channels['effect']['effect_id']=='fx2')
        self.assertEqual(self.c._auto_events['front']['state'],'played')

    async def test_sonos_announcement_preserves_background_volume_and_stop(self):
        with patch.object(self.module,'player_can_overlay',return_value=True):
            mood=await self.c.async_play('mood',{'output':'speakers','speakers':['media_player.one'],'lights':[],'volume':.3},channel='mood')
            await self.until(lambda:'media_player.one' in self.played())
            await self.c.async_play('fx',{'output':'speakers','speakers':['media_player.one'],'lights':[],'volume':.8})
            await self.until(lambda:len(self.played())==2)
            announcement=[data for _,action,data in self.calls if action=='play_media'][-1]
            self.assertTrue(announcement['announce'])
            self.assertEqual(announcement['extra']['volume'],80)
            self.calls.clear()
            await self.c.async_stop(channel='effect')
            self.assertFalse(any(action=='media_stop' for _,action,_ in self.calls))
            self.assertEqual(self.states['media_player.one'].attributes['volume_level'],.3)
            self.assertEqual(self.c.channels['mood']['run_id'],mood['run_id'])
