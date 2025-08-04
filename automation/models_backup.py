"""
Data models for betslip conversion system.

This module contains dataclasses and validation functions for:
- Selection: Individual betting selections with game details, markets, and odds
- ConversionResult: API response objects for conversion operations
- BookmakerConfig: Configuration data for different bookmaker platforms
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
import re
from decimal import Decimal


@dataclass
class Selection:
    """
    Represents a single betting selection from a betslip.
    
    Attributes:
        game_id: Unique identifier for the game/match
        home_team: Name of the home team
        away_team: Name of the away team
        market: Type of bet (e.g., "Match Result", "Over/Under 2.5")
        odds: Decimal odds for the selection
        event_date: Date and time when the event takes place
        league: League or competition name
        original_text: Original text from the bookmaker's betslip
    """
    game_id: str
    home_team: str
    away_team: str
    market: str
    odds: float
    event_date: datetime
    league: str
    original_text: str
    
    def __post_init__(self):
        """Validate selection data after initialization."""
        validate_selection(self)


@dataclass
class ConversionResult:
    """
    Represents the result of a betslip conversion operation.
    
    Attributes:
        success: Whether the conversion was successful
        new_betslip_code: Generated betslip code on destination bookmaker
        converted_selections: List of successfully converted selections
        warnings: List of warning messages for partial conversions
        processing_time: Time taken to complete the conversion in seconds
        partial_conversion: Whether some selections couldn't be converted
        error_message: Error message if conversion failed
    """
    success: bool
    new_betslip_code: Optional[str] = None
    converted_selections: List[Selection] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    partial_conversion: bool = False
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate conversion result data after initialization."""
        validate_conversion_result(self)


@dataclass
class BookmakerConfig:
    """
    Configuration data for a specific bookmaker platform.
    
    Attributes:
        id: Unique identifier for the bookmaker
        name: Display name of the bookmaker
        base_url: Base URL of the bookmaker's website
        betslip_url_pattern: URL pattern for accessing betslips
        betting_url: URL for the betting page
        dom_selectors: Dictionary of CSS selectors for DOM elements
        market_mappings: Dictionary mapping market names to bookmaker-specific terms
        team_name_normalizations: Dictionary for normalizing team names
        supported: Whether this bookmaker is currently supported
    """
    id: str
    name: str
    base_url: str
    betslip_url_pattern: str
    betting_url: str
    dom_selectors: Dict[str, str] = field(default_factory=dict)
    market_mappings: Dict[str, str] = field(default_factory=dict)
    team_name_normalizations: Dict[str, str] = field(default_factory=dict)
    supported: bool = True
    
    def __post_init__(self):
        """Validate bookmaker configuration after initialization."""
        validate_bookmaker_config(self)


# Validation Functions

def validate_selection(selection: Selection) -> None:
    """
    Validate a Selection object for data integrity.
    
    Args:
        selection: Selection object to validate
        
    Raises:
        ValueError: If validation fails
    """
    if not selection.game_id or not isinstance(selection.game_id, str):
        raise ValueError("game_id must be a non-empty string")
    
    if not selection.home_team or not isinstance(selection.home_team, str):
        raise ValueError("home_team must be a non-empty string")
    
    if not selection.away_team or not isinstance(selection.away_team, str):
        raise ValueError("away_team must be a non-empty string")
    
    if not selection.market or not isinstance(selection.market, str):
        raise ValueError("market must be a non-empty string")
    
    if not isinstance(selection.odds, (int, float)) or selection.odds <= 0:
        raise ValueError("odds must be a positive number")
    
    if not isinstance(selection.event_date, datetime):
        raise ValueError("event_date must be a datetime object")
    
    if selection.event_date < datetime.now():
        raise ValueError("event_date cannot be in the past")
    
    if not selection.league or not isinstance(selection.league, str):
        raise ValueError("league must be a non-empty string")
    
    if not selection.original_text or not isinstance(selection.original_text, str):
        raise ValueError("original_text must be a non-empty string")


def validate_conversion_result(result: ConversionResult) -> None:
    """
    Validate a ConversionResult object for data integrity.
    
    Args:
        result: ConversionResult object to validate
        
    Raises:
        ValueError: If validation fails
    """
    if not isinstance(result.success, bool):
        raise ValueError("success must be a boolean")
    
    if result.success and not result.new_betslip_code:
        raise ValueError("new_betslip_code is required when success is True")
    
    if result.new_betslip_code and not isinstance(result.new_betslip_code, str):
        raise ValueError("new_betslip_code must be a string when provided")
    
    if not isinstance(result.converted_selections, list):
        raise ValueError("converted_selections must be a list")
    
    for selection in result.converted_selections:
        if not isinstance(selection, Selection):
            raise ValueError("All items in converted_selections must be Selection objects")
    
    if not isinstance(result.warnings, list):
        raise ValueError("warnings must be a list")
    
    for warning in result.warnings:
        if not isinstance(warning, str):
            raise ValueError("All warnings must be strings")
    
    if not isinstance(result.processing_time, (int, float)) or result.processing_time < 0:
        raise ValueError("processing_time must be a non-negative number")
    
    if not isinstance(result.partial_conversion, bool):
        raise ValueError("partial_conversion must be a boolean")
    
    if result.error_message and not isinstance(result.error_message, str):
        raise ValueError("error_message must be a string when provided")


def validate_bookmaker_config(config: BookmakerConfig) -> None:
    """
    Validate a BookmakerConfig object for data integrity.
    
    Args:
        config: BookmakerConfig object to validate
        
    Raises:
        ValueError: If validation fails
    """
    if not config.id or not isinstance(config.id, str):
        raise ValueError("id must be a non-empty string")
    
    if not config.name or not isinstance(config.name, str):
        raise ValueError("name must be a non-empty string")
    
    if not config.base_url or not isinstance(config.base_url, str):
        raise ValueError("base_url must be a non-empty string")
    
    # Validate URL format
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$'$', re.IGNORECASE)
    
    if not url_pattern.match(config.base_url):
        raise ValueError("base_url must be a valid URL")
    
    if not config.betslip_url_pattern or not isinstance(config.betslip_url_pattern, str):
        raise ValueError("betslip_url_pattern must be a non-empty string")
    
    if not config.betting_url or not isinstance(config.betting_url, str):
        raise ValueError("betting_url must be a non-empty string")
    
    if not url_pattern.match(config.betting_url):
        raise ValueError("betting_url must be a valid URL")
    
    if not isinstance(config.dom_selectors, dict):
        raise ValueError("dom_selectors must be a dictionary")
    
    if not isinstance(config.market_mappings, dict):
        raise ValueError("market_mappings must be a dictionary")
    
    if not isinstance(config.team_name_normalizations, dict):
        raise ValueError("team_name_normalizations must be a dictionary")
    
    if not isinstance(config.supported, bool):
        raise ValueError("supported must be a boolean")


def validate_betslip_code(betslip_code: str) -> bool:
    """
    Validate a betslip code format.
    
    Args:
        betslip_code: The betslip code to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(betslip_code, str):
        return False
    
    # Remove whitespace and check if not empty
    betslip_code = betslip_code.strip()
    if not betslip_code:
        return False
    
    # Check length (typically between 6-20 characters)
    if len(betslip_code) < 6 or len(betslip_code) > 20:
        return False
    
    # Check if alphanumeric (may include hyphens or underscores)
    if not re.match(r'^[A-Za-z0-9_-]+$'$', betslip_code):
        return False
    
    return True


def validate_odds_tolerance(original_odds: float, new_odds: float, tolerance: float = 0.05) -> bool:
    """
    Check if odds are within acceptable tolerance range.
    
    Args:
        original_odds: Original odds from source bookmaker
        new_odds: New odds from destination bookmaker
        tolerance: Acceptable difference threshold (default 0.05)
        
    Returns:
        bool: True if within tolerance, False otherwise
    """
    if not isinstance(original_odds, (int, float)) or not isinstance(new_odds, (int, float)):
        return False
    
    if original_odds <= 0 or new_odds <= 0:
        return False
    
    difference = abs(original_odds - new_odds)
    return difference <= tolerance