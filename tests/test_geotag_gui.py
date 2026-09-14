import os
import sys
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import photo_organizer.geotag_gui as geotag_gui_module
from photo_organizer.geotag_gui import GeotagWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class _FakeMapPickerDialog:
    """Zastępuje prawdziwy MapPickerDialog w testach, by uniknąć blokującego exec()
    (prawdziwe okno ładuje QWebEngineView i czeka na interakcję użytkownika)."""

    last_initial_marker = None

    def __init__(self, initial_marker=None, parent=None):
        _FakeMapPickerDialog.last_initial_marker = initial_marker
        self.picked = (52.2297, 21.0122)

    def exec(self):
        return None


def test_pick_on_map_fills_coordinate_fields(qapp, monkeypatch):
    monkeypatch.setattr(geotag_gui_module, "MapPickerDialog", _FakeMapPickerDialog)

    window = GeotagWindow()
    window._pick_on_map()

    assert window.lat_edit.text() == "52.229700"
    assert window.lon_edit.text() == "21.012200"
    assert "52.229700" in window.search_result_label.text()


def test_pick_on_map_passes_current_coords_as_initial_marker(qapp, monkeypatch):
    monkeypatch.setattr(geotag_gui_module, "MapPickerDialog", _FakeMapPickerDialog)

    window = GeotagWindow()
    window.lat_edit.setText("10.5")
    window.lon_edit.setText("20.5")

    window._pick_on_map()

    assert _FakeMapPickerDialog.last_initial_marker == (10.5, 20.5)


def test_pick_on_map_with_no_prior_coords_has_no_initial_marker(qapp, monkeypatch):
    monkeypatch.setattr(geotag_gui_module, "MapPickerDialog", _FakeMapPickerDialog)

    window = GeotagWindow()
    window._pick_on_map()

    assert _FakeMapPickerDialog.last_initial_marker is None


def test_set_context_prefills_photo_and_coordinates(qapp, tmp_path):
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"dummy")

    window = GeotagWindow()
    window.set_context(photo, 48.8566, 2.3522)

    assert window.paths_list.count() == 1
    assert window.paths_list.item(0).text() == str(photo)
    assert window.lat_edit.text() == "48.856600"
    assert window.lon_edit.text() == "2.352200"
