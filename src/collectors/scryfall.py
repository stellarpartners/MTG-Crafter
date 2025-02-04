import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
from tqdm import tqdm
from datetime import datetime, timedelta
import hashlib
from database.card_database import CardDatabase

class ScryfallCollector:
    """Handles data collection from Scryfall API"""
    
    BASE_URL = "https://api.scryfall.com"
    BULK_DATA_URL = "https://api.scryfall.com/bulk-data"
    
    # Scryfall recommends no more than 10 requests per second
    REQUEST_DELAY = 0.1  # 100ms between requests
    
    def __init__(self, cache_dir: str = "cache/scryfall", data_dir: str = "data/database", skip_load: bool = False):
        self.cache_dir = Path(cache_dir)
        self.data_dir = Path(data_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        if not skip_load:
            self.database = CardDatabase(data_dir=data_dir)
        else:
            self.database = None
        
        # Cache files
        self.bulk_cache_file = self.cache_dir / "bulk_cards_cache.json"
        self.bulk_metadata_file = self.cache_dir / "bulk_cache_metadata.json"
        
        # Request tracking
        self.last_request_time = 0
        self.metadata_file = self.cache_dir / "metadata.json"
        self.load_metadata()
    
    def load_metadata(self):
        """Load or initialize metadata tracking"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                'sets': {},
                'last_update': None,
                'card_hashes': {}
            }
    
    def save_metadata(self):
        """Save current metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def calculate_card_hash(self, card_data: Dict) -> str:
        """Calculate hash of card data to detect changes"""
        card_str = json.dumps(card_data, sort_keys=True)
        return hashlib.md5(card_str.encode()).hexdigest()
    
    def needs_update(self, set_code: str, set_data: Dict) -> bool:
        """Check if a set needs updating"""
        if set_code not in self.metadata['sets']:
            return True
            
        stored_date = self.metadata['sets'][set_code]['updated_at']
        new_date = set_data.get('updated_at')
        return stored_date != new_date
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - time_since_last)
        self.last_request_time = time.time()
        
    def _make_request(self, url: str, params: Dict = None) -> requests.Response:
        """Make a rate-limited request"""
        self._wait_for_rate_limit()
        response = requests.get(url, params=params)
        
        if response.status_code == 429:  # Too Many Requests
            print("Rate limit hit, waiting 1 second...")
            time.sleep(1)
            return self._make_request(url, params)
            
        response.raise_for_status()
        return response
    
    def fetch_bulk_data_urls(self) -> Dict[str, str]:
        """Fetch URLs for bulk data downloads"""
        response = self._make_request(self.BULK_DATA_URL)
        
        data = response.json()
        return {
            item['type']: item['download_uri'] 
            for item in data['data']
        }
    
    def download_oracle_cards(self) -> List[Dict]:
        """Download all Oracle cards data"""
        urls = self.fetch_bulk_data_urls()
        oracle_url = urls['oracle_cards']
        
        print(f"Downloading Oracle cards from {oracle_url}")
        response = self._make_request(oracle_url)
        
        cards = response.json()
        
        # Save raw data
        output_file = self.cache_dir / "oracle_cards.json"
        with open(output_file, 'w') as f:
            json.dump(cards, f)
            
        return cards
    
    def fetch_card_by_name(self, name: str) -> Optional[Dict]:
        """Fetch a single card by exact name"""
        url = f"{self.BASE_URL}/cards/named"
        
        try:
            response = self._make_request(url, params={'exact': name})
            return response.json()
        except requests.exceptions.RequestException:
            return None
            
    def fetch_set_data(self) -> List[Dict]:
        """Fetch all set data"""
        url = f"{self.BASE_URL}/sets"
        response = self._make_request(url)
        
        sets = response.json()['data']
        
        # Save raw data
        output_file = self.cache_dir / "sets.json"
        with open(output_file, 'w') as f:
            json.dump(sets, f)
            
        return sets

    def fetch_sample_cards(self, count: int = 5) -> List[Dict]:
        """Fetch a small sample of random cards for testing"""
        url = f"{self.BASE_URL}/cards/random"
        cards = []
        
        print(f"Fetching {count} random cards...")
        for _ in range(count):
            response = self._make_request(url)
            card_data = response.json()
            cards.append(card_data)
            
        # Save sample data
        output_file = self.cache_dir / "sample_cards.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cards, f, indent=2)
            
        return cards

    def analyze_card_structure(self, cards: List[Dict]):
        """Analyze and print the data structure of cards"""
        print("\nAnalyzing card data structure:")
        
        # Collect all possible fields
        all_fields = set()
        for card in cards:
            all_fields.update(card.keys())
            
        # Analyze each field
        for field in sorted(all_fields):
            field_types = set()
            non_null_count = 0
            
            for card in cards:
                if field in card and card[field] is not None:
                    field_types.add(type(card[field]).__name__)
                    non_null_count += 1
                    
            presence_percentage = (non_null_count / len(cards)) * 100
            print(f"\n{field}:")
            print(f"  Present in {presence_percentage:.1f}% of cards")
            print(f"  Types: {', '.join(field_types)}")
            
            # Show example value from first card that has it
            for card in cards:
                if field in card and card[field] is not None:
                    example = card[field]
                    if isinstance(example, (dict, list)):
                        example = str(example)[:100] + "..." if len(str(example)) > 100 else str(example)
                    print(f"  Example: {example}")
                    break

    def fetch_standard_sets(self) -> List[Dict]:
        """Fetch all sets currently in Standard with error handling"""
        try:
            url = f"{self.BASE_URL}/sets"
            print(f"Making request to {url}...")
            
            response = self._make_request(url)
            data = response.json()
            
            if 'data' not in data:
                print(f"Unexpected API response format: {data}")
                return []
                
            sets_data = data['data']
            print(f"Found {len(sets_data)} total sets")
            
            # Debug: Print set types
            print("\nAnalyzing set types:")
            set_types = set(s.get('set_type') for s in sets_data)
            print(f"Available set types: {set_types}")
            
            # Filter Standard sets with debug info
            standard_sets = []
            for set_data in sets_data:
                set_type = set_data.get('set_type')
                
                # Standard sets are typically expansions or core sets that aren't digital-only
                if (set_type in ['expansion', 'core'] and 
                    not set_data.get('digital', False) and
                    datetime.strptime(set_data.get('released_at', '1970-01-01'), '%Y-%m-%d') > 
                    datetime.now() - timedelta(days=730)):  # roughly 2 years
                    
                    standard_sets.append(set_data)
                    print(f"Found Standard set: {set_data['name']} ({set_data['code']}) - Released: {set_data['released_at']}")
            
            if not standard_sets:
                print("\nNo Standard sets found. Example of first set data:")
                print(json.dumps(sets_data[0], indent=2))
            else:
                print(f"\nFound {len(standard_sets)} Standard-legal sets")
            
            # Sort by release date
            standard_sets.sort(key=lambda x: x.get('released_at', ''), reverse=True)
            
            # Save Standard sets data
            output_file = self.cache_dir / "standard_sets.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(standard_sets, f, indent=2)
            
            return standard_sets
            
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching Standard sets: {e}")
            print(f"Response status code: {getattr(e.response, 'status_code', 'N/A')}")
            print(f"Response text: {getattr(e.response, 'text', 'N/A')}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching Standard sets: {type(e).__name__}: {e}")
            return []
    
    def fetch_cards_from_set(self, set_code: str, force_update: bool = False) -> List[Dict]:
        """Fetch all cards from a specific set with progress bar and update checking"""
        url = f"{self.BASE_URL}/cards/search"
        cards = []
        
        try:
            # Check if we need to update
            set_file = self.cache_dir / f"cards_{set_code}.json"
            if not force_update and set_file.exists():
                with open(set_file, 'r') as f:
                    cards = json.load(f)
                if not self.needs_update(set_code, {'updated_at': self.metadata['sets'].get(set_code, {}).get('updated_at')}):
                    print(f"Set {set_code} is up to date, skipping...")
                    return cards
            
            print(f"Fetching cards from set {set_code}...")
            
            # First request to get total count
            params = {'q': f'set:{set_code}', 'page': 1}
            response = self._make_request(url, params)
            data = response.json()
            total_cards = data.get('total_cards', 0)
            
            # Initialize progress bar
            with tqdm(total=total_cards, desc=f"Downloading {set_code}") as pbar:
                cards.extend(data.get('data', []))
                pbar.update(len(data.get('data', [])))
                
                # Get remaining pages
                while data.get('has_more', False):
                    params['page'] += 1
                    try:
                        response = self._make_request(url, params)
                        data = response.json()
                        new_cards = data.get('data', [])
                        cards.extend(new_cards)
                        pbar.update(len(new_cards))
                    except requests.exceptions.RequestException as e:
                        print(f"Error on page {params['page']}: {e}")
                        continue
            
            # Update metadata
            self.metadata['sets'][set_code] = {
                'updated_at': datetime.now().isoformat(),
                'card_count': len(cards)
            }
            
            # Save cards and metadata
            with open(set_file, 'w', encoding='utf-8') as f:
                json.dump(cards, f, indent=2)
            self.save_metadata()
            
            return cards
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching cards from set {set_code}: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error processing set {set_code}: {e}")
            return []

    def fetch_all_cards(self, force_download: bool = False) -> List[Dict]:
        """Download or load cached Oracle cards from Scryfall bulk data"""
        cache_status = self._check_cache()
        
        if not force_download and cache_status.exists:
            if cache_status.is_current:
                print("\nUsing cached card data...")
                print(f"Cache date: {cache_status.cache_date}")
                print(f"Cards in cache: {cache_status.card_count:,}")
                
                with open(self.bulk_cache_file, 'r') as f:
                    cards = json.load(f)
                if self.database:  # Only update database if it exists
                    self.database.update_from_scryfall(cards)
                return cards
            else:
                print("\nCache is outdated:")
                print(f"Cache date: {cache_status.cache_date}")
                print(f"Latest Scryfall update: {cache_status.latest_update}")
                use_cache = input("Use cached data anyway? (y/N): ").lower() == 'y'
                if use_cache:
                    with open(self.bulk_cache_file, 'r') as f:
                        cards = json.load(f)
                    if self.database:  # Only update database if it exists
                        self.database.update_from_scryfall(cards)
                    return cards
        
        # Download new data
        print("\nDownloading fresh card data from Scryfall...")
        try:
            # Get bulk data information
            response = requests.get(self.BULK_DATA_URL)
            response.raise_for_status()
            bulk_data = response.json()
            
            # Find the Oracle cards download URL
            oracle_bulk = next(
                data for data in bulk_data['data'] 
                if data['type'] == 'oracle_cards'
            )
            
            print(f"Downloading {oracle_bulk['size'] // 1024 // 1024}MB of card data...")
            print(f"Last updated: {oracle_bulk['updated_at']}")
            
            # Download the bulk data file
            cards_response = requests.get(oracle_bulk['download_uri'])
            cards_response.raise_for_status()
            cards = cards_response.json()
            
            # Save to cache
            print("Saving to cache...")
            with open(self.bulk_cache_file, 'w') as f:
                json.dump(cards, f)
            with open(self.bulk_metadata_file, 'w') as f:
                json.dump({
                    'downloaded_at': datetime.now().isoformat(),
                    'last_updated': oracle_bulk['updated_at'],
                    'card_count': len(cards)
                }, f, indent=2)
            
            return cards
            
        except Exception as e:
            print(f"Error downloading cards: {e}")
            if cache_status.exists:
                print("Falling back to cached data...")
                with open(self.bulk_cache_file, 'r') as f:
                    cards = json.load(f)
                if self.database:  # Only update database if it exists
                    self.database.update_from_scryfall(cards)
                return cards
            return []
    
    def _check_cache(self) -> 'CacheStatus':
        """Check status of cached data"""
        if not self.bulk_cache_file.exists() or not self.bulk_metadata_file.exists():
            return CacheStatus(exists=False)
            
        try:
            # Get cache metadata
            with open(self.bulk_metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Get latest Scryfall update
            response = requests.get(self.BULK_DATA_URL)
            response.raise_for_status()
            bulk_data = response.json()
            oracle_bulk = next(
                data for data in bulk_data['data'] 
                if data['type'] == 'oracle_cards'
            )
            
            return CacheStatus(
                exists=True,
                is_current=metadata['last_updated'] == oracle_bulk['updated_at'],
                cache_date=metadata['downloaded_at'],
                latest_update=oracle_bulk['updated_at'],
                card_count=metadata['card_count']
            )
        except Exception as e:
            print(f"Error checking cache: {e}")
            return CacheStatus(exists=False)

class CacheStatus:
    def __init__(self, exists: bool, is_current: bool = False, 
                 cache_date: str = None, latest_update: str = None,
                 card_count: int = 0):
        self.exists = exists
        self.is_current = is_current
        self.cache_date = cache_date
        self.latest_update = latest_update
        self.card_count = card_count

if __name__ == "__main__":
    collector = ScryfallCollector()
    
    # Fetch Standard sets
    print("Fetching Standard sets...")
    standard_sets = collector.fetch_standard_sets()
    
    if not standard_sets:
        print("Error: Could not fetch Standard sets")
        exit(1)
        
    print(f"Found {len(standard_sets)} Standard sets:")
    for set_data in standard_sets:
        print(f"- {set_data['name']} ({set_data['code']}) - Released: {set_data['released_at']}")
    
    # Fetch cards from each Standard set
    all_standard_cards = []
    for set_data in standard_sets:
        set_cards = collector.fetch_cards_from_set(set_data['code'])
        all_standard_cards.extend(set_cards)
    
    if all_standard_cards:
        # Save all Standard cards
        output_file = collector.cache_dir / "standard_cards.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_standard_cards, f, indent=2)
        
        print(f"\nTotal Standard cards downloaded: {len(all_standard_cards)}")
    else:
        print("Error: No Standard cards were downloaded")
    
    # Fetch and analyze sample cards
    sample_cards = collector.fetch_sample_cards(5)
    collector.analyze_card_structure(sample_cards)
    
    # Print full data for one card as example
    print("\nDetailed example of one card:")
    print(json.dumps(sample_cards[0], indent=2))
    
    # Download all Oracle cards
    print("Downloading Oracle cards...")
    cards = collector.download_oracle_cards()
    print(f"Downloaded {len(cards)} cards")
    
    # Fetch a specific card
    print("\nFetching a specific card...")
    sol_ring = collector.fetch_card_by_name("Sol Ring")
    if sol_ring:
        print(f"Found: {sol_ring['name']} - {sol_ring['mana_cost']}")
    
    # Fetch set data
    print("\nFetching set data...")
    sets = collector.fetch_set_data()
    print(f"Downloaded {len(sets)} sets")
    
    # Fetch all cards
    print("Fetching all cards...")
    all_cards = collector.fetch_all_cards()
    print(f"Downloaded {len(all_cards)} cards") 