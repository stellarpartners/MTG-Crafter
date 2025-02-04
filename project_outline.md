# MTG Deck Builder Project

## Project Goals
- Create a tool to build Magic: The Gathering decks based on specific attributes
- Implement deck building rules and constraints
- Provide intelligent card suggestions based on synergies
- Store and analyze deck data

## Components

### 1. Data Collection
- Card database (potentially from Scryfall API)
- Card attributes:
  - Mana cost
  - Colors
  - Card types
  - Keywords
  - Rules text
  - Power/Toughness
  - Rarity
  - Set information

### 2. Core Features
- Card search and filtering
- Deck validation (format rules, card limits)
- Mana curve analysis
- Color distribution analysis
- Card synergy detection
- Deck statistics

### 3. Technical Requirements
- Database to store card information
- API integration for card data
- Search functionality
- Rule processing engine
- User interface (CLI or GUI)

## Implementation Phases

### Phase 1: Data Foundation
- [x] Set up project structure
- [ ] Document format rules and constraints
- [ ] Implement data collection from Scryfall API
- [ ] Create local database schema
- [ ] Basic card search functionality

### Phase 2: Core Logic
- [ ] Implement deck building rules
- [ ] Add mana curve analysis
- [ ] Create color requirements calculator
- [ ] Basic synergy detection

### Phase 3: Advanced Features
- [ ] Advanced card recommendations
- [ ] Deck optimization suggestions
- [ ] Format-specific rule handling
- [ ] Export functionality

## Project Structure
- /rules
  - format_rules.md (Format-specific rules)
  - deck_construction.md (Deck building guidelines)
  - banned_restricted.md (Banned/restricted lists)

## Questions to Consider
1. Which format(s) will we support initially? (Standard, Modern, Commander, etc.)
2. Will we focus on competitive or casual deck building?
3. How will we handle card pricing and budget constraints?
4. Should we implement AI-based recommendations? 