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

### AI-Powered Analysis
- Semantic theme detection using BERT and Sentence Transformers
- Mechanical pattern recognition
- Synergy scoring
- Card categorization based on role and function
- Theme relationship mapping

### Data Collection and Management
- Intelligent card data collection from Scryfall API
- Automatic cache management
- Format banlist tracking
- Theme and keyword processing
- Oracle text analysis

### Deck Output
- Multiple export formats (JSON, CSV, Moxfield)
- Detailed card information
- Theme analysis results
- Synergy explanations

## Directory Structure

```
project/
├── src/
│ ├── deckbuilding/ # Core deck building logic
│ │ ├── lib/ # Core libraries
│ │ │ ├── theme_learner.py # Theme detection
│ │ │ └── models.py # Data models
│ │ ├── ml/ # Machine learning components
│ │ │ ├── semantic_analyzer.py # Semantic analysis
│ │ │ └── embeddings.py # Text embeddings
│ │ └── deck_suggester.py # Main suggestion engine
│ ├── collectors/ # Data collection
│ │ ├── data_engine.py # Centralized data management
│ │ ├── scryfall.py # Scryfall API interface
│ │ └── theme_.py # Theme collectors
│ ├── database/ # Database management
│ │ └── card_database.py # Card data processing
│ └── utils/ # Utility functions
│
├── data/ # Processed data
│ ├── analyzed_cards/ # Generated deck suggestions
│ ├── models/ # Trained ML models
│ ├── training/ # Training data
│ ├── oracle/ # Card database
│ └── metadata.json # Update tracking and configurations
│
├── rules/ # Game rules and restrictions
│ ├── banned_restricted.md # Format-specific banlists
│ └── format_rules.md # Format-specific rules
│
└── docs/ # Project documentation
└── product_management.md # Development tracking
```

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Dependencies
- Python 3.8+
- PyTorch
- Transformers
- Sentence-Transformers
- TQDM
- NumPy
- scikit-learn

## Usage

### Deck Building
```bash
python 3.build_deck.py
```

The deck builder offers several options:

1. **Build around a card**
   - Enter any legendary creature name
   - AI analyzes the card's themes and mechanics
   - Get categorized card suggestions based on:
     - Commander's colors
     - Mechanical themes (e.g., sacrifice, counters)
     - Semantic relationships
     - Synergy patterns

2. **Build from colors/themes**
   - Choose your color combination
   - Select from available themes
   - Get suggestions that match both colors and themes

3. **Setup/Update Models**
   - Download card data
   - Train theme classifier
   - Update semantic models

### Data Collection
```bash
python 1.gather_data.py
```

## How It Works

### Theme Detection

The system uses multiple approaches to identify card themes:

1. **Semantic Analysis**
   - Uses BERT and Sentence Transformers for text understanding
   - Compares card text semantically
   - Identifies thematic similarities
   - Learns from card relationships

2. **Pattern Recognition**
   - Identifies mechanical themes like:
     - +1/+1 counters
     - Graveyard interaction
     - Sacrifice effects
     - Enter-the-battlefield triggers
   - Analyzes keyword frequency
   - Detects synergy patterns

3. **Color Identity**
   - Respects commander color identity
   - Filters suggestions appropriately
   - Considers color-specific mechanics

### Card Categorization

Cards are intelligently sorted into categories:

- **Commander**: The deck's leader
- **Core**: Primary theme enablers (25 cards)
- **Support**: Synergistic additions (35 cards)
- **Utility**: Interaction/removal (25 cards)
- **Lands**: Theme-supporting lands (14 cards)

### Machine Learning Components

1. **Semantic Analyzer**
   - Uses transformer models for text understanding
   - Identifies thematic relationships
   - Scores card synergies
   - Learns from example decks

2. **Theme Learner**
   - Discovers themes from card text
   - Clusters related mechanics
   - Maps theme relationships
   - Identifies key cards per theme

## Development

The project uses a modular architecture with several key components:

- `deck_suggester.py`: Main interface for deck suggestions
- `theme_learner.py`: Theme discovery and analysis
- `semantic_analyzer.py`: ML-powered text analysis
- `embeddings.py`: Text embedding generation

### Future Development

Planned features:
- Interactive deck building
- Archetype detection
- Price consideration
- Format legality checking
- Deck statistics
- Power level estimation

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for any enhancements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
