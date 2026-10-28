"""Area metadata for device filters; no integrations or devices are started."""
from types import SimpleNamespace
from unittest.mock import patch
import unittest


class PickerAreaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from homeassistant.core import State
            from custom_components.boocue import api
        except ModuleNotFoundError as err:
            raise unittest.SkipTest('Run area metadata checks in the HA image') from err
        cls.State=State
        cls.api=api

    def test_entity_area_overrides_device_area_and_unassigned_is_explicit(self):
        entries={
            'light.front':SimpleNamespace(area_id='garden',device_id='device'),
            'media_player.hall':SimpleNamespace(area_id=None,device_id='device'),
        }
        areas={'garden':SimpleNamespace(id='garden',name='Garden'),
               'hall':SimpleNamespace(id='hall',name='Hall')}
        states=[self.State('light.front','on',{'friendly_name':'Front light'}),
                self.State('media_player.hall','idle',{'friendly_name':'Hall speaker'}),
                self.State('light.unassigned','off',{})]
        hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda:states))
        with patch.object(self.api.entity_registry,'async_get',return_value=SimpleNamespace(async_get=entries.get)), \
             patch.object(self.api.device_registry,'async_get',return_value=SimpleNamespace(async_get=lambda key:SimpleNamespace(area_id='hall'))), \
             patch.object(self.api.area_registry,'async_get',return_value=SimpleNamespace(async_get_area=areas.get)), \
             patch.object(self.api,'player_can_overlay',return_value=False):
            result=self.api.entities(hass)
        lights={item['entity_id']:item for item in result['lights']}
        self.assertEqual((lights['light.front']['area_id'],lights['light.front']['area']),('garden','Garden'))
        self.assertEqual(result['players'][0]['area_id'],'hall')
        self.assertEqual(lights['light.unassigned']['area_id'],'')


if __name__=='__main__':
    unittest.main()
