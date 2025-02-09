from dataclasses import dataclass
from typing import List, Dict, Set
import random
from collections import defaultdict
import re
from src.collectors.data_engine import CardDatabase

@dataclass
class GameState:
    """Tracks the current game state during simulation"""
    hand: List[str]
    lands_in_play: List[str]
    mana_rocks_in_play: List[str]
    cards_in_play: Set[str]
    mana_available: Dict[str, int]
    lands_in_hand: List[str]

@dataclass
class CurveHealth:
    """Dataclass for storing curve health information"""
    status: str
    message: str
    distribution: Dict[str, float]

class Manalysis:
    """Class for analyzing mana distribution and running simulations"""
    def __init__(self, decklist: Dict[str, int], card_db: CardDatabase):
        """
        Initialize analyzer with decklist and card database
        
        Args:
            decklist: Dictionary mapping card names to quantities
            card_db: CardDatabase object
        """
        print(f"[DEBUG] Initializing Manalysis with card_db: {card_db}")  # Debug
        self.decklist = decklist
        self.card_db = card_db
        if not self.card_db.is_loaded:
            print(f"[DEBUG] Card database not loaded. Path: {self.card_db.json_file_path}")  # Debug
            print("Card database not found, please run 1.gather_data.py to create it")
            self.card_db = None
        else:
            print("[DEBUG] Card database loaded successfully")  # Debug
        
        self.lands = self._find_lands()
        self.mana_sources = {
            'W': [], 'U': [], 'B': [], 'R': [], 'G': []
        }
        self.commander = None
        self._analyze_mana_sources()
    
    def _find_lands(self) -> List[str]:
        """Find all lands in the decklist"""
        lands = []
        for card_name in self.decklist:
            card = self._get_card_info(card_name)
            if card and card.get('is_land'):
                lands.append(card_name)
        return lands
    
    def _analyze_mana_sources(self):
        """Analyze the decklist to identify all mana sources"""
        for card_name in self.decklist:
            card_info = self._get_card_info(card_name)
            
            # Check if the card is a land using type_line
            is_land = 'land' in card_info.get('type_line', '').lower()  # Check if it's a land
            
            if is_land:
                self.lands.append(card_name)
                # Add land to mana sources
                for color in card_info.get('produces_mana', []):
                    if color in 'WUBRG':
                        self.mana_sources[color].append(card_name)
            # Check for non-land mana sources (rocks, dorks, etc)
            elif card_info.get('produces_mana'):
                for color in card_info.get('produces_mana', []):
                    if color in 'WUBRG':
                        self.mana_sources[color].append(card_name)
    
    def calculate_mana_curve(self) -> Dict:
        """Calculate detailed mana curve statistics"""
        try:
            curve_data = defaultdict(int)
            total_cards = 0
            total_mana = 0
            total_mana_without_lands = 0
            mana_value_values = []
            mana_value_values_without_lands = []
            
            for card_name, quantity in self.decklist.items():
                card = self._get_card_info(card_name)
                if not card:
                    continue
                
                mana_value = card.get('mana_value', 0)
                is_land = card.get('is_land', False)
                
                # Update counts
                if not is_land:  # Exclude lands from curve data
                    curve_data[mana_value] += quantity
                total_cards += quantity
                total_mana += mana_value * quantity
                mana_value_values.extend([mana_value] * quantity)
                
                if not is_land:
                    total_mana_without_lands += mana_value * quantity
                    mana_value_values_without_lands.extend([mana_value] * quantity)
            
            # Calculate averages
            avg_mana_value = total_mana / total_cards if total_cards else 0
            avg_mana_value_without_lands = total_mana_without_lands / len(mana_value_values_without_lands) if mana_value_values_without_lands else 0
            
            # Calculate medians
            mana_value_values.sort()
            mana_value_without_lands_sorted = sorted(mana_value_values_without_lands)
            median_mana_value = mana_value_values[len(mana_value_values)//2] if mana_value_values else 0
            median_mana_value_without_lands = mana_value_without_lands_sorted[len(mana_value_without_lands_sorted)//2] if mana_value_without_lands_sorted else 0
            
            # Calculate distribution percentages
            distribution = {
                mana_value: round(count/total_cards * 100, 1) 
                for mana_value, count in curve_data.items()
            }
            
            # Analyze curve health
            curve_health = self._analyze_curve_health(distribution)
            
            # Create visualization
            max_count = max(curve_data.values()) if curve_data else 0
            visualization = self._visualize_curve(curve_data, max_count)
            
            # Calculate color statistics
            color_stats = self.calculate_color_stats()
            
            # Analyze mana sources
            mana_sources = self.analyze_mana_sources()
            
            # Analyze mana discounts
            mana_discounts = self.analyze_mana_discounts()
            
            return {
                'curve': dict(curve_data),
                'average_mana_value': round(avg_mana_value, 2),
                'average_mana_value_without_lands': round(avg_mana_value_without_lands, 2),
                'median_mana_value': median_mana_value,
                'median_mana_value_without_lands': median_mana_value_without_lands,
                'total_mana_value': total_mana,
                'total_cards': total_cards,
                'distribution': distribution,
                'curve_health': {
                    'status': curve_health.status,
                    'message': curve_health.message,
                    'distribution': curve_health.distribution
                },
                'visualization': visualization,
                'color_stats': color_stats,
                'mana_sources': mana_sources,
                'mana_discounts': mana_discounts
            }
        except Exception as e:
            print(f"Error calculating mana curve: {str(e)}")
            return {'error': str(e)}
    
    def analyze_casting_sequence(self, num_simulations: int = 1000) -> Dict:
        """Simulate gameplay to determine casting probabilities"""
        cast_turns = defaultdict(list)  # Card -> List of turns cast
        card_draws = defaultdict(list)  # Card -> List of turns drawn
        sample_games = []
        
        # Run simulations
        for sim in range(num_simulations):
            game_state = self._setup_game()
            
            # Track initial draws
            for card in game_state.hand:
                card_draws[card].append(0)  # Turn 0 for opening hand
            
            # Simulate first 10 turns
            deck = self._create_library()
            for turn in range(1, 11):
                # Draw step
                if deck:
                    drawn = deck.pop()
                    game_state.hand.append(drawn)
                    card_draws[drawn].append(turn)
                
                # Reset mana pool
                game_state.mana_available.clear()
                self._add_available_mana(game_state)
                
                # Try to play lands and cast spells
                self._simulate_turn(game_state, turn, cast_turns)
        
        # Process results
        results = {
            'earliest_cast': {},
            'average_cast': {},
            'cast_probability': {},
            'problematic_cards': []
        }
        
        for card in self.decklist:
            if cast_turns[card]:
                results['earliest_cast'][card] = min(cast_turns[card])
                results['average_cast'][card] = sum(cast_turns[card]) / len(cast_turns[card])
                results['cast_probability'][card] = len(cast_turns[card]) / num_simulations
            else:
                results['problematic_cards'].append(card)
        
        return results
    
    def _setup_game(self) -> GameState:
        """Initialize a new game state"""
        try:
            deck = self._create_library()
            hand = deck[:7]
            
            lands_in_hand = [
                card for card in hand 
                if self.card_db.get_card(card) and 
                   self.card_db.get_card(card).get('is_land', False)
            ]
            
            return GameState(
                hand=hand,
                lands_in_play=[],
                mana_rocks_in_play=[],
                cards_in_play=set(),
                mana_available=defaultdict(int),
                lands_in_hand=lands_in_hand
            )
        except Exception as e:
            print(f"Error setting up game: {str(e)}")
            # Return empty game state on error
            return GameState([], [], [], set(), defaultdict(int), [])
    
    def _create_library(self) -> List[str]:
        """Create and shuffle a new library"""
        deck = []
        for card, quantity in self.decklist.items():
            deck.extend([card] * quantity)
        random.shuffle(deck)
        return deck
    
    def _add_available_mana(self, state: GameState):
        """Calculate available mana from lands and rocks"""
        try:
            for land in state.lands_in_play:
                card = self.card_db.get_card(land)
                if card:
                    for color in card.get('produces_mana', []):
                        if color in 'WUBRG':
                            state.mana_available[color] += 1
            
            for rock in state.mana_rocks_in_play:
                card = self.card_db.get_card(rock)
                if card:
                    for color in card.get('produces_mana', []):
                        if color in 'WUBRG':
                            state.mana_available[color] += 1
        except Exception as e:
            print(f"Error calculating available mana: {str(e)}")
            # Initialize with empty mana pool on error
            state.mana_available.clear()
    
    def _simulate_turn(self, state: GameState, turn: int, cast_turns: Dict):
        """Simulate a single turn of gameplay"""
        try:
            # Try to play a land
            for card in state.lands_in_hand[:]:
                state.lands_in_play.append(card)
                state.hand.remove(card)
                state.lands_in_hand.remove(card)
                break
            
            # Try to cast spells
            castable = self._get_castable_spells(state)
            for card in castable:
                cast_turns[card].append(turn)
                state.hand.remove(card)
                card_info = self.card_db.get_card(card)
                if card_info and card_info.get('is_mana_rock', False):
                    state.mana_rocks_in_play.append(card)
        except Exception as e:
            print(f"Error simulating turn {turn}: {str(e)}")
    
    def _get_castable_spells(self, state: GameState) -> List[str]:
        """Determine which spells in hand can be cast"""
        castable = []
        for card in state.hand:
            if card not in state.lands_in_hand:
                card_info = self.card_db.get_card(card)
                if self._can_cast(card_info, state.mana_available):
                    castable.append(card)
        return castable
    
    def _get_card_info(self, card_name: str) -> Dict:
        """Get card information from our card database"""
        if self.card_db is None:
            return self._get_fallback_card_info(card_name)
        
        try:
            card = self.card_db.get_card(card_name)
            if card:
                return {
                    "mana_value": card.get('cmc', 0),
                    "is_land": card.get('is_land', False),
                    "type_line": card.get('type_line', ''),
                    "colors": card.get('color_identity', []),
                    "mana_cost": card.get('mana_cost', ''),
                    "produces_mana": card.get('produces_mana', []),
                    "is_mana_rock": 'artifact' in card.get('type_line', '').lower() 
                                   and card.get('produces_mana'),
                    "oracle_text": card.get('oracle_text', '')
                }
            else:
                print(f"Warning: Card not found in database: {card_name}")
                return self._get_fallback_card_info(card_name)
        
        except Exception as e:
            print(f"Error getting card info for {card_name}: {str(e)}")
            return self._get_fallback_card_info(card_name)

    def _get_fallback_card_info(self, card_name: str) -> Dict:
        """Fallback method to provide basic card info if DB lookup fails"""
        # This is a placeholder; replace with actual fallback logic if needed
        return {
            "mana_value": 0,
            "is_land": False,
            "colors": [],
            "mana_cost": '',
            "produces_mana": [],
            "is_mana_rock": False,
            "oracle_text": ''
        }
    
    def _visualize_curve(self, curve_data: Dict[int, int], max_count: int) -> str:
        """Create a simple text-based visualization of the mana curve"""
        visualization = ""
        for mana_value in sorted(curve_data.keys()):
            count = curve_data[mana_value]
            bar = "#" * int(30 * (count / max_count)) if max_count > 0 else ""
            visualization += f"{mana_value}: {bar} {count}\n"
        return visualization
    
    def simulate_opening_hand(self, num_simulations: int = 1000) -> Dict:
        """
        Simulate drawing opening hands and analyze mana distribution
        
        Args:
            num_simulations: Number of hands to simulate
        
        Returns:
            Dictionary containing:
            - lands_distribution: How many hands had X lands
            - color_distribution: Color presence in opening hands
            - no_land_percentage: Percentage of hands with no lands
            - average_lands: Average number of lands in hand
            - visualization: ASCII visualization of land distribution
        """
        HAND_SIZE = 7
        lands_count = defaultdict(int)
        color_count = defaultdict(int)
        total_no_lands = 0
        
        # Convert decklist to list of cards (with duplicates)
        deck = []
        for card_name, quantity in self.decklist.items():
            deck.extend([card_name] * quantity)
        
        for _ in range(num_simulations):
            # Draw a hand
            hand = random.sample(deck, HAND_SIZE)
            
            # Count lands and colors in this hand
            lands_in_hand = 0
            colors_in_hand = set()
            
            for card in hand:
                card_info = self._get_card_info(card)
                
                if card_info.get('is_land', False):
                    lands_in_hand += 1
                    # TODO: Add produced colors to colors_in_hand
                    
                # TODO: Add required colors to colors_in_hand from non-land cards
            
            lands_count[lands_in_hand] += 1
            if lands_in_hand == 0:
                total_no_lands += 1
            
            for color in colors_in_hand:
                color_count[color] += 1
        
        # Calculate statistics
        total_lands = sum(1 for card in deck if self._get_card_info(card).get('is_land', False))
        avg_lands = sum(count * num for num, count in lands_count.items()) / num_simulations
        
        results = {
            'lands_distribution': dict(sorted(lands_count.items())),
            'color_distribution': {
                color: count / num_simulations * 100 
                for color, count in color_count.items()
            },
            'no_land_percentage': (total_no_lands / num_simulations) * 100,
            'average_lands': avg_lands,
            'total_lands_in_deck': total_lands,
            'land_percentage': (total_lands / len(deck)) * 100
        }
        
        # Add visualization
        max_count = max(lands_count.values())
        results['visualization'] = self._visualize_land_distribution(lands_count, max_count)
        
        return results
    
    def _visualize_land_distribution(self, dist: Dict[int, int], max_count: int) -> str:
        """Create ASCII visualization of land distribution in opening hands"""
        height = 10  # Height of the graph
        visualization = ["\nLands distribution in opening hands:"]
        
        # Create the bars
        for lands in range(8):  # 0-7 lands
            count = dist.get(lands, 0)
            percentage = (count / max_count) * height if max_count > 0 else 0
            bar = f"\n{lands}│ {'█' * int(percentage)}{' ' * (height - int(percentage))} {count:3d} ({count/sum(dist.values())*100:4.1f}%)"
            visualization.append(bar)
        
        # Add bottom border
        visualization.append("\n ╰" + "─" * (height + 15))
        
        return "".join(visualization)
    
    def probability_of_casting(self, card_name: str, turn: int) -> float:
        """
        Calculate the probability of being able to cast a specific card by turn X
        """
        # TODO: Implement probability calculation
        return 0.0

    def analyze_mana_sources(self):
        """Analyze mana sources in the deck, including rocks and dorks"""
        mana_sources = {
            'total_sources': 0,
            'breakdown': {
                'by_color': {
                    'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'C': 0
                }
            },
            'mana_rocks': [],
            'mana_dorks': []
        }
        
        for card_name, quantity in self.decklist.items():
            card = self._get_card_info(card_name)
            if not card:
                continue
            
            produces_mana = card.get('produces_mana', [])
            
            # Check for mana rocks
            if card.get('is_mana_rock'):
                mana_sources['mana_rocks'].extend([card_name] * quantity)
            
            # Check for mana dorks (creatures that produce mana)
            if 'creature' in card.get('type_line', '').lower() and produces_mana:
                mana_sources['mana_dorks'].extend([card_name] * quantity)
            
            for color in produces_mana:
                if color in mana_sources['breakdown']['by_color']:
                    mana_sources['breakdown']['by_color'][color] += quantity
                    mana_sources['total_sources'] += quantity
        
        return mana_sources

    def analyze_mana_discounts(self) -> Dict:
        """Analyze mana discounts in the deck"""
        discounts = {}
        
        for card_name in self.decklist:
            card = self._get_card_info(card_name)
            if not card:
                continue
            
            text = card.get('oracle_text', '')
            mana_value = card.get('mana_value', 0)
            
            # Check for Avatar of Woe-like abilities
            condition = "If there are ten or more creature cards total in all graveyards, this spell costs {6} less to cast."
            if condition in text:
                reduced_mana_value = 2  # Example: Avatar of Woe
                discounts[card_name] = {
                    'original_mana_value': mana_value,
                    'reduced_mana_value': reduced_mana_value,
                    'condition': "Ten or more creature cards in all graveyards"
                }
                print(f"Card: {card_name}, Discount: {reduced_mana_value} (Condition: {condition})")
        
        return discounts

    def analyze_color_balance(self):
        """Analyze color distribution of the deck"""
        color_counts = defaultdict(int)
        
        for card_name, quantity in self.decklist.items():
            try:
                card = self.card_db.get_card(card_name)
                if not card:
                    continue
                
                colors = card.get('color_identity', [])
                for color in colors:
                    color_counts[color] += quantity
            except Exception as e:
                print(f"Error processing {card_name}: {str(e)}")
                continue
            
        return dict(color_counts)

    def analyze_lands(self):
        """Analyze the lands in the deck."""
        lands = []
        total_lands = 0
        
        for card_name, quantity in self.decklist.items():
            card_info = self._get_card_info(card_name)
            if card_info.get('is_land', False):
                lands.extend([card_name] * quantity)
                total_lands += quantity
        
        # Create land summary
        summary = ["Land Summary", "-" * 40]
        summary.append(f"Total lands found: {total_lands}")
        summary.append(f"Total non-land cards: {sum(self.decklist.values()) - total_lands}")
        summary.append("")
        
        # Mana sources analysis
        mana_sources = self.analyze_mana_sources()
        summary.append("Mana Sources:")
        summary.append(f"Total mana sources: {mana_sources['total_sources']}")
        summary.append(f"- Lands: {mana_sources['breakdown']['lands']}")
        
        return "\n".join(summary)

    def get_total_reduction(self) -> Dict:
        """Get the total potential mana reduction in the deck"""
        discounts = self.analyze_mana_discounts()
        return {
            'total': discounts['total_reduction']['total'],
            'fixed': discounts['total_reduction']['fixed'],
            'optimal_scaling': discounts['total_reduction']['optimal_scaling']
        }

    def _can_cast(self, card_info: Dict, available_mana: Dict[str, int]) -> bool:
        """Check if a card can be cast with available mana"""
        try:
            if not card_info or 'mana_cost' not in card_info:
                return False
            
            mana_cost = card_info['mana_cost']
            if not mana_cost:
                return True  # Free spell
            
            # Parse mana cost string (e.g., "{2}{W}{U}")
            cost_parts = re.findall(r'{([^}]+)}', mana_cost)
            required_mana = defaultdict(int)
            generic_cost = 0
            
            for part in cost_parts:
                if part.isdigit():
                    generic_cost += int(part)
                else:
                    required_mana[part] += 1
            
            # Make a copy of available_mana to not modify the original
            available = available_mana.copy()
            
            # Check colored mana requirements
            for color, amount in required_mana.items():
                if available.get(color, 0) < amount:
                    return False
                available[color] -= amount
            
            # Check if we have enough mana for generic cost
            total_remaining = sum(available.values())
            return total_remaining >= generic_cost
        except Exception as e:
            print(f"Error checking if card can be cast: {str(e)}")
            return False

    def display_color_distribution(self, color_data: Dict):
        """Display color distribution with error handling"""
        if not color_data:
            print("\nNo color data available - check database connection")
            return
        
        try:
            print("\nColor Distribution:")
            print("-" * 40)
            total = sum(color_data.values())
            
            if total == 0:
                print("No colored cards found in deck")
                return
            
            for color, count in sorted(color_data.items()):
                percentage = (count / total) * 100
                print(f"{color}: {count} ({percentage:.1f}%)")
            
        except Exception as e:
            print(f"\nError displaying color distribution: {str(e)}")

    def _analyze_curve_health(self, distribution: Dict[int, float]) -> CurveHealth:
        """Analyze the mana curve distribution and provide feedback"""
        early_game = sum(distribution.get(mv, 0) for mv in range(3))
        mid_game = sum(distribution.get(mv, 0) for mv in range(3, 6))
        late_game = sum(distribution.get(mv, 0) for mv in range(6, 20))
        
        total = early_game + mid_game + late_game
        
        early_game = (early_game / total) * 100 if total > 0 else 0
        mid_game = (mid_game / total) * 100 if total > 0 else 0
        late_game = (late_game / total) * 100 if total > 0 else 0
        
        distribution = {
            'early_game': early_game,
            'mid_game': mid_game,
            'late_game': late_game
        }
        
        if early_game >= 30:
            status = "Healthy"
            message = "This deck has a good early game presence"
        elif early_game >= 20:
            status = "Moderate"
            message = "This deck could use more early game presence"
        else:
            status = "Poor"
            message = "This deck needs more early game presence"
            
        return CurveHealth(status=status, message=message, distribution=distribution)

    def calculate_color_stats(self) -> Dict:
        """Calculate detailed color statistics for the deck"""
        color_counts = {
            'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'C': 0
        }
        
        land_count = 0
        non_land_count = 0
        
        land_produces = {
            'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'C': 0
        }
        
        land_mana_symbols = {
            'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'C': 0
        }
        
        non_land_cards = {
            'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'C': 0
        }
        
        non_land_mana_symbols = {
            'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'C': 0
        }
        
        for card_name, quantity in self.decklist.items():
            card = self._get_card_info(card_name)
            if not card:
                continue
            
            is_land = card.get('is_land', False)
            
            if is_land:
                land_count += quantity
                produces_mana = card.get('produces_mana', [])
                
                for color in produces_mana:
                    land_produces[color] += quantity
                    
                    # Count mana symbols on lands
                    mana_cost = card.get('mana_cost', '')
                    if mana_cost:
                        for symbol in mana_cost:
                            if symbol in color_counts:
                                land_mana_symbols[symbol] += quantity
            else:
                non_land_count += quantity
                colors = card.get('colors', [])
                
                print(f"Card: {card_name}, Colors: {colors}")  # Debugging
                
                for color in colors:
                    non_land_cards[color] += quantity
                    
                # Count mana symbols on non-land cards
                mana_cost = card.get('mana_cost', '')
                if mana_cost:
                    for symbol in mana_cost:
                        if symbol in color_counts:
                            non_land_mana_symbols[symbol] += quantity
        
        return {
            'land_count': land_count,
            'non_land_count': non_land_count,
            'land_produces': land_produces,
            'land_mana_symbols': land_mana_symbols,
            'non_land_cards': non_land_cards,
            'non_land_mana_symbols': non_land_mana_symbols
        }
