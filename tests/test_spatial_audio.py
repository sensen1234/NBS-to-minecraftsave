"""Spatial listening is derived from export geometry and playable local samples."""

from copy import deepcopy
from io import BytesIO
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tracemalloc
import unittest
from unittest.mock import patch
import wave

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pynbs
from PyQt6.QtCore import QThreadPool
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from nbs2save.core.preview import build_preview
from nbs2save.core.spatial_audio import (
    RenderCancelled, collect_spatial_events, decode_audio_sample, render_spatial_audio,
)
from nbs2save.gui.listening_panel import ListeningPanel


def make_song(*notes, tempo=10):
    song = pynbs.new_file(tempo=tempo)
    song.notes = list(notes) or [pynbs.Note(tick=0, layer=0, instrument=0, key=45, panning=20)]
    song.header.song_length = max(note.tick for note in song.notes)
    song.layers = [pynbs.Layer(0), pynbs.Layer(1)]
    return song


def make_groups(mode="default", offset="pan"):
    return {0: {"base_coords": ("10", "64", "30"), "layers": [0],
                "block": {"base": "stone", "cover": "redstone_lamp"},
                "generation_mode": mode, "offset_mode": offset}}


def write_tone(path, frequency=440, rate=16000, duration=.25):
    signal = np.sin(2 * np.pi * frequency * np.arange(round(rate * duration)) / rate) * .4
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes((signal * 32767).astype("<i2").tobytes())


class SpatialAudioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.sample = Path(self.tempdir.name) / "tone.wav"
        write_tone(self.sample)
        self.song = make_song()
        self.groups = make_groups()

    def render(self, **kwargs):
        config = kwargs.pop("config", {"instrument_samples": {"0": str(self.sample)}})
        return render_spatial_audio(self.song, self.groups, config,
                                    sample_rate=16000, listener=kwargs.pop("listener", (10.5, 64.5, 26.5)), **kwargs)

    def test_events_use_every_real_export_mode_and_offset(self):
        self.song.notes[0].velocity = 40
        for output, modes in (("schematic", ("default", "staircase", "staircase_up")),
                              ("mcfunction", ("default",))):
            for mode in modes:
                for offset in ("pan", "volume"):
                    with self.subTest(output=output, mode=mode, offset=offset):
                        groups = make_groups(mode, offset)
                        events = collect_spatial_events(self.song, groups, {"type": output})
                        actual = build_preview(self.song.notes, groups, {"type": output}, global_max_tick=0)
                        notes = [block for block in actual.blocks if "note_block[" in block.blockstate]
                        self.assertEqual([(event.position, event.blockstate) for event in events],
                                         [(block.position, block.blockstate) for block in notes])

    def test_world_coordinates_and_pitch_come_from_export(self):
        event, = collect_spatial_events(self.song, self.groups)
        self.assertEqual(event.position, (10, 64, 32))
        self.assertEqual(event.note_pitch, 12)
        self.assertEqual(event.pitch_key, 45)
        self.song.notes[0].key = 80
        self.assertEqual(collect_spatial_events(self.song, self.groups)[0].note_pitch, 0)

    def test_range_zero_and_both_tempo_modes(self):
        song = make_song(pynbs.Note(tick=10, layer=0, instrument=0, key=45),
                         pynbs.Note(tick=20, layer=0, instrument=0, key=45), tempo=20)
        nbs = collect_spatial_events(song, self.groups, start_tick=10, end_tick=20)
        redstone = collect_spatial_events(song, self.groups, start_tick=10, end_tick=20, timing="redstone")
        self.assertEqual([event.time for event in nbs], [0, .5])
        self.assertEqual([event.time for event in redstone], [0, 1])
        self.assertEqual([event.position[0] for event in nbs], [30, 50])

    def test_later_group_removes_overwritten_sound_source(self):
        groups = make_groups()
        groups[1] = deepcopy(groups[0])
        groups[1]["layers"] = [1]
        groups[1]["base_coords"] = ("10", "64", "32")
        actual = build_preview(self.song.notes, groups, global_max_tick=0)
        self.assertFalse(any(block.position == (10, 64, 32) and "note_block" in block.state for block in actual.blocks))
        self.assertEqual(collect_spatial_events(self.song, groups), ())

    def test_custom_support_mapping_applies_to_vanilla_notes(self):
        song = make_song(pynbs.Note(tick=0, layer=0, instrument=2, key=45, panning=20))
        config = {"custom_instruments": [{"nbs_id": 16, "name": "Custom drum", "base_block": "stone",
                                          "sound_file": str(self.sample), "sound_id": "demo:drum", "root_key": 45}]}
        event, = collect_spatial_events(song, self.groups, config)
        self.assertEqual(event.instrument, 16)
        audio = render_spatial_audio(song, self.groups, config, listener=(10.5,64.5,26.5), sample_rate=16000)
        self.assertAlmostEqual(audio.events[0].gain, 1 - 6 / 16)
        self.assertIn(self.sample.name, audio.events[0].sample_source)

    def test_cross_tick_overlap_uses_complete_song_geometry(self):
        song = make_song(pynbs.Note(tick=1, layer=0, instrument=0, key=45, panning=20),
                         pynbs.Note(tick=0, layer=1, instrument=0, key=45, panning=20))
        groups = make_groups()
        groups[1] = deepcopy(groups[0])
        groups[1]["layers"] = [1]
        groups[1]["base_coords"] = ("12", "64", "30")
        self.assertEqual(collect_spatial_events(song, groups, start_tick=1, end_tick=1), ())

    def test_box_covered_by_later_group_is_silent(self):
        song = make_song(pynbs.Note(tick=0, layer=0, instrument=0, key=45, panning=20),
                         pynbs.Note(tick=0, layer=1, instrument=0, key=45, panning=20))
        groups = make_groups()
        groups[1] = deepcopy(groups[0])
        groups[1]["layers"] = [1]
        groups[1]["base_coords"] = ("10", "66", "30")
        event, = collect_spatial_events(song, groups)
        self.assertEqual((event.group_id,event.position), (1,(10,66,32)))

    def test_lost_custom_support_does_not_resolve_custom_by_nbs_id(self):
        song = make_song(pynbs.Note(tick=0, layer=0, instrument=0, key=45, panning=20),
                         pynbs.Note(tick=0, layer=1, instrument=1, key=45, panning=20))
        groups = make_groups()
        groups[1] = deepcopy(groups[0])
        groups[1]["layers"] = [1]
        groups[1]["base_coords"] = ("10", "63", "30")
        config = {"custom_instruments": [{"nbs_id": 0, "name": "Custom harp", "base_block": "diamond_block",
                                          "sound_file": "absent.ogg", "sound_id": "demo:harp", "root_key": 45}]}
        event, = collect_spatial_events(song, groups, config)
        self.assertIsNone(event.custom_instrument)
        # Its support is now another note box; the old custom sample must not
        # be decoded (the deliberately missing path makes that observable).
        audio = render_spatial_audio(song, groups, config, listener=(10.5,64.5,26.5),sample_rate=16000)
        self.assertIn("合成参考", audio.events[0].sample_source)
        self.assertAlmostEqual(audio.events[0].gain, 1-6/48)

    def test_all_legal_custom_root_keys_are_playable(self):
        self.song.notes[0].instrument = 16
        for root, key in ((0,57),(87,33)):
            with self.subTest(root=root,key=key):
                self.song.notes[0].key = key
                config = {"custom_instruments": [{"nbs_id": 16, "name": "Extreme", "base_block": "diamond_block",
                                                  "sound_file": str(self.sample), "sound_id": "demo:tone", "root_key": root}]}
                audio = self.render(config=config)
                self.assertTrue(np.any(np.frombuffer(audio.pcm, "<i2")))

    def test_polyphony_does_not_retain_per_note_pcm(self):
        write_tone(self.sample, duration=2)
        song = make_song(*[pynbs.Note(tick=0, layer=layer, instrument=0,key=45,panning=20) for layer in range(300)])
        groups = {}
        for layer in range(300):
            groups[layer] = deepcopy(self.groups[0])
            groups[layer]["layers"] = [layer]
            groups[layer]["base_coords"] = ("10", "64", str(30+layer*4))
        tracemalloc.start()
        try:
            audio = render_spatial_audio(song,groups,{"instrument_samples":{"0":str(self.sample)}},
                                         sample_rate=16000,listener=(10.5,64.5,26.5))
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertEqual(len(audio.events), 300)
        self.assertLess(peak, 32 * 1024 * 1024)

    def test_yaw_swaps_ears_in_pcm_and_interaural_delay(self):
        # A source west of the listener is on the right when facing south.
        listener = (16.5, 64.5, 32.5)
        first = self.render(listener=listener, yaw=0)
        reverse = self.render(listener=listener, yaw=180)
        a = np.frombuffer(first.pcm, "<i2").reshape(-1, 2).astype(float)
        b = np.frombuffer(reverse.pcm, "<i2").reshape(-1, 2).astype(float)
        self.assertGreater(np.sum(a[:,1] ** 2), np.sum(a[:,0] ** 2) * 10)
        self.assertGreater(np.sum(b[:,0] ** 2), np.sum(b[:,1] ** 2) * 10)
        self.assertGreater(first.events[0].left_delay, first.events[0].right_delay)
        self.assertLess(reverse.events[0].left_delay, reverse.events[0].right_delay)
        np.testing.assert_allclose(a[:,0], b[:,1], atol=1)

    def test_distance_reduces_level_and_radius_is_silent(self):
        near = self.render(listener=(10.5,64.5,30.5))
        far = self.render(listener=(10.5,64.5,2.5))
        outside = self.render(listener=(10.5,64.5,-30))
        energy = lambda audio: np.mean(np.frombuffer(audio.pcm, "<i2").astype(float) ** 2)
        self.assertGreater(energy(near), energy(far) * 3)
        self.assertEqual(energy(outside), 0)
        self.assertTrue(any("听觉范围" in message for message in outside.warnings))

    def test_local_sample_transposes_to_exported_note(self):
        self.song.notes[0].key = 57
        audio = self.render()
        mono = np.frombuffer(audio.pcm, "<i2").reshape(-1, 2).mean(axis=1)[:1800]
        peak = np.argmax(abs(np.fft.rfft(mono))) * 16000 / len(mono)
        self.assertAlmostEqual(peak, 880, delta=12)
        self.assertFalse(audio.warnings)

    def test_custom_root_key_changes_sample_pitch(self):
        self.song.notes[0].instrument = 16
        config = {"custom_instruments": [{"nbs_id": 16, "name": "Tone", "base_block": "diamond_block",
                                          "sound_file": str(self.sample), "sound_id": "demo:tone", "root_key": 33}]}
        audio = self.render(config=config)
        mono = np.frombuffer(audio.pcm, "<i2").reshape(-1, 2).mean(axis=1)[:1800]
        peak = np.argmax(abs(np.fft.rfft(mono))) * 16000 / len(mono)
        self.assertAlmostEqual(peak, 880, delta=12)
        self.assertAlmostEqual(audio.events[0].gain, 1 - 6 / 16)

    def test_velocity_changes_position_not_source_volume_twice(self):
        self.song.notes[0].velocity = 40
        first = self.render()
        self.song.notes[0].velocity = 100
        second = self.render()
        self.assertEqual(first.pcm, second.pcm)

    def test_fallback_is_audible_and_explicitly_labelled(self):
        audio = self.render(config={})
        self.assertTrue(np.any(np.frombuffer(audio.pcm, "<i2")))
        self.assertTrue(any("非 Minecraft 原版" in message for message in audio.warnings))

    def test_wav_decoder_resamples_real_sample_and_wav_export(self):
        samples = decode_audio_sample(self.sample, 8000)
        self.assertEqual(len(samples), 2000)
        self.assertAlmostEqual(float(np.max(samples)), .4, delta=.01)
        audio = self.render()
        with wave.open(BytesIO(audio.wav_bytes()), "rb") as reader:
            self.assertEqual((reader.getnchannels(),reader.getsampwidth(),reader.getframerate()), (2,2,16000))
            self.assertEqual(reader.readframes(reader.getnframes()), audio.pcm)

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg needed to generate a real Vorbis test fixture")
    def test_qt_ffmpeg_decodes_real_ogg_on_render_worker(self):
        ogg = self.sample.with_suffix(".ogg")
        subprocess.run([shutil.which("ffmpeg"), "-v", "error", "-y", "-i", str(self.sample),
                        "-c:a", "libvorbis", str(ogg)], check=True, capture_output=True)
        panel = ListeningPanel(lambda: self.song, lambda: self.groups,
                               lambda: {"instrument_samples": {"0": str(ogg)}})
        panel.set_listener((10.5,64.5,26.5))
        with patch.object(panel, "_play_audio") as play:
            panel.render_and_play()
            deadline = time.monotonic() + 10
            while panel._audio is None and panel._workers and time.monotonic() < deadline:
                QTest.qWait(20)
            self.assertIsNotNone(panel._audio, panel.status_label.text())
            self.assertTrue(np.any(np.frombuffer(panel._audio.pcm, "<i2")))
            play.assert_called_once()
        panel.shutdown()
        panel.close()

    def test_cancel_invalid_ranges_and_missing_custom_sample_fail(self):
        cancelled = threading.Event()
        cancelled.set()
        with self.assertRaises(RenderCancelled):
            self.render(cancel=cancelled)
        for kwargs in ({"start_tick": -1}, {"sample_rate": 3}, {"listener": (float("nan"),0,0)}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                options = {"sample_rate": 16000, "listener": (0,64,0)} | kwargs
                render_spatial_audio(self.song,self.groups,{},**options)
        self.song.notes[0].instrument = 16
        config = {"custom_instruments": [{"nbs_id": 16, "name": "Missing", "base_block": "diamond_block",
                                          "sound_file": str(self.sample.with_name("absent.ogg")), "sound_id": "demo:missing"}]}
        with self.assertRaisesRegex(ValueError, "不存在"):
            self.render(config=config)

    def test_panel_persists_listener_range_and_stops_stale_work(self):
        config = {"instrument_samples": {"0": str(self.sample)}}
        panel = ListeningPanel(lambda: self.song, lambda: self.groups, lambda: config)
        self.addCleanup(panel.close)
        changes = []
        panel.listenerChanged.connect(lambda position,yaw: changes.append((position,yaw)))
        panel.set_listener((10.5,64.5,26.5), 90)
        panel.set_range(0, 10)
        self.assertEqual(config["listening"]["position"], [10.5,64.5,26.5])
        self.assertEqual(config["listening"]["span"], 11)
        self.assertEqual(changes[-1], ((10.5,64.5,26.5),90))
        with patch.object(panel, "_play_audio") as play:
            panel.render_and_play()
            panel.invalidate()
            deadline = time.monotonic() + 5
            while panel._workers and time.monotonic() < deadline:
                QTest.qWait(10)
            self.assertFalse(panel._workers)
            self.assertIsNone(panel._audio)
            play.assert_not_called()
        panel.shutdown()
        self.assertFalse(panel.play_button.isEnabled())


if __name__ == "__main__":
    unittest.main()
