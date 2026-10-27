"""Exercise pack validation, archive boundaries and scheduler behavior."""

import asyncio
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
package = types.ModuleType("boocue_test_core")
package.__path__ = [str(ROOT / "custom_components/boocue")]
sys.modules[package.__name__] = package
from boocue_test_core.engine import play_timeline
from boocue_test_core.library import import_zip, load_library, read_pack
from boocue_test_core.models import Cue, Effect, parse_effect


class PackTests(unittest.TestCase):
    def test_original_demos_are_complete(self):
        effects = [e for e in read_pack(ROOT / "custom_components/boocue/assets/pack.json")
                   if e.source == "BooCue Originals"]
        self.assertEqual(len(effects), 8)
        self.assertEqual(len({e.id for e in effects}), 8)
        self.assertTrue(all(e.audio.stat().st_size > 1000 for e in effects))

    def test_bundled_catalog_is_complete(self):
        assets = ROOT / "custom_components/boocue/assets"
        with tempfile.TemporaryDirectory() as temp:
            result, errors = load_library(assets, Path(temp) / "absent")
        self.assertEqual(len(result), 68)
        self.assertEqual(errors, [])
        self.assertFalse((assets / "packs").exists())
        self.assertTrue(all(e.audio.parent == assets / "audio" for e in result.values()))
        halloween = [e for e in result.values() if e.id.startswith("hh-")]
        self.assertEqual(sum(e.category == "effects" for e in halloween), 48)
        self.assertEqual(sum(e.category == "moods" for e in halloween), 12)
        self.assertTrue(all(e.description and "Imported locally" not in e.description for e in halloween))
        self.assertGreater(len({e.icon for e in halloween}), 25)
        self.assertTrue(all(e.audio.stat().st_size > 1000 and e.cues for e in result.values()))

    def test_demo_regeneration_preserves_other_sounds_and_asset_terms(self):
        assets = ROOT / "custom_components/boocue/assets"
        spec = importlib.util.spec_from_file_location("boocue_generate_demos", ROOT / "tools/generate_demos.py")
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        raw = json.loads((assets / "pack.json").read_text())
        third_party = [e for e in raw["effects"] if e["id"].startswith("hh-")]
        with tempfile.TemporaryDirectory() as temp:
            generator.OUT = Path(temp)
            (generator.OUT / "audio").mkdir()
            (generator.OUT / "pack.json").write_text(json.dumps(raw))
            expected = {}
            for e in third_party:
                dest = generator.OUT / e["audio"]
                shutil.copy2(assets / e["audio"], dest)
                expected[dest] = hashlib.sha256(dest.read_bytes()).digest()
            with redirect_stdout(io.StringIO()):
                generator.main()
            regenerated = json.loads((generator.OUT / "pack.json").read_text())
            self.assertEqual(len(regenerated["effects"]), 68)
            self.assertEqual(regenerated["license_file"], raw["license_file"])
            self.assertEqual(regenerated["license"], raw["license"])
            self.assertEqual([e for e in regenerated["effects"] if e["id"].startswith("hh-")], third_party)
            for dest, digest in expected.items():
                self.assertEqual(hashlib.sha256(dest.read_bytes()).digest(), digest)

    def test_legacy_import_is_recognized_without_deleting_files(self):
        assets = ROOT / "custom_components/boocue/assets"
        with tempfile.TemporaryDirectory() as temp:
            private = Path(temp) / "packs"
            local = private / "hue-halloween-local"
            (local / "audio").mkdir(parents=True)
            raw = json.loads((assets / "pack.json").read_text())
            raw["effects"] = [e for e in raw["effects"] if e["id"].startswith("hh-")]
            for e in raw["effects"]:
                shutil.copy2(assets / e["audio"], local / e["audio"])
            raw["id"] = "hue-halloween-local"
            for e in raw["effects"]:
                e.update(description="Imported locally · BooCue light routing", icon="mdi:ghost", source="Local import")
            (local / "pack.json").write_text(json.dumps(raw))
            result, errors = load_library(assets, private)
            self.assertEqual(len(result), 68)
            self.assertEqual(errors, [])
            self.assertTrue(result["hh-fx1"].audio.is_relative_to(assets))
            self.assertEqual(len(list(local.glob("audio/*.mp3"))), 60)
            self.assertTrue((local / "pack.json").is_file())

    def test_modified_bundled_id_is_reported_without_shadowing(self):
        assets = ROOT / "custom_components/boocue/assets"
        for change in ["audio", "cues", "description"]:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temp:
                private = Path(temp) / "packs"
                local = private / "modified"
                local.mkdir(parents=True)
                raw = json.loads((assets / "pack.json").read_text())
                raw["effects"] = [e for e in raw["effects"] if e["id"] == "hh-fx1"]
                effect = raw["effects"][0]
                (local / "audio").mkdir()
                shutil.copy2(assets / effect["audio"], local / effect["audio"])
                if change == "audio":
                    with (local / effect["audio"]).open("ab") as f:
                        f.write(b"changed")
                elif change == "cues":
                    effect["cues"][0]["brightness"] = .1234567
                else:
                    effect["description"] = "My customized effect"
                (local / "pack.json").write_text(json.dumps(raw))
                result, errors = load_library(assets, private)
                self.assertEqual(len(result), 68)
                self.assertEqual(errors, ["modified: Effect ids overlap another pack"])
                self.assertTrue(result["hh-fx1"].audio.is_relative_to(assets))
                self.assertTrue((local / effect["audio"]).is_file())

    def test_duplicate_ids_between_private_packs_remain_an_error(self):
        assets = ROOT / "custom_components/boocue/assets"
        with tempfile.TemporaryDirectory() as temp:
            private = Path(temp) / "packs"
            raw = json.loads((assets / "pack.json").read_text())
            raw["effects"] = raw["effects"][:1]
            raw["effects"][0]["id"] = "user-thunder"
            for name in ["first", "second"]:
                dest = private / name
                (dest / "audio").mkdir(parents=True)
                (dest / "pack.json").write_text(json.dumps(raw))
                shutil.copy2(assets / raw["effects"][0]["audio"], dest / raw["effects"][0]["audio"])
            result, errors = load_library(assets, private)
            self.assertEqual(len(result), 69)
            self.assertEqual(errors, ["second: Effect ids overlap another pack"])

    def test_unsafe_audio_path_is_rejected(self):
        raw = json.loads((ROOT / "custom_components/boocue/assets/pack.json").read_text())["effects"][0]
        for path in ["../outside.mp3", "/tmp/outside.wav", "..\\outside.mp3"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                parse_effect({**raw, "audio": path}, ROOT / "custom_components/boocue/assets")

    def test_nonfinite_and_unsorted_cues_are_rejected(self):
        raw = json.loads((ROOT / "custom_components/boocue/assets/pack.json").read_text())["effects"][0]
        for overrides in [{"duration": float("nan")},
                          {"cues": [{"at": 2}, {"at": 1}]},
                          {"cues": [{"at": 0, "brightness": 1.1}]}]:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                parse_effect({**raw, **overrides}, ROOT / "custom_components/boocue/assets")

    def test_zip_traversal_leaves_no_published_pack(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "evil.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("../outside.mp3", b"test")
            with self.assertRaises(ValueError):
                import_zip(archive, root / "packs", set())
            self.assertFalse((root / "outside.mp3").exists())
            self.assertEqual(list((root / "packs").iterdir()), [])

    def test_valid_pack_import_and_duplicate_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "pack.zip"
            assets = ROOT / "custom_components/boocue/assets"
            raw = json.loads((assets / "pack.json").read_text())
            raw["id"] = "test-pack"
            raw["effects"] = [e for e in raw["effects"] if e["source"] == "BooCue Originals"]
            for e in raw["effects"]:
                e["id"] = "test-" + e["id"]
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("pack.json", json.dumps(raw))
                for e in raw["effects"]:
                    z.write(assets / e["audio"], e["audio"])
            self.assertEqual(import_zip(archive, root / "packs", set()), 8)
            result, errors = load_library(assets, root / "packs")
            self.assertEqual(len(result), 76)
            self.assertEqual(errors, [])
            with self.assertRaises(ValueError):
                import_zip(archive, root / "packs", set(result))


class SchedulerTests(unittest.IsolatedAsyncioTestCase):
    def effect(self, duration=.4):
        return Effect("test", "Test", "", "effects", duration, Path("/unused"),
                      tuple(Cue(i / 100, 0, 0, .5) for i in range(int(duration * 100))))

    async def test_slow_device_does_not_replay_every_stale_cue(self):
        seen = []
        async def emit(cue, step):
            seen.append(cue.at)
            await asyncio.sleep(.13)
        await play_timeline(self.effect(), emit, lambda p, c: None,
                            start_delay=0, speed=1, interval=.05, repeat=False)
        self.assertGreaterEqual(len(seen), 2)
        self.assertLessEqual(len(seen), 4)
        self.assertGreater(seen[1] - seen[0], .1)
        self.assertEqual(seen, sorted(seen))

    async def test_cancel_during_initial_delay_emits_nothing(self):
        seen = []
        async def emit(cue, step):
            seen.append(cue.at)
        task = asyncio.create_task(play_timeline(self.effect(), emit, lambda p,c:None,
                    start_delay=1, speed=1, interval=.05, repeat=False))
        await asyncio.sleep(.02)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(seen, [])

    async def test_repeat_wraps_and_can_be_stopped(self):
        cycles = []
        async def emit(cue, step):
            pass
        task = asyncio.create_task(play_timeline(self.effect(.15), emit, lambda p,c:cycles.append(c),
                    start_delay=0, speed=2, interval=.02, repeat=True))
        await asyncio.sleep(.25)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertGreaterEqual(max(cycles), 2)


if __name__ == "__main__":
    unittest.main()
