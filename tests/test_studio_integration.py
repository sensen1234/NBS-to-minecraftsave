"""Project persistence and the real workbench/instrument page integration."""

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from io import BytesIO
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pynbs
from mcschematic import Version
from PyQt6.QtCore import QThreadPool
from PyQt6.QtWidgets import QApplication, QDialog, QTableWidgetItem

from nbs2save.gui.coordinate_picker import CoordinatePickerDialog
from nbs2save.gui.listening_panel import ListeningPanel
from nbs2save.gui.window import MainWindow, _make_json_safe, _restore_from_json


class StudioIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        with patch.object(MainWindow, "load_last_config"):
            self.window = MainWindow()

    def tearDown(self):
        for panel in self.window.findChildren(ListeningPanel):
            panel.shutdown()
        self.window.close()
        QThreadPool.globalInstance().waitForDone(5000)
        self.app.processEvents()

    def add_instrument(self):
        page = self.window.instrumentsInterface
        page.add_instrument()
        page.table.setItem(0, 1, QTableWidgetItem("自定义钢琴"))
        page.table.setItem(0, 2, QTableWidgetItem("diamond_block"))
        return page

    def test_save_collects_unsaved_home_groups_and_instruments(self):
        page = self.add_instrument()
        self.window.homeInterface.setInputFile("uncommitted.nbs")
        self.window.homeInterface.setOutputFile("new-output")
        self.window.homeInterface.setVersion(Version.JE_1_21_4)
        self.window.groupsInterface.table.setItem(0, 1, QTableWidgetItem("123"))
        path = Path(self.directory.name) / "project.json"
        with patch("nbs2save.gui.window.QFileDialog.getSaveFileName", return_value=(str(path), "")):
            self.window.save_config()
        restored, groups = _restore_from_json(json.loads(path.read_text(encoding="utf-8")))
        self.assertEqual(restored["input_file"], "uncommitted.nbs")
        self.assertEqual(restored["output_file"], "new-output")
        self.assertEqual(restored["data_version"], Version.JE_1_21_4)
        self.assertEqual(groups[0]["base_coords"], ("123", "0", "0"))
        self.assertEqual(restored["custom_instruments"][0]["base_block"], "minecraft:diamond_block")
        self.assertEqual(restored["custom_instruments"][0]["name"], "自定义钢琴")
        self.window.config = restored
        self.window.group_config = groups
        self.window._syncUIFromConfig()
        self.assertEqual(page.table.item(0, 1).text(), "自定义钢琴")
        self.assertEqual(page.pack_format.value(), 46)

    def test_invalid_instrument_does_not_start_conversion_or_save_dialog(self):
        page = self.add_instrument()
        page.table.setItem(0, 0, QTableWidgetItem("invalid"))
        with patch.object(self.window, "_settings_error") as error, \
             patch("nbs2save.gui.window.pynbs.read") as read, \
             patch("nbs2save.gui.window.QFileDialog.getSaveFileName") as save:
            self.window.start_conversion()
            self.window.save_config()
        self.assertEqual(error.call_count, 2)
        read.assert_not_called()
        save.assert_not_called()
        self.assertEqual(self.window.config["custom_instruments"], [])

    def test_nbs_import_uses_absolute_custom_ids_and_original_sample_pitch(self):
        path = Path(self.directory.name) / "custom.nbs"
        sample = path.parent / "sample.ogg"
        sample.write_bytes(b"placeholder, import does not decode")
        song = pynbs.new_file()
        song.instruments = [pynbs.Instrument(0, "My piano", "sample.ogg", pitch=40)]
        song.notes = [pynbs.Note(0, 0, instrument=16, key=45)]
        song.save(str(path))
        self.window.homeInterface.setInputFile(str(path))
        page = self.window.instrumentsInterface
        page.import_from_nbs()
        page.import_from_nbs()
        self.assertEqual(page.table.rowCount(), 1)
        entry = page.collect_instruments()[0]
        self.assertEqual((entry["nbs_id"], entry["root_key"]), (16, 40))
        self.assertEqual(Path(entry["sound_file"]), sample.resolve())

    def test_export_button_builds_install_bundle_from_current_table(self):
        page = self.add_instrument()
        fixture = Path(__file__).parent / "fixtures" / "custom_note_mono.ogg"
        page.table.setItem(0, 5, QTableWidgetItem(str(fixture)))
        self.window.homeInterface.setVersion(Version.JE_1_21_4)
        destination = Path(self.directory.name) / "instrument.zip"
        with patch("nbs2save.gui.instruments_interface.QFileDialog.getSaveFileName", return_value=(str(destination), "")), \
             patch.object(page, "_message") as message:
            page.export_pack()
        self.assertEqual(message.call_args.args[0], "导出完成")
        with zipfile.ZipFile(destination) as bundle:
            mapping = json.loads(bundle.read("config/notebetterfabric.json"))
            self.assertEqual(mapping["mappings"][0]["block"], "minecraft:diamond_block")
            with zipfile.ZipFile(BytesIO(bundle.read("resourcepacks/nbs2save-custom-instruments.zip"))) as resource:
                self.assertEqual(json.loads(resource.read("pack.mcmeta"))["pack"]["pack_format"], 46)
                self.assertIn("assets/nbs2save/sounds/custom.instrument_16.ogg", resource.namelist())

    def test_manual_pack_format_is_retained_when_game_version_changes(self):
        page = self.window.instrumentsInterface
        page.auto_format.setChecked(False)
        page.pack_format.setValue(42)
        self.window.homeInterface.setVersion(Version.JE_1_21_4)
        page.save_to_config()
        self.assertEqual(self.window.config["notebetter_pack_format"], 42)
        page.load_from_config()
        self.assertFalse(page.auto_format.isChecked())
        self.assertEqual(page.pack_format.value(), 42)

    def test_workbench_applies_all_groups_and_listening_preferences_together(self):
        self.window.groupsInterface.addGroup()
        self.window.group_config[1]["extra_setting"] = "preserved"

        def edit_and_accept(dialog):
            dialog.spin_x.setValue(42)
            dialog.select_group(1)
            dialog.spin_z.setValue(-99)
            panel = dialog.findChild(ListeningPanel)
            panel.set_listener((42.5, 1.62, -6), 90)
            dialog.accept()
            return QDialog.DialogCode.Accepted

        with patch.object(CoordinatePickerDialog, "exec", edit_and_accept):
            self.window.groupsInterface.openWorkbench()
        self.assertEqual(tuple(map(int, self.window.group_config[0]["base_coords"])), (42, 0, 0))
        self.assertEqual(tuple(map(int, self.window.group_config[1]["base_coords"])), (0, 0, -99))
        self.assertEqual(self.window.group_config[1]["extra_setting"], "preserved")
        self.assertEqual(self.window.config["listening"]["yaw"], 90)
        self.assertEqual(self.window.groupsInterface.table.item(1, 3).text(), "-99")

    def test_cancel_discards_all_workbench_and_nested_listening_changes(self):
        self.window.groupsInterface.addGroup()
        self.window.config["listening"] = {"position": [3, 4, 5], "yaw": 12}
        self.window.collect_settings()
        before = deepcopy(_make_json_safe(self.window.config, self.window.group_config))

        def edit_and_cancel(dialog):
            dialog.spin_x.setValue(999)
            dialog.select_group(1)
            dialog.spin_y.setValue(200)
            dialog.findChild(ListeningPanel).set_listener((99, 99, 99), 180)
            dialog.reject()
            return QDialog.DialogCode.Rejected

        with patch.object(CoordinatePickerDialog, "exec", edit_and_cancel):
            self.window.groupsInterface.openWorkbench()
        self.assertEqual(_make_json_safe(self.window.config, self.window.group_config), before)


if __name__ == "__main__":
    unittest.main()
