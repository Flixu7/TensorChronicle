import sys
from pathlib import Path
from typing import Optional, Tuple

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog,
    QTextEdit, QProgressBar, QGroupBox, QMessageBox, QDialog
)

from .geocoding import geocode_place
from .geotagger import apply_geotag_to_paths, GeotagReport
from .map_view import MapWidget, WEBENGINE_AVAILABLE
from .widgets import DropListWidget
from .theme import DARK_STYLESHEET, SPACE_4, SPACE_6


class GeocodeWorker(QThread):
    finished_signal = Signal(object)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self):
        result = geocode_place(self.query)
        self.finished_signal.emit(result)


class ApplyGeotagWorker(QThread):
    finished_signal = Signal(GeotagReport)

    def __init__(self, paths, latitude: float, longitude: float):
        super().__init__()
        self.paths = paths
        self.latitude = latitude
        self.longitude = longitude

    def run(self):
        report = apply_geotag_to_paths(self.paths, self.latitude, self.longitude)
        self.finished_signal.emit(report)


class MapPickerDialog(QDialog):
    """Okno z mapą (ten sam komponent co podgląd zdjęć) w trybie wyboru lokalizacji.

    Kliknięcie na mapie aktualizuje ``self.picked`` na bieżąco; okno pozostaje otwarte,
    dopóki użytkownik nie potwierdzi wyboru przyciskiem "Gotowe" (lub nie anuluje).
    """

    def __init__(self, initial_marker=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wybierz lokalizację na mapie")
        self.resize(800, 600)
        self.picked: Optional[Tuple[float, float]] = initial_marker

        layout = QVBoxLayout(self)

        if not WEBENGINE_AVAILABLE:
            layout.addWidget(QLabel(
                "Moduł QtWebEngine nie jest dostępny.\n"
                "Zainstaluj pakiet PySide6-Addons, aby wyświetlić mapę."
            ))
            btn_close = QPushButton("Zamknij")
            btn_close.clicked.connect(self.reject)
            layout.addWidget(btn_close)
            return

        self.map_widget = MapWidget(mode="picker", initial_marker=initial_marker, parent=self)
        self.map_widget.location_picked.connect(self._on_location_picked)
        layout.addWidget(self.map_widget, 1)

        layout.addWidget(QLabel(
            "Kliknij na mapie, aby ustawić współrzędne. Możesz kliknąć ponownie, aby poprawić."
        ))

        btn_done = QPushButton("Gotowe")
        btn_done.clicked.connect(self.accept)
        layout.addWidget(btn_done)

    def _on_location_picked(self, lat: float, lon: float):
        self.picked = (lat, lon)


class GeotagPanel(QWidget):
    """Panel dodawania geolokalizacji — osadzany jako zakładka w głównym oknie
    (``gui.py``) lub, opakowany w ``GeotagWindow``, uruchamiany samodzielnie."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACE_6, SPACE_6, SPACE_6, SPACE_6)
        main_layout.setSpacing(SPACE_6)

        paths_group = QGroupBox("Zdjęcia i Katalogi")
        paths_layout = QVBoxLayout(paths_group)
        paths_layout.setSpacing(SPACE_4)

        self.paths_list = DropListWidget()
        self.paths_list.paths_dropped.connect(self._add_dropped_paths)
        paths_layout.addWidget(self.paths_list)

        paths_btn_layout = QHBoxLayout()
        paths_btn_layout.setSpacing(SPACE_4)
        btn_add_dir = QPushButton("Dodaj Katalog")
        btn_add_dir.clicked.connect(self._add_directory)
        btn_add_files = QPushButton("Dodaj Pliki")
        btn_add_files.clicked.connect(self._add_files)
        btn_remove = QPushButton("Usuń Zaznaczone")
        btn_remove.clicked.connect(self._remove_selected)
        btn_clear = QPushButton("Wyczyść Listę")
        btn_clear.clicked.connect(self.paths_list.clear)

        paths_btn_layout.addWidget(btn_add_dir)
        paths_btn_layout.addWidget(btn_add_files)
        paths_btn_layout.addWidget(btn_remove)
        paths_btn_layout.addWidget(btn_clear)
        paths_layout.addLayout(paths_btn_layout)
        main_layout.addWidget(paths_group)

        location_group = QGroupBox("Lokalizacja")
        location_layout = QVBoxLayout(location_group)
        location_layout.setSpacing(SPACE_4)

        search_layout = QHBoxLayout()
        search_layout.setSpacing(SPACE_4)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("np. Kraków, Rynek Główny")
        self.search_edit.returnPressed.connect(self._search_location)
        self.btn_search = QPushButton("Szukaj")
        self.btn_search.clicked.connect(self._search_location)
        self.btn_pick_on_map = QPushButton("Wybierz na mapie")
        self.btn_pick_on_map.clicked.connect(self._pick_on_map)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_pick_on_map)
        location_layout.addLayout(search_layout)

        self.search_result_label = QLabel("")
        self.search_result_label.setWordWrap(True)
        location_layout.addWidget(self.search_result_label)

        coords_layout = QHBoxLayout()
        coords_layout.setSpacing(SPACE_4)
        coords_layout.addWidget(QLabel("Szerokość (lat):"))
        self.lat_edit = QLineEdit()
        self.lat_edit.setValidator(QDoubleValidator(-90.0, 90.0, 6))
        coords_layout.addWidget(self.lat_edit)

        coords_layout.addWidget(QLabel("Długość (lon):"))
        self.lon_edit = QLineEdit()
        self.lon_edit.setValidator(QDoubleValidator(-180.0, 180.0, 6))
        coords_layout.addWidget(self.lon_edit)
        location_layout.addLayout(coords_layout)

        main_layout.addWidget(location_group)

        self.btn_apply = QPushButton("Zastosuj Geolokalizację")
        self.btn_apply.setObjectName("primaryButton")
        self.btn_apply.setMinimumWidth(260)
        self.btn_apply.clicked.connect(self._apply_geotag)
        btn_apply_row = QHBoxLayout()
        btn_apply_row.addStretch(1)
        btn_apply_row.addWidget(self.btn_apply)
        btn_apply_row.addStretch(1)
        main_layout.addLayout(btn_apply_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        report_group = QGroupBox("Raport")
        report_layout = QVBoxLayout(report_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        report_layout.addWidget(self.log_text)
        main_layout.addWidget(report_group)

    def _add_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Wybierz katalog ze zdjęciami")
        if dir_path:
            self.paths_list.addItem(dir_path)

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Wybierz zdjęcia",
            filter="Obrazy (*.jpg *.jpeg *.png *.tiff *.tif *.webp *.heic *.heif);;Wszystkie pliki (*)"
        )
        for f in files:
            self.paths_list.addItem(f)

    def _remove_selected(self):
        for item in self.paths_list.selectedItems():
            self.paths_list.takeItem(self.paths_list.row(item))

    def _add_dropped_paths(self, paths):
        existing = {self.paths_list.item(i).text() for i in range(self.paths_list.count())}
        for p in paths:
            if p not in existing:
                self.paths_list.addItem(p)
                existing.add(p)

    def _search_location(self):
        query = self.search_edit.text().strip()
        if not query:
            QMessageBox.warning(self, "Błąd", "Wpisz nazwę miejsca do wyszukania.")
            return

        self.btn_search.setEnabled(False)
        self.btn_search.setText("Szukanie...")
        self.search_result_label.setText("")

        self.geocode_worker = GeocodeWorker(query)
        self.geocode_worker.finished_signal.connect(self._on_geocode_finished)
        self.geocode_worker.start()

    def _on_geocode_finished(self, result: Optional[Tuple[float, float, str]]):
        self.btn_search.setEnabled(True)
        self.btn_search.setText("Szukaj")

        if result is None:
            self.search_result_label.setText("Nie znaleziono lokalizacji. Sprawdź połączenie z internetem lub wpisz współrzędne ręcznie.")
            return

        latitude, longitude, display_name = result
        self.lat_edit.setText(f"{latitude:.6f}")
        self.lon_edit.setText(f"{longitude:.6f}")
        self.search_result_label.setText(f"Znaleziono: {display_name}")

    def _pick_on_map(self):
        initial_marker = self._current_coords()

        dialog = MapPickerDialog(initial_marker=initial_marker, parent=self)
        dialog.exec()

        if dialog.picked:
            latitude, longitude = dialog.picked
            self.lat_edit.setText(f"{latitude:.6f}")
            self.lon_edit.setText(f"{longitude:.6f}")
            self.search_result_label.setText(
                f"Lokalizacja wybrana na mapie: {latitude:.6f}, {longitude:.6f}"
            )

    def _current_coords(self) -> Optional[Tuple[float, float]]:
        lat_text = self.lat_edit.text().strip().replace(",", ".")
        lon_text = self.lon_edit.text().strip().replace(",", ".")
        if not lat_text or not lon_text:
            return None
        try:
            return float(lat_text), float(lon_text)
        except ValueError:
            return None

    def set_context(
        self,
        photo_path: Path,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ):
        """Ustawia zdjęcie i (opcjonalnie) współrzędne przekazane z podglądu mapy."""
        self.paths_list.clear()
        self.paths_list.addItem(str(photo_path))

        if latitude is not None and longitude is not None:
            self.lat_edit.setText(f"{latitude:.6f}")
            self.lon_edit.setText(f"{longitude:.6f}")
            self.search_result_label.setText(
                f"Lokalizacja ustawiona kliknięciem na mapie: {latitude:.6f}, {longitude:.6f}"
            )

    def _apply_geotag(self):
        path_count = self.paths_list.count()
        if path_count == 0:
            QMessageBox.warning(self, "Błąd", "Wskaż przynajmniej jeden katalog lub plik ze zdjęciami.")
            return

        lat_text = self.lat_edit.text().strip().replace(",", ".")
        lon_text = self.lon_edit.text().strip().replace(",", ".")
        try:
            latitude = float(lat_text)
            longitude = float(lon_text)
        except ValueError:
            QMessageBox.warning(self, "Błąd", "Podaj prawidłowe współrzędne (szerokość i długość geograficzną).")
            return

        if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
            QMessageBox.warning(self, "Błąd", "Współrzędne poza dopuszczalnym zakresem.")
            return

        paths = [Path(self.paths_list.item(i).text()) for i in range(path_count)]

        self.btn_apply.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.log_text.clear()
        self.log_text.append("Trwa zapisywanie metadanych GPS...")

        self.apply_worker = ApplyGeotagWorker(paths, latitude, longitude)
        self.apply_worker.finished_signal.connect(self._on_apply_finished)
        self.apply_worker.start()

    def _on_apply_finished(self, report: GeotagReport):
        self.btn_apply.setEnabled(True)
        self.progress_bar.setVisible(False)

        self.log_text.clear()
        self.log_text.append("=== RAPORT DODAWANIA GEOLOKALIZACJI ===")
        self.log_text.append(f"Znalezione pliki: {report.total_found}")
        self.log_text.append(f"Zaktualizowane pliki: {report.processed_count}")

        if report.skipped_files:
            self.log_text.append("\nPominięte pliki:")
            for filepath, reason in report.skipped_files.items():
                self.log_text.append(f"  - {filepath}: {reason}")

        if report.errors:
            self.log_text.append("\nBłędy:")
            for filepath, err in report.errors.items():
                self.log_text.append(f"  - {filepath}: {err}")


class GeotagWindow(QMainWindow):
    """Okno samodzielne wokół ``GeotagPanel`` — do uruchamiania geotaggera bez głównego GUI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dodawanie Geolokalizacji do Zdjęć")
        self.resize(780, 780)
        self.panel = GeotagPanel(self)
        self.setCentralWidget(self.panel)

    def __getattr__(self, name):
        return getattr(self.panel, name)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    window = GeotagWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
