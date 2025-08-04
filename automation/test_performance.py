#!/usr/bin/env python3
"""
Performance tests for betslip conversion system.
Tests response time requirements, load handling, and resource usage.
"""

import sys
import os
import time
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add the automation directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Selection, ConversionResult
from market_matcher import create_market_matcher


class PerformanceTestSuite:
    """Performance test suite for betslip conversion system."""
    
    def __init__(self):
        self.test_results = []
        self.performance_metrics = {}
    
    def create_test_selection(self, game_id="test_game"):
        """Create a test selection for performance testing."""
        return Selection(
            game_id=game_id,
            home_team="Manchester United",
            away_team="Liverpool",
            market="Match Result",
            odds=2.50,
            event_date=datetime.now() + timedelta(hours=2),
            league="Premier League",
            original_text="Test selection for performance testing"
        )
    
    def create_mock_available_games(self, count=10):
        """Create mock available games for testing."""
        games = []
        for i in range(count):
            games.append({
                "home_team": f"Team {i}A",
                "away_team": f"Team {i}B",
                "markets": [
                    {"name": "Match Result", "odds": 2.0 + (i % 10) * 0.1},
                    {"name": "Over/Under 2.5", "odds": 1.8 + (i % 5) * 0.05},
                    {"name": "Both Teams to Score", "odds": 1.7 + (i % 3) * 0.1}
                ]
            })
        return games
    
    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    
    def test_single_selection_matching_performance(self):
        """Test performance of single selection matching."""
        print("\n=== Testing Single Selection Matching Performance ===")
        
        matcher = create_market_matcher()
        selection = self.create_test_selection()
        available_games = self.create_mock_available_games(50)  # 50 games to search through
        
        # Warm up
        matcher.match_selection(selection, "sportybet", available_games[:5])
        
        # Measure performance
        result, execution_time = self.measure_execution_time(
            matcher.match_selection, selection, "sportybet", available_games
        )
        
        print(f"Single selection matching time: {execution_time:.4f} seconds")
        print(f"Games searched: {len(available_games)}")
        print(f"Match found: {result.success}")
        print(f"Confidence: {result.confidence:.3f}")
        
        # Performance requirements
        assert execution_time < 1.0, f"Single selection matching too slow: {execution_time:.4f}s"
        assert execution_time < 0.5, f"Should be under 0.5s for 50 games: {execution_time:.4f}s"
        
        self.performance_metrics['single_selection_time'] = execution_time
        print("✅ Single selection matching performance test passed")
        
        return execution_time
    
    def test_multiple_selections_performance(self):
        """Test performance with multiple selections."""
        print("\n=== Testing Multiple Selections Performance ===")
        
        matcher = create_market_matcher()
        selections = [self.create_test_selection(f"game_{i}") for i in range(10)]
        available_games = self.create_mock_available_games(100)
        
        # Sequential processing
        start_time = time.time()
        sequential_results = []
        for selection in selections:
            result = matcher.match_selection(selection, "sportybet", available_games)
            sequential_results.append(result)
        sequential_time = time.time() - start_time
        
        print(f"Sequential processing time: {sequential_time:.4f} seconds")
        print(f"Average per selection: {sequential_time / len(selections):.4f} seconds")
        print(f"Selections processed: {len(selections)}")
        print(f"Successful matches: {sum(1 for r in sequential_results if r.success)}")
        
        # Performance requirements for multiple selections
        assert sequential_time < 30.0, f"Multiple selections too slow: {sequential_time:.4f}s"
        assert sequential_time / len(selections) < 3.0, f"Average per selection too slow"
        
        self.performance_metrics['multiple_selections_time'] = sequential_time
        self.performance_metrics['avg_selection_time'] = sequential_time / len(selections)
        
        print("✅ Multiple selections performance test passed")
        
        return sequential_time
    
    def test_parallel_processing_performance(self):
        """Test parallel processing performance improvement."""
        print("\n=== Testing Parallel Processing Performance ===")
        
        matcher = create_market_matcher()
        selections = [self.create_test_selection(f"parallel_game_{i}") for i in range(10)]
        available_games = self.create_mock_available_games(50)
        
        # Parallel processing using ThreadPoolExecutor
        start_time = time.time()
        parallel_results = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_selection = {
                executor.submit(matcher.match_selection, selection, "sportybet", available_games): selection
                for selection in selections
            }
            
            for future in as_completed(future_to_selection):
                result = future.result()
                parallel_results.append(result)
        
        parallel_time = time.time() - start_time
        
        print(f"Parallel processing time: {parallel_time:.4f} seconds")
        print(f"Workers used: 5")
        print(f"Selections processed: {len(selections)}")
        print(f"Successful matches: {sum(1 for r in parallel_results if r.success)}")
        
        # Compare with sequential baseline (if available)
        if 'multiple_selections_time' in self.performance_metrics:
            sequential_time = self.performance_metrics['multiple_selections_time']
            speedup = sequential_time / parallel_time
            print(f"Speedup vs sequential: {speedup:.2f}x")
            
            # Should show some improvement with parallel processing
            assert parallel_time <= sequential_time, "Parallel should not be slower than sequential"
        
        # Performance requirements
        assert parallel_time < 15.0, f"Parallel processing too slow: {parallel_time:.4f}s"
        
        self.performance_metrics['parallel_processing_time'] = parallel_time
        
        print("✅ Parallel processing performance test passed")
        
        return parallel_time
    
    def test_large_dataset_performance(self):
        """Test performance with large datasets."""
        print("\n=== Testing Large Dataset Performance ===")
        
        matcher = create_market_matcher()
        selection = self.create_test_selection("large_dataset_test")
        
        # Test with increasing dataset sizes
        dataset_sizes = [100, 500, 1000]
        
        for size in dataset_sizes:
            available_games = self.create_mock_available_games(size)
            
            result, execution_time = self.measure_execution_time(
                matcher.match_selection, selection, "sportybet", available_games
            )
            
            print(f"Dataset size: {size} games")
            print(f"  Execution time: {execution_time:.4f} seconds")
            print(f"  Games per second: {size / execution_time:.0f}")
            print(f"  Match found: {result.success}")
            
            # Performance should scale reasonably
            assert execution_time < 5.0, f"Too slow for {size} games: {execution_time:.4f}s"
            
            # Should process at least 100 games per second
            games_per_second = size / execution_time
            assert games_per_second > 100, f"Too slow processing rate: {games_per_second:.0f} games/s"
        
        print("✅ Large dataset performance test passed")
    
    def test_memory_usage_efficiency(self):
        """Test memory usage efficiency."""
        print("\n=== Testing Memory Usage Efficiency ===")
        
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"Initial memory usage: {initial_memory:.2f} MB")
        
        # Create large dataset and process it
        matcher = create_market_matcher()
        selections = [self.create_test_selection(f"memory_test_{i}") for i in range(100)]
        available_games = self.create_mock_available_games(1000)
        
        # Process selections
        results = []
        for selection in selections:
            result = matcher.match_selection(selection, "sportybet", available_games)
            results.append(result)
        
        # Check memory usage after processing
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Final memory usage: {final_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        print(f"Selections processed: {len(selections)}")
        print(f"Memory per selection: {memory_increase / len(selections):.3f} MB")
        
        # Memory usage should be reasonable
        assert memory_increase < 100, f"Memory usage too high: {memory_increase:.2f} MB"
        assert memory_increase / len(selections) < 1.0, "Memory per selection too high"
        
        self.performance_metrics['memory_increase'] = memory_increase
        
        print("✅ Memory usage efficiency test passed")
    
    def test_concurrent_load_handling(self):
        """Test handling of concurrent load."""
        print("\n=== Testing Concurrent Load Handling ===")
        
        matcher = create_market_matcher()
        available_games = self.create_mock_available_games(50)
        
        # Simulate concurrent requests
        num_concurrent_requests = 20
        results = []
        errors = []
        
        def process_request(request_id):
            try:
                selection = self.create_test_selection(f"concurrent_{request_id}")
                start_time = time.time()
                result = matcher.match_selection(selection, "sportybet", available_games)
                end_time = time.time()
                
                return {
                    'request_id': request_id,
                    'success': result.success,
                    'processing_time': end_time - start_time,
                    'confidence': result.confidence
                }
            except Exception as e:
                errors.append({'request_id': request_id, 'error': str(e)})
                return None
        
        # Execute concurrent requests
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_request, i) for i in range(num_concurrent_requests)]
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        total_time = time.time() - start_time
        
        print(f"Concurrent requests: {num_concurrent_requests}")
        print(f"Total processing time: {total_time:.4f} seconds")
        print(f"Successful requests: {len(results)}")
        print(f"Failed requests: {len(errors)}")
        print(f"Average response time: {sum(r['processing_time'] for r in results) / len(results):.4f} seconds")
        print(f"Requests per second: {num_concurrent_requests / total_time:.2f}")
        
        # Performance requirements for concurrent load
        assert len(errors) == 0, f"Should handle concurrent load without errors: {errors}"
        assert total_time < 10.0, f"Concurrent processing too slow: {total_time:.4f}s"
        assert len(results) == num_concurrent_requests, "All requests should complete successfully"
        
        # Average response time should be reasonable
        avg_response_time = sum(r['processing_time'] for r in results) / len(results)
        assert avg_response_time < 2.0, f"Average response time too slow: {avg_response_time:.4f}s"
        
        self.performance_metrics['concurrent_load_time'] = total_time
        self.performance_metrics['avg_concurrent_response_time'] = avg_response_time
        
        print("✅ Concurrent load handling test passed")
    
    def test_cache_performance_impact(self):
        """Test performance impact of caching."""
        print("\n=== Testing Cache Performance Impact ===")
        
        matcher = create_market_matcher()
        selection = self.create_test_selection("cache_test")
        available_games = self.create_mock_available_games(100)
        
        # First run (cold cache)
        result1, time1 = self.measure_execution_time(
            matcher.match_selection, selection, "sportybet", available_games
        )
        
        # Second run (warm cache - simulated by running same operation)
        result2, time2 = self.measure_execution_time(
            matcher.match_selection, selection, "sportybet", available_games
        )
        
        # Third run
        result3, time3 = self.measure_execution_time(
            matcher.match_selection, selection, "sportybet", available_games
        )
        
        print(f"First run (cold): {time1:.4f} seconds")
        print(f"Second run: {time2:.4f} seconds")
        print(f"Third run: {time3:.4f} seconds")
        
        # Results should be consistent
        assert result1.success == result2.success == result3.success
        assert abs(result1.confidence - result2.confidence) < 0.01
        
        # Performance should be consistent (no significant degradation)
        avg_time = (time1 + time2 + time3) / 3
        assert all(abs(t - avg_time) < avg_time * 0.5 for t in [time1, time2, time3]), \
            "Performance should be consistent across runs"
        
        self.performance_metrics['cache_consistency'] = {
            'times': [time1, time2, time3],
            'avg_time': avg_time
        }
        
        print("✅ Cache performance impact test passed")
    
    def test_stress_testing(self):
        """Perform stress testing with high load."""
        print("\n=== Stress Testing ===")
        
        matcher = create_market_matcher()
        available_games = self.create_mock_available_games(200)
        
        # High load parameters
        num_requests = 100
        max_workers = 20
        
        def stress_test_request(request_id):
            selection = self.create_test_selection(f"stress_{request_id}")
            start_time = time.time()
            
            try:
                result = matcher.match_selection(selection, "sportybet", available_games)
                processing_time = time.time() - start_time
                
                return {
                    'request_id': request_id,
                    'success': True,
                    'match_success': result.success,
                    'processing_time': processing_time,
                    'confidence': result.confidence
                }
            except Exception as e:
                processing_time = time.time() - start_time
                return {
                    'request_id': request_id,
                    'success': False,
                    'error': str(e),
                    'processing_time': processing_time
                }
        
        # Execute stress test
        print(f"Starting stress test with {num_requests} requests, {max_workers} workers...")
        
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(stress_test_request, i) for i in range(num_requests)]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        if successful_requests:
            avg_processing_time = sum(r['processing_time'] for r in successful_requests) / len(successful_requests)
            max_processing_time = max(r['processing_time'] for r in successful_requests)
            min_processing_time = min(r['processing_time'] for r in successful_requests)
        else:
            avg_processing_time = max_processing_time = min_processing_time = 0
        
        print(f"Stress test completed in {total_time:.2f} seconds")
        print(f"Total requests: {num_requests}")
        print(f"Successful requests: {len(successful_requests)}")
        print(f"Failed requests: {len(failed_requests)}")
        print(f"Success rate: {len(successful_requests) / num_requests * 100:.1f}%")
        print(f"Requests per second: {num_requests / total_time:.2f}")
        print(f"Average processing time: {avg_processing_time:.4f} seconds")
        print(f"Min processing time: {min_processing_time:.4f} seconds")
        print(f"Max processing time: {max_processing_time:.4f} seconds")
        
        # Stress test requirements
        success_rate = len(successful_requests) / num_requests
        assert success_rate > 0.95, f"Success rate too low under stress: {success_rate:.2%}"
        assert avg_processing_time < 5.0, f"Average processing time too slow under stress: {avg_processing_time:.4f}s"
        assert total_time < 60.0, f"Total stress test time too long: {total_time:.2f}s"
        
        self.performance_metrics['stress_test'] = {
            'total_time': total_time,
            'success_rate': success_rate,
            'avg_processing_time': avg_processing_time,
            'requests_per_second': num_requests / total_time
        }
        
        print("✅ Stress testing passed")
    
    def test_response_time_requirements(self):
        """Test specific response time requirements from the spec."""
        print("\n=== Testing Response Time Requirements ===")
        
        matcher = create_market_matcher()
        
        # Test 30-second requirement for standard betslips
        print("Testing 30-second requirement for standard betslips...")
        
        # Create a standard betslip scenario (5 selections)
        selections = [self.create_test_selection(f"standard_{i}") for i in range(5)]
        available_games = self.create_mock_available_games(100)
        
        start_time = time.time()
        results = []
        for selection in selections:
            result = matcher.match_selection(selection, "sportybet", available_games)
            results.append(result)
        total_time = time.time() - start_time
        
        print(f"Standard betslip (5 selections): {total_time:.2f} seconds")
        assert total_time < 30.0, f"Standard betslip processing too slow: {total_time:.2f}s"
        
        # Test individual selection response time (should be much faster)
        print("Testing individual selection response time...")
        
        single_selection = self.create_test_selection("single_test")
        start_time = time.time()
        result = matcher.match_selection(single_selection, "sportybet", available_games)
        single_time = time.time() - start_time
        
        print(f"Single selection: {single_time:.4f} seconds")
        assert single_time < 2.0, f"Single selection too slow: {single_time:.4f}s"
        
        # Test large betslip scenario (15 selections)
        print("Testing large betslip scenario...")
        
        large_selections = [self.create_test_selection(f"large_{i}") for i in range(15)]
        start_time = time.time()
        large_results = []
        for selection in large_selections:
            result = matcher.match_selection(selection, "sportybet", available_games)
            large_results.append(result)
        large_time = time.time() - start_time
        
        print(f"Large betslip (15 selections): {large_time:.2f} seconds")
        # Large betslips might take longer but should still be reasonable
        assert large_time < 60.0, f"Large betslip processing too slow: {large_time:.2f}s"
        
        self.performance_metrics['response_times'] = {
            'standard_betslip': total_time,
            'single_selection': single_time,
            'large_betslip': large_time
        }
        
        print("✅ Response time requirements test passed")
    
    def test_scalability_with_increasing_load(self):
        """Test system scalability with increasing load."""
        print("\n=== Testing Scalability with Increasing Load ===")
        
        matcher = create_market_matcher()
        available_games = self.create_mock_available_games(50)
        
        load_levels = [1, 5, 10, 20, 50]  # Number of concurrent requests
        scalability_results = {}
        
        for load_level in load_levels:
            print(f"Testing with {load_level} concurrent requests...")
            
            def process_request(request_id):
                selection = self.create_test_selection(f"scale_{request_id}")
                start_time = time.time()
                result = matcher.match_selection(selection, "sportybet", available_games)
                processing_time = time.time() - start_time
                return processing_time, result.success
            
            # Execute concurrent requests
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=load_level) as executor:
                futures = [executor.submit(process_request, i) for i in range(load_level)]
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            processing_times = [r[0] for r in results]
            success_count = sum(1 for r in results if r[1])
            
            avg_processing_time = sum(processing_times) / len(processing_times)
            throughput = load_level / total_time
            
            scalability_results[load_level] = {
                'total_time': total_time,
                'avg_processing_time': avg_processing_time,
                'throughput': throughput,
                'success_rate': success_count / load_level
            }
            
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Avg processing time: {avg_processing_time:.4f}s")
            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Success rate: {success_count}/{load_level}")
        
        # Analyze scalability
        print("\nScalability Analysis:")
        for load_level in load_levels:
            result = scalability_results[load_level]
            print(f"Load {load_level:2d}: {result['throughput']:6.2f} req/s, "
                  f"{result['avg_processing_time']:6.4f}s avg, "
                  f"{result['success_rate']:5.1%} success")
        
        # Verify scalability requirements
        # Throughput should not degrade significantly with moderate load increases
        low_load_throughput = scalability_results[5]['throughput']
        high_load_throughput = scalability_results[20]['throughput']
        throughput_degradation = (low_load_throughput - high_load_throughput) / low_load_throughput
        
        print(f"\nThroughput degradation (5->20 concurrent): {throughput_degradation:.1%}")
        assert throughput_degradation < 0.5, f"Throughput degradation too high: {throughput_degradation:.1%}"
        
        # Success rate should remain high
        for load_level, result in scalability_results.items():
            assert result['success_rate'] > 0.95, f"Success rate too low at load {load_level}: {result['success_rate']:.1%}"
        
        self.performance_metrics['scalability'] = scalability_results
        
        print("✅ Scalability test passed")
    
    def test_resource_utilization_efficiency(self):
        """Test resource utilization efficiency under different loads."""
        print("\n=== Testing Resource Utilization Efficiency ===")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        matcher = create_market_matcher()
        
        # Baseline measurements
        initial_cpu_percent = process.cpu_percent()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"Baseline - CPU: {initial_cpu_percent:.1f}%, Memory: {initial_memory:.1f} MB")
        
        # Test resource usage under different workloads
        workloads = [
            ("light", 10, 50),    # 10 selections, 50 games
            ("medium", 50, 100),  # 50 selections, 100 games
            ("heavy", 100, 200)   # 100 selections, 200 games
        ]
        
        resource_metrics = {}
        
        for workload_name, num_selections, num_games in workloads:
            print(f"\nTesting {workload_name} workload ({num_selections} selections, {num_games} games)...")
            
            selections = [self.create_test_selection(f"{workload_name}_{i}") for i in range(num_selections)]
            available_games = self.create_mock_available_games(num_games)
            
            # Measure resource usage during processing
            start_time = time.time()
            cpu_measurements = []
            memory_measurements = []
            
            def measure_resources():
                while time.time() - start_time < 10:  # Measure for up to 10 seconds
                    cpu_measurements.append(process.cpu_percent())
                    memory_measurements.append(process.memory_info().rss / 1024 / 1024)
                    time.sleep(0.1)
            
            # Start resource monitoring in background
            import threading
            monitor_thread = threading.Thread(target=measure_resources)
            monitor_thread.start()
            
            # Process selections
            processing_start = time.time()
            results = []
            for selection in selections:
                result = matcher.match_selection(selection, "sportybet", available_games)
                results.append(result)
            processing_time = time.time() - processing_start
            
            # Wait for monitoring to complete
            monitor_thread.join()
            
            # Calculate resource metrics
            if cpu_measurements and memory_measurements:
                avg_cpu = sum(cpu_measurements) / len(cpu_measurements)
                max_cpu = max(cpu_measurements)
                avg_memory = sum(memory_measurements) / len(memory_measurements)
                max_memory = max(memory_measurements)
                memory_increase = max_memory - initial_memory
            else:
                avg_cpu = max_cpu = avg_memory = max_memory = memory_increase = 0
            
            successful_results = sum(1 for r in results if r.success)
            
            resource_metrics[workload_name] = {
                'processing_time': processing_time,
                'avg_cpu_percent': avg_cpu,
                'max_cpu_percent': max_cpu,
                'avg_memory_mb': avg_memory,
                'max_memory_mb': max_memory,
                'memory_increase_mb': memory_increase,
                'selections_processed': num_selections,
                'successful_matches': successful_results,
                'efficiency_score': successful_results / processing_time if processing_time > 0 else 0
            }
            
            print(f"  Processing time: {processing_time:.2f}s")
            print(f"  CPU usage: {avg_cpu:.1f}% avg, {max_cpu:.1f}% max")
            print(f"  Memory usage: {avg_memory:.1f} MB avg, {max_memory:.1f} MB max")
            print(f"  Memory increase: {memory_increase:.1f} MB")
            print(f"  Efficiency: {resource_metrics[workload_name]['efficiency_score']:.2f} matches/second")
        
        # Analyze resource efficiency
        print(f"\nResource Efficiency Analysis:")
        for workload_name, metrics in resource_metrics.items():
            print(f"{workload_name.capitalize():6} workload: "
                  f"{metrics['efficiency_score']:5.2f} matches/s, "
                  f"{metrics['avg_cpu_percent']:4.1f}% CPU, "
                  f"{metrics['memory_increase_mb']:5.1f} MB increase")
        
        # Verify resource efficiency requirements
        for workload_name, metrics in resource_metrics.items():
            # CPU usage should be reasonable
            assert metrics['max_cpu_percent'] < 80, f"{workload_name} workload CPU usage too high: {metrics['max_cpu_percent']:.1f}%"
            
            # Memory increase should be reasonable
            assert metrics['memory_increase_mb'] < 100, f"{workload_name} workload memory increase too high: {metrics['memory_increase_mb']:.1f} MB"
            
            # Efficiency should improve or stay reasonable with larger workloads
            assert metrics['efficiency_score'] > 1.0, f"{workload_name} workload efficiency too low: {metrics['efficiency_score']:.2f}"
        
        self.performance_metrics['resource_utilization'] = resource_metrics
        
        print("✅ Resource utilization efficiency test passed")
    
    def generate_performance_report(self):
        """Generate a comprehensive performance report."""
        print("\n" + "="*80)
        print("PERFORMANCE TEST REPORT")
        print("="*80)
        
        if not self.performance_metrics:
            print("No performance metrics collected.")
            return
        
        print(f"Test execution completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Single selection performance
        if 'single_selection_time' in self.performance_metrics:
            time_ms = self.performance_metrics['single_selection_time'] * 1000
            print(f"Single Selection Matching: {time_ms:.2f} ms")
        
        # Multiple selections performance
        if 'multiple_selections_time' in self.performance_metrics:
            total_time = self.performance_metrics['multiple_selections_time']
            avg_time = self.performance_metrics.get('avg_selection_time', 0)
            print(f"Multiple Selections (10): {total_time:.3f} s (avg: {avg_time:.3f} s per selection)")
        
        # Parallel processing performance
        if 'parallel_processing_time' in self.performance_metrics:
            parallel_time = self.performance_metrics['parallel_processing_time']
            print(f"Parallel Processing (10 selections, 5 workers): {parallel_time:.3f} s")
        
        # Memory usage
        if 'memory_increase' in self.performance_metrics:
            memory_mb = self.performance_metrics['memory_increase']
            print(f"Memory Usage Increase: {memory_mb:.2f} MB")
        
        # Concurrent load handling
        if 'concurrent_load_time' in self.performance_metrics:
            concurrent_time = self.performance_metrics['concurrent_load_time']
            avg_response = self.performance_metrics['avg_concurrent_response_time']
            print(f"Concurrent Load (20 requests): {concurrent_time:.3f} s (avg response: {avg_response:.3f} s)")
        
        # Stress test results
        if 'stress_test' in self.performance_metrics:
            stress_data = self.performance_metrics['stress_test']
            print(f"Stress Test (100 requests): {stress_data['total_time']:.2f} s")
            print(f"  Success Rate: {stress_data['success_rate']:.1%}")
            print(f"  Requests/Second: {stress_data['requests_per_second']:.2f}")
            print(f"  Avg Processing Time: {stress_data['avg_processing_time']:.3f} s")
        
        print("\n" + "="*80)
        print("PERFORMANCE SUMMARY")
        print("="*80)
        
        # Overall assessment
        issues = []
        
        if 'single_selection_time' in self.performance_metrics:
            if self.performance_metrics['single_selection_time'] > 0.5:
                issues.append("Single selection matching is slow")
        
        if 'avg_selection_time' in self.performance_metrics:
            if self.performance_metrics['avg_selection_time'] > 3.0:
                issues.append("Average selection processing time is too high")
        
        if 'memory_increase' in self.performance_metrics:
            if self.performance_metrics['memory_increase'] > 50:
                issues.append("Memory usage is high")
        
        if 'stress_test' in self.performance_metrics:
            stress_data = self.performance_metrics['stress_test']
            if stress_data['success_rate'] < 0.95:
                issues.append("Success rate under stress is low")
        
        if issues:
            print("⚠️  Performance Issues Detected:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ All performance requirements met!")
        
        print("\nRecommendations:")
        if 'parallel_processing_time' in self.performance_metrics and 'multiple_selections_time' in self.performance_metrics:
            speedup = self.performance_metrics['multiple_selections_time'] / self.performance_metrics['parallel_processing_time']
            if speedup < 2.0:
                print("   - Consider optimizing parallel processing implementation")
            else:
                print("   - Parallel processing shows good performance improvement")
        
        if 'memory_increase' in self.performance_metrics:
            if self.performance_metrics['memory_increase'] > 20:
                print("   - Consider implementing memory optimization strategies")
            else:
                print("   - Memory usage is within acceptable limits")
        
        print("   - Monitor performance in production environment")
        print("   - Consider implementing performance monitoring and alerting")
    
    def run_all_performance_tests(self):
        """Run all performance tests."""
        print("="*80)
        print("BETSLIP CONVERTER - PERFORMANCE TEST SUITE")
        print("="*80)
        
        tests = [
            self.test_single_selection_matching_performance,
            self.test_multiple_selections_performance,
            self.test_parallel_processing_performance,
            self.test_large_dataset_performance,
            self.test_memory_usage_efficiency,
            self.test_concurrent_load_handling,
            self.test_cache_performance_impact,
            self.test_stress_testing
        ]
        
        passed_tests = 0
        failed_tests = 0
        
        for test in tests:
            try:
                test()
                passed_tests += 1
            except Exception as e:
                print(f"❌ {test.__name__} failed: {str(e)}")
                failed_tests += 1
        
        print(f"\n{'='*80}")
        print(f"PERFORMANCE TESTS COMPLETED")
        print(f"{'='*80}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Total: {passed_tests + failed_tests}")
        
        # Generate comprehensive report
        self.generate_performance_report()
        
        return failed_tests == 0


def main():
    """Main function to run performance tests."""
    suite = PerformanceTestSuite()
    success = suite.run_all_performance_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()