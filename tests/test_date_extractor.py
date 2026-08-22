from datetime import datetime
from pathlib import Path
from photo_organizer.date_extractor import extract_filename_date, extract_date
from photo_organizer.season import get_season

def test_get_season():
    assert get_season(3) == "wiosna"
    assert get_season(5) == "wiosna"
    assert get_season(6) == "lato"
    assert get_season(8) == "lato"
    assert get_season(9) == "jesień"
    assert get_season(11) == "jesień"
    assert get_season(12) == "zima"
    assert get_season(1) == "zima"
    assert get_season(2) == "zima"

def test_extract_filename_date_ddmmyyyy():
    dt = extract_filename_date(Path("12092011.png"))
    assert dt == datetime(2011, 9, 12)

def test_extract_filename_date_yyyymmdd():
    dt = extract_filename_date(Path("photo_20200515_120000.jpg"))
    assert dt == datetime(2020, 5, 15)

def test_extract_filename_date_mmddyyyy():
    dt = extract_filename_date(Path("vacation_11252019.jpg"))
    assert dt == datetime(2019, 11, 25)

