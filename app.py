#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ==============================================================================
# NBS到Minecraft结构转换工具 GUI启动入口
# ==============================================================================
# 该文件是程序的图形用户界面(GUI)启动入口
# 负责初始化GUI应用程序并显示主窗口
# 用户可以通过运行该文件启动图形界面版本的转换工具

import sys

# 从项目模块中导入所需的GUI组件
# FluentApplication: 自定义的Fluent Design风格应用程序类
# NBSConverterGUI: 主窗口类，包含所有GUI功能
from nbs2save.gui.widgets import FluentApplication
from nbs2save.gui.window import NBSConverterGUI

# --------------------------
# 主程序入口点
# --------------------------
# 程序的执行从这里开始
# 当直接运行该脚本时，__name__变量的值为"__main__"，条件成立
# 如果该模块被其他模块导入，则不会执行以下代码
if __name__ == "__main__":
    # 创建Fluent Design风格的应用程序实例
    # sys.argv参数包含了命令行参数，传递给Qt应用程序
    app = FluentApplication(sys.argv)

    # 创建主窗口实例
    # NBSConverterGUI类封装了所有GUI功能和界面元素
    window = NBSConverterGUI()
    
    # 显示主窗口
    # show()方法使窗口可见
    window.show()

    # 启动应用程序的事件循环
    # exec()方法开始处理用户交互，如点击按钮、输入文本等
    # sys.exit()确保程序正常退出并返回适当的退出码
    sys.exit(app.exec())