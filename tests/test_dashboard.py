"""Compact Lovelace catalog, cache revisions and resource invalidation."""
import inspect
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import AsyncMock, patch
from test_core import Cue, Effect
from test_playback import PlaybackFixture


class CompactCatalogTests(unittest.TestCase):
    def test_compact_catalog_is_bounded_and_matches_the_panel_groups(self):
        cues=tuple(Cue(i, i, 1, .5) for i in range(100))
        effect=Effect('test','Test','Own sound','effects',100,Path('private.wav'),cues)
        compact=effect.public(compact=True)
        self.assertNotIn('cues',compact)
        self.assertNotIn('audio',compact)
        self.assertEqual(len(compact['cue_blocks']),18)
        self.assertEqual([c['at'] for c in compact['cue_blocks']],[cues[i*100//18].at for i in range(18)])
        self.assertEqual(compact['cue_blocks'][-1]['at'],94)
        self.assertEqual(len(effect.public()['cues']),100)


class DashboardTests(PlaybackFixture):
    async def test_native_url_manager_replaces_and_removes_only_our_module(self):
        import custom_components.boocue as integration
        from homeassistant.components import frontend
        changes=[]
        manager=frontend.UrlManager(lambda *args:changes.append(args),['/other-card.js'])
        hass=SimpleNamespace(data={frontend.DATA_EXTRA_MODULE_URL:manager})
        data={}
        integration.register_card_module(hass,data,'old')
        old=data['card_module_url']
        integration.register_card_module(hass,data,'new')
        self.assertNotIn(old,manager.urls)
        self.assertIn(data['card_module_url'],manager.urls)
        integration.remove_card_module(hass,data)
        integration.remove_card_module(hass,data)
        self.assertEqual(manager.urls,frozenset({'/other-card.js'}))

    async def test_dashboard_endpoint_omits_entity_inventory_and_motion_definitions(self):
        from custom_components.boocue import api
        self.hass.data={'boocue':{'controller':self.c}}
        self.c.settings['motion_rules']=[{'name':'Private sensor rule'}]
        results=[]
        connection=SimpleNamespace(send_result=lambda mid,result:results.append(result),send_error=lambda *args:self.fail(str(args)))
        inspect.unwrap(api.ws_dashboard)(self.hass,connection,{'id':1})
        result=results[0]
        self.assertNotIn('entities',result)
        self.assertNotIn('motion_rules',result['settings'])
        self.assertEqual(result['motion_rule_count'],1)
        self.assertEqual(len(result['effects']),3)
        self.assertTrue(all('cue_blocks' in effect and 'cues' not in effect for effect in result['effects']))
        self.assertIn('settings_revision',result['status'])
        self.assertIn('library_revision',result['status'])
        self.c.settings['motion_rules']=[]

    async def test_only_configuration_and_library_changes_advance_catalog_revisions(self):
        revision=self.c.status['settings_revision']
        await self.c.async_save_settings({'volume':.4})
        self.assertEqual(self.c.status['settings_revision'],revision+1)
        await self.c.async_save_settings({'volume':.4})
        self.assertEqual(self.c.status['settings_revision'],revision+1)
        await self.c.async_play('fx')
        self.assertEqual(self.c.status['settings_revision'],revision+1)
        previous=self.c.status['library_revision']
        self.hass.async_add_executor_job=AsyncMock(return_value=(self.c.effects,[]))
        await self.c.async_reload_library()
        self.assertEqual(self.c.status['library_revision'],previous+1)

    async def test_changing_card_source_invalidates_the_frontend_module_revision(self):
        import custom_components.boocue as integration
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);front=root/'frontend';front.mkdir()
            (front/'boocue-panel.js').write_text('panel')
            (front/'panel.css').write_text('styles')
            card=front/'boocue-card.js';card.write_text('old card')
            with patch.object(integration,'Path',return_value=root/'__init__.py'):
                before=integration.frontend_revision();card.write_text('new card')
                self.assertNotEqual(integration.frontend_revision(),before)
