#!/usr/bin/env python3
"""
Manalysis - Interactive tool for Magic: The Gathering mana analysis
"""

from src.manalysis import DeckLoader, Manalysis
from src import CardDatabase  # Import from src package directly
from typing import Dict
from pathlib import Path

def show_analysis_menu(analyzer, decklist):
    """Show deck analysis"""
    # Get analysis data
    curve_data = analyzer.calculate_mana_curve()
    color_data = analyzer.analyze_color_balance()
    
    # Calculate mana value statistics
    total_cards = sum(analyzer.decklist.values())
    total_mv = 0
    total_mv_no_lands = 0
    mv_list = []  # for median calculation
    mv_list_no_lands = []  # for median without lands
    
    for card_name, quantity in analyzer.decklist.items():
        card = analyzer.card_db.get_card(card_name)
        mv = card.get('cmc', 0)
        is_land = card.get('is_land', False)
        
        mv_list.extend([mv] * quantity)
        total_mv += mv * quantity
        
        if not is_land:
            mv_list_no_lands.extend([mv] * quantity)
            total_mv_no_lands += mv * quantity
    
    # Calculate averages
    avg_mv = total_mv / len(mv_list) if mv_list else 0
    avg_mv_no_lands = total_mv_no_lands / len(mv_list_no_lands) if mv_list_no_lands else 0
    
    # Calculate medians
    mv_list.sort()
    mv_list_no_lands.sort()
    median_mv = mv_list[len(mv_list)//2] if mv_list else 0
    median_mv_no_lands = mv_list_no_lands[len(mv_list_no_lands)//2] if mv_list_no_lands else 0
    
    # Print mana value statistics
    print("\nMana Value Statistics:")
    print("-" * 50)
    print(f"The average mana value of your deck is {avg_mv:.2f} with lands and {avg_mv_no_lands:.2f} without lands.")
    print(f"The median mana value of your deck is {median_mv} with lands and {median_mv_no_lands} without lands.")
    print(f"This deck's total mana value is {total_mv}.")
    
    # Color Distribution
    print("\nColor Distribution:")
    print("-" * 50)
    for color in 'WUBRG':
        if color in color_data['color_stats']:
            stats = color_data['color_stats'][color]
            cards_of_color = sum(1 for card_name, qty in analyzer.decklist.items() 
                               if not analyzer.card_db.get_card(card_name).get('is_land', False)
                               and color in analyzer.card_db.get_card(card_name).get('color_identity', ''))
            
            print(f"\n{color} Color Statistics:")
            print(f"- {cards_of_color} out of {total_cards - len(analyzer.lands)} non-land cards are {color}")
            print(f"- {stats['symbols_in_costs']} out of {color_data['total_symbols']} mana symbols are {color}")
            print(f"- {stats['producing_lands']} out of {len(analyzer.lands)} lands produce {color}")
            print(f"- {stats['producing_lands']} out of {sum(s['producing_lands'] for s in color_data['color_stats'].values())} mana symbols on lands are {color}")
    
    # Continue with existing analysis...
    print("\nMana Curve Analysis:")
    print("-" * 50)
    print(f"Average CMC: {curve_data['average_cmc']}")
    print(f"Total non-land cards: {curve_data['total_cards']}")
    print("\nDistribution:")
    for cmc, count in sorted(curve_data['curve'].items()):
        percentage = curve_data['distribution'][cmc]
        print(f"CMC {cmc}: {count} cards ({percentage}%)")
        print("█" * int(percentage/2))  # Visual bar
    
    # 2. Color Balance Analysis
    print("\nColor Balance Analysis:")
    print("-" * 50)
    print(f"Total Cards: {color_data['total_cards']}")
    print(f"Total Lands: {color_data['total_lands']}")
    
    if color_data['color_stats']:
        print("\nColor Requirements vs Production:")
        for color, stats in color_data['color_stats'].items():
            print(f"\n{color}:")
            print(f"  Required: {stats['required']:.1f}%")
            print(f"  Produced: {stats['produced']:.1f}%")
            print(f"  Sources: {stats['producing_lands']} lands")
    
    if color_data['mismatches']:
        print("\nPotential Color Issues:")
        for color in color_data['mismatches']:
            stats = color_data['color_stats'][color]
            print(f"  {color}: Required {stats['required']:.1f}% vs Produced {stats['produced']:.1f}%")
    
    # 3. Summary Statistics
    print("\nSummary Statistics:")
    print("-" * 50)
    print(f"Total Cards: {sum(analyzer.decklist.values())}")
    print(f"Non-land Cards: {curve_data['total_cards']}")
    print(f"Lands: {len(analyzer.lands)}")
    
    print("\nMana Production:")
    for color, sources in analyzer.mana_sources.items():
        if sources:
            print(f"{color}: {len(sources)} sources")

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