"""Editorial metadata and the actual routed light-command preview."""
import asyncio
import unittest
from unittest.mock import patch

from test_core import package
from boocue_test_core.presentation import PRESENTATIONS, LEGACY_DESCRIPTION, presentation_for
from test_playback import PlaybackFixture


class PresentationTests(unittest.TestCase):
    def test_complete_known_catalog_has_descriptions_and_semantic_icons(self):
        expected={f'hh-fx{i}' for i in range(1,49)}|{f'hh-mood{i*100}' for i in range(1,13)}
        self.assertTrue(expected<=PRESENTATIONS.keys())
        self.assertEqual(len(PRESENTATIONS),68)
        for eid,(title,icon,english,dutch) in PRESENTATIONS.items():
            result=presentation_for(eid,title,LEGACY_DESCRIPTION,'mdi:ghost')
            self.assertEqual(result['descriptions'],{'en':english,'nl':dutch})
            self.assertNotIn('Imported',result['description'])
            self.assertTrue(result['icon'].startswith('mdi:'))
        self.assertGreater(len({p[1] for p in PRESENTATIONS.values()}),40)

    def test_custom_metadata_and_coincident_ids_are_preserved(self):
        self.assertEqual(presentation_for('hh-fx1','Thunder','My recording','mdi:music-note'),
                         {'description':'My recording','icon':'mdi:music-note'})
        self.assertEqual(presentation_for('hh-fx1','Different sound','My sound','mdi:bell'),
                         {'description':'My sound','icon':'mdi:bell'})


class LightPreviewTests(PlaybackFixture):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        fast=patch.object(self.module,'START_DELAY_SECONDS',.01)
        fast.start();self.addCleanup(fast.stop)

    async def until(self,predicate):
        async with asyncio.timeout(2):
            while not predicate():await asyncio.sleep(.005)

    async def test_alternating_colors_follow_individual_last_commands_and_capabilities(self):
        await self.c.async_play('fx',{'lights':['light.a','light.b'],'routing':'alternate','brightness':1})
        await self.until(lambda:len(self.c._runs['effect'].desired)==2)
        samples={p['id']:p for p in self.c.status['channels']['effect']['light_preview']}
        self.assertEqual(samples['light.a']['hue'],200)
        self.assertEqual(samples['light.a']['saturation'],1)
        self.assertEqual(samples['light.b']['saturation'],0)
        self.assertAlmostEqual(samples['light.b']['brightness'],round(.7*255)/255)
        self.assertTrue(all(p['active'] for p in samples.values()))

    async def test_foreground_marks_shared_mood_lights_as_overridden_then_resumes(self):
        await self.c.async_play('mood',{'lights':['light.a'],'output':'none'},channel='mood')
        await self.until(lambda:bool(self.c.status['channels']['mood']['light_preview']))
        await self.c.async_play('fx',{'lights':['light.a'],'output':'none'})
        self.assertFalse(self.c.status['channels']['mood']['light_preview'][0]['active'])
        await self.c.async_stop(channel='effect')
        self.assertTrue(self.c.status['channels']['mood']['light_preview'][0]['active'])

    async def test_sound_only_exposes_timeline_preview_without_light_commands(self):
        await self.c.async_play('fx',{'lights':[],'output':'browser','brightness':.5},browser=True)
        await self.until(lambda:bool(self.c.status['channels']['effect']['light_preview']))
        state=self.c.status['channels']['effect']
        self.assertEqual(state['preview_kind'],'timeline')
        self.assertAlmostEqual(state['light_preview'][0]['brightness'],.45)
        self.assertFalse(any(domain=='light' for domain,_,_ in self.calls))
