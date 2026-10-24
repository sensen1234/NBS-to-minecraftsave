"""Verify atomic coordinate tools and whole-layout undo history."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nbs2save.gui.layout_tools import LayoutHistory, arrange_along_z, translate_all


class LayoutToolsTest(unittest.TestCase):
    def setUp(self):
        self.coords = {7: (10, 64, -20), 3: (-5, 70, 15)}

    def test_translation_preserves_relative_positions_without_mutating_input(self):
        shifted = translate_all(self.coords, (-10, 3, 100))
        self.assertEqual(shifted, {7: (0, 67, 80), 3: (-15, 73, 115)})
        self.assertEqual(tuple(shifted[3][i] - shifted[7][i] for i in range(3)),
                         tuple(self.coords[3][i] - self.coords[7][i] for i in range(3)))
        self.assertEqual(self.coords, {7: (10, 64, -20), 3: (-5, 70, 15)})

    def test_translation_rejects_overflow_atomically_on_every_axis(self):
        for coords, delta, axis in (
            ({0: (0, 64, 0), 1: (30_000_000, 64, 0)}, (1, 0, 0), "X"),
            ({0: (0, -64, 0)}, (0, -1, 0), "Y"),
            ({0: (0, 320, 0)}, (0, 1, 0), "Y"),
            ({0: (0, 64, -30_000_000)}, (0, 0, -1), "Z"),
        ):
            before = dict(coords)
            with self.subTest(axis=axis, delta=delta), self.assertRaisesRegex(ValueError, axis):
                translate_all(coords, delta)
            self.assertEqual(coords, before)
        for delta in ((1.0, 0, 0), (True, 0, 0), (1, 2)):
            with self.subTest(delta=delta), self.assertRaises(ValueError):
                translate_all(self.coords, delta)

    def test_arrangement_uses_group_order_and_preserves_other_axes(self):
        self.assertEqual(arrange_along_z(self.coords, -100, 24),
                         {7: (10, 64, -100), 3: (-5, 70, -76)})
        with self.assertRaises(ValueError):
            arrange_along_z(self.coords, 0, 0)
        with self.assertRaisesRegex(ValueError, "Z"):
            arrange_along_z(self.coords, 30_000_000, 1)
        self.assertEqual(self.coords[3], (-5, 70, 15))

    def test_history_merges_one_edit_and_removes_net_zero_edit(self):
        history = LayoutHistory(self.coords)
        moved = translate_all(self.coords, (1, 0, 0))
        later = translate_all(self.coords, (2, 0, 0))
        history.record(moved, "move", "drag")
        history.record(later, "move", "drag")
        self.assertEqual(history.undo_count, 1)
        self.assertEqual(history.undo(), self.coords)
        self.assertEqual(history.redo(), later)
        history.record(self.coords, "move", "new-drag")
        history.record(later, "move", "new-drag")
        self.assertEqual(history.undo_count, 1)
        self.assertEqual(history.current, later)

    def test_history_branches_and_returns_independent_snapshots(self):
        history = LayoutHistory(self.coords)
        one = translate_all(self.coords, (1, 0, 0))
        two = translate_all(self.coords, (2, 0, 0))
        history.record(one, "first")
        history.record(two, "second")
        self.assertEqual(history.undo_label, "second")
        self.assertEqual(history.undo(), one)
        self.assertEqual(history.redo_label, "second")
        branch = translate_all(self.coords, (0, 1, 0))
        history.record(branch, "branch")
        self.assertEqual(history.redo_count, 0)
        self.assertEqual(history.current, branch)
        returned = history.current
        returned[7] = (999, 999, 999)
        branch[7] = (888, 888, 888)
        self.assertEqual(history.current[7], (10, 65, -20))
        with self.assertRaises(ValueError):
            history.record({7: (0, 64, 0)}, "missing group")

    def test_history_keeps_original_layout_after_undo_limit(self):
        history = LayoutHistory(self.coords, limit=2)
        for amount in range(1, 5):
            history.record(translate_all(self.coords, (amount, 0, 0)), str(amount))
        self.assertEqual(history.undo_count, 2)
        self.assertEqual(history.initial, self.coords)
        self.assertEqual(history.undo(), translate_all(self.coords, (3, 0, 0)))
        self.assertEqual(history.undo(), translate_all(self.coords, (2, 0, 0)))


if __name__ == "__main__":
    unittest.main()
