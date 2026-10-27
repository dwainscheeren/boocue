"""Local effect packs, including bounded ZIP import."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
import shutil
import stat
import tempfile
import zipfile

from .models import Effect, MAX_EFFECTS, SAFE_ID, parse_effect

LOGGER = logging.getLogger(__name__)
MAX_BYTES = 100 * 1024 * 1024


def read_pack(path: Path) -> list[Effect]:
    if path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("pack.json is too large")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("version") != 1:
        raise ValueError("Expected a BooCue version 1 pack")
    effects = raw.get("effects")
    if not isinstance(effects, list) or not 1 <= len(effects) <= MAX_EFFECTS:
        raise ValueError("A pack needs 1–200 effects")
    parsed = [parse_effect(e, path.parent) for e in effects]
    if len({e.id for e in parsed}) != len(parsed):
        raise ValueError("Duplicate effect ids in pack")
    return parsed


def _same_content(left: Effect, right: Effect) -> bool:
    """Recognize an unchanged local copy of a now-bundled effect."""
    left_data, right_data = left.public(), right.public()
    left_data.pop("source")
    right_data.pop("source")
    if left_data != right_data:
        return False
    with left.audio.open("rb") as left_audio, right.audio.open("rb") as right_audio:
        return (hashlib.file_digest(left_audio, "sha256").digest()
                == hashlib.file_digest(right_audio, "sha256").digest())


def load_library(builtin: Path, private: Path) -> tuple[dict[str, Effect], list[str]]:
    result = {e.id: e for e in read_pack(builtin / "pack.json")}
    bundled_ids = set(result)
    errors = []
    if private.exists():
        for path in sorted(private.glob("*/pack.json")):
            try:
                effects = read_pack(path)
                for effect in effects:
                    if effect.id in result and (effect.id not in bundled_ids
                            or not _same_content(effect, result[effect.id])):
                        raise ValueError("Effect ids overlap another pack")
                additions = {e.id: e for e in effects if e.id not in result}
                if len(result) + len(additions) > 600:
                    raise ValueError("The library supports at most 600 effects")
                result.update(additions)
            except (OSError, ValueError, TypeError, KeyError) as err:
                errors.append(f"{path.parent.name}: {err}")
                LOGGER.warning("Cannot load BooCue pack %s: %s", path.parent.name, err)
    return result, errors


def import_zip(archive: Path, private: Path, existing: set[str]) -> int:
    """Validate in a staging directory, then publish a whole new pack."""
    private.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".boocue-", dir=private) as stage:
        stage_path = Path(stage) / "payload"
        stage_path.mkdir()
        with zipfile.ZipFile(archive) as z:
            files = z.infolist()
            if len(files) > 500 or sum(i.file_size for i in files) > MAX_BYTES:
                raise ValueError("The pack exceeds 500 files or 100 MB")
            for item in files:
                name = item.filename
                path = Path(name)
                mode = item.external_attr >> 16
                if (path.is_absolute() or ".." in path.parts or "\\" in name
                        or stat.S_ISLNK(mode) or name.startswith(".")
                        or (mode and not item.is_dir() and stat.S_IFMT(mode) not in {0, stat.S_IFREG})):
                    raise ValueError("Unsafe path or special file in ZIP")
                dest = stage_path / path
                if item.is_dir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(item) as source, dest.open("xb") as target:
                        shutil.copyfileobj(source, target)
        manifests = list(stage_path.glob("pack.json")) + list(stage_path.glob("*/pack.json"))
        if len(manifests) != 1:
            raise ValueError("ZIP must contain exactly one pack.json at its root or in one folder")
        manifest = manifests[0]
        raw = json.loads(manifest.read_text(encoding="utf-8"))
        pack_id = raw.get("id", "")
        if not isinstance(pack_id, str) or not SAFE_ID.fullmatch(pack_id):
            raise ValueError("Pack needs a safe id")
        effects = read_pack(manifest)
        if any(e.id in existing for e in effects):
            raise ValueError("An effect with this id already exists; use a new pack id")
        if len(existing) + len(effects) > 600:
            raise ValueError("The library supports at most 600 effects")
        dest = private / pack_id
        if dest.exists():
            raise ValueError("A pack with this id already exists")
        manifest.parent.rename(dest)
        return len(effects)
