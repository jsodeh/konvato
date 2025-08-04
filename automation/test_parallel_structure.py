#!/usr/bin/env python3
"""
Test script for parallel processing structure without requiring OpenAI API.
Tests the queue, memory management, and basic class structure.
"""

import asyncio
import time
import threading
from queue import Queue, Empty
from datetime import datetime
from parallel_browser_manager import ConversionQueue, ConversionTask

def test_conversion_queue():
    """Test the conversion queue functionality"""
    print("Testing ConversionQueue...")
    
    queue = ConversionQueue(max_size=5)
    
    # Test adding tasks
    task1 = ConversionTask("task1", "TEST123", "bet9ja", "sportybet")
    task2 = ConversionTask("task2", "TEST456", "sportybet", "betway")
    
    assert queue.add_task(task1) == True, "Should be able to add task1"
    assert queue.add_task(task2) == True, "Should be able to add task2"
    
    # Test queue size
    assert queue.get_queue_size() == 2, f"Queue size should be 2, got {queue.get_queue_size()}"
    
    # Test getting tasks
    retrieved_task = queue.get_task()
    assert retrieved_task is not None, "Should retrieve a task"
    assert retrieved_task.task_id == "task1", f"Should get task1, got {retrieved_task.task_id}"
    
    # Test processing count
    assert queue.get_processing_count() == 1, f"Processing count should be 1, got {queue.get_processing_count()}"
    
    # Test completing task
    queue.complete_task("task1", {"success": True})
    result = queue.get_result("task1")
    assert result is not None, "Should get result for completed task"
    assert result["success"] == True, "Result should indicate success"
    
    print("ConversionQueue test passed!")

def test_conversion_task():
    """Test the ConversionTask dataclass"""
    print("Testing ConversionTask...")
    
    # Test task creation
    task = ConversionTask("test_task", "ABC123", "bet9ja", "sportybet", priority=1)
    
    assert task.task_id == "test_task", f"Task ID should be 'test_task', got {task.task_id}"
    assert task.betslip_code == "ABC123", f"Betslip code should be 'ABC123', got {task.betslip_code}"
    assert task.source_bookmaker == "bet9ja", f"Source should be 'bet9ja', got {task.source_bookmaker}"
    assert task.destination_bookmaker == "sportybet", f"Destination should be 'sportybet', got {task.destination_bookmaker}"
    assert task.priority == 1, f"Priority should be 1, got {task.priority}"
    assert task.created_at is not None, "Created_at should be set automatically"
    
    # Test task with default values
    task2 = ConversionTask("test_task2", "DEF456", "sportybet", "betway")
    assert task2.priority == 0, f"Default priority should be 0, got {task2.priority}"
    assert task2.created_at is not None, "Created_at should be set automatically"
    
    print("ConversionTask test passed!")

def test_queue_threading():
    """Test queue behavior with multiple threads"""
    print("Testing queue with multiple threads...")
    
    queue = ConversionQueue(max_size=10)
    results = []
    
    def producer():
        """Producer thread that adds tasks to queue"""
        for i in range(5):
            task = ConversionTask(f"task_{i}", f"CODE{i}", "bet9ja", "sportybet")
            queue.add_task(task)
            time.sleep(0.1)
    
    def consumer():
        """Consumer thread that processes tasks from queue"""
        processed = 0
        while processed < 5:
            task = queue.get_task()
            if task:
                # Simulate processing
                time.sleep(0.05)
                queue.complete_task(task.task_id, {"success": True, "processed_by": threading.current_thread().name})
                results.append(task.task_id)
                processed += 1
    
    # Start producer and consumer threads
    producer_thread = threading.Thread(target=producer)
    consumer_thread = threading.Thread(target=consumer)
    
    producer_thread.start()
    consumer_thread.start()
    
    # Wait for completion
    producer_thread.join()
    consumer_thread.join()
    
    # Verify results
    assert len(results) == 5, f"Should have processed 5 tasks, got {len(results)}"
    assert queue.get_queue_size() == 0, f"Queue should be empty, got {queue.get_queue_size()}"
    assert queue.get_processing_count() == 0, f"No tasks should be processing, got {queue.get_processing_count()}"
    
    # Check that all results are available
    for i in range(5):
        result = queue.get_result(f"task_{i}")
        assert result is not None, f"Should have result for task_{i}"
        assert result["success"] == True, f"Task_{i} should be successful"
    
    print("Queue threading test passed!")

def test_queue_overflow():
    """Test queue behavior when it reaches capacity"""
    print("Testing queue overflow handling...")
    
    queue = ConversionQueue(max_size=2)
    
    # Add tasks up to capacity
    task1 = ConversionTask("task1", "CODE1", "bet9ja", "sportybet")
    task2 = ConversionTask("task2", "CODE2", "bet9ja", "sportybet")
    task3 = ConversionTask("task3", "CODE3", "bet9ja", "sportybet")
    
    assert queue.add_task(task1) == True, "Should add task1"
    assert queue.add_task(task2) == True, "Should add task2"
    assert queue.add_task(task3) == False, "Should reject task3 (queue full)"
    
    assert queue.get_queue_size() == 2, f"Queue size should be 2, got {queue.get_queue_size()}"
    
    print("Queue overflow test passed!")

def test_task_timing():
    """Test task timing and creation timestamps"""
    print("Testing task timing...")
    
    start_time = datetime.now()
    task = ConversionTask("timed_task", "TIME123", "bet9ja", "sportybet")
    end_time = datetime.now()
    
    # Check that created_at is within reasonable bounds
    assert start_time <= task.created_at <= end_time, "Task creation time should be within test bounds"
    
    # Test that different tasks have different timestamps (assuming some time passes)
    time.sleep(0.001)  # Small delay
    task2 = ConversionTask("timed_task2", "TIME456", "bet9ja", "sportybet")
    
    assert task2.created_at > task.created_at, "Second task should have later timestamp"
    
    print("Task timing test passed!")

def main():
    """Run all structure tests"""
    print("Starting parallel processing structure tests...")
    print("=" * 50)
    
    try:
        test_conversion_task()
        test_conversion_queue()
        test_queue_threading()
        test_queue_overflow()
        test_task_timing()
        
        print("\n" + "=" * 50)
        print("All structure tests passed successfully!")
        
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)