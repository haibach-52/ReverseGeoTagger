"""
Worker-Thread für die Geocodierung
"""

import os
import subprocess
import requests
from pathlib import Path
from typing import Optional, Tuple, List, Dict

from PyQt6.QtCore import QThread, pyqtSignal

from config import Config
from cache import GeocodingCache


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
            
            precision_info = self.cache.get_precision_info()
            self.log.emit(f'Cache-Genauigkeit: {precision_info["name"]} ({precision_info["accuracy"]})')
            self.log.emit(f'Cache-Lebensdauer: {self.cache.cache_max_age_days} Tage')
            
            if self.skip_existing:
                self.log.emit('⚡ Bereits getaggte Bilder werden übersprungen')
            
            self.log.emit('─' * 60)
            
            for i, image_file in enumerate(image_files):
                if self.should_stop:
                    self.log.emit('Abgebrochen.')
                    break
                
                self.progress.emit(i + 1, len(image_files))
                self.process_image(image_file)
            
            self.log.emit('\n' + '=' * 60)
            self.log.emit('📊 Statistiken:')
            self.log.emit(f'   Gefundene Dateien: {len(image_files)}')
            self.log.emit(f'   Verarbeitete Dateien: {self.stats["total_processed"]}')
            self.log.emit(f'   Übersprungen (bereits getaggt): {self.stats["skipped_already_tagged"]}')
            self.log.emit(f'   Übersprungen (keine GPS): {self.stats["skipped_no_gps"]}')
            self.log.emit(f'   Cache-Treffer: {self.stats["cache_hits"]}')
            self.log.emit(f'   API-Aufrufe: {self.stats["api_calls"]}')
            self.log.emit(f'   Metadaten geschrieben: {self.stats["metadata_written"]}')
            self.log.emit(f'   Metadaten unverändert: {self.stats["metadata_unchanged"]}')
            
            if self.stats['total_processed'] > 0:
                cache_rate = (self.stats['cache_hits'] / self.stats['total_processed']) * 100
                self.log.emit(f'   Cache-Trefferquote: {cache_rate:.1f}%')
            
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
    
    def check_existing_location_data(self, image_path: Path) -> bool:
        try:
            result = subprocess.run(
                [
                    self.config.get_exiftool_path(),
                    '-IPTC:City',
                    '-XMP:City',
                    '-s3',
                    str(image_path)
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout.strip()
            return bool(output)
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
    
    def get_gps_data(self, image_path: Path) -> Optional[Tuple[float, float]]:
        xmp_path = image_path.with_suffix(image_path.suffix + '.xmp')
        
        use_xmp = False
        if xmp_path.exists():
            image_mtime = image_path.stat().st_mtime
            xmp_mtime = xmp_path.stat().st_mtime
            if xmp_mtime > image_mtime:
                use_xmp = True
                self.log.emit(f'  → XMP-Sidecar ist neuer')
        
        file_to_read = xmp_path if use_xmp else image_path
        
        try:
            result = subprocess.run(
                [
                    self.config.get_exiftool_path(),
                    '-GPSLatitude',
                    '-GPSLongitude',
                    '-n',
                    str(file_to_read)
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            lat, lon = None, None
            for line in result.stdout.split('\n'):
                if 'GPS Latitude' in line:
                    try:
                        lat = float(line.split(':')[1].strip())
                    except (IndexError, ValueError):
                        pass
                elif 'GPS Longitude' in line:
                    try:
                        lon = float(line.split(':')[1].strip())
                    except (IndexError, ValueError):
                        pass
            
            if lat is not None and lon is not None:
                return (lat, lon)
            
        except subprocess.TimeoutExpired:
            self.log.emit(f'  ⚠ Timeout beim Lesen')
        except FileNotFoundError:
            self.log.emit('  ⚠ ExifTool nicht gefunden')
        except Exception as e:
            self.log.emit(f'  ⚠ Fehler: {str(e)}')
        
        return None
    
    def compare_location_data(self, image_path: Path, new_location: Dict[str, str]) -> bool:
        try:
            result = subprocess.run(
                [
                    self.config.get_exiftool_path(),
                    '-IPTC:City',
                    '-IPTC:Province-State',
                    '-IPTC:Country-PrimaryLocationName',
                    '-s3',
                    str(image_path)
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.strip().split('\n')
            existing_city = lines[0] if len(lines) > 0 else ''
            existing_state = lines[1] if len(lines) > 1 else ''
            existing_country = lines[2] if len(lines) > 2 else ''
            
            new_city = new_location.get('city', '')
            new_state = new_location.get('state', '')
            new_country = new_location.get('country', '')
            
            if (existing_city == new_city and 
                existing_state == new_state and 
                existing_country == new_country):
                return False
            
            return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return True
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        cached_data = self.cache.get(lat, lon)
        if cached_data:
            self.log.emit(f'  💾 Cache-Treffer')
            self.stats['cache_hits'] += 1
            return cached_data
        
        self.log.emit(f'  🌐 Photon API Abfrage...')
        self.stats['api_calls'] += 1
        
        try:
            url = 'https://photon.komoot.io/reverse'
            params = {
                'lat': lat,
                'lon': lon,
                'lang': 'de'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'features' in data and len(data['features']) > 0:
                props = data['features'][0]['properties']
                
                location_data = {
                    'country': props.get('country', ''),
                    'state': props.get('state', ''),
                    'county': props.get('county', ''),
                    'city': props.get('city', ''),
                    'suburb': props.get('suburb', ''),
                    'district': props.get('district', ''),
                    'street': props.get('street', ''),
                    'housenumber': props.get('housenumber', ''),
                    'postcode': props.get('postcode', ''),
                    'name': props.get('name', ''),
                    'locality': props.get('locality', ''),
                    'countrycode': props.get('countrycode', ''),
                }
                
                self.cache.set(lat, lon, location_data)
                
                return location_data
        
        except requests.RequestException as e:
            self.log.emit(f'  ⚠ API Fehler: {str(e)}')
        except Exception as e:
            self.log.emit(f'  ⚠ Fehler: {str(e)}')
        
        return None
    
    def write_location_data(self, image_path: Path, location: Dict[str, str]):
        xmp_path = image_path.with_suffix(image_path.suffix + '.xmp')
        
        args = [self.config.get_exiftool_path()]
        
        if location.get('country'):
            args.extend([
                f'-IPTC:Country-PrimaryLocationName={location["country"]}',
                f'-XMP:Country={location["country"]}',
                f'-XMP-iptcExt:LocationShownCountryName={location["country"]}'
            ])
        
        if location.get('countrycode'):
            args.extend([
                f'-IPTC:Country-PrimaryLocationCode={location["countrycode"].upper()}',
                f'-XMP:CountryCode={location["countrycode"].upper()}',
                f'-XMP-iptcExt:LocationShownCountryCode={location["countrycode"].upper()}'
            ])
        
        if location.get('state'):
            args.extend([
                f'-IPTC:Province-State={location["state"]}',
                f'-XMP:State={location["state"]}',
                f'-XMP-iptcExt:LocationShownProvinceState={location["state"]}'
            ])
        
        if location.get('county'):
            args.extend([
                f'-XMP-iptcExt:LocationShownCity={location["county"]}',
            ])
        
        if location.get('city'):
            args.extend([
                f'-IPTC:City={location["city"]}',
                f'-XMP:City={location["city"]}',
                f'-XMP-photoshop:City={location["city"]}'
            ])
        
        suburb_or_district = location.get('suburb') or location.get('district')
        if suburb_or_district:
            args.extend([
                f'-IPTC:Sub-location={suburb_or_district}',
                f'-XMP:Location={suburb_or_district}',
                f'-XMP-iptcExt:LocationShownSublocation={suburb_or_district}'
            ])
        
        if location.get('street'):
            street_full = location['street']
            if location.get('housenumber'):
                street_full += f' {location["housenumber"]}'
            
            args.extend([
                f'-XMP-iptcCore:Location={street_full}',
            ])
        
        if location.get('postcode'):
            args.extend([
                f'-XMP-photoshop:PostalCode={location["postcode"]}',
            ])
        
        if location.get('name') and not location.get('city'):
            args.extend([
                f'-XMP-iptcExt:LocationShownCity={location["name"]}'
            ])
        
        args.extend([
            '-overwrite_original',
            '-P',
            '-codedcharacterset=utf8',
            str(image_path)
        ])
        
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log.emit(f'  ✓ Metadaten geschrieben')
                self.stats['metadata_written'] += 1
                
                if xmp_path.exists():
                    xmp_args = args.copy()
                    xmp_args[-1] = str(xmp_path)
                    subprocess.run(xmp_args, capture_output=True, timeout=30)
                    self.log.emit(f'  ✓ XMP-Sidecar aktualisiert')
            else:
                self.log.emit(f'  ⚠ ExifTool Fehler')
        
        except subprocess.TimeoutExpired:
            self.log.emit(f'  ⚠ Timeout')
        except Exception as e:
            self.log.emit(f'  ⚠ Fehler: {str(e)}')
    
    def process_image(self, image_path: Path):
        self.log.emit(f'\n📷 {image_path.name}')
        
        if self.skip_existing and self.check_existing_location_data(image_path):
            self.log.emit('  ⏭️  Bereits getaggt')
            self.stats['skipped_already_tagged'] += 1
            return
        
        gps_data = self.get_gps_data(image_path)
        
        if not gps_data:
            self.log.emit('  ⊘ Keine GPS-Daten')
            self.stats['skipped_no_gps'] += 1
            return
        
        lat, lon = gps_data
        self.log.emit(f'  📍 GPS: {lat:.6f}, {lon:.6f}')
        
        location = self.reverse_geocode(lat, lon)
        
        if not location:
            self.log.emit('  ⊘ Keine Ortsdaten gefunden')
            return
        
        self.stats['total_processed'] += 1
        
        location_parts = []
        if location.get('street'):
            street = location['street']
            if location.get('housenumber'):
                street += f' {location["housenumber"]}'
            location_parts.append(street)
        
        if location.get('postcode'):
            location_parts.append(location['postcode'])
        
        if location.get('suburb') or location.get('district'):
            location_parts.append(location.get('suburb') or location.get('district'))
        
        if location.get('city'):
            location_parts.append(location['city'])
        
        if location.get('county'):
            location_parts.append(f"({location['county']})")
        
        if location.get('state'):
            location_parts.append(location['state'])
        
        if location.get('country'):
            country_display = location['country']
            if location.get('countrycode'):
                country_display += f" ({location['countrycode'].upper()})"
            location_parts.append(country_display)
        
        location_str = ', '.join(filter(None, location_parts))
        self.log.emit(f'  🌍 {location_str}')
        
        if not self.compare_location_data(image_path, location):
            self.log.emit('  ⏭️  Daten bereits korrekt')
            self.stats['metadata_unchanged'] += 1
            return
        
        self.write_location_data(image_path, location)
    
    def stop(self):
        self.should_stop = True