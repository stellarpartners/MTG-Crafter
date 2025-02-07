from dataclasses import dataclass
from typing import List, Dict
import random
from collections import defaultdict
import re

@dataclass
class Manalysis:
    """Class for analyzing mana distribution and running simulations"""
    decklist: Dict[str, int]  # Card name to quantity mapping
    lands: List[str]  # List of land cards
    mana_sources: Dict[str, List[str]]  # Mapping of mana colors to source cards
    card_db: any  # Card database reference
    commander: str = None
    
    def __init__(self, decklist: Dict[str, int], card_db):
        """
        Initialize analyzer with decklist and card database
        
        Args:
            decklist: Dictionary mapping card names to quantities
            card_db: Database containing card information
        """
        self.decklist = decklist
        self.card_db = card_db
        self.lands = []
        self.mana_sources = {
            'W': [], 'U': [], 'B': [], 'R': [], 'G': []
        }
        self._analyze_mana_sources()
    
    def _analyze_mana_sources(self):
        """Analyze the decklist to identify all mana sources"""
        for card_name in self.decklist:
            card_info = self._get_card_info(card_name)
            if card_info.get('is_land', False):
                self.lands.append(card_name)
            # TODO: Add mana source analysis
    
    def calculate_mana_curve(self) -> Dict:
        """Analyze the mana curve of the deck"""
        curve_original = defaultdict(int)
        curve_reduced = defaultdict(int)
        total_spells = 0
        total_mv_original = 0
        total_mv_reduced = 0
        total_cards = sum(self.decklist.values())
        
        # Statistics tracking
        all_values_original = {'with_lands': [], 'without_lands': []}
        all_values_reduced = {'with_lands': [], 'without_lands': []}
        
        # Get cost reduction data first
        cost_reductions = self.analyze_mana_discounts()
        reduction_map = {
            card['card_name']: {
                'amount': card['discount_amount'],
                'type': card['discount_type']
            }
            for card in cost_reductions['cards']
        }
        
        # Single pass through the deck
        for card_name, quantity in self.decklist.items():
            card_info = self._get_card_info(card_name)
            mv = card_info.get('mana_value', 0)
            mv_reduced = mv
            
            # Apply reductions if applicable
            if card_name in reduction_map:
                reduction = reduction_map[card_name]
                if reduction['type'] in ['fixed', 'optimal scaling']:
                    mv_reduced = max(0, mv - reduction['amount'])
            
            # Track values
            total_mv_original += mv * quantity
            total_mv_reduced += mv_reduced * quantity
            
            # Update curves and counts for non-lands
            if not card_info.get('is_land', False):
                curve_original[mv] += quantity
                curve_reduced[mv_reduced] += quantity
                total_spells += quantity
                
                # Add to statistics lists
                all_values_original['without_lands'].extend([mv] * quantity)
                all_values_reduced['without_lands'].extend([mv_reduced] * quantity)
                all_values_original['with_lands'].extend([mv] * quantity)
                all_values_reduced['with_lands'].extend([mv_reduced] * quantity)
            else:
                # Add lands to with_lands statistics
                all_values_original['with_lands'].extend([mv] * quantity)
                all_values_reduced['with_lands'].extend([mv_reduced] * quantity)
        
        def calc_stats(values):
            if not values:
                return {'average': 0, 'median': 0}
            return {
                'average': sum(values) / len(values),
                'median': sorted(values)[len(values) // 2]
            }
        
        nested_result = {
            'original': {
                'curve': dict(sorted(curve_original.items())),
                'total_mv': total_mv_original,
                'stats_with_lands': calc_stats(all_values_original['with_lands']),
                'stats_without_lands': calc_stats(all_values_original['without_lands'])
            },
            'reduced': {
                'curve': dict(sorted(curve_reduced.items())),
                'total_mv': total_mv_reduced,
                'stats_with_lands': calc_stats(all_values_reduced['with_lands']),
                'stats_without_lands': calc_stats(all_values_reduced['without_lands'])
            },
            'total_spells': total_spells,
            'total_cards': total_cards,
            'cost_reduction': cost_reductions['total_reduction']
        }
        
        # Add curve visualizations for both
        max_count = max(max(curve_original.values() or [0]), max(curve_reduced.values() or [0]))
        if max_count > 0:
            nested_result['original']['visualization'] = self._visualize_curve(curve_original, max_count)
            nested_result['reduced']['visualization'] = self._visualize_curve(curve_reduced, max_count)
        
        # For backward compatibility, return the original values in the old format
        result = {
            'curve': nested_result['original']['curve'],
            'total_mv': nested_result['original']['total_mv'],
            'total_spells': total_spells,
            'total_cards': total_cards,
            'stats_with_lands': nested_result['original']['stats_with_lands'],
            'stats_without_lands': nested_result['original']['stats_without_lands'],
            'visualization': nested_result['original']['visualization'] if max_count > 0 else None,
            # Add missing fields for backward compatibility
            'average_mv': nested_result['original']['stats_without_lands']['average'],
            'median_mv': nested_result['original']['stats_without_lands']['median'],
            # Add the nested data for new code that wants to use it
            'detailed': nested_result
        }
        
        return result
    
    def _get_card_info(self, card_name: str) -> Dict:
        """
        Get card information from our card database
        """
        if self.card_db is None:
            # If no database provided, use fallback data
            return self._get_fallback_card_info(card_name)
        
        try:
            # Get card from our database using SQL query
            card = self.card_db.get_card(card_name)
            if card:
                return {
                    "mana_value": card['cmc'],
                    "is_land": card['is_land'],
                    "colors": card['color_identity'].split(',') if card['color_identity'] else [],
                    "mana_cost": card['mana_cost']
                }
            else:
                print(f"Warning: Card not found in database: {card_name}")
                return self._get_fallback_card_info(card_name)
            
        except Exception as e:
            print(f"Error getting card info for {card_name}: {str(e)}")
            return self._get_fallback_card_info(card_name)

    def _get_fallback_card_info(self, card_name: str) -> Dict:
        """Fallback method when card is not found in database"""
        # Try to guess if it's a land based on name
        is_likely_land = any(land_type in card_name.lower() 
                            for land_type in ['plains', 'island', 'swamp', 'mountain', 'forest', 'land'])
        
        return {
            "mana_value": 0 if is_likely_land else -1,
            "is_land": is_likely_land,
            "colors": [],
            "mana_cost": None
        }
    
    def _visualize_curve(self, curve: Dict[int, int], max_count: int) -> str:
        """Create ASCII visualization of the mana curve"""
        height = 10  # Height of the graph
        visualization = []
        
        # Find the maximum mana value to show
        max_mv = max(curve.keys()) if curve else 0
        
        # Create the bars
        for mv in range(max_mv + 1):
            count = curve.get(mv, 0)
            bar_height = int((count / max_count) * height) if max_count > 0 else 0
            bar = f"\n{mv:2d}│ {'█' * bar_height}{' ' * (height - bar_height)} {count:2d}"
            visualization.append(bar)
        
        # Add bottom border
        visualization.append("\n  ╰" + "─" * (height + 3))
        
        return "".join(visualization)
    
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

    def analyze_mana_sources(self) -> Dict:
        """Analyze all mana sources in the deck"""
        lands = []
        mana_dorks = []
        artifacts = []
        other_sources = []
        
        # Track unique cards for type counting
        unique_lands = set()
        unique_dorks = set()
        unique_artifacts = set()
        unique_other = set()
        
        mana_keywords = [
            "add {", "add one", "add two", "add three",
            "add any", "add that", "add mana"
        ]
        
        for card_name, quantity in self.decklist.items():
            card = self.card_db.get_card(card_name)
            if not card:
                print(f"Debug: Card not found - {card_name}")
                continue
            
            is_mana_source = False
            oracle_text = card['oracle_text'].lower() if card['oracle_text'] else ''
            is_land = 'land' in card['type_line'].lower()
            is_creature = 'creature' in card['type_line'].lower()
            
            # Check if card can produce mana
            produces_mana = card['produces_mana'].split(',') if card['produces_mana'] else []
            if produces_mana or any(keyword in oracle_text.lower() for keyword in mana_keywords):
                is_mana_source = True
            
            if is_land:  # Count all lands, whether they produce mana or not
                lands.extend([card_name] * quantity)
                unique_lands.add(card_name)
                
            if is_mana_source:
                if is_land and is_creature:  # Handle Dryad Arbor case
                    mana_dorks.extend([card_name] * quantity)
                    unique_dorks.add(card_name)
                elif is_creature:
                    mana_dorks.extend([card_name] * quantity)
                    unique_dorks.add(card_name)
                elif 'artifact' in card['type_line'].lower():
                    artifacts.extend([card_name] * quantity)
                    unique_artifacts.add(card_name)
                elif not is_land:  # Only add to other if not already counted as land
                    other_sources.extend([card_name] * quantity)
                    unique_other.add(card_name)
        
        return {
            'lands': lands,
            'mana_dorks': mana_dorks,
            'artifacts': artifacts,
            'other_sources': other_sources,
            'total_sources': len(set(lands + mana_dorks + artifacts + other_sources)),
            'breakdown': {
                'lands': len(lands),  # Use total count including duplicates
                'mana_dorks': len(mana_dorks),
                'artifacts': len(artifacts),
                'other': len(other_sources)
            }
        }

    def analyze_mana_discounts(self) -> Dict:
        """Analyze cards with mana cost reduction abilities"""
        discounts = []
        seen_cards = set()
        
        discount_patterns = [
            # Match scaling patterns first
            (r"costs? \{?(\d+)\}? less .* for each", "scaling"),  # Match "for each" pattern first
            (r"for each .*costs? \{?(\d+)\}? less", "scaling"),   # Alternative order
            # Then fixed patterns
            (r"costs? \{?(\d+)\}? less to cast", "fixed"),
            (r"costs? (\d+) less to cast", "fixed"),
            (r"costs? \{?(\d+)\}? less", "fixed"),
            # Other patterns
            (r"if .* costs? (\d+) less", "conditional"),
            (r"reduces? the cost .* by \{?(\d+)\}?", "fixed"),
        ]
        
        def parse_mana_cost(cost: str) -> tuple:
            """Parse mana cost into (generic, colored) components"""
            if not cost:
                return (0, "")
            generic = 0
            colored = ""
            parts = cost.strip("{}").split("}{")
            for part in parts:
                if part.isdigit():
                    generic = int(part)
                elif part in 'WUBRG':
                    colored += part
            return (generic, colored)
        
        def format_mana_cost(generic: int, colored: str) -> str:
            """Format mana cost components into string"""
            if generic > 0:
                return f"{generic}+{''.join(colored)}"
            return ''.join(colored)
        
        for card_name, quantity in self.decklist.items():
            if card_name in seen_cards:
                continue
            
            card = self.card_db.get_card(card_name)
            if not card or not card['oracle_text']:
                continue
            
            seen_cards.add(card_name)
            oracle_text = card['oracle_text'].lower()
            mana_cost = card['mana_cost'] if card['mana_cost'] else ''
            generic, colored = parse_mana_cost(mana_cost)
            
            # Look for cost reduction patterns
            for pattern, discount_type in discount_patterns:
                matches = re.finditer(pattern, oracle_text)
                for match in matches:
                    try:
                        amount = int(match.group(1))
                        start_idx = max(0, oracle_text.rfind('.', 0, match.start()) + 1)
                        end_idx = oracle_text.find('.', match.end())
                        if end_idx == -1:
                            end_idx = len(oracle_text)
                        context = oracle_text[start_idx:end_idx].strip()
                        
                        # Skip self-referential cost reductions
                        if "creature spells" in context and 'creature' in card['type_line'].lower():
                            continue
                        
                        # Handle different reduction types
                        if discount_type == "scaling":
                            if "creature card in your graveyard" in context:
                                actual_reduction = generic  # For optimal scaling, we reduce all generic mana
                                potential_cost = format_mana_cost(0, colored)
                                discount_type = "optimal scaling"
                                amount = actual_reduction
                            else:
                                potential_cost = "Variable"
                        else:
                            # For fixed reductions, calculate both the reduced cost and the reduction amount
                            potential_generic = max(0, generic - amount)
                            potential_cost = format_mana_cost(potential_generic, colored)
                        
                        discounts.append({
                            'card_name': card_name,
                            'quantity': quantity,
                            'original_cost': format_mana_cost(generic, colored),
                            'potential_cost': potential_cost,
                            'discount_type': discount_type,
                            'discount_amount': amount,
                            'condition': context
                        })
                    except (ValueError, IndexError):
                        continue
        
        # Process cards once and calculate everything
        card_categories = {
            'fixed': set(),
            'scaling': set(),
            'optimal_scaling': set(),
            'conditional': set()
        }
        
        total_reductions = {
            'fixed': 0,
            'optimal_scaling': 0
        }
        
        # Track processed cards to avoid counting duplicates
        processed_cards = set()
        
        # Single pass through discounts to categorize and total
        for card in discounts:
            card_name = card['card_name']
            if card_name in processed_cards:
                continue
            processed_cards.add(card_name)
            
            discount_type = card['discount_type']
            quantity = card['quantity']
            amount = card['discount_amount']
            
            # Categorize the card
            if discount_type == 'fixed':
                card_categories['fixed'].add(card_name)
                total_reductions['fixed'] += amount * quantity
            elif discount_type == 'optimal scaling':
                card_categories['optimal_scaling'].add(card_name)
                total_reductions['optimal_scaling'] += min(amount, 
                    self._get_card_info(card_name).get('mana_value', 0)) * quantity
            elif discount_type == 'scaling':
                card_categories['scaling'].add(card_name)
            else:  # conditional
                card_categories['conditional'].add(card_name)
        
        # Calculate the total reduction
        total = total_reductions['fixed'] + total_reductions['optimal_scaling']
        
        return {
            'cards': discounts,
            'total_cards': len(set(card['card_name'] for card in discounts)),
            'total_reduction': {
                'fixed': total_reductions['fixed'],
                'optimal_scaling': total_reductions['optimal_scaling'],
                'total': total
            },
            'types': {
                'fixed': len(card_categories['fixed']),
                'scaling': len(card_categories['scaling'] | card_categories['optimal_scaling']),
                'conditional': len(card_categories['conditional'])
            }
        }

    def analyze_color_balance(self) -> Dict:
        """Analyze color requirements vs production"""
        # Track card colors and mana symbols
        card_colors = defaultdict(int)
        symbols_in_costs = defaultdict(int)
        total_nonland_cards = 0
        total_symbols = 0
        
        # Track mana production
        land_symbols = defaultdict(int)
        total_land_symbols = 0
        land_producers = defaultdict(int)
        total_lands = 0
        
        # Analyze cards and costs
        for card_name, quantity in self.decklist.items():
            card = self.card_db.get_card(card_name)
            if not card:
                continue
            
            is_land = 'land' in card['type_line'].lower()
            is_creature = 'creature' in card['type_line'].lower()
            
            # Count non-land cards (including dual-type cards like Dryad Arbor)
            if not is_land or is_creature:
                total_nonland_cards += quantity
                # Count cards of each color (from color identity)
                colors = card['color_identity'].split(',') if card['color_identity'] else []
                for color in colors:
                    if color in 'WUBRG':
                        card_colors[color] += quantity
                
                # Count mana symbols in costs
                if card['mana_cost']:
                    for symbol in 'WUBRG':
                        count = card['mana_cost'].count(f"{{{symbol}}}")
                        symbols_in_costs[symbol] += count * quantity
                        total_symbols += count * quantity
            
            # Count lands (including dual-type cards)
            if is_land:
                total_lands += quantity
                # Count lands that produce each color
                produces = card['produces_mana'].split(',') if card['produces_mana'] else []
                for color in produces:
                    if color in 'WUBRG':
                        land_producers[color] += quantity
                        land_symbols[color] += quantity
                        total_land_symbols += quantity
        
        return {
            'card_colors': {
                color: {
                    'count': count,
                    'percentage': (count / total_nonland_cards * 100) if total_nonland_cards > 0 else 0
                }
                for color, count in card_colors.items()
            },
            'mana_symbols': {
                color: {
                    'count': count,
                    'percentage': (count / total_symbols * 100) if total_symbols > 0 else 0
                }
                for color, count in symbols_in_costs.items()
            },
            'land_production': {
                color: {
                    'count': count,
                    'percentage': (count / total_lands * 100) if total_lands > 0 else 0,
                    'symbol_percentage': (land_symbols[color] / total_land_symbols * 100) if total_land_symbols > 0 else 0
                }
                for color, count in land_producers.items()
            },
            'totals': {
                'nonland_cards': total_nonland_cards,
                'lands': total_lands,
                'mana_symbols': total_symbols,
                'land_symbols': total_land_symbols
            }
        }

    def _generate_color_recommendations(self, requirements: Dict, production: Dict) -> List[str]:
        """Generate recommendations based on color analysis"""
        recommendations = []
        
        # Calculate total production per color
        total_production = defaultdict(int)
        for source in production.values():
            for color, count in source.items():
                total_production[color] += count
        
        # Analyze each color
        for color in 'WUBRG':
            req_percent = requirements.get(color, 0)
            prod_percent = total_production.get(color, 0)
            
            if req_percent > 0:
                if prod_percent < req_percent * 0.8:
                    recommendations.append(
                        f"⚠️ Insufficient {color} production ({prod_percent:.1f}%) "
                        f"for requirements ({req_percent:.1f}%)"
                    )
                elif prod_percent > req_percent * 1.5:
                    recommendations.append(
                        f"ℹ️ Excess {color} production ({prod_percent:.1f}%) "
                        f"for requirements ({req_percent:.1f}%)"
                    )
            elif prod_percent > 5:
                recommendations.append(
                    f"⚠️ Unnecessary {color} production ({prod_percent:.1f}%) "
                    f"with no requirements"
                )
        
        return recommendations

    def _diagnose_color_balance(self, symbols_required: Dict, land_production: Dict) -> Dict:
        """Analyze overall health of the mana base"""
        total_symbols = sum(symbols_required.values())
        total_production = sum(land_production.values())
        
        if not total_symbols:
            return {
                'status': 'UNKNOWN',
                'message': 'No colored mana requirements found in deck'
            }
        
        # Calculate color intensity
        colors_used = [c for c, count in symbols_required.items() if count > 0]
        color_requirements = {
            color: count / total_symbols * 100 
            for color, count in symbols_required.items()
            if count > 0
        }
        
        # Check if production matches requirements
        mismatches = []
        for color, req_percent in color_requirements.items():
            prod_percent = (land_production.get(color, 0) / total_production * 100) if total_production else 0
            ratio = prod_percent / req_percent if req_percent > 0 else 0
            
            if ratio < 0.8:
                mismatches.append(f"{color} (needs {req_percent:.1f}%, has {prod_percent:.1f}%)")
        
        # Evaluate overall balance
        if not mismatches:
            if len(colors_used) == 1:
                return {
                    'status': 'EXCELLENT',
                    'message': f'Mono-{colors_used[0]} deck with appropriate mana base'
                }
            else:
                return {
                    'status': 'GOOD',
                    'message': f'Well-balanced {len(colors_used)}-color mana base'
                }
        elif len(mismatches) == 1:
            return {
                'status': 'FAIR',
                'message': f'Generally good, but light on {mismatches[0]}'
            }
        else:
            return {
                'status': 'NEEDS WORK',
                'message': f'Significant imbalances in: {", ".join(mismatches)}'
            }

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
