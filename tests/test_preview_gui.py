"""Real NBS-to-dialog integration checks; run headlessly with unittest."""

from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pynbs
from PyQt6.QtCore import QEvent, QPoint, QPointF, QRectF, QThreadPool, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialog

from nbs2save.core.preview import build_preview
from nbs2save.gui.coordinate_picker import CoordinatePickerDialog
from nbs2save.gui.preview_3d import MinecraftPreviewWidget


class PreviewDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.nbs_path = Path(self.tempdir.name) / "preview.nbs"
        song = pynbs.new_file(song_name="3D integration fixture")
        song.layers = [pynbs.Layer(0), pynbs.Layer(1)]
        song.notes = [
            pynbs.Note(tick=0, layer=0, instrument=0, key=45, panning=20),
            pynbs.Note(tick=20, layer=0, instrument=3, key=33, panning=-30),
            pynbs.Note(tick=80, layer=0, instrument=1, key=57, panning=0),
            pynbs.Note(tick=80, layer=1, instrument=2, key=40, panning=0),
        ]
        song.save(str(self.nbs_path))
        self.groups = {
            0: {
                "base_coords": ("10", "64", "30"),
                "layers": [0],
                "block": {"base": "stone", "cover": "redstone_lamp"},
                "generation_mode": "default",
                "offset_mode": "pan",
            },
            1: {
                "base_coords": ("-100", "80", "-50"),
                "layers": [1],
                "block": {"base": "glass", "cover": "redstone_lamp"},
                "generation_mode": "default",
                "offset_mode": "pan",
            },
        }
        self.dialogs = []

    def tearDown(self):
        for dialog in self.dialogs:
            dialog.close()
        QThreadPool.globalInstance().waitForDone(5000)
        self.app.processEvents()

    def make_dialog(self, *, input_file=None):
        dialog = CoordinatePickerDialog(
            0, self.groups,
            input_file=str(self.nbs_path) if input_file is None else input_file,
            preview_config={"type": "schematic"},
        )
        self.dialogs.append(dialog)
        dialog.show()
        QTest.qWait(60)
        return dialog

    def wait_until(self, condition, message="preview did not finish", timeout=5):
        deadline = time.monotonic() + timeout
        while not condition():
            if time.monotonic() >= deadline:
                self.fail(message() if callable(message) else message)
            QTest.qWait(10)
        self.app.processEvents()

    def wait_for_data(self, dialog, previous=None):
        self.wait_until(
            lambda: (
                dialog._preview_data is not None
                and dialog._preview_data is not previous
                and not dialog._preview_busy
            ),
            lambda: dialog.preview_summary.text(),
        )
        return dialog._preview_data

    @staticmethod
    def blocks(data, group_id=None):
        return {
            block.position: block.blockstate
            for block in data.blocks
            if group_id is None or block.group_id == group_id
        }

    def test_switch_to_3d_loads_actual_blocks_and_world_coordinates(self):
        original = deepcopy(self.groups)
        dialog = self.make_dialog()
        self.assertIs(dialog.view_stack.currentWidget(), dialog.view)
        dialog.segWidget.setCurrentItem("3d")
        data = self.wait_for_data(dialog)
        self.assertIs(dialog.view_stack.currentWidget(), dialog.preview3d)
        self.assertEqual((data.start_tick, data.end_tick), (0, 63))
        self.assertEqual(data.visible_notes, 2)
        blocks = self.blocks(data)
        self.assertEqual(
            blocks[(10, 64, 32)], "minecraft:note_block[note=12,instrument=harp]"
        )
        self.assertEqual(blocks[(10, 63, 32)], "minecraft:dirt")
        self.assertEqual(
            blocks[(50, 64, 27)], "minecraft:note_block[note=0,instrument=snare]"
        )
        self.assertEqual(blocks[(50, 63, 27)], "minecraft:sand")
        self.assertEqual(blocks[(50, 62, 27)], "minecraft:barrier")
        self.assertEqual(blocks[(9, 64, 30)], "minecraft:repeater[delay=1,facing=west]")
        self.assertIn((-100, 80, -50), self.blocks(data, 1))
        self.assertEqual(self.groups, original)

    def test_coordinate_edits_move_only_target_group_without_saving_config(self):
        original = deepcopy(self.groups)
        dialog = self.make_dialog()
        dialog.segWidget.setCurrentItem("3d")
        initial = self.wait_for_data(dialog)
        dialog.spin_x.setValue(17)
        dialog.spin_y.setValue(69)
        dialog.spin_z.setValue(19)
        moved = self.wait_for_data(dialog, initial)
        translated = {
            (x + 7, y + 5, z - 11): state
            for (x, y, z), state in self.blocks(initial, 0).items()
        }
        self.assertEqual(self.blocks(moved, 0), translated)
        self.assertEqual(self.blocks(moved, 1), self.blocks(initial, 1))
        self.assertEqual(dialog.get_coords(), (17, 69, 19))
        self.assertEqual(self.groups, original)

    def test_edits_in_both_2d_views_refresh_when_returning_to_3d(self):
        dialog = self.make_dialog()
        dialog.segWidget.setCurrentItem("3d")
        initial = self.wait_for_data(dialog)
        dialog.segWidget.setCurrentItem("south")
        dialog.spin_x.setValue(30)
        dialog.segWidget.setCurrentItem("west")
        dialog.spin_z.setValue(-20)
        dialog.segWidget.setCurrentItem("3d")
        updated = self.wait_for_data(dialog, initial)
        self.assertIn((30, 64, -18), self.blocks(updated, 0))
        self.assertNotIn((10, 64, 32), self.blocks(updated, 0))

    def test_editing_z_requires_confirmation_again_in_every_view(self):
        for view in ("south", "west", "3d"):
            with self.subTest(view=view):
                dialog = self.make_dialog()
                dialog.segWidget.setCurrentItem(view)
                dialog._btn_ok.click()
                dialog.spin_z.setValue(dialog.spin_z.value() + 1)
                self.assertFalse(dialog._confirmed)
                self.assertNotIn("已保存", dialog._btn_ok.text())
                dialog._try_close()
                self.assertTrue(dialog.isVisible())
                self.assertIn("请先", dialog._confirm_label.text())
                dialog._btn_ok.click()
                dialog._try_close()
                self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)

    def test_without_nbs_shows_explicit_empty_state(self):
        dialog = self.make_dialog(input_file="")
        dialog.segWidget.setCurrentItem("3d")
        self.app.processEvents()
        self.assertIs(dialog.view_stack.currentWidget(), dialog.preview3d)
        self.assertIsNone(dialog._preview_data)
        self.assertFalse(dialog._preview_busy)
        self.assertIn("未加载 NBS", dialog.preview_summary.text())
        dialog.spin_z.setValue(42)
        self.wait_until(lambda: "未加载 NBS" in dialog.preview_summary.text())
        self.assertIsNone(dialog._preview_data)

    def test_range_controls_keep_original_tick_offsets(self):
        dialog = self.make_dialog()
        dialog.segWidget.setCurrentItem("3d")
        first = self.wait_for_data(dialog)
        dialog.preview_span.setCurrentIndex(0)  # 16 tick
        short = self.wait_for_data(dialog, first)
        self.assertEqual((short.start_tick, short.end_tick), (0, 15))
        self.assertEqual(short.visible_notes, 1)
        dialog.preview_next.click()
        second = self.wait_for_data(dialog, short)
        self.assertEqual((second.start_tick, second.end_tick), (16, 31))
        self.assertIn((50, 64, 27), self.blocks(second, 0))
        self.assertNotIn((10, 64, 32), self.blocks(second, 0))
        dialog.preview_start.setValue(80)
        tail = self.wait_for_data(dialog, second)
        self.assertEqual((tail.start_tick, tail.end_tick), (80, 80))
        self.assertIn((170, 64, 30), self.blocks(tail, 0))
        self.assertFalse(dialog.preview_next.isEnabled())

    def test_conflicting_notes_clear_successful_scene_and_show_error(self):
        dialog = self.make_dialog()
        dialog.segWidget.setCurrentItem("3d")
        self.wait_for_data(dialog)
        self.groups[0]["layers"] = [0, 1]
        dialog.preview_start.setValue(80)
        self.wait_until(lambda: "预览失败" in dialog.preview_summary.text())
        self.assertIn("位置冲突", dialog.preview_summary.text())
        self.assertIsNone(dialog._preview_data)
        self.assertFalse(dialog.preview3d._blocks)
        self.assertFalse(dialog.preview3d._faces)

    def test_renderer_hover_reports_actual_world_block_after_camera_changes(self):
        song = pynbs.read(str(self.nbs_path))
        data = build_preview(
            song.notes, {0: self.groups[0]}, end_tick=0, global_max_tick=80
        )
        canvas = MinecraftPreviewWidget()
        self.dialogs.append(canvas)
        canvas.resize(800, 600)
        canvas.show()
        canvas.set_preview(data, {0: (10, 64, 30)}, 0, reset_camera=True)
        messages = []
        canvas.hoverInfoChanged.connect(messages.append)
        QTest.qWait(30)

        note_top = (10.5, 65, 32.5)
        QTest.mouseMove(canvas, QPoint(1, 1))
        QTest.mouseMove(canvas, canvas._project(note_top).toPoint(), 20)
        self.assertTrue(messages)
        self.assertIn("(10, 64, 32)", messages[-1])
        self.assertIn("note=12", messages[-1])
        self.assertIn("instrument=harp", messages[-1])

        first = canvas._project((10, 64, 32))
        second = canvas._project((11, 64, 32))
        original_distance = (second - first).manhattanLength()
        canvas.zoom(1.5)
        first = canvas._project((10, 64, 32))
        second = canvas._project((11, 64, 32))
        self.assertAlmostEqual((second - first).manhattanLength(), original_distance * 1.5)

        before_rotation = canvas._project(note_top)
        QTest.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(400, 300))
        QTest.mouseMove(canvas, QPoint(450, 315), 20)
        QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPoint(450, 315))
        QTest.qWait(30)
        self.assertGreater((canvas._project(note_top) - before_rotation).manhattanLength(), 1)
        QTest.mouseMove(canvas, QPoint(1, 1))
        QTest.mouseMove(canvas, canvas._project(note_top).toPoint(), 20)
        self.assertIn("(10, 64, 32)", messages[-1])

        canvas.set_preview(None, {0: (10, 64, 30)}, 0)
        QTest.qWait(20)
        self.assertEqual(messages[-1], "")
        self.assertFalse(canvas._blocks)
        self.assertFalse(canvas._faces)

    def test_renderer_fit_and_zoom_support_world_border_distances(self):
        canvas = MinecraftPreviewWidget()
        self.dialogs.append(canvas)
        canvas.resize(900, 600)
        anchors = {0: (-30000000, 64, -30000000), 1: (30000000, 64, 30000000)}
        data = SimpleNamespace(blocks=tuple(
            SimpleNamespace(position=xyz, blockstate="minecraft:iron_block", group_id=gid)
            for gid, xyz in anchors.items()
        ))
        canvas.set_preview(data, anchors, 0, reset_camera=True)
        viewport = QRectF(canvas.rect())
        for point in anchors.values():
            self.assertTrue(viewport.contains(canvas._project(point)))
        self.assertLess(canvas._scale, .004)
        # Zooming out from the fitted view must not snap back to the old floor.
        before = (canvas._project(anchors[1]) - canvas._project(anchors[0])).manhattanLength()
        canvas.zoom(.5)
        after = (canvas._project(anchors[1]) - canvas._project(anchors[0])).manhattanLength()
        self.assertAlmostEqual(after, before * .5)

    def test_renderer_scene_replacement_discards_picking_before_repaint(self):
        canvas = MinecraftPreviewWidget()
        self.dialogs.append(canvas)
        canvas.resize(900, 600)
        canvas.show()
        data = SimpleNamespace(blocks=tuple(
            SimpleNamespace(position=(x, 64, 0), blockstate="minecraft:iron_block", group_id=0)
            for x in range(20)
        ))
        smaller = SimpleNamespace(blocks=data.blocks[:1])
        for replacement in (None, smaller):
            with self.subTest(empty=replacement is None):
                canvas.set_preview(data, {}, 0, reset_camera=True)
                self.app.processEvents()
                polygon, _, index = canvas._screen_faces[-1]
                self.assertGreater(index, 0)
                point = QPointF(sum(p.x() for p in polygon) / 4, sum(p.y() for p in polygon) / 4)
                canvas.set_preview(replacement, {}, 0)
                # Deliver input synchronously, before Qt can rebuild the image.
                event = QMouseEvent(QEvent.Type.MouseMove, point, point,
                                    Qt.MouseButton.NoButton, Qt.MouseButton.NoButton,
                                    Qt.KeyboardModifier.NoModifier)
                canvas.mouseMoveEvent(event)
                self.assertIsNone(canvas._hover)
                self.assertEqual(canvas._hover_text, "")

    def test_reload_reads_the_updated_nbs_file(self):
        dialog = self.make_dialog()
        dialog.segWidget.setCurrentItem("3d")
        initial = self.wait_for_data(dialog)
        song = pynbs.read(str(self.nbs_path))
        song.notes[0].panning = 70
        song.save(str(self.nbs_path))
        dialog._reload_preview()
        reloaded = self.wait_for_data(dialog, initial)
        blocks = self.blocks(reloaded, 0)
        self.assertEqual(blocks[(10, 64, 37)], "minecraft:note_block[note=12,instrument=harp]")
        self.assertEqual(blocks[(10, 64, 32)], "minecraft:redstone_wire[north=side,south=side]")

    def test_edit_during_build_discards_stale_coordinates(self):
        entered = threading.Event()
        release = threading.Event()
        calls = 0

        def delayed_first_build(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                entered.set()
                if not release.wait(5):
                    raise TimeoutError("test did not release preview worker")
            return build_preview(*args, **kwargs)

        dialog = self.make_dialog()
        with patch("nbs2save.core.preview.build_preview", side_effect=delayed_first_build):
            try:
                dialog.segWidget.setCurrentItem("3d")
                self.wait_until(entered.is_set)
                dialog.spin_x.setValue(300)
                dialog.spin_z.setValue(-100)
            finally:
                release.set()
            data = self.wait_for_data(dialog)
        self.assertIn((300, 64, -98), self.blocks(data, 0))
        self.assertNotIn((10, 64, 32), self.blocks(data, 0))
        self.assertGreaterEqual(calls, 2)

    def test_close_during_build_does_not_reopen_or_modify_configuration(self):
        entered = threading.Event()
        release = threading.Event()
        original = deepcopy(self.groups)

        def delayed_build(*args, **kwargs):
            entered.set()
            if not release.wait(5):
                raise TimeoutError("test did not release preview worker")
            return build_preview(*args, **kwargs)

        dialog = self.make_dialog()
        with patch("nbs2save.core.preview.build_preview", side_effect=delayed_build):
            try:
                dialog.segWidget.setCurrentItem("3d")
                self.wait_until(entered.is_set)
                dialog.close()
                self.assertFalse(dialog.isVisible())
            finally:
                release.set()
            self.wait_until(lambda: not dialog._preview_busy)
        self.assertFalse(dialog.isVisible())
        self.assertEqual(self.groups, original)


if __name__ == "__main__":
    unittest.main()
