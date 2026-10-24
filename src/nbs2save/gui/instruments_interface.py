"""Custom NBS instruments and NoteBetter resource-pack authoring."""

from copy import deepcopy
from pathlib import Path
import re

import pynbs
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem,
    QFileDialog, QFrame, QAbstractItemView,
)
from qfluentwidgets import (
    ScrollArea, CardWidget, TableWidget, SubtitleLabel, BodyLabel,
    CaptionLabel, PushButton, PrimaryPushButton, SpinBox,
    CheckBox, InfoBar, InfoBarPosition,
)
from .studio_style import PageHeader, apply_page_style, muted_label


class InstrumentsInterface(ScrollArea):
    """The table is kept with the project, including paths to users' samples."""

    FIELDS = ("nbs_id", "name", "base_block", "sound_id", "root_key", "sound_file")
    # Familiar full blocks available in every supported game version, excluding
    # the ordinary instrument bases so an added mapping does not affect them.
    SUPPORT_BLOCKS = (
        "diamond_block", "lapis_block", "quartz_block",
        "obsidian", "mossy_cobblestone", "chiseled_stone_bricks",
        "cracked_stone_bricks", "redstone_block", "coal_block", "sea_lantern",
        "prismarine", "dark_prismarine", "purpur_block", "purpur_pillar",
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("instrumentsInterface")
        self._main_window = parent
        self.scrollWidget = QWidget()
        layout = QVBoxLayout(self.scrollWidget)
        layout.setContentsMargins(36, 20, 36, 36)
        layout.setSpacing(12)
        self.setWidget(self.scrollWidget)
        self.scrollWidget.setObjectName("instrumentsContent")
        self.scrollWidget.setAutoFillBackground(False)
        self.setWidgetResizable(True)
        apply_page_style(self)
        header = PageHeader(
            "自定义音色", "为每个 NBS 音色指定垫块、音高和 OGG 采样；导出、3D 预览与试听共用此表。",
            "NOTE BETTER · 音色配置", self.scrollWidget,
        )
        layout.addWidget(header)

        toolbar = QHBoxLayout()
        self.add_button = PushButton("新增音色")
        self.import_button = PushButton("从当前 NBS 导入")
        self.duplicate_button = PushButton("复制选中")
        self.remove_button = PushButton("删除选中")
        self.apply_button = PrimaryPushButton("应用音色设置")
        toolbar.addWidget(self.import_button)
        toolbar.addStretch()
        toolbar.addWidget(self.apply_button)
        layout.addLayout(toolbar)
        edit_toolbar = QHBoxLayout()
        for button in (self.add_button, self.duplicate_button, self.remove_button):
            edit_toolbar.addWidget(button)
        edit_toolbar.addStretch()
        layout.addLayout(edit_toolbar)

        self.table = TableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "NBS ID", "音色名称", "音色下垫块", "声音 ID", "采样原音键", "OGG 文件", "选择",
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setWordWrap(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setMinimumHeight(280)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setMinimumSectionSize(65)
        self._column_minima = (70, 120, 185, 200, 95, 180, 65)
        for column, width in enumerate((70, 150, 205, 230, 100, 215, 65)):
            self.table.setColumnWidth(column, width)
        header.setStretchLastSection(False)
        header.sectionResized.connect(self._keep_column_readable)
        layout.addWidget(self.table, 1)
        detail = muted_label(CaptionLabel(
            "声音 ID 是资源包事件名；原音键是采样的实际 NBS 键值（默认 45）。OGG 请使用单声道 Vorbis，"
            "文件路径需持续有效。下垫块必须唯一，否则 NoteBetter 无法区分音色。"
        ))
        detail.setWordWrap(True)
        layout.addWidget(detail)

        sample_row = QHBoxLayout()
        self.selection_label = muted_label(CaptionLabel("未选择音色"))
        sample_row.addWidget(self.selection_label, 1)
        self.sample_play_button = PushButton("试听选中采样")
        self.sample_play_button.setToolTip("直接播放 OGG 原始采样，不进行空间定位或 NBS 音高变换")
        self.sample_stop_button = PushButton("停止采样")
        self.sample_stop_button.setEnabled(False)
        self.sample_stop_button.setToolTip("停止当前 OGG 采样试听")
        sample_row.addWidget(self.sample_play_button)
        sample_row.addWidget(self.sample_stop_button)
        layout.addLayout(sample_row)
        self._sample_player = None
        self._sample_output = None

        card = CardWidget()
        pack_layout = QVBoxLayout(card)
        pack_layout.setContentsMargins(18, 14, 18, 14)
        pack_layout.addWidget(SubtitleLabel("一键导出音效包"))
        row = QHBoxLayout()
        row.addWidget(BodyLabel("资源包格式"))
        self.auto_format = CheckBox("跟随目标游戏版本")
        self.auto_format.setChecked(True)
        row.addWidget(self.auto_format)
        self.pack_format = SpinBox()
        self.pack_format.setRange(1, 10000)
        self.pack_format.setValue(46)
        self.pack_format.setEnabled(False)
        self.pack_format.setToolTip("pack.mcmeta 的 pack_format，需匹配目标 Minecraft 版本")
        row.addWidget(self.pack_format)
        row.addStretch()
        pack_layout.addLayout(row)
        export_row = QHBoxLayout()
        export_row.addStretch()
        self.export_button = PrimaryPushButton("导出 NoteBetter 音效包 ZIP")
        export_row.addWidget(self.export_button)
        pack_layout.addLayout(export_row)
        self.pack_help = muted_label(CaptionLabel(
            "ZIP 含 NoteBetter 配置、资源包和安装说明；同一垫块的音符盒都会触发对应映射。"
        ))
        self.pack_help.setWordWrap(True)
        pack_layout.addWidget(self.pack_help)
        layout.addWidget(card)
        self.status = CaptionLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch()

        self.add_button.clicked.connect(self.add_instrument)
        self.import_button.clicked.connect(self.import_from_nbs)
        self.duplicate_button.clicked.connect(self.duplicate_selected)
        self.remove_button.clicked.connect(self.remove_selected)
        self.apply_button.clicked.connect(self.apply_settings)
        self.export_button.clicked.connect(self.export_pack)
        self.auto_format.toggled.connect(lambda checked: self.pack_format.setEnabled(not checked))
        self.auto_format.toggled.connect(self._update_pack_format)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.sample_play_button.clicked.connect(self.preview_selected_sample)
        self.sample_stop_button.clicked.connect(self.stop_sample_preview)
        for column, tip in {
            0: "NBS 文件中的音色编号（0–15 可覆盖原版，16 起通常为自定义）",
            2: "Minecraft 音符盒下方的方块 ID；每个自定义音色必须唯一",
            3: "资源包中实际播放的声音事件 ID，例如 nbs2save:custom.piano",
            4: "采样录制时对应的 NBS 键值，导出时据此校正音高",
        }.items():
            item = self.table.horizontalHeaderItem(column)
            if item:
                item.setToolTip(tip)
        if parent is not None:
            combo = getattr(getattr(parent, "homeInterface", None), "versionCard", None)
            combo = getattr(combo, "comboBox", None)
            if combo is not None:
                combo.currentIndexChanged.connect(self._update_pack_format)
        self._selection_changed()

    def _keep_column_readable(self, column, _old, width):
        minimum = self._column_minima[column]
        if width < minimum:
            self.table.setColumnWidth(column, minimum)

    def _selection_changed(self):
        self.stop_sample_preview()
        rows = sorted({index.row() for index in self.table.selectedIndexes()})
        if not rows:
            self.selection_label.setText("未选择音色 · 共 %d 个" % self.table.rowCount())
            self.duplicate_button.setEnabled(False)
            self.remove_button.setEnabled(False)
            self.sample_play_button.setEnabled(False)
            return
        self.selection_label.setText("已选择第 %d 行 · 共 %d 个" % (rows[0] + 1, self.table.rowCount()))
        self.duplicate_button.setEnabled(True)
        self.remove_button.setEnabled(True)
        self.sample_play_button.setEnabled(True)

    def _ensure_sample_player(self):
        if self._sample_player is None:
            self._sample_output = QAudioOutput(self)
            self._sample_output.setVolume(0.8)
            self._sample_player = QMediaPlayer(self)
            self._sample_player.setAudioOutput(self._sample_output)
            self._sample_player.errorOccurred.connect(self._sample_error)
            self._sample_player.playbackStateChanged.connect(
                lambda state: self.sample_stop_button.setEnabled(state == QMediaPlayer.PlaybackState.PlayingState)
            )
        return self._sample_player

    def _sample_error(self, error, message):
        self.sample_stop_button.setEnabled(False)
        if message:
            self._message("采样试听失败", f"{message}。请检查文件是否为有效的 Ogg Vorbis 采样。", True)
        else:
            self._message("采样试听失败", str(error), True)

    def preview_selected_sample(self):
        rows = sorted({index.row() for index in self.table.selectedIndexes()})
        if not rows:
            self._message("尚未选择音色", "请先选择一行音色。", True)
            return
        item = self.table.item(rows[0], 5)
        path = Path(item.text().strip()).expanduser() if item else Path()
        if not path.is_file() or path.suffix.lower() != ".ogg":
            self._message("无法试听", "选中音色的 OGG 文件不存在或不是 .ogg 文件。", True)
            return
        self.stop_sample_preview()
        player = self._ensure_sample_player()
        player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        player.play()
        self.sample_stop_button.setEnabled(True)
        self.status.setText(f"正在试听原始采样：{path.name}（未进行空间定位和音高变换）")

    def stop_sample_preview(self):
        if self._sample_player is not None:
            self._sample_player.stop()
            # Detach the decoder from its source so the OGG can be replaced and
            # a hidden page does not retain decoded sample buffers.
            self._sample_player.setSource(QUrl())
        self.sample_stop_button.setEnabled(False)

    def shutdown(self):
        self.stop_sample_preview()
        if self._sample_player is not None:
            self._sample_player.setSource(QUrl())
            self._sample_player.deleteLater()
            self._sample_player = None
        if self._sample_output is not None:
            self._sample_output.deleteLater()
            self._sample_output = None

    def hideEvent(self, event):
        self.stop_sample_preview()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.shutdown()
        super().closeEvent(event)

    def _update_pack_format(self, *_):
        if not self.auto_format.isChecked():
            return
        from ..core.custom_instruments import resource_pack_format

        try:
            self.pack_format.setValue(resource_pack_format(self._main_window.homeInterface.getVersion()))
            self.pack_format.setToolTip("根据基础设置中的目标游戏版本自动选择")
        except ValueError as exc:
            self.pack_format.setToolTip(str(exc))

    def load_from_config(self):
        self.stop_sample_preview()
        config = self._main_window.config
        self.table.setRowCount(0)
        for entry in config.get("custom_instruments", []):
            self._append(entry)
        manual_format = config.get("notebetter_pack_format")
        self.auto_format.setChecked(manual_format is None)
        if manual_format is not None:
            self.pack_format.setValue(int(manual_format))
        self._update_pack_format()
        self._selection_changed()

    def _append(self, entry):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, field in enumerate(self.FIELDS):
            value = entry.get(field, 45 if field == "root_key" else "")
            item = QTableWidgetItem(str(value))
            item.setToolTip(str(value))
            self.table.setItem(row, column, item)
        browse = PushButton("浏览")
        # Resolve the current row at click time, since earlier rows may be deleted.
        browse.clicked.connect(lambda _, button=browse: self._browse_sample(button))
        self.table.setCellWidget(row, 6, browse)

    def _used_values(self, column):
        values = set()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, column)
            if item is not None:
                values.add(item.text().strip())
        return values

    def _next_id(self):
        used = set()
        for value in self._used_values(0):
            try:
                used.add(int(value))
            except ValueError:
                pass
        for candidate in range(16, 256):
            if candidate not in used:
                return candidate
        raise ValueError("16–255 的自定义音色 ID 已用完，请删除不用的音色后再添加。")

    def _next_support(self):
        used = {value if ":" in value else "minecraft:" + value for value in self._used_values(2)}
        return next(("minecraft:" + value for value in self.SUPPORT_BLOCKS
                     if "minecraft:" + value not in used), "")

    def _next_sound_id(self, instrument_id):
        used = self._used_values(3)
        base = f"nbs2save:custom.instrument_{instrument_id}"
        candidate, suffix = base, 2
        while candidate in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        return candidate

    def add_instrument(self):
        try:
            instrument_id = self._next_id()
        except ValueError as exc:
            self._message("无法新增", str(exc), True)
            return
        support = self._next_support()
        self._append({
            "nbs_id": instrument_id, "name": f"自定义音色 {instrument_id}",
            "base_block": support,
            "sound_id": self._next_sound_id(instrument_id),
            "root_key": 45, "sound_file": "",
        })
        self.table.selectRow(self.table.rowCount() - 1)
        self.status.setText("已新增音色；请选择 OGG 采样。" if support else "已新增音色；下垫块待填写，请指定未使用的方块 ID。")

    def duplicate_selected(self):
        rows = sorted({index.row() for index in self.table.selectedIndexes()})
        if not rows:
            return
        try:
            instrument_id = self._next_id()
        except ValueError as exc:
            self._message("无法复制", str(exc), True)
            return
        entry = {field: self.table.item(rows[0], column).text()
                 if self.table.item(rows[0], column) else ""
                 for column, field in enumerate(self.FIELDS)}
        support = self._next_support()
        entry.update(nbs_id=instrument_id, name=entry["name"] + " 副本",
                     base_block=support, sound_id=self._next_sound_id(instrument_id))
        self._append(entry)
        self.table.selectRow(self.table.rowCount() - 1)
        self.status.setText("已复制采样与原音键，并分配独立 ID 和垫块。" if support else "已复制音色；下垫块待填写，请指定未使用的方块 ID。")

    def remove_selected(self):
        self.stop_sample_preview()
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)
        self._selection_changed()
        self.status.setText(f"已删除 {len(rows)} 个音色；剩余 {self.table.rowCount()} 个。")

    def _browse_sample(self, button):
        row = next((r for r in range(self.table.rowCount())
                    if self.table.cellWidget(r, 6) is button), None)
        if row is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, "选择音色采样", "", "Ogg Vorbis (*.ogg)")
        if path:
            self.stop_sample_preview()
            self.table.setItem(row, 5, QTableWidgetItem(path))

    def collect_instruments(self):
        result = []
        for row in range(self.table.rowCount()):
            entry = {
                field: self.table.item(row, column).text().strip() if self.table.item(row, column) else ""
                for column, field in enumerate(self.FIELDS)
            }
            try:
                entry["nbs_id"] = int(entry["nbs_id"])
                entry["root_key"] = int(entry["root_key"])
            except ValueError as exc:
                raise ValueError(f"音色表第 {row + 1} 行：NBS ID 和采样原音键须为整数") from exc
            result.append(entry)
        return result

    def save_to_config(self):
        """Validate and commit when saving, exporting, converting or opening the studio."""
        from ..core.custom_instruments import validate_custom_instruments

        entries = self.collect_instruments()
        entries = validate_custom_instruments(entries, require_files=False)
        self._main_window.config["custom_instruments"] = deepcopy(entries)
        self._main_window.config["notebetter_pack_format"] = (
            None if self.auto_format.isChecked() else self.pack_format.value()
        )
        return entries

    def _message(self, title, text, error=False):
        self.status.setText(text)
        show = InfoBar.error if error else InfoBar.success
        show(title=title, content=text, orient=Qt.Orientation.Horizontal,
             isClosable=True, position=InfoBarPosition.TOP, duration=6000, parent=self)

    def apply_settings(self):
        try:
            entries = self.save_to_config()
            self._message("已应用", f"已应用 {len(entries)} 个自定义音色，可保存项目配置以便下次使用。")
        except Exception as exc:
            self._message("音色设置有误", str(exc), True)

    def import_from_nbs(self):
        try:
            path = Path(self._main_window.homeInterface.getInputFile())
            if not path.is_file():
                raise ValueError("请先在基础设置中选择 NBS 文件。")
            song = pynbs.read(str(path))
            existing = {int(value) for value in self._used_values(0) if value.isdecimal()}
            imported = 0
            for instrument in song.instruments:
                instrument_id = song.header.default_instruments + instrument.id
                if instrument_id in existing:
                    continue
                sample = Path(instrument.file)
                if not sample.is_absolute():
                    sample = path.parent / sample
                slug = re.sub(r"[^a-z0-9_.-]", "_", instrument.name.lower()).strip("_") or f"instrument_{instrument_id}"
                self._append({
                    "nbs_id": instrument_id, "name": instrument.name,
                    "base_block": self._next_support(),
                    "sound_id": f"nbs2save:custom.{slug}_{instrument_id}",
                    "root_key": instrument.pitch,
                    "sound_file": str(sample.resolve()) if sample.is_file() else "",
                })
                existing.add(instrument_id)
                imported += 1
            self.status.setText(f"已导入 {imported} 个音色；请分别指定独立垫块和 OGG 文件后应用。")
            self._selection_changed()
        except Exception as exc:
            self._message("导入失败", str(exc), True)

    def export_pack(self):
        self.stop_sample_preview()
        try:
            self.save_to_config()
            if not self._main_window.config.get("custom_instruments"):
                raise ValueError("请先添加至少一个自定义音色。")
            path, _ = QFileDialog.getSaveFileName(self, "导出 NoteBetter 音效包", "NoteBetter-Sounds.zip", "ZIP (*.zip)")
            if not path:
                return
            if not path.lower().endswith(".zip"):
                path += ".zip"
            from ..core.custom_instruments import export_notebetter_pack

            export_notebetter_pack(
                path, self._main_window.config,
                pack_format=None if self.auto_format.isChecked() else self.pack_format.value(),
                minecraft_version=self._main_window.homeInterface.getVersion(),
            )
            self._message("导出完成", f"已导出 {Path(path).name}，安装方式见包内说明。")
        except Exception as exc:
            self._message("导出失败", str(exc), True)
