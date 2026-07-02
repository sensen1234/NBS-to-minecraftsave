#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI入口
----------
通过图形界面方式调用NBS转换工具，适用于普通用户操作
"""

import io
import sys

# 屏蔽 QFluentWidgets 的 Pro 广告 Tips
_real_stdout = sys.stdout
sys.stdout = io.StringIO()
from qfluentwidgets import setThemeColor, setTheme, Theme
sys.stdout = _real_stdout

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from nbs2save.gui.window import MainWindow


def main() -> None:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("NBS-to-Minecraftsave")
    app.setApplicationVersion("2.4.0")

    # 设置强调色与主题（自动跟随系统明暗）
    setThemeColor('#0078d4')
    setTheme(Theme.AUTO)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
