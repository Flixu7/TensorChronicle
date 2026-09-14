"""Źródło prawdy dla ciemnego motywu UI — jedyne miejsce z kolorami/promieniami/odstępami.

Tokeny odwzorowują wartości wyciągnięte z paddle-billing.vercel.app (shadcn/ui + Tailwind,
motyw ``.dark`` — patrz artefakt "AeroEdit Tokens"). Projekt nie ma CSS/Tailwinda — to jest
natywna aplikacja Qt, więc odpowiednikiem "zmiennych w :root" są tu nazwane stałe modułu,
a odpowiednikiem "przepięcia komponentów na zmienne" jest budowanie ``DARK_STYLESHEET``
wyłącznie z tych stałych (żadnych hexów/px poza tym blokiem).

Zastosowanie: ``app.setStyleSheet(DARK_STYLESHEET)`` zaraz po utworzeniu ``QApplication``.

Miejsca, w których tokeny źródłowe nie pokrywały 1:1 widżetu Qt (interpretacja):
- COLOR_ACCENT: strona nie ma osobnego "koloru accentu" — CTA (--primary) jest tam jasnym,
  odwróconym tłem na ciemnym motywie. Nazwałem go semantycznie ACCENT, bo tak jest używany
  w tej appce (jedyny wyróżniony przycisk akcji), ale to interpretacja nazwy, nie 1:1 token.
- COLOR_FOCUS_RING (#fffa66) w źródle ma też 2px *offset* od obramowania (outline-offset) —
  QSS nie ma odpowiednika offsetu, więc fokus renderuje się jako pogrubiona 2px ramka wprost
  na krawędzi kontrolki, bez odstępu.
- Wysokość przycisków: źródło ma sztywne ``h-11`` (44px) niezależne od treści; Qt tego nie ma
  bez utraty elastyczności etykiet o różnej długości — przybliżyłem przez padding pionowy
  (SPACE_3), więc realna wysokość to ok. 40–42px, nie idealne 44px.
- Padding kart: źródłowe karty mają p-8 (32px) — w gęstych formularzach tej appki zostawiłem
  mniejszy, bo 32px zjadałoby zbyt dużo miejsca w oknie 780×720.
- Backdrop-blur, gradientowy tekst odznaki i poświaty w tle nie mają odpowiednika w QSS —
  pominięte całkowicie (nie ma tu odznak ani hero, więc i tak nie miały zastosowania).
- Font: Inter nie jest dołączony do aplikacji (offline-first) — zadeklarowany jako
  preferowany, z "Segoe UI" jako fallbackiem, gdy nie jest zainstalowany w systemie.
"""

# ---------------------------------------------------------------------------
# Kolory (odpowiednik zmiennych CSS w :root)
# ---------------------------------------------------------------------------
COLOR_BG = "#0f1515"                # --background
COLOR_TEXT = "#f4f4f5"              # --foreground
COLOR_SURFACE = "#020817"           # --card / --popover
COLOR_SURFACE_ACTIVE = "#182222"    # data-state=active (aktywna zakładka/wiersz)
COLOR_SURFACE_INPUT = "#1e293b"     # --muted / --input
COLOR_BORDER = "#272f30"            # --border
COLOR_BORDER_STRONG = "#414b4e"     # obramowanie kart / hairline
COLOR_TEXT_MUTED = "#797c7c"        # --muted-foreground
COLOR_TEXT_FAINT = "#5b6462"        # przygaszony wariant etykiet pobocznych
COLOR_SECONDARY = "#c9c9cf"         # --secondary
COLOR_SECONDARY_INK = "#0f172a"     # tekst na --secondary

COLOR_ACCENT = "#f8fafc"            # --primary (patrz uwaga o interpretacji wyżej)
COLOR_ACCENT_HOVER = "#e2e8f0"
COLOR_ACCENT_PRESSED = "#cbd5e1"
COLOR_ACCENT_INK = "#0f172a"        # --primary-foreground

COLOR_FOCUS_RING = "#fffa66"        # --ring
COLOR_DESTRUCTIVE = "#7f1d1d"       # --destructive

COLOR_DISABLED_BG = "#191a1a"
COLOR_DISABLED_TEXT = "#52605e"

# ---------------------------------------------------------------------------
# Promienie (odpowiednik --radius i pochodnych rounded-lg/md/sm/xs)
# ---------------------------------------------------------------------------
RADIUS_CARD = 16     # rounded-lg — karty / grupy
RADIUS_CONTROL = 14  # rounded-md — przyciski, pola, listy
RADIUS_SM = 12       # rounded-sm
RADIUS_TAB = 8       # rounded-xs — zakładki, drobne elementy

# ---------------------------------------------------------------------------
# Odstępy (odpowiednik skali spacing Tailwinda: jednostka bazowa 4px)
# ---------------------------------------------------------------------------
SPACE_1 = 4
SPACE_2 = 8
SPACE_3 = 12
SPACE_4 = 16
SPACE_5 = 20
SPACE_6 = 24
SPACE_8 = 32

DARK_STYLESHEET = f"""
* {{
    font-family: "Inter", "Segoe UI", sans-serif;
    font-size: 14px;
}}

QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
}}

QMainWindow, QDialog {{
    background-color: {COLOR_BG};
}}

QGroupBox {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CARD}px;
    margin-top: {SPACE_4}px;
    padding: {SPACE_5}px {SPACE_4}px {SPACE_4}px {SPACE_4}px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: {SPACE_3}px;
    padding: 0 {SPACE_2}px;
    color: {COLOR_TEXT_MUTED};
}}

QLabel {{
    background: transparent;
}}

/* Wariant "szklany" (odpowiednik secondary-button ze strony wzorcowej):
   półprzezroczyste białe tło na ciemnej karcie. Ta sama geometria co primaryButton —
   w źródle oba warianty CTA mają identyczne h-11/px-5/py-[10px], różni je tylko kolor. */
QPushButton, QPushButton#primaryButton {{
    border-radius: {RADIUS_CONTROL}px;
    padding: {SPACE_3}px {SPACE_5}px;
    font-weight: 500;
}}

QPushButton {{
    background-color: rgba(252, 252, 252, 40);
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER_STRONG};
}}

QPushButton:hover {{
    background-color: rgba(252, 252, 252, 64);
}}

QPushButton:pressed {{
    background-color: rgba(252, 252, 252, 28);
}}

QPushButton:disabled {{
    background-color: {COLOR_DISABLED_BG};
    color: {COLOR_DISABLED_TEXT};
    border: 1px solid {COLOR_BORDER};
}}

QPushButton:focus {{
    border: 2px solid {COLOR_FOCUS_RING};
}}

/* Wariant "primary" (odpowiednik CTA ze strony wzorcowej): odwrócony, jasne tło na ciemnym motywie. */
QPushButton#primaryButton {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_ACCENT_INK};
    border: none;
}}

QPushButton#primaryButton:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

QPushButton#primaryButton:pressed {{
    background-color: {COLOR_ACCENT_PRESSED};
}}

QPushButton#primaryButton:disabled {{
    background-color: {COLOR_DISABLED_BG};
    color: {COLOR_DISABLED_TEXT};
}}

QLineEdit, QComboBox, QSpinBox, QTextEdit, QListWidget {{
    background-color: {COLOR_SURFACE_INPUT};
    border: 1px solid {COLOR_BORDER_STRONG};
    border-radius: {RADIUS_CONTROL}px;
    padding: {SPACE_2}px {SPACE_3}px;
    selection-background-color: {COLOR_SECONDARY};
    selection-color: {COLOR_SECONDARY_INK};
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {{
    border: 2px solid {COLOR_FOCUS_RING};
}}

QListWidget::item {{
    padding: {SPACE_2}px {SPACE_1}px;
    border-radius: {RADIUS_TAB}px;
}}

QListWidget::item:selected {{
    background-color: {COLOR_SURFACE_ACTIVE};
    color: {COLOR_TEXT};
}}

QComboBox::drop-down {{
    border: none;
    width: {SPACE_5}px;
}}

QCheckBox {{
    spacing: {SPACE_2}px;
}}

QCheckBox::indicator {{
    width: {SPACE_4}px;
    height: {SPACE_4}px;
    border-radius: 4px;
    border: 1px solid {COLOR_BORDER_STRONG};
    background-color: {COLOR_SURFACE_INPUT};
}}

QCheckBox::indicator:checked {{
    background-color: {COLOR_ACCENT};
    border: 1px solid {COLOR_ACCENT};
}}

QProgressBar {{
    background-color: {COLOR_SURFACE_INPUT};
    border: 1px solid {COLOR_BORDER_STRONG};
    border-radius: {RADIUS_CONTROL}px;
    text-align: center;
    color: {COLOR_TEXT};
    padding: 1px;
}}

QProgressBar::chunk {{
    background-color: {COLOR_ACCENT};
    border-radius: {RADIUS_SM}px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: {SPACE_2}px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLOR_BORDER_STRONG};
    border-radius: 5px;
    min-height: {SPACE_6}px;
}}

QScrollBar::handle:vertical:hover {{
    background: #545f60;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: {SPACE_2}px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {COLOR_BORDER_STRONG};
    border-radius: 5px;
    min-width: {SPACE_6}px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QMenu {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_TAB}px;
}}

QMenu::item {{
    padding: {SPACE_2}px {SPACE_5}px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLOR_SURFACE_ACTIVE};
}}

QMessageBox {{
    background-color: {COLOR_SURFACE};
}}

QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CARD}px;
    background-color: {COLOR_SURFACE};
    top: -1px;
}}

QTabBar {{
    background: {COLOR_BG};
}}

QTabBar::tab {{
    background: transparent;
    color: {COLOR_TEXT_MUTED};
    padding: {SPACE_2}px {SPACE_5}px;
    margin-right: {SPACE_1}px;
    border-top-left-radius: {RADIUS_TAB}px;
    border-top-right-radius: {RADIUS_TAB}px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: {COLOR_SURFACE_ACTIVE};
    color: {COLOR_TEXT};
}}

QTabBar::tab:!selected:hover {{
    color: {COLOR_TEXT};
}}
"""
