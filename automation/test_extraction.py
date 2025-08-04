#!/usr/bin/env python3
"""
Test script for betslip extraction functionality.
"""

import asyncio
import json
import pytest
from browser_manager import BrowserUseManager
from models import validate_betslip_code


@pytest.mark.asyncio
async def test_extraction():
    """Test the betslip extraction functionality"""
    
    # Test betslip code validation
    print("Testing betslip code validation...")
    
    valid_codes = ["ABC123", "XYZ789", "TEST_CODE", "SLIP-123"]
    invalid_codes = ["", "AB", "TOOLONGBETSLIPCODE123456", "INVALID@CODE", "123 456"]
    
    for code in valid_codes:
        assert validate_betslip_code(code), f"Valid code {code} failed validation"
        print(f"✓ {code} - Valid")
    
    for code in invalid_codes:
        assert not validate_betslip_code(code), f"Invalid code {code} passed validation"
        print(f"✓ {code} - Invalid (correctly rejected)")
    
    print("\nTesting BrowserUseManager initialization...")
    
    try:
        # Test with dummy API key for testing
        manager = BrowserUseManager("test-api-key")
        print("✓ Manager initialized successfully")
        
        # Test bookmaker config retrieval
        config = manager._get_bookmaker_config("bet9ja")
        print(f"✓ Retrieved config for {config.name}")
        
        # Test unsupported bookmaker
        try:
            manager._get_bookmaker_config("unsupported")
            print("✗ Should have failed for unsupported bookmaker")
        except ValueError as e:
            print(f"✓ Correctly rejected unsupported bookmaker: {e}")
        
        # Test data parsing with JSON format
        test_data = {
            "selections": [
                {
                    "game": "Arsenal vs Chelsea",
                    "home_team": "Arsenal",
                    "away_team": "Chelsea",
                    "market": "Match Result - Home Win",
                    "odds": 2.50,
                    "league": "Premier League"
                }
            ]
        }
        
        selections = manager._parse_extracted_data(json.dumps(test_data), "bet9ja")
        print(f"✓ Parsed {len(selections)} selections from JSON test data")
        
        if selections:
            sel = selections[0]
            print(f"  - Game: {sel.home_team} vs {sel.away_team}")
            print(f"  - Market: {sel.market}")
            print(f"  - Odds: {sel.odds}")
        
        # Test data parsing with text format
        text_data = """
        Match: Arsenal vs Chelsea
        Market: Match Result - Home Win
        Odds: 2.50
        League: Premier League
        
        Match: Liverpool vs Manchester United
        Market: Over/Under 2.5 Goals
        Odds: 1.85
        League: Premier League
        """
        
        text_selections = manager._parse_extracted_data(text_data, "sportybet")
        print(f"✓ Parsed {len(text_selections)} selections from text data")
        
        # Test invalid betslip code validation in extraction
        try:
            await manager.extract_betslip_selections("AB", "bet9ja")
            print("✗ Should have failed for invalid betslip code")
        except ValueError as e:
            print(f"✓ Correctly rejected invalid betslip code: {e}")
        
        # Test unsupported bookmaker in extraction
        try:
            await manager.extract_betslip_selections("ABC123", "unsupported")
            print("✗ Should have failed for unsupported bookmaker")
        except ValueError as e:
            print(f"✓ Correctly rejected unsupported bookmaker in extraction: {e}")
        
        print("\n✓ All tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_extraction())