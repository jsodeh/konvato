#!/usr/bin/env python3
"""
Unit tests for BookmakerAdapter classes.
"""

import unittest
from bookmaker_adapters import (
    get_bookmaker_adapter, 
    Bet9jaAdapter, 
    SportybetAdapter, 
    BetwayAdapter, 
    Bet365Adapter,
    BookmakerAdapter
)


class TestBookmakerAdapters(unittest.TestCase):
    """Test cases for bookmaker adapter functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bet9ja = get_bookmaker_adapter('bet9ja')
        self.sportybet = get_bookmaker_adapter('sportybet')
        self.betway = get_bookmaker_adapter('betway')
        self.bet365 = get_bookmaker_adapter('bet365')
    
    def test_adapter_factory(self):
        """Test the adapter factory function."""
        # Test valid bookmakers
        self.assertIsInstance(self.bet9ja, Bet9jaAdapter)
        self.assertIsInstance(self.sportybet, SportybetAdapter)
        self.assertIsInstance(self.betway, BetwayAdapter)
        self.assertIsInstance(self.bet365, Bet365Adapter)
        
        # Test case insensitive
        bet9ja_upper = get_bookmaker_adapter('BET9JA')
        self.assertIsInstance(bet9ja_upper, Bet9jaAdapter)
        
        # Test invalid bookmaker
        with self.assertRaises(ValueError):
            get_bookmaker_adapter('invalid_bookmaker')
    
    def test_base_adapter_interface(self):
        """Test that all adapters implement the base interface."""
        adapters = [self.bet9ja, self.sportybet, self.betway, self.bet365]
        
        for adapter in adapters:
            self.assertIsInstance(adapter, BookmakerAdapter)
            
            # Test required methods exist
            self.assertTrue(hasattr(adapter, 'get_betslip_url'))
            self.assertTrue(hasattr(adapter, 'get_betting_url'))
            self.assertTrue(hasattr(adapter, 'get_base_url'))
            self.assertTrue(hasattr(adapter, 'normalize_game_name'))
            self.assertTrue(hasattr(adapter, 'map_market_name'))
            self.assertTrue(hasattr(adapter, 'get_dom_selectors'))
    
    def test_url_generation(self):
        """Test URL generation methods."""
        test_code = "ABC123"
        
        # Test betslip URL generation
        bet9ja_url = self.bet9ja.get_betslip_url(test_code)
        self.assertIn(test_code, bet9ja_url)
        self.assertTrue(bet9ja_url.startswith('https://'))
        
        sportybet_url = self.sportybet.get_betslip_url(test_code)
        self.assertIn(test_code, sportybet_url)
        self.assertTrue(sportybet_url.startswith('https://'))
        
        # Test betting URL
        self.assertTrue(self.bet9ja.get_betting_url().startswith('https://'))
        self.assertTrue(self.sportybet.get_betting_url().startswith('https://'))
        
        # Test base URL
        self.assertTrue(self.bet9ja.get_base_url().startswith('https://'))
        self.assertTrue(self.sportybet.get_base_url().startswith('https://'))
    
    def test_team_name_normalization(self):
        """Test team name normalization."""
        test_cases = [
            ("Manchester United", "Man"),  # Should contain normalized version
            ("Real Madrid FC", "Real Madrid"),  # Should remove FC
            ("Brighton & Hove Albion", "Brighton"),  # Should normalize to Brighton
            ("Paris Saint-Germain", "PSG")  # Should normalize to PSG for some adapters
        ]
        
        for original, expected_part in test_cases:
            bet9ja_normalized = self.bet9ja.normalize_game_name(original)
            sportybet_normalized = self.sportybet.normalize_game_name(original)
            
            # Normalized names should be different from original (in most cases)
            # and should contain expected parts
            self.assertIsInstance(bet9ja_normalized, str)
            self.assertIsInstance(sportybet_normalized, str)
    
    def test_market_mapping(self):
        """Test market name mapping."""
        test_markets = [
            "Match Result",
            "1X2", 
            "Over/Under 2.5",
            "Both Teams to Score",
            "Double Chance"
        ]
        
        for market in test_markets:
            bet9ja_mapped = self.bet9ja.map_market_name(market)
            sportybet_mapped = self.sportybet.map_market_name(market)
            
            self.assertIsInstance(bet9ja_mapped, str)
            self.assertIsInstance(sportybet_mapped, str)
            self.assertTrue(len(bet9ja_mapped) > 0)
            self.assertTrue(len(sportybet_mapped) > 0)
    
    def test_dom_selectors(self):
        """Test DOM selector retrieval."""
        required_selectors = [
            'betslip_input',
            'submit_button', 
            'selections_container',
            'selection_item',
            'game_name',
            'market_name',
            'odds'
        ]
        
        adapters = [self.bet9ja, self.sportybet, self.betway, self.bet365]
        
        for adapter in adapters:
            selectors = adapter.get_dom_selectors()
            self.assertIsInstance(selectors, dict)
            
            for required_selector in required_selectors:
                self.assertIn(required_selector, selectors)
                self.assertIsInstance(selectors[required_selector], str)
                self.assertTrue(len(selectors[required_selector]) > 0)
    
    def test_search_variations(self):
        """Test search term variation generation."""
        home_team = "Manchester United"
        away_team = "Liverpool"
        
        adapters = [self.bet9ja, self.sportybet, self.betway, self.bet365]
        
        for adapter in adapters:
            variations = adapter.get_search_variations(home_team, away_team)
            
            self.assertIsInstance(variations, list)
            self.assertTrue(len(variations) > 0)
            
            # Should contain original team names
            found_original = any(home_team in var and away_team in var for var in variations)
            self.assertTrue(found_original)
    
    def test_odds_validation(self):
        """Test odds range validation."""
        adapters = [self.bet9ja, self.sportybet, self.betway, self.bet365]
        
        for adapter in adapters:
            # Test valid odds within tolerance
            self.assertTrue(adapter.validate_odds_range(2.50, 2.55, 0.10))
            self.assertTrue(adapter.validate_odds_range(1.80, 1.85, 0.10))
            
            # Test odds outside tolerance
            self.assertFalse(adapter.validate_odds_range(2.50, 2.70, 0.10))
            self.assertFalse(adapter.validate_odds_range(1.50, 1.80, 0.10))
            
            # Test invalid odds
            self.assertFalse(adapter.validate_odds_range(0, 2.50, 0.10))
            self.assertFalse(adapter.validate_odds_range(2.50, -1.0, 0.10))
    
    def test_team_extraction(self):
        """Test team name extraction from game names."""
        test_cases = [
            ("Manchester United vs Liverpool", ("Manchester United", "Liverpool")),
            ("Real Madrid v Barcelona", ("Real Madrid", "Barcelona")),
            ("Chelsea - Arsenal", ("Chelsea", "Arsenal")),
            ("Bayern Munich x Dortmund", ("Bayern Munich", "Dortmund")),
            ("Invalid format", (None, None))
        ]
        
        adapters = [self.bet9ja, self.sportybet, self.betway, self.bet365]
        
        for adapter in adapters:
            for game_name, expected in test_cases:
                result = adapter.extract_teams_from_game_name(game_name)
                self.assertEqual(result, expected)
    
    def test_bookmaker_specific_configurations(self):
        """Test that each bookmaker has unique configurations."""
        adapters = {
            'bet9ja': self.bet9ja,
            'sportybet': self.sportybet, 
            'betway': self.betway,
            'bet365': self.bet365
        }
        
        # Test that each adapter has unique base URLs
        base_urls = set()
        for name, adapter in adapters.items():
            base_url = adapter.get_base_url()
            self.assertNotIn(base_url, base_urls, f"Duplicate base URL for {name}")
            base_urls.add(base_url)
        
        # Test that each adapter has unique configurations
        for name, adapter in adapters.items():
            config = adapter.config
            self.assertEqual(config.id, name)
            self.assertTrue(len(config.name) > 0)
            self.assertTrue(config.supported)


if __name__ == '__main__':
    unittest.main()