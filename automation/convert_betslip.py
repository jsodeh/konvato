#!/usr/bin/env python3
"""
Entry point script for betslip conversion automation.
This script is called by the Node.js server to perform betslip conversions.
"""

import sys
import json
import asyncio
import time
import os
from typing import Dict, Any
from browser_manager import BrowserUseManager, ConversionResult, Selection
from parallel_browser_manager import ParallelBrowserManager


async def convert_betslip(betslip_code: str, source_bookmaker: str, destination_bookmaker: str) -> Dict[str, Any]:
    """
    Main conversion function that orchestrates the betslip conversion process.
    Uses parallel processing for improved performance.
    
    Args:
        betslip_code: The betslip code to convert
        source_bookmaker: Source bookmaker identifier
        destination_bookmaker: Destination bookmaker identifier
    
    Returns:
        Dictionary containing conversion results
    """
    start_time = time.time()
    
    # Determine whether to use parallel processing based on environment variable
    use_parallel = os.getenv('USE_PARALLEL_PROCESSING', 'true').lower() == 'true'
    
    try:
        if use_parallel:
            # Initialize parallel browser automation manager
            manager = ParallelBrowserManager(
                max_concurrent=int(os.getenv('MAX_CONCURRENT_BROWSERS', '3')),
                max_memory_mb=int(os.getenv('MAX_MEMORY_MB', '2048'))
            )
        else:
            # Use standard browser manager for simpler cases
            manager = BrowserUseManager()
        
        try:
            # Step 1: Extract selections from source bookmaker
            extracted_selections = await manager.extract_betslip_selections(betslip_code, source_bookmaker)
            
            if not extracted_selections:
                return {
                    "success": False,
                    "error": "Failed to extract selections from betslip code",
                    "new_betslip_code": None,
                    "converted_selections": [],
                    "warnings": ["Could not find or extract betting selections from the provided betslip code"],
                    "processing_time": (time.time() - start_time) * 1000,
                    "partial_conversion": False
                }
            
            # Step 2: Create new betslip on destination bookmaker
            if use_parallel and len(extracted_selections) > 1:
                # Use parallel processing for multiple selections
                new_betslip_code = await _create_betslip_parallel(manager, extracted_selections, destination_bookmaker)
            else:
                # Use standard processing for single selections or when parallel is disabled
                new_betslip_code = await manager.create_betslip(extracted_selections, destination_bookmaker)
            
            if not new_betslip_code:
                return {
                    "success": False,
                    "error": "Failed to create betslip on destination bookmaker",
                    "new_betslip_code": None,
                    "converted_selections": [],
                    "warnings": ["Could not create betslip on destination bookmaker"],
                    "processing_time": (time.time() - start_time) * 1000,
                    "partial_conversion": False
                }
            
            # Format successful response
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "new_betslip_code": new_betslip_code,
                "converted_selections": [
                    {
                        "game": f"{sel.home_team} vs {sel.away_team}",
                        "market": sel.market,
                        "odds": sel.odds,
                        "originalOdds": sel.odds,  # Will be different when actual implementation is done
                        "status": "converted"
                    } for sel in extracted_selections
                ],
                "warnings": [],
                "processing_time": processing_time,
                "partial_conversion": False,
                "parallel_processing": use_parallel,
                "selections_count": len(extracted_selections)
            }
            
        finally:
            # Cleanup parallel manager if used
            if use_parallel and isinstance(manager, ParallelBrowserManager):
                await manager.shutdown()
        
    except Exception as e:
        error_msg = str(e)
        warnings = []
        
        # Enhanced error categorization
        if "not found" in error_msg.lower():
            warnings.append("Some games or markets were not available on the destination bookmaker")
        elif "blocked" in error_msg.lower() or "bot" in error_msg.lower():
            warnings.append("Access was temporarily blocked by anti-bot protection")
        elif "timeout" in error_msg.lower():
            warnings.append("Betslip creation timed out - the bookmaker may be slow or unavailable")
        elif "memory" in error_msg.lower():
            warnings.append("System memory pressure detected - try again later")
        elif "queue" in error_msg.lower():
            warnings.append("System is busy processing other requests - try again later")
        else:
            warnings.append(f"Conversion failed: {error_msg}")
        
        return {
            "success": False,
            "error": error_msg,
            "new_betslip_code": None,
            "converted_selections": [],
            "warnings": warnings,
            "processing_time": (time.time() - start_time) * 1000,
            "partial_conversion": False,
            "parallel_processing": use_parallel
        }


async def _create_betslip_parallel(manager: ParallelBrowserManager, selections: list, destination_bookmaker: str) -> str:
    """
    Create betslip using parallel processing for multiple selections.
    
    Args:
        manager: ParallelBrowserManager instance
        selections: List of Selection objects
        destination_bookmaker: Destination bookmaker identifier
    
    Returns:
        Generated betslip code
    """
    try:
        # Process selections in parallel to verify availability and add to betslip
        selection_results = await manager.process_multiple_selections_parallel(selections, destination_bookmaker)
        
        # Filter successful selections
        successful_selections = [sel for sel, success in selection_results if success]
        
        if not successful_selections:
            raise Exception("No selections could be added to the betslip")
        
        # Create final betslip with successful selections
        betslip_code = await manager.create_betslip(successful_selections, destination_bookmaker)
        
        # Log parallel processing statistics
        total_selections = len(selections)
        successful_count = len(successful_selections)
        
        print(f"Parallel processing completed: {successful_count}/{total_selections} selections successful")
        
        return betslip_code
        
    except Exception as e:
        print(f"Parallel betslip creation failed: {e}")
        # Fallback to standard processing
        return await manager.create_betslip(selections, destination_bookmaker)


def main():
    """Main entry point for the script."""
    if len(sys.argv) != 4:
        print(json.dumps({
            "success": False,
            "error": "Invalid arguments. Expected: betslip_code source_bookmaker destination_bookmaker"
        }))
        sys.exit(1)
    
    betslip_code = sys.argv[1]
    source_bookmaker = sys.argv[2]
    destination_bookmaker = sys.argv[3]
    
    try:
        # Run the async conversion function
        result = asyncio.run(convert_betslip(betslip_code, source_bookmaker, destination_bookmaker))
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Script execution failed: {str(e)}",
            "new_betslip_code": None,
            "converted_selections": [],
            "warnings": [f"Script execution error: {str(e)}"],
            "processing_time": 0,
            "partial_conversion": False
        }
        print(json.dumps(error_result))
        sys.exit(1)


if __name__ == "__main__":
    main()