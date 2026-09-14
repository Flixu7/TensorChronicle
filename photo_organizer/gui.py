import sys
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog,
    QComboBox, QCheckBox, QSpinBox, QTextEdit, QProgressBar,
    QGroupBox, QMessageBox, QTabWidget
)

from concurrent.futures import ThreadPoolExecutor

from .organizer import organize_photos, OrganizerOptions, OrganizeReport
from .geolocation import collect_all_photos
from .map_view import PhotoMapDialog, thumbnail_data_uri
from .geotag_gui import GeotagPanel
from .widgets import DropListWidget
from .theme import DARK_STYLESHEET, SPACE_4, SPACE_6

class OrganizeWorker(QThread):
    finished_signal = Signal(OrganizeReport)

    def __init__(self, options: OrganizerOptions):
        super().__init__()
        self.options = options

    def run(self):
        report = organize_photos(self.options)
        self.finished_signal.emit(report)

class GeotagScanWorker(QThread):
    finished_signal = Signal(list)

    def __init__(self, input_dirs):
        super().__init__()
        self.input_dirs = input_dirs

    def run(self):
        photos = collect_all_photos(self.input_dirs)

        geotagged = [p for p in photos if p["lat"] is not None]
        if geotagged:
            # Miniaturki liczone równolegle tutaj (wątek roboczy), żeby PhotoMapDialog
            # mógł je od razu wstawić do HTML bez blokowania wątku UI przy otwarciu mapy.
            with ThreadPoolExecutor(max_workers=8) as executor:
                thumbs = executor.map(thumbnail_data_uri, (p["path"] for p in geotagged))
                for photo, thumb in zip(geotagged, thumbs):
                    photo["thumb"] = thumb

        self.finished_signal.emit(photos)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Organizator Zdjęć - PySide6")
        self.resize(860, 800)
        self._init_ui()

    def _init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        organize_tab = QWidget()
        self._init_organize_tab(organize_tab)
        self.tabs.addTab(organize_tab, "Organizacja")

        self.geotag_panel = GeotagPanel()
        self.tabs.addTab(self.geotag_panel, "Geolokalizacja")

    def _init_organize_tab(self, container):
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(SPACE_6, SPACE_6, SPACE_6, SPACE_6)
        main_layout.setSpacing(SPACE_6)

        input_group = QGroupBox("Katalogi Wejściowe")
        input_layout = QVBoxLayout(input_group)
        input_layout.setSpacing(SPACE_4)

        self.input_list = DropListWidget()
        self.input_list.paths_dropped.connect(self._add_dropped_paths)
        input_layout.addWidget(self.input_list)

        input_btn_layout = QHBoxLayout()
        input_btn_layout.setSpacing(SPACE_4)
        btn_add_dir = QPushButton("Dodaj Katalog")
        btn_add_dir.clicked.connect(self._add_input_dir)
        btn_remove_dir = QPushButton("Usuń Zaznaczony")
        btn_remove_dir.clicked.connect(self._remove_input_dir)
        btn_clear_dirs = QPushButton("Wyczyść Lista")
        btn_clear_dirs.clicked.connect(self.input_list.clear)

        btn_show_map = QPushButton("Pokaż na Mapie")
        btn_show_map.clicked.connect(self._show_photos_on_map)

        btn_open_geotagger = QPushButton("Przejdź do Geolokalizacji")
        btn_open_geotagger.clicked.connect(lambda: self._activate_geotag_tab())

        input_btn_layout.addWidget(btn_add_dir)
        input_btn_layout.addWidget(btn_remove_dir)
        input_btn_layout.addWidget(btn_clear_dirs)
        input_btn_layout.addWidget(btn_show_map)
        input_btn_layout.addWidget(btn_open_geotagger)
        input_layout.addLayout(input_btn_layout)
        main_layout.addWidget(input_group)

        output_group = QGroupBox("Katalog Docelowy")
        output_layout = QHBoxLayout(output_group)
        output_layout.setSpacing(SPACE_4)
        self.output_edit = QLineEdit()
        btn_browse_output = QPushButton("Przeglądaj...")
        btn_browse_output.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(btn_browse_output)
        main_layout.addWidget(output_group)

        opts_group = QGroupBox("Opcje Przetwarzania")
        opts_layout = QHBoxLayout(opts_group)
        opts_layout.setSpacing(SPACE_4)

        opts_layout.addWidget(QLabel("Tryb:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["copy", "move"])
        opts_layout.addWidget(self.mode_combo)

        opts_layout.addWidget(QLabel("Kolizje:"))
        self.collision_combo = QComboBox()
        self.collision_combo.addItems(["unique", "overwrite", "skip"])
        opts_layout.addWidget(self.collision_combo)

        self.dup_checkbox = QCheckBox("Sprawdzaj Duplikaty")
        self.dup_checkbox.setChecked(True)
        opts_layout.addWidget(self.dup_checkbox)

        self.dry_run_checkbox = QCheckBox("Dry-Run")
        opts_layout.addWidget(self.dry_run_checkbox)

        opts_layout.addWidget(QLabel("Wątki:"))
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 32)
        self.workers_spin.setValue(4)
        opts_layout.addWidget(self.workers_spin)

        main_layout.addWidget(opts_group)

        self.btn_start = QPushButton("Rozpocznij Organizację")
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.setMinimumWidth(260)
        self.btn_start.clicked.connect(self._start_processing)
        btn_start_row = QHBoxLayout()
        btn_start_row.addStretch(1)
        btn_start_row.addWidget(self.btn_start)
        btn_start_row.addStretch(1)
        main_layout.addLayout(btn_start_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        report_group = QGroupBox("Raport i Logi")
        report_layout = QVBoxLayout(report_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        report_layout.addWidget(self.log_text)
        main_layout.addWidget(report_group)

    def _add_input_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Wybierz katalog ze zdjęciami")
        if dir_path:
            self.input_list.addItem(dir_path)

    def _remove_input_dir(self):
        for item in self.input_list.selectedItems():
            self.input_list.takeItem(self.input_list.row(item))

    def _add_dropped_paths(self, paths):
        existing = {self.input_list.item(i).text() for i in range(self.input_list.count())}
        for p in paths:
            if p not in existing:
                self.input_list.addItem(p)
                existing.add(p)

    def _browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Wybierz katalog docelowy")
        if dir_path:
            self.output_edit.setText(dir_path)

    def _show_photos_on_map(self):
        input_count = self.input_list.count()
        if input_count == 0:
            QMessageBox.warning(self, "Błąd", "Wskaż przynajmniej jeden katalog wejściowy.")
            return

        input_dirs = [Path(self.input_list.item(i).text()) for i in range(input_count)]

        self.btn_show_map_enabled_widgets = self.sender()
        if self.btn_show_map_enabled_widgets:
            self.btn_show_map_enabled_widgets.setEnabled(False)
            self.btn_show_map_enabled_widgets.setText("Skanowanie EXIF...")

        self.map_worker = GeotagScanWorker(input_dirs)
        self.map_worker.finished_signal.connect(self._on_map_scan_finished)
        self.map_worker.start()

    def _on_map_scan_finished(self, photos):
        if self.btn_show_map_enabled_widgets:
            self.btn_show_map_enabled_widgets.setEnabled(True)
            self.btn_show_map_enabled_widgets.setText("Pokaż na Mapie")

        dialog = PhotoMapDialog(
            photos, parent=self, on_location_picked=self._handle_location_picked_from_map
        )
        dialog.exec()

    def _handle_location_picked_from_map(self, photo_path: Path, latitude: float, longitude: float):
        """Wywoływane, gdy użytkownik kliknie na mapie, aby ustawić lokalizację zdjęcia bez GPS."""
        self._activate_geotag_tab(photo_path=photo_path, latitude=latitude, longitude=longitude)

    def _activate_geotag_tab(
        self,
        photo_path: Optional[Path] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ):
        if photo_path is not None:
            self.geotag_panel.set_context(photo_path, latitude, longitude)
        self.tabs.setCurrentWidget(self.geotag_panel)

    def _start_processing(self):
        input_count = self.input_list.count()
        if input_count == 0:
            QMessageBox.warning(self, "Błąd", "Wskaż przynajmniej jeden katalog wejściowy.")
            return

        out_path = self.output_edit.text().strip()
        if not out_path:
            QMessageBox.warning(self, "Błąd", "Wskaż katalog docelowy.")
            return

        input_dirs = [Path(self.input_list.item(i).text()) for i in range(input_count)]
        output_dir = Path(out_path)

        options = OrganizerOptions(
            input_dirs=input_dirs,
            output_dir=output_dir,
            mode=self.mode_combo.currentText(),
            dry_run=self.dry_run_checkbox.isChecked(),
            check_duplicates=self.dup_checkbox.isChecked(),
            collision_strategy=self.collision_combo.currentText(),
            num_workers=self.workers_spin.value()
        )

        self.btn_start.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.log_text.clear()
        self.log_text.append("Trwa przetwarzanie zdjęć...")

        self.worker = OrganizeWorker(options)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, report: OrganizeReport):
        self.btn_start.setEnabled(True)
        self.progress_bar.setVisible(False)

        self.log_text.clear()
        self.log_text.append("=== RAPORT PRZETWARZANIA ZDJĘĆ ===")
        self.log_text.append(f"Znalezione pliki: {report.total_found}")
        self.log_text.append(f"Przetworzone pliki: {report.processed_count}")
        self.log_text.append("\nLiczba plików według roku i pory roku:")

        for year, seasons in sorted(report.counts_by_year_season.items()):
            for season, count in sorted(seasons.items()):
                season_label = f" -> {season}" if season else ""
                self.log_text.append(f"  - {year}{season_label}: {count}")

        if report.skipped_files:
            self.log_text.append("\nPominięte pliki:")
            for filepath, reason in report.skipped_files.items():
                self.log_text.append(f"  - {filepath}: {reason}")

        if report.errors:
            self.log_text.append("\nBłędy:")
            for filepath, err in report.errors.items():
                self.log_text.append(f"  - {filepath}: {err}")

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
