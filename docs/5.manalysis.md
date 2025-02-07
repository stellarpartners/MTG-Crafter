Upon launch, the tool will:

- Check for the Card Database.
- Display a main menu with options to load a deck from the clipboard or exit.
- Issue an error message if the Card Database is missing, with instructions to run `1.gather_data.py` beforehand.

## How It Works

### 1. Deck Loading

- **Source:**  
  Manalysis reads the deck list from the clipboard using the `DeckLoader` component.
  
- **Expected Format:**  
  Each line should contain the card quantity and name, for example:  
  ```
  1x Card Name
  4x Other Card
  ```
  
- **Output:**  
  Once loaded, the total card count is displayed along with details for each card.

### 2. Interactive Menu Options

Once a deck is loaded, the following analysis options are available:

- **Mana Curve Analysis:**  
  Displays statistics such as the average and median mana values, both before and after applying any detected cost reductions. It also shows a visual breakdown (a bar chart) of the card distribution by mana value.

- **Opening Hand Simulation:**  
  Simulates drawing multiple opening hands (default is 1000 simulations) and presents statistics including:
  - Total lands drawn.
  - Land percentage.
  - Average lands per hand.
  - Chance of drawing no lands.
  - Color distribution among the opening hands.

- **Casting Probabilities:**  
  Allows you to select a specific card from your deck and calculate the probability of being able to cast it by a chosen turn.

- **Full Deck Statistics:**  
  Provides overall deck details such as:
  - Total card count.
  - Commander details (if applicable).
  - Additional insights (customizable by implementation).

- **Return to Main Menu:**  
  Leaves the analysis menu and returns to the primary deck loading and exit options.

### 3. Cost Reduction (Discount) Analysis

- **Detection:**  
  Manalysis scans the oracle text of cards for cost reduction patterns (fixed, optimal scaling, scaling, and conditional).  
- **Computation:**  
  It calculates the potential mana cost reductions and adjusts the deck's mana curve accordingly.
- **Display:**  
  Results include a detailed breakdown by card, including:
  - The original and potential mana cost.
  - The reduction type.
  - The effective discount amount.
- **Note:**  
  Variable and conditional reductions are noted separately and are not included in some calculations.

### 4. Color Balance Analysis

- **Purpose:**  
  To determine if your deck's mana production (lands and other mana sources) matches the color requirements of your spells.
- **Process:**  
  It counts:
  - The number of non-land cards per color.
  - Mana symbols present in cards' costs.
  - The corresponding production (lands) for each color.
- **Recommendations:**  
  Based on detected discrepancies, the tool issues suggestions, such as:
  - "Need more [color] sources" if the land ratio is too low.
  - "Could reduce [color] sources" if there is an excess.
  
## Extending Manalysis

Developers interested in extending Manalysis can consider:
- Adding new cost reduction detection rules in the analyzer.
- Incorporating additional simulation parameters.
- Refining color balance metrics based on user feedback.

## Troubleshooting

- **Missing Card Database:**  
  If you run into the error "Card database not found," please run `1.gather_data.py` to create the database.
  
- **Invalid Deck Format:**  
  Ensure the deck list you copy follows the expected pattern (e.g., "1x Card Name").

## Additional Resources

- [Contributing Guidelines](../CONTRIBUTING.md)
- [License](../LICENSE)
- [Project Roadmap](roadmap.md)

---

For further questions or to contribute improvements to Manalysis, please consult the project repository or contact the development team.
