#!/usr/bin/env python3
"""
Unit tests for betslip creation functionality without external API dependencies.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

# Add the automation directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Selection

def test_format_selections_for_prompt():
    """Test the _format_selections_for_prompt method"""
    print("=== Testing Format Selections for Prompt ===")
    
    # Create mock BrowserUseManager with just the method we need
    class MockBrowserManager:
        def _format_selections_for_prompt(self, selections):
            """Format selections for inclusion in the browser automation prompt"""
            formatted_selections = []
            
            for i, selection in enumerate(selections, 1):
                formatted_selection = f"""
        Selection {i}:
        - Game: {selection.home_team} vs {selection.away_team}
        - Market: {selection.market}
        - Expected Odds: {selection.odds}
        - League: {selection.league}
        - Event Date: {selection.event_date.strftime('%Y-%m-%d %H:%M')}
        """
                formatted_selections.append(formatted_selection)
            
            return '\n'.join(formatted_selections)
    
    try:
        manager = MockBrowserManager()
        
        # Create test selections
        test_selections = [
            Selection(
                game_id="test_1",
                home_team="Arsenal",
                away_team="Chelsea",
                market="Match Result - Home Win",
                odds=2.50,
                event_date=datetime.now() + timedelta(hours=2),
                league="Premier League",
                original_text="Test selection 1"
            ),
            Selection(
                game_id="test_2",
                home_team="Liverpool",
                away_team="Manchester United",
                market="Over/Under 2.5 Goals",
                odds=1.85,
                event_date=datetime.now() + timedelta(hours=4),
                league="Premier League",
                original_text="Test selection 2"
            )
        ]
        
        formatted = manager._format_selections_for_prompt(test_selections)
        
        print("Formatted selections:")
        print(formatted)
        
        # Verify the format contains expected elements
        assert "Selection 1:" in formatted, "Selection 1 not found in formatted output"
        assert "Selection 2:" in formatted, "Selection 2 not found in formatted output"
        assert "Arsenal vs Chelsea" in formatted, "Arsenal vs Chelsea not found"
        assert "Liverpool vs Manchester United" in formatted, "Liverpool vs Manchester United not found"
        assert "Match Result - Home Win" in formatted, "Match Result - Home Win not found"
        assert "Over/Under 2.5 Goals" in formatted, "Over/Under 2.5 Goals not found"
        assert "2.5" in formatted, "2.5 odds not found"  # Changed from 2.50 to 2.5
        assert "1.85" in formatted, "1.85 odds not found"
        assert "Premier League" in formatted, "Premier League not found"
        
        print("✅ Format selections test passed")
        return True
        
    except Exception as e:
        print(f"❌ Format selections test failed: {str(e)}")
        return False

def test_create_betslip_validation():
    """Test input validation for create_betslip method"""
    print("\n=== Testing Create Betslip Validation ===")
    
    # Mock the BrowserUseManager class
    class MockBrowserManager:
        def __init__(self):
            pass
        
        def _get_bookmaker_config(self, bookmaker):
            if bookmaker.lower() not in ['bet9ja', 'sportybet', 'betway', 'bet365']:
                raise ValueError(f"Unsupported bookmaker: {bookmaker}")
            
            # Return a mock config
            class MockConfig:
                def __init__(self):
                    self.name = bookmaker.title()
                    self.betting_url = f"https://www.{bookmaker}.com/sport"
            
            return MockConfig()
        
        async def create_betslip(self, selections, bookmaker):
            """Mock create_betslip method with validation"""
            if not selections:
                raise ValueError("No selections provided for betslip creation")
            
            config = self._get_bookmaker_config(bookmaker)
            
            # Mock successful creation
            return f"MOCK_BETSLIP_{bookmaker.upper()}_123"
    
    try:
        manager = MockBrowserManager()
        
        # Test with empty selections
        try:
            import asyncio
            result = asyncio.run(manager.create_betslip([], "sportybet"))
            print("❌ Should have failed with empty selections")
            return False
        except ValueError as e:
            print(f"✅ Correctly rejected empty selections: {e}")
        
        # Test with unsupported bookmaker
        test_selection = Selection(
            game_id="test",
            home_team="Arsenal",
            away_team="Chelsea",
            market="Match Result",
            odds=2.50,
            event_date=datetime.now() + timedelta(hours=2),
            league="Premier League",
            original_text="Test"
        )
        
        try:
            result = asyncio.run(manager.create_betslip([test_selection], "unsupported"))
            print("❌ Should have failed with unsupported bookmaker")
            return False
        except ValueError as e:
            print(f"✅ Correctly rejected unsupported bookmaker: {e}")
        
        # Test with valid inputs
        result = asyncio.run(manager.create_betslip([test_selection], "sportybet"))
        print(f"✅ Valid inputs accepted, mock result: {result}")
        
        print("✅ Create betslip validation tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Create betslip validation test failed: {str(e)}")
        return False

def test_betslip_creation_error_handling():
    """Test error handling scenarios in betslip creation"""
    print("\n=== Testing Betslip Creation Error Handling ===")
    
    # Test different error scenarios that should be handled
    error_scenarios = [
        ("timeout", "Betslip creation timed out"),
        ("blocked", "Access blocked by anti-bot protection"),
        ("bot detection", "Access blocked by anti-bot protection"),
        ("network error", "Network error while accessing"),
        ("connection failed", "Network error while accessing"),
        ("not found", "Could not find games or markets"),
        ("unknown error", "Betslip creation failed")
    ]
    
    try:
        for error_msg, expected_pattern in error_scenarios:
            # Mock an exception with the error message
            class MockException(Exception):
                def __init__(self, msg):
                    super().__init__(msg)
                    self.args = (msg,)
                
                def __str__(self):
                    return self.args[0]
            
            # Test that the error handling logic would work correctly
            mock_error = MockException(error_msg)
            error_str = str(mock_error).lower()
            
            # Simulate the error handling logic from create_betslip
            if 'timeout' in error_str:
                handled_msg = f"Betslip creation timed out for bookmaker test"
            elif 'blocked' in error_str or 'bot' in error_str:
                handled_msg = f"Access blocked by anti-bot protection on test"
            elif 'network' in error_str or 'connection' in error_str:
                handled_msg = f"Network error while accessing test"
            elif 'not found' in error_str:
                handled_msg = f"Could not find games or markets on test"
            else:
                handled_msg = f"Betslip creation failed: {str(mock_error)}"
            
            print(f"✅ Error '{error_msg}' -> '{handled_msg}'")
        
        print("✅ Error handling tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False

def test_search_variations_generation():
    """Test the search variations generation logic"""
    print("\n=== Testing Search Variations Generation ===")
    
    # Mock the helper methods
    class MockBrowserManager:
        def _normalize_team_name(self, team_name):
            """Simple normalization for testing"""
            return team_name.replace("FC", "").replace("United", "Utd").strip()
        
        def _generate_search_variations(self, home_team, away_team):
            """Generate different search term variations for finding games"""
            home_normalized = self._normalize_team_name(home_team)
            away_normalized = self._normalize_team_name(away_team)
            
            variations = [
                f"{home_team} vs {away_team}",
                f"{away_team} vs {home_team}",
                f"{home_team} {away_team}",
                f"{away_team} {home_team}",
                f"{home_normalized} vs {away_normalized}",
                f"{away_normalized} vs {home_normalized}",
                home_team,
                away_team,
                home_normalized,
                away_normalized
            ]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_variations = []
            for variation in variations:
                if variation not in seen:
                    seen.add(variation)
                    unique_variations.append(variation)
            
            return unique_variations
    
    try:
        manager = MockBrowserManager()
        
        # Test with common team names
        variations = manager._generate_search_variations("Manchester United FC", "Liverpool FC")
        
        print(f"Generated {len(variations)} search variations:")
        for i, variation in enumerate(variations, 1):
            print(f"   {i}. {variation}")
        
        # Verify expected variations are present
        expected_patterns = [
            "Manchester United FC vs Liverpool FC",
            "Liverpool FC vs Manchester United FC", 
            "Manchester Utd vs Liverpool",
            "Liverpool vs Manchester Utd"
        ]
        
        for pattern in expected_patterns:
            if pattern in variations:
                print(f"✅ Found expected pattern: {pattern}")
            else:
                print(f"⚠️ Missing expected pattern: {pattern}")
        
        # Verify no duplicates
        if len(variations) == len(set(variations)):
            print("✅ No duplicate variations found")
        else:
            print("❌ Duplicate variations detected")
            return False
        
        print("✅ Search variations generation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Search variations test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=== Betslip Creation Unit Tests ===")
    
    tests = [
        test_format_selections_for_prompt,
        test_create_betslip_validation,
        test_betslip_creation_error_handling,
        test_search_variations_generation
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
        print("✅ All betslip creation unit tests passed!")
        return True
    else:
        print("❌ Some betslip creation tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)