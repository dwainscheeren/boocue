# Motion rules and Home Assistant automations

For props with their own paired lights and speakers, use [scare spots](SCARE_SPOTS.md). They support independent motion sensors, location loops, one-at-a-time or parallel playback and dedicated HA actions.

BooCue offers both. Use **Queues** for a saved sequence and **On motion** for one or more sensors, an effect/queue action, destinations and a cooldown. Use Home Assistant automations when you want schedules, sun conditions, presence, helpers, doorbells, or coordination with other integrations. Both call the same playback engine.

## Master power versus stopping a show

`switch.boocue_enabled` is the global enable switch. Off cancels the queue, stops both channels and blocks all new starts through the panel, motion rules and HA actions. It also cancels local browser previews that are still loading. The flag is stored and survives a HA restart. On permits future starts; it does not resume a cancelled show.

Master Off retains `switch.boocue_automatic`'s armed choice, so motion rules become effective again after master On, on a new sensor edge. Stop all instead stops the show **and disarms motion**, without changing master power. Explicit channel/queue stops leave both switches unchanged.

The native Stop all button and global `boocue.stop` action also cancel playing or loading Listen previews in connected panels after server cleanup. Independent channel/queue stops leave those local previews alone.

```yaml
action: switch.turn_off
target:
  entity_id: switch.boocue_enabled
```

The equivalent action is:

```yaml
action: boocue.set_enabled
data:
  enabled: false
```

To enable and start a background atmosphere:

```yaml
alias: BooCue evening atmosphere
sequence:
  - action: switch.turn_on
    target:
      entity_id: switch.boocue_enabled
  - action: boocue.play
    data:
      effect_id: campfire
      channel: mood
      output: speakers
      speakers:
        - media_player.living_room
      lights: []
      volume: 0.2
mode: single
```

`binary_sensor.boocue_active` is an easy running/idle condition, including queues waiting for motion or a pause. Native buttons can be placed on dashboards or called with `button.press`: `button.boocue_stop_all`, `button.boocue_stop_effect`, `button.boocue_stop_mood`, `button.boocue_stop_queue`, and `button.boocue_next_queue`. Next is available only for a running queue; use `boocue.queue_next` with a queue id when it should also start an idle queue. The queue id is now available in its editor’s **Outputs and lights** section before its first start.

The status sensors keep immediate start/stop/error updates, with ordinary progress at most once a second. High-frequency progress and nested channel data are excluded from recorder history; current attributes remain available for automations.

## Built-in motion rules

1. Open **On motion → New rule**.
2. Name the rule and choose one or more binary sensors. OR accepts movement from either; AND requires all selected sensors to be on at the moment of a new movement. This does not require simultaneous edges.
3. Choose **Play one effect**, **Start queue**, or **Next item / start queue**. For an effect choose a pool and random/sequence selection. For queue actions choose a saved queue.
4. Set a minimum time between accepted triggers. Effect rules own their destinations, overriding per-effect defaults; queue rules use the queue settings and per-effect audio routes. Browser rules require an enabled audio station.
5. Save and enable the rules when ready.

Only an `off` → `on` transition counts. A sensor staying on does not repeatedly retrigger. `unknown`/`unavailable` recovery and initial HA startup do not trigger a rule. Effect/start-queue triggers during another foreground effect or queue are skipped, without consuming a sequence step. Next-queue intentionally interrupts the current item or advances a waiting queue; if no queue is running it starts the selected queue. If a different queue is running, the trigger reports a conflict. Cooldown is measured from the last accepted start; runtime cooldown and sequence position reset on HA restart. Rule configuration and the armed state persist.

The native `switch.boocue_automatic` can be used in dashboards and HA schedules. **Stop all** disables automatic mode as well as stopping both channels. Stopping only the mood or effect leaves the armed state unchanged. A mood can remain on separate speakers, in the same browser, or on compatible Sonos speakers while motion effects play. Disarming prevents new motion triggers; an already running timed queue continues until stopped. **Stop effect** also cancels its queue; **Stop queue** leaves mood and the armed state unchanged.

## Saved queues

Create a named queue in the panel, add effects (including repeated rows) and reorder with the arrows. Choose fixed order or shuffle, repeat or a single pass, and a minimum/maximum pause. The default is 4–15 seconds **after completion**, followed by the normal preparation delay. Shuffle plays every row once per cycle and avoids immediate identical effects when another remaining row is available; duplicate rows give that effect extra weight.

**Wait for motion / Next** plays the first item on start, then waits between items. Create a **Next item / start queue** motion rule to start it on the first movement and step through later. Next while an item is playing interrupts it; Next during a timed pause skips the pause. A non-repeating queue ends after its final item.

Start an atmosphere from **Mood** separately. It keeps looping while the effect queue plays, pauses between effects, or waits for movement. Queue Stop leaves it running. For random effects over a constant atmosphere use a repeating shuffled queue with timed pauses; for motion effects use a motion pool or motion-advanced queue.

Runtime precedence is panel defaults → queue overrides → per-effect audio route → explicit action overrides. A queue snapshots its definition and resolved settings on start. Save/edit operations apply to the next start. Removing an active queue stops it. Remove or edit motion rules referencing a queue before deleting that queue.

The queue id is an attribute of `sensor.boocue_queue` while it runs. Use it in HA actions:

```yaml
action: boocue.queue_start
data:
  queue_id: your-saved-queue-id
  if_idle: true
  settings:
    lights:
      - light.porch
    output: speakers
    speakers:
      - media_player.porch
```

```yaml
action: boocue.queue_next
data:
  queue_id: your-saved-queue-id
```

```yaml
action: boocue.queue_stop
```

`queue_next` may omit `queue_id` while a queue is running. Starting a new queue replaces the foreground queue/effect after validating all its targets; a manual effect also stops the queue. `if_idle` skips instead. Queues do not restart automatically after HA restarts. Rule cooldown begins at an accepted trigger, not at clip completion.

## A fixed effect on multiple speakers

```yaml
action: boocue.play
data:
  effect_id: thunder-roll
  channel: effect
  output: speakers
  speakers:
    - media_player.porch
    - media_player.hall
  lights:
    - light.porch
  volume: 0.6
  if_idle: true
```

Omit `output`, `speakers` and `volume` to use the selected effect's saved audio route, falling back to the panel defaults. Explicit action values win. `if_idle: true` checks the channel atomically, so an automation cannot replace an effect that just started elsewhere. It skips instead of queueing. Browser output requires a BooCue card or panel with browser audio already enabled. Actions fail clearly when no station is ready. Keep the card or panel open and connected; HA-speaker and light-only actions need no panel.

## A continuously repeating mood

```yaml
action: boocue.play
data:
  effect_id: campfire
  channel: mood
  output: speakers
  speakers:
    - media_player.living_room
  lights: []
  volume: 0.2
```

Only effects categorized as `moods` can use this channel. It always repeats at normal speed. An effect can play at the same time on different speakers. Shared lights temporarily follow the foreground effect, then resume the current mood cues. Their original pre-show state is restored after the final owner releases them, when restoration is enabled. Starting a new mood replaces the old mood; starting a new effect replaces the old effect.

Playback is not automatically resumed after a HA restart. Add a startup automation if that is your intended behavior.

## Motion with a time condition in Home Assistant

```yaml
alias: BooCue porch after sunset
triggers:
  - trigger: state
    entity_id: binary_sensor.porch_motion
    from: "off"
    to: "on"
conditions:
  - condition: sun
    after: sunset
actions:
  - action: boocue.play
    data:
      effect_id: creaking-door
      channel: effect
      if_idle: true
      output: speakers
      speakers:
        - media_player.porch
      lights:
        - light.porch
  - wait_template: "{{ not is_state('sensor.boocue_effect', 'playing') }}"
    timeout: "00:10:00"
  - delay: "00:00:30"
mode: single
max_exceeded: silent
```

Entity ids above are examples; use your installation's entities. No built-in motion rule is needed for the same sensor when HA owns the automation, to avoid duplicate triggers.

## Stop independently, or stop and disarm everything

```yaml
action: boocue.stop
data:
  channel: effect
```

```yaml
action: boocue.stop
```

```yaml
action: boocue.set_automatic
data:
  enabled: false
```

Playback sensors: `sensor.boocue_playback` (combined), `sensor.boocue_effect`, `sensor.boocue_mood`, and `sensor.boocue_queue`. The queue sensor includes queue id, run id, current row, step, cycle, waiting state and errors. Home Assistant can change entity ids if they already exist; inspect the BooCue device for your actual ids. Each channel exposes its current effect, speakers, lamps, progress, warnings and error.

## Speaker limits

**This device** mixes the looping atmosphere and foreground effects using separate Web Audio sources. The atmosphere smoothly reduces to 35% of its selected volume during an effect, returning afterwards. Adjust **Background during effects** in the effect fine tuning controls. One enabled browser station receives automatic runs; another device cannot take over while its browser playback is active. Audio may be limited by mobile background-tab/lock-screen suspension.

**Compatible Sonos** targets with HA announcement support use `announce: true` and an announcement volume in automatic mixing mode. Sonos handles the overlap/ducking; BooCue's background multiplier applies to browser audio. Stopping an announcement early cannot reliably cancel just that announcement without stopping the atmosphere, so it may finish naturally and the status includes a warning. Physical firmware behavior is not guaranteed by the mocked adapter tests.

**Other HA speakers** need separate destinations for continuous atmosphere and foreground effects. BooCue rejects unsupported overlap, including known group members. It does not regroup speakers. Unknown integration-specific group topology cannot be inferred. Use **Separate speakers** mixing mode when announcements are unwanted. Multiple targets receive concurrent requests, not sample-accurate synchronization; prefer existing native speaker groups where synchronization matters.

Repeating on generic HA players starts the clip each cycle and may have gaps; browser mood loops a decoded buffer. Only players supporting `play_media` are selectable. For normal playback BooCue sets supported volume and restores it on stop; players without Stop/Pause may finish a clip after Stop, with a warning. Previous music queues are not restored. Both channels share the same light-ownership engine: effects temporarily take priority and mood resumes after them.
