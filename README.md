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
```

## Haftungsausschluss / Legal Disclaimer

---

## Deutsche Version

### Nutzung auf eigene Gefahr

ReverseGeoTagger wird "wie besehen" (AS IS) ohne jegliche Gewährleistung zur Verfügung gestellt. Die Nutzung erfolgt vollständig auf eigene Gefahr.

### Keine Haftung

Der Autor übernimmt keinerlei Haftung für:

- **Datenverlust oder -beschädigung** - Obwohl die Software darauf ausgelegt ist, nur Ortsdaten zu ändern, können technische Fehler nicht ausgeschlossen werden
- **Fehlerhafte Ortsdaten** - Die Genauigkeit der Geocodierung hängt von der Qualität der OpenStreetMap-Daten und der Photon API ab
- **Metadaten-Überschreibung** - Es wird dringend empfohlen, vor der Nutzung Backups anzulegen
- **API-Verfügbarkeit** - Die Photon API ist ein kostenloser Drittanbieter-Service, dessen Verfügbarkeit nicht garantiert werden kann
- **Urheberrechtsverletzungen** - Nutzer sind selbst verantwortlich für die rechtmäßige Verwendung ihrer Bilder
- **Folgeschäden** jeglicher Art

### Empfehlungen

**WICHTIG: Erstellen Sie IMMER ein Backup Ihrer Bilder, bevor Sie ReverseGeoTagger verwenden!**

1. **Backup erstellen** - Kopieren Sie alle Bilder vor der Verarbeitung
2. **Testlauf** - Testen Sie die Software zunächst mit wenigen Testbildern
3. **Überprüfung** - Kontrollieren Sie die geschriebenen Metadaten stichprobenartig
4. **XMP Sidecars** - Bei RAW-Dateien werden XMP-Sidecars empfohlen (nicht-destruktiv)

### ExifTool

Diese Software nutzt ExifTool von Phil Harvey. ExifTool ist ein eigenständiges Programm mit eigenen Lizenzbedingungen. Siehe: https://exiftool.org/

### Photon API

Diese Software nutzt die Photon API von Komoot, die auf OpenStreetMap-Daten basiert:
- **Fair Use** - Beachten Sie die Fair Use Policy der Photon API
- **Keine Garantie** - Die Verfügbarkeit und Genauigkeit der API wird nicht garantiert
- **Rate Limiting** - Bei exzessiver Nutzung kann der Zugang eingeschränkt werden

### Datenschutz

- **Lokale Verarbeitung** - Alle Bildverarbeitungen erfolgen lokal auf Ihrem Computer
- **API-Aufrufe** - GPS-Koordinaten werden zur Geocodierung an die Photon API übermittelt
- **Cache** - Geocoding-Ergebnisse werden lokal in `~/.geotagger/` gespeichert
- **Keine Tracking** - Die Software sammelt keine Nutzungsdaten oder Telemetrie

### Open Source

Diese Software ist Open Source unter der MIT-Lizenz. Der vollständige Lizenztext ist in der Datei [LICENSE](LICENSE) enthalten.

### Gewährleistungsausschluss gemäß MIT-Lizenz
