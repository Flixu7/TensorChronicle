from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ExifTags
from PIL.ExifTags import GPSTAGS

from .date_extractor import extract_date

DEFAULT_SCAN_WORKERS = 8


def _convert_to_degrees(value) -> float:
    d, m, s = value
    return float(d) + float(m) / 60.0 + float(s) / 3600.0


def extract_gps_coordinates(path: Path) -> Optional[Tuple[float, float]]:
    """Odczytuje współrzędne GPS (szerokość, długość) z metadanych EXIF zdjęcia."""
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return None

            gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
            if not gps_ifd:
                return None

            gps_data = {GPSTAGS.get(tag, tag): val for tag, val in gps_ifd.items()}

            lat = gps_data.get("GPSLatitude")
            lat_ref = gps_data.get("GPSLatitudeRef")
            lon = gps_data.get("GPSLongitude")
            lon_ref = gps_data.get("GPSLongitudeRef")

            if lat is None or lon is None or not lat_ref or not lon_ref:
                return None

            latitude = _convert_to_degrees(lat)
            if str(lat_ref).upper().startswith("S"):
                latitude = -latitude

            longitude = _convert_to_degrees(lon)
            if str(lon_ref).upper().startswith("W"):
                longitude = -longitude

            return latitude, longitude
    except Exception:
        return None


def _read_photo_entry(path: Path) -> Dict:
    coords = extract_gps_coordinates(path)
    date, _source = extract_date(path)
    return {
        "path": path,
        "lat": coords[0] if coords else None,
        "lon": coords[1] if coords else None,
        "date": date,
    }


def collect_all_photos(input_dirs: List[Path], num_workers: int = DEFAULT_SCAN_WORKERS) -> List[Dict]:
    """Przeszukuje katalogi wejściowe i zwraca wszystkie obsługiwane zdjęcia.

    Każdy wpis zawiera ``lat``/``lon`` (None, jeśli zdjęcie nie ma danych GPS w EXIF)
    oraz ``date`` wyznaczoną tą samą logiką co organizer (EXIF / nazwa pliku / system plików).
    Odczyt EXIF poszczególnych plików (operacje wejścia/wyjścia) jest zrównoleglony wątkami,
    tak jak przetwarzanie plików w organizer.py.
    """
    from .organizer import SUPPORTED_EXTENSIONS

    files: List[Path] = []
    for input_dir in input_dirs:
        input_dir = Path(input_dir)
        if not input_dir.exists():
            continue
        if input_dir.is_file():
            if input_dir.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(input_dir)
            continue
        for path in input_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(path)

    if not files:
        return []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        return list(executor.map(_read_photo_entry, files))


def collect_geotagged_photos(input_dirs: List[Path]) -> List[Dict]:
    """Przeszukuje katalogi wejściowe i zwraca listę zdjęć zawierających dane GPS."""
    return [p for p in collect_all_photos(input_dirs) if p["lat"] is not None]
