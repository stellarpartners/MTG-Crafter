#!/usr/bin/env python3
"""
Manalysis - Interactive tool for Magic: The Gathering mana analysis
"""

from src.manalysis import DeckLoader, Manalysis
from src import CardDatabase  # Import from src package directly
from typing import Dict
from pathlib import Path

def show_analysis_menu(analyzer, decklist):
    """Show analysis options for loaded deck"""
    while True:
        print("\nAnalysis Options:")
        print("1. Show Mana Curve")
        print("2. Simulate Opening Hands")
        print("3. Calculate Casting Probabilities")
        print("4. Show Full Deck Statistics")
        print("5. Return to Main Menu")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "5":
            break
            
        if choice == "1":
            curve = analyzer.calculate_mana_curve()
            print("\nMana Curve:")
            print("-" * 40)
            print(format_curve_results(curve, analyzer))
            
        elif choice == "2":
            num_sims = input("\nNumber of simulations (default 1000): ").strip()
            num_sims = int(num_sims) if num_sims.isdigit() else 1000
            
            sim_results = analyzer.simulate_opening_hand(num_sims)
            print("\nOpening Hand Analysis:")
            print("-" * 40)
            print(format_simulation_results(sim_results))
            
        elif choice == "3":
            print("\nSelect a card to analyze:")
            for card, qty in decklist.items():
                print(f"- {card}")
            card_name = input("\nCard name: ").strip()
            turn = input("By which turn? ").strip()
            
            if card_name in decklist and turn.isdigit():
                prob = analyzer.probability_of_casting(card_name, int(turn))
                print(f"\nProbability of casting {card_name} by turn {turn}: {prob:.1%}")
            else:
                print("Invalid card name or turn number")
                
        elif choice == "4":
            print("\nDeck Statistics:")
            print("-" * 40)
            print(f"Total cards: {sum(decklist.values())}")
            if analyzer.commander:
                print(f"Commander: {analyzer.commander}")
            # Add more statistics here
            
        input("\nPress Enter to continue...")

def format_simulation_results(results: Dict) -> str:
    """Format simulation results for display"""
    output = []
    
    # Add visualization
    if 'visualization' in results:
        output.append(results['visualization'])
    
    output.append("\nDeck Statistics:")
    output.append(f"Total lands in deck: {results['total_lands_in_deck']} ({results['land_percentage']:.1f}%)")
    output.append(f"Average lands in hand: {results['average_lands']:.2f}")
    output.append(f"Chance of no lands: {results['no_land_percentage']:.1f}%")
    
    if results['color_distribution']:
        output.append("\nColor Presence in Opening Hands:")
        for color, percentage in results['color_distribution'].items():
            output.append(f"{color}: {percentage:.1f}%")
    
    return "\n".join(output)

def format_discount_analysis(discounts: Dict) -> str:
    """Format and detail discount analysis for display"""
    output = []
    
    output.append("\nMana Cost Reduction Effects:")
    output.append(f"Found {len(set(card['card_name'] for card in discounts['cards']))} cards with cost reduction:")
    output.append(f"- Fixed reductions: {discounts['types']['fixed']}")
    output.append(f"- Scaling reductions: {discounts['types']['scaling']}")
    output.append(f"- Conditional reductions: {discounts['types']['conditional']}")
    
    # Detailed breakdown
    processed_cards = set()
    output.append("\nDetailed breakdown:")
    for card in discounts['cards']:
        if card['card_name'] not in processed_cards:
            processed_cards.add(card['card_name'])
            reduction_type = (
                "Fixed" if card['discount_type'] == "fixed" 
                else "Optimal Scaling" if card['discount_type'] == "optimal scaling"
                else "Scaling" if card['discount_type'] == "scaling"
                else "Conditional"
            )
            total_card_reduction = card['discount_amount'] * card['quantity']
            
            if card['discount_type'] == "optimal scaling":
                output.append(f"- {card['card_name']} ({card['original_cost']} → {card['potential_cost']} at optimal conditions)")
                output.append(f"  Type: {reduction_type} | Amount: {card['discount_amount']} × {card['quantity']} = {total_card_reduction}")
                output.append(f"  {card['condition']}")
            elif card['discount_type'] == "fixed":
                output.append(f"- {card['card_name']} ({card['original_cost']} → {card['potential_cost']})")
                output.append(f"  Type: {reduction_type} | Amount: {card['discount_amount']} × {card['quantity']} = {total_card_reduction}")
                output.append(f"  {card['condition']}")
            else:
                output.append(f"- {card['card_name']} ({card['original_cost']} → Variable)")
                output.append(f"  Type: {reduction_type}")
                output.append(f"  {card['condition']}")
    
    # Add summary totals after the detailed breakdown
    fixed = discounts['total_reduction']['fixed']
    optimal_scaling = discounts['total_reduction']['optimal_scaling']
    total = discounts['total_reduction']['total']
    output.append(f"\nTotal Potential Mana Reduction: {total}")
    output.append(f"- Fixed reductions: {fixed}")
    output.append(f"- Optimal scaling reductions: {optimal_scaling}")
    
    return "\n".join(output)

def format_curve_results(results: Dict, analyzer: Manalysis) -> str:
    """Format mana curve results for display"""
    output = []
    
    # Original summary
    output.append("\nDeck Summary (Before Cost Reduction):")
    output.append(f"The average mana value of your main deck is {results['stats_with_lands']['average']:.2f} with lands "
                 f"and {results['stats_without_lands']['average']:.2f} without lands. "
                 f"The median mana value of your main deck is {int(results['stats_with_lands']['median'])} with lands "
                 f"and {int(results['stats_without_lands']['median'])} without lands. "
                 f"This deck's total mana value is {results['total_mv']}.")
    
    if 'visualization' in results:
        output.append("\nMana Curve Distribution (Before Cost Reduction):")
        output.append(results['visualization'])
    
    output.append("\nMana Value Statistics (Before Cost Reduction):")
    output.append(f"Total non-land cards: {results['total_spells']}")
    output.append(f"Average mana value: {results['average_mv']:.2f}")
    output.append(f"Median mana value: {results['median_mv']}")
    
    output.append("\nBreakdown by mana value (Before Cost Reduction):")
    for mv, count in sorted(results['curve'].items()):
        output.append(f"MV {mv}: {count} cards")
    
    # Add mana source analysis
    mana_sources = analyzer.analyze_mana_sources()
    if mana_sources['total_sources'] > 0:
        output.append("\nMana Sources:")
        output.append(f"Total mana sources: {mana_sources['total_sources']}")
        output.append(f"- Lands: {mana_sources['breakdown']['lands']}")
        if mana_sources['mana_dorks']:
            output.append(f"- Mana creatures: {mana_sources['breakdown']['mana_dorks']}")
            output.append("  " + ", ".join(sorted(set(mana_sources['mana_dorks']))))
        if mana_sources['artifacts']:
            output.append(f"- Mana artifacts: {mana_sources['breakdown']['artifacts']}")
            output.append("  " + ", ".join(sorted(set(mana_sources['artifacts']))))
        if mana_sources['other_sources']:
            output.append(f"- Other sources: {mana_sources['breakdown']['other']}")
            output.append("  " + ", ".join(sorted(set(mana_sources['other_sources']))))
    
    # Add mana discount analysis
    discounts = analyzer.analyze_mana_discounts()
    if discounts['total_cards'] > 0:
        output.append(format_discount_analysis(discounts))
        
        # Add summary after cost reduction
        output.append("\nDeck Summary (After Cost Reduction):")
        output.append(f"The average mana value of your main deck is {results['detailed']['reduced']['stats_with_lands']['average']:.2f} with lands "
                     f"and {results['detailed']['reduced']['stats_without_lands']['average']:.2f} without lands. "
                     f"The median mana value of your main deck is {int(results['detailed']['reduced']['stats_with_lands']['median'])} with lands "
                     f"and {int(results['detailed']['reduced']['stats_without_lands']['median'])} without lands. ")
        # Compute adjusted total dynamically as original total MV minus the computed total discount
        discount_total = discounts['total_reduction']['total']
        adjusted_total = results['total_mv'] - discount_total
        output.append(f"This deck's adjusted total mana value is {adjusted_total}.")
        
        # Add adjusted curve visualization
        reduced_curve = results['detailed']['reduced']['curve']
        max_count = max(reduced_curve.values()) if reduced_curve else 0
        if max_count > 0:
            output.append("\nMana Curve Distribution (After Cost Reduction):")
            visualization = []
            max_mv = max(reduced_curve.keys()) if reduced_curve else 0
            
            for mv in range(max_mv + 1):
                count = reduced_curve.get(mv, 0)
                bar_height = int((count / max_count) * 10) if max_count > 0 else 0
                bar = f"\n{mv:2d}│ {'█' * bar_height}{' ' * (10 - bar_height)} {count:2d}"
                visualization.append(bar)
            visualization.append("\n  ╰" + "─" * 13)
            output.append("".join(visualization))
        
        output.append("\nBreakdown by mana value (After Cost Reduction):")
        for mv, count in sorted(reduced_curve.items()):
            output.append(f"MV {mv}: {count} cards")
        
        output.append("\nNote: Variable and conditional reductions not included in these calculations")
    
    # Add color balance analysis
    color_analysis = analyzer.analyze_color_balance()
    output.append("\nColor Balance Analysis:")
    
    # Add overall diagnosis first
    diagnosis = analyzer._diagnose_color_balance(
        {c: data['count'] for c, data in color_analysis['mana_symbols'].items()},
        {c: data['count'] for c, data in color_analysis['land_production'].items()}
    )
    output.append(f"\nMana Base Status: {diagnosis['status']}")
    output.append(f"Diagnosis: {diagnosis['message']}")
    
    for color in 'WUBRG':
        card_data = color_analysis['card_colors'].get(color, {'percentage': 0, 'count': 0})
        symbol_data = color_analysis['mana_symbols'].get(color, {'percentage': 0, 'count': 0})
        land_data = color_analysis['land_production'].get(color, {'percentage': 0, 'count': 0, 'symbol_percentage': 0})
        
        if card_data['count'] > 0 or symbol_data['count'] > 0 or land_data['count'] > 0:
            output.append(f"\n{color} Color Analysis:")
            output.append(f"Cards: {card_data['count']} out of {color_analysis['totals']['nonland_cards']} non-land cards ({card_data['percentage']:.1f}%)")
            output.append(f"Mana Symbols: {symbol_data['count']} out of {color_analysis['totals']['mana_symbols']} symbols ({symbol_data['percentage']:.1f}%)")
            output.append(f"Production: {land_data['count']} out of {color_analysis['totals']['lands']} lands ({land_data['percentage']:.1f}%)")
            output.append(f"Land Symbols: {land_data['symbol_percentage']:.1f}% of symbols on lands")
    
    # Add recommendations
    if any(data['count'] > 0 for data in color_analysis['mana_symbols'].values()):
        output.append("\nColor Balance Recommendations:")
        for color in 'WUBRG':
            symbol_percent = color_analysis['mana_symbols'].get(color, {'percentage': 0})['percentage']
            land_percent = color_analysis['land_production'].get(color, {'percentage': 0})['percentage']
            
            if symbol_percent > 0:
                if land_percent < symbol_percent * 0.8:
                    output.append(f"⚠️ Need more {color} sources (have {land_percent:.1f}%, need ~{symbol_percent:.1f}%)")
                elif land_percent > symbol_percent * 1.5:
                    output.append(f"ℹ️ Could reduce {color} sources (have {land_percent:.1f}%, need ~{symbol_percent:.1f}%)")
    
    return "\n".join(output)

def main():
    print("Welcome to Manalysis!")
    print("-" * 40)
    
    # Initialize card database
    print("Loading card database...")
    card_db = CardDatabase()
    if not card_db.db_path.exists():
        print("Error: Card database not found!")
        print("Please run '1.gather_data.py' first and select 'Build SQLite Database'")
        return
    print("Card database ready!")
    
    analyzer = None
    
    while True:
        if not analyzer:
            print("\nOptions:")
            print("1. Load deck from clipboard")
            print("0. Exit")
        else:
            print("\nOptions:")
            print("1. Analyze current deck")
            print("2. Load new deck")
            print("0. Exit")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "0":
            print("\nGoodbye!")
            break
        
        if not analyzer:
            if choice == "1":
                try:
                    print("\nReading deck from clipboard...")
                    loader = DeckLoader(card_db)
                    decklist = loader.load_from_clipboard()
                    
                    if not decklist:
                        print("No valid deck found in clipboard. Please copy a deck list and try again.")
                        print("Expected format:")
                        print("1x Card Name")
                        print("4x Other Card")
                        continue
                    
                    print(f"\nFound {sum(decklist.values())} cards:")
                    for card, quantity in decklist.items():
                        print(f"{quantity}x {card}")
                    
                    analyzer = Manalysis(decklist, card_db)
                    analyzer.commander = loader.commander
                    
                except Exception as e:
                    print(f"\nError: {str(e)}")
                    continue
            else:
                print("\nInvalid choice. Please try again.")
        else:
            if choice == "1":
                show_analysis_menu(analyzer, decklist)
            elif choice == "2":
                analyzer = None  # Reset for new deck
            else:
                print("\nInvalid choice. Please try again.")

if __name__ == '__main__':
    main() 