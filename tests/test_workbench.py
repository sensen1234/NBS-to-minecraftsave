"""Exercise multi-group layout transactions and mouse interaction in both views."""

from copy import deepcopy
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pynbs
from PyQt6.QtCore import QPoint, QPointF, QThreadPool, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialog
from unittest.mock import patch

from nbs2save.core.preview import build_preview
from nbs2save.gui.coordinate_picker import CoordinatePickerDialog, LayoutToolsDialog


class WorkbenchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "layout.nbs"
        self.song = pynbs.new_file()
        self.song.layers = [pynbs.Layer(0), pynbs.Layer(1)]
        self.song.notes = [pynbs.Note(0, 0, 0, 45), pynbs.Note(0, 1, 1, 45)]
        self.song.save(str(self.path))
        self.groups = {
            0: {"base_coords": ("0", "64", "0"), "layers": [0],
                "block": {"base": "stone", "cover": "redstone_lamp"},
                "generation_mode": "default", "offset_mode": "none"},
            1: {"base_coords": ("20", "64", "15"), "layers": [1],
                "block": {"base": "glass", "cover": "redstone_lamp"},
                "generation_mode": "default", "offset_mode": "none"},
        }
        self.original = deepcopy(self.groups)
        self.dialogs = []

    def tearDown(self):
        for dialog in self.dialogs:
            dialog.reject()
        QThreadPool.globalInstance().waitForDone(5000)
        self.app.processEvents()

    def dialog(self):
        dialog = CoordinatePickerDialog(0, self.groups, input_file=str(self.path))
        self.dialogs.append(dialog)
        dialog.show()
        QTest.qWait(60)
        return dialog

    def wait_for_data(self, dialog, previous=None):
        deadline = time.monotonic() + 5
        while dialog._preview_data is None or dialog._preview_data is previous or dialog._preview_busy:
            if time.monotonic() > deadline:
                self.fail(dialog.preview_summary.text())
            QTest.qWait(10)
        self.app.processEvents()
        return dialog._preview_data

    @staticmethod
    def placements(data, gid):
        return {block.position: block.blockstate for block in data.blocks if block.group_id == gid}

    def test_switching_groups_preserves_all_edits_and_builds_translated_geometry(self):
        dialog = self.dialog()
        changes = []
        ready = []
        dialog.coordinatesChanged.connect(changes.append)
        dialog.previewReady.connect(lambda song, data: ready.append((song, data)))
        dialog.spin_x.setValue(7)
        dialog.spin_y.setValue(66)
        dialog.group_selector.setCurrentIndex(1)
        self.assertEqual(dialog.selected_group_id, 1)
        dialog.spin_z.setValue(25)
        dialog.select_group(0)
        self.assertEqual((dialog.spin_x.value(), dialog.spin_y.value(), dialog.spin_z.value()), (7, 66, 0))
        self.assertEqual(dialog.get_coords(), (7, 66, 0))
        self.assertEqual(dialog.get_all_coords(), {0: (7, 66, 0), 1: (20, 64, 25)})
        self.assertEqual(changes[-1], dialog.get_all_coords())
        self.assertEqual(self.groups, self.original)
        dialog.segWidget.setCurrentItem("3d")
        data = self.wait_for_data(dialog)
        baseline = build_preview(self.song.notes, self.original)
        for gid, delta in ((0, (7, 2, 0)), (1, (0, 0, 10))):
            expected = {tuple(xyz[i] + delta[i] for i in range(3)): state
                        for xyz, state in self.placements(baseline, gid).items()}
            self.assertEqual(self.placements(data, gid), expected)
        self.assertIs(ready[-1][1], data)
        self.assertIs(dialog.load_preview_song(), dialog.get_preview_song())
        camera = (dialog.preview3d._center, dialog.preview3d._scale, dialog.preview3d._yaw)
        dialog.select_group(1)
        self.assertIs(dialog._preview_data, data)
        self.assertEqual(camera, (dialog.preview3d._center, dialog.preview3d._scale, dialog.preview3d._yaw))
        self.assertEqual(len(ready), 1)

    def test_cancel_discards_even_confirmed_changes_and_apply_returns_all_groups(self):
        dialog = self.dialog()
        dialog.spin_x.setValue(200)
        dialog._btn_ok.click()
        self.assertTrue(dialog._confirmed)
        dialog.cancel_button.click()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)
        self.assertEqual(self.groups, self.original)
        applied = self.dialog()
        applied.spin_x.setValue(100)
        applied.select_group(1)
        applied.spin_y.setValue(75)
        applied.apply_button.click()
        self.assertEqual(applied.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(applied.get_all_coords(), {0: (100, 64, 0), 1: (20, 75, 15)})
        self.assertEqual(applied.get_groups_data()[1]["layers"], [1])
        self.assertEqual(applied.get_groups_data()[1]["base_coords"], ("20", "75", "15"))
        self.assertEqual(applied.get_coords(), (100, 64, 0))
        self.assertEqual(self.groups, self.original)

    def test_2d_mouse_select_and_drag_arbitrary_group_in_each_projection(self):
        dialog = self.dialog()
        for mode, delta, expected in (
            ("south", QPoint(15, -9), (25, 67, 15)),
            ("west", QPoint(-12, 6), (25, 65, 11)),
        ):
            with self.subTest(mode=mode):
                dialog.segWidget.setCurrentItem(mode)
                dialog.select_group(0)
                self.app.processEvents()
                item = dialog._groups_items[1]
                start = dialog.view.mapFromScene(item.pos())
                viewport = dialog.view.viewport()
                QTest.mousePress(viewport, Qt.MouseButton.LeftButton, pos=start)
                QTest.mouseMove(viewport, start + QPoint(delta.x() // 2, delta.y() // 2), 20)
                QTest.mouseMove(viewport, start + delta, 20)
                QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, pos=start + delta)
                self.app.processEvents()
                self.assertEqual(dialog.selected_group_id, 1)
                self.assertEqual(dialog.get_all_coords()[1], expected)
                self.assertEqual(dialog.get_all_coords()[0], (0, 64, 0))
                self.assertEqual(item.pos(), QPointF(expected[0] if mode == "south" else expected[2], -expected[1]))
                self.assertEqual(dialog._history.undo_count, 1 if mode == "south" else 2)
        QTest.keyClick(dialog.view, Qt.Key.Key_Up)
        self.assertEqual(dialog.get_all_coords()[1], (25, 66, 11))
        QTest.keyClick(dialog.view, Qt.Key.Key_Right, Qt.KeyboardModifier.ShiftModifier)
        self.assertEqual(dialog.get_all_coords()[1], (25, 66, 21))
        self.assertEqual(self.groups, self.original)

    def test_3d_block_selection_and_origin_drags_change_real_world_coordinates(self):
        dialog = self.dialog()
        dialog.segWidget.setCurrentItem("3d")
        original = self.wait_for_data(dialog)
        canvas = dialog.preview3d
        clicked = False
        for polygon, _, index in reversed(canvas._screen_faces):
            if canvas._blocks[index].group_id != 1:
                continue
            point = QPointF(sum(p.x() for p in polygon) / 4, sum(p.y() for p in polygon) / 4)
            hit = canvas._block_at(point)
            if canvas._anchor_at(point) is None and hit is not None and canvas._blocks[hit].group_id == 1:
                QTest.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=point.toPoint())
                clicked = True
                break
        self.assertTrue(clicked, "fixture must expose a clickable group 1 block")
        self.assertEqual(dialog.selected_group_id, 1)
        for vertical, coords in ((False, (23, 64, 13)), (True, (23, 68, 13))):
            before = dialog._preview_data
            origin = dialog.get_all_coords()[1]
            start = canvas._project(origin).toPoint()
            end = canvas._project(coords).toPoint()
            modifier = Qt.KeyboardModifier.ShiftModifier if vertical else Qt.KeyboardModifier.NoModifier
            QTest.mousePress(canvas, Qt.MouseButton.LeftButton, modifier, start)
            QTest.mouseMove(canvas, QPoint((start.x() + end.x()) // 2, (start.y() + end.y()) // 2), 20)
            QTest.mouseMove(canvas, end, 20)
            self.assertTrue(dialog._preview_dragging)
            self.assertEqual(dialog.get_all_coords()[1], coords)
            self.assertEqual(canvas._anchors[1], coords)
            QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, modifier, end)
            updated = self.wait_for_data(dialog, before)
            delta = tuple(coords[i] - (20, 64, 15)[i] for i in range(3))
            expected = {tuple(xyz[i] + delta[i] for i in range(3)): state
                        for xyz, state in self.placements(original, 1).items()}
            self.assertEqual(self.placements(updated, 1), expected)
            self.assertEqual(self.placements(updated, 0), self.placements(original, 0))
            self.assertEqual(dialog._history.undo_count, 2 if vertical else 1)
        self.assertFalse(dialog._preview_dragging)
        self.assertEqual(self.groups, self.original)
        dialog.undo_layout()
        self.assertEqual(dialog.get_all_coords()[1], (23, 64, 13))
        dialog.undo_layout()
        self.assertEqual(dialog.get_all_coords()[1], (20, 64, 15))

    def test_history_merges_spin_changes_and_restores_whole_layout(self):
        dialog = self.dialog()
        dialog.spin_x.setValue(1)
        dialog.spin_x.setValue(2)
        dialog.spin_x.setValue(3)
        self.assertEqual(dialog._history.undo_count, 1)
        dialog.spin_z.setValue(4)
        dialog.spin_z.setValue(5)
        self.assertEqual(dialog._history.undo_count, 2)
        dialog.select_group(1)
        dialog.spin_z.setValue(16)
        dialog.spin_z.setValue(17)
        self.assertEqual(dialog._history.undo_count, 3)
        edited = dialog.get_all_coords()
        dialog.restore_initial_layout()
        self.assertEqual(dialog.get_all_coords(), {0: (0, 64, 0), 1: (20, 64, 15)})
        self.assertEqual(dialog._history.undo_count, 4)
        dialog.undo_layout()
        self.assertEqual(dialog.get_all_coords(), edited)
        self.assertEqual(dialog.spin_z.value(), 17)
        dialog.redo_layout()
        self.assertEqual(dialog.get_all_coords(), {0: (0, 64, 0), 1: (20, 64, 15)})
        self.assertEqual(dialog.spin_z.value(), 15)
        self.assertEqual(self.groups, self.original)

    def test_keyboard_undo_redo_from_canvas_and_coordinate_input(self):
        dialog = self.dialog()
        dialog.activateWindow()
        dialog.view.setFocus()
        QTest.qWait(30)
        dialog.spin_x.setValue(5)
        QTest.keyClick(dialog.view, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(dialog.get_all_coords()[0], (0, 64, 0))
        QTest.keyClick(dialog.view, Qt.Key.Key_Z,
                       Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        self.assertEqual(dialog.get_all_coords()[0], (5, 64, 0))
        dialog.spin_z.setFocus()
        QTest.qWait(20)
        dialog.spin_z.setValue(9)
        QTest.keyClick(dialog.spin_z, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(dialog.get_all_coords()[0], (5, 64, 0))
        QTest.keyClick(dialog.spin_z, Qt.Key.Key_Z,
                       Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        self.assertEqual(dialog.get_all_coords()[0], (5, 64, 9))

    def test_batch_tools_preview_validation_and_atomic_apply(self):
        dialog = self.dialog()
        coords = dialog.get_all_coords()
        tools = LayoutToolsDialog(coords, dialog)
        self.dialogs.append(tools)
        self.assertFalse(tools.apply_button.isEnabled())
        tools.delta_spins[0].setValue(4)
        tools.delta_spins[1].setValue(2)
        self.assertEqual(tools.proposed_coords(), {0: (4, 66, 0), 1: (24, 66, 15)})
        self.assertEqual(dialog.get_all_coords(), coords)
        self.assertEqual(self.groups, self.original)
        tools.delta_spins[1].setValue(300)
        self.assertIsNone(tools.proposed_coords())
        self.assertFalse(tools.apply_button.isEnabled())
        self.assertIn("Y", tools.summary.text())
        tools.mode.setCurrentItem("arrange")
        tools.start_z.setValue(-50)
        tools.spacing.setValue(12)
        proposal = {0: (0, 64, -50), 1: (20, 64, -38)}
        self.assertEqual(tools.proposed_coords(), proposal)
        self.assertTrue(tools.apply_button.isEnabled())

        def apply_batch(batch_dialog):
            batch_dialog.mode.setCurrentItem("arrange")
            batch_dialog.start_z.setValue(-50)
            batch_dialog.spacing.setValue(12)
            return QDialog.DialogCode.Accepted

        with patch.object(LayoutToolsDialog, "exec", apply_batch):
            dialog.open_layout_tools()
        self.assertEqual(dialog.get_all_coords(), proposal)
        self.assertEqual(dialog._history.undo_count, 1)
        dialog.undo_layout()
        self.assertEqual(dialog.get_all_coords(), coords)
        dialog.redo_layout()
        self.assertEqual(dialog.get_all_coords(), proposal)
        self.assertEqual(self.groups, self.original)

    def test_listener_marker_uses_world_ear_position_and_minecraft_yaw(self):
        dialog = self.dialog()
        dialog.segWidget.setCurrentItem("3d")
        self.wait_for_data(dialog)
        canvas = dialog.preview3d
        self.app.processEvents()
        image_cache = canvas._cache
        canvas.set_listener((4.5, 65.62, 2.5), 90)
        self.app.processEvents()
        self.assertIs(canvas._cache, image_cache)
        self.assertEqual(canvas._listener_position, (4.5, 65.62, 2.5))
        self.assertAlmostEqual(canvas._listener_forward[0], -1)
        self.assertAlmostEqual(canvas._listener_forward[2], 0)
        marker = canvas.grab().toImage()
        point = canvas._project(canvas._listener_position).toPoint()
        colors = [marker.pixelColor(point + QPoint(x, y)) for x in range(-11, 12) for y in range(-11, 12)]
        self.assertTrue(any(c.red() > 110 and c.blue() > c.green() * 1.4 for c in colors))
        canvas.set_listener((1000, 65.62, -1000), 0)
        canvas.fit_all()
        self.assertTrue(canvas.rect().contains(canvas._project(canvas._listener_position).toPoint()))
        canvas.set_listener(None)
        self.assertIsNone(canvas._listener_position)


if __name__ == "__main__":
    unittest.main()
