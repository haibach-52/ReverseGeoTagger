"""
Hauptfenster für Geo-Tagger
"""

import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog,
    QTextEdit, QProgressBar, QGroupBox, QCheckBox,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import Config
from cache import GeocodingCache
from worker import GeocodingWorker
from dialogs import ConfigDialog


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
        
        self.skip_existing_checkbox = QCheckBox('Bereits getaggte Bilder überspringen (schneller)')
        self.skip_existing_checkbox.setChecked(self.config.get_skip_if_exists())
        self.skip_existing_checkbox.toggled.connect(self.on_skip_existing_changed)
        self.skip_existing_checkbox.setToolTip(
            'Wenn aktiviert, werden Bilder mit bereits vorhandenen Ortsdaten übersprungen.\n'
            'Dies beschleunigt die Verarbeitung erheblich.'
        )
        optimization_layout.addWidget(self.skip_existing_checkbox)
        
        optimization_hint = QLabel(
            '💡 <b>Empfohlen für schnellere Verarbeitung.</b> '
            'Deaktivieren nur wenn Ortsdaten aktualisiert werden sollen.'
        )
        optimization_hint.setWordWrap(True)
        optimization_hint.setStyleSheet('color: #586069; font-size: 10px; padding: 5px;')
        optimization_layout.addWidget(optimization_hint)
        
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
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2c974b;
            }
        ''')
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton('⏹ Stoppen')
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet('''
            QPushButton {
                background-color: #d73a49;
                color: white;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #cb2431;
            }
        ''')
        button_layout.addWidget(self.stop_btn)
        
        config_btn = QPushButton('⚙ Einstellungen')
        config_btn.clicked.connect(self.show_config)
        config_btn.setStyleSheet('padding: 10px; font-size: 13px;')
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
            f"Genauigkeit: {cache_stats['precision_name']} ({cache_stats['precision_accuracy']}) | "
            f"Schnellmodus: {skip_existing}"
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