"""Authoring shortcuts and audio lifecycle at the GUI boundary."""

import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PyQt6.QtGui import QHideEvent
from PyQt6.QtMultimedia import QAudio
from PyQt6.QtWidgets import QApplication, QComboBox, QTableWidgetItem, QWidget

from nbs2save.core.custom_instruments import validate_custom_instruments
from nbs2save.gui.instruments_interface import InstrumentsInterface
from nbs2save.gui.listening_panel import ListeningPanel


class AudioAuthoringControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_instruments(self):
        host = QWidget()
        host.config = {}
        host.homeInterface = SimpleNamespace(
            getVersion=lambda: "1.21.4", getInputFile=lambda: "",
            versionCard=SimpleNamespace(comboBox=QComboBox(host)),
        )
        page = InstrumentsInterface(host)
        self.addCleanup(host.close)
        self.addCleanup(page.shutdown)
        return page

    def make_listening(self):
        config = {}
        panel = ListeningPanel(lambda: None, lambda: [], lambda: config)
        self.addCleanup(panel.shutdown)
        self.addCleanup(panel.close)
        return panel

    def test_duplicate_allocates_independent_mapping_and_keeps_sample_pitch(self):
        page = self.make_instruments()
        self.assertFalse(page.remove_button.isEnabled())
        page.add_instrument()
        page.table.setItem(0, 4, QTableWidgetItem("40"))
        page.table.setItem(0, 5, QTableWidgetItem("sample.ogg"))
        page.duplicate_selected()
        entries = validate_custom_instruments(page.collect_instruments())
        self.assertEqual(len(entries), 2)
        for field in ("nbs_id", "sound_id", "base_block"):
            self.assertNotEqual(entries[0][field], entries[1][field])
        self.assertEqual(entries[1]["sound_file"], "sample.ogg")
        self.assertEqual(entries[1]["root_key"], 40)
        self.assertIn("2", page.selection_label.text())
        page.remove_selected()
        page.table.clearSelection()
        self.assertEqual(page.table.rowCount(), 1)
        self.assertFalse(page.remove_button.isEnabled())

    def test_new_mapping_reuses_vacant_id_and_marks_exhausted_supports(self):
        page = self.make_instruments()
        page.add_instrument()
        page.table.setItem(0, 0, QTableWidgetItem("018"))
        page.add_instrument()
        self.assertEqual(page.table.item(1, 0).text(), "16")
        for _ in range(len(page.SUPPORT_BLOCKS)):
            page.add_instrument()
        self.assertEqual(page.table.item(page.table.rowCount() - 1, 2).text(), "")
        self.assertIn("待填写", page.status.text())

    def test_sample_preview_is_local_and_stops_on_leave_export_and_shutdown(self):
        page = self.make_instruments()
        page.add_instrument()
        fixture = Path(__file__).parent / "fixtures" / "custom_note_mono.ogg"
        page.table.setItem(0, 5, QTableWidgetItem(str(fixture)))
        player = Mock()
        page._sample_player = player
        with patch.object(page, "_ensure_sample_player", return_value=player):
            page.preview_selected_sample()
        self.assertEqual(Path(player.setSource.call_args.args[0].toLocalFile()), fixture.resolve())
        player.play.assert_called_once()
        page.hideEvent(QHideEvent())
        self.assertGreaterEqual(player.stop.call_count, 2)
        player.stop.reset_mock()
        with patch("nbs2save.gui.instruments_interface.QFileDialog.getSaveFileName", return_value=("", "")):
            page.export_pack()
        player.stop.assert_called_once()
        page.shutdown()
        self.assertIsNone(page._sample_player)
        self.assertTrue(player.setSource.call_args.args[0].isEmpty())

    def test_missing_sample_reports_actionable_error_without_starting_player(self):
        page = self.make_instruments()
        page.add_instrument()
        with patch.object(page, "_message") as message:
            page.preview_selected_sample()
        self.assertTrue(message.call_args.args[2])
        self.assertIn("OGG", message.call_args.args[1])
        self.assertIsNone(page._sample_player)

    def test_listener_shortcuts_emit_without_arguments(self):
        panel = self.make_listening()
        placed, faced = Mock(), Mock()
        panel.placeNearGroupRequested.connect(placed)
        panel.faceGroupRequested.connect(faced)
        panel.place_near_button.click()
        panel.face_group_button.click()
        placed.assert_called_once_with()
        faced.assert_called_once_with()

    def test_playback_completion_releases_native_resources_and_preserves_wav(self):
        panel = self.make_listening()
        sink, buffer, audio = Mock(), Mock(), object()
        panel._sink, panel._buffer, panel._audio = sink, buffer, audio
        panel._playing = True
        panel.save_button.setEnabled(True)
        panel.status_label.setText("正在播放 · 1 秒")
        panel._audio_state_changed(QAudio.State.IdleState)
        self.assertIsNone(panel._sink)
        self.assertIsNone(panel._buffer)
        sink.stop.assert_called_once()
        buffer.close.assert_called_once()
        self.assertIs(panel._audio, audio)
        self.assertTrue(panel.save_button.isEnabled())
        self.assertIn("播放完成", panel.status_label.text())
        panel.shutdown()
        self.assertIsNone(panel._audio)
        self.assertFalse(panel.play_button.isEnabled())
        self.assertFalse(panel.save_button.isEnabled())


if __name__ == "__main__":
    unittest.main()
