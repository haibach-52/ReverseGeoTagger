"""
Cache-System für Geocoding-Ergebnisse
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta


class GeocodingCache:
    """Cache für Geocodierung-Ergebnisse"""
    
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