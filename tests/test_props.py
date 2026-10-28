"""Physical-output lifecycle checks using fake HA switches and buttons only."""
import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from test_playback import PlaybackFixture


class PropTests(PlaybackFixture):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        from custom_components.boocue import props
        self.props_module = props
        for name, state in [('relay', 'off'), ('other', 'off'), ('already_on', 'on')]:
            self.states['switch.' + name] = self.State('switch.' + name, state)
        self.states['switch.group'] = self.State('switch.group', 'off', {'entity_id': ['switch.relay', 'switch.already_on']})
        self.states['button.clown'] = self.State('button.clown', 'unknown')
        self.store = SimpleNamespace(async_load=AsyncMock(return_value=None), async_save=AsyncMock())
        self.c.props.store = self.store
        registry = SimpleNamespace(async_get=lambda eid: SimpleNamespace(platform='boocue' if eid.startswith('switch.boocue') else 'esphome'))
        patches = [patch.object(self.module, 'START_DELAY_SECONDS', .02),
                   patch.object(props.entity_registry, 'async_get', return_value=registry)]
        for item in patches:
            item.start(); self.addCleanup(item.stop)
        self.fail_off = False
        original = self.hass.services.async_call

        async def call(domain, action, data, **kwargs):
            if domain not in {'switch', 'button'}:
                return await original(domain, action, data, **kwargs)
            self.calls.append((domain, action, deepcopy(data)))
            if action == 'turn_off' and self.fail_off:
                raise self.HAError('Disconnected relay')
            entity_id = data['entity_id']
            self.states[entity_id] = self.State(entity_id, 'on' if action == 'turn_on' else 'off' if action == 'turn_off' else 'pressed')
        self.hass.services.async_call = call
        self.definitions = [self.spot('clown', 'light.a'), self.spot('witch', 'light.b')]
        await self.configure([{'entity_id': 'switch.relay', 'duration': .1}, {'entity_id': 'button.clown', 'delay': .05}])

    def spot(self, sid, lamp):
        return {'id': sid, 'name': sid, 'enabled': True, 'effects': ['fx'], 'mode': 'sequence',
                'settings': {'lights': [lamp], 'output': 'none'}, 'sensors': [], 'props': []}

    async def configure(self, actions):
        self.definitions[0]['props'] = actions
        await self.c.async_save_settings({'scare_spots': self.definitions, 'spot_concurrency': 'parallel'})

    async def wait_for(self, predicate):
        async with asyncio.timeout(2):
            while not predicate():
                await asyncio.sleep(.005)

    def actions(self, entity_id):
        return [action for domain, action, data in self.calls if domain in {'switch', 'button'} and data['entity_id'] == entity_id]

    async def test_pulse_and_initial_unknown_button_run_once_and_finish_without_audio(self):
        self.definitions[0]['settings']['lights'] = []
        await self.configure(self.definitions[0]['props'])
        await self.c.spots.trigger('clown')
        await self.wait_for(lambda: not self.c.channels['spot:clown']['playing'])
        self.assertEqual(self.actions('switch.relay'), ['turn_on', 'turn_off'])
        self.assertEqual(self.actions('button.clown'), ['press'])
        self.assertEqual(self.c.props.pending, set())
        self.store.async_save.assert_any_await({'switches': ['switch.relay']})
        self.store.async_save.assert_any_await({'switches': []})

    async def test_stop_before_audio_start_cancels_every_planned_action(self):
        await self.c.spots.trigger('clown')
        await self.c.spots.stop_spot('clown')
        await asyncio.sleep(.12)
        self.assertEqual(self.actions('switch.relay'), [])
        self.assertEqual(self.actions('button.clown'), [])

    async def test_master_off_turns_owned_relay_off_and_cancels_later_button(self):
        await self.configure([{'entity_id': 'switch.relay', 'duration': 120}, {'entity_id': 'button.clown', 'delay': .25}])
        await self.c.spots.trigger('clown')
        await self.wait_for(lambda: self.states['switch.relay'].state == 'on')
        await self.c.async_save_settings({'enabled': False})
        await asyncio.sleep(.3)
        self.assertEqual(self.actions('switch.relay'), ['turn_on', 'turn_off'])
        self.assertEqual(self.actions('button.clown'), [])
        self.assertFalse(self.c.status['playing'])

    async def test_duration_cannot_keep_relay_on_after_the_effect_ends(self):
        await self.configure([{'entity_id': 'switch.relay', 'duration': 120}])
        await self.c.spots.trigger('clown')
        await self.wait_for(lambda: not self.c.channels['spot:clown']['playing'])
        self.assertEqual(self.states['switch.relay'].state, 'off')
        self.assertEqual(self.actions('switch.relay'), ['turn_on', 'turn_off'])

    async def test_existing_on_switch_is_untouched_and_group_leaves_are_owned_separately(self):
        await self.configure([{'entity_id': 'switch.group', 'duration': .1}])
        await self.c.spots.trigger('clown')
        await self.wait_for(lambda: not self.c.channels['spot:clown']['playing'])
        self.assertEqual(self.actions('switch.group'), [])
        self.assertEqual(self.actions('switch.already_on'), [])
        self.assertEqual(self.states['switch.already_on'].state, 'on')
        self.assertEqual(self.actions('switch.relay'), ['turn_on', 'turn_off'])

    async def test_shared_group_member_or_button_blocks_parallel_spot(self):
        for first, second in [([{'entity_id': 'switch.group'}], [{'entity_id': 'switch.relay'}]),
                              ([{'entity_id': 'button.clown'}], [{'entity_id': 'button.clown'}])]:
            with self.subTest(first=first):
                self.definitions[1]['props'] = second
                await self.configure(first)
                active = await self.c.spots.trigger('clown')
                self.assertIsNone(await self.c.spots.trigger('witch'))
                self.assertEqual(self.c.channels['spot:clown']['run_id'], active['run_id'])
                await self.c.spots.stop_spot('clown')

    async def test_pending_cleanup_survives_failure_blocks_reuse_and_retries_on_stop_all(self):
        await self.configure([{'entity_id': 'switch.relay', 'duration': 120}])
        await self.c.spots.trigger('clown')
        await self.wait_for(lambda: self.states['switch.relay'].state == 'on')
        self.fail_off = True
        with self.assertLogs(self.props_module.LOGGER, level='WARNING'):
            await self.c.spots.stop_spot('clown')
        self.assertEqual(self.c.status['prop_cleanup_pending'], ['switch.relay'])
        with self.assertRaisesRegex(ValueError, 'uitschakelen'):
            await self.c.spots.trigger('clown')
        self.fail_off = False
        await self.c.async_stop()
        self.assertEqual(self.states['switch.relay'].state, 'off')
        self.assertEqual(self.c.props.pending, set())

    async def test_restart_recovers_only_persisted_owned_switches(self):
        self.store.async_load.return_value = {'switches': ['switch.relay']}
        self.states['switch.relay'] = self.State('switch.relay', 'on')
        await self.c.props.load()
        self.assertEqual(self.actions('switch.relay'), ['turn_off'])
        self.assertEqual(self.actions('switch.already_on'), [])
        self.assertEqual(self.c.props.pending, set())

    async def test_stop_waits_for_inflight_on_before_sending_off(self):
        entered, release = asyncio.Event(), asyncio.Event()
        original = self.hass.services.async_call

        async def slow(domain, action, data, **kwargs):
            if domain == 'switch' and action == 'turn_on':
                entered.set(); await release.wait()
            return await original(domain, action, data, **kwargs)
        self.hass.services.async_call = slow
        await self.c.spots.trigger('clown')
        await asyncio.wait_for(entered.wait(), 1)
        stopping = asyncio.create_task(self.c.spots.stop_spot('clown'))
        await asyncio.sleep(.02)
        self.assertFalse(stopping.done())
        release.set(); await stopping
        self.assertEqual(self.actions('switch.relay'), ['turn_on', 'turn_off'])
        self.assertEqual(self.states['switch.relay'].state, 'off')

    async def test_partial_turn_on_failure_is_cleaned_up_without_waiting_for_clip_end(self):
        original = self.hass.services.async_call

        async def partial(domain, action, data, **kwargs):
            await original(domain, action, data, **kwargs)
            if domain == 'switch' and action == 'turn_on':
                raise self.HAError('No acknowledgement after relay switched')
        self.hass.services.async_call = partial
        await self.c.spots.trigger('clown')
        await self.wait_for(lambda: 'turn_off' in self.actions('switch.relay'))
        self.assertEqual(self.states['switch.relay'].state, 'off')
        self.assertTrue(self.c.channels['spot:clown']['playing'])
        self.assertTrue(self.c.channels['spot:clown']['warnings'])

    async def test_a_stalled_service_has_a_bounded_timeout_and_stop_can_finish(self):
        original = self.hass.services.async_call

        async def stalled(domain, action, data, **kwargs):
            if domain == 'switch' and action == 'turn_on':
                await asyncio.sleep(10)
            return await original(domain, action, data, **kwargs)
        self.hass.services.async_call = stalled
        with patch.object(self.props_module, 'SERVICE_TIMEOUT', .03):
            await self.c.spots.trigger('clown')
            await self.wait_for(lambda: 'turn_off' in self.actions('switch.relay'))
            await asyncio.wait_for(self.c.async_stop(), .5)
        self.assertEqual(self.states['switch.relay'].state, 'off')
        self.assertEqual(self.c.props.pending, set())

    async def test_slow_storage_cannot_dispatch_a_late_on_after_the_clip_has_ended(self):
        async def slow_save(data):
            if data['switches']:
                await asyncio.sleep(.45)
        self.store.async_save.side_effect = slow_save
        await self.configure([{'entity_id': 'switch.relay'}])
        await self.c.spots.trigger('clown')
        await self.wait_for(lambda: not self.c.channels['spot:clown']['playing'])
        self.assertNotIn('turn_on', self.actions('switch.relay'))
        self.assertEqual(self.states['switch.relay'].state, 'off')

    async def test_action_after_short_clip_is_skipped_and_disabled_spot_cancels_pending_actions(self):
        await self.configure([{'entity_id': 'button.clown', 'delay': 2}])
        await self.c.spots.trigger('clown')
        await self.wait_for(lambda: not self.c.channels['spot:clown']['playing'])
        self.assertEqual(self.actions('button.clown'), [])
        self.assertTrue(self.c.channels['spot:clown']['notes'])
        await self.configure([{'entity_id': 'button.clown', 'delay': .2}])
        await self.c.spots.trigger('clown')
        self.definitions[0]['enabled'] = False
        await self.c.async_save_settings({'scare_spots': self.definitions})
        await asyncio.sleep(.3)
        self.assertEqual(self.actions('button.clown'), [])

    async def test_invalid_actions_do_not_replace_saved_configuration(self):
        for actions in [[{'entity_id': 'script.anything'}], [{'entity_id': 'button.clown', 'duration': 1}],
                        [{'entity_id': 'switch.relay', 'duration': 0}], [{'entity_id': 'switch.relay', 'duration': 121}],
                        [{'entity_id': 'switch.relay', 'delay': float('nan')}], [{'entity_id': 'switch.relay', 'delay': True}],
                        [{'entity_id': 'button.clown'}, {'entity_id': 'button.clown'}]]:
            with self.subTest(actions=actions), self.assertRaises(ValueError):
                await self.c.async_save_settings({'scare_spots': [{**self.definitions[0], 'props': actions}]})
        self.assertEqual(len(self.c.settings['scare_spots']), 2)

    async def test_own_boocue_control_and_conflicting_group_times_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'eigen bediening'):
            self.c.props.prepare([{'entity_id': 'switch.boocue_enabled'}])
        with self.assertRaisesRegex(ValueError, 'verschillende tijden'):
            self.c.props.prepare([{'entity_id': 'switch.group', 'duration': 1}, {'entity_id': 'switch.relay', 'duration': 2}])
