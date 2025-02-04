mtg_deck_builder/
├── data/                  # Data storage
│   ├── raw/              # Raw downloaded data
│   └── processed/        # Processed/analyzed data
├── docs/                 # Documentation
│   ├── rules/           # Current rules docs
│   └── project/         # Project management docs
├── src/                  # Source code
│   ├── collectors/      # Data collection modules
│   │   ├── __init__.py
│   │   ├── scryfall.py  # Scryfall API client
│   │   └── edhrec.py    # EDHREC data collector
│   ├── models/          # Data models
│   │   ├── __init__.py
│   │   ├── card.py      # Card class
│   │   └── deck.py      # Deck class
│   ├── validation/      # Validation logic
│   │   ├── __init__.py
│   │   └── rules.py     # Rule checking
│   └── utils/           # Utility functions
│       ├── __init__.py
│       └── color.py     # Color handling
└── tests/               # Test files
    └── __init__.py 