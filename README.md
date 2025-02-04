# MTG Crafter

A Magic: The Gathering data processing engine.

## Directory Structure

```
project/
├── cache/                  # Raw downloaded data
│   ├── scryfall/          # Raw Scryfall downloads
│   │   ├── bulk_data.json
│   │   └── metadata.json
│   ├── themes/            # Raw theme data
│   │   └── edhrec/
│   └── rules/             # Downloaded rules
│
├── data/                   # Processed data
│   ├── database/          # Core card database
│   ├── themes/            # Processed themes
│   └── keywords/          # Processed keywords
```

## Usage

Run the engine with:
```bash
python src/run_engine.py
```

### Main Menu Options:
1. Show Cache Status - View status of downloaded data
2. Fresh Start - Download and compile everything
3. Compile Data from Cache - Process existing downloads
4. Update Components - Update specific components
5. Rebuild Data - Recompile from existing cache
6. Cache Maintenance - Manage cached data
7. Exit

### Cache Maintenance:
- Show Cache Size
- Clean Old Cache Files
- Verify Cache Integrity
- Delete All Cache

## Development

### Key Components:
- DataEngine: Main orchestrator
- ScryfallCollector: Handles Scryfall API interaction
- CardDatabase: Processes and stores card data
- ThemeCollector: Manages theme data from various sources
- KeywordCollector: Processes card keywords and rules

## Features

Current:
- ✓ Format-specific deck validation (Standard, Commander, Modern, Legacy)
- ✓ Automatic card data updates from Scryfall
- ✓ Keyword and ability word analysis
- ✓ Ban list tracking
- ✓ Comprehensive rules integration
- ✓ EDHREC theme tracking
- ✓ Theme categorization and color analysis
- ✓ Historical theme data collection

Planned:
- [ ] Deck statistics and analysis
- [ ] Card synergy detection
- [ ] Collection management
- [ ] Deck recommendations
- [ ] Budget optimization
- [ ] Theme-based deck suggestions
- [ ] Color identity analysis
- [ ] Theme trend analysis

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup
1. Clone the repository and navigate to the project directory
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Add Python Scripts to PATH (if you see PATH warnings):
   - Windows: Add to PATH: `%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\Scripts`
   - Linux/Mac: Usually handled automatically

3. Initialize the card database:
   ```bash
   python src/collectors/scryfall.py
   ```

The initialization will:
- Download current Standard-legal sets
- Extract keywords and ability words
- Generate ban lists
- Create necessary data structures

## Usage

### Basic Deck Creation
```python
from src.models.deck import Deck
from src.collectors.scryfall import ScryfallCollector

# Initialize collector and create a Standard deck
collector = ScryfallCollector()
deck = Deck(format_name="standard")

# Add some cards
card = collector.fetch_card_by_name("Consider")
deck.add_card(card, count=4)

# Validate the deck
errors = deck.validate()
if errors:
    print("Validation errors:", errors)
```

### Commander Deck
```python
# Create a Commander deck
deck = Deck(format_name="commander")

# Set commander
commander = collector.fetch_card_by_name("Atraxa, Praetors' Voice")
deck.commander = commander

# Add cards that match commander's color identity
deck.add_card(collector.fetch_card_by_name("Ghostly Prison"))
deck.add_card(collector.fetch_card_by_name("Cultivate"))
```

### Working with Collections
```python
from src.models.collection import Collection

# Initialize a collection
collection = Collection()

# Add cards with specific conditions
card = collector.fetch_card_by_name("Lightning Bolt")
collection.add_card(card, quantity=2, condition="NM", is_foil=False)

# Check if you can build a deck from your collection
can_build = collection.can_build_deck(deck.cards)
```
 
