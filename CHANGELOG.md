# Changelog

## 1.2.0

- Pair HA switches and buttons with scare spots, with searchable choices grouped and filtered by area.
- Schedule a single button press or a switch pulse relative to the audio start. Switch on-time is limited to 0.1–120 seconds and ends with the effect or Stop.
- Support silent spots with only prop devices, as well as props combined with speakers, lights, motion triggers and location loops.
- Protect shared switches, buttons and expanded switch-group members during parallel playback; leave switches that are already on untouched.
- Cancel delayed actions on Stop, wait for in-flight commands before cleanup, and persist owned switches for cleanup after an HA restart. Failed cleanup is visible and can be retried with Stop all.
- Keep Stop all available for active scare spots and pending switch cleanup in the panel and dashboard card.

## 1.1.4

- Fix new scare spots, queues and motion rules failing to open when Home Assistant is accessed over plain HTTP on a local network.
- Generate UUIDs with `crypto.getRandomValues`, which works on HTTP as well as HTTPS, and cover all three creation flows with regression tests.

## 1.1.3

- Search lights, speakers, effects and sensors inside the editors by name, description or entity ID.
- Filter device choices by Home Assistant area and scan devices grouped under area headings.
- Keep selected devices across searches, area filters and form changes; show matching-result and selection counts.
- Search the queue's effect selector without changing effects already in the queue.

## 1.1.2

- Create and edit scare spots, queues and motion rules in focused dialogs with a fixed action bar.
- Full-screen editors on phones, keyboard focus containment and Escape/Cancel return to the original list action.
- Keep validation and save errors inside the editor; retain draft changes for retry after a connection failure.

## 1.1.1

- Keep audio and the remaining light timeline running when a lamp temporarily disconnects or times out. Failed light commands appear as playback warnings.
- Document Twinkly command pacing and UltimateSensor speaker compatibility.

## 1.1.0

- Named scare spots with paired speakers, lights and individual effect pools.
- One-at-a-time or parallel playback, with shared-device conflict protection.
- Per-spot motion sensors, OR/AND matching and independent cooldowns.
- Ordered/shuffled location loops, separate stops and HA actions.
- Shared mood lights resume after spot effects; background audio remains independent.

## 1.0.0

- Sound-and-light panel and Lovelace dashboard card for Home Assistant.
- 68 bundled sounds in one audio directory: 54 effects and 14 background atmospheres.
- Independent continuous mood and foreground effects, with separate lights, speakers and volume.
- Ordered or shuffled queues, repeat, random pauses and motion/manual advance.
- Multi-sensor motion rules, native HA entities and automation actions.
- Browser mixing and mood ducking, speaker routing, cue markers and light-state restoration.
- Light/dark themes, English/Dutch controls, custom sound imports and virtual demo lights.
- Illustrated getting-started guide and practical setup/automation examples.
