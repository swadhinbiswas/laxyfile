#!/usr/bin/env python3
"""
Performance Optimization Test Suite

Tests all performance optimizations implemented in task 13.2:
- Startup time optimization
- Memory usage optimization
- UI animation optimization
- AI response caching
- Large directory handling
"""

import asyncio
import time
import psutil
import tempfile
from pathlib import Path
from typing import Dict, Any
import sys
import os

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from laxyfile.core.performance_optimizer import PerformanceOptimizer, PerformanceConfig
from laxyfile.core.startup_optimizer import StartupOptimizer, StartupConfig
from laxyfile.core.advanced_file_manager import AdvancedFileManager
from laxyfile.ui.animation_optimizer import AnimationOptimizer, AnimationConfig, AnimationQuality
from laxyfile.ai.advanced_assistant import AdvancedAIAssistant, ResponseCache
from laxyfile.core.config import Config
from laxyfile.utils.logger import Logger


class PerformanceTestSuite:
    """Comprehensive performance optimization test suite"""

    def __init__(self):
        self.logger = Logger()
        self.test_results = {}
        self.config = Config()

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance optimization tests"""
        self.logger.info("Starting performance optimization test suite")

        tests = [
            ("startup_optimization", self.test_startup_optimization),
            ("memory_optimization", self.test_memory_optimization),
            ("animation_optimization", self.test_animation_optimization),
            ("ai_caching", self.test_ai_caching),
            ("large_directory_handling", self.test_large_directory_handling),
            ("performance_monitoring", self.test_performance_monitoring)
        ]

        for test_name, test_func in tests:
            try:
                self.logger.info(f"Running test: {test_name}")
                start_time = time.time()
                result = await test_func()
                duration = time.time() - start_time

                self.test_results[test_name] = {
                    'status': 'passed' if result['success'] else 'failed',
                    'duration': duration,
                    'details': result
                }

                self.logger.info(f"Test {test_name}: {'PASSED' if result['success'] else 'FAILED'} ({duration:.3f}s)")

            except Exception as e:
                self.test_results[test_name] = {
                    'status': 'error',
                    'duration': 0,
                    'error': str(e)
                }
                self.logger.error(f"Test {test_name} failed with error: {e}")

        return self.test_results

    async def test_startup_optimization(self) -> Dict[str, Any]:
        """Test startup optimization system"""
        try:
            # Test startup optimizer
            config = StartupConfig(
                enable_lazy_loading=True,
                enable_preloading=True,
                enable_background_init=True,
                max_startup_threads=2
            )

            optimizer = StartupOptimizer(config)

            # Register test components
            def dummy_init():
                time.sleep(0.1)  # Simulate initialization time
                return "initialized"

            optimizer.register_component("test_critical", dummy_init, priority=10)
            optimizer.register_component("test_preload", dummy_init, priority=5)
            optimizer.register_component("test_background", dummy_init, priority=1)

            # Test startup sequence
            start_time = time.time()
            startup_stats = await optimizer.optimize_startup()
            total_time = time.time() - start_time

            # Verify results
            success = (
                startup_stats['total_time'] > 0 and
                startup_stats['critical_time'] > 0 and
                len(optimizer.initialized_components) > 0 and
                total_time < 5.0  # Should complete quickly
            )

            optimizer.shutdown()

            return {
                'success': success,
                'startup_time': total_time,
                'stats': startup_stats,
                'components_initialized': len(optimizer.initialized_components)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_memory_optimization(self) -> Dict[str, Any]:
        """Test memory optimization system"""
        try:
            config = PerformanceConfig(
                memory_threshold_mb=100,
                gc_interval_seconds=1
            )

            optimizer = PerformanceOptimizer(config)
            await optimizer.initialize()

            # Get initial memory usage
            initial_memory = optimizer.memory_manager.check_memory_usage()

            # Create some objects to trigger memory usage
            test_data = []
            for i in range(1000):
                test_data.append(f"test_string_{i}" * 100)

            # Test memory optimization
            optimization_stats = optimizer.memory_manager.optimize_memory()

            # Get final memory usage
            final_memory = optimizer.memory_manager.check_memory_usage()

            # Test memory trend analysis
            trend = optimizer.memory_manager.get_memory_trend()

            success = (
                optimization_stats.get('optimization_time', 0) > 0 and
                initial_memory.get('rss', 0) > 0 and
                final_memory.get('rss', 0) > 0 and
                isinstance(trend, dict)
            )

            await optimizer.shutdown()

            return {
                'success': success,
                'initial_memory_mb': initial_memory.get('rss', 0) / (1024 * 1024),
                'final_memory_mb': final_memory.get('rss', 0) / (1024 * 1024),
                'optimization_stats': optimization_stats,
                'memory_trend': trend
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_animation_optimization(self) -> Dict[str, Any]:
        """Test animation optimization system"""
        try:
            config = AnimationConfig(
                quality=AnimationQuality.MEDIUM,
                max_fps=30,
                adaptive_quality=True
            )

            optimizer = AnimationOptimizer(config)

            # Test animation creation
            fade_anim = optimizer.create_fade_animation("test_fade", "Test Content", 0.5)
            color_anim = optimizer.create_color_transition("test_color", "Test", "red", "blue", 0.3)
            spinner_anim = optimizer.create_loading_spinner("test_spinner", 1.0)

            # Start animations
            optimizer.start_animation(fade_anim)
            optimizer.start_animation(color_anim)
            optimizer.start_animation(spinner_anim)

            # Test animation updates
            frames_rendered = 0
            for i in range(10):
                current_frames = optimizer.update_animations()
                if current_frames:
                    frames_rendered += 1
                await asyncio.sleep(0.05)  # 50ms

            # Test performance stats
            perf_stats = optimizer.get_performance_stats()

            # Test quality adjustment
            original_quality = optimizer.current_quality
            optimizer.set_quality(AnimationQuality.LOW)
            new_quality = optimizer.current_quality

            success = (
                len(fade_anim.frames) > 0 and
                len(color_anim.frames) > 0 and
                len(spinner_anim.frames) > 0 and
                frames_rendered > 0 and
                perf_stats.get('frames_rendered', 0) > 0 and
                new_quality == AnimationQuality.LOW
            )

            optimizer.clear_all_animations()

            return {
                'success': success,
                'frames_rendered': frames_rendered,
                'performance_stats': perf_stats,
                'quality_change': f"{original_quality.value} -> {new_quality.value}",
                'fade_frames': len(fade_anim.frames),
                'color_frames': len(color_anim.frames),
                'spinner_frames': len(spinner_anim.frames)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_ai_caching(self) -> Dict[str, Any]:
        """Test AI response caching system"""
        try:
            cache = ResponseCache(max_size=100, default_ttl=60)

            # Test cache operations
            test_prompt = "Test prompt for caching"
            test_model = "test_model"
            test_response = {"response": "Test AI response", "confidence": 0.9}

            # Test cache miss
            cached_response = cache.get(test_prompt, test_model)
            cache_miss = cached_response is None

            # Test cache set
            cache.set(test_prompt, test_model, test_response)

            # Test cache hit
            cached_response = cache.get(test_prompt, test_model)
            cache_hit = cached_response is not None

            # Test cache stats
            stats = cache.get_stats()

            # Test cache with different parameters
            cache.set("prompt2", "model2", {"response": "Response 2"})
            cache.set("prompt3", "model3", {"response": "Response 3"})

            # Test cache eviction (fill beyond max_size)
            for i in range(150):
                cache.set(f"prompt_{i}", "model", f"response_{i}")

            final_stats = cache.get_stats()

            success = (
                cache_miss and
                cache_hit and
                cached_response == test_response and
                stats.get('total_entries', 0) > 0 and
                final_stats.get('total_entries', 0) <= cache.max_size
            )

            return {
                'success': success,
                'cache_miss': cache_miss,
                'cache_hit': cache_hit,
                'initial_stats': stats,
                'final_stats': final_stats,
                'response_match': cached_response == test_response
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_large_directory_handling(self) -> Dict[str, Any]:
        """Test large directory handling optimizations"""
        try:
            # Create temporary directory with many files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Create test files
                file_count = 500  # Reduced for faster testing
                for i in range(file_count):
                    (temp_path / f"test_file_{i:04d}.txt").write_text(f"Content {i}")

                # Create subdirectories
                for i in range(50):
                    subdir = temp_path / f"subdir_{i:02d}"
                    subdir.mkdir()
                    (subdir / "file.txt").write_text(f"Subdir content {i}")

                # Test file manager with large directory
                file_manager = AdvancedFileManager(self.config)
                await file_manager.initialize()

                # Test directory listing performance
                start_time = time.time()
                files = await file_manager.list_directory(
                    temp_path,
                    show_hidden=False,
                    lazy_load=True,
                    chunk_size=100
                )
                listing_time = time.time() - start_time

                # Test optimization for large directory
                optimization_result = await file_manager.optimize_for_large_directory(file_count)

                # Test cache performance
                cache_stats = file_manager.get_cache_stats()

                # Test performance stats
                perf_stats = file_manager.get_performance_stats()

                success = (
                    len(files) > 0 and
                    listing_time < 5.0 and  # Should complete within 5 seconds
                    optimization_result.get('file_count') == file_count and
                    cache_stats.get('file_cache_size', 0) >= 0 and
                    'list_directory' in perf_stats
                )

                return {
                    'success': success,
                    'file_count': file_count,
                    'files_listed': len(files),
                    'listing_time': listing_time,
                    'optimization_result': optimization_result,
                    'cache_stats': cache_stats,
                    'performance_stats': perf_stats
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_performance_monitoring(self) -> Dict[str, Any]:
        """Test performance monitoring system"""
        try:
            config = PerformanceConfig(
                background_processing=True,
                memory_check_interval=1
            )

            optimizer = PerformanceOptimizer(config)
            await optimizer.initialize()

            # Let background monitoring run for a short time
            await asyncio.sleep(2)

            # Record some operation times
            optimizer.record_operation_time("test_operation", 0.1)
            optimizer.record_operation_time("test_operation", 0.2)
            optimizer.record_operation_time("test_operation", 0.15)

            # Test performance stats
            stats = optimizer.get_performance_stats()

            # Test cache optimization
            test_cache = {"key1": ("value1", time.time()), "key2": ("value2", time.time())}
            cache_result = optimizer.optimize_cache("test_cache", test_cache)

            # Test background task submission
            def dummy_task():
                time.sleep(0.1)
                return "completed"

            future = optimizer.submit_background_task("test_pool", dummy_task)
            task_result = future.result(timeout=1.0)

            await optimizer.shutdown()

            success = (
                stats.get('memory') is not None and
                stats.get('operation_times') is not None and
                'test_operation' in stats.get('operation_times', {}) and
                cache_result.get('cache_name') == 'test_cache' and
                task_result == "completed"
            )

            return {
                'success': success,
                'performance_stats': stats,
                'cache_optimization': cache_result,
                'background_task_result': task_result,
                'operation_count': len(stats.get('operation_times', {}).get('test_operation', {}).get('count', 0))
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def print_test_summary(self):
        """Print a summary of all test results"""
        print("\n" + "="*60)
        print("PERFORMANCE OPTIMIZATION TEST SUMMARY")
        print("="*60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'passed')
        failed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'failed')
        error_tests = sum(1 for result in self.test_results.values() if result['status'] == 'error')

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Errors: {error_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()

        for test_name, result in self.test_results.items():
            status_symbol = "✅" if result['status'] == 'passed' else "❌" if result['status'] == 'failed' else "⚠️"
            print(f"{status_symbol} {test_name}: {result['status'].upper()} ({result['duration']:.3f}s)")

            if result['status'] == 'error':
                print(f"   Error: {result.get('error', 'Unknown error')}")
            elif result['status'] == 'failed':
                print(f"   Details: {result.get('details', {}).get('error', 'Test failed')}")

        print("\n" + "="*60)


async def main():
    """Run the performance optimization test suite"""
    test_suite = PerformanceTestSuite()

    print("🚀 LaxyFile Performance Optimization Test Suite")
    print("Testing all performance enhancements from task 13.2...")
    print()

    # Run all tests
    results = await test_suite.run_all_tests()

    # Print summary
    test_suite.print_test_summary()

    # Return success status
    all_passed = all(result['status'] == 'passed' for result in results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)