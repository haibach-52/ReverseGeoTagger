# ReverseGeoTagger

<div align="center">

![Version](https://img.shields.io/badge/version-0.5.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

**Automatische Reverse-Geocodierung für Bilder mit GPS-Daten**

*Automatic reverse geocoding for images with GPS data*

[Features](#-features) • [Installation](#-installation) • [Verwendung](#-verwendung) • [Screenshots](#-beispiel-ausgabe) • [Lizenz](#-lizenz)

</div>

---

## 📖 Über das Projekt

ReverseGeoTagger ist eine Python-Anwendung mit grafischer Benutzeroberfläche, die automatisch GPS-Koordinaten aus Bildern ausliest und diese durch detaillierte Ortsinformationen (Land, Stadt, Straße, PLZ, etc.) ergänzt.

### Warum ReverseGeoTagger?

- 🎯 **Einfach zu bedienen** - Intuitive GUI, kein Terminal nötig
- ⚡ **Schnell** - Intelligenter Cache reduziert API-Aufrufe drastisch
- 🔒 **Sicher** - Ändert nur Ortsdaten, alle anderen Metadaten bleiben unberührt
- 🌍 **Kostenlos** - Nutzt die freie Photon API (OpenStreetMap)
- 📝 **XMP-Support** - Unterstützt XMP Sidecar-Dateien

## ✨ Features

### Ortsdaten-Extraktion
- **Land** & Ländercode (DE, AT, CH, etc.)
- **Bundesland** / Region
- **Bezirk** / Landkreis
- **Stadt**
- **Stadtteil** / Vorort
- **Straße** & Hausnummer
- **Postleitzahl**

### Intelligenter Cache
- 💾 Lokale Speicherung aller Geocoding-Ergebnisse
- ⚙️ Konfigurierbare Genauigkeit (3-7 Dezimalstellen)
- ⏰ Einstellbare Cache-Lebensdauer (1-365 Tage)
- 📊 Cache-Statistiken und Verwaltung

### Optimierungen
- ⚡ Bereits getaggte Bilder überspringen
- 🔄 Nur geänderte Daten schreiben
- 📝 XMP Sidecar-Unterstützung (automatische Erkennung)
- 🚀 Batch-Verarbeitung ganzer Ordner (rekursiv)

### Unterstützte Formate
- **JPEG** (.jpg, .jpeg)
- **PNG** (.png)
- **TIFF** (.tiff, .tif)
- **RAW-Formate** (.dng, .raw, .cr2, .nef, .arw, .orf, .rw2, .pef, .srw, .raf)

## 🚀 Installation

### Voraussetzungen

- **Python 3.8 oder höher**
- **ExifTool** (muss separat installiert werden)

#### ExifTool installieren

**Windows:**
1. Download von https://exiftool.org/
2. `exiftool(-k).exe` in `exiftool.exe` umbenennen
3. In einen Ordner im PATH verschieben (z.B. `C:\Windows\`)

**Linux:**
```bash
sudo apt install exiftool
