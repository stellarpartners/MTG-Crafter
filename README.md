# MTG Crafter

A Magic: The Gathering data collection and search engine.

## Features

### Data Collection (`1.gather_data.py`)
- Smart set-based data collection from Scryfall
- Automatic cache management
- Format banlist tracking
- Theme collection from EDHREC
- Rules and keyword processing

### Card Search (`2.search_cards.py`)
- Search by exact card name
- Full text search
- View all printings with prices
- Track Oracle text changes
- Access card images

## Directory Structure

```
project/
├── src/
│   ├── search/            # Search engine components
│   │   ├── engine.py      # Core search functionality
│   │   ├── indexer.py     # Card indexing
│   │   └── models.py      # Data models
│   └── collectors/        # Data collection
│       ├── data_engine.py # Main collection engine
│       ├── scryfall.py    # Scryfall interface
│       └── theme_*.py     # Theme collectors
│
├── cache/                 # Raw downloaded data
│   ├── scryfall/         # Card data from Scryfall
│   │   └── sets/         # Individual set data
│   ├── themes/           # Theme data
│   ├── rules/            # Game rules
│   └── banlists/         # Format banlists
│
├── data/                 # Processed data
│   ├── database/        # Core card database
│   ├── themes/          # Processed themes
│   ├── keywords/        # Processed keywords
│   └── banlists/        # Processed banlist data
```

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -e .
```

## Usage

### Data Collection
```bash
python gather_data.py
```

Options:
1. Show Cache Status
2. Fresh Start (Download Everything)
3. Update Individual Components
4. Rebuild from Cache
5. Cache Maintenance
6. View Card Data

### Card Search
```bash
python search_cards.py
```

## Development

The project uses a modular architecture:
- `src/search/` - Search engine components
- `src/collectors/` - Data collection modules
- Smart caching system that tracks updates per set
- Type-safe data models using dataclasses

## Cache Management

- Individual set files in `cache/scryfall/sets/`
- Set-level metadata tracking
- Automatic update detection
- Selective downloading of new/changed sets
