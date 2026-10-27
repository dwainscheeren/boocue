# Contributing to BooCue

Bug reports, documentation improvements and focused code changes are welcome. Include the Home Assistant version, the relevant output type and clear reproduction steps when reporting a problem. Remove tokens, personal configuration and imported media from logs or attachments.

## Project layout

- `custom_components/boocue/`: integration, playback engine, panel, Lovelace card and bundled sound packs.
- `tests/`: pack, scheduling, HA adapter and browser-lifecycle checks.
- `tools/`: demo generation, repository validation and release packaging.
- `dev/`: isolated panel preview with simulated devices.
- `docs/`: configuration and automation examples.

## Local checks

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q custom_components tools
node --input-type=module --check < custom_components/boocue/frontend/boocue-panel.js
node --check custom_components/boocue/frontend/boocue-card.js
node --test tests/test_frontend.mjs tests/test_card.mjs
python3 tools/validate_repository.py
```

Tests that need Home Assistant skip when its Python package is unavailable. To run the complete suite in the supported HA environment:

```sh
docker run --rm --network none --entrypoint python \
  -v "$PWD:/repo:ro" -w /repo \
  ghcr.io/home-assistant/home-assistant:2026.8.0 \
  -m unittest discover -s tests -v
```

Adapter tests simulate devices; they do not establish physical speaker/lamp latency or audibility. Use virtual demo lamps or a separate test installation for playback checks.

## Panel preview

```sh
python3 dev/preview_server.py
```

Open the localhost URL printed by the server. The preview uses simulated entities and the bundled sound catalog. Verify the Lovelace card and its graphical editor in a Home Assistant dashboard.

Keep both themes, narrow dashboard columns, keyboard focus, pending/disabled states and cancellation behavior working. Play, queue and motion actions share one server engine; avoid separate scheduling logic in the UI.

## Assets and releases

All bundled sounds live in `assets/audio/`, described by the shared `assets/pack.json` catalog. Regenerate the eight original demos with `python3 tools/generate_demos.py`; the other recordings, cue definitions and asset-license metadata are preserved. See [ASSETS.md](ASSETS.md) for their terms. Keep installation-specific packs, credentials and local work files out of commits. Add third-party media only with permission and a notice that describes its distribution terms; the code's MIT license does not cover it automatically.

```sh
python3 tools/package_release.py dist/boocue-v1.1.0.zip
```

The archive contains the `boocue/` integration folder and is accompanied by a SHA-256 file. Check the manifest version, archive layout and included assets before creating a release. Preserve upstream copyright and license notices.
