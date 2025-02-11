# MTG Crafter System Architecture

## Overview
MTG Crafter is an AI-powered deck building assistant for Magic: The Gathering. It integrates data collection, a robust card database, and advanced mana analysis to generate thematic and synergistic deck suggestions. This document outlines the core components, their dependencies, and guidelines for tracking changes to prevent breaking compatibility.

## Core Components

### 1. Data Collection Layer
- **Script**: `1.gather_data.py`
- **Version**: 2.1.0
- **Responsibilities**:
  - Collect raw card data from the Scryfall API.
  - Manage local caching in the `cache/` directory.
  - Build and update the Card Database.
- **Dependencies**:
  - Scryfall API (v2.0)
  - Python libraries: Requests, TQDM, JSON, SQLite3
  - Data Engine (located in `src/collectors/data_engine.py`)

### 2. Card Database
- **File**: `src/database/card_database.py`
- **Version**: 1.2.1
- **Responsibilities**:
  - Store and manage card data using SQLite
  - Handle low-level database operations
- **Dependencies**:
  - SQLite3, TQDM, JSON, Pathlib

### 3. Card Repository (NEW)
- **File**: `src/database/card_repository.py`
- **Version**: 1.0.0
- **Responsibilities**:
  - Provide unified API for all card data access
  - Abstract database implementation details
  - Centralize query logic and error handling
- **Dependencies**:
  - Card Database component

### 4. Mana Analysis
- **File**: `src/manalysis/analyzer.py`
- **Version**: 0.9.5
- **Responsibilities**:
  - Analyze deck lists for mana distribution, cost reduction, and mana curve metrics.
  - Verify and filter valid cards using the Card Database.
  - Simulate drawing opening hands and calculate color statistics.
  - Check database compatibility by enforcing that the Card Database version is ≥ 1.2 and schema version is ≥ 1.1.
- **Dependencies**:
  - Card Database (must meet the version and schema requirements)
  - Standard Python libraries (Python 3.8+)

### 5. Additional Components
- **Deck Building Layer**:
  - Managed via files like `3.build_deck.py` and a `DeckLoader` class.
  - Integrates analysis results and AI-powered suggestions to build complete decks.
  
- **Collectors & Data Engine** (within `src/collectors/`):
  - Orchestrate data collection across various sources.
  - Maintain cache integrity and track data versioning.

### 6. Data Validation Layer (NEW)
- **Files**: `src/utils/json_validator.py`, `src/utils/data_repair.py`
- **Version**: 1.0.0
- **Responsibilities**:
  - Validate JSON structures against Scryfall schemas
  - Repair corrupted data files
  - Ensure data integrity throughout the pipeline
- **Dependencies**:
  - jsonschema package
  - All data collection components

## Component Interactions

The components interact according to the following logical hierarchy:

- **Data Collection Layer** collects and updates raw card data.
  - This data is then used to build and update the **Card Database**.
- **Card Database** serves as the central repository for card information.
  - **Mana Analysis** uses the Card Database to validate deck lists and calculate mana statistics.
- **Mana Analysis** outputs its findings, which are then fed into the **Deck Building Layer** for final deck suggestions.
- **Collectors** and the **Data Engine** coordinate updates and maintain cache data to ensure all components work with the latest data.

## Version Compatibility Matrix

| Component             | Version   | Dependencies                          | Compatibility Requirements                |
|-----------------------|-----------|---------------------------------------|-------------------------------------------|
| Data Collection       | 2.1.0     | Scryfall API, Requests, TQDM, SQLite3   | N/A                                       |
| Card Database         | 1.2.1     | SQLite3, TQDM, JSON, Pathlib           | Schema Version: 1.1                       |
| Mana Analysis         | 0.9.5     | Card Database (≥1.2, Schema ≥1.1), Python 3.8+ | See `REQUIRED_DB_VERSION` & `COMPATIBLE_DB_SCHEMA` requirements |

## Dependency Tracking & Change Control

- **Centralized Versioning**:  
  Each component defines explicit version constants (e.g., `VERSION_MAJOR`, `VERSION_MINOR`, and `SCHEMA_VERSION` in the Card Database; `REQUIRED_DB_VERSION` and `COMPATIBLE_DB_SCHEMA` in Mana Analysis) to manage breaking changes.

- **Compatibility Checks**:  
  For example, the Mana Analysis component checks at runtime whether the connected Card Database meets the minimum version and schema compatibility requirements.

- **Change Protocol**:
  - **Breaking Changes**: Require updating the relevant version constants and documenting the changes here.
  - **Dependency Updates**: Must be tested across all affected components. Update the compatibility matrix as needed.
  - **Documentation**: This file must be updated with every significant code change affecting cross-component interactions.

## Additional Resources

- [README.md](../README.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [Project Roadmap](roadmap.md)
- [License](../LICENSE)

---

This document is intended to be a living guide to the MTG Crafter system's architecture. Keeping it updated with every significant change helps ensure stability and smooth integration of future features.
