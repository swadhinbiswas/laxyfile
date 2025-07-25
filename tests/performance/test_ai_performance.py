"""
Performance benchmarks for AI components

Comprehensive benchmarks testing AI assistant performance, response times,
caching efficiency, and resource usage under various workloads.
"""

import pytest
import asyncio
import time
import json
import psutil
import gc
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from laxyfile.ai.advanced_assistant import AdvancedAIAssistant, AnalysisType, AnalysisResult
from laxyfile.ai.file_analyzer import FileAnalyzer
from laxyfile.ai.organization_engine import OrganizationEngine
from laxyfile.ai.security_analyzer import SecurityAnalyzer


@pytest.mark.performance
class TestAIAssistantBenchmarks:
    """Benchmark tests for AI assistant performance"""

    @pytest.fixture
    def ai_config(self):
        """Create optimized AI configuration for benchmarks"""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'ai.provider': 'openrouter',
            'ai.model': 'anthropic/claude-3-haiku',
            'ai.api_key': 'test-key',
            'ai.max_tokens': 4000,
            'ai.temperature': 0.1,
            'ai.cache_size': 1000,
            'ai.cache_ttl': 3600,
            'ai.timeout': 30,
            'ai.max_concurrent_requests': 5,
            'ai.enable_local_models': True,
            'ai.local_model_path': '/tmp/test-model',
            'performance.ai_cache_size': 2000,
            'performance.ai_response_cache_ttl': 7200
        }.get(key, default))
        return config

    @pytest.fixture
    def benchmark_assistant(self, ai_config):
        """Create AI assistant for benchmarking"""
        return AdvancedAIAssistant(ai_config)

    @pytest.fixture
    def test_files(self, temp_dir):
        """Create test files for AI analysis"""
        files = []

        # Create various file types for analysis
        file_contents = {
            'python_code.py': '''
import os
import sys
from pathlib import Path

def analyze_directory(path):
    """Analyze directory structure and contents"""
    files = []
    for item in Path(path).rglob("*"):
        if item.is_file():
            files.append({
                'name': item.name,
                'size': item.stat().st_size,
                'modified': item.stat().st_mtime
            })
    return files

if __name__ == "__main__":
    result = analyze_directory(sys.argv[1])
    print(f"Found {len(result)} files")
''',
            'config.json': '''
{
    "application": {
        "name": "LaxyFile",
        "version": "2.0.0",
        "debug": false
    },
    "ui": {
        "theme": "catppuccin",
        "animations": true,
        "font_size": 12
    },
    "performance": {
        "cache_size": 1000,
        "max_workers": 8,
        "lazy_loading": true
    }
}
''',
            'readme.md': '''
# LaxyFile Performance Testing

This document describes the performance testing framework for LaxyFile.

## Overview

LaxyFile includes comprehensive performance tests covering:

- File manager operations
- UI rendering performance
- AI assistant response times
- Memory usage optimization
- Concurrent operation handling

## Running Tests

```bash
pytest tests/performance/ -v --benchmark-only
```

## Benchmarking Guidelines

1. Run tests on consistent hardware
2. Close unnecessary applications
3. Use dedicated test data
4. Monitor system resources
''',
            'large_text.txt': 'This is a large text file for testing. ' * 1000,
            'data.csv': '''name,age,city,salary
John Doe,30,New York,75000
Jane Smith,25,Los Angeles,65000
Bob Johnson,35,Chicago,80000
Alice Brown,28,Houston,70000
''' * 100
        }

        for filename, content in file_contents.items():
            file_path = temp_dir / filename
            file_path.write_text(content)
            files.append(file_path)

        return files
@pytest.mark.asyncio
    async def test_file_analysis_performance(self, benchmark_assistant, test_files, benchmark):
        """Benchmark file analysis performance"""

        async def analyze_files():
            results = []
            for file_path in test_files:
                result = await benchmark_assistant.analyze_file(
                    file_path,
                    analysis_type=AnalysisType.COMPREHENSIVE
                )
                results.append(result)
            return results

        def analyze_files_sync():
            return asyncio.run(analyze_files())

        # Mock AI responses to focus on processing performance
        with patch.object(benchmark_assistant, '_make_ai_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                'analysis': 'Test analysis result',
                'suggestions': ['Test suggestion 1', 'Test suggestion 2'],
                'confidence': 0.85
            }

            # Benchmark file analysis
            results = benchmark(analyze_files_sync)

            # Verify results
            assert len(results) == len(test_files)
            for result in results:
                assert result.analysis is not None
                assert len(result.suggestions) > 0

        # Performance assertions
        stats = benchmark.stats
        assert stats.mean < 2.0  # Should complete within 2 seconds
        assert mock_request.call_count == len(test_files)

    @pytest.mark.asyncio
    async def test_batch_analysis_performance(self, benchmark_assistant, test_files, benchmark):
        """Benchmark batch file analysis performance"""

        async def batch_analyze():
            return await benchmark_assistant.analyze_files_batch(
                test_files,
                analysis_type=AnalysisType.QUICK
            )

        def batch_analyze_sync():
            return asyncio.run(batch_analyze())

        # Mock AI responses
        with patch.object(benchmark_assistant, '_make_ai_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                'batch_analysis': [
                    {'file': str(f), 'analysis': f'Analysis for {f.name}'}
                    for f in test_files
                ]
            }

            # Benchmark batch analysis
            results = benchmark(batch_analyze_sync)

            # Verify results
            assert len(results) == len(test_files)

        # Performance assertions (batch should be more efficient)
        stats = benchmark.stats
        assert stats.mean < 1.5  # Batch processing should be faster

    @pytest.mark.asyncio
    async def test_organization_suggestions_performance(self, benchmark_assistant, test_files, benchmark):
        """Benchmark organization suggestions performance"""

        async def get_organization_suggestions():
            return await benchmark_assistant.suggest_organization(
                test_files[0].parent,
                include_ai_analysis=True
            )

        def get_suggestions_sync():
            return asyncio.run(get_organization_suggestions())

        # Mock AI responses
        with patch.object(benchmark_assistant, '_make_ai_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                'suggestions': [
                    {
                        'type': 'create_folder',
                        'name': 'code',
                        'files': ['python_code.py']
                    },
                    {
                        'type': 'create_folder',
                        'name': 'docs',
                        'files': ['readme.md']
                    }
                ]
            }

            # Benchmark organization suggestions
            suggestions = benchmark(get_suggestions_sync)

            # Verify results
            assert len(suggestions) > 0

        # Performance assertions
        stats = benchmark.stats
        assert stats.mean < 3.0  # Organization analysis can take longer

    @pytest.mark.asyncio
    async def test_cache_performance(self, benchmark_assistant, test_files, benchmark):
        """Benchmark AI response caching performance"""

        async def cache_test():
            # First pass - populate cache
            first_pass_start = time.time()
            for file_path in test_files[:3]:  # Use subset for cache testing
                await benchmark_assistant.analyze_file(file_path, AnalysisType.QUICK)
            first_pass_time = time.time() - first_pass_start

            # Second pass - should use cache
            second_pass_start = time.time()
            for file_path in test_files[:3]:
                await benchmark_assistant.analyze_file(file_path, AnalysisType.QUICK)
            second_pass_time = time.time() - second_pass_start

            return first_pass_time, second_pass_time

        def cache_test_sync():
            return asyncio.run(cache_test())

        # Mock AI responses
        with patch.object(benchmark_assistant, '_make_ai_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                'analysis': 'Cached analysis result',
                'suggestions': ['Cached suggestion']
            }

            # Benchmark cache performance
            first_time, second_time = benchmark(cache_test_sync)

            # Cache should improve performance significantly
            assert second_time < first_time * 0.5  # At least 50% improvement

    def test_memory_usage_benchmark(self, benchmark_assistant, test_files, benchmark):
        """Benchmark AI assistant memory usage"""

        def memory_benchmark():
            process = psutil.Process()
            initial_memory = process.memory_info().rss

            # Perform memory-intensive AI operations
            async def memory_operations():
                # Analyze many files
                for file_path in test_files * 10:  # Repeat files to increase load
                    await benchmark_assistant.analyze_file(file_path, AnalysisType.QUICK)

                # Get organization suggestions
                await benchmark_assistant.suggest_organization(test_files[0].parent)

            # Mock AI responses to focus on memory usage
            with patch.object(benchmark_assistant, '_make_ai_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {'analysis': 'Memory test result'}
                asyncio.run(memory_operations())

            peak_memory = process.memory_info().rss
            memory_increase = peak_memory - initial_memory

            # Force garbage collection
            gc.collect()
            final_memory = process.memory_info().rss

            return {
                'initial_mb': initial_memory / 1024 / 1024,
                'peak_mb': peak_memory / 1024 / 1024,
                'final_mb': final_memory / 1024 / 1024,
                'increase_mb': memory_increase / 1024 / 1024
            }

        # Benchmark memory usage
        memory_stats = benchmark(memory_benchmark)

        # Memory usage assertions
        assert memory_stats['increase_mb'] < 100  # Should not use more than 100MB extra
        assert memory_stats['final_mb'] < memory_stats['peak_mb'] + 10  # Should release most memory


@pytest.mark.performance
class TestFileAnalyzerBenchmarks:
    """Benchmark tests for file analyzer performance"""

    @pytest.fixture
    def file_analyzer(self, ai_config):
        """Create file analyzer for benchmarking"""
        return FileAnalyzer(ai_config)

    @pytest.mark.asyncio
    async def test_code_analysis_performance(self, file_analyzer, test_files, benchmark):
        """Benchmark code analysis performance"""

        # Find Python file for code analysis
        python_file = next((f for f in test_files if f.suffix == '.py'), test_files[0])

        async def analyze_code():
            return await file_analyzer.analyze_code_structure(python_file)

        def analyze_code_sync():
            return asyncio.run(analyze_code())

        # Benchmark code analysis
        result = benchmark(analyze_code_sync)

        # Verify results
        assert result is not None

        # Performance assertions
        stats = benchmark.stats
        assert stats.mean < 1.0  # Code analysis should be fast


@pytest.mark.performance
class TestAIStressTests:
    """Stress tests for AI components under extreme conditions"""

    @pytest.fixture
    def stress_assistant(self, ai_config):
        """Create AI assistant for stress testing"""
        # Increase limits for stress testing
        ai_config.get = Mock(side_effect=lambda key, default=None: {
            'ai.max_concurrent_requests': 20,
            'ai.cache_size': 5000,
            'ai.timeout': 60,
            'performance.ai_cache_size': 10000
        }.get(key, default) or ai_config.get(key, default))
        return AdvancedAIAssistant(ai_config)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_memory_stress_ai(self, stress_assistant, test_files):
        """Stress test AI memory usage under extreme load"""

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Mock AI responses
        with patch.object(stress_assistant, '_make_ai_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                'analysis': 'Memory stress test analysis' * 100,  # Large response
                'suggestions': [f'Suggestion {i}' for i in range(50)]
            }

            # Perform memory-intensive operations
            for _ in range(10):  # Multiple batches
                # Analyze files
                tasks = [stress_assistant.analyze_file(f, AnalysisType.COMPREHENSIVE) for f in test_files]
                await asyncio.gather(*tasks)

                # Get organization suggestions
                await stress_assistant.suggest_organization(test_files[0].parent)

        peak_memory = process.memory_info().rss
        memory_increase = (peak_memory - initial_memory) / 1024 / 1024  # MB

        # Memory usage should be reasonable even under stress
        assert memory_increase < 500  # Should not use more than 500MB extra

        # Force cleanup and verify memory is released
        gc.collect()

        final_memory = process.memory_info().rss
        final_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        # Should release significant memory after cleanup
        assert final_increase < memory_increase * 0.7  # At least 30% reduction