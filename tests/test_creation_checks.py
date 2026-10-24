"""Authoring checks must describe real omitted notes and unsupported exports."""

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pynbs

from nbs2save.core.creation_checks import check_creation


class CreationChecksTests(unittest.TestCase):
    def setUp(self):
        self.song = pynbs.new_file()
        self.song.notes = [pynbs.Note(0, 0, instrument=0, key=45), pynbs.Note(2, 1, instrument=0, key=20)]
        self.groups = {0: {"base_coords": (0, 64, 0), "layers": [0], "generation_mode": "default"}}

    def test_unassigned_notes_are_counted_without_pitch_warning_for_omitted_notes(self):
        before = deepcopy(self.groups)
        issues = check_creation(self.song, self.groups, {})
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].title, "1 个音符尚未分组")
        self.assertIn("轨道 1", issues[0].detail)
        self.assertEqual(self.groups, before)

    def test_pitch_and_staircase_export_issues_are_actionable(self):
        self.groups[0]["layers"] = [0, 1]
        self.groups[0]["generation_mode"] = "staircase_up"
        issues = check_creation(self.song, self.groups, {"type": "mcfunction"})
        self.assertEqual([i.severity for i in issues], ["error", "warning"])
        self.assertIn("Schematic", issues[0].detail)
        self.assertIn("note=0", issues[1].detail)

    def test_duplicated_tracks_and_origins_are_explicit(self):
        self.groups[1] = deepcopy(self.groups[0])
        issues = check_creation(self.song, self.groups, {})
        self.assertTrue(any(i.severity == "info" and "重复" in i.title for i in issues))
        self.assertTrue(any("同一起点" in i.title for i in issues))

    def test_unconfigured_custom_and_missing_used_sample_are_distinct(self):
        self.song.notes = [pynbs.Note(0, 0, instrument=16, key=45)]
        self.assertTrue(any("尚未配置" in i.title for i in check_creation(self.song, self.groups, {})))
        config = {"custom_instruments": [{"nbs_id": 16, "name": "Bell", "base_block": "diamond_block", "sound_id": "test:bell", "root_key": 45, "sound_file": "missing_sample.ogg"}]}
        issues = check_creation(self.song, self.groups, config)
        self.assertTrue(any(i.severity == "error" and "找不到采样" in i.title for i in issues))
        self.assertFalse(any("尚未配置" in i.title for i in issues))

    def test_unused_custom_sample_does_not_block_current_song(self):
        self.song.notes = [pynbs.Note(0, 0, instrument=0, key=45)]
        config = {"custom_instruments": [{"nbs_id": 16, "name": "Unused", "base_block": "diamond_block", "sound_id": "test:bell", "root_key": 45, "sound_file": "missing_sample.ogg"}]}
        self.assertEqual(check_creation(self.song, self.groups, config), [])


if __name__ == "__main__":
    unittest.main()
