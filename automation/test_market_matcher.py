#!/usr/bin/env python3
"""
Unit tests for the MarketMatcher class functionality.
Tests fuzzy matching, odds comparison, market mapping, and game availability checking.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the automation directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from market_matcher import MarketMatcher, MatchResult, GameAvailability, create_market_matcher
from models import Selection

def test_fuzzy_team_name_matching():
    """Test fuzzy matching for team names with normalization rules"""
    print("=== Testing Fuzzy Team Name Matching ===")
    
    matcher = create_market_matcher()
    
    test_cases = [
        # (source_home, source_away, target_home, target_away, source_bm, target_bm, expected_confidence_range, expected_swapped)
        ("Manchester United", "Liverpool", "Man Utd", "Liverpool", "bet9ja", "sportybet", (0.8, 1.0), False),
        ("Real Madrid", "Barcelona", "R Madrid", "Barcelona", "bet9ja", "sportybet", (0.8, 1.0), False),
        ("Arsenal", "Chelsea", "Chelsea", "Arsenal", "bet9ja", "sportybet", (0.8, 1.0), True),  # Swapped teams
        ("Manchester City", "Liverpool", "Man City", "Liverpool", "bet9ja", "sportybet", (0.9, 1.0), False),  # Exact abbreviation match
        ("PSG", "Liverpool", "Paris Saint-Germain", "Liverpool", "bet9ja", "sportybet", (0.6, 0.8), False),  # Abbreviation vs full name
        ("Random Team A", "Random Team B", "Unknown Team X", "Unknown Team Y", "bet9ja", "sportybet", (0.0, 0.3), False),  # No match
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases):
        if len(test_case) == 8:
            source_home, source_away, target_home, target_away, source_bm, target_bm, conf_range, expected_swapped = test_case
        else:
            source_home, source_away, target_home, target_away, source_bm, target_bm, conf_range, expected_swapped = test_case + (test_case[2], test_case[3])
        
        try:
            confidence, teams_swapped = matcher.fuzzy_match_team_names(
                source_home, source_away, target_home, target_away, source_bm, target_bm
            )
            
            conf_ok = conf_range[0] <= confidence <= conf_range[1]
            swap_ok = teams_swapped == expected_swapped
            
            status = "✅" if conf_ok and swap_ok else "❌"
            print(f"   {status} Test {i+1}: {source_home} vs {source_away} -> {target_home} vs {target_away}")
            print(f"      Confidence: {confidence:.3f} (expected: {conf_range[0]}-{conf_range[1]})")
            print(f"      Teams swapped: {teams_swapped} (expected: {expected_swapped})")
            
            if not (conf_ok and swap_ok):
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ Test {i+1} failed with exception: {str(e)}")
            all_passed = False
    
    return all_passed

def test_odds_comparison():
    """Test odds comparison logic with configurable tolerance ranges"""
    print("\n=== Testing Odds Comparison ===")
    
    matcher = create_market_matcher(odds_tolerance=0.05)
    
    test_cases = [
        # (original_odds, target_odds, custom_tolerance, expected_within_tolerance, description)
        (2.50, 2.45, None, True, "Within default tolerance"),
        (2.50, 2.55, None, True, "Within default tolerance (upper)"),
        (2.50, 2.60, None, False, "Outside default tolerance"),
        (2.50, 2.40, None, False, "Outside default tolerance (lower)"),
        (2.50, 2.60, 0.15, True, "Within custom tolerance"),
        (2.50, 2.65, 0.10, False, "Outside custom tolerance"),
        (1.50, 1.50, None, True, "Exact match"),
        (0, 2.50, None, False, "Invalid original odds"),
        (2.50, 0, None, False, "Invalid target odds"),
    ]
    
    all_passed = True
    
    for i, (orig_odds, target_odds, tolerance, expected, description) in enumerate(test_cases):
        try:
            within_tolerance, difference = matcher.compare_odds(orig_odds, target_odds, tolerance)
            
            status = "✅" if within_tolerance == expected else "❌"
            print(f"   {status} Test {i+1}: {description}")
            print(f"      {orig_odds} vs {target_odds} (tolerance: {tolerance or 0.05}) -> {within_tolerance}, diff: {difference:.3f}")
            
            if within_tolerance != expected:
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ Test {i+1} failed with exception: {str(e)}")
            all_passed = False
    
    return all_passed

def test_market_mapping():
    """Test market mapping across different bookmakers"""
    print("\n=== Testing Market Mapping ===")
    
    matcher = create_market_matcher()
    
    test_cases = [
        # (market, source_bookmaker, target_bookmaker, expected_contains, description)
        ("Match Result", "bet9ja", "sportybet", "Match Result", "Standard market mapping"),
        ("1X2", "bet9ja", "sportybet", "Match Result", "1X2 to Match Result"),
        ("Over/Under 2.5", "bet9ja", "sportybet", "Over/Under", "Over/Under mapping"),
        ("Both Teams to Score", "bet9ja", "sportybet", "Both Teams", "BTTS mapping"),
        ("Unknown Market", "bet9ja", "sportybet", "Unknown Market", "Unknown market passthrough"),
    ]
    
    all_passed = True
    
    for i, (market, source_bm, target_bm, expected_contains, description) in enumerate(test_cases):
        try:
            mapped_market, confidence = matcher.map_market_across_bookmakers(market, source_bm, target_bm)
            
            contains_expected = expected_contains.lower() in mapped_market.lower()
            conf_ok = 0.0 <= confidence <= 1.0
            
            status = "✅" if contains_expected and conf_ok else "❌"
            print(f"   {status} Test {i+1}: {description}")
            print(f"      {market} ({source_bm} -> {target_bm}) -> {mapped_market} (confidence: {confidence:.3f})")
            
            if not (contains_expected and conf_ok):
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ Test {i+1} failed with exception: {str(e)}")
            all_passed = False
    
    return all_passed

def test_game_availability_checking():
    """Test availability checking for games and markets on destination bookmakers"""
    print("\n=== Testing Game Availability Checking ===")
    
    matcher = create_market_matcher()
    
    # Create test selection
    selection = Selection(
        game_id="test_game_1",
        home_team="Manchester United",
        away_team="Liverpool",
        market="Match Result",
        odds=2.50,
        event_date=datetime.now() + timedelta(hours=2),
        league="Premier League",
        original_text="Manchester United vs Liverpool - Match Result @ 2.50"
    )
    
    # Mock available games data
    available_games = [
        {
            "home_team": "Man Utd",
            "away_team": "Liverpool",
            "markets": [
                {"name": "Match Result", "odds": 2.45},
                {"name": "Over/Under 2.5", "odds": 1.85},
                {"name": "Both Teams to Score", "odds": 1.75}
            ]
        },
        {
            "home_team": "Arsenal",
            "away_team": "Chelsea", 
            "markets": [
                {"name": "Match Result", "odds": 2.10},
                {"name": "Over/Under 2.5", "odds": 1.90}
            ]
        }
    ]
    
    test_cases = [
        # (selection, bookmaker, available_games, expected_available, description)
        (selection, "sportybet", available_games, True, "Game available with good match"),
        (selection, "sportybet", [], False, "No available games"),
        (selection, "sportybet", [{"home_team": "Arsenal", "away_team": "Chelsea", "markets": []}], False, "No matching game"),
    ]
    
    all_passed = True
    
    for i, (sel, bookmaker, games, expected_available, description) in enumerate(test_cases):
        try:
            availability = matcher.check_game_availability(sel, bookmaker, games)
            
            status = "✅" if availability.available == expected_available else "❌"
            print(f"   {status} Test {i+1}: {description}")
            print(f"      Available: {availability.available}, Confidence: {availability.confidence:.3f}")
            if availability.available:
                print(f"      Game: {availability.game_name}")
                print(f"      Markets: {len(availability.markets)}")
            
            if availability.available != expected_available:
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ Test {i+1} failed with exception: {str(e)}")
            all_passed = False
    
    return all_passed

def test_complete_selection_matching():
    """Test complete matching of a selection against available games"""
    print("\n=== Testing Complete Selection Matching ===")
    
    matcher = create_market_matcher()
    
    # Create test selection
    selection = Selection(
        game_id="test_game_1",
        home_team="Manchester United",
        away_team="Liverpool",
        market="Match Result",
        odds=2.50,
        event_date=datetime.now() + timedelta(hours=2),
        league="Premier League",
        original_text="Manchester United vs Liverpool - Match Result @ 2.50"
    )
    
    # Mock available games with good match
    good_games = [
        {
            "home_team": "Man Utd",
            "away_team": "Liverpool",
            "markets": [
                {"name": "Match Result", "odds": 2.48},  # Within tolerance
                {"name": "Over/Under 2.5", "odds": 1.85}
            ]
        }
    ]
    
    # Mock available games with poor odds
    poor_odds_games = [
        {
            "home_team": "Man Utd", 
            "away_team": "Liverpool",
            "markets": [
                {"name": "Match Result", "odds": 2.80},  # Outside tolerance
                {"name": "Over/Under 2.5", "odds": 1.85}
            ]
        }
    ]
    
    test_cases = [
        # (selection, bookmaker, available_games, expected_success, description)
        (selection, "sportybet", good_games, True, "Good match with acceptable odds"),
        (selection, "sportybet", poor_odds_games, True, "Match found but odds outside tolerance"),
        (selection, "sportybet", [], False, "No available games"),
    ]
    
    all_passed = True
    
    for i, (sel, bookmaker, games, expected_success, description) in enumerate(test_cases):
        try:
            match_result = matcher.match_selection(sel, bookmaker, games)
            
            status = "✅" if match_result.success == expected_success else "❌"
            print(f"   {status} Test {i+1}: {description}")
            print(f"      Success: {match_result.success}, Confidence: {match_result.confidence:.3f}")
            if match_result.success:
                print(f"      Matched game: {match_result.matched_game}")
                print(f"      Matched market: {match_result.matched_market}")
                print(f"      Odds: {match_result.original_odds} -> {match_result.matched_odds}")
                if match_result.odds_difference:
                    print(f"      Odds difference: {match_result.odds_difference:.3f}")
            if match_result.warnings:
                print(f"      Warnings: {match_result.warnings}")
            
            if match_result.success != expected_success:
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ Test {i+1} failed with exception: {str(e)}")
            all_passed = False
    
    return all_passed

def test_search_variations():
    """Test generation of search term variations"""
    print("\n=== Testing Search Variations ===")
    
    matcher = create_market_matcher()
    
    test_cases = [
        ("Manchester United", "Liverpool", "sportybet", 8, "Standard team names"),
        ("Real Madrid", "Barcelona", "bet9ja", 8, "Spanish teams"),
        ("", "Liverpool", "sportybet", 4, "Empty home team"),
        ("Manchester United", "", "sportybet", 4, "Empty away team"),
    ]
    
    all_passed = True
    
    for i, (home_team, away_team, bookmaker, min_variations, description) in enumerate(test_cases):
        try:
            variations = matcher.get_search_variations(home_team, away_team, bookmaker)
            
            has_min_variations = len(variations) >= min_variations
            has_unique_variations = len(variations) == len(set(variations))
            
            status = "✅" if has_min_variations and has_unique_variations else "❌"
            print(f"   {status} Test {i+1}: {description}")
            print(f"      Generated {len(variations)} variations (expected >= {min_variations})")
            print(f"      Sample variations: {variations[:3]}")
            
            if not (has_min_variations and has_unique_variations):
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ Test {i+1} failed with exception: {str(e)}")
            all_passed = False
    
    return all_passed

def main():
    """Main test function"""
    print("=== Market Matcher Test Suite ===")
    
    tests = [
        test_fuzzy_team_name_matching,
        test_odds_comparison,
        test_market_mapping,
        test_game_availability_checking,
        test_complete_selection_matching,
        test_search_variations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All market matcher tests passed!")
        return True
    else:
        print("❌ Some market matcher tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)