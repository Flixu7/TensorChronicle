import pytest
from pathlib import Path
from PIL import Image, ExifTags

from photo_organizer.geolocation import extract_gps_coordinates, collect_geotagged_photos


def _make_photo_with_gps(path: Path, lat_dms, lat_ref, lon_dms, lon_ref):
    img = Image.new("RGB", (10, 10), color="red")
    exif = img.getexif()
    exif[ExifTags.IFD.GPSInfo] = {
        1: lat_ref,
        2: lat_dms,
        3: lon_ref,
        4: lon_dms,
    }
    img.save(path, exif=exif)


def test_extract_gps_coordinates_north_east(tmp_path):
    p = tmp_path / "photo.jpg"
    _make_photo_with_gps(p, (40.0, 26.0, 46.0), "N", (14.0, 27.0, 35.0), "E")

    coords = extract_gps_coordinates(p)

    assert coords is not None
    lat, lon = coords
    assert lat == pytest.approx(40.446111, rel=1e-4)
    assert lon == pytest.approx(14.459722, rel=1e-4)


def test_extract_gps_coordinates_south_west(tmp_path):
    p = tmp_path / "photo.jpg"
    _make_photo_with_gps(p, (33.0, 51.0, 32.0), "S", (18.0, 25.0, 26.0), "W")

    coords = extract_gps_coordinates(p)

    assert coords is not None
    lat, lon = coords
    assert lat < 0
    assert lon < 0


def test_extract_gps_coordinates_missing_returns_none(tmp_path):
    p = tmp_path / "no_gps.jpg"
    Image.new("RGB", (10, 10), color="blue").save(p)

    assert extract_gps_coordinates(p) is None


def test_collect_geotagged_photos_filters_by_gps(tmp_path):
    in_dir = tmp_path / "in"
    in_dir.mkdir()

    with_gps = in_dir / "with_gps.jpg"
    _make_photo_with_gps(with_gps, (40.0, 26.0, 46.0), "N", (14.0, 27.0, 35.0), "E")

    without_gps = in_dir / "without_gps.jpg"
    Image.new("RGB", (10, 10), color="green").save(without_gps)

    results = collect_geotagged_photos([in_dir])

    assert len(results) == 1
    assert results[0]["path"] == with_gps
    assert results[0]["lat"] == pytest.approx(40.446111, rel=1e-4)
    assert results[0]["lon"] == pytest.approx(14.459722, rel=1e-4)
