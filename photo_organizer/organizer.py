import os
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set, Optional

from .date_extractor import extract_date
from .duplicate_detector import compute_file_hash
from .season import get_season

SUPPORTED_EXTENSIONS: Set[str] = {
    ".jpg", ".jpeg", ".png", ".heic", ".heif", ".tiff", ".tif", ".bmp", ".webp", ".raw", ".cr2", ".nef",
    ".mp4", ".mov", ".avi", ".mkv", ".m4v", ".wmv", ".flv", ".mts", ".m2ts", ".3gp"
}

@dataclass
class OrganizerOptions:
    input_dirs: List[Path]
    output_dir: Path
    mode: str = "copy"
    dry_run: bool = False
    check_duplicates: bool = True
    collision_strategy: str = "unique"
    num_workers: int = 4

@dataclass
class OrganizeReport:
    total_found: int = 0
    processed_count: int = 0
    counts_by_year_season: Dict[str, Dict[str, int]] = field(default_factory=dict)
    skipped_files: Dict[str, str] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)

def _get_unique_target_path(target_path: Path, existing_paths: Set[Path]) -> Path:
    if target_path not in existing_paths and not target_path.exists():
        return target_path
    
    stem = target_path.stem
    suffix = target_path.suffix
    parent = target_path.parent
    counter = 1
    
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if candidate not in existing_paths and not candidate.exists():
            return candidate
        counter += 1

def _collect_photo_files(input_dirs: List[Path]) -> List[Path]:
    files = []
    for idir in input_dirs:
        idir = Path(idir)
        if not idir.exists():
            continue
        if idir.is_file():
            if idir.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(idir)
            continue
        for p in idir.rglob("*"):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(p)
    return files

def organize_photos(options: OrganizerOptions) -> OrganizeReport:
    report = OrganizeReport()
    files = _collect_photo_files(options.input_dirs)
    report.total_found = len(files)

    seen_hashes: Set[str] = set()
    used_target_paths: Set[Path] = set()
    lock = threading.Lock()

    def process_single_file(src_path: Path):
        nonlocal seen_hashes, used_target_paths
        
        if options.check_duplicates:
            try:
                fhash = compute_file_hash(src_path)
                with lock:
                    if fhash in seen_hashes:
                        report.skipped_files[str(src_path)] = "Duplikat (taki sam hash SHA-256)"
                        return
                    seen_hashes.add(fhash)
            except Exception as e:
                with lock:
                    report.errors[str(src_path)] = f"Błąd obliczania hasha: {e}"
                return

        dt, source = extract_date(src_path)
        
        if dt is None:
            rel_dir = Path("nieznana-data")
            year_str = "nieznana-data"
            season_str = ""
        else:
            year_str = str(dt.year)
            season_str = get_season(dt.month)
            rel_dir = Path(year_str) / season_str

        dest_dir = options.output_dir / "organized_photos" / rel_dir
        dest_file_path = dest_dir / src_path.name

        with lock:
            if dest_file_path.exists() or dest_file_path in used_target_paths:
                if options.collision_strategy == "skip":
                    report.skipped_files[str(src_path)] = f"Plik o nazwie {src_path.name} już istnieje w miejscu docelowym"
                    return
                elif options.collision_strategy == "unique":
                    dest_file_path = _get_unique_target_path(dest_file_path, used_target_paths)
                elif options.collision_strategy == "overwrite":
                    pass
            
            used_target_paths.add(dest_file_path)

        if not options.dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            try:
                if options.mode == "move":
                    shutil.move(str(src_path), str(dest_file_path))
                else:
                    shutil.copy2(str(src_path), str(dest_file_path))
            except Exception as e:
                with lock:
                    report.errors[str(src_path)] = f"Błąd zapisu pliku: {e}"
                return

        with lock:
            report.processed_count += 1
            if year_str not in report.counts_by_year_season:
                report.counts_by_year_season[year_str] = {}
            if season_str not in report.counts_by_year_season[year_str]:
                report.counts_by_year_season[year_str][season_str] = 0
            report.counts_by_year_season[year_str][season_str] += 1

    with ThreadPoolExecutor(max_workers=options.num_workers) as executor:
        futures = [executor.submit(process_single_file, f) for f in files]
        for future in as_completed(futures):
            future.result()

    return report
