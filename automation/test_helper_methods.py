#!/usr/bin/env python3
"""
Unit tests for helper methods in betslip creation functionality.
These tests don't require external API keys.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the automation directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Selection, validate_betslip_code, validate_odds_tolerance

def test_selection_creation():
    """Test creating Selection objects"""
    print("=== Testing Selection Creation ===")
    
    try:
        selection = Selection(
            game_id="test_game_1",
            home_team="Manchester United",
            away_team="Liverpool", 
            market="Match Result - Home Win",
            odds=2.50,
            event_date=datetime.now() + timedelta(hours=2),
            league="Premier League",
            original_text="Manchester United vs Liverpool - Match Result - Home Win @ 2.50"
        )
        
        print(f"✅ Selection created successfully:")
        print(f"   Game: {selection.home_team} vs {selection.away_team}")
        print(f"   Market: {selection.market}")
        print(f"   Odds: {selection.odds}")
        print(f"   League: {selection.league}")
        return True
        
    except Exception as e:
        print(f"❌ Selection creation failed: {str(e)}")
        return False

def test_betslip_code_validation():
    """Test betslip code validation"""
    print("\n=== Testing Betslip Code Validation ===")
    
    test_codes = [
        ("ABC123DEF", True, "Valid alphanumeric code"),
        ("12345678", True, "Valid numeric code"),
        ("TEST-CODE-123", True, "Valid code with hyphens"),
        ("TEST_CODE_123", True, "Valid code with underscores"),
        ("", False, "Empty code"),
        ("ABC", False, "Too short"),
        ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", False, "Too long"),
        ("ABC@123", False, "Invalid characters"),
        (123, False, "Non-string input")
    ]
    
    all_passed = True
    
    for code, expected, description in test_codes:
        result = validate_betslip_code(code)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {description}: '{code}' -> {result}")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_odds_tolerance():
    """Test odds tolerance validation"""
    print("\n=== Testing Odds Tolerance ===")
    
    test_cases = [
        (2.50, 2.45, 0.05, True, "Within tolerance"),
        (2.50, 2.55, 0.05, True, "Within tolerance (upper)"),
        (2.50, 2.60, 0.05, False, "Outside tolerance"),
        (2.50, 2.35, 0.05, False, "Outside tolerance (lower)"),
        (1.50, 1.50, 0.05, True, "Exact match"),
        (0, 2.50, 0.05, False, "Invalid original odds"),
        (2.50, 0, 0.05, False, "Invalid new odds"),
        ("2.50", 2.45, 0.05, False, "Non-numeric input")
    ]
    
    all_passed = True
    
    for orig, new, tolerance, expected, description in test_cases:
        result = validate_odds_tolerance(orig, new, tolerance)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {description}: {orig} vs {new} (±{tolerance}) -> {result}")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_bookmaker_adapters():
    """Test bookmaker adapter functionality"""
    print("\n=== Testing Bookmaker Adapters ===")
    
    try:
        from bookmaker_adapters import get_bookmaker_adapter
        
        # Test different bookmaker adapters
        bookmakers = ['bet9ja', 'sportybet', 'betway', 'bet365']
        
        for bookmaker in bookmakers:
            print(f"\nTesting {bookmaker} adapter:")
            adapter = get_bookmaker_adapter(bookmaker)
            
            # Test team name normalization
            test_teams = [
                "Manchester United FC",
                "Real Madrid C.F.",
                "Liverpool F.C.",
                "Arsenal FC"
            ]
            
            print("  Team name normalization:")
            for team in test_teams:
                normalized = adapter.normalize_game_name(team)
                print(f"    {team} -> {normalized}")
            
            # Test market name mapping
            test_markets = [
                "Match Result",
                "1X2",
                "Over/Under 2.5",
                "Both Teams to Score"
            ]
            
            print("  Market name mapping:")
            for market in test_markets:
                mapped = adapter.map_market_name(market)
                print(f"    {market} -> {mapped}")
            
            # Test search variations
            variations = adapter.get_search_variations("Manchester United", "Liverpool")
            print(f"  Search variations (showing first 3): {variations[:3]}")
            
            # Test URL generation
            betslip_url = adapter.get_betslip_url("TEST123")
            betting_url = adapter.get_betting_url()
            print(f"  Betslip URL: {betslip_url}")
            print(f"  Betting URL: {betting_url}")
        
        print("✅ Bookmaker adapters test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Bookmaker adapters test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=== Betslip Creation Helper Methods Test Suite ===")
    
    tests = [
        test_selection_creation,
        test_betslip_code_validation,
        test_odds_tolerance,
        test_bookmaker_adapters
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
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)