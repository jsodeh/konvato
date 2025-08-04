#!/usr/bin/env python3
"""
Comprehensive test runner for the betslip conversion system.
Runs all unit tests and generates a summary report.
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from typing import List, Dict, Tuple


class TestResult:
    """Represents the result of a test execution."""
    
    def __init__(self, name: str, passed: bool, duration: float, output: str = "", error: str = ""):
        self.name = name
        self.passed = passed
        self.duration = duration
        self.output = output
        self.error = error


class TestRunner:
    """Main test runner class."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
    
    def run_python_test(self, test_file: str, test_name: str) -> TestResult:
        """Run a Python test file and return the result."""
        print(f"\n{'='*60}")
        print(f"Running {test_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Change to automation directory for Python tests
            if test_file.startswith('automation/'):
                cwd = 'automation'
                test_file = test_file.replace('automation/', '')
            else:
                cwd = '.'
            
            result = subprocess.run(
                [sys.executable, test_file],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ {test_name} PASSED ({duration:.2f}s)")
                return TestResult(test_name, True, duration, result.stdout, result.stderr)
            else:
                print(f"❌ {test_name} FAILED ({duration:.2f}s)")
                print(f"Error output: {result.stderr}")
                return TestResult(test_name, False, duration, result.stdout, result.stderr)
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"❌ {test_name} TIMEOUT ({duration:.2f}s)")
            return TestResult(test_name, False, duration, "", "Test timed out after 60 seconds")
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ {test_name} ERROR ({duration:.2f}s)")
            print(f"Exception: {str(e)}")
            return TestResult(test_name, False, duration, "", str(e))
    
    def run_node_test(self, test_file: str, test_name: str) -> TestResult:
        """Run a Node.js test file and return the result."""
        print(f"\n{'='*60}")
        print(f"Running {test_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Change to appropriate directory for Node tests
            if test_file.startswith('client/'):
                cwd = 'client'
                test_file = test_file.replace('client/', '')
            elif test_file.startswith('server/'):
                cwd = 'server'
                test_file = test_file.replace('server/', '')
            else:
                cwd = '.'
            
            result = subprocess.run(
                ['node', test_file],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ {test_name} PASSED ({duration:.2f}s)")
                return TestResult(test_name, True, duration, result.stdout, result.stderr)
            else:
                print(f"❌ {test_name} FAILED ({duration:.2f}s)")
                print(f"Error output: {result.stderr}")
                return TestResult(test_name, False, duration, result.stdout, result.stderr)
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"❌ {test_name} TIMEOUT ({duration:.2f}s)")
            return TestResult(test_name, False, duration, "", "Test timed out after 60 seconds")
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ {test_name} ERROR ({duration:.2f}s)")
            print(f"Exception: {str(e)}")
            return TestResult(test_name, False, duration, "", str(e))
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        print("Checking dependencies...")
        
        # Check Python
        try:
            result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
            print(f"✅ Python: {result.stdout.strip()}")
        except Exception:
            print("❌ Python not found")
            return False
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            print(f"✅ Node.js: {result.stdout.strip()}")
        except Exception:
            print("❌ Node.js not found")
            return False
        
        # Check if test files exist
        test_files = [
            'automation/test_models_comprehensive.py',
            'automation/test_helper_methods.py',
            'automation/test_market_matcher.py',
            'automation/test_bookmaker_adapters.py',
            'automation/test_betslip_creation_unit.py',
            'automation/test_integration_e2e.py',
            'automation/test_performance.py',
            'automation/test_adapter_integration.py',
            'automation/test_parallel_processing.py',
            'automation/test_parallel_structure.py',
            'client/test_validation.js',
            'client/test_react_components.js',
            'server/test_api_comprehensive.js',
            'server/test_cache.js',
            'server/test_endpoint.js'
        ]
        
        missing_files = []
        for test_file in test_files:
            if not os.path.exists(test_file):
                missing_files.append(test_file)
        
        if missing_files:
            print("❌ Missing test files:")
            for file in missing_files:
                print(f"   - {file}")
            return False
        
        print("✅ All test files found")
        return True
    
    def run_all_tests(self) -> None:
        """Run all unit tests."""
        self.start_time = datetime.now()
        
        print("="*80)
        print("BETSLIP CONVERTER - COMPREHENSIVE TEST SUITE")
        print("="*80)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check dependencies first
        if not self.check_dependencies():
            print("\n❌ Dependency check failed. Please install required dependencies.")
            return
        
        # Define all tests to run
        tests = [
            # Python tests - Core functionality
            ('automation/test_models_comprehensive.py', 'Models Comprehensive Tests'),
            ('automation/test_helper_methods.py', 'Helper Methods Tests'),
            ('automation/test_market_matcher.py', 'Market Matcher Tests'),
            ('automation/test_bookmaker_adapters.py', 'Bookmaker Adapters Tests'),
            ('automation/test_betslip_creation_unit.py', 'Betslip Creation Unit Tests'),
            
            # Python tests - Integration and Performance
            ('automation/test_integration_e2e.py', 'End-to-End Integration Tests'),
            ('automation/test_performance.py', 'Performance Tests'),
            ('automation/test_adapter_integration.py', 'Adapter Integration Tests'),
            ('automation/test_parallel_processing.py', 'Parallel Processing Tests'),
            ('automation/test_parallel_structure.py', 'Parallel Structure Tests'),
            
            # JavaScript tests
            ('client/test_validation.js', 'Frontend Validation Tests'),
            ('client/test_react_components.js', 'React Components Tests'),
            ('server/test_cache.js', 'Cache Manager Tests'),
            ('server/test_api_comprehensive.js', 'API Endpoints Tests'),
            ('server/test_endpoint.js', 'API Endpoint Tests')
        ]
        
        # Run each test
        for test_file, test_name in tests:
            if test_file.endswith('.py'):
                result = self.run_python_test(test_file, test_name)
            else:
                result = self.run_node_test(test_file, test_name)
            
            self.results.append(result)
        
        self.end_time = datetime.now()
        self.generate_report()
    
    def generate_report(self) -> None:
        """Generate a comprehensive test report."""
        print(f"\n{'='*80}")
        print("TEST EXECUTION SUMMARY")
        print(f"{'='*80}")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        total_duration = sum(r.duration for r in self.results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Finished: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Elapsed: {(self.end_time - self.start_time).total_seconds():.2f}s")
        
        # Detailed results
        print(f"\n{'='*80}")
        print("DETAILED RESULTS")
        print(f"{'='*80}")
        
        for result in self.results:
            status = "PASS" if result.passed else "FAIL"
            print(f"{status:4} | {result.name:40} | {result.duration:6.2f}s")
        
        # Failed tests details
        if failed_tests > 0:
            print(f"\n{'='*80}")
            print("FAILED TESTS DETAILS")
            print(f"{'='*80}")
            
            for result in self.results:
                if not result.passed:
                    print(f"\n❌ {result.name}")
                    print(f"Duration: {result.duration:.2f}s")
                    if result.error:
                        print(f"Error: {result.error}")
                    if result.output:
                        print(f"Output: {result.output[:500]}...")  # Truncate long output
        
        # Test coverage summary
        print(f"\n{'='*80}")
        print("TEST COVERAGE SUMMARY")
        print(f"{'='*80}")
        
        categories = {
            'Data Models': ['Models Comprehensive Tests'],
            'Business Logic': ['Market Matcher Tests', 'Helper Methods Tests'],
            'External Integrations': ['Bookmaker Adapters Tests', 'Betslip Creation Unit Tests', 'Adapter Integration Tests'],
            'Integration & E2E': ['End-to-End Integration Tests', 'Parallel Processing Tests', 'Parallel Structure Tests'],
            'Performance': ['Performance Tests'],
            'Frontend': ['Frontend Validation Tests', 'React Components Tests'],
            'Backend': ['API Endpoints Tests', 'API Endpoint Tests', 'Cache Manager Tests']
        }
        
        for category, test_names in categories.items():
            category_results = [r for r in self.results if r.name in test_names]
            if category_results:
                category_passed = sum(1 for r in category_results if r.passed)
                category_total = len(category_results)
                category_rate = (category_passed / category_total) * 100
                print(f"{category:20} | {category_passed:2}/{category_total:2} | {category_rate:5.1f}%")
        
        # Recommendations
        print(f"\n{'='*80}")
        print("RECOMMENDATIONS")
        print(f"{'='*80}")
        
        if failed_tests == 0:
            print("✅ All tests passed! The codebase appears to be in good shape.")
            print("✅ Consider adding more edge case tests as the system evolves.")
        else:
            print("❌ Some tests failed. Please address the following:")
            for result in self.results:
                if not result.passed:
                    print(f"   - Fix issues in: {result.name}")
            
            if failed_tests > total_tests * 0.5:
                print("⚠️  High failure rate detected. Consider reviewing system architecture.")
            elif failed_tests > total_tests * 0.2:
                print("⚠️  Moderate failure rate. Focus on stabilizing core functionality.")
            else:
                print("ℹ️  Low failure rate. Address specific issues and re-run tests.")
        
        # Performance insights
        slowest_tests = sorted(self.results, key=lambda r: r.duration, reverse=True)[:3]
        if slowest_tests:
            print(f"\n📊 Slowest Tests:")
            for result in slowest_tests:
                print(f"   - {result.name}: {result.duration:.2f}s")
        
        print(f"\n{'='*80}")
        print("TEST EXECUTION COMPLETE")
        print(f"{'='*80}")
    
    def save_report(self, filename: str = None) -> None:
        """Save the test report to a file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"test_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w') as f:
                f.write("BETSLIP CONVERTER - TEST REPORT\n")
                f.write("="*50 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                total_tests = len(self.results)
                passed_tests = sum(1 for r in self.results if r.passed)
                failed_tests = total_tests - passed_tests
                
                f.write(f"Summary:\n")
                f.write(f"  Total Tests: {total_tests}\n")
                f.write(f"  Passed: {passed_tests}\n")
                f.write(f"  Failed: {failed_tests}\n")
                f.write(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%\n\n")
                
                f.write("Detailed Results:\n")
                for result in self.results:
                    status = "PASS" if result.passed else "FAIL"
                    f.write(f"  {status} | {result.name} | {result.duration:.2f}s\n")
                
                if failed_tests > 0:
                    f.write("\nFailed Tests:\n")
                    for result in self.results:
                        if not result.passed:
                            f.write(f"  - {result.name}: {result.error}\n")
            
            print(f"📄 Test report saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save report: {str(e)}")


def main():
    """Main function."""
    runner = TestRunner()
    
    # Check if we should save report
    save_report = '--save-report' in sys.argv
    
    try:
        runner.run_all_tests()
        
        if save_report:
            runner.save_report()
        
        # Exit with appropriate code
        failed_tests = sum(1 for r in runner.results if not r.passed)
        sys.exit(0 if failed_tests == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n\n❌ Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()