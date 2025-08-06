#!/usr/bin/env python3
"""
Test script for betslip creation functionality.
This script tests the create_betslip method with sample data.
"""

import asyncio
import sys
import os
import pytest
from datetime import datetime, timedelta
from browser_manager import BrowserUseManager
from models import Selection

@pytest.mark.asyncio
async def test_betslip_creation():
    """Test the betslip creation functionality with sample selections"""
    
    # Create sample selections for testing
    test_selections = [
        Selection(
            game_id="test_game_1",
            home_team="Manchester United",
            away_team="Liverpool",
            market="Match Result - Home Win",
            odds=2.50,
            event_date=datetime.now() + timedelta(hours=2),
            league="Premier League",
            original_text="Manchester United vs Liverpool - Match Result - Home Win @ 2.50"
        ),
        Selection(
            game_id="test_game_2", 
            home_team="Arsenal",
            away_team="Chelsea",
            market="Over/Under 2.5 Goals",
            odds=1.85,
            event_date=datetime.now() + timedelta(hours=4),
            league="Premier League",
            original_text="Arsenal vs Chelsea - Over/Under 2.5 Goals @ 1.85"
        )
    ]
    
    try:
        # Initialize browser manager
        manager = BrowserUseManager()
        
        print("Testing betslip creation functionality...")
        print(f"Test selections: {len(test_selections)}")
        
        for i, selection in enumerate(test_selections, 1):
            print(f"Selection {i}: {selection.home_team} vs {selection.away_team} - {selection.market} @ {selection.odds}")
        
        # Test with SportyBet as destination
        destination_bookmaker = "sportybet"
        print(f"\nTesting betslip creation on {destination_bookmaker}...")
        
        # Create betslip
        betslip_code = await manager.create_betslip(test_selections, destination_bookmaker)
        
        if betslip_code:
            print(f"✅ Betslip creation successful!")
            print(f"Generated betslip code: {betslip_code}")
            return True
        else:
            print("❌ Betslip creation failed - no code returned")
            return False
            
    except Exception as e:
        print(f"❌ Betslip creation test failed: {str(e)}")
        return False

# @pytest.mark.asyncio
# async def test_helper_methods():
#     """Test the helper methods for team name normalization and search variations"""
    
#     manager = BrowserUseManager()
    
#     print("\n=== Testing Helper Methods ===")
    
#     # Test team name normalization
#     test_teams = [
#         "Manchester United FC",
#         "Real Madrid C.F.",
#         "Liverpool F.C.",
#         "Arsenal FC"
#     ]
    
#     print("\nTeam name normalization:")
#     for team in test_teams:
#         normalized = manager._normalize_team_name(team)
#         print(f"  {team} -> {normalized}")
    
#     # Test market name normalization
#     test_markets = [
#         "Match Result",
#         "1X2",
#         "Over/Under 2.5",
#         "Both Teams to Score",
#         "BTTS"
#     ]
    
#     print("\nMarket name normalization:")
#     for market in test_markets:
#         normalized = manager._normalize_market_name(market, "sportybet")
#         print(f"  {market} -> {normalized}")
    
#     # Test search variations
#     print("\nSearch variations for 'Manchester United vs Liverpool':")
#     variations = manager._generate_search_variations("Manchester United", "Liverpool")
#     for i, variation in enumerate(variations[:5], 1):  # Show first 5
#         print(f"  {i}. {variation}")
    
#     print("✅ Helper methods test completed")

def main():
    """Main test function"""
    print("=== Betslip Creation Test Suite ===")
    
    # Check if OpenAI API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key to run this test")
        sys.exit(1)
    
    try:
        # Run helper methods test (synchronous)
        asyncio.run(test_helper_methods())
        
        # Run betslip creation test (asynchronous)
        success = asyncio.run(test_betslip_creation())
        
        if success:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()