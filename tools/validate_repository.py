"""Small deterministic packaging checks; not a substitute for HACS review."""

import json
from pathlib import Path
import wave

root = Path(__file__).resolve().parents[1]
integration = root / "custom_components/boocue"
assert [p.name for p in (root / "custom_components").iterdir() if p.is_dir() and p.name != "__pycache__"] == ["boocue"]
manifest = json.loads((integration / "manifest.json").read_text())
for field in ["domain", "name", "version", "documentation", "issue_tracker", "codeowners"]:
    assert manifest.get(field), field
assert manifest["domain"] == "boocue"
assert (integration / "brand/icon.png").is_file()
assert (root / "hacs.json").is_file()
for p in integration.rglob("*.json"):
    json.loads(p.read_text())
assets = integration / "assets"
referenced = set()
pack = assets / "pack.json"
raw = json.loads(pack.read_text())
notice = (assets / raw.get("license_file", "")).resolve()
assert raw.get("license"), "Missing bundled asset license metadata"
assert notice.is_relative_to(assets.resolve()) and notice.is_file(), "Missing asset license notice"
assert notice.read_text().strip(), "Empty asset license notice"
for effect in raw["effects"]:
    assert effect.get("license"), f"Missing asset license: {effect['id']}"
    audio = (assets / effect["audio"]).resolve()
    assert audio.parent == (assets / "audio").resolve(), f"Bundled audio must live in assets/audio: {audio}"
    assert audio.is_file() and audio.stat().st_size > 1000, f"Missing or empty bundled audio: {audio}"
    referenced.add(audio)
assert not (assets / "packs").exists(), "Use the shared bundled catalog and audio directory"
media = {p.resolve() for p in assets.rglob("*") if p.suffix.lower() in {".wav", ".mp3", ".ogg", ".flac", ".m4a"}}
assert media == referenced, "Every bundled recording must belong to a documented pack"
assert not list(integration.rglob("import-notes.json")), "Local import notes do not belong in a release"
for p in (assets / "audio").glob("*.wav"):
    with wave.open(str(p)) as f:
        assert f.getnframes() > 0
        data = f.readframes(f.getnframes())
        assert any(data), f"Silent demo sound: {p.name}"
print(f"BooCue manifest, layout, translations, brand and {len(media)} bundled recordings with asset notices checked")
