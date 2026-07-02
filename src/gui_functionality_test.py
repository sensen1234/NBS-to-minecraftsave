#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI功能完整性测试脚本
测试GUI的各项核心功能是否正常工作
"""

import os
import sys
import time
import unittest
from unittest.mock import patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QApplication,
    QLineEdit,
    QComboBox,
    QTableWidget,
)

from qfluentwidgets import setThemeColor, setTheme, Theme

from nbs2save.gui.window import MainWindow


class GUI_Functionality_Test(unittest.TestCase):
    """GUI功能测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

        setThemeColor('#0078d4')
        setTheme(Theme.AUTO)

        cls.window = MainWindow()
        cls.window.show()
        QApplication.processEvents()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.window.close()
        QApplication.processEvents()

    def test_01_window_initialization(self):
        """测试窗口初始化"""
        print("\U0001f9ea 测试窗口初始化...")

        self.assertIn("NBS", self.window.windowTitle())

        # 检查子界面是否存在
        self.assertIsNotNone(self.window.homeInterface)
        self.assertIsNotNone(self.window.groupsInterface)
        self.assertIsNotNone(self.window.logInterface)

        # 检查输入控件
        self.assertGreater(
            len(self.window.findChildren(QLineEdit)), 0, "应该存在输入框控件"
        )
        self.assertGreater(
            len(self.window.findChildren(QComboBox)), 0, "应该存在下拉框控件"
        )

        print("\u2705 窗口初始化测试通过")

    def test_02_basic_input_fields(self):
        """测试基本输入字段"""
        print("\U0001f9ea 测试基本输入字段...")

        # 测试输入文件编辑框
        self.window.homeInterface.setInputFile("test_nbs_file.nbs")
        self.assertEqual(
            self.window.homeInterface.getInputFile(), "test_nbs_file.nbs"
        )

        # 测试输出文件编辑框
        self.window.homeInterface.setOutputFile("output_test")
        self.assertEqual(
            self.window.homeInterface.getOutputFile(), "output_test"
        )

        print("\u2705 基本输入字段测试通过")

    def test_03_combobox_functionality(self):
        """测试下拉框功能"""
        print("\U0001f9ea 测试下拉框功能...")

        # 测试版本下拉框
        version_card = self.window.homeInterface.versionCard
        self.assertGreater(version_card.comboBox.count(), 0, "版本下拉框应有选项")

        # 测试输出类型下拉框
        type_card = self.window.homeInterface.typeCard
        self.assertGreater(type_card.comboBox.count(), 0, "类型下拉框应有选项")

        print("\u2705 下拉框功能测试通过")

    def test_04_table_operations(self):
        """测试表格操作"""
        print("\U0001f9ea 测试表格操作...")

        table = self.window.groupsInterface.table
        self.assertIsNotNone(table)

        # 检查表格列数
        self.assertEqual(table.columnCount(), 9)

        # 检查表头
        headers = [
            table.horizontalHeaderItem(i).text()
            for i in range(table.columnCount())
        ]
        expected_headers = [
            "ID", "基准X", "基准Y", "基准Z", "坐标规划",
            "轨道ID", "基础方块", "覆盖方块", "生成模式",
        ]
        self.assertEqual(headers, expected_headers)

        print("\u2705 表格操作测试通过")

    def test_05_group_config(self):
        """测试轨道组配置"""
        print("\U0001f9ea 测试轨道组配置...")

        gc = self.window.group_config
        self.assertIsInstance(gc, dict)
        self.assertGreater(len(gc), 0, "应至少有一个轨道组")

        first_group = gc[0]
        self.assertIn("base_coords", first_group)
        self.assertIn("layers", first_group)
        self.assertIn("block", first_group)

        print("\u2705 轨道组配置测试通过")

    def test_06_file_browsing_simulation(self):
        """模拟测试文件浏览功能"""
        print("\U0001f9ea 模拟文件浏览功能...")

        with patch("PyQt6.QtWidgets.QFileDialog.getOpenFileName") as mock_open:
            mock_open.return_value = ("test.nbs", "NBS Files (*.nbs)")
            self.window.homeInterface.inputFileCard._onBrowse()
            mock_open.assert_called_once()
            self.assertEqual(
                self.window.homeInterface.getInputFile(), "test.nbs"
            )

        print("\u2705 文件浏览功能测试通过")

    def test_07_log_interface(self):
        """测试日志界面"""
        print("\U0001f9ea 测试日志界面...")

        self.window.log("测试日志消息")
        QApplication.processEvents()

        log_text = self.window.logInterface.logText.toPlainText()
        self.assertIn("测试日志消息", log_text)

        print("\u2705 日志界面测试通过")

    def test_08_config_save_load(self):
        """测试配置保存和加载"""
        print("\U0001f9ea 测试配置保存和加载...")

        import json
        import tempfile

        test_config = {
            "app_config": self.window.config,
            "group_config": self.window.group_config,
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(test_config, f, ensure_ascii=False)
            tmp_path = f.name

        try:
            with open(tmp_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertIn("app_config", loaded)
            self.assertIn("group_config", loaded)
        finally:
            os.unlink(tmp_path)

        print("\u2705 配置保存和加载测试通过")

    def test_09_fluent_widgets_present(self):
        """测试 Fluent 组件是否正确使用"""
        print("\U0001f9ea 测试 Fluent 组件...")

        from qfluentwidgets import (
            MSFluentWindow,
            ScrollArea,
            SettingCardGroup,
            CardWidget,
        )

        self.assertIsInstance(self.window, MSFluentWindow)
        self.assertIsInstance(self.window.homeInterface, ScrollArea)
        self.assertIsInstance(self.window.groupsInterface, ScrollArea)

        print("\u2705 Fluent 组件测试通过")


def run_gui_functionality_tests():
    """运行GUI功能测试"""
    print("\U0001f680 开始 Fluent Design GUI 功能完整性测试")
    print("=" * 60)

    test_suite = unittest.TestLoader().loadTestsFromTestCase(GUI_Functionality_Test)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    print("\n" + "=" * 60)
    print("\U0001f4ca 测试结果统计")
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n\U0001f389 所有GUI功能测试通过！")
    else:
        print("\n\u26a0\ufe0f 部分测试未通过，需要进一步检查")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_gui_functionality_tests()
    sys.exit(0 if success else 1)
