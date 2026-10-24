"""Exercise native Qt theme changes in a child process so crashes are isolated."""

import os
from pathlib import Path
import subprocess
import sys
import unittest


_SMOKE = r'''
from unittest.mock import patch
from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QWidget
from qfluentwidgets import PlainTextEdit, Theme, setTheme
from nbs2save.gui.window import MainWindow

app = QApplication([])
windows = []
for initial, alternate in ((Theme.LIGHT, Theme.DARK), (Theme.DARK, Theme.LIGHT)):
    # Also switch theme after the previous window has closed, before deleting it.
    setTheme(initial)
    with patch.object(MainWindow, 'load_last_config'):
        window = MainWindow()
    windows.append(window)
    window.resize(800, 600)
    window.show()
    window.switchTo(window.wikiInterface)
    QTest.qWait(50)
    wiki = window.wikiInterface
    title = wiki.titleLabel
    child_count = len(wiki.findChildren(QWidget))
    arrow, section = wiki._toc_sections[0]
    section.hide()
    arrow.setText('\u25b8')
    code = wiki.findChild(PlainTextEdit)
    assert code is not None
    for theme in (alternate, initial, alternate):
        setTheme(theme)
        QTest.qWait(50)
        assert wiki.titleLabel is title, 'theme change rebuilt the wiki'
        assert len(wiki.findChildren(QWidget)) == child_count, 'theme change leaked widgets'
        assert section.isHidden(), 'theme change reset the table of contents'
        color = '#1e1e1e' if theme == Theme.DARK else '#f8f8f8'
        assert color in code.styleSheet(), 'code palette failed to follow the theme'
    window.close()
    app.processEvents()
for window in windows:
    window.deleteLater()
QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
setTheme(Theme.LIGHT)
QTest.qWait(50)
print('THEME_SMOKE_OK')
'''


class ThemeLifecycleTests(unittest.TestCase):
    def test_theme_changes_keep_open_and_closed_windows_safe(self):
        root = Path(__file__).resolve().parents[1]
        environment = os.environ.copy()
        environment['QT_QPA_PLATFORM'] = 'offscreen'
        environment['PYTHONPATH'] = str(root / 'src') + os.pathsep + environment.get('PYTHONPATH', '')
        result = subprocess.run(
            [sys.executable, '-X', 'faulthandler', '-c', _SMOKE], cwd=root,
            env=environment, capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=45,
        )
        self.assertEqual(result.returncode, 0, result.stdout + '\n' + result.stderr)
        self.assertIn('THEME_SMOKE_OK', result.stdout)


if __name__ == '__main__':
    unittest.main()
