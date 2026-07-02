"""
主窗口 - 基于 MSFluentWindow 的 Fluent Design 架构
参考 March7thAssistant UI 设计文档实现
"""

import os
import json
import traceback

import pynbs
from mcschematic import Version

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog

from qfluentwidgets import (
    MSFluentWindow,
    FluentIcon,
    NavigationItemPosition,
    InfoBar,
    InfoBarPosition,
)

from ..core.constants import MINECRAFT_VERSIONS
from ..core.core import GroupProcessor
from ..core.schematic import SchematicOutputStrategy
from ..core.mcfunction import McFunctionOutputStrategy

from .home_interface import HomeInterface
from .groups_interface import GroupsInterface
from .log_interface import LogInterface
from .wiki_interface import WikiInterface
from .about_interface import AboutInterface


def _make_json_safe(config: dict, group_config: dict) -> dict:
    """将 config 中的 Version 枚举转为字符串，使其可 JSON 序列化"""
    safe_config = dict(config)
    dv = safe_config.get("data_version")
    if isinstance(dv, Version):
        safe_config["data_version"] = dv.name
    return {"app_config": safe_config, "group_config": group_config}


def _restore_from_json(d: dict):
    """从 JSON 字典恢复 config 和 group_config，还原 Version 枚举和 tuple 类型"""
    config = d["app_config"]
    group_config = d["group_config"]

    # 还原 Version 枚举
    dv = config.get("data_version")
    if isinstance(dv, str):
        try:
            config["data_version"] = Version[dv]
        except KeyError:
            config["data_version"] = MINECRAFT_VERSIONS[0]

    # 还原 base_coords 为 tuple
    for gid, cfg in group_config.items():
        bc = cfg.get("base_coords")
        if isinstance(bc, list):
            cfg["base_coords"] = tuple(bc)
        # 确保 int key（JSON 会将 int key 转为 str）
    # JSON 会把 dict 的 int key 转为 str，需要转回 int
    if any(isinstance(k, str) for k in group_config):
        group_config = {int(k): v for k, v in group_config.items()}

    return config, group_config


class MainWindow(MSFluentWindow):
    """NBS-to-Minecraft 主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NBS-to-Minecraft")
        self.resize(1060, 780)
        self.setMinimumSize(800, 600)

        # ── 核心数据 ──
        self.config = {
            "data_version": MINECRAFT_VERSIONS[0],
            "input_file": "",
            "type": "schematic",
            "output_file": "output",
        }

        self.group_config = {
            0: {
                "base_coords": ("0", "0", "0"),
                "layers": [0],
                "block": {
                    "base": "minecraft:iron_block",
                    "cover": "minecraft:iron_block",
                },
                "generation_mode": "default",
            }
        }

        # ── 初始化界面 ──
        self._initInterfaces()
        self._initNavigation()
        self._connectSignals()

        # 加载上次配置
        self.load_last_config()
        self._syncUIFromConfig()

    # ── 界面初始化 ──

    def _initInterfaces(self):
        self.homeInterface = HomeInterface(self)
        self.groupsInterface = GroupsInterface(self)
        self.groupsInterface.setMainWindow(self)
        self.wikiInterface = WikiInterface(self)
        self.logInterface = LogInterface(self)
        self.aboutInterface = AboutInterface(self)

    def _initNavigation(self):
        # 主要功能（顶部）
        self.addSubInterface(
            self.homeInterface, FluentIcon.HOME, "基础设置"
        )
        self.addSubInterface(
            self.groupsInterface, FluentIcon.TILES, "轨道组"
        )
        self.addSubInterface(
            self.wikiInterface, FluentIcon.DICTIONARY, "使用文档"
        )

        # 辅助功能（底部）
        self.addSubInterface(
            self.logInterface,
            FluentIcon.COMMAND_PROMPT,
            "运行日志",
            position=NavigationItemPosition.BOTTOM,
        )
        self.addSubInterface(
            self.aboutInterface,
            FluentIcon.INFO,
            "关于",
            position=NavigationItemPosition.BOTTOM,
        )

    def _connectSignals(self):
        # 主页信号
        self.homeInterface.startConvertSignal.connect(self.start_conversion)
        self.homeInterface.loadConfigSignal.connect(self.load_config)
        self.homeInterface.saveConfigSignal.connect(self.save_config)
        self.homeInterface.exitSignal.connect(self.close)

        # 轨道组按钮
        self.groupsInterface.addBtn.clicked.connect(self.groupsInterface.addGroup)
        self.groupsInterface.removeBtn.clicked.connect(
            self.groupsInterface.removeGroup
        )

    def _syncUIFromConfig(self):
        """将 config/group_config 同步到界面控件"""
        self.homeInterface.setInputFile(self.config.get("input_file", ""))
        self.homeInterface.setOutputFile(self.config.get("output_file", ""))
        self.homeInterface.setVersion(self.config.get("data_version"))
        self.homeInterface.setType(self.config.get("type", "schematic"))
        self.groupsInterface.refreshTable()

    # ── 日志与进度 ──

    def log(self, message: str):
        """追加日志，短消息同时更新状态栏"""
        self.logInterface.appendLog(message)
        # 与原始行为一致：短消息（<50字符且不含">>>"）更新状态栏
        if len(message) < 50 and ">>>" not in message:
            self.homeInterface.setStatus(message)

    def update_progress(self, value: int):
        """更新进度条"""
        self.homeInterface.setProgressVisible(True)
        self.homeInterface.progressBar.setValue(value)
        if value >= 100:
            self.homeInterface.setStatus("任务完成")

    # ── 文件配置操作 ──

    def save_config(self):
        self.groupsInterface.saveTableToConfig()
        path, _ = QFileDialog.getSaveFileName(
            self, "保存配置", "", "JSON (*.json)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    _make_json_safe(self.config, self.group_config),
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            InfoBar.success(
                title="保存成功",
                content=f"配置已保存到 {os.path.basename(path)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )

    def load_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "加载配置", "", "JSON (*.json)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                self.config, self.group_config = _restore_from_json(d)
                self._syncUIFromConfig()
                self.log(f"已加载配置: {path}")
                InfoBar.success(
                    title="加载成功",
                    content="配置已加载",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self,
                )
            except Exception as e:
                InfoBar.error(
                    title="加载失败",
                    content=str(e),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self,
                )

    def save_last_config(self):
        try:
            with open("last_config.json", "w", encoding="utf-8") as f:
                json.dump(
                    _make_json_safe(self.config, self.group_config),
                    f,
                    ensure_ascii=False,
                )
        except Exception:
            pass

    def load_last_config(self):
        try:
            if os.path.exists("last_config.json"):
                with open("last_config.json", "r", encoding="utf-8") as f:
                    d = json.load(f)
                self.config, self.group_config = _restore_from_json(d)
        except Exception:
            pass

    # ── 转换核心逻辑 ──

    def start_conversion(self):
        self.groupsInterface.saveTableToConfig()
        self.config["data_version"] = self.homeInterface.getVersion()
        self.config["input_file"] = self.homeInterface.getInputFile()
        self.config["type"] = self.homeInterface.getType()

        # 标准化输出路径：移除已有扩展名，由核心模块统一添加
        output_file = self.homeInterface.getOutputFile()
        if self.config["type"] == "schematic":
            if output_file.endswith(".schem"):
                output_file = output_file[:-6]
        elif self.config["type"] == "mcfunction":
            if output_file.endswith(".mcfunction"):
                output_file = output_file[:-11]
        self.config["output_file"] = output_file

        if not self.config["input_file"] or not os.path.exists(
            self.config["input_file"]
        ):
            InfoBar.error(
                title="错误",
                content="请输入有效的 NBS 文件路径",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self,
            )
            return

        # 切换到日志页面
        self.logInterface.appendLog(">>> 开始转换任务...")
        self.homeInterface.setStatus("正在分析...")
        self.homeInterface.setProgressVisible(True)
        self.homeInterface.progressBar.setValue(0)

        try:
            song = pynbs.read(self.config["input_file"])

            proc = GroupProcessor(
                song.notes,
                song.header.song_length,
                self.config,
                self.group_config,
            )
            proc.set_log_callback(self.log)
            proc.set_progress_callback(self.update_progress)

            if self.config["type"] == "schematic":
                proc.set_output_strategy(SchematicOutputStrategy())
            else:
                proc.set_output_strategy(McFunctionOutputStrategy())

            proc.process()
            self.logInterface.appendLog(">>> 转换成功!")
            self.homeInterface.setStatus("就绪")
            self.save_last_config()

            InfoBar.success(
                title="转换完成",
                content="文件已成功生成",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )

        except Exception as e:
            self.logInterface.appendLog(f">>> 错误: {e}")
            self.logInterface.appendLog(traceback.format_exc())
            InfoBar.error(
                title="转换失败",
                content=str(e),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=8000,
                parent=self,
            )
        finally:
            self.homeInterface.progressBar.setValue(100)
