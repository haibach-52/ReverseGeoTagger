"""
Dialog-Fenster für Geo-Tagger
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QGroupBox, QComboBox, QSpinBox, QCheckBox,
    QScrollArea, QWidget, QMessageBox, QFileDialog
)

from config import Config
from cache import GeocodingCache


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
            '<b>Empfehlung:</b> 30 Tage für normale Nutzung. '
            'Kürzere Dauer (7-14 Tage) für häufig ändernde Daten.'
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