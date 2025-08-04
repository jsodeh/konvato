#!/usr/bin/env python3
"""
Integration test for BookmakerAdapter classes with BrowserUseManager.
This test verifies that the adapter system integrates correctly with the browser manager.
"""

import sys
import os
from unittest.mock import Mock, patch

# Add the automation directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bookmaker_adapters import get_bookmaker_adapter

# Mock browser_use module to avoid dependency issues
sys.modules['browser_use'] = Mock()
sys.modules['langchain_openai'] = Mock()

# Now we can import browser_manager
from browser_manager import BrowserUseManager


def test_adapter_integration():
    """Test that BrowserUseManager correctly uses the adapter system."""
    print("=== Testing Adapter Integration with BrowserUseManager ===")
    
    try:
        # Mock the OpenAI API key to avoid requiring actual key for this test
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            # Create BrowserUseManager instance
            manager = BrowserUseManager()
            
            # Test that manager can get adapters for all supported bookmakers
            bookmakers = ['bet9ja', 'sportybet', 'betway', 'bet365']
            
            for bookmaker in bookmakers:
                print(f"\nTesting {bookmaker} adapter integration:")
                
                # Test that manager can get the adapter
                adapter = manager._get_bookmaker_adapter(bookmaker)
                print(f"  ✅ Successfully created {bookmaker} adapter")
                
                # Test that adapter has correct configuration
                config = adapter.config
                print(f"  ✅ Adapter config: {config.name} ({config.id})")
                
                # Test URL generation
                betslip_url = adapter.get_betslip_url("TEST123")
                betting_url = adapter.get_betting_url()
                print(f"  ✅ URLs generated successfully")
                
                # Test DOM selectors
                selectors = adapter.get_dom_selectors()
                required_selectors = ['betslip_input', 'submit_button', 'selections_container']
                for selector in required_selectors:
                    if selector not in selectors:
                        raise ValueError(f"Missing required selector: {selector}")
                print(f"  ✅ DOM selectors validated ({len(selectors)} selectors)")
                
                # Test team name normalization
                test_team = "Manchester United FC"
                normalized = adapter.normalize_game_name(test_team)
                print(f"  ✅ Team normalization: '{test_team}' -> '{normalized}'")
                
                # Test market mapping
                test_market = "Match Result"
                mapped = adapter.map_market_name(test_market)
                print(f"  ✅ Market mapping: '{test_market}' -> '{mapped}'")
                
                # Test search variations
                variations = adapter.get_search_variations("Arsenal", "Chelsea")
                print(f"  ✅ Search variations generated: {len(variations)} variations")
        
        print("\n✅ All adapter integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Adapter integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_adapter_error_handling():
    """Test error handling in adapter system."""
    print("\n=== Testing Adapter Error Handling ===")
    
    try:
        # Test invalid bookmaker
        try:
            get_bookmaker_adapter('invalid_bookmaker')
            print("❌ Should have raised ValueError for invalid bookmaker")
            return False
        except ValueError as e:
            print(f"✅ Correctly raised ValueError for invalid bookmaker: {str(e)}")
        
        # Test case insensitive bookmaker names
        adapters = []
        test_cases = ['BET9JA', 'bet9ja', 'Bet9ja', 'BET9ja']
        for case in test_cases:
            adapter = get_bookmaker_adapter(case)
            adapters.append(adapter)
        
        # All should be the same type
        adapter_types = [type(adapter) for adapter in adapters]
        if len(set(adapter_types)) != 1:
            print("❌ Case insensitive handling failed")
            return False
        
        print("✅ Case insensitive bookmaker names handled correctly")
        
        print("✅ All error handling tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False


def test_adapter_consistency():
    """Test that all adapters have consistent interfaces."""
    print("\n=== Testing Adapter Consistency ===")
    
    try:
        bookmakers = ['bet9ja', 'sportybet', 'betway', 'bet365']
        adapters = [get_bookmaker_adapter(bm) for bm in bookmakers]
        
        # Test that all adapters have the same interface
        required_methods = [
            'get_betslip_url',
            'get_betting_url', 
            'get_base_url',
            'normalize_game_name',
            'map_market_name',
            'get_dom_selectors',
            'get_search_variations',
            'validate_odds_range',
            'extract_teams_from_game_name'
        ]
        
        for adapter in adapters:
            for method in required_methods:
                if not hasattr(adapter, method):
                    print(f"❌ Adapter {adapter.config.id} missing method: {method}")
                    return False
                if not callable(getattr(adapter, method)):
                    print(f"❌ Adapter {adapter.config.id} method not callable: {method}")
                    return False
        
        print(f"✅ All {len(adapters)} adapters have consistent interfaces")
        
        # Test that all adapters have required DOM selectors
        required_selectors = [
            'betslip_input',
            'submit_button',
            'selections_container',
            'selection_item',
            'game_name',
            'market_name',
            'odds'
        ]
        
        for adapter in adapters:
            selectors = adapter.get_dom_selectors()
            for selector in required_selectors:
                if selector not in selectors:
                    print(f"❌ Adapter {adapter.config.id} missing selector: {selector}")
                    return False
        
        print(f"✅ All adapters have required DOM selectors")
        
        # Test that all adapters have unique base URLs
        base_urls = [adapter.get_base_url() for adapter in adapters]
        if len(set(base_urls)) != len(base_urls):
            print("❌ Adapters have duplicate base URLs")
            return False
        
        print("✅ All adapters have unique base URLs")
        
        print("✅ All consistency tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Consistency test failed: {str(e)}")
        return False


def main():
    """Main test function."""
    print("=== BookmakerAdapter Integration Test Suite ===")
    
    tests = [
        test_adapter_integration,
        test_adapter_error_handling,
        test_adapter_consistency
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
        print("✅ All integration tests passed!")
        return True
    else:
        print("❌ Some integration tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)