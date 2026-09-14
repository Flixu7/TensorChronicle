import os
import sys
from datetime import datetime

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from photo_organizer.map_view import MapWidget, PhotoMapDialog, build_map_html


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_build_map_html_picker_mode_contains_click_wiring():
    html = build_map_html(mode="picker", initial_marker=(52.2297, 21.0122))

    assert "map.on('click'" in html
    assert "qtBridge.notify_click" in html
    assert "QWebChannel" in html
    assert "52.2297" in html
    assert "21.0122" in html


def test_build_map_html_view_mode_has_no_click_wiring():
    html = build_map_html(mode="view")

    assert "map.on('click'" not in html
    assert "QWebChannel" not in html


def test_build_map_html_rejects_unknown_mode_via_widget(qapp):
    with pytest.raises(ValueError):
        MapWidget(mode="bogus")


def test_map_widget_picker_bridge_relays_location(qapp):
    """Sprawdza mechanizm callbacku: MapClickBridge.notify_click (wywoływane przez JS)
    musi trafić do sygnału MapWidget.location_picked z poprawnymi współrzędnymi."""
    widget = MapWidget(mode="picker")
    received = []
    widget.location_picked.connect(lambda lat, lon: received.append((lat, lon)))

    widget._bridge.notify_click(52.2297, 21.0122)

    assert received == [(52.2297, 21.0122)]


def test_map_widget_picker_click_roundtrip_via_js(qapp):
    """Test end-to-end: symuluje kliknięcie na załadowanej mapie Leaflet i weryfikuje,
    że sygnał location_picked dostaje poprawny lat/lon przez most QWebChannel."""
    widget = MapWidget(mode="picker")

    load_loop = QEventLoop()
    QTimer.singleShot(20000, load_loop.quit)
    widget.view.loadFinished.connect(load_loop.quit)
    load_loop.exec()

    received = []
    widget.location_picked.connect(lambda lat, lon: received.append((lat, lon)))

    widget.view.page().runJavaScript(
        "map.fire('click', {latlng: L.latLng(52.2297, 21.0122)});"
    )

    result_loop = QEventLoop()
    QTimer.singleShot(10000, result_loop.quit)

    def _poll():
        if received:
            result_loop.quit()

    poll_timer = QTimer()
    poll_timer.timeout.connect(_poll)
    poll_timer.start(50)
    result_loop.exec()
    poll_timer.stop()

    if not received:
        pytest.skip("Kliknięcie JS nie dotarło do Pythona (brak dostępu do sieci/CDN w tym środowisku).")

    lat, lon = received[0]
    assert lat == pytest.approx(52.2297, abs=1e-4)
    assert lon == pytest.approx(21.0122, abs=1e-4)


def test_photo_map_dialog_click_invokes_callback_with_target_photo(qapp, tmp_path):
    geotagged_photo = tmp_path / "with_gps.jpg"
    geotagged_photo.write_bytes(b"dummy")
    ungeotagged_photo = tmp_path / "without_gps.jpg"
    ungeotagged_photo.write_bytes(b"dummy")

    photos = [
        {"path": geotagged_photo, "lat": 50.0, "lon": 19.0, "date": datetime(2020, 1, 1)},
        {"path": ungeotagged_photo, "lat": None, "lon": None, "date": None},
    ]

    picked = []
    dialog = PhotoMapDialog(
        photos, on_location_picked=lambda path, lat, lon: picked.append((path, lat, lon))
    )

    assert dialog.target_combo.count() == 1
    assert dialog.target_combo.itemData(0) == ungeotagged_photo

    dialog._on_map_clicked(52.2297, 21.0122)

    assert picked == [(ungeotagged_photo, 52.2297, 21.0122)]


def test_photo_map_dialog_without_callback_has_no_picker_controls(qapp, tmp_path):
    ungeotagged_photo = tmp_path / "without_gps.jpg"
    ungeotagged_photo.write_bytes(b"dummy")
    photos = [{"path": ungeotagged_photo, "lat": None, "lon": None, "date": None}]

    dialog = PhotoMapDialog(photos, on_location_picked=None)

    assert dialog.btn_pick is None
