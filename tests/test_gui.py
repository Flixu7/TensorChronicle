import os
import sys
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from photo_organizer.gui import MainWindow

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

def test_main_window_init(qapp):
    window = MainWindow()
    assert window.windowTitle() == "Organizator Zdjęć - PySide6"
    assert window.input_list.count() == 0
    assert window.output_edit.text() == ""
