"""Creative shortcuts should edit the selected draft and preserve project data."""

from copy import deepcopy
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PyQt6.QtCore import QThreadPool
from PyQt6.QtWidgets import QApplication, QDialog, QTableWidgetItem
from nbs2save.gui.coordinate_picker import CoordinatePickerDialog
from nbs2save.gui.listening_panel import ListeningPanel
from nbs2save.gui.window import MainWindow


class StudioAuthoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        with patch.object(MainWindow, "load_last_config"):
            self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        QThreadPool.globalInstance().waitForDone(5000)
        self.app.processEvents()

    def test_duplicate_group_is_independent_and_preserves_current_table_edits(self):
        self.window.group_config[0]["extra"] = {"value": [1]}
        page = self.window.groupsInterface
        page.table.setItem(0, 1, QTableWidgetItem("12"))
        page.table.selectRow(0)
        page.duplicateGroup()
        first, copied = self.window.group_config[0], self.window.group_config[1]
        self.assertEqual(copied["base_coords"], ("12", "0", "24"))
        self.assertEqual(first["base_coords"], ("12", "0", "0"))
        copied["extra"]["value"].append(2)
        self.assertEqual(first["extra"]["value"], [1])

    def test_invalid_coordinates_and_negative_layer_do_not_replace_config(self):
        page = self.window.groupsInterface
        before = deepcopy(self.window.group_config)
        page.table.setItem(0, 1, QTableWidgetItem("3.5"))
        with self.assertRaisesRegex(ValueError, "整数"):
            page.saveTableToConfig()
        self.assertEqual(self.window.group_config, before)
        page.table.setItem(0, 1, QTableWidgetItem("3"))
        page.table.setItem(0, 5, QTableWidgetItem("-1"))
        with self.assertRaisesRegex(ValueError, "非负"):
            page.saveTableToConfig()
        self.assertEqual(self.window.group_config, before)

    def test_listener_shortcuts_follow_workbench_selection(self):
        self.window.groupsInterface.addGroup()
        self.window.group_config[1]["base_coords"] = (100, 72, 40)
        self.window.groupsInterface.refreshTable()
        def edit(dialog):
            dialog.select_group(1)
            panel = dialog.findChild(ListeningPanel)
            panel.place_near_button.click()
            self.assertEqual(panel.listener, (100.5, 73.62, 34.0))
            panel.set_listener((90.5, 73.62, 30.5), 0)
            panel.face_group_button.click()
            self.assertAlmostEqual(panel.yaw, -45, places=2)
            dialog.reject()
            return QDialog.DialogCode.Rejected
        with patch.object(CoordinatePickerDialog, "exec", edit):
            self.window.groupsInterface.openWorkbench()


if __name__ == "__main__":
    unittest.main()
