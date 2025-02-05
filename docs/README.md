# MTG Crafter Documentation

## System Components

### [1. Data Collection](1.data_collection.md)
The data collection system manages card data, rules, and themes from various sources.
- Data Engine and Collectors
- Cache Management
- API Integration
- Error Handling

### [2. Search System](2.search_system.md)
Card search and lookup functionality with advanced filtering.
- Search Methods
- Data Models
- Results Display
- Advanced Features

### [3. Deck Building](3.deck_building.md)
AI-powered deck building and suggestion system.
- Theme Analysis
- Machine Learning Pipeline
- Card Categorization
- Output Formats

## Quick Start

1. Initial Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Download card data and train models
python 3.build_deck.py
# Select option 3 (Setup/Update Models)
```

2. Building Your First Deck
```bash
python 3.build_deck.py
# Select option 1 (Build around a card)
# Enter a legendary creature name
```

## Architecture Overview

```
MTG Crafter
├── Data Collection Layer
│   └── Manages raw data acquisition and processing
├── Search Layer
│   └── Provides card lookup and filtering
└── Deck Building Layer
    └── AI-powered deck suggestions and analysis
```

## Development Workflow

1. Data Updates
   - Run `1.gather_data.py` to update card database
   - Check cache status for data freshness
   - Validate downloaded data

2. Card Search
   - Use `2.search_cards.py` for card lookup
   - View card details and printings
   - Check price history

3. Deck Building
   - Use `3.build_deck.py` for deck creation
   - Review AI suggestions
   - Export in desired format

## Additional Resources
- [Contributing Guidelines](../CONTRIBUTING.md)
- [License](../LICENSE)
- [Project Roadmap](roadmap.md) 