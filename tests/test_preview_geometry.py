"""Preview geometry is checked against the real export strategies, in memory."""

import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcschematic import Version
from pynbs import Note

from nbs2save.core.mcfunction import McFunctionProcessor
from nbs2save.core.preview import build_preview
from nbs2save.core.schematic import SchematicOutputStrategy, SchematicProcessor


def group(layers=(0, 1), mode="default", offset="pan", coords=(10, 64, -8)):
    return {
        "layers": list(layers),
        "base_coords": tuple(map(str, coords)),
        "block": {"base": "minecraft:iron_block", "cover": "redstone_lamp"},
        "generation_mode": mode,
        "offset_mode": offset,
    }


def normalized(state):
    return state if ":" in state.split("[", 1)[0] else "minecraft:" + state


def scene_map(scene):
    return {block.position: block.blockstate for block in scene.blocks}


def real_schematic(notes, groups, max_tick):
    config = {"type": "schematic", "output_file": "unused", "data_version": Version.JE_1_21_4}
    processor = SchematicProcessor(notes, max_tick, config, groups)
    # Only serialization is disabled: initialization, processors and all actual
    # MCSchematic writes run exactly as during export.
    with patch("mcschematic.MCSchematic.save", side_effect=AssertionError("unexpected save")):
        processor.output_strategy.initialize(processor)
        processor._process_groups()
    schem = processor.output_strategy.schem
    blocks = {}
    for position in schem.getStructure().getBlockStates():
        state = normalized(schem.getBlockDataAt(position))
        if state.split("[", 1)[0] not in {"minecraft:air", "minecraft:cave_air", "minecraft:void_air"}:
            blocks[position] = state
    return blocks


def cropped_schematic(notes, groups, max_tick, start, end):
    windows = [
        (int(cfg["base_coords"][0]) + start * 2 - 1,
         int(cfg["base_coords"][0]) + end * 2)
        for cfg in groups.values()
    ]
    return {
        pos: state for pos, state in real_schematic(notes, groups, max_tick).items()
        if any(first <= pos[0] <= last for first, last in windows)
    }


class PreviewGeometryTests(unittest.TestCase):
    def setUp(self):
        self.notes = [
            Note(0, 0, 0, 33),
            Note(2, 0, 3, 45, velocity=90, panning=30),
            Note(2, 1, 11, 57, velocity=70, panning=-50),
            Note(3, 0, 4, 42, velocity=80, panning=10),
            Note(4, 1, 7, 49, velocity=50, panning=-10),
        ]

    def test_matches_actual_schematic_for_all_layout_and_offset_modes(self):
        for mode in ("default", "staircase", "staircase_up"):
            for offset in ("pan", "volume"):
                with self.subTest(mode=mode, offset=offset):
                    groups = {"a": group(mode=mode, offset=offset)}
                    actual = build_preview(self.notes, groups, global_max_tick=6)
                    self.assertEqual(scene_map(actual), real_schematic(self.notes, groups, 6))
                    self.assertTrue(any(b.blockstate == "minecraft:barrier" for b in actual.blocks))
                    self.assertEqual(actual.end_tick, 6)

    def test_mixed_group_modes_share_final_scene(self):
        groups = {
            0: group(layers=(0,), coords=(10, 64, -8)),
            1: group(layers=(1,), mode="staircase", coords=(12, 65, -5)),
            2: group(layers=(0,), mode="staircase_up", coords=(10, 64, -8)),
        }
        actual = build_preview(self.notes, groups, global_max_tick=6)
        self.assertEqual(scene_map(actual), real_schematic(self.notes, groups, 6))
        self.assertEqual(actual.group_count, 3)
        self.assertGreater(actual.overwritten_blocks, 0)
        last_note = next(b for b in actual.blocks if b.position == (10, 64, -8))
        self.assertEqual(last_note.group_id, 2)

    def test_later_group_air_removes_earlier_blocks(self):
        erase = group(layers=())
        erase["block"] = {"base": "air", "cover": "minecraft:air"}
        groups = {"first": group(), "erase": erase}
        actual = build_preview(self.notes, groups, global_max_tick=4)
        self.assertEqual(scene_map(actual), real_schematic(self.notes, groups, 4))
        self.assertNotIn((10, 64, -8), scene_map(actual))
        repeater = next(b for b in actual.blocks if b.position == (9, 64, -8))
        self.assertEqual(repeater.group_id, "erase")

    def test_window_preserves_world_tick_coordinates_and_matches_export_crop(self):
        groups = {0: group(mode="staircase_up")}
        actual = build_preview(self.notes, groups, start_tick=2, end_tick=3, global_max_tick=6)
        exported = real_schematic(self.notes, groups, 6)
        expected = {p: s for p, s in exported.items() if 13 <= p[0] <= 16}
        self.assertEqual(scene_map(actual), expected)
        self.assertEqual(actual.visible_notes, 3)
        self.assertEqual(actual.total_notes, 5)
        self.assertEqual(actual.bounds[0][0], 13)
        self.assertEqual(actual.bounds[1][0], 16)

    def test_far_window_bounds_generation_cost(self):
        notes = [Note(900_000, 0, 0, 33)]
        actual = build_preview(notes, {0: group()}, start_tick=900_000,
                               end_tick=900_002, global_max_tick=1_000_000)
        self.assertEqual(len(actual.blocks), 12)
        self.assertEqual(actual.written_blocks, 14)
        self.assertIn((1_800_010, 64, -8), scene_map(actual))

    def test_other_tick_of_later_group_overwrites_selected_note(self):
        notes = [Note(0, 0, 0, 33), Note(1, 1, 3, 45)]
        groups = {
            0: group(layers=(0,), coords=(0, 64, 0)),
            1: group(layers=(1,), coords=(-2, 64, 0)),
        }
        actual = build_preview(notes, groups, start_tick=0, end_tick=0, global_max_tick=1)
        self.assertEqual(scene_map(actual), cropped_schematic(notes, groups, 1, 0, 0))
        overlapped = next(block for block in actual.blocks if block.position == (0, 64, 0))
        self.assertEqual(overlapped.group_id, 1)
        self.assertIn("instrument=snare", overlapped.blockstate)
        # This statistic intentionally describes the selected time interval.
        self.assertEqual(actual.visible_notes, 1)

    def test_other_tick_air_write_clears_selected_note(self):
        erase = group(layers=(), coords=(-2, 64, 0))
        erase["block"] = {"base": "air", "cover": "air"}
        notes = [Note(0, 0, 0, 33)]
        groups = {0: group(layers=(0,), coords=(0, 64, 0)), 1: erase}
        actual = build_preview(notes, groups, start_tick=0, end_tick=0, global_max_tick=1)
        self.assertNotIn((0, 64, 0), scene_map(actual))
        self.assertEqual(scene_map(actual), cropped_schematic(notes, groups, 1, 0, 0))

    def test_negative_odd_origins_and_disjoint_windows_match_full_export_crop(self):
        groups = {
            0: group(layers=(0,), coords=(-101, 64, -8)),
            1: group(layers=(1,), mode="staircase", coords=(80, 64, -8)),
            2: group(layers=(2,), mode="staircase_up", coords=(-16, 64, -8)),
        }
        notes = [
            Note(2, 0, 3, 41, panning=30),
            Note(92, 0, 0, 33, panning=-30),
            Note(2, 1, 11, 48, panning=-50),
            Note(49, 2, 7, 57, panning=40),
        ]
        actual = build_preview(notes, groups, start_tick=2, end_tick=3, global_max_tick=100)
        self.assertEqual(scene_map(actual), cropped_schematic(notes, groups, 100, 2, 3))
        self.assertFalse(any(-94 <= b.position[0] <= -14 for b in actual.blocks))
        self.assertFalse(any(-9 <= b.position[0] <= 82 for b in actual.blocks))

    def test_far_origins_and_other_tick_overwrites_keep_generation_bounded(self):
        groups = {
            0: group(layers=(0,), coords=(0, 64, 0)),
            1: group(layers=(1,), coords=(-1_800_000, 64, 0)),
        }
        notes = [Note(900_000, 0, 0, 33), Note(1_800_000, 1, 3, 45)]
        generated_ticks = []
        original = SchematicOutputStrategy.write_base_structures

        def counted(strategy, processor, tick):
            generated_ticks.append(tick)
            original(strategy, processor, tick)

        with patch.object(SchematicOutputStrategy, "write_base_structures", new=counted):
            actual = build_preview(notes, groups, start_tick=900_000, end_tick=900_002,
                                   global_max_tick=2_000_000)
        self.assertEqual(len(generated_ticks), 12)
        self.assertEqual(len(actual.blocks), 25)  # sand support adds one barrier
        self.assertLess(actual.written_blocks, 60)
        overlapped = next(b for b in actual.blocks if b.position == (1_800_000, 64, 0))
        self.assertEqual(overlapped.group_id, 1)
        self.assertIn("instrument=snare", overlapped.blockstate)

    def test_preview_never_opens_output_files_for_any_strategy(self):
        for output_type in ("schematic", "mcfunction"):
            modes = ("default",) if output_type == "mcfunction" else ("default", "staircase", "staircase_up")
            for mode in modes:
                with self.subTest(output_type=output_type, mode=mode):
                    with patch("builtins.open", side_effect=AssertionError("unexpected file I/O")), \
                         patch("mcschematic.MCSchematic.save", side_effect=AssertionError("unexpected save")):
                        data = build_preview(self.notes, {0: group(mode=mode)}, {"type": output_type})
                    self.assertTrue(data.blocks)

    def test_mcfunction_staircases_report_unsupported_final_output(self):
        for mode in ("staircase", "staircase_up"):
            for mixed in (False, True):
                with self.subTest(mode=mode, mixed=mixed):
                    groups = {0: group(mode=mode)}
                    if mixed:
                        groups[1] = group(mode="default")
                    with patch("builtins.open", side_effect=AssertionError("unexpected file I/O")), \
                         self.assertRaisesRegex(ValueError, "阶梯模式暂仅支持 schematic 结构预览"):
                        build_preview(self.notes, groups, {"type": "mcfunction"})
        empty = build_preview(None, {0: group(mode="staircase")}, {"type": "mcfunction"})
        self.assertFalse(empty.has_song)
        self.assertEqual(empty.blocks, ())

    def test_no_song_has_no_invented_structure(self):
        actual = build_preview(None, {0: group()}, global_max_tick=64, end_tick=63)
        self.assertEqual(actual.blocks, ())
        self.assertIsNone(actual.bounds)
        self.assertFalse(actual.has_song)

    def test_loaded_empty_song_includes_clock_and_header_trailing_ticks(self):
        actual = build_preview([], {0: group()}, global_max_tick=3)
        self.assertTrue(actual.has_song)
        self.assertEqual(len(actual.blocks), 16)
        self.assertEqual(actual.end_tick, 3)
        self.assertEqual(actual.visible_notes, 0)

    def test_conflicting_notes_propagate_export_error(self):
        notes = [Note(4, 0, 0, 33), Note(4, 1, 1, 34)]
        with self.assertRaisesRegex(Exception, "位置冲突.*Tick 4"):
            build_preview(notes, {0: group()}, start_tick=4, end_tick=4)
        self.assertEqual(len(build_preview(notes, {0: group()}, end_tick=3).blocks), 16)

    def test_inputs_are_not_modified_by_temporary_preview_coordinates(self):
        groups = {0: group()}
        previous = copy.deepcopy(groups)
        notes_before = copy.deepcopy(self.notes)
        build_preview(self.notes, groups, {"type": "schematic"})
        self.assertEqual(groups, previous)
        self.assertEqual(self.notes, notes_before)

    def test_mcfunction_matches_actual_saved_commands(self):
        groups = {0: group()}
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "song")
            processor = McFunctionProcessor(self.notes, 6, {"type": "mcfunction", "output_file": path}, groups)
            processor.process()
            commands = Path(path + ".mcfunction").read_text(encoding="utf-8").splitlines()
        expected = {}
        for command in filter(None, commands):
            parts = command.split()
            if parts[0] == "setblock":
                expected[tuple(map(int, parts[1:4]))] = normalized(parts[4])
            elif parts[0] == "fill":
                x1, y1, z1, x2, y2, z2 = map(int, parts[1:7])
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    for y in range(min(y1, y2), max(y1, y2) + 1):
                        for z in range(min(z1, z2), max(z1, z2) + 1):
                            expected[x, y, z] = normalized(parts[7])
        actual = build_preview(self.notes, groups, {"type": "mcfunction"}, global_max_tick=6)
        self.assertEqual(scene_map(actual), expected)

    def test_invalid_or_outside_range(self):
        with self.assertRaises(ValueError):
            build_preview(self.notes, {0: group()}, start_tick=-1)
        with self.assertRaises(ValueError):
            build_preview(self.notes, {0: group()}, start_tick=3, end_tick=2)
        actual = build_preview(self.notes, {0: group()}, start_tick=10, end_tick=20)
        self.assertEqual(actual.blocks, ())
        self.assertIsNone(actual.bounds)


if __name__ == "__main__":
    unittest.main()
