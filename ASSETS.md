# Assets and licenses

## Original demo sounds

The eight WAV files in `custom_components/boocue/assets/audio/` are procedural synthesizer output from `tools/generate_demos.py`. They combine seeded noise, oscillators, envelopes and simple resonances. Their sound-and-light cue definitions are included in `assets/pack.json`.

Regenerate them with `python3 tools/generate_demos.py`. The output is mono, signed 16-bit PCM at 22,050 Hz. These sounds and cue definitions are covered by the project's [MIT license](LICENSE).

## Halloween Collection

`custom_components/boocue/assets/audio/` contains 60 third-party MP3 recordings: 48 foreground effects and 12 background atmospheres. The shared `assets/pack.json` catalog includes their corresponding light-cue sequences alongside the original demos. Each entry identifies its asset license. Original recordings are unchanged; BooCue supplies its own editorial descriptions, icon choices and user-selected light routing.

The recordings and cue sequences are redistributed with permission. Copyright remains with the respective rights holders; they are **excluded from the project's MIT license**. BooCue does not grant additional rights to relicense or reuse them in other projects. See the [collection's notice](custom_components/boocue/assets/LICENSE-AUDIO.txt), also included in installation archives. BooCue's original editorial descriptions and icon choices remain MIT licensed.

All 68 sounds share the same audio directory and catalog and load directly from the integration. Previously imported, unchanged copies with the same IDs are recognized without duplication; local files are preserved.

## Icons

The panel and dashboard card request Material Design Icons through Home Assistant. The integration's brand mark uses the Pictogrammers `ghost` shape with BooCue's color treatment. The isolated development preview includes MDI path data from `@mdi/js`.

Upstream source and attribution are preserved in [NOTICE](NOTICE) and [LICENSE-ICONS](LICENSE-ICONS), and within the integration's `brand/` directory.

## Screenshots and imported packs

Documentation screenshots show the BooCue panel and dashboard card with example devices. The panel examples use simulated lights, speakers and motion sensors.

User-supplied packs are stored in the Home Assistant configuration directory and are not part of this repository or its release archives. Their recordings and other assets retain their respective licenses.
