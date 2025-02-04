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
│   ├── rules/             # Downloaded rules
│   └── banlists/         # Raw banlist data
│
├── data/                   # Processed data
│   ├── database/          # Core card database
│   ├── themes/            # Processed themes
│   ├── keywords/          # Processed keywords
│   └── banlists/         # Processed banlist data
```

## Usage

Run the engine with:
```