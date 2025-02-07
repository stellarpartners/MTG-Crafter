# MTG Crafter

An AI-powered Magic: The Gathering deck building assistant that uses semantic analysis and machine learning to suggest thematic and synergistic decks.

## Features

### Smart Deck Building
- Build decks around any legendary creature
- Theme-based deck construction
- AI-powered card suggestions
- Color identity validation
- Synergy detection
- Multiple deck categories (Commander, Core pieces, Support, Utility, Lands)
- **Unified Export Formats:** Export decks in JSON (detailed), CSV (tabular) and Moxfield (simple list) formats using a centralized exporter pipeline.

### AI-Powered Analysis
- Semantic theme detection using BERT and Sentence Transformers
- Mechanical pattern recognition
- Synergy scoring and card categorization based on role and function
- Theme relationship mapping

### Data Collection and Management
- Intelligent card data collection from the Scryfall API
- Automatic cache management (with orphaned file cleanup via CacheManager)
- Banlist tracking and rules validation
- Theme and keyword processing
- Oracle text analysis

### Deck Output
- Multiple export formats (JSON, CSV, Moxfield)
- Detailed card information including cost, type, and oracle text
- Simplified Moxfield export (one card per line, no extra metadata)
- Consistent error handling and metadata logging

## Directory Structure

```
project/
├── src/
│   ├── deckbuilding/         # Core deck building logic
│   │   ├── lib/              # Core libraries: theme detection, data models
│   │   ├── ml/               # Machine learning components: semantic analysis, embeddings
│   │   └── deck_suggester.py # Main deck suggestion engine
│   ├── manalysis/           # Mana analysis components
│   │   ├── analyzer.py      # Core analysis logic
│   │   ├── cli.py          # Command-line interface
│   │   ├── deck_loader.py  # Deck import functionality
│   │   └── models.py       # Mana-related data models
│   ├── collectors/          # Data collection interfaces (Scryfall, themes, etc.)
│   ├── database/            # Card database processing and management
│   └── utils/               # Utility functions (exporters, cache management)
├── data/                    # Processed data and analyzed decks (e.g., analyzed_cards)
├── cache/                   # Cached API responses and processed data
├── rules/                   # Game rules and banlists
└── docs/                    # Project documentation (roadmap, guides, etc.)
```

## Quick Start

1. **Initial Setup**
   ```bash
   # Install dependencies
   pip install -r requirements.txt

   # Download card data and train models, then run deck builder
   python 3.build_deck.py
   # Select option 3 (Setup/Update Models) if required
   ```

2. **Building Your First Deck**
   ```bash
   python 3.build_deck.py
   # Select option 1 (Build around a card)
   # Enter a legendary creature name when prompted
   ```

## Architecture Overview

```
MTG Crafter
├── Data Collection Layer
│   └── Manages raw data acquisition, caching, and updates
├── Search Layer
│   └── Provides efficient card lookup and filtering
└── Deck Building Layer
    └── AI-powered deck suggestions with a unified export pipeline and robust error handling
```

## Development Workflow

1. **Data Updates**
   - Run `1.gather_data.py` to update the card database.
   - Verify cache integrity and freshness through CacheManager.
   - Validate downloaded data via metadata tracking.

2. **Card Search**
   - Use `2.search_cards.py` for detailed card lookup.
   - View card details, printings, price history, and legality information.

3. **Deck Building**
   - Use `3.build_deck.py` for deck creation.
   - Review AI-driven deck suggestions.
   - Export decks in multiple formats (JSON, CSV, Moxfield) saved under `data/analyzed_cards`.

## Additional Resources
- [Contributing Guidelines](../CONTRIBUTING.md)
- [License](../LICENSE)
- [Project Roadmap](roadmap.md) 