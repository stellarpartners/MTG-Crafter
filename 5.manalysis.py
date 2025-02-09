#!/usr/bin/env python3
"""
Manalysis - Interactive tool for Magic: The Gathering mana analysis
"""

from src.manalysis import DeckLoader, Manalysis
from src.database.card_database import CardDatabase  # Updated import
from typing import Dict
from pathlib import Path
from src.manalysis.analyzer import Manalysis as ManalysisAnalyzer
from src.collectors.data_engine import DataEngine

def show_analysis_menu(analyzer: ManalysisAnalyzer, decklist: Dict[str, int]):
    """Display analysis menu and handle input"""
    while True:
        print("\nAnalysis Options:")
        print("1. Show Mana Curve")
        print("4. Simulate Opening Hands")
        print("5. Check Casting Probabilities")
        print("0. Return to Main Menu")
        
        choice = input("\nSelect an option (0-5): ")
        
        if choice == "0":
            return
        elif choice == "1":
            curve = analyzer.calculate_mana_curve()
            print("\nMana Value Statistics:")
            print("-" * 40)
            print(f"The average mana value of your deck is {curve['average_mana_value']:.2f} with lands and "
                  f"{curve['average_mana_value_without_lands']:.2f} without lands.")
            print(f"The median mana value of your deck is {curve['median_mana_value']} with lands and "
                  f"{curve['median_mana_value_without_lands']} without lands.")
            print(f"This deck's total mana value is {curve['total_mana_value']}.")
            
            # Add visualization
            print("\nCard Count by Mana Value:")
            print(f"{'-' * 40}")
            print(curve['visualization'])
            
            # Add curve health analysis
            print(f"\nCurve Health: {curve['curve_health']['status']}")
            print(curve['curve_health']['message'])
            print(f"Early game (0-2): {curve['curve_health']['distribution']['early_game']:.1f}%")
            print(f"Mid game (3-5): {curve['curve_health']['distribution']['mid_game']:.1f}%")
            print(f"Late game (6+): {curve['curve_health']['distribution']['late_game']:.1f}%")
            
            # Add detailed color statistics
            color_stats = curve['color_stats']
            print("\nDetailed Color Statistics:")
            print("-" * 40)
            print(f"Land cards: {color_stats['land_count']}")
            print(f"Non-land cards: {color_stats['non_land_count']}")
            
            for color in ['W', 'U', 'B', 'R', 'G', 'C']:
                print(f"\n{color}:")
                print(f"  {color_stats['non_land_cards'][color]} out of {color_stats['non_land_count']} non-land cards are {{{color}}}")
                print(f"  {color_stats['non_land_mana_symbols'][color]} out of {sum(color_stats['non_land_mana_symbols'].values())} mana symbols on non-land cards are {{{color}}}")
                print(f"  {color_stats['land_produces'][color]} out of {color_stats['land_count']} land cards produce {{{color}}}")
                print(f"  {color_stats['land_mana_symbols'][color]} out of {sum(color_stats['land_mana_symbols'].values())} mana symbols on lands produce {{{color}}}")
            
            # Add mana sources analysis
            mana_sources = curve['mana_sources']
            print("\nMana Sources Analysis:")
            print("-" * 40)
            print(f"Total mana sources: {mana_sources['total_sources']}")
            print("Breakdown by color:")
            for color, count in mana_sources['breakdown']['by_color'].items():
                print(f"{color}: {count}")
            
            # Add mana rock and mana dork statistics
            print("\nMana Rocks:")
            if mana_sources['mana_rocks']:
                for rock in mana_sources['mana_rocks']:
                    print(f"  - {rock}")
            else:
                print("  No mana rocks found")
            
            print("\nMana Dorks:")
            if mana_sources['mana_dorks']:
                for dork in mana_sources['mana_dorks']:
                    print(f"  - {dork}")
            else:
                print("  No mana dorks found")
            
            # Add mana discount analysis
            mana_discounts = curve['mana_discounts']
            print("\nMana Value Discounts:")
            if mana_discounts:
                for card_name, discount in mana_discounts.items():
                    print(f"  - {card_name}: Original MV = {discount['original_mana_value']}, Reduced MV = {discount['reduced_mana_value']} ({discount['condition']})")
            else:
                print("  No mana value discounts found")
        elif choice == "4":
            num_sims = int(input("How many simulations? (100-10000): "))
            results = analyzer.analyze_opening_hands(num_sims)
            print(results['visualization'])
        elif choice == "5":
            num_sims = int(input("How many simulations? (100-1000): "))
            results = analyzer.analyze_casting_sequence(num_sims)
            print("\nCasting Probabilities:")
            for card, prob in results['cast_probability'].items():
                print(f"{card}: {prob*100:.1f}% chance to cast by turn 10")
        else:
            print("Invalid choice, please try again")

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

def _visualize_curve(curve: Dict[int, int], max_count: int) -> str:
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

def format_curve_results(results: Dict, analyzer = None) -> str:
    """Format mana curve results for display"""
    output = []
    
    # Create visualization
    output.append("Card Count by Mana Value:")
    output.append(f"{'-' * 40}")
    
    # Add visualization if available
    if results.get('visualization'):
        output.append(results['visualization'])
    
    # Add average MV
    output.append(f"\nAverage Mana Value: {results['average_mv']:.2f}")
    
    # Add detailed statistics
    if 'detailed_stats' in results:
        stats = results['detailed_stats']
        output.append("\nDetailed Statistics:")
        output.append("-" * 40)
        output.append(f"Median MV: {stats['median_mv']}")
        
        # Show breakdown by card type
        output.append("\nBy Card Type:")
        for card_type, type_stats in sorted(stats['by_type'].items()):
            output.append(f"{card_type}: {type_stats['count']} cards (Avg MV: {type_stats['avg_mv']:.2f})")
        
        # Show breakdown by color
        output.append("\nBy Color:")
        for color, color_stats in sorted(stats['by_color'].items()):
            output.append(f"{color}: {color_stats['count']} cards (Avg MV: {color_stats['avg_mv']:.2f})")
    
    # Add curve health analysis
    if 'curve_health' in results:
        health = results['curve_health']
        output.append(f"\nCurve Health: {health['status']}")
        output.append(health['message'])
        if 'distribution' in health:
            dist = health['distribution']
            output.append(f"Early game (0-2): {dist['early_game']:.1f}%")
            output.append(f"Mid game (3-5): {dist['mid_game']:.1f}%")
            output.append(f"Late game (6+): {dist['late_game']:.1f}%")
    
    # Add color analysis if available
    color_analysis = results.get('color_analysis')
    if color_analysis:
        output.append("\nColor Analysis:")
        output.append("-" * 40)
        
        for color, data in color_analysis.items():
            if data['count'] > 0:
                output.append(f"{color}: {data['count']} cards ({data['percentage']:.1f}%)")
    
    return "\n".join(output)

def show_saved_analysis(analysis: Dict):
    """Display saved analysis results"""
    print("\nSaved Analysis Results:")
    print("-" * 40)
    
    # Show mana curve
    print("\nMana Curve:")
    print(format_curve_results(analysis['curve']))
    
    # Show casting analysis
    print("\nCasting Analysis:")
    print("-" * 40)
    print("\nEarliest Casting Turns (sorted by mana value):")
    print("MV | Turn | Card")
    print("-" * 40)
    for card, data in sorted(analysis['casting']['earliest_cast'].items(), 
                           key=lambda x: (-x[1]['mana_value'], x[1]['turn'], x[0])):
        print(f"{data['mana_value']:2d} | {data['turn']:4d} | {card}")
    
    # Show statistics
    print("\nStatistical Analysis:")
    output = ["Casting Statistics Analysis", "=" * 40, ""]
    
    # Show cards with most consistent casting turns
    output.extend([
        "Most Consistent Cards (Low Variance):",
        "-" * 30
    ])
    sorted_by_variance = sorted(analysis['statistics']['average_first_cast'].items(), 
                              key=lambda x: x[1]['std'])
    for card, data in sorted_by_variance[:5]:
        output.append(
            f"{card}: Turn {data['mean']:.1f} ±{data['std']:.2f}"
        )
    
    # Show problematic cards (high variance)
    output.extend([
        "",
        "Most Variable Cards:",
        "-" * 30
    ])
    for card, variance in analysis['statistics']['variance_analysis']:
        output.append(f"{card}: ±{variance:.2f} turns")
    
    print("\n".join(output))

def main():
    print("Welcome to Manalysis!")
    print("-" * 40)
    
    # Initialize card database
    print("Loading card database...")
    card_db = CardDatabase()
    loader = DeckLoader(card_db)
    if not card_db.db_path.exists():
        print("Error: Card database not found!")
        print("Please run '1.gather_data.py' first and select 'Build SQLite Database'")
        return
    print("Card database ready!")
    
    while True:
        print("\nOptions:")
        print("1. Load saved deck")
        print("2. Save new deck from clipboard")
        print("3. List saved decks")
        print("4. Update saved deck")
        print("5. Show Casting Analysis")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-5): ").strip()
        
        if choice == "0":
            print("\nGoodbye!")
            break
        
        if choice == "1":
            try:
                loader = DeckLoader(card_db)
                print("\nSaved decks:")
                decks = loader.list_saved_decks()
                if not decks:
                    print("No saved decks found")
                    continue
                    
                for i, deck in enumerate(decks, 1):
                    analysis_status = "✓" if deck.get('manalysis') else " "
                    print(f"{i}. [{analysis_status}] {deck['name']} ({deck['commander']}) - {deck['total_cards']} cards")
                
                deck_choice = input("\nEnter deck number or name to load: ").strip()
                deck_data = loader.load_saved_deck_with_data(deck_choice)
                decklist = deck_data['cards']
                
                print(f"\nLoaded deck: {deck_data['name']} ({deck_data['commander']}) - {sum(decklist.values())} cards")

                analyzer = Manalysis(decklist, card_db)
                analyzer.commander = loader.commander
                
                # Check if we have saved analysis
                if deck_data.get('manalysis'):
                    print("\nFound saved analysis. Would you like to:")
                    print("1. View saved analysis")
                    print("2. Run new analysis")
                    analysis_choice = input("\nEnter choice (1-2): ").strip()
                    
                    if analysis_choice == "1":
                        show_saved_analysis(deck_data['manalysis'])
                        continue
                
                show_analysis_menu(analyzer, decklist)
                
                # Save analysis results
                save = input("\nWould you like to save this analysis? (1=yes, 0=no): ").strip()
                if save == '1':
                    analysis_results = {
                        'curve': analyzer.calculate_mana_curve(),
                        'casting': analyzer.analyze_casting_sequence(),
                        'statistics': analyzer.analyze_casting_statistics()
                    }
                    loader.save_manalysis(deck_choice, analysis_results)
                    print("Analysis saved!")
            except Exception as e:
                print(f"\nError: {str(e)}")
                continue
        elif choice == "2":
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
                
                # Ask to save the deck
                save = input("\nWould you like to save this deck? (1=yes, 0=no): ").strip()
                if save == '1':
                    while True:
                        name = input("Enter deck name: ").strip()
                        if not name:
                            print("Please enter a valid name.")
                            continue
                            
                        try:
                            if loader.save_deck(decklist, name):
                                print(f"Deck saved as '{name}'")
                                break
                        except Exception as e:
                            print(f"Error saving deck: {str(e)}")
                            retry = input("Try again? (1=yes, 0=no): ").strip()
                            if retry != '1':
                                break
                            
                # Proceed with analysis regardless of save choice
                if decklist:
                    analyzer = Manalysis(decklist, card_db)
                    analyzer.commander = loader.commander
                    show_analysis_menu(analyzer, decklist)
                
            except Exception as e:
                print(f"\nError: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        elif choice == "3":
            loader = DeckLoader(card_db)
            print("\nSaved decks:")
            decks = loader.list_saved_decks()
            if not decks:
                print("No saved decks found")
                continue
                
            for deck in decks:
                print(f"\n{deck['name']}:")
                print(f"  Commander: {deck['commander']}")
                print(f"  Total cards: {deck['total_cards']}")
        elif choice == "4":
            try:
                loader = DeckLoader(card_db)
                print("\nSaved decks:")
                decks = loader.list_saved_decks()
                if not decks:
                    print("No saved decks found")
                    continue
                    
                for i, deck in enumerate(decks, 1):
                    print(f"{i}. {deck['name']} ({deck['commander']}) - {deck['total_cards']} cards")
                
                deck_choice = input("\nEnter deck number or name to update: ").strip()
                if loader.update_deck(deck_choice):
                    print("Deck updated successfully!")
                
            except Exception as e:
                print(f"\nError: {str(e)}")
                continue
        elif choice == "5":
            try:
                loader = DeckLoader(card_db)
                print("\nSaved decks:")
                decks = loader.list_saved_decks()
                if not decks:
                    print("No saved decks found")
                    continue
                    
                for i, deck in enumerate(decks, 1):
                    print(f"{i}. {deck['name']} ({deck['commander']}) - {deck['total_cards']} cards")
                
                deck_choice = input("\nEnter deck number or name to show casting analysis: ").strip()
                deck_data = loader.load_saved_deck_with_data(deck_choice)
                decklist = deck_data['cards']
                
                print(f"\nLoaded deck: {deck_data['name']} ({deck_data['commander']}) - {sum(decklist.values())} cards")

                analyzer = Manalysis(decklist, card_db)
                analyzer.commander = loader.commander
                show_saved_analysis(deck_data['manalysis'])
            except Exception as e:
                print(f"\nError: {str(e)}")
                continue
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == '__main__':
    main() 