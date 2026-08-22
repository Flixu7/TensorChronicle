# TensorChronicle

1. Duplikaty zawartości (taka sama treść pliku)
Gdy opcja Sprawdzaj Duplikaty (check_duplicates=True) jest włączona:

Dla każdego pliku obliczany jest unikalny hash SHA-256 w pliku `duplicate_detector.py`.
Jeśli ten sam hash zostanie wykryty ponownie (nawet przy innej nazwie lub w innym folderze źródłowym), plik jest pomijany.
Informacja o pominiętym duplikacie trafia do raportu końcowego.

2. Kolizje nazw (różna treść, taka sama nazwa pliku)
Gdy pliki różnią się zawartością, ale trafiają do tego samego podfolderu docelowego z tą samą nazwą, decyduje opcja Kolizje (collision_strategy):

unique (domyślnie): Automatycznie dodaje licznik do nazwy (np. 12092011.png → 12092011_1.png, 12092011_2.png).
skip: Pomija plik o powtarzającej się nazwie i odnotowuje to w raporcie.
overwrite: Nadpisuje plik w katalogu docelowym.
