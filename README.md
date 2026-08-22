# TensorChronicle

The application is a multi threaded photo organizer that operates at high speeds and uses a PySide6 GUI to manage EXIF date extraction and duplicate detection.

Features

- The software sorts image files into directories that it structures by Year & Season, specifically Wiosna, Lato, Jesień & Zima.
- It reads the original capture dates from EXIF metadata but it uses filename pattern matching or file modification timestamps if that data is missing.
- There is a SHA-256 content hashing mechanism that prevents the presence of duplicate images across different folders and file names.
- Strategies for name collisions are
- The `unique` setting is the default and it appends counter suffixes like `photo_1.jpg` or `photo_2.jpg`.
- The `skip` setting stops the process if a file with the same name already exists in the target folder.
- The `overwrite` setting replaces the file that exists in the target directory.
- Fast parallel processing is possible because the application uses a multi threaded worker pool.
- In Dry Run Mode, the user previews the results and generated reports without the software modifying the filesystem.
- The PySide6 Graphical Interface is available for users alongside a full featured CLI interface.

---

Installation

```bash
git clone https://github.com/Flixu7/TensorChronicle.git
cd TensorChronicle
pip install -r requirements.txt
```

---

Usage

Graphical Interface (GUI)

By running this command, the user launches the PySide6 application

```bash
python -m photo_organizer.gui
```

---

Command Line Interface (CLI)

To run the application via module execution, the user enters

```bash
python -m photo_organizer.cli -i /path/to/photos
```