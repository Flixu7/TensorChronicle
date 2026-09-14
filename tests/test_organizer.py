import pytest
from pathlib import Path
from photo_organizer.organizer import organize_photos, OrganizerOptions

def test_organize_photos_copy(tmp_path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()

    f1 = in_dir / "12092011.png"
    f1.write_bytes(b"dummy photo content 1")
    
    f2 = in_dir / "01012022.jpg"
    f2.write_bytes(b"dummy photo content 2")

    f3 = in_dir / "duplicate.png"
    f3.write_bytes(b"dummy photo content 1")

    options = OrganizerOptions(
        input_dirs=[in_dir],
        output_dir=out_dir,
        mode="copy",
        dry_run=False,
        check_duplicates=True,
        collision_strategy="unique",
        num_workers=2
    )

    report = organize_photos(options)

    assert report.total_found == 3
    assert report.processed_count == 2
    assert len(report.skipped_files) == 1
    
    target_f1 = out_dir / "organized_photos" / "2011" / "jesień" / "12092011.png"
    target_f2 = out_dir / "organized_photos" / "2022" / "zima" / "01012022.jpg"

    assert target_f1.exists()
    assert target_f2.exists()
    assert f1.exists()

def test_organize_photos_dry_run(tmp_path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()

    f1 = in_dir / "15062015.jpg"
    f1.write_bytes(b"content")

    options = OrganizerOptions(
        input_dirs=[in_dir],
        output_dir=out_dir,
        mode="copy",
        dry_run=True
    )

    report = organize_photos(options)
    assert report.processed_count == 1
    target_f1 = out_dir / "organized_photos" / "2015" / "lato" / "15062015.jpg"
    assert not target_f1.exists()

def test_organize_video_files(tmp_path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()

    v1 = in_dir / "VID_20210815_120000.mp4"
    v1.write_bytes(b"dummy video content")

    options = OrganizerOptions(
        input_dirs=[in_dir],
        output_dir=out_dir,
        mode="copy"
    )

    report = organize_photos(options)
    assert report.processed_count == 1
    assert (out_dir / "organized_photos" / "2021" / "lato" / "VID_20210815_120000.mp4").exists()

