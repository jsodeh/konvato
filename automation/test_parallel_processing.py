#!/usr/bin/env python3
"""
Test script for parallel browser processing functionality.
"""

import asyncio
import time
import os
import pytest
from typing import List
from datetime import datetime
from parallel_browser_manager import ParallelBrowserManager, ConversionTask
from models import Selection

@pytest.mark.asyncio
async def test_browser_pool():
    """Test browser instance pooling"""
    print("Testing browser instance pooling...")
    
    manager = ParallelBrowserManager(max_concurrent=2, max_memory_mb=1024)
    
    try:
        # Test getting multiple instances
        instance1 = await manager.browser_pool.get_instance()
        print(f"Got instance 1: {instance1.id}")
        
        instance2 = await manager.browser_pool.get_instance()
        print(f"Got instance 2: {instance2.id}")
        
        # Release instances
        manager.browser_pool.release_instance(instance1)
        manager.browser_pool.release_instance(instance2)
        
        print("Browser pool test completed successfully")
        
    except Exception as e:
        print(f"Browser pool test failed: {e}")
    finally:
        await manager.shutdown()

@pytest.mark.asyncio
async def test_conversion_queue():
    """Test conversion task queue"""
    print("\nTesting conversion queue...")
    
    manager = ParallelBrowserManager(max_concurrent=2)
    
    try:
        # Add test tasks to queue
        task1_id = await manager.convert_betslip_parallel("TEST123", "bet9ja", "sportybet")
        print(f"Added task 1: {task1_id}")
        
        task2_id = await manager.convert_betslip_parallel("TEST456", "sportybet", "betway")
        print(f"Added task 2: {task2_id}")
        
        # Check queue status
        status = manager.get_queue_status()
        print(f"Queue status: {status}")
        
        # Wait a bit and check for results (they will likely fail due to invalid codes, but that's expected)
        await asyncio.sleep(5)
        
        result1 = manager.get_conversion_result(task1_id)
        result2 = manager.get_conversion_result(task2_id)
        
        print(f"Task 1 result: {'Found' if result1 else 'Not found'}")
        print(f"Task 2 result: {'Found' if result2 else 'Not found'}")
        
        print("Conversion queue test completed")
        
    except Exception as e:
        print(f"Conversion queue test failed: {e}")
    finally:
        await manager.shutdown()

@pytest.mark.asyncio
async def test_parallel_selections():
    """Test parallel processing of multiple selections"""
    print("\nTesting parallel selection processing...")
    
    manager = ParallelBrowserManager(max_concurrent=2)
    
    try:
        # Create test selections
        selections = [
            Selection(
                game_id="test1",
                home_team="Manchester United",
                away_team="Liverpool",
                market="Match Result",
                odds=2.50,
                event_date=datetime.now(),
                league="Premier League",
                original_text="Man United vs Liverpool - Match Result"
            ),
            Selection(
                game_id="test2",
                home_team="Chelsea",
                away_team="Arsenal",
                market="Over/Under 2.5",
                odds=1.85,
                event_date=datetime.now(),
                league="Premier League",
                original_text="Chelsea vs Arsenal - Over/Under 2.5"
            )
        ]
        
        # Process selections in parallel (this will likely fail due to no actual browser automation, but tests the structure)
        start_time = time.time()
        results = await manager.process_multiple_selections_parallel(selections, "sportybet")
        processing_time = time.time() - start_time
        
        print(f"Processed {len(results)} selections in {processing_time:.2f} seconds")
        
        for selection, success in results:
            print(f"Selection {selection.game_id}: {'Success' if success else 'Failed'}")
        
        print("Parallel selection processing test completed")
        
    except Exception as e:
        print(f"Parallel selection processing test failed: {e}")
    finally:
        await manager.shutdown()

@pytest.mark.asyncio
async def test_memory_management():
    """Test memory management and cleanup"""
    print("\nTesting memory management...")
    
    manager = ParallelBrowserManager(max_concurrent=2, max_memory_mb=512)  # Low memory limit for testing
    
    try:
        # Check initial memory usage
        initial_memory = manager.browser_pool.get_memory_usage()
        print(f"Initial memory usage: {initial_memory:.2f} MB")
        
        # Create some instances
        instances = []
        for i in range(2):
            instance = await manager.browser_pool.get_instance()
            instances.append(instance)
            print(f"Created instance {i+1}: {instance.id}")
        
        # Check memory after creating instances
        current_memory = manager.browser_pool.get_memory_usage()
        print(f"Memory usage after creating instances: {current_memory:.2f} MB")
        
        # Check memory pressure
        memory_pressure = manager.browser_pool.check_memory_pressure()
        print(f"Memory pressure detected: {memory_pressure}")
        
        # Release instances
        for instance in instances:
            manager.browser_pool.release_instance(instance)
        
        # Cleanup
        manager.browser_pool.cleanup_instances()
        
        final_memory = manager.browser_pool.get_memory_usage()
        print(f"Final memory usage: {final_memory:.2f} MB")
        
        print("Memory management test completed")
        
    except Exception as e:
        print(f"Memory management test failed: {e}")
    finally:
        await manager.shutdown()

@pytest.mark.asyncio
async def test_queue_status():
    """Test queue status monitoring"""
    print("\nTesting queue status monitoring...")
    
    manager = ParallelBrowserManager(max_concurrent=2)
    
    try:
        # Get initial status
        status = manager.get_queue_status()
        print(f"Initial queue status: {status}")
        
        # Add some tasks
        task_ids = []
        for i in range(3):
            task_id = await manager.convert_betslip_parallel(f"TEST{i}", "bet9ja", "sportybet")
            task_ids.append(task_id)
        
        # Check status after adding tasks
        status = manager.get_queue_status()
        print(f"Status after adding tasks: {status}")
        
        # Wait a bit for processing
        await asyncio.sleep(2)
        
        # Check final status
        status = manager.get_queue_status()
        print(f"Final status: {status}")
        
        print("Queue status monitoring test completed")
        
    except Exception as e:
        print(f"Queue status monitoring test failed: {e}")
    finally:
        await manager.shutdown()

async def main():
    """Run all tests"""
    print("Starting parallel processing tests...")
    print("=" * 50)
    
    # Only run tests if OpenAI API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("OPENAI_API_KEY not set - skipping tests that require browser automation")
        print("Testing only the queue and memory management components...")
        
        # Test basic functionality without browser automation
        await test_memory_management()
        return
    
    # Run all tests
    await test_browser_pool()
    await test_conversion_queue()
    await test_parallel_selections()
    await test_memory_management()
    await test_queue_status()
    
    print("\n" + "=" * 50)
    print("All parallel processing tests completed!")

if __name__ == "__main__":
    asyncio.run(main())