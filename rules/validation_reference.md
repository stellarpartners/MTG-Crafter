# Deck Validation Reference

## Core Rules References

### Deck Construction (Rule 100.2)
- Constructed minimum: 60 cards
- Commander exactly: 100 cards
- Maximum 4 copies rule (except basic lands)
- Sideboard: exactly 15 cards (where allowed)

### Color Identity (Rules 105 and 903.4)
Color identity includes:
1. Mana symbols in mana cost
2. Colored mana symbols in rules text
3. Color indicators
4. Colors from characteristic-defining abilities
5. Basic land types implicitly add their mana symbols

### Zone Rules (Section 4)
Relevant zones for deck validation:
- Library (401) - The deck itself
- Command (408) - For commander
- Sideboard (100.4)

### Card Types (Section 3)
For commander validation:
- Legendary (205.4d)
- Creature (302)
- Planeswalker (306)

## Validation Checklist

### Pre-Game Validation
1. Deck Size
   - Count total cards
   - Verify against format minimum/maximum
   - Include commander for Commander format
   - Verify sideboard size if present

2. Card Legality
   - Check each card against format's legal sets
   - Verify against banned/restricted list
   - For Commander:
     - Verify commander is legendary creature/planeswalker
     - Check if commander has "can be your commander" ability

3. Card Quantity
   - Count copies of each card
   - Maximum 4 copies (except basic lands)
   - For Commander: maximum 1 copy
   - Basic land exception applies to:
     - Plains
     - Island
     - Swamp
     - Mountain
     - Forest
     - Wastes (colorless basic land)

4. Color Requirements
   For Commander:
   - Calculate commander's color identity
   - Check each card's color identity
   - Verify all cards' color identity is subset of commander's

## Implementation Notes

### Color Identity Calculation
1. Start with card's mana cost
2. Add colors from:
   - Rules text mana symbols
   - Color indicators
   - Characteristic-defining abilities
3. For lands, include mana symbols of basic land types
4. Hybrid/Phyrexian mana counts as both colors
5. Reminder text is ignored

### Card Legality Verification
1. Check card's printing date/set
2. Compare against format cutoff
3. Check current banned/restricted list
4. For Commander, check both:
   - General banlist
   - Commander-specific banlist

### Special Cases
- Split cards: Consider both halves
- Double-faced cards: Consider both faces
- Adventure cards: Consider both parts
- Hybrid mana: Consider both colors
- Phyrexian mana: Consider the color 