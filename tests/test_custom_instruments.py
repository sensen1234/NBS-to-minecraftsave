"""Custom notes must export consistently and produce a usable NoteBetter bundle."""

import copy
import io
import json
import math
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcschematic import Version
from pynbs import Note

from nbs2save.core.constants import INSTRUMENT_BLOCK_MAPPING, INSTRUMENT_MAPPING
from nbs2save.core.custom_instruments import (
    NOTEBETTER_CONFIG_PATH,
    RESOURCE_PACK_PATH,
    export_notebetter_pack,
    get_note_block_info,
    resolve_custom_instrument,
    resource_pack_format,
    validate_custom_instruments,
)
from nbs2save.core.mcfunction import McFunctionOutputStrategy, McFunctionProcessor
from nbs2save.core.preview import build_preview
from nbs2save.core.schematic import SchematicOutputStrategy, SchematicProcessor
from nbs2save.core.staircase_schematic import (
    StaircaseSchematicOutputStrategy,
    StaircaseUpSchematicOutputStrategy,
)


FIXTURES = Path(__file__).parent / "fixtures"
MONO_SAMPLE = FIXTURES / "custom_note_mono.ogg"
STEREO_SAMPLE = FIXTURES / "custom_note_stereo.ogg"


def instrument(**overrides):
    item = {
        "nbs_id": 16,
        "name": "测试钟声",
        "base_block": "minecraft:diamond_block",
        "sound_file": str(MONO_SAMPLE),
        "sound_id": "nbs2save:instruments/test_bell",
        "root_key": 45,
    }
    item.update(overrides)
    return item


def group(mode):
    return {
        "layers": [0],
        "base_coords": [10, 64, -8],
        "block": {"base": "minecraft:iron_block", "cover": "minecraft:redstone_lamp"},
        "generation_mode": mode,
        "offset_mode": "pan",
    }


class CustomInstrumentTests(unittest.TestCase):
    def test_vanilla_and_unknown_instruments_keep_original_behavior(self):
        strategies = (SchematicOutputStrategy, StaircaseSchematicOutputStrategy,
                      StaircaseUpSchematicOutputStrategy, McFunctionOutputStrategy)
        for instrument_id in range(17):
            for key in (20, 33, 45, 57, 70):
                note = Note(0, 0, instrument_id, key)
                expected = (INSTRUMENT_MAPPING.get(instrument_id, "harp"),
                            INSTRUMENT_BLOCK_MAPPING.get(instrument_id, "minecraft:stone"),
                            str(key - 33) if 33 <= key <= 57 else "0")
                self.assertEqual(get_note_block_info(note), expected)
                for strategy in strategies:
                    self.assertEqual(strategy.get_note_block_info(note), expected)

    def test_custom_and_vanilla_override_use_legal_note_properties(self):
        config = {"custom_instruments": [instrument(), instrument(
            nbs_id=3, base_block="minecraft:lapis_block", sound_id="nbs2save:snare")]}
        self.assertEqual(get_note_block_info(Note(0, 0, 16, 57), config),
                         ("harp", "minecraft:diamond_block", "24"))
        self.assertEqual(get_note_block_info(Note(0, 0, 3, 33), config),
                         ("harp", "minecraft:lapis_block", "0"))
        self.assertEqual(get_note_block_info(Note(0, 0, 0, 45), config),
                         ("harp", "minecraft:dirt", "12"))
        self.assertEqual(resolve_custom_instrument(16, config)["root_key"], 45)
        self.assertIsNone(resolve_custom_instrument(2, config))

    def test_normalization_defaults_and_independent_results(self):
        config = {"custom_instruments": [{"nbs_id": 16, "base_block": "diamond_block"}]}
        original = copy.deepcopy(config)
        first = validate_custom_instruments(config)
        self.assertEqual(first[0]["root_key"], 45)
        self.assertEqual(first[0]["sound_id"], "nbs2save:instrument_16")
        self.assertEqual(first[0]["base_block"], "minecraft:diamond_block")
        first[0]["base_block"] = "minecraft:air"
        self.assertEqual(validate_custom_instruments(config)[0]["base_block"], "minecraft:diamond_block")
        self.assertEqual(config, original)
        self.assertEqual(validate_custom_instruments(None), [])

    def test_duplicate_ids_block_mappings_and_sound_events_are_rejected(self):
        for second in (
            instrument(base_block="minecraft:lapis_block", sound_id="nbs2save:other"),
            instrument(nbs_id=17, base_block="diamond_block", sound_id="nbs2save:other"),
            instrument(nbs_id=17, base_block="minecraft:lapis_block"),
        ):
            with self.subTest(second=second), self.assertRaisesRegex(ValueError, "重复"):
                validate_custom_instruments([instrument(), second])

    def test_unsafe_identifiers_and_invalid_fields_are_rejected(self):
        for field, value in (
            ("base_block", "minecraft:stone[axis=x]"),
            ("base_block", "minecraft:Stone"),
            ("sound_id", "../bad"),
            ("sound_id", "test:foo/../outside"),
            ("sound_id", "test:foo//bar"),
            ("sound_id", "test:/absolute"),
            ("sound_id", "test:foo\\bar"),
            ("nbs_id", -1), ("nbs_id", 256), ("nbs_id", True),
            ("root_key", 88), ("root_key", -1), ("name", ""),
        ):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate_custom_instruments([instrument(**{field: value})])

    def test_missing_samples_do_not_prevent_geometry_but_prevent_pack_export(self):
        item = instrument(sound_file="missing-custom-sample.ogg")
        self.assertEqual(validate_custom_instruments([item])[0]["nbs_id"], 16)
        with self.assertRaisesRegex(ValueError, "找不到"):
            validate_custom_instruments([item], require_files=True)
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "existing.zip"
            destination.write_bytes(b"original bundle")
            with self.assertRaises(ValueError):
                export_notebetter_pack(destination, [item])
            self.assertEqual(destination.read_bytes(), b"original bundle")
            self.assertEqual(list(Path(directory).iterdir()), [destination])

    def test_samples_require_complete_single_channel_ogg_vorbis(self):
        self.assertEqual(len(validate_custom_instruments([instrument()], require_files=True)), 1)
        with self.assertRaisesRegex(ValueError, "单声道"):
            validate_custom_instruments([instrument(sound_file=str(STEREO_SAMPLE))], require_files=True)
        with tempfile.TemporaryDirectory() as directory:
            sample = Path(directory) / "fake.ogg"
            valid = MONO_SAMPLE.read_bytes()
            for content in (b"RIFFthis-is-a-wav", b"OggSnot-vorbis", valid[:-1], valid[:100] + b"X" + valid[101:]):
                sample.write_bytes(content)
                with self.subTest(size=len(content)), self.assertRaisesRegex(ValueError, "OGG Vorbis"):
                    validate_custom_instruments([instrument(sound_file=str(sample))], require_files=True)
            sample = Path(directory) / "renamed.wav"
            sample.write_bytes(valid)
            with self.assertRaisesRegex(ValueError, ".ogg"):
                validate_custom_instruments([instrument(sound_file=str(sample))], require_files=True)

    def test_resource_pack_formats_follow_target_game_version(self):
        for version, expected in (("1.16.5", 6), ("1.19.4", 13), ("1.20.6", 32),
                                  ("1.21", 34), ("JE_1_21_3", 42),
                                  (Version.JE_1_21_4, 46), (Version.JE_1_21_5, 55)):
            self.assertEqual(resource_pack_format(version), expected)
        with self.assertRaises(ValueError):
            resource_pack_format("1.15.2")

    def test_bundle_contains_actual_mod_config_and_valid_nested_resource_pack(self):
        config = {"custom_instruments": [instrument(root_key=57), instrument(
            nbs_id=17, base_block="minecraft:lapis_block", sound_id="other:bell", root_key=33)],
            "data_version": Version.JE_1_21_5}
        with tempfile.TemporaryDirectory() as directory:
            destination = export_notebetter_pack(Path(directory) / "bundle", config)
            self.assertEqual(destination.suffix, ".zip")
            with zipfile.ZipFile(destination) as bundle:
                self.assertEqual(set(bundle.namelist()), {"README.txt", NOTEBETTER_CONFIG_PATH, RESOURCE_PACK_PATH})
                mappings = json.loads(bundle.read(NOTEBETTER_CONFIG_PATH))["mappings"]
                self.assertEqual(mappings[0], {"block": "minecraft:diamond_block", "sound": {
                    "sound": "nbs2save:instruments/test_bell", "volume": 1.0, "pitch": 0.5}})
                self.assertEqual(mappings[1]["sound"]["pitch"], 2.0)
                readme = bundle.read("README.txt").decode("utf-8")
                self.assertIn("https://github.com/chsbuffer/NoteBetter", readme)
                self.assertIn("客户端", readme)
                self.assertIn("1.21.5", readme)
                with zipfile.ZipFile(io.BytesIO(bundle.read(RESOURCE_PACK_PATH))) as pack:
                    self.assertEqual(json.loads(pack.read("pack.mcmeta"))["pack"]["pack_format"], 55)
                    events = json.loads(pack.read("assets/nbs2save/sounds.json"))
                    self.assertEqual(events["instruments/test_bell"]["sounds"][0]["name"], "nbs2save:instruments/test_bell")
                    self.assertEqual(pack.read("assets/nbs2save/sounds/instruments/test_bell.ogg"), MONO_SAMPLE.read_bytes())
                    self.assertIn("assets/other/sounds.json", pack.namelist())

    def test_custom_sample_root_pitch_matches_exported_note_pitch(self):
        for root_key in (0, 33, 45, 57, 87):
            for key in (33, 45, 57):
                note_pitch = int(get_note_block_info(Note(0, 0, 16, key), [instrument(root_key=root_key)])[2])
                actual = 2 ** ((45 - root_key) / 12) * 2 ** ((note_pitch - 12) / 12)
                self.assertTrue(math.isclose(actual, 2 ** ((key - root_key) / 12)))

    def test_all_schematic_layouts_and_preview_use_custom_base_blocks(self):
        notes = [Note(0, 0, 16, 45, panning=0), Note(1, 0, 16, 57, panning=50)]
        for mode in ("default", "staircase", "staircase_up"):
            config = {"type": "schematic", "output_file": "unused", "data_version": Version.JE_1_21_4,
                      "custom_instruments": [instrument(sound_file="missing.ogg")]}
            processor = SchematicProcessor(notes, 1, config, {0: group(mode)})
            with patch("mcschematic.MCSchematic.save"):
                processor.process()
            schem = processor.output_strategy.schem
            exported = {position: schem.getBlockDataAt(position)
                        for position in schem.getStructure().getBlockStates()}
            bases = {position for position, state in exported.items() if state == "minecraft:diamond_block"}
            self.assertEqual(len(bases), 2)
            scene = build_preview(notes, {0: group(mode)}, config, global_max_tick=1)
            preview_bases = {block.position for block in scene.blocks if block.blockstate == "minecraft:diamond_block"}
            self.assertEqual(preview_bases, bases)
            for x, y, z in bases:
                self.assertIn("instrument=harp", exported[(x, y + 1, z)])

    def test_mcfunction_export_uses_same_custom_note_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "song"
            config = {"type": "mcfunction", "output_file": str(output), "custom_instruments": [instrument()]}
            processor = McFunctionProcessor([Note(0, 0, 16, 45)], 0, config, {0: group("default")})
            processor.process()
            commands = output.with_suffix(".mcfunction").read_text(encoding="utf-8")
            self.assertIn("setblock 10 64 -8 note_block[note=12,instrument=harp]", commands)
            self.assertIn("setblock 10 63 -8 minecraft:diamond_block", commands)


if __name__ == "__main__":
    unittest.main()
