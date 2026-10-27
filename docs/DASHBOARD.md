# BooCue Lovelace card

The integration includes `custom:boocue-card`: master power, continuous mood, foreground effects and saved-queue transport on a regular Home Assistant dashboard. The full BooCue panel is only needed to create queues, motion rules and effect packs or to change global defaults.

## Add the card

1. Install BooCue 1.1.0 or newer and restart Home Assistant.
2. Refresh the browser page. The integration registers the card module automatically; no separate HACS frontend repository is needed.
3. Edit a dashboard, choose **Add card**, search for **BooCue**, and save.

Or add a manual card:

```yaml
type: custom:boocue-card
```

The graphical editor exposes title, theme, default selections, visible sections and optional output overrides per channel. A Home Assistant administrator is required, matching the existing BooCue panel/actions. The card supports native sections and masonry layouts and adapts to narrow dashboard columns.

If the card is missing after an update, fully refresh the page. As a fallback, add a **JavaScript module** dashboard resource with URL `/boocue_frontend/boocue-card.js?v=1.1.0`, then refresh again. Do not copy the card into `www` separately: it updates with the integration.

## Operation

- The header's power button controls the persistent master gate. Off stops playback and blocks new starts; On does not resume an old show.
- **Mood** plays its selected atmosphere continuously. **Effect** starts a foreground effect. Each has its own Stop. The saved output and per-effect audio routing are used by default.
- **Queue** selects a saved queue and offers Play, Next and Stop. Next interrupts an item or skips its pause. Queue Stop leaves mood running. Ordered/shuffled playback, gaps, repeat and motion advance come from the saved queue definition.
- Cue-derived color blocks and one downward arrow show the current cue group. Time, repeat, speed and light offset follow the server timeline. These are intended colors, not measured bulb output.
- The motion checkbox arms saved rules. It is disabled with an explanatory label when no rules exist. Stop all stops the show and disarms motion; it leaves master power unchanged.
- Up to eight saved effect favorites appear as quick-play buttons when available. The two theme variants follow HA automatically, or can be selected explicitly in the editor.

Choosing a different dropdown item does not interrupt the current show until Play is pressed. Current playback is named below the selector. Status/progress updates preserve dropdown values and keyboard focus. Other cards, the full panel and HA automations share the same server state; they are controls for the same two channels, rather than independent shows.

## Card configuration

| Option | Default | Purpose |
| --- | --- | --- |
| `title` | `BooCue` | Card title. |
| `theme` | `auto` | `auto`, `light` or `dark`. |
| `effect`, `mood`, `queue` | automatic | Initial ids selected by this card. The corresponding dropdown remains usable. |
| `show_effects`, `show_mood`, `show_queue` | `true` | Show/hide a playback lane. |
| `show_motion`, `show_favorites` | `true` | Show motion arming and favorite shortcuts. |
| `effect_settings`, `mood_settings`, `queue_settings` | none | Optional runtime overrides, scoped to starts from this card. |

The output overrides do not rewrite BooCue's saved settings. Explicit card overrides win over saved routes and queue defaults. Configure the queue's order/repeat behavior in the BooCue panel. The editor's **Use saved lights/speakers** choices distinguish inheritance from an intentionally empty target list.

For example, route mood to one player and effects/queues to two others:

```yaml
type: custom:boocue-card
title: Haunted hallway
theme: auto
effect: thunder-roll
mood: campfire
mood_settings:
  output: speakers
  speakers:
    - media_player.living_room
  lights: []
  volume: 0.2
effect_settings:
  output: speakers
  speakers:
    - media_player.porch
    - media_player.hall
  lights:
    - light.porch
  volume: 0.6
queue_settings:
  output: speakers
  speakers:
    - media_player.porch
    - media_player.hall
  lights:
    - light.porch
```

Ids above are examples. Supported runtime keys are the same as BooCue playback actions: lights, output, speakers, volume, brightness, speed, light offset, routing, repeat, restoration, light-command interval, audio mixing mode and mood ducking. See [automation/output limits](AUTOMATIONS.md).

## Browser sound and multiple cards

Play enables/resumes browser audio from the user click when needed. **Enable sound on this device** explicitly prepares this dashboard as a station for queues, motion and HA actions. Keep the dashboard open and connected for browser output; compatible HA speakers need no open dashboard.

Multiple BooCue cards in one HA connection share one subscription and one browser audio engine, preventing duplicate sound. Closing/removing the last card releases its browser station and stops its owned browser playback. HA-speaker and light-only shows continue on the server. A station in another tab/device cannot be taken over while its browser show is active. Disconnect cancels local audio and pending starts; reconnect refreshes the catalog without silently claiming the station again.

The browser can mix mood and effects and duck the mood during foreground audio. Speaker synchronization, announcements, loop gaps, restored volumes and hardware timing have the same practical limits as the full panel. The small card catalog contains at most 18 cue groups per effect and omits complete timelines, motion-rule definitions and the home's entity inventory.

Implementation follows Home Assistant's [custom-card API](https://contributors.home-assistant.io/frontend/custom-ui/card/) and [editor/picker conventions](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/). All 68 bundled sounds are included; user-supplied packs stay in the Home Assistant configuration directory. See [asset licenses](../ASSETS.md) for the bundled recordings and cues.
