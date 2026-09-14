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


def test_activate_geotag_tab_with_context(qapp, tmp_path):
    window = MainWindow()
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"dummy")

    window._activate_geotag_tab(photo_path=photo, latitude=50.061947, longitude=19.936856)

    assert window.tabs.currentWidget() is window.geotag_panel
    assert window.geotag_panel.paths_list.count() == 1
    assert window.geotag_panel.paths_list.item(0).text() == str(photo)
    assert window.geotag_panel.lat_edit.text() == "50.061947"
    assert window.geotag_panel.lon_edit.text() == "19.936856"


def test_activate_geotag_tab_without_context(qapp):
    window = MainWindow()
    window.tabs.setCurrentIndex(0)

    window._activate_geotag_tab()

    assert window.tabs.currentWidget() is window.geotag_panel
    assert window.geotag_panel.paths_list.count() == 0
    assert window.geotag_panel.lat_edit.text() == ""


def test_handle_location_picked_from_map_activates_geotag_tab(qapp, tmp_path):
    window = MainWindow()
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"dummy")

    window._handle_location_picked_from_map(photo, 48.8566, 2.3522)

    assert window.tabs.currentWidget() is window.geotag_panel
    assert window.geotag_panel.paths_list.item(0).text() == str(photo)
    assert window.geotag_panel.lat_edit.text() == "48.856600"
    assert window.geotag_panel.lon_edit.text() == "2.352200"
