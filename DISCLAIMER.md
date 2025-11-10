# Haftungsausschluss / Legal Disclaimer

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
