"""Headphone listening controls for the generated world, with cancellable mixing."""

from copy import deepcopy
from pathlib import Path
import threading

from PyQt6.QtCore import (
    QByteArray, QBuffer, QIODevice, QObject, QRunnable, QThreadPool, Qt,
    pyqtSignal,
)
from PyQt6.QtMultimedia import QAudio, QAudioFormat, QAudioSink, QMediaDevices
from PyQt6.QtWidgets import (
    QFileDialog, QHBoxLayout,
    QProgressBar, QVBoxLayout, QWidget,
)
from qfluentwidgets import (
    DoubleSpinBox as QDoubleSpinBox, SpinBox as QSpinBox, PushButton as QPushButton,
    LineEdit as QLineEdit, ComboBox as QComboBox, BodyLabel as QLabel,
    CaptionLabel, SubtitleLabel,
)

from ..core.spatial_audio import RenderCancelled, render_spatial_audio
from .studio_style import muted_label, label_font


class _RenderSignals(QObject):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(int, object, str)


class _RenderWorker(QRunnable):
    def __init__(self, revision, song, groups, config, options):
        super().__init__()
        self.signals = _RenderSignals()
        self.revision = revision
        self.song, self.groups, self.config, self.options = song, groups, config, options
        self.cancel = threading.Event()

    def run(self):
        try:
            result = render_spatial_audio(
                self.song, self.groups, self.config,
                cancel=self.cancel,
                progress=lambda value: self.signals.progress.emit(self.revision, value),
                **self.options,
            )
            self.signals.finished.emit(self.revision, result, "")
        except RenderCancelled:
            self.signals.finished.emit(self.revision, None, "")
        except Exception as exc:
            self.signals.finished.emit(self.revision, None, str(exc))


class ListeningPanel(QWidget):
    """Providers are evaluated on the GUI thread; workers receive deep snapshots.

    Listener coordinates are ear/eye coordinates in Minecraft world space.
    Preferences are written into the provider's mutable ``config['listening']``.
    The parent owns this widget and should call ``shutdown`` when its workbench
    closes. ``invalidate`` cancels audio after any change to the generated world.
    """

    listenerChanged = pyqtSignal(tuple, float)
    placeNearGroupRequested = pyqtSignal()
    faceGroupRequested = pyqtSignal()

    def __init__(self, song_provider, groups_provider, config_provider, parent=None):
        super().__init__(parent)
        self._song_provider = song_provider
        self._groups_provider = groups_provider
        self._config_provider = config_provider
        self._revision = 0
        self._workers = {}
        self._closed = False
        self._updating = True
        self._sink = None
        self._buffer = None
        self._audio = None
        self._playing = False
        self._max_tick = None
        settings = self._config_provider().get("listening", {})

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        heading = QHBoxLayout()
        heading.addWidget(label_font(SubtitleLabel("空间试听"), 16))
        heading.addStretch(1)
        self.place_near_button = QPushButton("监听当前组附近")
        self.place_near_button.setToolTip("将双耳放到当前音符组旁，便于检查距离和声像")
        self.place_near_button.clicked.connect(lambda: self.placeNearGroupRequested.emit())
        self.face_group_button = QPushButton("转向当前组")
        self.face_group_button.setToolTip("保留当前位置，将视线与双耳朝向当前音符组")
        self.face_group_button.clicked.connect(lambda: self.faceGroupRequested.emit())
        heading.addWidget(self.place_near_button)
        heading.addWidget(self.face_group_button)
        layout.addLayout(heading)
        description = muted_label(CaptionLabel("双耳世界坐标 · 0° 南(+Z)，90° 西(−X) · 建议使用耳机"))
        description.setToolTip("监听双耳位置通常高于玩家脚底 1.62 格；模拟距离衰减、双耳时差和头部遮挡。")
        layout.addWidget(description)
        grid = QHBoxLayout()
        grid.setSpacing(5)
        self.listener_spins = []
        position = settings.get("position", (0, 65.62, -6))
        if not isinstance(position, (list, tuple)) or len(position) != 3:
            position = (0, 65.62, -6)
        for column, (axis, value) in enumerate(zip("XYZ", position)):
            grid.addWidget(QLabel(axis))
            spin = QDoubleSpinBox()
            spin.setRange(-30_000_000, 30_000_000)
            spin.setDecimals(2)
            spin.setSingleStep(.5)
            spin.setMinimumWidth(100)
            spin.setValue(float(value))
            spin.setToolTip("监听双耳位置的世界坐标；玩家视角通常高于脚底 1.62 格")
            spin.valueChanged.connect(self._listener_edited)
            self.listener_spins.append(spin)
            grid.addWidget(spin, 1)
        grid.addWidget(QLabel("朝向"))
        self.yaw_spin = QDoubleSpinBox()
        self.yaw_spin.setRange(-360, 360)
        self.yaw_spin.setSuffix("°")
        self.yaw_spin.setValue(float(settings.get("yaw", 0)))
        self.yaw_spin.valueChanged.connect(self._listener_edited)
        self.yaw_spin.setMinimumWidth(90)
        self.yaw_spin.setToolTip("Minecraft 朝向：0° 南(+Z)，90° 西(−X)，180° 北(−Z)，−90° 东(+X)")
        grid.addWidget(self.yaw_spin, 1)
        layout.addLayout(grid)

        range_grid = QHBoxLayout()
        range_grid.setSpacing(5)
        self.start_spin = QSpinBox()
        self.start_spin.setRange(0, 2_147_483_647)
        self.start_spin.setValue(int(settings.get("start_tick", 0)))
        self.span_spin = QSpinBox()
        self.span_spin.setRange(1, 4096)
        self.span_spin.setValue(int(settings.get("span", 100)))
        self.start_spin.setMinimumWidth(100)
        self.span_spin.setMinimumWidth(90)
        range_grid.addWidget(QLabel("起始 tick"))
        range_grid.addWidget(self.start_spin)
        range_grid.addWidget(QLabel("长度"))
        range_grid.addWidget(self.span_spin)
        self.timing_combo = QComboBox()
        self.timing_combo.addItem("NBS 原曲速度", userData="nbs")
        self.timing_combo.addItem("Minecraft 红石（10 tick/秒）", userData="redstone")
        self.timing_combo.setToolTip(
            "NBS 原曲速度使用曲谱的 tempo；红石速度按每秒 10 个 NBS tick 播放。\n"
            "结构的位置和音高相同，所选速度仅决定试听时序。"
        )
        self.start_spin.setToolTip("开始播放的 NBS tick，包含起始 tick")
        self.span_spin.setToolTip("播放多少个 NBS tick；最多 4096 tick / 120 秒")
        self.timing_combo.setCurrentIndex(max(0, self.timing_combo.findData(settings.get("timing", "nbs"))))
        range_grid.addWidget(self.timing_combo, 1)
        self.start_spin.valueChanged.connect(self._options_edited)
        self.span_spin.valueChanged.connect(self._options_edited)
        self.timing_combo.currentIndexChanged.connect(self._options_edited)
        layout.addLayout(range_grid)

        source_row = QHBoxLayout()
        self.assets_edit = QLineEdit()
        self.assets_edit.setText(str(self._config_provider().get("minecraft_assets_dir", "")))
        self.assets_edit.setPlaceholderText("Minecraft 音色目录（可选）")
        self.assets_edit.setToolTip("选择含 harp.ogg 等文件的 note 目录，或资源包根目录；自定义乐器使用其单独配置的 OGG")
        self.assets_edit.editingFinished.connect(self._assets_edited)
        source_row.addWidget(self.assets_edit, 1)
        browse = QPushButton("浏览")
        browse.clicked.connect(self._browse_assets)
        source_row.addWidget(browse)
        layout.addLayout(source_row)
        hint = muted_label(CaptionLabel("未提供游戏采样时，原版音色使用合成参考音；自定义音色使用配置中的 OGG。"))
        hint.setWordWrap(True)
        hint.setToolTip("支持 OGG/WAV。提供游戏音符盒采样后可试听实际音色；合成参考音仅用于检查节奏、音高和声源位置。")
        layout.addWidget(hint)

        buttons = QHBoxLayout()
        self.play_button = QPushButton("生成并试听")
        self.play_button.clicked.connect(self.render_and_play)
        self.stop_button = QPushButton("停止")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)
        self.save_button = QPushButton("保存 WAV")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._save_wav)
        for button in (self.play_button, self.stop_button, self.save_button):
            buttons.addWidget(button)
        buttons.addStretch(1)
        buttons.addWidget(QLabel("音量"))
        self.volume_spin = QSpinBox()
        self.volume_spin.setRange(0, 100)
        self.volume_spin.setSuffix(" %")
        self.volume_spin.setValue(int(settings.get("volume", 70)))
        self.volume_spin.valueChanged.connect(self._volume_changed)
        self.volume_spin.setFixedWidth(110)
        buttons.addWidget(self.volume_spin)
        layout.addLayout(buttons)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        layout.addWidget(self.progress)
        self.status_label = QLabel("设置监听位置后生成试听。最多 120 秒 / 4096 tick。")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(28)
        label_font(self.status_label, 11)
        self.status_label.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status_label)
        self._updating = False

    @property
    def listener(self):
        return tuple(spin.value() for spin in self.listener_spins)

    @property
    def yaw(self):
        return self.yaw_spin.value()

    def _persist(self):
        if self._updating or self._closed:
            return
        self._config_provider()["listening"] = {
            "position": list(self.listener), "yaw": self.yaw,
            "start_tick": self.start_spin.value(), "span": self.span_spin.value(),
            "timing": self.timing_combo.currentData(), "volume": self.volume_spin.value(),
        }

    def set_listener(self, position, yaw=None):
        self._updating = True
        try:
            for spin, value in zip(self.listener_spins, position):
                spin.setValue(float(value))
            if yaw is not None:
                self.yaw_spin.setValue(float(yaw))
        finally:
            self._updating = False
        self._listener_edited()

    def set_range(self, start_tick, end_tick):
        """Follow the visible preview range without starting playback."""
        start, end = max(0, int(start_tick)), max(0, int(end_tick))
        self._updating = True
        try:
            self.start_spin.setValue(start)
            self.span_spin.setValue(max(1, end - start + 1))
        finally:
            self._updating = False
        self._options_edited()

    def _listener_edited(self, *_):
        if self._updating:
            return
        self._persist()
        self.invalidate()
        self.listenerChanged.emit(self.listener, self.yaw)

    def _options_edited(self, *_):
        if not self._updating:
            self._persist()
            self.invalidate()

    def _volume_changed(self, *_):
        self._persist()
        if self._sink is not None:
            self._sink.setVolume(self.volume_spin.value() / 100)

    def _assets_edited(self):
        self._config_provider()["minecraft_assets_dir"] = self.assets_edit.text().strip()
        self.invalidate()

    def _browse_assets(self):
        directory = QFileDialog.getExistingDirectory(self, "选择 Minecraft 音色目录", self.assets_edit.text())
        if directory:
            self.assets_edit.setText(directory)
            self._assets_edited()

    def invalidate(self, *_):
        self.stop()
        self._audio = None
        self.save_button.setEnabled(False)
        if not self._closed:
            self.status_label.setText("位置或结构已更新，请重新生成试听。")

    def stop(self, *_):
        self._revision += 1
        for worker in self._workers.values():
            worker.cancel.set()
        self._release_playback()
        self.stop_button.setEnabled(False)
        self.play_button.setEnabled(not self._closed)
        self.progress.setValue(0)
        if not self._closed:
            self.status_label.setText("已停止。")

    def _release_playback(self):
        """Drop native audio and PCM buffers without discarding a render for WAV."""
        self._playing = False
        if self._sink is not None:
            sink, self._sink = self._sink, None
            try:
                sink.stateChanged.disconnect(self._audio_state_changed)
            except (TypeError, RuntimeError):
                pass
            sink.stop()
            sink.deleteLater()
        if self._buffer is not None:
            self._buffer.close()
            self._buffer.deleteLater()
            self._buffer = None

    def shutdown(self, *_):
        self._closed = True
        self.stop()
        self._audio = None
        self.save_button.setEnabled(False)

    def render_and_play(self, *_):
        if self._closed:
            return
        self.stop()
        self._audio = None
        self.save_button.setEnabled(False)
        try:
            song = self._song_provider()
            if song is None:
                raise ValueError("请先加载 NBS 文件")
            config = deepcopy(self._config_provider())
            worker = _RenderWorker(
                self._revision, deepcopy(song), deepcopy(self._groups_provider()), config,
                {"listener": self.listener, "yaw": self.yaw,
                 "start_tick": self.start_spin.value(),
                 "end_tick": self.start_spin.value() + self.span_spin.value() - 1,
                 "timing": self.timing_combo.currentData()},
            )
        except Exception as exc:
            self.status_label.setText(f"无法试听：{exc}")
            return
        self._persist()
        self._workers[worker.revision] = worker
        worker.signals.progress.connect(self._render_progress)
        worker.signals.finished.connect(self._render_done)
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("正在根据导出坐标生成空间音频…")
        QThreadPool.globalInstance().start(worker)

    def _render_progress(self, revision, value):
        if not self._closed and revision == self._revision:
            self.progress.setValue(value)

    def _render_done(self, revision, audio, error):
        self._workers.pop(revision, None)
        if self._closed or revision != self._revision:
            return
        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if error:
            self.status_label.setText(f"试听失败：{error}")
            return
        if audio is None:
            return
        self._audio = audio
        self.save_button.setEnabled(True)
        self.progress.setValue(100)
        self._play_audio(audio)

    def _play_audio(self, audio):
        summary = f"{len(audio.events)} 个声源 · {audio.duration:.2f} 秒"
        if audio.warnings:
            summary += "\n" + "\n".join(audio.warnings)
        device = QMediaDevices.defaultAudioOutput()
        if device.isNull():
            self.status_label.setText(summary + "\n没有可用的音频输出设备；可保存 WAV。")
            return
        fmt = QAudioFormat()
        fmt.setSampleRate(audio.sample_rate)
        fmt.setChannelCount(2)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        if not device.isFormatSupported(fmt):
            self.status_label.setText(summary + "\n当前输出设备不支持 44.1 kHz 双声道 PCM；可保存 WAV。")
            return
        self._buffer = QBuffer(self)
        self._buffer.setData(QByteArray(audio.pcm))
        self._buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self._sink = QAudioSink(device, fmt, self)
        self._sink.setVolume(self.volume_spin.value() / 100)
        self._sink.stateChanged.connect(self._audio_state_changed)
        self._playing = True
        self.stop_button.setEnabled(True)
        self.status_label.setText("正在播放 · " + summary)
        self._sink.start(self._buffer)

    def _audio_state_changed(self, state):
        if not self._playing or self._sink is None:
            return
        if state == QAudio.State.IdleState:
            self.status_label.setText(self.status_label.text().replace("正在播放", "播放完成", 1))
            self._release_playback()
            self.stop_button.setEnabled(False)
        elif state == QAudio.State.StoppedState and self._sink.error() != QAudio.Error.NoError:
            self.status_label.setText(f"音频设备播放失败（{self._sink.error().name}）；可保存 WAV。")
            self._release_playback()
            self.stop_button.setEnabled(False)

    def _save_wav(self):
        if self._audio is None:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "保存空间试听", "空间试听.wav", "WAV 音频 (*.wav)")
        if filename:
            try:
                Path(filename).write_bytes(self._audio.wav_bytes())
                self.status_label.setText(f"已保存：{filename}")
            except OSError as exc:
                self.status_label.setText(f"保存失败：{exc}")

    def closeEvent(self, event):
        self.shutdown()
        super().closeEvent(event)

    def hideEvent(self, event):
        self.stop()
        super().hideEvent(event)
