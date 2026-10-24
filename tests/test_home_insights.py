"""Read-only song inspection and asynchronous home-page result ownership."""

from copy import deepcopy
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pynbs
from mcschematic import Version
from PyQt6.QtCore import QThreadPool
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from nbs2save.core.song_insights import analyze_song, read_song_insights
from nbs2save.gui.home_interface import HomeInterface


def example_song(title="A real song"):
    song = pynbs.new_file(song_name=title, song_author="Composer", tempo=20)
    song.layers = [pynbs.Layer(0), pynbs.Layer(1), pynbs.Layer(2)]
    song.notes = [pynbs.Note(tick=0, layer=0, instrument=0, key=33),
                  pynbs.Note(tick=20, layer=0, instrument=16, key=45),
                  pynbs.Note(tick=40, layer=2, instrument=16, key=58),
                  pynbs.Note(tick=41, layer=2, instrument=17, key=20)]
    song.instruments = [pynbs.Instrument(0,"Glass bells","bells.ogg"),
                        pynbs.Instrument(1,"Soft piano","piano.ogg")]
    return song


class SongInsightsTests(unittest.TestCase):
    def test_summary_uses_real_notes_custom_ids_and_does_not_modify_song(self):
        song = example_song()
        before = deepcopy(song.__dict__)
        result = analyze_song(song)
        self.assertEqual((result.title,result.author,result.tempo),("A real song","Composer",20))
        self.assertEqual((result.note_count,result.used_layer_count,result.out_of_range_count), (4,2,2))
        self.assertEqual((result.length_ticks,result.duration_seconds), (42,2.1))
        self.assertEqual(result.custom_note_count,3)
        self.assertEqual([(item.instrument_id,item.name,item.note_count) for item in result.custom_instruments],
                         [(16,"Glass bells",2),(17,"Soft piano",1)])
        self.assertEqual(song.__dict__,before)

    def test_real_file_read_and_metadata_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"fallback-title.nbs"
            song = example_song("")
            song.header.song_author = ""
            song.header.original_author = "Original composer"
            song.save(str(path))
            result = read_song_insights(path)
            self.assertEqual((result.title,result.author),("fallback-title","Original composer"))
            self.assertEqual(result.note_count,4)

    def test_empty_song_header_silence_and_bad_tempo(self):
        song = pynbs.new_file()
        song.header.song_length = 100
        result = analyze_song(song)
        self.assertEqual((result.note_count,result.duration_seconds), (0,10))
        self.assertEqual(result.duration_text,"0:10")
        song.header.tempo = 0
        with self.assertRaises(ValueError):
            analyze_song(song)


class HomeInsightsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)/"real.nbs"
        example_song().save(str(self.path))
        self.page = HomeInterface()
        self.page.resize(800,600)
        self.page.show()
        self.releases = []

    def tearDown(self):
        for release in self.releases:
            release.set()
        self.page.shutdown()
        self.page.close()
        QThreadPool.globalInstance().waitForDone(5000)
        self.app.processEvents()

    def wait_until(self, predicate, timeout=3):
        deadline = time.monotonic()+timeout
        while not predicate():
            if time.monotonic()>deadline:
                self.fail(self.page.analysisStatusLabel.text())
            QTest.qWait(10)

    def start_now(self):
        self.page._analysis_timer.stop()
        self.page._start_analysis()

    def test_real_selection_populates_song_summary_and_preserves_export_api(self):
        self.page.setInputFile(str(self.path))
        self.wait_until(lambda:self.page.songInsights is not None)
        self.assertEqual(self.page.songTitleLabel.text(),"A real song")
        self.assertEqual(self.page.metricLabels["notes"].text(),"4")
        self.assertIn("回落到最低音",self.page.analysisStatusLabel.text())
        self.assertIn("自定义音色",self.page.analysisStatusLabel.text())
        self.assertIn("20 NBS tick/秒",self.page.songMetaLabel.text())
        self.page.setOutputFile("my-structure")
        self.page.setInputFile(str(self.path.with_name("new.nbs")))
        self.assertEqual(self.page.getOutputFile(),"my-structure")
        self.page.setVersion(Version.JE_1_21_4)
        self.page.setType("mcfunction")
        self.assertEqual(self.page.getVersion(),Version.JE_1_21_4)
        self.assertEqual(self.page.getType(),"mcfunction")
        self.page.setStatus("正在导出")
        self.assertEqual(self.page.statusLabel.text(),"正在导出")
        self.assertEqual(self.page.horizontalScrollBar().maximum(),0)

    def test_debounce_only_reads_last_typed_path(self):
        with patch("nbs2save.gui.home_interface.read_song_insights", wraps=read_song_insights) as read:
            self.page.setInputFile("typing.nbs")
            QTest.qWait(50)
            self.page.setInputFile(str(self.path))
            self.wait_until(lambda:self.page.songInsights is not None)
            read.assert_called_once_with(str(self.path))

    def test_old_worker_cannot_overwrite_new_song(self):
        entered,release = threading.Event(),threading.Event()
        self.releases.append(release)
        ready=[]
        self.page.analysisReady.connect(lambda result:ready.append(result.title))
        def analyze(path):
            if path == "old.nbs":
                entered.set()
                release.wait(4)
                return analyze_song(example_song("Old title"))
            return analyze_song(example_song("New title"))
        with patch("nbs2save.gui.home_interface.read_song_insights",side_effect=analyze):
            self.page.setInputFile("old.nbs")
            self.start_now()
            self.wait_until(entered.is_set)
            self.page.setInputFile("new.nbs")
            self.start_now()
            self.wait_until(lambda:self.page.songInsights is not None)
            release.set()
            self.wait_until(lambda:not self.page._analysis_workers)
        self.assertEqual(self.page.songTitleLabel.text(),"New title")
        self.assertEqual(ready,["New title"])

    def test_shutdown_ignores_late_result_and_stops_pending_debounce(self):
        entered,release = threading.Event(),threading.Event()
        self.releases.append(release)
        def analyze(path):
            entered.set()
            release.wait(4)
            return analyze_song(example_song())
        with patch("nbs2save.gui.home_interface.read_song_insights",side_effect=analyze):
            self.page.setInputFile("closing.nbs")
            self.start_now()
            self.wait_until(entered.is_set)
            self.page.shutdown()
            title = self.page.songTitleLabel.text()
            release.set()
            self.wait_until(lambda:not self.page._analysis_workers)
        self.assertIsNone(self.page.songInsights)
        self.assertEqual(self.page.songTitleLabel.text(),title)
        self.assertFalse(self.page._analysis_timer.isActive())

    def test_missing_and_corrupt_files_have_friendly_status(self):
        self.page.setInputFile(str(self.path.with_name("missing.nbs")))
        self.start_now()
        self.wait_until(lambda:not self.page._analysis_workers)
        self.assertIn("找不到",self.page.analysisStatusLabel.text())
        self.path.write_bytes(b"not a song")
        self.page.setInputFile(str(self.path))
        self.start_now()
        self.wait_until(lambda:not self.page._analysis_workers)
        self.assertIn("无法解析",self.page.analysisStatusLabel.text())

    def test_shortcuts_emit_their_public_signals(self):
        calls=[]
        for name,button in (("groups",self.page.groupsBtn),("workbench",self.page.workbenchBtn),("instruments",self.page.instrumentsBtn)):
            signal=getattr(self.page,{"groups":"openGroupsSignal","workbench":"openWorkbenchSignal","instruments":"openInstrumentsSignal"}[name])
            signal.connect(lambda name=name:calls.append(name))
            button.click()
        self.assertEqual(calls,["groups","workbench","instruments"])


if __name__=="__main__":
    unittest.main()
