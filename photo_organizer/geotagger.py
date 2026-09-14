import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

import piexif

WRITABLE_EXTENSIONS: Set[str] = {".jpg", ".jpeg"}
DEFAULT_WRITE_WORKERS = 8


@dataclass
class GeotagReport:
    total_found: int = 0
    processed_count: int = 0
    skipped_files: Dict[str, str] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)


def _decimal_to_dms_rational(value: float):
    value = abs(value)
    degrees = int(value)
    minutes_float = (value - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60 * 100)

    if seconds >= 6000:
        seconds -= 6000
        minutes += 1
    if minutes >= 60:
        minutes -= 60
        degrees += 1

    return ((degrees, 1), (minutes, 1), (seconds, 100))


def write_gps_metadata(path: Path, latitude: float, longitude: float) -> None:
    """Zapisuje współrzędne GPS w metadanych EXIF pliku JPEG, bez ponownej kompresji obrazu."""
    path = Path(path)
    if path.suffix.lower() not in WRITABLE_EXTENSIONS:
        raise ValueError(f"Format {path.suffix} nie jest obsługiwany do zapisu metadanych GPS (tylko JPEG).")

    try:
        exif_dict = piexif.load(str(path))
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    exif_dict["GPS"] = {
        piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: "N" if latitude >= 0 else "S",
        piexif.GPSIFD.GPSLatitude: _decimal_to_dms_rational(latitude),
        piexif.GPSIFD.GPSLongitudeRef: "E" if longitude >= 0 else "W",
        piexif.GPSIFD.GPSLongitude: _decimal_to_dms_rational(longitude),
    }

    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, str(path))


def _collect_files(paths: List[Path]) -> List[Path]:
    from .organizer import SUPPORTED_EXTENSIONS

    files: List[Path] = []
    for raw_path in paths:
        p = Path(raw_path)
        if p.is_dir():
            for sub in p.rglob("*"):
                if sub.is_file() and sub.suffix.lower() in SUPPORTED_EXTENSIONS:
                    files.append(sub)
        elif p.is_file():
            files.append(p)
    return files


def apply_geotag_to_paths(
    paths: List[Path],
    latitude: float,
    longitude: float,
    num_workers: int = DEFAULT_WRITE_WORKERS,
) -> GeotagReport:
    """Zapisuje podane współrzędne GPS we wszystkich obsługiwanych zdjęciach w podanych
    ścieżkach (plikach i/lub katalogach). Zapis poszczególnych plików jest zrównoleglony
    wątkami (operacje dyskowe), tak jak przetwarzanie plików w organizer.py."""
    report = GeotagReport()
    files = _collect_files(paths)
    report.total_found = len(files)
    lock = threading.Lock()

    def process_single_file(file_path: Path):
        if file_path.suffix.lower() not in WRITABLE_EXTENSIONS:
            with lock:
                report.skipped_files[str(file_path)] = f"Format {file_path.suffix} nieobsługiwany (tylko JPEG)."
            return
        try:
            write_gps_metadata(file_path, latitude, longitude)
            with lock:
                report.processed_count += 1
        except Exception as e:
            with lock:
                report.errors[str(file_path)] = str(e)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(process_single_file, f) for f in files]
        for future in as_completed(futures):
            future.result()

    return report
