#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Geo-Tagger - Automatische Reverse-Geocodierung für Bilder
"""

import sys
import os
import json
import subprocess
import requests
import traceback
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from datetime import datetime, timedelta
import hashlib

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit,
        QProgressBar, QDialog, QFormLayout, QCheckBox, QScrollArea,
        QGroupBox, QMessageBox, QComboBox, QSpinBox
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
    from PyQt6.QtGui import QFont
except ImportError as e:
    print(f"FEHLER beim Importieren von PyQt6: {e}")
    print("Bitte installieren Sie PyQt6 mit: pip install PyQt6")
    input("Drücken Sie Enter zum Beenden...")
    sys.exit(1)


class GeocodingCache:
    """Cache für Geocodierung-Ergebnisse"""
    
    # Genauigkeits-Level mit Beschreibung
    PRECISION_LEVELS = {
        3: {'name': '3 Dezimalstellen', 'accuracy': '~111m', 'description': 'Stadtteile/große Bereiche'},
        4: {'name': '4 Dezimalstellen', 'accuracy': '~11m', 'description': 'Straßenabschnitte'},
        5: {'name': '5 Dezimalstellen', 'accuracy': '~1m', 'description': 'Gebäude (Standard)'},
        6: {'name': '6 Dezimalstellen', 'accuracy': '~0.1m', 'description': 'Exakte Position'},
        7: {'name': '7 Dezimalstellen', 'accuracy': '~0.01m', 'description': 'Maximale Genauigkeit'},
    }
    
    def __init__(self, cache_file: Path = None, precision: int = 5, max_age_days: int = 30):
        if cache_file is None:
            cache_dir = Path.home() / '.geotagger'
            cache_dir.mkdir(exist_ok=True)
            self.cache_file = cache_dir / 'geocoding_cache.json'
        else:
            self.cache_file = cache_file
        
        self.cache_data = {}
        self.cache_max_age_days = max_age_days
        self.precision = precision
        self.load_cache()
    
    def set_precision(self, precision: int):
        if precision in self.PRECISION_LEVELS:
            self.precision = precision
    
    def set_max_age_days(self, days: int):
        if days > 0:
            self.cache_max_age_days = days
    
    def get_precision_info(self) -> Dict[str, str]:
        return self.PRECISION_LEVELS.get(self.precision, self.PRECISION_LEVELS[5])
    
    def _generate_cache_key(self, lat: float, lon: float) -> str:
        lat_rounded = round(lat, self.precision)
        lon_rounded = round(lon, self.precision)
        key = f"{lat_rounded},{lon_rounded}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warnung: Cache konnte nicht geladen werden: {e}")
                self.cache_data = {}
    
    def save_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Warnung: Cache konnte nicht gespeichert werden: {e}")
    
    def get(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        cache_key = self._generate_cache_key(lat, lon)
        
        if cache_key not in self.cache_data:
            return None
        
        cache_entry = self.cache_data[cache_key]
        timestamp_str = cache_entry.get('timestamp')
        if not timestamp_str:
            return None
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            age = datetime.now() - timestamp
            
            if age > timedelta(days=self.cache_max_age_days):
                return None
            
            return cache_entry.get('location_data')
        except (ValueError, TypeError):
            return None
    
    def set(self, lat: float, lon: float, location_data: Dict[str, str]):
        cache_key = self._generate_cache_key(lat, lon)
        
        self.cache_data[cache_key] = {
            'timestamp': datetime.now().isoformat(),
            'coordinates': {
                'lat': round(lat, self.precision),
                'lon': round(lon, self.precision)
            },
            'precision': self.precision,
            'location_data': location_data
        }
        
        self.save_cache()
    
    def clear_old_entries(self, max_age_days: int = None):
        if max_age_days is None:
            max_age_days = self.cache_max_age_days
        
        now = datetime.now()
        keys_to_delete = []
        
        for key, entry in self.cache_data.items():
            timestamp_str = entry.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    age = now - timestamp
                    
                    if age > timedelta(days=max_age_days):
                        keys_to_delete.append(key)
                except (ValueError, TypeError):
                    keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.cache_data[key]
        
        if keys_to_delete:
            self.save_cache()
        
        return len(keys_to_delete)
    
    def get_stats(self) -> Dict[str, any]:
        total_entries = len(self.cache_data)
        
        now = datetime.now()
        valid_entries = 0
        expired_entries = 0
        
        for entry in self.cache_data.values():
            timestamp_str = entry.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    age = now - timestamp
                    
                    if age <= timedelta(days=self.cache_max_age_days):
                        valid_entries += 1
                    else:
                        expired_entries += 1
                except (ValueError, TypeError):
                    expired_entries += 1
        
        precision_info = self.get_precision_info()
        
        return {
            'total': total_entries,
            'valid': valid_entries,
            'expired': expired_entries,
            'cache_file': str(self.cache_file),
            'max_age_days': self.cache_max_age_days,
            'precision': self.precision,
            'precision_name': precision_info['name'],
            'precision_accuracy': precision_info['accuracy']
        }


class Config:
    """Konfigurationsverwaltung"""
    
    def __init__(self):
        self.settings = QSettings('GeoTagger', 'GeoTagger')
        self.default_exiftool_path = 'exiftool'
        self.default_file_types = [
            '.jpg', '.jpeg', '.png', '.tiff', '.tif',
            '.dng', '.raw', '.cr2', '.nef', '.arw', '.orf'
        ]
        self.default_cache_precision = 5
        self.default_cache_max_age_days = 30
    
    def get_exiftool_path(self) -> str:
        return self.settings.value('exiftool_path', self.default_exiftool_path)
    
    def set_exiftool_path(self, path: str):
        self.settings.setValue('exiftool_path', path)
    
    def get_file_types(self) -> List[str]:
        types = self.settings.value('file_types', self.default_file_types)
        if isinstance(types, str):
            types = json.loads(types)
        return types
    
    def set_file_types(self, types: List[str]):
        self.settings.setValue('file_types', json.dumps(types))
    
    def get_last_directory(self) -> str:
        return self.settings.value('last_directory', str(Path.home()))
    
    def set_last_directory(self, directory: str):
        self.settings.setValue('last_directory', directory)
    
    def get_cache_precision(self) -> int:
        return int(self.settings.value('cache_precision', self.default_cache_precision))
    
    def set_cache_precision(self, precision: int):
        self.settings.setValue('cache_precision', precision)
    
    def get_cache_max_age_days(self) -> int:
        return int(self.settings.value('cache_max_age_days', self.default_cache_max_age_days))
    
    def set_cache_max_age_days(self, days: int):
        self.settings.setValue('cache_max_age_days', days)
    
    def get_skip_if_exists(self) -> bool:
        return self.settings.value('skip_if_exists', True, type=bool)
    
    def set_skip_if_exists(self, skip: bool):
        self.settings.setValue('skip_if_exists', skip)


class ConfigDialog(QDialog):
    """Konfigurationsdialog"""
    
    def __init__(self, config: Config, cache: GeocodingCache, parent=None):
        super().__init__(parent)
        self.config = config
        self.cache = cache
        self.setWindowTitle('Einstellungen')
        self.setModal(True)
        self.resize(650, 650)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # ExifTool-Pfad
        exiftool_group = QGroupBox('ExifTool Konfiguration')
        exiftool_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel('ExifTool Pfad:'))
        self.exiftool_path_input = QLineEdit(self.config.get_exiftool_path())
        path_layout.addWidget(self.exiftool_path_input)
        
        browse_btn = QPushButton('Durchsuchen...')
        browse_btn.clicked.connect(self.browse_exiftool)
        path_layout.addWidget(browse_btn)
        
        exiftool_layout.addLayout(path_layout)
        
        hint_label = QLabel('Leer lassen für Standardpfad (exiftool im PATH)')
        hint_label.setStyleSheet('color: gray; font-size: 10px;')
        exiftool_layout.addWidget(hint_label)
        
        exiftool_group.setLayout(exiftool_layout)
        layout.addWidget(exiftool_group)
        
        # Cache-Konfiguration
        cache_config_group = QGroupBox('Cache-Konfiguration')
        cache_config_layout = QVBoxLayout()
        
        # Genauigkeits-Auswahl
        precision_layout = QHBoxLayout()
        precision_layout.addWidget(QLabel('Genauigkeit:'))
        
        self.precision_combo = QComboBox()
        current_precision = self.config.get_cache_precision()
        
        for precision, info in sorted(GeocodingCache.PRECISION_LEVELS.items()):
            display_text = f"{info['name']} ({info['accuracy']}) - {info['description']}"
            self.precision_combo.addItem(display_text, precision)
            
            if precision == current_precision:
                self.precision_combo.setCurrentIndex(self.precision_combo.count() - 1)
        
        precision_layout.addWidget(self.precision_combo)
        cache_config_layout.addLayout(precision_layout)
        
        precision_hint = QLabel(
            '<b>Hinweis:</b> Eine niedrigere Genauigkeit führt zu mehr Cache-Treffern.'
        )
        precision_hint.setWordWrap(True)
        precision_hint.setStyleSheet('color: gray; font-size: 10px; padding: 5px;')
        cache_config_layout.addWidget(precision_hint)
        
        # Cache-Lebensdauer
        max_age_layout = QHBoxLayout()
        max_age_layout.addWidget(QLabel('Cache-Lebensdauer:'))
        
        self.max_age_spinbox = QSpinBox()
        self.max_age_spinbox.setMinimum(1)
        self.max_age_spinbox.setMaximum(365)
        self.max_age_spinbox.setSuffix(' Tage')
        self.max_age_spinbox.setValue(self.config.get_cache_max_age_days())
        max_age_layout.addWidget(self.max_age_spinbox)
        max_age_layout.addStretch()
        
        cache_config_layout.addLayout(max_age_layout)
        
        max_age_hint = QLabel(
            '<b>Empfehlung:</b> 30 Tage für normale Nutzung.'
        )
        max_age_hint.setWordWrap(True)
        max_age_hint.setStyleSheet('color: gray; font-size: 10px; padding: 5px;')
        cache_config_layout.addWidget(max_age_hint)
        
        cache_config_group.setLayout(cache_config_layout)
        layout.addWidget(cache_config_group)
        
        # Cache-Informationen
        cache_group = QGroupBox('Cache-Informationen')
        cache_layout = QVBoxLayout()
        
        cache_stats = self.cache.get_stats()
        
        stats_text = f"""<b>Cache-Datei:</b> {cache_stats['cache_file']}<br>
<b>Aktuelle Genauigkeit:</b> {cache_stats['precision_name']} ({cache_stats['precision_accuracy']})<br>
<b>Aktuelle Lebensdauer:</b> {cache_stats['max_age_days']} Tage<br>
<b>Gesamt-Einträge:</b> {cache_stats['total']}<br>
<b>Gültige Einträge:</b> {cache_stats['valid']}<br>
<b>Abgelaufene Einträge:</b> {cache_stats['expired']}"""
        
        self.stats_label = QLabel(stats_text)
        self.stats_label.setWordWrap(True)
        cache_layout.addWidget(self.stats_label)
        
        cache_button_layout = QHBoxLayout()
        
        clear_old_btn = QPushButton('Alte Einträge löschen')
        clear_old_btn.clicked.connect(self.clear_old_cache_entries)
        cache_button_layout.addWidget(clear_old_btn)
        
        clear_all_btn = QPushButton('Cache komplett leeren')
        clear_all_btn.clicked.connect(self.clear_all_cache)
        clear_all_btn.setStyleSheet('background-color: #d73a49; color: white;')
        cache_button_layout.addWidget(clear_all_btn)
        
        cache_layout.addLayout(cache_button_layout)
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        # Dateitypen
        filetype_group = QGroupBox('Unterstützte Dateitypen')
        filetype_layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(120)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        self.filetype_checkboxes = {}
        all_types = [
            '.jpg', '.jpeg', '.png', '.tiff', '.tif',
            '.dng', '.raw', '.cr2', '.nef', '.arw',
            '.orf', '.rw2', '.pef', '.srw', '.raf'
        ]
        
        selected_types = self.config.get_file_types()
        
        for ftype in all_types:
            # FIX: .upper() statt .UPPER()
            cb = QCheckBox(ftype.upper())
            cb.setChecked(ftype in selected_types)
            self.filetype_checkboxes[ftype] = cb
            scroll_layout.addWidget(cb)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        filetype_layout.addWidget(scroll)
        
        filetype_group.setLayout(filetype_layout)
        layout.addWidget(filetype_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton('Speichern')
        save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton('Abbrechen')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def browse_exiftool(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, 'ExifTool auswählen', '',
            'Ausführbare Dateien (*.exe);;Alle Dateien (*)'
        )
        if filename:
            self.exiftool_path_input.setText(filename)
    
    def update_stats_display(self):
        cache_stats = self.cache.get_stats()
        
        stats_text = f"""<b>Cache-Datei:</b> {cache_stats['cache_file']}<br>
<b>Aktuelle Genauigkeit:</b> {cache_stats['precision_name']} ({cache_stats['precision_accuracy']})<br>
<b>Aktuelle Lebensdauer:</b> {cache_stats['max_age_days']} Tage<br>
<b>Gesamt-Einträge:</b> {cache_stats['total']}<br>
<b>Gültige Einträge:</b> {cache_stats['valid']}<br>
<b>Abgelaufene Einträge:</b> {cache_stats['expired']}"""
        
        self.stats_label.setText(stats_text)
    
    def clear_old_cache_entries(self):
        deleted = self.cache.clear_old_entries()
        QMessageBox.information(
            self, 'Cache bereinigt',
            f'{deleted} alte Einträge wurden gelöscht.'
        )
        self.update_stats_display()
    
    def clear_all_cache(self):
        reply = QMessageBox.question(
            self, 'Cache leeren',
            'Möchten Sie wirklich den gesamten Cache löschen?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.cache.cache_data = {}
            self.cache.save_cache()
            QMessageBox.information(
                self, 'Cache geleert',
                'Der Cache wurde vollständig geleert.'
            )
            self.update_stats_display()
    
    def save_config(self):
        exiftool_path = self.exiftool_path_input.text().strip()
        if not exiftool_path:
            exiftool_path = 'exiftool'
        self.config.set_exiftool_path(exiftool_path)
        
        precision = self.precision_combo.currentData()
        self.config.set_cache_precision(precision)
        self.cache.set_precision(precision)
        
        max_age_days = self.max_age_spinbox.value()
        self.config.set_cache_max_age_days(max_age_days)
        self.cache.set_max_age_days(max_age_days)
        
        selected_types = [
            ftype for ftype, cb in self.filetype_checkboxes.items()
            if cb.isChecked()
        ]
        self.config.set_file_types(selected_types)
        
        self.accept()


class GeocodingWorker(QThread):
    """Worker-Thread für die Geocodierung"""
    
    progress = pyqtSignal(int, int)
    log = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    cache_stats = pyqtSignal(dict)
    
    def __init__(self, directory: str, config: Config, cache: GeocodingCache, skip_existing: bool):
        super().__init__()
        self.directory = directory
        self.config = config
        self.cache = cache
        self.skip_existing = skip_existing
        self.should_stop = False
        self.stats = {
            'cache_hits': 0,
            'api_calls': 0,
            'total_processed': 0,
            'skipped_already_tagged': 0,
            'skipped_no_gps': 0,
            'metadata_written': 0,
            'metadata_unchanged': 0
        }
    
    def run(self):
        try:
            self.log.emit('Suche nach Bilddateien...')
            image_files = self.find_image_files()
            
            if not image_files:
                self.log.emit('Keine Bilddateien gefunden.')
                self.finished.emit()
                return
            
            self.log.emit(f'{len(image_files)} Bilddatei(en) gefunden.')
            self.log.emit('─' * 60)
            
            for i, image_file in enumerate(image_files):
                if self.should_stop:
                    self.log.emit('Abgebrochen.')
                    break
                
                self.progress.emit(i + 1, len(image_files))
            
            self.log.emit('\n' + '=' * 60)
            self.log.emit('📊 Statistiken:')
            self.log.emit(f'   Gefundene Dateien: {len(image_files)}')
            self.log.emit('=' * 60)
            
            self.cache_stats.emit(self.stats)
            self.log.emit('\nFertig!')
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(f'Fehler: {str(e)}')
    
    def find_image_files(self) -> List[Path]:
        image_files = []
        file_types = self.config.get_file_types()
        
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                if any(file.lower().endswith(ft) for ft in file_types):
                    image_files.append(Path(root) / file)
        
        return image_files
    
    def stop(self):
        self.should_stop = True


class MainWindow(QMainWindow):
    """Hauptfenster der Anwendung"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.cache = GeocodingCache(
            precision=self.config.get_cache_precision(),
            max_age_days=self.config.get_cache_max_age_days()
        )
        self.worker = None
        self.setWindowTitle('Geo-Tagger - Automatische Reverse-Geocodierung')
        self.resize(800, 650)
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel('Geo-Tagger')
        header.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        subtitle = QLabel('Automatische Reverse-Geocodierung für Bilder')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet('color: gray;')
        layout.addWidget(subtitle)
        
        # Cache-Info
        self.cache_info_label = QLabel()
        self.cache_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cache_info_label.setStyleSheet('color: #0366d6; font-size: 11px;')
        layout.addWidget(self.cache_info_label)
        
        layout.addSpacing(20)
        
        # Verzeichnisauswahl
        dir_group = QGroupBox('Verzeichnis')
        dir_layout = QHBoxLayout()
        
        self.directory_input = QLineEdit(self.config.get_last_directory())
        dir_layout.addWidget(self.directory_input)
        
        browse_btn = QPushButton('Durchsuchen...')
        browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(browse_btn)
        
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)
        
        # Optimierungs-Optionen
        optimization_group = QGroupBox('⚡ Optimierungen')
        optimization_layout = QVBoxLayout()
        
        self.skip_existing_checkbox = QCheckBox('Bereits getaggte Bilder überspringen')
        self.skip_existing_checkbox.setChecked(self.config.get_skip_if_exists())
        self.skip_existing_checkbox.toggled.connect(self.on_skip_existing_changed)
        optimization_layout.addWidget(self.skip_existing_checkbox)
        
        optimization_group.setLayout(optimization_layout)
        layout.addWidget(optimization_group)
        
        # Aktionsbuttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton('▶ Starten')
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setStyleSheet('''
            QPushButton {
                background-color: #2ea44f;
                color: white;
                padding: 10px;
                font-weight: bold;
            }
        ''')
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton('⏹ Stoppen')
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        config_btn = QPushButton('⚙ Einstellungen')
        config_btn.clicked.connect(self.show_config)
        button_layout.addWidget(config_btn)
        
        layout.addLayout(button_layout)
        
        # Fortschritt
        progress_group = QGroupBox('Fortschritt')
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel('Bereit')
        progress_layout.addWidget(self.progress_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Log
        log_group = QGroupBox('Log')
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont('Courier', 9))
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton('Log löschen')
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        central_widget.setLayout(layout)
        
        # Cache-Info NACH Checkbox-Erstellung
        self.update_cache_info()
    
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, 'Verzeichnis auswählen',
            self.directory_input.text()
        )
        if directory:
            self.directory_input.setText(directory)
    
    def on_skip_existing_changed(self, checked):
        self.config.set_skip_if_exists(checked)
        self.update_cache_info()
    
    def show_config(self):
        dialog = ConfigDialog(self.config, self.cache, self)
        if dialog.exec():
            self.cache.set_precision(self.config.get_cache_precision())
            self.cache.set_max_age_days(self.config.get_cache_max_age_days())
            self.update_cache_info()
    
    def update_cache_info(self):
        cache_stats = self.cache.get_stats()
        skip_existing = "✓" if self.skip_existing_checkbox.isChecked() else "✗"
        info_text = (
            f"📦 Cache: {cache_stats['valid']} gültige Einträge ({cache_stats['max_age_days']} Tage) | "
            f"Genauigkeit: {cache_stats['precision_name']} | Schnellmodus: {skip_existing}"
        )
        self.cache_info_label.setText(info_text)
    
    def start_processing(self):
        directory = self.directory_input.text()
        
        if not directory or not os.path.isdir(directory):
            QMessageBox.warning(
                self, 'Ungültiges Verzeichnis',
                'Bitte wählen Sie ein gültiges Verzeichnis aus.'
            )
            return
        
        self.config.set_last_directory(directory)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.skip_existing_checkbox.setEnabled(False)
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        skip_existing = self.skip_existing_checkbox.isChecked()
        self.worker = GeocodingWorker(directory, self.config, self.cache, skip_existing)
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.append_log)
        self.worker.finished.connect(self.processing_finished)
        self.worker.error.connect(self.show_error)
        self.worker.cache_stats.connect(self.show_cache_stats)
        self.worker.start()
    
    def stop_processing(self):
        if self.worker:
            self.worker.stop()
            self.stop_btn.setEnabled(False)
    
    def update_progress(self, current: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f'{current} von {total} Dateien')
    
    def append_log(self, message: str):
        self.log_text.append(message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def processing_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.skip_existing_checkbox.setEnabled(True)
        self.progress_label.setText('Fertig')
        self.update_cache_info()
    
    def show_error(self, error_msg: str):
        QMessageBox.critical(self, 'Fehler', error_msg)
        self.processing_finished()
    
    def show_cache_stats(self, stats: dict):
        self.update_cache_info()


def main():
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        window = MainWindow()
        window.show()
        
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