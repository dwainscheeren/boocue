# Example setups

These recipes use the built-in sounds and the same playback engine as the dashboard card. Example light, speaker and sensor IDs below are placeholders: replace them with entities from your Home Assistant installation.

## Rain in the background, random scares at the porch

![Background moods and their independent destinations](images/moods.jpg)

1. Open **Mood**, select **Rain** and choose the background speaker. Leave its light selection empty if you want only background sound. Start playback.
2. Open **Effects** and select the porch lights and the speaker for foreground effects. Use a different speaker from the mood unless your player supports Sonos announcement mixing; **This device** can also mix both channels.
3. Go to **Queues → New queue** and name it **Porch surprises**.
4. Add **Thunder**, **Knocking**, **Ghost** and **Witch**. Choose shuffle, repeat, automatic advance and a pause between **4** and **15** seconds.
5. Save and start the queue. Each selected row plays once per shuffle cycle. The delay starts after an effect finishes; the atmosphere continues underneath.

**Stop queue** ends the scares while the mood continues. **Stop all** ends both channels and disarms motion rules.

## Advance a scene when someone moves

![Queue configuration](images/queues.jpg)

1. Save a queue called **Haunted hallway** containing **Stairs → Door → Scream**.
2. Choose fixed order and **Wait for motion / Next**. Disable repeat for one pass, or enable it to keep cycling.
3. Open **On motion → New rule**. Give it a name and select your hallway sensor and, optionally, another sensor.
4. Use **OR** to accept either sensor. Use **AND** when every selected sensor must be on when a new movement arrives.
5. Set the action to **Next item / start queue**, choose **Haunted hallway**, set a cooldown such as **15 seconds**, save and arm automatic mode.

![Motion sensors, sensor matching and a queue action](images/motion.jpg)

The first accepted movement starts the queue. Later movements advance it, including interrupting an item already playing. If you want each sound to finish automatically, use an automatic queue and the **Start queue** motion action instead.

Only an `off` → `on` transition counts. A sensor staying on does not keep retriggering. AND means all selected sensors are currently on; they do not need to change at precisely the same instant.

For a single random effect per visitor, choose **Play one effect**, select an effect pool and use shuffle/random selection with a cooldown. Home Assistant automations are useful when you also need time, sun or presence conditions.

## A compact dashboard

```yaml
type: custom:boocue-card
title: Haunted hallway
effect: hh-fx1
mood: hh-mood800
show_effects: true
show_mood: true
show_queue: true
show_motion: true
show_favorites: true
```

Use the dropdown to choose one of your saved queues. Set per-channel lights and speaker overrides in the card's visual editor if they should differ from the panel defaults. [All card options](DASHBOARD.md).

## Start a background atmosphere from an HA script

```yaml
alias: BooCue rain atmosphere
sequence:
  - action: boocue.set_enabled
    data:
      enabled: true
  - action: boocue.play
    data:
      effect_id: hh-mood800
      channel: mood
      lights: []
      output: speakers
      speakers:
        - media_player.background_speaker
      volume: 0.25
mode: single
```

Mood always repeats. It has its own output and volume; starting or stopping a foreground effect does not stop it.

## Motion with a time window and cooldown

This HA automation plays thunder when either sensor changes from off to on between 17:00 and 23:00, while the BooCue master switch is on. Its single execution mode and final delay provide a 20-second cooldown.

```yaml
alias: BooCue porch thunder
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.porch_motion
      - binary_sensor.garden_motion
    from: "off"
    to: "on"
conditions:
  - condition: state
    entity_id: switch.boocue_enabled
    state: "on"
  - condition: time
    after: "17:00:00"
    before: "23:00:00"
actions:
  - action: boocue.play
    data:
      effect_id: hh-fx1
      channel: effect
      if_idle: true
      lights:
        - light.porch
      output: speakers
      speakers:
        - media_player.porch_speaker
      volume: 0.5
      restore: true
  - delay: "00:00:20"
mode: single
```

Use a separate background speaker when combining this with a mood, unless your target supports announcement mixing. `if_idle` skips a start while the foreground channel is occupied. If using HA automations for these sensors, leave equivalent built-in rules disarmed to avoid sending the same trigger twice.

## Arm saved motion rules from HA

```yaml
action: switch.turn_on
target:
  entity_id: switch.boocue_automatic
```

This arms your saved rules; the master switch must also be on. `switch.turn_off` disarms future triggers. A timed queue already running continues until you stop it.

To stop and disarm the whole show:

```yaml
action: boocue.stop
```

For queue IDs, action parameters and independent channel stops, see the [automation reference](AUTOMATIONS.md).
