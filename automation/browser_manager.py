"""
Browser automation manager for betslip conversion using browser-use library.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
from browser_use import Agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from models import Selection, ConversionResult, BookmakerConfig, validate_betslip_code
from bookmaker_adapters import get_bookmaker_adapter, BookmakerAdapter
from browser_config import BrowserConfig, LLMConfig

# Load environment variables
load_dotenv()

class BrowserUseManager:
    """Manager class for browser-use automation"""
    
    def __init__(self, openai_api_key: str = None, anthropic_api_key: str = None, groq_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.groq_api_key = groq_api_key or os.getenv('GROQ_API_KEY')
        
        # Determine which LLM provider to use, prioritizing Groq
        provider = os.getenv('LLM_PROVIDER', 'groq').lower()
        
        llm_config = LLMConfig.get_extraction_config()

        if provider == 'groq':
            if not self.groq_api_key:
                raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
            # Recommended model for Groq with JSON mode support
            llm_config['model_name'] = 'llama3-70b-8192'
            self.llm = ChatGroq(
                api_key=self.groq_api_key,
                **llm_config
            )
        elif provider == 'anthropic':
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
            self.llm = ChatAnthropic(
                api_key=self.anthropic_api_key,
                **llm_config
            )
        elif provider == 'openai':
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
            self.llm = ChatOpenAI(
                api_key=self.openai_api_key,
                **llm_config
            )
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {provider}. Choose from 'groq', 'openai', 'anthropic'.")
    
    def _get_bookmaker_adapter(self, bookmaker: str) -> BookmakerAdapter:
        """Get adapter for a specific bookmaker"""
        return get_bookmaker_adapter(bookmaker)
    
    def _parse_extracted_data(self, raw_data: str, bookmaker: str) -> List[Selection]:
        """Parse raw extracted data into Selection objects"""
        try:
            # Try to parse as JSON first
            if raw_data.strip().startswith('{') or raw_data.strip().startswith('['):
                data = json.loads(raw_data)
            else:
                # If not JSON, try to extract structured data from text
                data = self._extract_structured_data_from_text(raw_data)
            
            selections = []
            
            # Handle different data structures
            if isinstance(data, dict):
                if 'selections' in data:
                    selections_data = data['selections']
                elif 'bets' in data:
                    selections_data = data['bets']
                elif 'items' in data:
                    selections_data = data['items']
                else:
                    # Assume the dict itself contains selection data
                    selections_data = [data]
            elif isinstance(data, list):
                selections_data = data
            else:
                raise ValueError("Invalid data structure")
            
            for item in selections_data:
                if isinstance(item, dict):
                    selection = self._create_selection_from_dict(item, bookmaker)
                    if selection:
                        selections.append(selection)
            
            return selections
            
        except Exception as e:
            raise ValueError(f"Failed to parse extracted data: {str(e)}")
    
    def _extract_structured_data_from_text(self, text: str) -> List[Dict]:
        """Extract structured data from plain text using regex patterns"""
        selections = []
        
        # Common patterns for extracting betting information
        patterns = {
            'game_pattern': r'(?:Match|Game|Event):\s*([^\n]+)',
            'teams_pattern': r'([A-Za-z\s]+)\s+(?:vs?|v)\s+([A-Za-z\s]+)',
            'market_pattern': r'(?:Market|Bet Type):\s*([^\n]+)',
            'odds_pattern': r'(?:Odds|Price):\s*(\d+\.?\d*)',
            'league_pattern': r'(?:League|Competition):\s*([^\n]+)'
        }
        
        lines = text.split('\n')
        current_selection = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_selection:
                    selections.append(current_selection.copy())
                    current_selection = {}
                continue
            
            # Try to match each pattern
            for pattern_name, pattern in patterns.items():
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    if pattern_name == 'teams_pattern':
                        current_selection['home_team'] = match.group(1).strip()
                        current_selection['away_team'] = match.group(2).strip()
                        current_selection['game'] = f"{match.group(1).strip()} vs {match.group(2).strip()}"
                    elif pattern_name == 'game_pattern':
                        current_selection['game'] = match.group(1).strip()
                    elif pattern_name == 'market_pattern':
                        current_selection['market'] = match.group(1).strip()
                    elif pattern_name == 'odds_pattern':
                        current_selection['odds'] = float(match.group(1))
                    elif pattern_name == 'league_pattern':
                        current_selection['league'] = match.group(1).strip()
                    break
        
        # Add the last selection if exists
        if current_selection:
            selections.append(current_selection)
        
        return selections
    
    def _create_selection_from_dict(self, data: Dict, bookmaker: str) -> Optional[Selection]:
        """Create a Selection object from dictionary data"""
        try:
            # Extract game information
            game = data.get('game', data.get('match', data.get('event', '')))
            home_team = data.get('home_team', '')
            away_team = data.get('away_team', '')
            
            # If teams not provided, try to extract from game name
            if not home_team or not away_team:
                if ' vs ' in game:
                    teams = game.split(' vs ')
                    home_team = teams[0].strip()
                    away_team = teams[1].strip() if len(teams) > 1 else ''
                elif ' v ' in game:
                    teams = game.split(' v ')
                    home_team = teams[0].strip()
                    away_team = teams[1].strip() if len(teams) > 1 else ''
            
            # Extract other fields
            market = data.get('market', data.get('bet_type', data.get('selection', '')))
            odds = float(data.get('odds', data.get('price', 0)))
            league = data.get('league', data.get('competition', 'Unknown League'))
            original_text = data.get('original_text', str(data))
            
            # Generate game_id
            game_id = f"{bookmaker}_{home_team}_{away_team}_{market}".replace(' ', '_').lower()
            
            # Set event date (default to current time + 1 hour if not provided)
            event_date = datetime.now().replace(hour=datetime.now().hour + 1, minute=0, second=0, microsecond=0)
            if 'event_date' in data:
                try:
                    event_date = datetime.fromisoformat(data['event_date'])
                except:
                    pass
            
            # Validate required fields
            if not home_team or not away_team or not market or odds <= 0:
                return None
            
            return Selection(
                game_id=game_id,
                home_team=home_team,
                away_team=away_team,
                market=market,
                odds=odds,
                event_date=event_date,
                league=league,
                original_text=original_text
            )
            
        except Exception as e:
            print(f"Error creating selection from data: {e}")
            return None
    
    async def extract_betslip_selections(self, betslip_code: str, bookmaker: str) -> List[Selection]:
        """
        Extract betting selections from a betslip code using browser-use Agent.
        
        Args:
            betslip_code: The betslip code to extract selections from
            bookmaker: The source bookmaker identifier
            
        Returns:
            List of Selection objects extracted from the betslip
            
        Raises:
            ValueError: If betslip code is invalid or bookmaker is unsupported
            Exception: If extraction fails
        """
        # Validate inputs
        if not validate_betslip_code(betslip_code):
            raise ValueError(f"Invalid betslip code format: {betslip_code}")
        
        adapter = self._get_bookmaker_adapter(bookmaker)
        config = adapter.config
        
        # Create the extraction task prompt
        task_prompt = f"""
        You are a web automation agent tasked with extracting betting selections from a betslip on {config.name}.
        
        TASK STEPS:
        1. Navigate to {adapter.get_base_url()}
        2. Look for a betslip input field or "Load Betslip" functionality
        3. Enter the betslip code: {betslip_code}
        4. Submit the form or click the load button
        5. Wait for the betslip to load completely
        6. Extract ALL betting selections from the loaded betslip
        
        For each selection, extract:
        - Game/Match name (including team names)
        - Home team name
        - Away team name  
        - Betting market/type (e.g., "Match Result", "Over/Under 2.5", "Both Teams to Score")
        - Odds/Price
        - League/Competition name
        - Event date/time if available
        
        IMPORTANT INSTRUCTIONS:
        - If the betslip code is invalid or expired, return an error message
        - If anti-bot protection appears, try to bypass it naturally
        - Extract data from ALL selections in the betslip
        - Return the data in JSON format with this structure:
        {{
            "success": true/false,
            "error": "error message if failed",
            "selections": [
                {{
                    "game": "Team A vs Team B",
                    "home_team": "Team A",
                    "away_team": "Team B",
                    "market": "Match Result - Home Win",
                    "odds": 2.50,
                    "league": "Premier League",
                    "event_date": "2024-01-15T15:00:00",
                    "original_text": "original text from the page"
                }}
            ]
        }}
        
        DOM SELECTORS TO TRY:
        - Betslip input: {adapter.get_dom_selectors().get('betslip_input', 'input[placeholder*="betslip"], input[placeholder*="code"]')}
        - Submit button: {adapter.get_dom_selectors().get('submit_button', 'button[type="submit"], .submit-btn')}
        - Selections container: {adapter.get_dom_selectors().get('selections_container', '.selections, .bet-items')}
        - Selection items: {adapter.get_dom_selectors().get('selection_item', '.selection, .bet-item')}
        - Game names: {adapter.get_dom_selectors().get('game_name', '.match-name, .game-name')}
        - Markets: {adapter.get_dom_selectors().get('market_name', '.market, .bet-type')}
        - Odds: {adapter.get_dom_selectors().get('odds', '.odds, .price')}
        
        If the exact selectors don't work, use your intelligence to find similar elements.
        """
        
        try:
            # Create and run the browser-use agent with optimized config
            agent = Agent(
                task=task_prompt,
                llm=self.llm,
                browser_config=BrowserConfig.get_extraction_config()
            )
            
            # Execute the extraction task
            result = await agent.run()
            
            # Parse the result
            if hasattr(result, 'extracted_content') and result.extracted_content:
                raw_data = result.extracted_content
            elif hasattr(result, 'result') and result.result:
                raw_data = result.result
            else:
                raw_data = str(result)
            
            # Try to parse as JSON first
            try:
                if isinstance(raw_data, str):
                    # Clean up the raw data
                    raw_data = raw_data.strip()
                    if raw_data.startswith('```json'):
                        raw_data = raw_data[7:]
                    if raw_data.endswith('```'):
                        raw_data = raw_data[:-3]
                    
                    parsed_result = json.loads(raw_data)
                else:
                    parsed_result = raw_data
                
                # Check if extraction was successful
                if isinstance(parsed_result, dict) and not parsed_result.get('success', True):
                    error_msg = parsed_result.get('error', 'Unknown extraction error')
                    raise ValueError(f"Betslip extraction failed: {error_msg}")
                
                # Parse the selections
                selections = self._parse_extracted_data(json.dumps(parsed_result), bookmaker)
                
                if not selections:
                    raise ValueError("No valid selections found in betslip")
                
                return selections
                
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract from raw text
                selections = self._parse_extracted_data(raw_data, bookmaker)
                
                if not selections:
                    raise ValueError("Failed to extract selections from betslip data")
                
                return selections
            
        except Exception as e:
            # Enhanced error handling with specific error types
            error_msg = str(e).lower()
            
            if 'invalid' in error_msg and 'betslip' in error_msg:
                raise ValueError(f"Invalid or expired betslip code: {betslip_code}")
            elif 'timeout' in error_msg:
                raise Exception(f"Extraction timed out for bookmaker {bookmaker}")
            elif 'blocked' in error_msg or 'bot' in error_msg:
                raise Exception(f"Access blocked by anti-bot protection on {bookmaker}")
            elif 'network' in error_msg or 'connection' in error_msg:
                raise Exception(f"Network error while accessing {bookmaker}")
            else:
                raise Exception(f"Betslip extraction failed: {str(e)}")
    
    async def create_betslip(self, selections: List[Selection], bookmaker: str) -> str:
        """
        Create a new betslip on the destination bookmaker using browser automation.
        
        Args:
            selections: List of Selection objects to add to the betslip
            bookmaker: The destination bookmaker identifier
            
        Returns:
            String containing the generated betslip code
            
        Raises:
            ValueError: If bookmaker is unsupported or selections are invalid
            Exception: If betslip creation fails
        """
        if not selections:
            raise ValueError("No selections provided for betslip creation")
        
        adapter = self._get_bookmaker_adapter(bookmaker)
        config = adapter.config
        
        # Create the betslip creation task prompt
        task_prompt = f"""
        You are a web automation agent tasked with creating a new betslip on {config.name}.
        
        TASK OVERVIEW:
        Create a betslip with the following {len(selections)} selections:
        
        {self._format_selections_for_prompt(selections)}
        
        DETAILED STEPS:
        1. Navigate to {adapter.get_betting_url()}
        2. For each selection above:
           a. Search for the game/match using team names
           b. Navigate to the specific game page
           c. Find and click on the specified betting market
           d. Verify the odds are reasonable (within ±0.10 of expected)
           e. Add the selection to the betslip
        3. Once all selections are added, generate/save the betslip
        4. Extract the betslip code from the generated betslip
        
        IMPORTANT INSTRUCTIONS:
        - Search for games using both team names (e.g., "Team A vs Team B" or "Team A Team B")
        - If exact team names don't match, try variations and abbreviations
        - For betting markets, look for equivalent terms:
          * "Match Result" = "1X2", "Full Time Result", "Winner"
          * "Over/Under 2.5" = "Total Goals Over/Under 2.5", "O/U 2.5"
          * "Both Teams to Score" = "BTTS", "Both Teams To Score - Yes"
        - If a game or market is not available, skip it and continue with others
        - Accept odds within ±0.10 of the expected odds
        - If anti-bot protection appears, try to bypass it naturally
        - After creating the betslip, look for a betslip code, share code, or reference number
        
        RETURN FORMAT:
        Return a JSON response with this structure:
        {{
            "success": true/false,
            "betslip_code": "extracted betslip code",
            "created_selections": [
                {{
                    "game": "Team A vs Team B",
                    "market": "Match Result - Home Win", 
                    "odds": 2.45,
                    "status": "added"
                }}
            ],
            "skipped_selections": [
                {{
                    "game": "Team C vs Team D",
                    "market": "Over/Under 2.5",
                    "reason": "Game not found"
                }}
            ],
            "error": "error message if failed"
        }}
        
        DOM SELECTORS TO TRY:
        - Search box: input[placeholder*="search"], input[name*="search"], .search-input
        - Game links: .match-link, .game-link, .event-link, a[href*="match"], a[href*="game"]
        - Market buttons: .market-btn, .bet-btn, .odds-btn, button[data-market]
        - Betslip area: .betslip, .bet-slip, .coupon, #betslip
        - Betslip code: .betslip-code, .share-code, .reference-code, .coupon-id
        - Add to betslip: .add-to-betslip, .add-bet, button[data-add]
        
        If exact selectors don't work, use your intelligence to find similar elements.
        """
        
        # Retry logic for betslip creation (requirement 4.5)
        max_retries = 3
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                print(f"Betslip creation attempt {attempt + 1}/{max_retries} for {bookmaker}")
                
                # Create and run the browser-use agent with optimized config
                creation_llm_config = LLMConfig.get_creation_config()
                provider = os.getenv('LLM_PROVIDER', 'groq').lower()
                
                if provider == 'groq':
                    creation_llm_config['model_name'] = 'llama3-70b-8192'
                    creation_llm = ChatGroq(api_key=self.groq_api_key, **creation_llm_config)
                elif provider == 'anthropic':
                    creation_llm = ChatAnthropic(api_key=self.anthropic_api_key, **creation_llm_config)
                elif provider == 'openai':
                    creation_llm = ChatOpenAI(api_key=self.openai_api_key, **creation_llm_config)
                else:
                    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
                
                agent = Agent(
                    task=task_prompt,
                    llm=creation_llm,
                    browser_config=BrowserConfig.get_creation_config()
                )
                
                # Execute the betslip creation task
                result = await agent.run()
                
                # If we get here, the attempt was successful, break out of retry loop
                break
                
            except Exception as e:
                last_exception = e
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                
                # If this was the last attempt, re-raise the exception
                if attempt == max_retries - 1:
                    raise e
                
                # Wait before retrying (exponential backoff)
                import asyncio
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
        
        # Parse the result (this should be outside the retry loop)
        if hasattr(result, 'extracted_content') and result.extracted_content:
            raw_data = result.extracted_content
        elif hasattr(result, 'result') and result.result:
            raw_data = result.result
        else:
            raw_data = str(result)
        
        # Parse the JSON response
        try:
            if isinstance(raw_data, str):
                # Clean up the raw data
                raw_data = raw_data.strip()
                if raw_data.startswith('```json'):
                    raw_data = raw_data[7:]
                if raw_data.endswith('```'):
                    raw_data = raw_data[:-3]
                
                parsed_result = json.loads(raw_data)
            else:
                parsed_result = raw_data
            
            # Check if creation was successful
            if not isinstance(parsed_result, dict):
                raise ValueError("Invalid response format from betslip creation")
            
            if not parsed_result.get('success', False):
                error_msg = parsed_result.get('error', 'Unknown betslip creation error')
                raise Exception(f"Betslip creation failed: {error_msg}")
            
            # Extract the betslip code
            betslip_code = parsed_result.get('betslip_code', '').strip()
            if not betslip_code:
                raise Exception("No betslip code returned from creation process")
            
            # Log creation details for debugging
            created_selections = parsed_result.get('created_selections', [])
            skipped_selections = parsed_result.get('skipped_selections', [])
            
            print(f"Betslip created successfully on {bookmaker}")
            print(f"Created selections: {len(created_selections)}")
            print(f"Skipped selections: {len(skipped_selections)}")
            print(f"Betslip code: {betslip_code}")
            
            # Validate betslip code format
            if not validate_betslip_code(betslip_code):
                raise Exception(f"Invalid betslip code format returned: {betslip_code}")
            
            return betslip_code
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse betslip creation response: {str(e)}")
        except Exception as e:
            # Enhanced error handling with specific error types
            error_msg = str(e).lower()
            
            if 'timeout' in error_msg:
                raise Exception(f"Betslip creation timed out for bookmaker {bookmaker}")
            elif 'blocked' in error_msg or 'bot' in error_msg:
                raise Exception(f"Access blocked by anti-bot protection on {bookmaker}")
            elif 'network' in error_msg or 'connection' in error_msg:
                raise Exception(f"Network error while accessing {bookmaker}")
            elif 'not found' in error_msg:
                raise Exception(f"Could not find games or markets on {bookmaker}")
            else:
                raise Exception(f"Betslip creation failed: {str(e)}")
    
    def _format_selections_for_prompt(self, selections: List[Selection]) -> str:
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
        
        return unique_variations
    
    async def verify_market_availability(self, selection: Selection, bookmaker: str) -> bool:
        """Verify if a market is available on the bookmaker"""
        # Placeholder implementation
        # This will be implemented in task 6.2
        return True