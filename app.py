import sys
from nbs2save.gui.widgets import FluentApplication
from nbs2save.gui.window import NBSConverterGUI

# --------------------------
# 主程序入口
# --------------------------

if __name__ == "__main__":
    app = FluentApplication(sys.argv)

    window = NBSConverterGUI()
    window.show()

    sys.exit(app.exec())
