"""Native HA adapter checks. Run inside the HA image; skip on plain Python."""

from types import SimpleNamespace
import unittest


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from homeassistant.core import State
            from custom_components.boocue.controller import expand_lights, light_command, validate_settings
            from custom_components.boocue.const import DEFAULT_SETTINGS
            from custom_components.boocue.models import Cue
        except ModuleNotFoundError as err:
            raise unittest.SkipTest("Run HA adapter checks inside the Home Assistant container") from err
        cls.State = State
        cls.Cue = Cue
        cls.expand = staticmethod(expand_lights)
        cls.command = staticmethod(light_command)
        cls.settings = staticmethod(validate_settings)
        cls.defaults = DEFAULT_SETTINGS

    def test_color_and_dimmer_and_onoff_have_correct_service_payloads(self):
        cue = self.Cue(0, 210, .6, .8, .5)
        for modes, expected in [(["hs"], {"brightness", "hs_color"}),
                                (["color_temp"], {"brightness"}),
                                (["onoff"], set())]:
            state = self.State("light.demo", "on", {"supported_color_modes":modes})
            action, data = self.command(state, cue, .5, 1)
            self.assertEqual(action, "turn_on")
            self.assertEqual(set(data), expected)
            if "brightness" in data:
                self.assertEqual(data["brightness"], 102)
        action, data = self.command(self.State("light.demo", "on", {}), self.Cue(0,0,0,0), 1, 1)
        self.assertEqual(action, "turn_off")
        self.assertEqual(data, {})

    def test_only_transition_capable_lamps_receive_transition(self):
        state = self.State("light.demo", "on", {"supported_features":32,"supported_color_modes":["hs"]})
        _, data = self.command(state, self.Cue(0,0,0,.5,1),1,2)
        self.assertEqual(data["transition"], .5)

    def test_group_expansion_deduplicates_and_handles_cycles(self):
        states = {
            "light.group":self.State("light.group","on",{"entity_id":["light.a","light.b","light.nested"]}),
            "light.nested":self.State("light.nested","on",{"entity_id":["light.group","light.a"]}),
            "light.a":self.State("light.a","off",{}),
            "light.b":self.State("light.b","unavailable",{}),
        }
        hass = SimpleNamespace(states=SimpleNamespace(get=states.get))
        self.assertEqual(self.expand(hass,["light.group","light.a"]),["light.a"])

    def test_settings_reject_invalid_ranges_and_entities(self):
        for raw in [{"volume":float("nan")},{"lights":["switch.outlet"]},
                    {"interval_ms":0},{"output":"https://untrusted.example/audio.mp3"},
                    {"restore":"false"}]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.settings(raw,self.defaults,set())
