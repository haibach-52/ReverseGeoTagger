#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReverseGeoTagger - Automatische Reverse-Geocodierung für Bilder
Haupteinstieg der Anwendung
"""

import sys
import traceback

try:
    from PyQt6.QtWidgets import QApplication
    from mainwindow import MainWindow
except ImportError as e:
    print(f"FEHLER beim Importieren: {e}")
    print("Bitte installieren Sie die Abhängigkeiten mit: pip install -r requirements.txt")
    input("Drücken Sie Enter zum Beenden...")
    sys.exit(1)


def main():
    """Hauptfunktion"""
    try:
        print("Starte ReverseGeoTagger...")
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        print("Erstelle Hauptfenster...")
        window = MainWindow()
        window.show()
        
        print("Anwendung läuft.")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"\n!!! KRITISCHER FEHLER !!!")
        print(f"Fehler: {e}")
        print(f"\nTraceback:")
        traceback.print_exc()
        input("\nDrücken Sie Enter zum Beenden...")
        sys.exit(1)


if __name__ == '__main__':
    main()