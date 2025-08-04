"""
Intelligent market matching system for betslip conversion.

This module provides fuzzy matching for team names, odds comparison logic,
market availability checking, and cross-bookmaker market mapping functionality.
"""

import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from difflib import SequenceMatcher
from models import Selection
from bookmaker_adapters import get_bookmaker_adapter, BookmakerAdapter


@dataclass
class MatchResult:
    """Result of a market matching operation."""
    success: bool
    confidence: float  # 0.0 to 1.0
    matched_game: Optional[str] = None
    matched_market: Optional[str] = None
    matched_odds: Optional[float] = None
    original_odds: Optional[float] = None
    odds_difference: Optional[float] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class GameAvailability:
    """Availability status of a game on a bookmaker."""
    available: bool
    game_name: Optional[str] = None
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    markets: List[str] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.markets is None:
            self.markets = []


class MarketMatcher:
    """
    Intelligent market matching system with fuzzy matching and odds comparison.
    
    This class provides functionality for:
    - Fuzzy matching of team names across bookmakers
    - Odds comparison with configurable tolerance
    - Market availability checking
    - Cross-bookmaker market mapping
    """
    
    def __init__(self, odds_tolerance: float = 0.05):
        """
        Initialize the market matcher.
        
        Args:
            odds_tolerance: Default tolerance for odds comparison (±0.05)
        """
        self.odds_tolerance = odds_tolerance
        self._team_name_cache = {}
        self._market_mapping_cache = {}
    
    def fuzzy_match_team_names(self, 
                              source_home: str, 
                              source_away: str,
                              target_home: str, 
                              target_away: str,
                              source_bookmaker: str,
                              target_bookmaker: str) -> Tuple[float, bool]:
        """
        Perform fuzzy matching between team names from different bookmakers.
        
        Args:
            source_home: Home team name from source bookmaker
            source_away: Away team name from source bookmaker
            target_home: Home team name from target bookmaker
            target_away: Away team name from target bookmaker
            source_bookmaker: Source bookmaker identifier
            target_bookmaker: Target bookmaker identifier
            
        Returns:
            Tuple of (confidence_score, teams_swapped)
            confidence_score: 0.0 to 1.0 indicating match quality
            teams_swapped: True if home/away teams are swapped in target
        """
        # Get adapters for normalization
        source_adapter = get_bookmaker_adapter(source_bookmaker)
        target_adapter = get_bookmaker_adapter(target_bookmaker)
        
        # Normalize team names using bookmaker-specific rules
        norm_source_home = source_adapter.normalize_game_name(source_home)
        norm_source_away = source_adapter.normalize_game_name(source_away)
        norm_target_home = target_adapter.normalize_game_name(target_home)
        norm_target_away = target_adapter.normalize_game_name(target_away)
        
        # Calculate similarity scores for both orientations
        # Normal orientation (home vs home, away vs away)
        home_similarity_normal = self._calculate_team_similarity(norm_source_home, norm_target_home)
        away_similarity_normal = self._calculate_team_similarity(norm_source_away, norm_target_away)
        normal_score = (home_similarity_normal + away_similarity_normal) / 2
        
        # Swapped orientation (home vs away, away vs home)
        home_similarity_swapped = self._calculate_team_similarity(norm_source_home, norm_target_away)
        away_similarity_swapped = self._calculate_team_similarity(norm_source_away, norm_target_home)
        swapped_score = (home_similarity_swapped + away_similarity_swapped) / 2
        
        # Determine best match
        if normal_score >= swapped_score:
            return normal_score, False
        else:
            return swapped_score, True
    
    def _calculate_team_similarity(self, team1: str, team2: str) -> float:
        """
        Calculate similarity between two team names using multiple methods.
        
        Args:
            team1: First team name
            team2: Second team name
            
        Returns:
            Similarity score from 0.0 to 1.0
        """
        if not team1 or not team2:
            return 0.0
        
        # Exact match
        if team1.lower() == team2.lower():
            return 1.0
        
        # Sequence matcher for overall similarity
        sequence_similarity = SequenceMatcher(None, team1.lower(), team2.lower()).ratio()
        
        # Word-based similarity (handles abbreviations better)
        words1 = set(team1.lower().split())
        words2 = set(team2.lower().split())
        
        if not words1 or not words2:
            word_similarity = 0.0
        else:
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            word_similarity = intersection / union if union > 0 else 0.0
        
        # Substring matching (handles partial names)
        substring_similarity = 0.0
        if team1.lower() in team2.lower() or team2.lower() in team1.lower():
            substring_similarity = 0.8
        
        # Common abbreviation patterns
        abbrev_similarity = self._check_abbreviation_match(team1, team2)
        
        # Weighted combination of all similarity measures
        weights = {
            'sequence': 0.4,
            'word': 0.3,
            'substring': 0.2,
            'abbreviation': 0.1
        }
        
        total_similarity = (
            sequence_similarity * weights['sequence'] +
            word_similarity * weights['word'] +
            substring_similarity * weights['substring'] +
            abbrev_similarity * weights['abbreviation']
        )
        
        return min(total_similarity, 1.0)
    
    def _check_abbreviation_match(self, team1: str, team2: str) -> float:
        """Check if teams match through common abbreviation patterns."""
        # Common abbreviation mappings
        abbreviations = {
            'manchester united': ['man utd', 'man united', 'mufc'],
            'manchester city': ['man city', 'mcfc'],
            'tottenham hotspur': ['tottenham', 'spurs', 'thfc'],
            'arsenal': ['arsenal fc', 'afc'],
            'chelsea': ['chelsea fc', 'cfc'],
            'liverpool': ['liverpool fc', 'lfc'],
            'real madrid': ['r madrid', 'real', 'rmcf'],
            'barcelona': ['barca', 'fcb', 'fc barcelona'],
            'bayern munich': ['bayern', 'fcb munich'],
            'paris saint-germain': ['psg', 'paris sg'],
            'ac milan': ['milan', 'acm'],
            'inter milan': ['inter', 'internazionale'],
            'atletico madrid': ['atletico', 'atm', 'a madrid'],
            'borussia dortmund': ['dortmund', 'bvb', 'b dortmund']
        }
        
        team1_lower = team1.lower().strip()
        team2_lower = team2.lower().strip()
        
        # Check direct abbreviation matches
        for full_name, abbrevs in abbreviations.items():
            if (team1_lower == full_name and team2_lower in abbrevs) or \
               (team2_lower == full_name and team1_lower in abbrevs) or \
               (team1_lower in abbrevs and team2_lower in abbrevs):
                return 0.9
        
        # Check if one is an abbreviation of the other
        if len(team1_lower) <= 4 and team1_lower in team2_lower:
            return 0.7
        if len(team2_lower) <= 4 and team2_lower in team1_lower:
            return 0.7
        
        return 0.0
    
    def compare_odds(self, 
                    original_odds: float, 
                    target_odds: float, 
                    tolerance: Optional[float] = None) -> Tuple[bool, float]:
        """
        Compare odds with configurable tolerance ranges.
        
        Args:
            original_odds: Original odds from source bookmaker
            target_odds: Target odds from destination bookmaker
            tolerance: Custom tolerance (uses default if None)
            
        Returns:
            Tuple of (within_tolerance, difference)
        """
        if tolerance is None:
            tolerance = self.odds_tolerance
        
        if original_odds <= 0 or target_odds <= 0:
            return False, float('inf')
        
        difference = abs(original_odds - target_odds)
        within_tolerance = difference <= tolerance
        
        return within_tolerance, difference
    
    def map_market_across_bookmakers(self, 
                                   market: str, 
                                   source_bookmaker: str, 
                                   target_bookmaker: str) -> Tuple[str, float]:
        """
        Map a market name from source bookmaker to target bookmaker format.
        
        Args:
            market: Market name from source bookmaker
            source_bookmaker: Source bookmaker identifier
            target_bookmaker: Target bookmaker identifier
            
        Returns:
            Tuple of (mapped_market_name, confidence_score)
        """
        # Use cache to avoid repeated lookups
        cache_key = f"{source_bookmaker}_{target_bookmaker}_{market.lower()}"
        if cache_key in self._market_mapping_cache:
            return self._market_mapping_cache[cache_key]
        
        source_adapter = get_bookmaker_adapter(source_bookmaker)
        target_adapter = get_bookmaker_adapter(target_bookmaker)
        
        # First, normalize the market name using source adapter
        normalized_market = source_adapter.map_market_name(market)
        
        # Then map to target bookmaker format
        target_market = target_adapter.map_market_name(normalized_market)
        
        # Calculate confidence based on mapping success
        confidence = self._calculate_market_mapping_confidence(
            market, normalized_market, target_market
        )
        
        # Cache the result
        result = (target_market, confidence)
        self._market_mapping_cache[cache_key] = result
        
        return result
    
    def _calculate_market_mapping_confidence(self, 
                                           original: str, 
                                           normalized: str, 
                                           mapped: str) -> float:
        """Calculate confidence score for market mapping."""
        # If no changes were made, confidence is lower
        if original == normalized == mapped:
            return 0.6
        
        # If mapping occurred, confidence is higher
        if original != mapped:
            return 0.9
        
        # If only normalization occurred
        if original != normalized:
            return 0.8
        
        return 0.7
    
    def check_game_availability(self, 
                              selection: Selection, 
                              bookmaker: str,
                              available_games: List[Dict[str, Any]]) -> GameAvailability:
        """
        Check if a game is available on the target bookmaker.
        
        Args:
            selection: Selection object to check
            bookmaker: Target bookmaker identifier
            available_games: List of available games from bookmaker
            
        Returns:
            GameAvailability object with availability status
        """
        if not available_games:
            return GameAvailability(available=False, confidence=0.0)
        
        best_match = None
        best_confidence = 0.0
        best_markets = []
        
        adapter = get_bookmaker_adapter(bookmaker)
        
        for game in available_games:
            # Extract game information
            game_home = game.get('home_team', '')
            game_away = game.get('away_team', '')
            game_markets = game.get('markets', [])
            
            if not game_home or not game_away:
                continue
            
            # Calculate team name similarity
            confidence, teams_swapped = self.fuzzy_match_team_names(
                selection.home_team, selection.away_team,
                game_home, game_away,
                'bet9ja', bookmaker  # Use bet9ja as default source bookmaker
            )
            
            # Update best match if this is better
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = game
                best_markets = game_markets
        
        # Determine if game is available (confidence threshold of 0.7)
        available = best_confidence >= 0.7
        
        if available and best_match:
            return GameAvailability(
                available=True,
                game_name=f"{best_match.get('home_team', '')} vs {best_match.get('away_team', '')}",
                home_team=best_match.get('home_team', ''),
                away_team=best_match.get('away_team', ''),
                markets=best_markets,
                confidence=best_confidence
            )
        else:
            return GameAvailability(
                available=False,
                confidence=best_confidence
            )
    
    def check_market_availability(self, 
                                selection: Selection, 
                                bookmaker: str,
                                available_markets: List[str]) -> Tuple[bool, str, float]:
        """
        Check if a specific market is available for a game.
        
        Args:
            selection: Selection object with market to check
            bookmaker: Target bookmaker identifier
            available_markets: List of available markets for the game
            
        Returns:
            Tuple of (available, mapped_market, confidence)
        """
        if not available_markets:
            return False, selection.market, 0.0
        
        # Map the market to target bookmaker format
        mapped_market, mapping_confidence = self.map_market_across_bookmakers(
            selection.market, 'bet9ja', bookmaker
        )
        
        # Check if mapped market exists in available markets
        best_match = None
        best_confidence = 0.0
        
        for available_market in available_markets:
            # Direct match
            if mapped_market.lower() == available_market.lower():
                return True, available_market, 1.0
            
            # Fuzzy match
            similarity = SequenceMatcher(None, 
                                       mapped_market.lower(), 
                                       available_market.lower()).ratio()
            
            if similarity > best_confidence:
                best_confidence = similarity
                best_match = available_market
        
        # Consider it available if similarity is above threshold
        available = best_confidence >= 0.8
        final_market = best_match if available else mapped_market
        final_confidence = best_confidence * mapping_confidence
        
        return available, final_market, final_confidence
    
    def match_selection(self, 
                       selection: Selection, 
                       bookmaker: str,
                       available_games: List[Dict[str, Any]],
                       tolerance: Optional[float] = None) -> MatchResult:
        """
        Perform complete matching of a selection against available games.
        
        Args:
            selection: Selection to match
            bookmaker: Target bookmaker identifier
            available_games: List of available games with markets and odds
            tolerance: Custom odds tolerance
            
        Returns:
            MatchResult with complete matching information
        """
        warnings = []
        
        # Check game availability
        game_availability = self.check_game_availability(selection, bookmaker, available_games)
        
        if not game_availability.available:
            return MatchResult(
                success=False,
                confidence=game_availability.confidence,
                warnings=[f"Game not found: {selection.home_team} vs {selection.away_team}"]
            )
        
        # Find the matching game data
        matching_game = None
        for game in available_games:
            game_home = game.get('home_team', '')
            game_away = game.get('away_team', '')
            
            confidence, _ = self.fuzzy_match_team_names(
                selection.home_team, selection.away_team,
                game_home, game_away,
                'bet9ja', bookmaker
            )
            
            if confidence >= 0.7:
                matching_game = game
                break
        
        if not matching_game:
            return MatchResult(
                success=False,
                confidence=0.0,
                warnings=["Could not find matching game data"]
            )
        
        # Check market availability
        available_markets = matching_game.get('markets', [])
        market_available, mapped_market, market_confidence = self.check_market_availability(
            selection, bookmaker, [m.get('name', '') for m in available_markets]
        )
        
        if not market_available:
            warnings.append(f"Market not available: {selection.market}")
            return MatchResult(
                success=False,
                confidence=market_confidence,
                matched_game=game_availability.game_name,
                warnings=warnings
            )
        
        # Find odds for the matched market
        matched_odds = None
        for market in available_markets:
            if market.get('name', '').lower() == mapped_market.lower():
                matched_odds = market.get('odds', 0.0)
                break
        
        if not matched_odds or matched_odds <= 0:
            warnings.append("No valid odds found for market")
            return MatchResult(
                success=False,
                confidence=market_confidence,
                matched_game=game_availability.game_name,
                matched_market=mapped_market,
                warnings=warnings
            )
        
        # Compare odds
        odds_within_tolerance, odds_difference = self.compare_odds(
            selection.odds, matched_odds, tolerance
        )
        
        if not odds_within_tolerance:
            warnings.append(f"Odds difference too large: {odds_difference:.3f}")
        
        # Calculate overall confidence
        overall_confidence = (
            game_availability.confidence * 0.4 +
            market_confidence * 0.4 +
            (1.0 if odds_within_tolerance else 0.5) * 0.2
        )
        
        return MatchResult(
            success=True,
            confidence=overall_confidence,
            matched_game=game_availability.game_name,
            matched_market=mapped_market,
            matched_odds=matched_odds,
            original_odds=selection.odds,
            odds_difference=odds_difference,
            warnings=warnings
        )
    
    def get_search_variations(self, 
                            home_team: str, 
                            away_team: str, 
                            bookmaker: str) -> List[str]:
        """
        Generate search term variations for finding games on a bookmaker.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            bookmaker: Target bookmaker identifier
            
        Returns:
            List of search term variations
        """
        adapter = get_bookmaker_adapter(bookmaker)
        return adapter.get_search_variations(home_team, away_team)
    
    def validate_odds_range(self, 
                          odds: float, 
                          expected_odds: float, 
                          tolerance: Optional[float] = None) -> bool:
        """
        Validate if odds are within acceptable range.
        
        Args:
            odds: Actual odds found
            expected_odds: Expected odds from source
            tolerance: Custom tolerance (uses default if None)
            
        Returns:
            True if odds are within tolerance, False otherwise
        """
        if tolerance is None:
            tolerance = self.odds_tolerance
        
        within_tolerance, _ = self.compare_odds(expected_odds, odds, tolerance)
        return within_tolerance


# Factory function for creating market matcher instances
def create_market_matcher(odds_tolerance: float = 0.05) -> MarketMatcher:
    """
    Create a MarketMatcher instance with specified configuration.
    
    Args:
        odds_tolerance: Default odds tolerance for comparisons
        
    Returns:
        Configured MarketMatcher instance
    """
    return MarketMatcher(odds_tolerance=odds_tolerance)


# Export main classes and functions
__all__ = [
    'MarketMatcher',
    'MatchResult', 
    'GameAvailability',
    'create_market_matcher'
]