"""
Konfigurationsverwaltung für Geo-Tagger
"""

import json
from typing import List
from pathlib import Path
from PyQt6.QtCore import QSettings


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