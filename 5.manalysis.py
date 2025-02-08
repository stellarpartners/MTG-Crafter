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
        print("4. Run Statistical Analysis")
        print("5. Show Full Deck Statistics")
        print("6. Return to Main Menu")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "6":
            break
            
        if choice == "1":
            curve = analyzer.calculate_mana_curve()
            print("\nMana Curve:")
            print("-" * 40)
            print(format_curve_results(curve, analyzer))
            
        elif choice == "2":
            num_sims = input("\nNumber of simulations (default 20): ").strip()
            num_sims = int(num_sims) if num_sims.isdigit() else 1000
            
            sim_results = analyzer.simulate_opening_hand(num_sims)
            print("\nOpening Hand Analysis:")
            print("-" * 40)
            print(format_simulation_results(sim_results))
            
        elif choice == "3":
            casting_analysis = analyzer.analyze_casting_sequence(1000)  # Run 1000 simulations
            
            print("\nCasting Analysis:")
            print("-" * 40)
            
            print("\nDetailed Card Statistics (sorted by mana value):")
            print("MV | Drawn % | Cast % | Cast Turn | Card")
            print("-" * 40)
            for card, stats in sorted(casting_analysis['card_statistics'].items(), 
                                    key=lambda x: (x[1]['mana_value'], x[0])):
                cast_turn = stats['average_cast_turn']
                print(f"{stats['mana_value']:2d} | {stats['draw_percentage']:6.1f}% | {stats['cast_percentage']:5.1f}% | "
                      f"{'Never' if cast_turn == float('inf') else f'{cast_turn:4.1f}'} | {card}")
            
            # Show deck castability by turn
            print("\nDeck Castability:")
            for turn, percentage in casting_analysis['cast_by_turn'].items():
                print(f"By turn {turn}: {percentage:.1f}% of non-land cards")
            
            # Show problematic cards
            if casting_analysis['problematic_cards']:
                print("\nCards Not Cast in Simulations:")
                for card in casting_analysis['problematic_cards']:
                    print(f"- {card}")
            
            # Show sample games
            print("\nSample Game Logs:")
            print("=" * 60)
            for game_log in casting_analysis['sample_games']:
                print(game_log)
                print("=" * 60)
            
        elif choice == "4":
            print("\nRunning statistical analysis (this may take a while)...")
            stats = analyzer.analyze_casting_statistics()
            print(analyzer._visualize_casting_statistics(stats))
            
            # Ask if user wants to see detailed stats for specific cards
            while True:
                card = input("\nEnter card name for detailed stats (or press Enter to continue): ").strip()
                if not card:
                    break
                if card in stats['average_first_cast']:
                    print(f"\nDetailed statistics for {card}:")
                    print(f"Average first cast: Turn {stats['average_first_cast'][card]['mean']:.1f}")
                    print(f"95% Confidence Interval: {stats['confidence_intervals'][card]['lower']:.1f} - {stats['confidence_intervals'][card]['upper']:.1f}")
                    print("\nCast reliability by turn:")
                    for turn, probability in stats['cast_reliability'][card].items():
                        print(f"Turn {turn}: {probability:.1f}%")
                else:
                    print("Card not found in analysis")
            
        elif choice == "5":
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
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-4): ").strip()
        
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
                
                # Ask to save the deck before doing anything else
                save = input("\nWould you like to save this deck? (1=yes, 0=no): ").strip()
                if save == '1':
                    while True:
                        name = input("Enter deck name: ").strip()
                        if name:
                            if loader.save_deck(decklist, name):
                                print(f"Deck saved as '{name}'")
                                break
                            else:
                                print("Failed to save deck. Try a different name.")
                        else:
                            print("Please enter a valid name.")
                
                # Proceed with analysis regardless of save choice
                analyzer = Manalysis(decklist, card_db)
                analyzer.commander = loader.commander
                show_analysis_menu(analyzer, decklist)
                
            except Exception as e:
                print(f"\nError: {str(e)}")
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
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == '__main__':
    main() 