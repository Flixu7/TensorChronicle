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
- The "Pokaż na Mapie" button reads GPS EXIF data from photos in the selected input directories and displays them as markers with thumbnails on an interactive OpenStreetMap/Leaflet map (requires an internet connection to load map tiles).
- A separate Geotagging tool lets the user pick a directory or individual JPEG photos, type or search a place name (geocoded via OpenStreetMap Nominatim) or enter coordinates directly, and writes the GPS EXIF data losslessly into the selected files without re-encoding the image.
- The map preview and the geotagging tool exchange context while staying two separate windows: clicking a photo without GPS data on the map and then clicking a spot on the map opens the geotagger pre-filled with that photo and the chosen coordinates; conversely, the geotagger has a "Wybierz na mapie" button that opens the same map component in picker mode so a location can be chosen by clicking instead of typing.

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

To launch the standalone geotagging tool (add GPS location to photos):

```bash
python -m photo_organizer.geotag_gui
```

---

Command Line Interface (CLI)

To run the application via module execution, the user enters

```bash
python -m photo_organizer.cli -i /path/to/photos
```