#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI入口
----------
通过图形界面方式调用NBS转换工具，适用于普通用户操作
"""

import sys
from PyQt6.QtWidgets import QApplication

from nbs2save.gui.window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
