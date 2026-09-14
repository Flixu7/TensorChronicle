import base64
import io
import json
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebChannel import QWebChannel
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False

DEFAULT_CENTER = (51.9194, 19.1451)  # Środek Polski, gdy brak zdjęć z GPS ani punktu startowego


def thumbnail_data_uri(path: Path, max_size=(160, 160)) -> str:
    """Buduje miniaturkę zdjęcia jako data URI (JPEG, base64). Kosztowne operacyjnie (I/O +
    dekodowanie obrazu) — wołający, który przetwarza wiele zdjęć, powinien to robić poza
    wątkiem UI i najlepiej równolegle (patrz GeotagScanWorker w gui.py)."""
    from PIL import Image

    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail(max_size)
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=70)
            encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
            return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        return ""


def build_map_html(
    photos: Optional[List[Dict]] = None,
    mode: str = "view",
    initial_marker: Optional[Tuple[float, float]] = None,
) -> str:
    """Buduje stronę HTML z mapą Leaflet/OSM.

    mode="view": statyczne znaczniki dla zdjęć posiadających współrzędne GPS (z miniaturką w popupie).
    mode="picker": mapa nasłuchuje kliknięć i zwraca współrzędne do Pythona przez QWebChannel
      (sygnał ``location_picked`` na obiekcie ``bridge``); opcjonalnie pokazuje też znaczniki
      kontekstowe z ``photos`` oraz wstępny znacznik w miejscu ``initial_marker``.
    """
    photos = photos or []
    geotagged = [p for p in photos if p.get("lat") is not None and p.get("lon") is not None]

    if geotagged:
        avg_lat = sum(p["lat"] for p in geotagged) / len(geotagged)
        avg_lon = sum(p["lon"] for p in geotagged) / len(geotagged)
        zoom = 12
    elif initial_marker:
        avg_lat, avg_lon = initial_marker
        zoom = 13
    else:
        avg_lat, avg_lon = DEFAULT_CENTER
        zoom = 5

    markers = []
    for photo in geotagged:
        thumb = photo.get("thumb")
        if thumb is None:
            thumb = thumbnail_data_uri(photo["path"])
        name = photo["path"].name
        date = photo.get("date")
        date_str = date.strftime("%Y-%m-%d") if date else "nieznana data"

        popup_html = '<div style="text-align:center;font-family:sans-serif;">'
        popup_html += f'<b>{name}</b><br>{date_str}'
        if thumb:
            popup_html += (
                f'<br><img src="{thumb}" '
                f'style="max-width:160px;max-height:160px;margin-top:4px;border-radius:4px;"/>'
            )
        popup_html += "</div>"

        markers.append({"lat": photo["lat"], "lon": photo["lon"], "popup": popup_html})

    markers_json = json.dumps(markers)

    picker_js = ""
    webchannel_script = ""
    if mode == "picker":
        webchannel_script = '<script src="qrc:///qtwebchannel/qwebchannel.js"></script>'
        initial_marker_json = json.dumps(list(initial_marker)) if initial_marker else "null"
        picker_js = f"""
  var pickedMarker = null;
  var initialPick = {initial_marker_json};
  var qtBridge = null;

  function setPicked(lat, lon) {{
      if (pickedMarker) {{ map.removeLayer(pickedMarker); }}
      pickedMarker = L.marker([lat, lon]).addTo(map);
      if (qtBridge) {{ qtBridge.notify_click(lat, lon); }}
  }}

  if (initialPick) {{ setPicked(initialPick[0], initialPick[1]); }}

  map.on('click', function (e) {{
      setPicked(e.latlng.lat, e.latlng.lng);
  }});

  new QWebChannel(qt.webChannelTransport, function (channel) {{
      qtBridge = channel.objects.bridge;
  }});
"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
{webchannel_script}
<style>html, body, #map {{ height: 100%; margin: 0; padding: 0; }}</style>
</head>
<body>
<div id="map"></div>
<script>
  const map = L.map('map').setView([{avg_lat}, {avg_lon}], {zoom});
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
  }}).addTo(map);

  const markers = {markers_json};
  const bounds = [];
  markers.forEach(function (m) {{
      const marker = L.marker([m.lat, m.lon]).addTo(map);
      marker.bindPopup(m.popup);
      bounds.push([m.lat, m.lon]);
  }});
  if (bounds.length > 1) {{
      map.fitBounds(bounds, {{ padding: [40, 40] }});
  }}
{picker_js}
</script>
</body>
</html>"""


class MapClickBridge(QObject):
    """Most QWebChannel: przekazuje kliknięcia na mapie (JS) do sygnału Qt (Python)."""

    location_picked = Signal(float, float)

    @Slot(float, float)
    def notify_click(self, lat: float, lon: float):
        self.location_picked.emit(lat, lon)


class MapWidget(QWidget):
    """Reużywalny komponent mapy Leaflet/OSM, współdzielony przez podgląd zdjęć i wybór lokalizacji.

    mode="view": pokazuje znaczniki zdjęć z ``photos`` (wymagają lat/lon).
    mode="picker": kliknięcie na mapie emituje sygnał ``location_picked(lat, lon)``;
      ``photos`` (opcjonalnie) są wyświetlane jako znaczniki kontekstowe, a ``initial_marker``
      ustawia wstępną pozycję znacznika wyboru.
    """

    location_picked = Signal(float, float)

    def __init__(
        self,
        mode: str = "view",
        photos: Optional[List[Dict]] = None,
        initial_marker: Optional[Tuple[float, float]] = None,
        parent=None,
    ):
        super().__init__(parent)
        if mode not in ("view", "picker"):
            raise ValueError(f"Nieznany tryb mapy: {mode}")

        self.mode = mode
        self.view = None
        self._bridge = None
        self._channel = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if not WEBENGINE_AVAILABLE:
            layout.addWidget(QLabel(
                "Moduł QtWebEngine nie jest dostępny.\n"
                "Zainstaluj pakiet PySide6-Addons, aby wyświetlić mapę."
            ))
            return

        self.view = QWebEngineView()

        if mode == "picker":
            self._bridge = MapClickBridge()
            self._bridge.location_picked.connect(self.location_picked)
            self._channel = QWebChannel()
            self._channel.registerObject("bridge", self._bridge)
            self.view.page().setWebChannel(self._channel)

        html = build_map_html(photos=photos, mode=mode, initial_marker=initial_marker)
        self.view.setHtml(html, baseUrl=QUrl("https://unpkg.com/"))
        layout.addWidget(self.view)


class PhotoMapDialog(QDialog):
    """Okno prezentujące zdjęcia na mapie na podstawie ich współrzędnych GPS.

    Dla zdjęć bez GPS umożliwia wskazanie lokalizacji kliknięciem na mapie — wybrana
    lokalizacja jest przekazywana do ``on_location_picked(photo_path, lat, lon)``, co
    pozwala wywołującemu (np. gui.py) otworzyć geotagger z gotowym kontekstem.
    """

    def __init__(
        self,
        photos: List[Dict],
        parent=None,
        on_location_picked: Optional[Callable[[Path, float, float], None]] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Zdjęcia na mapie")
        self.resize(900, 750)

        self._on_location_picked = on_location_picked
        self._geotagged = [p for p in photos if p.get("lat") is not None and p.get("lon") is not None]
        self._ungeotagged = [p for p in photos if p.get("lat") is None or p.get("lon") is None]
        self.map_widget: Optional[MapWidget] = None

        layout = QVBoxLayout(self)

        if not WEBENGINE_AVAILABLE:
            layout.addWidget(QLabel(
                "Moduł QtWebEngine nie jest dostępny.\n"
                "Zainstaluj pakiet PySide6-Addons, aby wyświetlić mapę."
            ))
            return

        if not photos:
            layout.addWidget(QLabel(
                "Nie znaleziono obsługiwanych zdjęć w wybranych katalogach."
            ))
            return

        if self._ungeotagged and self._on_location_picked:
            picker_row = QHBoxLayout()
            picker_row.addWidget(QLabel("Zdjęcie bez lokalizacji:"))
            self.target_combo = QComboBox()
            for photo in self._ungeotagged:
                self.target_combo.addItem(photo["path"].name, photo["path"])
            picker_row.addWidget(self.target_combo, 1)

            self.btn_pick = QPushButton("Kliknij na mapie, aby ustawić lokalizację")
            self.btn_pick.setCheckable(True)
            self.btn_pick.toggled.connect(self._toggle_picking)
            picker_row.addWidget(self.btn_pick)
            layout.addLayout(picker_row)
        else:
            self.btn_pick = None

        self.map_container = QWidget()
        self.map_container_layout = QVBoxLayout(self.map_container)
        self.map_container_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.map_container, 1)

        if not self._geotagged:
            layout.addWidget(QLabel(
                "Żadne ze zdjęć nie zawiera danych geolokalizacyjnych (EXIF GPS)."
            ))

        self._set_map_mode("view")

    def _set_map_mode(self, mode: str):
        if self.map_widget is not None:
            self.map_container_layout.removeWidget(self.map_widget)
            self.map_widget.deleteLater()
            self.map_widget = None

        self.map_widget = MapWidget(mode=mode, photos=self._geotagged, parent=self.map_container)
        if mode == "picker":
            self.map_widget.location_picked.connect(self._on_map_clicked)
        self.map_container_layout.addWidget(self.map_widget)

    def _toggle_picking(self, checked: bool):
        if checked:
            self.btn_pick.setText("Kliknij na mapie... (Anuluj)")
            self._set_map_mode("picker")
        else:
            self.btn_pick.setText("Kliknij na mapie, aby ustawić lokalizację")
            self._set_map_mode("view")

    def _on_map_clicked(self, lat: float, lon: float):
        target_path = self.target_combo.currentData()
        if target_path is None or self._on_location_picked is None:
            return

        if self.btn_pick is not None:
            self.btn_pick.setChecked(False)

        self._on_location_picked(target_path, lat, lon)
