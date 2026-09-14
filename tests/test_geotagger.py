import pytest
from pathlib import Path
from PIL import Image

from photo_organizer.geotagger import write_gps_metadata, apply_geotag_to_paths
from photo_organizer.geolocation import extract_gps_coordinates


def _make_plain_jpeg(path: Path):
    Image.new("RGB", (20, 20), color="red").save(path, format="JPEG")


def test_write_gps_metadata_roundtrip_north_east(tmp_path):
    p = tmp_path / "photo.jpg"
    _make_plain_jpeg(p)

    write_gps_metadata(p, 50.061947, 19.936856)

    coords = extract_gps_coordinates(p)
    assert coords is not None
    lat, lon = coords
    assert lat == pytest.approx(50.061947, abs=1e-4)
    assert lon == pytest.approx(19.936856, abs=1e-4)


def test_write_gps_metadata_roundtrip_south_west(tmp_path):
    p = tmp_path / "photo.jpg"
    _make_plain_jpeg(p)

    write_gps_metadata(p, -33.865143, -151.209900)

    coords = extract_gps_coordinates(p)
    assert coords is not None
    lat, lon = coords
    assert lat == pytest.approx(-33.865143, abs=1e-4)
    assert lon == pytest.approx(-151.209900, abs=1e-4)


def test_write_gps_metadata_preserves_pixels(tmp_path):
    p = tmp_path / "photo.jpg"
    _make_plain_jpeg(p)

    with Image.open(p) as img:
        original_pixels = list(img.getdata())

    write_gps_metadata(p, 10.0, 20.0)

    with Image.open(p) as img:
        new_pixels = list(img.getdata())

    assert original_pixels == new_pixels


def test_write_gps_metadata_rejects_unsupported_format(tmp_path):
    p = tmp_path / "photo.png"
    Image.new("RGB", (10, 10), color="blue").save(p)

    with pytest.raises(ValueError):
        write_gps_metadata(p, 10.0, 20.0)


def test_apply_geotag_to_paths_mixed_dir_and_files(tmp_path):
    in_dir = tmp_path / "in"
    in_dir.mkdir()

    jpg1 = in_dir / "a.jpg"
    _make_plain_jpeg(jpg1)

    png1 = in_dir / "b.png"
    Image.new("RGB", (10, 10), color="green").save(png1)

    standalone_jpg = tmp_path / "standalone.jpg"
    _make_plain_jpeg(standalone_jpg)

    report = apply_geotag_to_paths([in_dir, standalone_jpg], 48.8566, 2.3522)

    assert report.total_found == 3
    assert report.processed_count == 2
    assert len(report.skipped_files) == 1
    assert str(png1) in report.skipped_files

    for jpg in (jpg1, standalone_jpg):
        coords = extract_gps_coordinates(jpg)
        assert coords is not None
        lat, lon = coords
        assert lat == pytest.approx(48.8566, abs=1e-4)
        assert lon == pytest.approx(2.3522, abs=1e-4)
