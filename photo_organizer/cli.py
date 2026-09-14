import argparse
import sys
from pathlib import Path
from .organizer import organize_photos, OrganizerOptions

def main():
    parser = argparse.ArgumentParser(description="Organizator zdjęć wg roku i pory roku.")
    parser.add_argument("-i", "--input", nargs="+", required=True, type=Path, help="Katalogi wejściowe ze zdjęciami.")
    parser.add_argument("-o", "--output", required=True, type=Path, help="Katalog wyjściowy.")
    parser.add_argument("-m", "--mode", choices=["copy", "move"], default="copy", help="Tryb operacji: copy (domyślnie) lub move.")
    parser.add_argument("--dry-run", action="store_true", help="Tryb symulacji bez wprowadzania zmian.")
    parser.add_argument("--no-duplicates-check", action="store_true", help="Wyłącz sprawdzanie duplikatów po hashu SHA-256.")
    parser.add_argument("--collision", choices=["unique", "overwrite", "skip"], default="unique", help="Strategia przy konflikcie nazw plików.")
    parser.add_argument("-w", "--workers", type=int, default=4, help="Liczba wątków do przetwarzania równoległego.")
    
    args = parser.parse_args()

    options = OrganizerOptions(
        input_dirs=args.input,
        output_dir=args.output,
        mode=args.mode,
        dry_run=args.dry_run,
        check_duplicates=not args.no_duplicates_check,
        collision_strategy=args.collision,
        num_workers=args.workers
    )

    report = organize_photos(options)

    print("=== RAPORT PRZETWARZANIA ZDJĘĆ ===")
    print(f"Znalezione pliki: {report.total_found}")
    print(f"Przetworzone pliki: {report.processed_count}")
    print("\nLiczba plików według roku i pory roku:")
    for year, seasons in sorted(report.counts_by_year_season.items()):
        for season, count in sorted(seasons.items()):
            season_label = f" -> {season}" if season else ""
            print(f"  - {year}{season_label}: {count}")

    if report.skipped_files:
        print("\nPominięte pliki:")
        for filepath, reason in report.skipped_files.items():
            print(f"  - {filepath}: {reason}")

    if report.errors:
        print("\nBłędy:")
        for filepath, err in report.errors.items():
            print(f"  - {filepath}: {err}")

if __name__ == "__main__":
    main()
