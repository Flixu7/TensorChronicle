import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from PIL import Image, ExifTags

def extract_exif_date(path: Path) -> Optional[datetime]:
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return None
            
            exif_data = {}
            for tag_id, val in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                exif_data[tag_name] = val
            
            for key in ["DateTimeOriginal", "CreateDate", "DateTime"]:
                if key in exif_data and isinstance(exif_data[key], str):
                    val_str = exif_data[key].strip()
                    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y:%m:%d", "%Y-%m-%d"):
                        try:
                            return datetime.strptime(val_str, fmt)
                        except ValueError:
                            pass
    except Exception:
        pass
    return None

def extract_filename_date(path: Path) -> Optional[datetime]:
    name = path.stem
    
    match_ddmmyyyy = re.search(r'(?<!\d)(\d{2})(\d{2})(\d{4})(?!\d)', name)
    if match_ddmmyyyy:
        d_str, m_str, y_str = match_ddmmyyyy.groups()
        day, month, year = int(d_str), int(m_str), int(y_str)
        if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
            try:
                return datetime(year, month, day)
            except ValueError:
                pass

    match_yyyymmdd = re.search(r'(?<!\d)(\d{4})[-_]?(\d{2})[-_]?(\d{2})(?!\d)', name)
    if match_yyyymmdd:
        y_str, m_str, d_str = match_yyyymmdd.groups()
        year, month, day = int(y_str), int(m_str), int(d_str)
        if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
            try:
                return datetime(year, month, day)
            except ValueError:
                pass

    match_mmddyyyy = re.search(r'(?<!\d)(\d{2})[-_]?(\d{2})[-_]?(\d{4})(?!\d)', name)
    if match_mmddyyyy:
        m_str, d_str, y_str = match_mmddyyyy.groups()
        month, day, year = int(m_str), int(d_str), int(y_str)
        if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
            try:
                return datetime(year, month, day)
            except ValueError:
                pass

    return None

def extract_fs_date(path: Path) -> Optional[datetime]:
    try:
        stat = path.stat()
        mtime = stat.st_mtime
        if mtime > 0:
            return datetime.fromtimestamp(mtime)
    except Exception:
        pass
    return None

def extract_date(path: Path) -> tuple[Optional[datetime], str]:
    exif_dt = extract_exif_date(path)
    if exif_dt:
        return exif_dt, "exif"
    
    fn_dt = extract_filename_date(path)
    if fn_dt:
        return fn_dt, "filename"
    
    fs_dt = extract_fs_date(path)
    if fs_dt:
        return fs_dt, "filesystem"
    
    return None, "unknown"
