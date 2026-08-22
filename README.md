# TensorChronicle

A modern, fast, multi-threaded photo organizer with EXIF date extraction, duplicate detection, and a PySide6 GUI.

## 🚀 Features

- **Automatic Organization**: Sorts photos into directories structured by Year and Season (Wiosna, Lato, Jesień, Zima).
- **EXIF & Date Extraction**: Reads original capture dates from EXIF metadata, fallback to filename pattern matching, and file modification timestamps.
- **SHA-256 Duplicate Detection**: Prevents duplicate photos across different folders and file names using SHA-256 content hashing.
- **Name Collision Strategies**:
  - `unique` (default): Automatically appends counter suffixes (`photo_1.jpg`, `photo_2.jpg`).
  - `skip`: Skips processing if a file with the same name exists in the target folder.
  - `overwrite`: Replaces existing file in the target directory.
- **Multi-threaded Execution**: Fast parallel processing using a worker pool.
- **Dry-Run Mode**: Preview organizing results and generated reports without modifying filesystem.
- **PySide6 Graphical Interface**: User-friendly GUI alongside a full-featured CLI interface.

---

## 🛠️ Installation

```bash
git clone https://github.com/Flixu7/TensorChronicle.git
cd TensorChronicle
pip install -r requirements.txt
```

---

## 🖥️ Usage

### Graphical Interface (GUI)

Launch the PySide6 application:

```bash
python -m photo_organizer.gui
```

---

### Command Line Interface (CLI)

Run via module execution:

```bash
python -m photo_organizer.cli -i /path/to/photos -o /path/to/organized
```

#### CLI Options

| Argument | Short | Default | Description |
|---|---|---|---|
| `--input` | `-i` | Required | Space-separated list of input directories |
| `--output` | `-o` | Required | Target output directory |
| `--mode` | `-m` | `copy` | Operation mode: `copy` or `move` |
| `--dry-run` | | `False` | Run simulation without file modifications |
| `--no-duplicates-check` | | `False` | Disable SHA-256 duplicate detection |
| `--collision` | | `unique` | Strategy for filename conflicts (`unique`, `skip`, `overwrite`) |
| `--workers` | `-w` | `4` | Number of worker threads |

Example:

```bash
python -m photo_organizer.cli -i ./Unsorted1 ./Unsorted2 -o ./SortedPhotos -m copy --collision unique -w 8
```

---

## 📁 Directory & Project Structure

```
TensorChronicle/
├── photo_organizer/
│   ├── __init__.py
│   ├── cli.py               # CLI entry point
│   ├── date_extractor.py    # EXIF & filename date parsing
│   ├── duplicate_detector.py # SHA-256 hash duplication checking
│   ├── gui.py               # PySide6 desktop GUI
│   ├── organizer.py         # Main multi-threaded sorting engine
│   └── season.py            # Seasonal mapping logic
├── TensorChronicle/
│   └── ui_constellation.py  # Constellation-inspired UI component
├── tests/
│   ├── test_date_extractor.py
│   ├── test_gui.py
│   └── test_organizer.py
├── requirements.txt
└── README.md
```

---

## ⚙️ How Duplicate Detection & Collision Handling Works

1. **Content Duplicates (`check_duplicates=True`)**
   - Calculates SHA-256 digest for each file.
   - If identical content was already processed, the duplicate is skipped and recorded in the report.

2. **Name Collisions (`collision_strategy`)**
   - When different files share the same filename in the same target folder:
     - `unique`: Generates unique names (`12092011_1.png`, `12092011_2.png`).
     - `skip`: Skips duplicate name file and records entry in final report.
     - `overwrite`: Overwrites target file.

---

## 🧪 Running Automated Tests

Run the test suite using `pytest`:

```bash
python -m pytest
```
