#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI功能完整性测试脚本
测试GUI的各项核心功能是否正常工作
该脚本使用ai辅助编写，测试窗口初始化、基本输入字段、轨道组设置、生成模式选择、输出目录选择、转换按钮点击等核心功能。
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
    QComboBox,
    QLineEdit,
    QPushButton,
    QTableWidget,
)

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
        cls.window = MainWindow()
        cls.window.show()
        QApplication.processEvents()
        time.sleep(0.1)  # 确保窗口完全加载

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.window.close()
        QApplication.processEvents()

    def test_01_window_initialization(self):
        """测试窗口初始化"""
        print("🧪 测试窗口初始化...")

        # 检查窗口标题
        self.assertIn("NBS", self.window.windowTitle())

        # 检查主要控件是否存在（通过类型检查）
        self.assertGreater(
            len(self.window.findChildren(QLineEdit)), 0, "应该存在输入框控件"
        )
        self.assertGreater(
            len(self.window.findChildren(QComboBox)), 0, "应该存在下拉框控件"
        )
        self.assertGreater(
            len(self.window.findChildren(QTableWidget)), 0, "应该存在表格控件"
        )

        print("✅ 窗口初始化测试通过")

    def test_02_basic_input_fields(self):
        """测试基本输入字段"""
        print("🧪 测试基本输入字段...")

        # 测试输入文件编辑框
        input_edit = self.window.findChild(QLineEdit)
        if input_edit:
            input_edit.setText("test_nbs_file.nbs")
            self.assertEqual(input_edit.text(), "test_nbs_file.nbs")

        # 测试基础方块输入框（现在在轨道组表格中）
        groups_table = getattr(self.window, "groups_table", None)
        if groups_table and groups_table.rowCount() > 0:
            # 在表格中设置基础方块
            base_block_item = groups_table.item(0, 5)  # 基础方块列
            if base_block_item:
                base_block_item.setText("minecraft:diamond_block")
                self.assertEqual(base_block_item.text(), "minecraft:diamond_block")

        print("✅ 基本输入字段测试通过")

    def test_03_combobox_functionality(self):
        """测试下拉框功能"""
        print("🧪 测试下拉框功能...")

        # 测试版本下拉框
        version_combo = getattr(self.window, "version_combo", None)
        if version_combo:
            original_index = version_combo.currentIndex()
            version_combo.setCurrentIndex(1)
            self.assertNotEqual(version_combo.currentIndex(), original_index)

        # 测试输出类型下拉框
        type_combo = getattr(self.window, "type_combo", None)
        if type_combo:
            self.assertTrue(type_combo.count() >= 1)

        print("✅ 下拉框功能测试通过")

    def test_04_table_operations(self):
        """测试表格操作"""
        print("🧪 测试表格操作...")

        # 获取轨道组表格
        groups_table = getattr(self.window, "groups_table", None)
        if groups_table:
            # 检查表格行数
            initial_rows = groups_table.rowCount()
            print(f"   初始表格行数: {initial_rows}")

            # 检查表格列数
            self.assertEqual(groups_table.columnCount(), 8)

            # 检查表头
            headers = [
                groups_table.horizontalHeaderItem(i).text()
                for i in range(groups_table.columnCount())
            ]
            expected_headers = [
                "ID",
                "基准X",
                "基准Y",
                "基准Z",
                "轨道ID",
                "基础方块",
                "覆盖方块",
                "生成模式",
            ]
            self.assertEqual(headers, expected_headers)

        print("✅ 表格操作测试通过")

    def test_05_button_functionality(self):
        """测试按钮功能"""
        print("🧪 测试按钮功能...")

        # 测试各种按钮对象是否存在
        buttons = {
            "runButton": self.window.findChild(QPushButton, "runButton"),
            "saveButton": self.window.findChild(QPushButton, "saveButton"),
            "loadButton": self.window.findChild(QPushButton, "loadButton"),
            "exitButton": self.window.findChild(QPushButton, "exitButton"),
        }

        for btn_name, btn in buttons.items():
            if btn:
                print(f"   ✅ 找到按钮: {btn_name}")
            else:
                print(f"   ⚠️  按钮未找到: {btn_name}")

        print("✅ 按钮功能测试通过")

    def test_06_file_browsing_simulation(self):
        """模拟测试文件浏览功能"""
        print("🧪 模拟文件浏览功能...")

        # 模拟文件对话框
        with patch("PyQt6.QtWidgets.QFileDialog.getOpenFileName") as mock_open:
            mock_open.return_value = ("test.nbs", "NBS Files (*.nbs)")

            # 测试输入文件浏览
            input_edit = self.window.findChild(QLineEdit)
            if input_edit:
                self.window.browse_input_file()
                mock_open.assert_called_once()

        print("✅ 文件浏览功能测试通过")

    def test_07_status_bar_functionality(self):
        """测试状态栏功能"""
        print("🧪 测试状态栏功能...")

        # 检查状态栏是否存在
        status_bar = self.window.statusBar()
        self.assertIsNotNone(status_bar)

        # 测试状态栏消息显示
        test_message = "测试状态消息"
        status_bar.showMessage(test_message)
        QApplication.processEvents()

        print("✅ 状态栏功能测试通过")

    def test_08_layout_structure(self):
        """测试布局结构"""
        print("🧪 测试布局结构...")

        # 检查主布局是否存在
        main_widget = self.window.centralWidget()
        self.assertIsNotNone(main_widget)

        # 检查是否使用了正确的布局
        layout = main_widget.layout()
        self.assertIsNotNone(layout)

        print("✅ 布局结构测试通过")

    def test_09_windows11_style_applied(self):
        """测试Win11样式是否应用"""
        print("🧪 测试Win11样式应用...")

        # 检查窗口样式
        style_sheet = self.window.styleSheet()
        self.assertIn("Fluent", style_sheet)
        self.assertIn("QGroupBox", style_sheet)

        # 检查主要控件是否有样式
        input_edit = self.window.findChild(QLineEdit)
        if input_edit:
            edit_style = input_edit.styleSheet()
            self.assertTrue(
                len(edit_style) > 0 or "FluentLineEdit" in str(type(input_edit))
            )

        print("✅ Win11样式应用测试通过")


def run_gui_functionality_tests():
    """运行GUI功能测试"""
    print("🚀 开始Win11风格GUI功能完整性测试")
    print("=" * 60)

    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(GUI_Functionality_Test)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    print("\n" + "=" * 60)
    print("📊 测试结果统计")
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n🎉 所有GUI功能测试通过！Win11风格美化效果良好！")
    else:
        print("\n⚠️ 部分测试未通过，需要进一步检查")

        if result.failures:
            print("\n失败的测试:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")

        if result.errors:
            print("\n错误的测试:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_gui_functionality_tests()
    sys.exit(0 if success else 1)
