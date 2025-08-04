#!/usr/bin/env python3
"""
Comprehensive unit tests for the models module.
Tests data validation, edge cases, and error handling for all model classes.
"""

import sys
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

# Add the automation directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    Selection, ConversionResult, BookmakerConfig,
    validate_selection, validate_conversion_result, validate_bookmaker_config,
    validate_betslip_code, validate_odds_tolerance
)


class TestSelectionModel:
    """Test cases for Selection model and validation."""
    
    def test_valid_selection_creation(self):
        """Test creating a valid Selection object."""
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
        
        assert selection.game_id == "test_game_1"
        assert selection.home_team == "Manchester United"
        assert selection.away_team == "Liverpool"
        assert selection.market == "Match Result"
        assert selection.odds == 2.50
        assert selection.league == "Premier League"
        assert isinstance(selection.event_date, datetime)
    
    def test_selection_validation_empty_game_id(self):
        """Test Selection validation with empty game_id."""
        with pytest.raises(ValueError, match="game_id must be a non-empty string"):
            Selection(
                game_id="",
                home_team="Manchester United",
                away_team="Liverpool",
                market="Match Result",
                odds=2.50,
                event_date=datetime.now() + timedelta(hours=2),
                league="Premier League",
                original_text="Test"
            )
    
    def test_selection_validation_invalid_odds(self):
        """Test Selection validation with invalid odds."""
        with pytest.raises(ValueError, match="odds must be a positive number"):
            Selection(
                game_id="test_game_1",
                home_team="Manchester United",
                away_team="Liverpool",
                market="Match Result",
                odds=-1.0,
                event_date=datetime.now() + timedelta(hours=2),
                league="Premier League",
                original_text="Test"
            )
    
    def test_selection_validation_past_event_date(self):
        """Test Selection validation with past event date."""
        with pytest.raises(ValueError, match="event_date cannot be in the past"):
            Selection(
                game_id="test_game_1",
                home_team="Manchester United",
                away_team="Liverpool",
                market="Match Result",
                odds=2.50,
                event_date=datetime.now() - timedelta(hours=1),
                league="Premier League",
                original_text="Test"
            )
    
    def test_selection_validation_non_string_fields(self):
        """Test Selection validation with non-string fields."""
        with pytest.raises(ValueError, match="home_team must be a non-empty string"):
            Selection(
                game_id="test_game_1",
                home_team=123,
                away_team="Liverpool",
                market="Match Result",
                odds=2.50,
                event_date=datetime.now() + timedelta(hours=2),
                league="Premier League",
                original_text="Test"
            )


class TestConversionResultModel:
    """Test cases for ConversionResult model and validation."""
    
    def test_valid_conversion_result_success(self):
        """Test creating a valid successful ConversionResult."""
        selection = Selection(
            game_id="test_game_1",
            home_team="Manchester United",
            away_team="Liverpool",
            market="Match Result",
            odds=2.50,
            event_date=datetime.now() + timedelta(hours=2),
            league="Premier League",
            original_text="Test"
        )
        
        result = ConversionResult(
            success=True,
            new_betslip_code="ABC123",
            converted_selections=[selection],
            warnings=["Minor odds difference"],
            processing_time=5.2,
            partial_conversion=False
        )
        
        assert result.success is True
        assert result.new_betslip_code == "ABC123"
        assert len(result.converted_selections) == 1
        assert len(result.warnings) == 1
        assert result.processing_time == 5.2
        assert result.partial_conversion is False
    
    def test_valid_conversion_result_failure(self):
        """Test creating a valid failed ConversionResult."""
        result = ConversionResult(
            success=False,
            error_message="Betslip not found",
            processing_time=2.1
        )
        
        assert result.success is False
        assert result.new_betslip_code is None
        assert len(result.converted_selections) == 0
        assert len(result.warnings) == 0
        assert result.error_message == "Betslip not found"
    
    def test_conversion_result_validation_missing_betslip_code(self):
        """Test ConversionResult validation when success=True but no betslip code."""
        with pytest.raises(ValueError, match="new_betslip_code is required when success is True"):
            ConversionResult(
                success=True,
                processing_time=5.0
            )
    
    def test_conversion_result_validation_invalid_selections(self):
        """Test ConversionResult validation with invalid selections."""
        with pytest.raises(ValueError, match="All items in converted_selections must be Selection objects"):
            ConversionResult(
                success=True,
                new_betslip_code="ABC123",
                converted_selections=["invalid_selection"],
                processing_time=5.0
            )
    
    def test_conversion_result_validation_negative_processing_time(self):
        """Test ConversionResult validation with negative processing time."""
        with pytest.raises(ValueError, match="processing_time must be a non-negative number"):
            ConversionResult(
                success=False,
                processing_time=-1.0
            )


class TestBookmakerConfigModel:
    """Test cases for BookmakerConfig model and validation."""
    
    def test_valid_bookmaker_config(self):
        """Test creating a valid BookmakerConfig."""
        config = BookmakerConfig(
            id="bet9ja",
            name="Bet9ja",
            base_url="https://www.bet9ja.com",
            betslip_url_pattern="https://www.bet9ja.com/betslip/{code}",
            betting_url="https://www.bet9ja.com/sport",
            dom_selectors={
                "betslip_input": "#betslip-code",
                "submit_button": ".submit-btn"
            },
            market_mappings={
                "Match Result": "1X2",
                "Over/Under 2.5": "O/U 2.5"
            },
            team_name_normalizations={
                "Manchester United": "Man Utd",
                "Liverpool": "Liverpool FC"
            },
            supported=True
        )
        
        assert config.id == "bet9ja"
        assert config.name == "Bet9ja"
        assert config.base_url == "https://www.bet9ja.com"
        assert config.supported is True
        assert isinstance(config.dom_selectors, dict)
        assert isinstance(config.market_mappings, dict)
    
    def test_bookmaker_config_validation_invalid_url(self):
        """Test BookmakerConfig validation with invalid URL."""
        with pytest.raises(ValueError, match="base_url must be a valid URL"):
            BookmakerConfig(
                id="test",
                name="Test",
                base_url="invalid-url",
                betslip_url_pattern="https://test.com/{code}",
                betting_url="https://test.com/sport"
            )
    
    def test_bookmaker_config_validation_empty_id(self):
        """Test BookmakerConfig validation with empty ID."""
        with pytest.raises(ValueError, match="id must be a non-empty string"):
            BookmakerConfig(
                id="",
                name="Test",
                base_url="https://test.com",
                betslip_url_pattern="https://test.com/{code}",
                betting_url="https://test.com/sport"
            )
    
    def test_bookmaker_config_validation_non_dict_selectors(self):
        """Test BookmakerConfig validation with non-dict selectors."""
        with pytest.raises(ValueError, match="dom_selectors must be a dictionary"):
            BookmakerConfig(
                id="test",
                name="Test",
                base_url="https://test.com",
                betslip_url_pattern="https://test.com/{code}",
                betting_url="https://test.com/sport",
                dom_selectors="invalid"
            )


class TestValidationFunctions:
    """Test cases for standalone validation functions."""
    
    def test_validate_betslip_code_valid_codes(self):
        """Test validate_betslip_code with valid codes."""
        valid_codes = [
            "ABC123DEF",
            "12345678",
            "TEST-CODE-123",
            "TEST_CODE_123",
            "ABCDEF",
            "123456789012345"
        ]
        
        for code in valid_codes:
            assert validate_betslip_code(code) is True, f"Code {code} should be valid"
    
    def test_validate_betslip_code_invalid_codes(self):
        """Test validate_betslip_code with invalid codes."""
        invalid_codes = [
            "",  # Empty
            "ABC",  # Too short
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",  # Too long
            "ABC@123",  # Invalid characters
            "ABC 123",  # Space
            123,  # Non-string
            None,  # None
            "ABC#123"  # Hash character
        ]
        
        for code in invalid_codes:
            assert validate_betslip_code(code) is False, f"Code {code} should be invalid"
    
    def test_validate_odds_tolerance_within_range(self):
        """Test validate_odds_tolerance with odds within tolerance."""
        test_cases = [
            (2.50, 2.45, 0.05, True),
            (2.50, 2.55, 0.05, True),
            (1.50, 1.50, 0.05, True),  # Exact match
            (2.00, 1.95, 0.10, True),  # Custom tolerance
        ]
        
        for orig, new, tolerance, expected in test_cases:
            result = validate_odds_tolerance(orig, new, tolerance)
            assert result == expected, f"Odds {orig} vs {new} with tolerance {tolerance} should be {expected}"
    
    def test_validate_odds_tolerance_outside_range(self):
        """Test validate_odds_tolerance with odds outside tolerance."""
        test_cases = [
            (2.50, 2.60, 0.05, False),
            (2.50, 2.35, 0.05, False),
            (1.50, 1.80, 0.10, False),
            (0, 2.50, 0.05, False),  # Invalid original odds
            (2.50, 0, 0.05, False),  # Invalid new odds
            ("2.50", 2.45, 0.05, False),  # Non-numeric input
        ]
        
        for orig, new, tolerance, expected in test_cases:
            result = validate_odds_tolerance(orig, new, tolerance)
            assert result == expected, f"Odds {orig} vs {new} with tolerance {tolerance} should be {expected}"
    
    def test_validate_selection_function(self):
        """Test standalone validate_selection function."""
        valid_selection = Selection(
            game_id="test_game_1",
            home_team="Manchester United",
            away_team="Liverpool",
            market="Match Result",
            odds=2.50,
            event_date=datetime.now() + timedelta(hours=2),
            league="Premier League",
            original_text="Test"
        )
        
        # Should not raise any exception
        validate_selection(valid_selection)
        
        # Test with invalid selection
        invalid_selection = Selection(
            game_id="test_game_1",
            home_team="Manchester United",
            away_team="Liverpool",
            market="Match Result",
            odds=2.50,
            event_date=datetime.now() + timedelta(hours=2),
            league="Premier League",
            original_text="Test"
        )
        
        # Manually set invalid odds to bypass __post_init__
        invalid_selection.odds = -1.0
        
        with pytest.raises(ValueError, match="odds must be a positive number"):
            validate_selection(invalid_selection)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_selection_with_minimum_valid_odds(self):
        """Test Selection with minimum valid odds."""
        selection = Selection(
            game_id="test_game_1",
            home_team="Manchester United",
            away_team="Liverpool",
            market="Match Result",
            odds=0.01,  # Very small but positive
            event_date=datetime.now() + timedelta(seconds=1),  # Just in the future
            league="Premier League",
            original_text="Test"
        )
        
        assert selection.odds == 0.01
    
    def test_selection_with_very_high_odds(self):
        """Test Selection with very high odds."""
        selection = Selection(
            game_id="test_game_1",
            home_team="Manchester United",
            away_team="Liverpool",
            market="Match Result",
            odds=999.99,
            event_date=datetime.now() + timedelta(hours=2),
            league="Premier League",
            original_text="Test"
        )
        
        assert selection.odds == 999.99
    
    def test_conversion_result_with_empty_lists(self):
        """Test ConversionResult with empty lists."""
        result = ConversionResult(
            success=False,
            converted_selections=[],
            warnings=[],
            processing_time=0.0
        )
        
        assert len(result.converted_selections) == 0
        assert len(result.warnings) == 0
        assert result.processing_time == 0.0
    
    def test_bookmaker_config_with_empty_dicts(self):
        """Test BookmakerConfig with empty dictionaries."""
        config = BookmakerConfig(
            id="test",
            name="Test",
            base_url="https://test.com",
            betslip_url_pattern="https://test.com/{code}",
            betting_url="https://test.com/sport",
            dom_selectors={},
            market_mappings={},
            team_name_normalizations={}
        )
        
        assert len(config.dom_selectors) == 0
        assert len(config.market_mappings) == 0
        assert len(config.team_name_normalizations) == 0
    
    def test_betslip_code_boundary_lengths(self):
        """Test betslip code validation at boundary lengths."""
        # Minimum valid length (6 characters)
        assert validate_betslip_code("ABCDEF") is True
        
        # Just below minimum (5 characters)
        assert validate_betslip_code("ABCDE") is False
        
        # Maximum valid length (20 characters)
        assert validate_betslip_code("A" * 20) is True
        
        # Just above maximum (21 characters)
        assert validate_betslip_code("A" * 21) is False
    
    def test_odds_tolerance_boundary_values(self):
        """Test odds tolerance validation at boundary values."""
        # Exactly at tolerance boundary
        assert validate_odds_tolerance(2.50, 2.55, 0.05) is True
        assert validate_odds_tolerance(2.50, 2.45, 0.05) is True
        
        # Just outside tolerance boundary
        assert validate_odds_tolerance(2.50, 2.551, 0.05) is False
        assert validate_odds_tolerance(2.50, 2.449, 0.05) is False


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])