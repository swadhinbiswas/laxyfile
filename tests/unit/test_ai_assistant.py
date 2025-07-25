"""
Unit tests for AdvancedAIAssistant

Tests the enhanced AI assistant with multi-model support, comprehensive analysis,
caching, and error handling capabilities.
"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from laxyfile.ai.advanced_assistant import (
    AdvancedAIAssistant, AIModelManager, ResponseCache, AIProvider, AnalysisType,
    AIModel, AnalysisResult, CacheEntry
)
from laxyfile.core.exceptions import AIError, ConfigurationError


@pytest.mark.unit
class TestAIModel:
    """Test the AIModel dataclass"""

    def test_ai_model_creation(self):
        """Test AI model creation with default values"""
        model = AIModel(
            provider=AIProvider.OPENROUTER,
            model_name="test/model"
        )

        assert model.provider == AIProvider.OPENROUTER
        assert model.model_name == "test/model"
        assert model.api_key is None
        assert model.max_tokens == 4096
        assert model.temperature == 0.7
        assert model.is_available is True
        assert model.capabilities == []

    def test_ai_model_with_custom_values(self):
        """Test AI model creation with custom values"""
        model = AIModel(
            provider=AIProvider.OLLAMA,
            model_name="llama2",
            base_url="http://localhost:11434",
            max_tokens=2048,
            temperature=0.5,
            capabilities=["text_analysis", "code_analysis"]
        )

        assert model.provider == AIProvider.OLLAMA
        assert model.base_url == "http://localhost:11434"
        assert model.max_tokens == 2048
        assert model.temperature == 0.5
        assert model.capabilities == ["text_analysis", "code_analysis"]


@pytest.mark.unit
class TestCacheEntry:
    """Test the CacheEntry dataclass"""

    def test_cache_entry_creation(self):
        """Test cache entry creation"""
        timestamp = datetime.now()
        entry = CacheEntry(
            key="test_key",
            response="test_response",
            timestamp=timestamp,
            model="test_model"
        )

        assert entry.key == "test_key"
        assert entry.response == "test_response"
        assert entry.timestamp == timestamp
        assert entry.model == "test_model"
        assert entry.expires_at is None
        assert entry.access_count == 0

    def test_cache_entry_expiration(self):
        """Test cache entry expiration logic"""
        # Non-expiring entry
        entry1 = CacheEntry("key1", "response1", datetime.now(), "model1")
        assert not entry1.is_expired()

        # Expired entry
        past_time = datetime.now() - timedelta(hours=1)
        entry2 = CacheEntry("key2", "response2", datetime.now(), "model2", expires_at=past_time)
        assert entry2.is_expired()

        # Non-expired entry
        future_time = datetime.now() + timedelta(hours=1)
        entry3 = CacheEntry("key3", "response3", datetime.now(), "model3", expires_at=future_time)
        assert not entry3.is_expired()


@pytest.mark.unit
class TestResponseCache:
    """Test the ResponseCache class"""

    def test_cache_initialization(self):
        """Test cache initialization"""
        cache = ResponseCache()
        assert cache.max_size == 1000
        assert cache.default_ttl == 3600
        assert len(cache.cache) == 0

        cache = ResponseCache(max_size=100, default_ttl=1800)
        assert cache.max_size == 100
        assert cache.default_ttl == 1800

    def test_cache_key_generation(self):
        """Test cache key generation"""
        cache = ResponseCache()

        key1 = cache._generate_key("prompt1", "model1")
        key2 = cache._generate_key("prompt1", "model1")
        key3 = cache._generate_key("prompt2", "model1")
        key4 = cache._generate_key("prompt1", "model2")

        # Same inputs should generate same key
        assert key1 == key2

        # Different inputs should generate different keys
        assert key1 != key3
        assert key1 != key4

    def test_cache_set_and_get(self):
        """Test cache set and get operations"""
        cache = ResponseCache()

        # Set and get without TTL
        cache.set("prompt1", "model1", "response1")
        result = cache.get("prompt1", "model1")
        assert result == "response1"

        # Get non-existent key
        result = cache.get("nonexistent", "model1")
        assert result is None

    def test_cache_with_ttl(self):
        """Test cache with TTL"""
        cache = ResponseCache(default_ttl=1)  # 1 second TTL

        cache.set("prompt1", "model1", "response1")

        # Should be available immediately
        result = cache.get("prompt1", "model1")
        assert result == "response1"

        # Mock time passage
        with patch('laxyfile.ai.advanced_assistant.datetime') as mock_datetime:
            future_time = datetime.now() + timedelta(seconds=2)
            mock_datetime.now.return_value = future_time

            # Should be expired
            result = cache.get("prompt1", "model1")
            assert result is None

    def test_cache_eviction(self):
        """Test cache eviction when full"""
        cache = ResponseCache(max_size=2)

        # Fill cache
        cache.set("prompt1", "model1", "response1")
        cache.set("prompt2", "model1", "response2")

        # Access first item to make it most recently used
        cache.get("prompt1", "model1")

        # Add third item, should evict second item
        cache.set("prompt3", "model1", "response3")

        assert cache.get("prompt1", "model1") == "response1"  # Still there
        assert cache.get("prompt2", "model1") is None  # Evicted
        assert cache.get("prompt3", "model1") == "response3"  # New item

    def test_cache_clear_expired(self):
        """Test clearing expired entries"""
        cache = ResponseCache()

        # Add entries with different expiration times
        past_time = datetime.now() - timedelta(hours=1)
        future_time = datetime.now() + timedelta(hours=1)

        cache.set("prompt1", "model1", "response1", ttl=None)  # Never expires
        cache.set("prompt2", "model1", "response2", ttl=1)    # Short TTL

        # Manually set expiration times for testing
        key1 = cache._generate_key("prompt1", "model1")
        key2 = cache._generate_key("prompt2", "model1")
        cache.cache[key2].expires_at = past_time  # Make it expired

        cache.clear_expired()

        assert cache.get("prompt1", "model1") == "response1"  # Should remain
        assert cache.get("prompt2", "model1") is None  # Should be removed

    def test_cache_stats(self):
        """Test cache statistics"""
        cache = ResponseCache()

        # Add some entries
        cache.set("prompt1", "model1", "response1")
        cache.set("prompt2", "model1", "response2")

        stats = cache.get_stats()

        assert stats['total_entries'] == 2
        assert stats['max_size'] == 1000
        assert 'hit_rate' in stats


@pytest.mark.unit
class TestAIModelManager:
    """Test the AIModelManager class"""

    def test_model_manager_initialization(self):
        """Test model manager initialization"""
        config = {
            'ai_models': {
                'test_model': {
                    'provider': 'openrouter',
                    'model_name': 'test/model',
                    'api_key': 'test_key',
                    'capabilities': ['text_analysis']
                }
            }
        }

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            manager = AIModelManager(config)

            assert 'test_model' in manager.models
            assert manager.models['test_model'].provider == AIProvider.OPENROUTER
            assert 'test_model' in manager.fallback_order

    def test_model_manager_no_models(self):
        """Test model manager with no available models"""
        config = {'ai_models': {}}
        with pytest.raises(ConfigurationError):
            AIModelManager(config)

    def test_get_best_model(self):
        """Test getting the best available model"""
        config = {
            'ai_models': {
                'model1': {
                    'provider': 'openrouter',
                    'model_name': 'test/model1',
                    'capabilities': ['text_analysis']
                },
                'model2': {
                    'provider': 'ollama',
                    'model_name': 'llama2',
                    'capabilities': ['code_analysis']
                }
            }
        }

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            manager = AIModelManager(config)

            # Get best model without capabilities
            best = manager.get_best_model()
            assert best is not None

            # Get best model with specific capabilities
            text_model = manager.get_best_model(capabilities=['text_analysis'])
            assert text_model.capabilities == ['text_analysis']

            code_model = manager.get_best_model(capabilities=['code_analysis'])
            assert code_model.capabilities == ['code_analysis']

    def test_get_model_by_id(self):
        """Test getting model by ID"""
        config = {
            'ai_models': {
                'test_model': {
                    'provider': 'openrouter',
                    'model_name': 'test/model',
                    'api_key': 'test_key'
                }
            }
        }

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            manager = AIModelManager(config)

            model = manager.get_model('test_model')
            assert model is not None
            assert model.model_name == 'test/model'

            nonexistent = manager.get_model('nonexistent')
            assert nonexistent is None

    def test_update_model_status(self):
        """Test updating model availability status"""
        config = {
            'ai_models': {
                'test_model': {
                    'provider': 'openrouter',
                    'model_name': 'test/model'
                }
            }
        }

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            manager = AIModelManager(config)

            # Initially available
            assert manager.models['test_model'].is_available
            assert 'test_model' in manager.fallback_order

            # Mark as unavailable
            manager.update_model_status('test_model', False)
            assert not manager.models['test_model'].is_available
            assert 'test_model' not in manager.fallback_order

            # Mark as available again
            manager.update_model_status('test_model', True)
            assert manager.models['test_model'].is_available
            assert 'test_model' in manager.fallback_order


@pytest.mark.unit
class TestAdvancedAIAssistant:
    """Test the AdvancedAIAssistant class"""

    def test_ai_assistant_initialization(self, mock_config):
        """Test AI assistant initialization"""
        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(mock_config)

            assert assistant.model_manager is not None
            assert assistant.cache is not None
            assert assistant.analysis_history == []
            assert assistant.max_history_size == 100

    @pytest.mark.asyncio
    async def test_analyze_file_comprehensive(self, temp_dir, sample_files):
        """Test comprehensive file analysis"""
        config = {
            'ai_models': {
                'test_model': {
                    'provider': 'openrouter',
                    'model_name': 'test/model',
                    'api_key': 'test_key',
                    'capabilities': ['text_analysis', 'security_analysis']
                }
            },
            'cache_size': 100,
            'cache_ttl': 3600,
            'max_analysis_history': 100
        }

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            # Mock the model call
            mock_response = json.dumps({
                "summary": "Test file analysis",
                "confidence": 0.9,
                "insights": ["Test insight"],
                "suggestions": ["Test suggestion"]
            })

            with patch.object(assistant, '_call_model', return_value=mock_response):
                results = await assistant.analyze_file_comprehensive(
                    sample_files['text_file'],
                    [AnalysisType.CONTENT, AnalysisType.SECURITY]
                )

                assert len(results) == 2  # Two analysis types
                assert all(isinstance(r, AnalysisResult) for r in results)
                assert len(assistant.analysis_history) == 2

    def test_get_required_capabilities(self):
        """Test getting required capabilities for analysis types"""
        config = {'ai_models': {'test': {'provider': 'openrouter', 'model_name': 'test'}}}

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            content_caps = assistant._get_required_capabilities(AnalysisType.CONTENT)
            assert 'text_analysis' in content_caps
            assert 'code_analysis' in content_caps

            security_caps = assistant._get_required_capabilities(AnalysisType.SECURITY)
            assert 'security_analysis' in security_caps
            assert 'vulnerability_detection' in security_caps

    @pytest.mark.asyncio
    async def test_generate_analysis_prompt(self, temp_dir, sample_files):
        """Test analysis prompt generation"""
        config = {'ai_models': {'test': {'provider': 'openrouter', 'model_name': 'test'}}}

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            # Test content analysis prompt
            prompt = await assistant._generate_analysis_prompt(
                sample_files['text_file'], AnalysisType.CONTENT
            )

            assert "content insights" in prompt.lower()
            assert "readme.txt" in prompt
            assert "sample text file" in prompt

    def test_generate_content_analysis_prompt(self):
        """Test content analysis prompt generation"""
        config = {'ai_models': {'test': {'provider': 'openrouter', 'model_name': 'test'}}}

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            file_info = {
                'name': 'test.py',
                'size': 1024,
                'mime_type': 'text/x-python',
                'extension': '.py'
            }
            content = "print('Hello, World!')"

            prompt = assistant._generate_content_analysis_prompt(file_info, content)

            assert "test.py" in prompt
            assert "print('Hello, World!')" in prompt
            assert "JSON format" in prompt
            assert "summary" in prompt

    def test_generate_security_analysis_prompt(self):
        """Test security analysis prompt generation"""
        config = {'ai_models': {'test': {'provider': 'openrouter', 'model_name': 'test'}}}

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            file_info = {
                'name': 'script.sh',
                'size': 512,
                'mime_type': 'application/x-shellscript',
                'extension': '.sh'
            }
            content = "#!/bin/bash\nrm -rf /"

            prompt = assistant._generate_security_analysis_prompt(file_info, content)

            assert "security analysis" in prompt.lower()
            assert "script.sh" in prompt
            assert "rm -rf /" in prompt
            assert "risk_level" in prompt

    @pytest.mark.asyncio
    async def test_call_ollama_model(self):
        """Test calling Ollama model"""
        config = {
            'ai_models': {
                'ollama_model': {
                    'provider': 'ollama',
                    'model_name': 'llama2',
                    'base_url': 'http://localhost:11434'
                }
            }
        }

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)
            model = assistant.model_manager.get_model('ollama_model')

            # Mock aiohttp session
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={'response': 'Test response'})

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

                result = await assistant._call_ollama(model, "Test prompt")
                assert result == "Test response"

    @pytest.mark.asyncio
    async def test_call_api_model_openrouter(self):
        """Test calling OpenRouter API model"""
        config = {
            'ai_models': {
                'openrouter_model': {
                    'provider': 'openrouter',
                    'model_name': 'test/model',
                    'api_key': 'test_key'
                }
            }
        }

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)
            model = assistant.model_manager.get_model('openrouter_model')

            # Mock aiohttp session
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                'choices': [{'message': {'content': 'Test response'}}]
            })

            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

                result = await assistant._call_api_model(model, "Test prompt")
                assert result == "Test response"

    def test_parse_analysis_response(self):
        """Test parsing analysis response"""
        config = {'ai_models': {'test': {'provider': 'openrouter', 'model_name': 'test'}}}

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            response = json.dumps({
                "summary": "Test analysis",
                "confidence": 0.85,
                "insights": ["Insight 1", "Insight 2"],
                "suggestions": ["Suggestion 1"]
            })

            result = assistant._parse_analysis_response(
                Path("test.txt"), AnalysisType.CONTENT, response, "test_model", 1.5
            )

            assert isinstance(result, AnalysisResult)
            assert result.file_path == Path("test.txt")
            assert result.analysis_type == AnalysisType.CONTENT
            assert result.confidence == 0.85
            assert result.model_used == "test_model"
            assert result.processing_time == 1.5

    def test_parse_invalid_json_response(self):
        """Test parsing invalid JSON response"""
        config = {'ai_models': {'test': {'provider': 'openrouter', 'model_name': 'test'}}}

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            # Invalid JSON response
            response = "This is not valid JSON"

            result = assistant._parse_analysis_response(
                Path("test.txt"), AnalysisType.CONTENT, response, "test_model", 1.0
            )

            assert isinstance(result, AnalysisResult)
            assert result.confidence == 0.0  # Low confidence for parsing errors
            assert len(result.errors) > 0

    def test_add_to_history(self):
        """Test adding analysis results to history"""
        config = {
            'ai_models': {'test': {'provider': 'openrouter', 'model_name': 'test'}},
            'max_analysis_history': 2
        }

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            # Create test results
            result1 = AnalysisResult(
                file_path=Path("test1.txt"),
                analysis_type=AnalysisType.CONTENT,
                results={},
                confidence=0.8,
                timestamp=datetime.now(),
                model_used="test_model",
                processing_time=1.0
            )

            result2 = AnalysisResult(
                file_path=Path("test2.txt"),
                analysis_type=AnalysisType.SECURITY,
                results={},
                confidence=0.9,
                timestamp=datetime.now(),
                model_used="test_model",
                processing_time=1.5
            )

            result3 = AnalysisResult(
                file_path=Path("test3.txt"),
                analysis_type=AnalysisType.CONTENT,
                results={},
                confidence=0.7,
                timestamp=datetime.now(),
                model_used="test_model",
                processing_time=2.0
            )

            # Add results
            assistant._add_to_history(result1)
            assistant._add_to_history(result2)
            assert len(assistant.analysis_history) == 2

            # Adding third should remove first (FIFO with max size 2)
            assistant._add_to_history(result3)
            assert len(assistant.analysis_history) == 2
            assert assistant.analysis_history[0] == result2  # First was removed
            assert assistant.analysis_history[1] == result3

    def test_update_performance_stats(self):
        """Test performance statistics updates"""
        config = {'ai_models': {'test': {'provider': 'openrouter', 'model_name': 'test'}}}

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            model = AIModel(
                provider=AIProvider.OPENROUTER,
                model_name="test/model",
                cost_per_token=0.001
            )

            # Update stats
            assistant._update_performance_stats(1.5, model, tokens_used=100)

            assert assistant.performance_stats['total_requests'] == 1
            assert assistant.performance_stats['successful_requests'] == 1
            assert assistant.performance_stats['total_tokens_used'] == 100
            assert assistant.performance_stats['total_cost'] == 0.1  # 100 * 0.001
            assert assistant.performance_stats['average_response_time'] == 1.5

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in AI operations"""
        config = {
            'ai_models': {
                'failing_model': {
                    'provider': 'openrouter',
                    'model_name': 'test/model',
                    'api_key': 'invalid_key'
                }
            }
        }

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            # Mock a failing model call
            with patch.object(assistant, '_call_model', side_effect=AIError("API call failed")):
                result = await assistant._perform_single_analysis(
                    Path("test.txt"), AnalysisType.CONTENT
                )

                assert result is None  # Should return None on error
                assert assistant.performance_stats['failed_requests'] == 1

    @pytest.mark.asyncio
    async def test_caching_behavior(self, temp_dir, sample_files):
        """Test caching behavior in AI assistant"""
        config = {
            'ai_models': {
                'test_model': {
                    'provider': 'openrouter',
                    'model_name': 'test/model',
                    'api_key': 'test_key',
                    'capabilities': ['text_analysis']
                }
            },
            'cache_size': 100,
            'cache_ttl': 3600
        }

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            mock_response = json.dumps({
                "summary": "Cached response",
                "confidence": 0.9
            })

            with patch.object(assistant, '_call_model', return_value=mock_response) as mock_call:
                # First call should hit the model
                result1 = await assistant._perform_single_analysis(
                    sample_files['text_file'], AnalysisType.CONTENT
                )
                assert mock_call.call_count == 1

                # Second call should use cache
                result2 = await assistant._perform_single_analysis(
                    sample_files['text_file'], AnalysisType.CONTENT
                )
                assert mock_call.call_count == 1  # No additional call
                assert assistant.performance_stats['cache_hits'] == 1

    def test_get_analysis_history(self):
        """Test getting analysis history"""
        config = {'ai_models': {'test': {'provider': 'openrouter', 'model_name': 'test'}}}

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            # Add some history
            result = AnalysisResult(
                file_path=Path("test.txt"),
                analysis_type=AnalysisType.CONTENT,
                results={"summary": "test"},
                confidence=0.8,
                timestamp=datetime.now(),
                model_used="test_model",
                processing_time=1.0
            )

            assistant._add_to_history(result)

            history = assistant.get_analysis_history()
            assert len(history) == 1
            assert history[0] == result

    def test_clear_analysis_history(self):
        """Test clearing analysis history"""
        config = {'ai_models': {'test': {'provider': 'openrouter', 'model_name': 'test'}}}

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            # Add some history
            result = AnalysisResult(
                file_path=Path("test.txt"),
                analysis_type=AnalysisType.CONTENT,
                results={},
                confidence=0.8,
                timestamp=datetime.now(),
                model_used="test_model",
                processing_time=1.0
            )

            assistant._add_to_history(result)
            assert len(assistant.analysis_history) == 1

            assistant.clear_analysis_history()
            assert len(assistant.analysis_history) == 0

    def test_get_performance_stats(self):
        """Test getting performance statistics"""
        config = {'ai_models': {'test': {'provider': 'openrouter', 'model_name': 'test'}}}

        with patch.object(AIModelManager, '_test_model_availability', return_value=True):
            assistant = AdvancedAIAssistant(config)

            # Update some stats
            assistant.performance_stats['total_requests'] = 10
            assistant.performance_stats['successful_requests'] = 8
            assistant.performance_stats['failed_requests'] = 2
            assistant.performance_stats['cache_hits'] = 3

            stats = assistant.get_performance_stats()

            assert stats['total_requests'] == 10
            assert stats['successful_requests'] == 8
            assert stats['failed_requests'] == 2
            assert stats['cache_hits'] == 3
            assert stats['success_rate'] == 0.8  # 8/10
            assert stats['cache_hit_rate'] == 0.3  # 3/10