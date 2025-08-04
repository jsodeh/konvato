"""
BookmakerAdapter classes for different bookmaker platforms.

This module provides adapter classes for each supported bookmaker with:
- URL patterns and DOM selectors
- Market mappings and team name normalizations  
- Bookmaker-specific configurations
- Base adapter interface with common functionality
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass
from models import BookmakerConfig


class BookmakerAdapter(ABC):
    """
    Base adapter interface with common functionality for all bookmakers.
    
    This abstract base class defines the interface that all bookmaker adapters
    must implement, providing common functionality for URL generation, 
    team name normalization, market mapping, and DOM selector management.
    """
    
    def __init__(self):
        self.config = self._get_config()
    
    @abstractmethod
    def _get_config(self) -> BookmakerConfig:
        """Get the bookmaker-specific configuration."""
        pass
    
    def get_betslip_url(self, betslip_code: str) -> str:
        """
        Generate the URL for accessing a specific betslip.
        
        Args:
            betslip_code: The betslip code to access
            
        Returns:
            Complete URL for the betslip
        """
        return self.config.betslip_url_pattern.format(code=betslip_code)
    
    def get_betting_url(self) -> str:
        """
        Get the main betting page URL.
        
        Returns:
            URL for the main betting/sports page
        """
        return self.config.betting_url
    
    def get_base_url(self) -> str:
        """
        Get the base URL of the bookmaker.
        
        Returns:
            Base URL of the bookmaker website
        """
        return self.config.base_url
    
    def normalize_game_name(self, game_name: str) -> str:
        """
        Normalize game names for better matching across bookmakers.
        
        Args:
            game_name: Original game name from the bookmaker
            
        Returns:
            Normalized game name
        """
        # Apply bookmaker-specific normalizations first
        normalized = game_name.strip()
        
        for original, replacement in self.config.team_name_normalizations.items():
            normalized = normalized.replace(original, replacement)
        
        # Apply common normalizations
        normalized = self._apply_common_normalizations(normalized)
        
        return normalized
    
    def _apply_common_normalizations(self, name: str) -> str:
        """Apply common team name normalizations."""
        # Remove common prefixes/suffixes
        common_normalizations = {
            r'\bFC\b': '',
            r'\bF\.C\.\b': '',
            r'\bF\.C\b': '',
            r'\bUnited\b': 'Utd',
            r'\bAthletic\b': 'Ath',
            r'\bAthletics\b': 'Ath',
            r'\bReal\b': 'R.',
            r'\bClub\b': 'C.',
            r'\bSporting\b': 'Sport',
            r'\bInternacional\b': 'Int',
            r'\bManchester\b': 'Man',
            r'\bLiverpool\b': 'Pool'
        }
        
        for pattern, replacement in common_normalizations.items():
            name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)
        
        # Clean up extra spaces and special characters
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'[^\w\s]', '', name)
        
        return name
    
    def map_market_name(self, market: str) -> str:
        """
        Map market names to bookmaker-specific terms.
        
        Args:
            market: Original market name
            
        Returns:
            Mapped market name for this bookmaker
        """
        market_lower = market.lower().strip()
        
        # Check bookmaker-specific mappings first
        for standard_market, bookmaker_market in self.config.market_mappings.items():
            if market_lower == standard_market.lower():
                return bookmaker_market
            if market_lower in standard_market.lower() or standard_market.lower() in market_lower:
                return bookmaker_market
        
        # Apply common market mappings
        return self._apply_common_market_mappings(market)
    
    def _apply_common_market_mappings(self, market: str) -> str:
        """Apply common market name mappings."""
        market_lower = market.lower().strip()
        
        # Common market mappings
        common_mappings = {
            'match result': ['1x2', 'full time result', 'winner', 'match winner'],
            '1x2': ['match result', 'full time result', 'winner'],
            'over/under 2.5': ['total goals over/under 2.5', 'o/u 2.5', 'total goals o/u 2.5'],
            'both teams to score': ['btts', 'both teams to score - yes', 'gg'],
            'double chance': ['dc', '1x', '12', 'x2'],
            'handicap': ['asian handicap', 'ah', 'spread'],
            'correct score': ['exact score', 'final score']
        }
        
        for standard_market, variations in common_mappings.items():
            if market_lower in variations or any(var in market_lower for var in variations):
                return standard_market
            if standard_market in market_lower:
                return standard_market
        
        return market
    
    def get_dom_selectors(self) -> Dict[str, str]:
        """
        Get DOM selectors for this bookmaker.
        
        Returns:
            Dictionary of CSS selectors for various page elements
        """
        return self.config.dom_selectors.copy()
    
    def get_search_variations(self, home_team: str, away_team: str) -> List[str]:
        """
        Generate search term variations for finding games.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            
        Returns:
            List of search term variations
        """
        home_normalized = self.normalize_game_name(home_team)
        away_normalized = self.normalize_game_name(away_team)
        
        variations = [
            f"{home_team} vs {away_team}",
            f"{away_team} vs {home_team}",
            f"{home_team} {away_team}",
            f"{away_team} {home_team}",
            f"{home_normalized} vs {away_normalized}",
            f"{away_normalized} vs {home_normalized}",
            f"{home_normalized} {away_normalized}",
            f"{away_normalized} {home_normalized}",
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
    
    def validate_odds_range(self, odds: float, expected_odds: float, tolerance: float = 0.10) -> bool:
        """
        Validate if odds are within acceptable range.
        
        Args:
            odds: Actual odds found
            expected_odds: Expected odds from source
            tolerance: Acceptable difference (default 0.10)
            
        Returns:
            True if odds are within tolerance, False otherwise
        """
        if odds <= 0 or expected_odds <= 0:
            return False
        
        difference = abs(odds - expected_odds)
        return difference <= tolerance
    
    def extract_teams_from_game_name(self, game_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract home and away team names from a game name string.
        
        Args:
            game_name: Full game name (e.g., "Team A vs Team B")
            
        Returns:
            Tuple of (home_team, away_team) or (None, None) if extraction fails
        """
        # Common separators
        separators = [' vs ', ' v ', ' - ', ' x ']
        
        for separator in separators:
            if separator in game_name:
                teams = game_name.split(separator, 1)
                if len(teams) == 2:
                    home_team = teams[0].strip()
                    away_team = teams[1].strip()
                    if home_team and away_team:
                        return home_team, away_team
        
        return None, None


class Bet9jaAdapter(BookmakerAdapter):
    """Adapter for Bet9ja bookmaker with specific configurations."""
    
    def _get_config(self) -> BookmakerConfig:
        """Get Bet9ja-specific configuration."""
        return BookmakerConfig(
            id="bet9ja",
            name="Bet9ja",
            base_url="https://www.bet9ja.com",
            betslip_url_pattern="https://www.bet9ja.com/betslip/{code}",
            betting_url="https://www.bet9ja.com/sport",
            dom_selectors={
                # Betslip loading selectors
                "betslip_input": "input[name='betslip_code'], input[id='betslip_code'], input[placeholder*='betslip'], input[placeholder*='code']",
                "submit_button": "button[type='submit'], input[type='submit'], .submit-btn, .load-betslip",
                "betslip_form": "form[action*='betslip'], .betslip-form, #betslip-form",
                
                # Selection extraction selectors
                "selections_container": ".betslip-selections, .selections, .bet-items, .coupon-items, .slip-content",
                "selection_item": ".selection, .bet-item, .coupon-item, .match-item, .slip-item",
                "game_name": ".match-name, .game-name, .event-name, .teams, .match-title",
                "market_name": ".market, .bet-type, .selection-type, .market-name",
                "odds": ".odds, .odd, .price, .odds-value",
                "league": ".league, .competition, .tournament",
                "event_date": ".date, .time, .event-time, .match-time",
                
                # Betting page selectors
                "search_box": "input[placeholder*='search'], input[name*='search'], .search-input, #search",
                "search_button": "button[type='submit'], .search-btn, .search-button",
                "game_links": ".match-link, .game-link, .event-link, a[href*='match'], a[href*='game']",
                "market_buttons": ".market-btn, .bet-btn, .odds-btn, button[data-market], .selection-btn",
                "add_to_betslip": ".add-to-betslip, .add-bet, button[data-add], .add-selection",
                "betslip_area": ".betslip, .bet-slip, .coupon, #betslip, .slip-container",
                "betslip_code_display": ".betslip-code, .share-code, .reference-code, .coupon-id, .slip-id"
            },
            market_mappings={
                # Standard market names to Bet9ja-specific terms
                "match result": "1X2",
                "1x2": "1X2", 
                "over/under 2.5": "Over/Under 2.5 Goals",
                "both teams to score": "Both Teams To Score",
                "double chance": "Double Chance",
                "handicap": "Handicap",
                "correct score": "Correct Score",
                "total goals": "Total Goals",
                "first half result": "1st Half Result",
                "half time/full time": "Half Time/Full Time"
            },
            team_name_normalizations={
                # Bet9ja-specific team name variations
                "Manchester United": "Man United",
                "Manchester City": "Man City", 
                "Tottenham Hotspur": "Tottenham",
                "Brighton & Hove Albion": "Brighton",
                "West Ham United": "West Ham",
                "Newcastle United": "Newcastle",
                "Wolverhampton Wanderers": "Wolves",
                "Leicester City": "Leicester",
                "Crystal Palace": "C Palace",
                "Sheffield United": "Sheffield Utd",
                "Real Madrid": "R Madrid",
                "Atletico Madrid": "A Madrid",
                "Bayern Munich": "Bayern",
                "Borussia Dortmund": "B Dortmund",
                "Paris Saint-Germain": "PSG",
                "AC Milan": "Milan",
                "Inter Milan": "Inter"
            },
            supported=True
        )


class SportybetAdapter(BookmakerAdapter):
    """Adapter for SportyBet bookmaker with specific configurations."""
    
    def _get_config(self) -> BookmakerConfig:
        """Get SportyBet-specific configuration."""
        return BookmakerConfig(
            id="sportybet",
            name="SportyBet",
            base_url="https://www.sportybet.com",
            betslip_url_pattern="https://www.sportybet.com/ng/sport/betslip/{code}",
            betting_url="https://www.sportybet.com/ng/sport",
            dom_selectors={
                # Betslip loading selectors
                "betslip_input": "input[name='betslip_code'], input[id='betslip_code'], input[placeholder*='betslip'], input[placeholder*='code']",
                "submit_button": "button[type='submit'], input[type='submit'], .submit-btn, .load-betslip, .btn-primary",
                "betslip_form": "form[action*='betslip'], .betslip-form, #betslip-form",
                
                # Selection extraction selectors  
                "selections_container": ".betslip-selections, .selections, .bet-items, .coupon-items, .betslip-content",
                "selection_item": ".selection, .bet-item, .coupon-item, .match-item, .betslip-item",
                "game_name": ".match-name, .game-name, .event-name, .teams, .match-title, .event-title",
                "market_name": ".market, .bet-type, .selection-type, .market-name, .bet-name",
                "odds": ".odds, .odd, .price, .odds-value, .rate",
                "league": ".league, .competition, .tournament, .league-name",
                "event_date": ".date, .time, .event-time, .match-time, .start-time",
                
                # Betting page selectors
                "search_box": "input[placeholder*='search'], input[name*='search'], .search-input, #search, .search-field",
                "search_button": "button[type='submit'], .search-btn, .search-button, .btn-search",
                "game_links": ".match-link, .game-link, .event-link, a[href*='match'], a[href*='game'], .event-item",
                "market_buttons": ".market-btn, .bet-btn, .odds-btn, button[data-market], .selection-btn, .odd-btn",
                "add_to_betslip": ".add-to-betslip, .add-bet, button[data-add], .add-selection, .add-to-slip",
                "betslip_area": ".betslip, .bet-slip, .coupon, #betslip, .slip-container, .betslip-panel",
                "betslip_code_display": ".betslip-code, .share-code, .reference-code, .coupon-id, .slip-id, .booking-code"
            },
            market_mappings={
                # Standard market names to SportyBet-specific terms
                "match result": "Match Result",
                "1x2": "Match Result",
                "over/under 2.5": "Total Goals Over/Under 2.5",
                "both teams to score": "Both Teams To Score",
                "double chance": "Double Chance", 
                "handicap": "Asian Handicap",
                "correct score": "Correct Score",
                "total goals": "Total Goals",
                "first half result": "1st Half Result",
                "half time/full time": "Half Time/Full Time",
                "draw no bet": "Draw No Bet",
                "goal line": "Goal Line"
            },
            team_name_normalizations={
                # SportyBet-specific team name variations
                "Manchester United": "Manchester Utd",
                "Manchester City": "Man City",
                "Tottenham Hotspur": "Tottenham",
                "Brighton & Hove Albion": "Brighton",
                "West Ham United": "West Ham",
                "Newcastle United": "Newcastle",
                "Wolverhampton Wanderers": "Wolverhampton",
                "Leicester City": "Leicester",
                "Crystal Palace": "Crystal Palace",
                "Sheffield United": "Sheffield Utd",
                "Real Madrid": "Real Madrid",
                "Atletico Madrid": "Atletico Madrid",
                "Bayern Munich": "Bayern Munich",
                "Borussia Dortmund": "Dortmund",
                "Paris Saint-Germain": "Paris SG",
                "AC Milan": "AC Milan",
                "Inter Milan": "Inter Milan",
                "Juventus": "Juventus",
                "Barcelona": "Barcelona",
                "Chelsea": "Chelsea",
                "Arsenal": "Arsenal",
                "Liverpool": "Liverpool"
            },
            supported=True
        )


class BetwayAdapter(BookmakerAdapter):
    """Adapter for Betway bookmaker with specific configurations."""
    
    def _get_config(self) -> BookmakerConfig:
        """Get Betway-specific configuration."""
        return BookmakerConfig(
            id="betway",
            name="Betway",
            base_url="https://www.betway.com",
            betslip_url_pattern="https://www.betway.com/betslip/{code}",
            betting_url="https://www.betway.com/sport",
            dom_selectors={
                # Betslip loading selectors
                "betslip_input": "input[name='betslip_code'], input[id='betslip_code'], input[placeholder*='betslip'], input[placeholder*='code']",
                "submit_button": "button[type='submit'], input[type='submit'], .submit-btn, .load-betslip, .btn-primary",
                "betslip_form": "form[action*='betslip'], .betslip-form, #betslip-form",
                
                # Selection extraction selectors
                "selections_container": ".betslip-selections, .selections, .bet-items, .coupon-items, .betslip-wrapper",
                "selection_item": ".selection, .bet-item, .coupon-item, .match-item, .betslip-selection",
                "game_name": ".match-name, .game-name, .event-name, .teams, .match-title, .fixture-name",
                "market_name": ".market, .bet-type, .selection-type, .market-name, .outcome-name",
                "odds": ".odds, .odd, .price, .odds-value, .decimal-odds",
                "league": ".league, .competition, .tournament, .competition-name",
                "event_date": ".date, .time, .event-time, .match-time, .kick-off-time",
                
                # Betting page selectors
                "search_box": "input[placeholder*='search'], input[name*='search'], .search-input, #search, .search-field",
                "search_button": "button[type='submit'], .search-btn, .search-button, .search-submit",
                "game_links": ".match-link, .game-link, .event-link, a[href*='match'], a[href*='game'], .fixture-link",
                "market_buttons": ".market-btn, .bet-btn, .odds-btn, button[data-market], .selection-btn, .outcome-btn",
                "add_to_betslip": ".add-to-betslip, .add-bet, button[data-add], .add-selection, .add-to-slip",
                "betslip_area": ".betslip, .bet-slip, .coupon, #betslip, .slip-container, .betslip-container",
                "betslip_code_display": ".betslip-code, .share-code, .reference-code, .coupon-id, .slip-reference"
            },
            market_mappings={
                # Standard market names to Betway-specific terms
                "match result": "Match Result",
                "1x2": "Match Result",
                "over/under 2.5": "Over/Under 2.5 Goals",
                "both teams to score": "Both Teams to Score",
                "double chance": "Double Chance",
                "handicap": "Handicap",
                "correct score": "Correct Score",
                "total goals": "Total Goals",
                "first half result": "First Half Result",
                "half time/full time": "Half Time/Full Time",
                "draw no bet": "Draw No Bet",
                "clean sheet": "Clean Sheet",
                "anytime goalscorer": "Anytime Goalscorer"
            },
            team_name_normalizations={
                # Betway-specific team name variations
                "Manchester United": "Man Utd",
                "Manchester City": "Man City",
                "Tottenham Hotspur": "Tottenham",
                "Brighton & Hove Albion": "Brighton",
                "West Ham United": "West Ham",
                "Newcastle United": "Newcastle",
                "Wolverhampton Wanderers": "Wolves",
                "Leicester City": "Leicester",
                "Crystal Palace": "Crystal Palace",
                "Sheffield United": "Sheffield Utd",
                "Real Madrid": "Real Madrid",
                "Atletico Madrid": "Atletico Madrid",
                "Bayern Munich": "Bayern Munich",
                "Borussia Dortmund": "Borussia Dortmund",
                "Paris Saint-Germain": "PSG",
                "AC Milan": "AC Milan",
                "Inter Milan": "Inter",
                "Juventus": "Juventus",
                "Barcelona": "Barcelona",
                "Chelsea": "Chelsea",
                "Arsenal": "Arsenal",
                "Liverpool": "Liverpool"
            },
            supported=True
        )


class Bet365Adapter(BookmakerAdapter):
    """Adapter for Bet365 bookmaker with specific configurations."""
    
    def _get_config(self) -> BookmakerConfig:
        """Get Bet365-specific configuration."""
        return BookmakerConfig(
            id="bet365",
            name="Bet365",
            base_url="https://www.bet365.com",
            betslip_url_pattern="https://www.bet365.com/betslip/{code}",
            betting_url="https://www.bet365.com/sport",
            dom_selectors={
                # Betslip loading selectors
                "betslip_input": "input[name='betslip_code'], input[id='betslip_code'], input[placeholder*='betslip'], input[placeholder*='code']",
                "submit_button": "button[type='submit'], input[type='submit'], .submit-btn, .load-betslip",
                "betslip_form": "form[action*='betslip'], .betslip-form, #betslip-form",
                
                # Selection extraction selectors
                "selections_container": ".betslip-selections, .selections, .bet-items, .coupon-items, .bss-NormalBetItem_Container",
                "selection_item": ".selection, .bet-item, .coupon-item, .match-item, .bss-NormalBetItem",
                "game_name": ".match-name, .game-name, .event-name, .teams, .match-title, .bss-NormalBetItem_Title",
                "market_name": ".market, .bet-type, .selection-type, .market-name, .bss-NormalBetItem_Market",
                "odds": ".odds, .odd, .price, .odds-value, .bss-NormalBetItem_Odds",
                "league": ".league, .competition, .tournament, .bss-NormalBetItem_Competition",
                "event_date": ".date, .time, .event-time, .match-time, .bss-NormalBetItem_StartTime",
                
                # Betting page selectors
                "search_box": "input[placeholder*='search'], input[name*='search'], .search-input, #search",
                "search_button": "button[type='submit'], .search-btn, .search-button",
                "game_links": ".match-link, .game-link, .event-link, a[href*='match'], a[href*='game'], .sl-CouponParticipantWithBookCloses",
                "market_buttons": ".market-btn, .bet-btn, .odds-btn, button[data-market], .selection-btn, .gl-Participant_General",
                "add_to_betslip": ".add-to-betslip, .add-bet, button[data-add], .add-selection",
                "betslip_area": ".betslip, .bet-slip, .coupon, #betslip, .bss-BetslipContainer",
                "betslip_code_display": ".betslip-code, .share-code, .reference-code, .coupon-id, .bss-ShareBetslip_Code"
            },
            market_mappings={
                # Standard market names to Bet365-specific terms
                "match result": "Result",
                "1x2": "Result",
                "over/under 2.5": "Goals Over/Under",
                "both teams to score": "Both Teams to Score",
                "double chance": "Double Chance",
                "handicap": "Asian Handicap",
                "correct score": "Correct Score",
                "total goals": "Total Goals",
                "first half result": "Half Time Result",
                "half time/full time": "Half Time/Full Time",
                "draw no bet": "Draw No Bet",
                "clean sheet": "To Keep a Clean Sheet",
                "anytime goalscorer": "Goalscorer"
            },
            team_name_normalizations={
                # Bet365-specific team name variations
                "Manchester United": "Man Utd",
                "Manchester City": "Man City",
                "Tottenham Hotspur": "Tottenham",
                "Brighton & Hove Albion": "Brighton",
                "West Ham United": "West Ham",
                "Newcastle United": "Newcastle",
                "Wolverhampton Wanderers": "Wolves",
                "Leicester City": "Leicester",
                "Crystal Palace": "Crystal Palace",
                "Sheffield United": "Sheffield Utd",
                "Real Madrid": "Real Madrid",
                "Atletico Madrid": "Atletico Madrid",
                "Bayern Munich": "Bayern Munich",
                "Borussia Dortmund": "Borussia Dortmund",
                "Paris Saint-Germain": "Paris SG",
                "AC Milan": "AC Milan",
                "Inter Milan": "Inter Milan",
                "Juventus": "Juventus",
                "Barcelona": "Barcelona",
                "Chelsea": "Chelsea",
                "Arsenal": "Arsenal",
                "Liverpool": "Liverpool"
            },
            supported=True
        )


# Factory function to create adapter instances
def get_bookmaker_adapter(bookmaker_id: str) -> BookmakerAdapter:
    """
    Factory function to create the appropriate bookmaker adapter.
    
    Args:
        bookmaker_id: The bookmaker identifier (e.g., 'bet9ja', 'sportybet')
        
    Returns:
        BookmakerAdapter instance for the specified bookmaker
        
    Raises:
        ValueError: If the bookmaker is not supported
    """
    adapters = {
        'bet9ja': Bet9jaAdapter,
        'sportybet': SportybetAdapter,
        'betway': BetwayAdapter,
        'bet365': Bet365Adapter
    }
    
    adapter_class = adapters.get(bookmaker_id.lower())
    if not adapter_class:
        supported_bookmakers = ', '.join(adapters.keys())
        raise ValueError(f"Unsupported bookmaker: {bookmaker_id}. Supported bookmakers: {supported_bookmakers}")
    
    return adapter_class()


# Export all adapter classes and factory function
__all__ = [
    'BookmakerAdapter',
    'Bet9jaAdapter', 
    'SportybetAdapter',
    'BetwayAdapter',
    'Bet365Adapter',
    'get_bookmaker_adapter'
]