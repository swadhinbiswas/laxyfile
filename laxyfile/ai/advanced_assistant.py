"""
Advanced AI Assistant

This module provides enhanced AI capabilities with multi-model support,
comprehensive analysis, and intelligent automation for LaxyFile.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import mimetypes
from datetime import datetime, timedelta

from ..core.types import OperationResult
from ..core.exceptions import AIError, ConfigurationError
from ..utils.logger import Logger
from .assistant import AIAssistant


class AIProvider(Enum):
    """Supported AI providers"""
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    GPT4ALL = "gpt4all"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class AnalysisType(Enum):
    """Types of file analysis"""
    CONTENT = "content"
    METADATA = "metadata"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ORGANIZATION = "organization"
    DUPLICATE = "duplicate"
    RELATIONSHIP = "relationship"


@dataclass
class AIModel:
    """AI model configuration"""
    provider: AIProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 30
    cost_per_token: float = 0.0
    capabilities: List[str] = field(default_factory=list)
    is_available: bool = True
    last_used: Optional[datetime] = None


@dataclass
class AnalysisResult:
    """Result of file analysis"""
    file_path: Path
    analysis_type: AnalysisType
    results: Dict[str, Any]
    confidence: float
    timestamp: datetime
    model_used: str
    processing_time: float
    suggestions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class CacheEntry:
    """Cache entry for AI responses"""
    key: str
    response: Any
    timestamp: datetime
    model: str
    expires_at: Optional[datetime] = None
    access_count: int = 0

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class AIModelManager:
    """Manages multiple AI models and providers"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = Logger()
        self.models: Dict[str, AIModel] = {}
        self.fallback_order: List[str] = []
        self.load_balancing = config.get('load_balancing', False)
        self.current_model_index = 0

        self._initialize_models()

    def _initialize_models(self):
        """Initialize AI models from configuration"""
        models_config = self.config.get('ai_models', {})

        for model_id, model_config in models_config.items():
            try:
                provider = AIProvider(model_config['provider'])
                model = AIModel(
                    provider=provider,
                    model_name=model_config['model_name'],
                    api_key=model_config.get('api_key'),
                    base_url=model_config.get('base_url'),
                    max_tokens=model_config.get('max_tokens', 4096),
                    temperature=model_config.get('temperature', 0.7),
                    timeout=model_config.get('timeout', 30),
                    cost_per_token=model_config.get('cost_per_token', 0.0),
                    capabilities=model_config.get('capabilities', [])
                )

                # Test model availability
                model.is_available = self._test_model_availability(model)
                self.models[model_id] = model

                if model.is_available:
                    self.fallback_order.append(model_id)

            except Exception as e:
                self.logger.error(f"Failed to initialize model {model_id}: {e}")

        if not self.fallback_order:
            raise ConfigurationError("ai_models", "No AI models available")

    def _tesdel_availability(self, model: AIModel) -> bool:
        """Test if a model is available"""
        try:
            if model.provider == AIProvider.OLLAMA:
                return self._test_ollama_availability(model)
            elif model.provider == AIProvider.GPT4ALL:
                return self._test_gpt4all_availability(model)
            elif model.provider in [AIProvider.OPENROUTER, AIProvider.OPENAI, AIProvider.ANTHROPIC]:
                return self._test_api_availability(model)
            else:
                return True  # Assume available for unknown providers
        except Exception as e:
            self.logger.error(f"Model availability test failed for {model.model_name}: {e}")
            return False

    def _test_ollama_availability(self, model: AIModel) -> bool:
        """Test Ollama model availability"""
        try:
            import requests
            base_url = model.base_url or "http://localhost:11434"
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(m['name'] == model.model_name for m in models)
            return False
        except Exception:
            return False

    def _test_gpt4all_availability(self, model: AIModel) -> bool:
        """Test GPT4All model availability"""
        try:
            import gpt4all
            # Try to load the model
            gpt4all.GPT4All(model.model_name)
            return True
        except Exception:
            return False

    def _test_api_availability(self, model: AIModel) -> bool:
        """Test API-based model availability"""
        if not model.api_key:
            return False

        try:
            import requests

            if model.provider == AIProvider.OPENROUTER:
                headers = {"Authorization": f"Bearer {model.api_key}"}
                response = requests.get("https://openrouter.ai/api/v1/models",
                                      headers=headers, timeout=5)
                return response.status_code == 200
            elif model.provider == AIProvider.OPENAI:
                headers = {"Authorization": f"Bearer {model.api_key}"}
                response = requests.get("https://api.openai.com/v1/models",
                                      headers=headers, timeout=5)
                return response.status_code == 200
            elif model.provider == AIProvider.ANTHROPIC:
                headers = {"x-api-key": model.api_key}
                # Anthropic doesn't have a simple models endpoint, so just return True if key exists
                return True

            return False
        except Exception:
            return False

    def get_best_model(self, capabilities: List[str] = None,
                      exclude: List[str] = None) -> Optional[AIModel]:
        """Get the best available model for given capabilities"""
        exclude = exclude or []

        available_models = [
            (model_id, model) for model_id, model in self.models.items()
            if model.is_available and model_id not in exclude
        ]

        if not available_models:
            return None

        # Filter by capabilities if specified
        if capabilities:
            filtered_models = []
            for model_id, model in available_models:
                if all(cap in model.capabilities for cap in capabilities):
                    filtered_models.append((model_id, model))

            if filtered_models:
                available_models = filtered_models

        # Load balancing
        if self.load_balancing and len(available_models) > 1:
            model_id, model = available_models[self.current_model_index % len(available_models)]
            self.current_model_index += 1
            return model

        # Return first available model (highest priority)
        return available_models[0][1]

    def get_model(self, model_id: str) -> Optional[AIModel]:
        """Get specific model by ID"""
        return self.models.get(model_id)

    def update_model_status(self, model_id: str, is_available: bool):
        """Update model availability status"""
        if model_id in self.models:
            self.models[model_id].is_available = is_available

            if is_available and model_id not in self.fallback_order:
                self.fallback_order.append(model_id)
            elif not is_available and model_id in self.fallback_order:
                self.fallback_order.remove(model_id)


class ResponseCache:
    """Enhanced cache for AI responses with performance optimizations"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.logger = Logger()

        # Performance optimizations
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size': 0
        }
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

    def _generate_key(self, prompt: str, model: str, **kwargs) -> str:
        """Generate cache key from prompt and parameters"""
        key_data = {
            'prompt': prompt,
            'model': model,
            **kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(self, prompt: str, model: str, **kwargs) -> Optional[Any]:
        """Get cached response with performance optimizations"""
        # Periodic cleanup
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self.clear_expired()
            self._last_cleanup = current_time

        key = self._generate_key(prompt, model, **kwargs)

        if key not in self.cache:
            self._cache_stats['misses'] += 1
            return None

        entry = self.cache[key]

        # Check if expired
        if entry.is_expired():
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            self._cache_stats['misses'] += 1
            return None

        # Update access
        entry.access_count += 1
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

        self._cache_stats['hits'] += 1
        return entry.response

    def set(self, prompt: str, model: str, response: Any, ttl: Optional[int] = None, **kwargs):
        """Cache response"""
        key = self._generate_key(prompt, model, **kwargs)

        # Calculate expiration
        expires_at = None
        if ttl is not None:
            expires_at = datetime.now() + timedelta(seconds=ttl)
        elif self.default_ttl > 0:
            expires_at = datetime.now() + timedelta(seconds=self.default_ttl)

        # Create cache entry
        entry = CacheEntry(
            key=key,
            response=response,
            timestamp=datetime.now(),
            model=model,
            expires_at=expires_at
        )

        # Add to cache
        self.cache[key] = entry
        self.access_order.append(key)

        # Evict if necessary
        self._evict_if_necessary()

    def _evict_if_necessary(self):
        """Evict least recently used entries if cache is full"""
        while len(self.cache) > self.max_size:
            if not self.access_order:
                break

            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                del self.cache[oldest_key]

    def clear_expired(self):
        """Clear expired entries"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]

        for key in expired_keys:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())

        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries,
            'max_size': self.max_size,
            'hit_rate': self._calculate_hit_rate()
        }

    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_accesses = sum(entry.access_count for entry in self.cache.values())
        if total_accesses == 0:
            return 0.0

        # This is a simplified calculation
        # In practice, you'd track hits vs misses separately
        return min(1.0, total_accesses / max(1, len(self.cache)))


class AdvancedAIAssistant(AIAssistant):
    """Enhanced AI assistant with multi-model support and advanced analysis"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_manager = AIModelManager(config)
        self.cache = ResponseCache(
            max_size=config.get('cache_size', 1000),
            default_ttl=config.get('cache_ttl', 3600)
        )

        # Analysis capabilities
        self.analysis_history: List[AnalysisResult] = []
        self.max_history_size = config.get('max_analysis_history', 1000)

        # Performance tracking
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'total_tokens_used': 0,
            'total_cost': 0.0,
            'average_response_time': 0.0
        }

    async def analyze_file_comprehensive(self, file_path: Path,
                                       analysis_types: List[AnalysisType] = None) -> List[AnalysisResult]:
        """Perform comprehensive file analysis"""
        if analysis_types is None:
            analysis_types = [AnalysisType.CONTENT, AnalysisType.METADATA, AnalysisType.SECURITY]

        results = []

        for analysis_type in analysis_types:
            try:
                result = await self._perform_single_analysis(file_path, analysis_type)
                if result:
                    results.append(result)
                    self._add_to_history(result)
            except Exception as e:
                self.logger.error(f"Analysis failed for {file_path} ({analysis_type.value}): {e}")

        return results

    async def _perform_single_analysis(self, file_path: Path,
                                     analysis_type: AnalysisType) -> Optional[AnalysisResult]:
        """Perform a single type of analysis"""
        start_time = time.time()

        try:
            # Get appropriate model for analysis type
            capabilities = self._get_required_capabilities(analysis_type)
            model = self.model_manager.get_best_model(capabilities)

            if not model:
                raise AIError(f"No suitable model available for {analysis_type.value} analysis")

            # Generate analysis prompt
            prompt = await self._generate_analysis_prompt(file_path, analysis_type)

            # Check cache first
            cached_response = self.cache.get(prompt, model.model_name, analysis_type=analysis_type.value)
            if cached_response:
                self.performance_stats['cache_hits'] += 1
                return cached_response

            # Perform analysis
            response = await self._call_model(model, prompt, analysis_type)

            # Parse response
            analysis_result = self._parse_analysis_response(
                file_path, analysis_type, response, model.model_name, time.time() - start_time
            )

            # Cache result
            self.cache.set(prompt, model.model_name, analysis_result, ttl=3600)

            # Update stats
            self.performance_stats['successful_requests'] += 1
            self._update_performance_stats(time.time() - start_time, model)

            return analysis_result

        except Exception as e:
            self.performance_stats['failed_requests'] += 1
            self.logger.error(f"Analysis failed: {e}")
            return None

    def _get_required_capabilities(self, analysis_type: AnalysisType) -> List[str]:
        """Get required model capabilities for analysis type"""
        capability_map = {
            AnalysisType.CONTENT: ['text_analysis', 'code_analysis'],
            AnalysisType.METADATA: ['file_analysis'],
            AnalysisType.SECURITY: ['security_analysis', 'vulnerability_detection'],
            AnalysisType.PERFORMANCE: ['performance_analysis'],
            AnalysisType.ORGANIZATION: ['organization_analysis'],
            AnalysisType.DUPLICATE: ['similarity_analysis'],
            AnalysisType.RELATIONSHIP: ['relationship_analysis']
        }

        return capability_map.get(analysis_type, [])

    async def _generate_analysis_prompt(self, file_path: Path,
                                      analysis_type: AnalysisType) -> str:
        """Generate analysis prompt based on file and analysis type"""
        # Read file content (with size limits)
        content = ""
        file_info = {}

        try:
            if file_path.exists() and file_path.is_file():
                file_stat = file_path.stat()
                file_info = {
                    'name': file_path.name,
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'extension': file_path.suffix.lower(),
                    'mime_type': mimetypes.guess_type(str(file_path))[0]
                }

                # Read content for text files (limit size)
                if file_stat.st_size < 1024 * 1024:  # 1MB limit
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')[:10000]  # 10K chars max
                    except Exception:
                        content = "[Binary or unreadable file]"
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")

        # Generate prompt based on analysis type
        prompts = {
            AnalysisType.CONTENT: self._generate_content_analysis_prompt(file_info, content),
            AnalysisType.METADATA: self._generate_metadata_analysis_prompt(file_info),
            AnalysisType.SECURITY: self._generate_security_analysis_prompt(file_info, content),
            AnalysisType.PERFORMANCE: self._generate_performance_analysis_prompt(file_info, content),
            AnalysisType.ORGANIZATION: self._generate_organization_analysis_prompt(file_info),
            AnalysisType.DUPLICATE: self._generate_duplicate_analysis_prompt(file_info, content),
            AnalysisType.RELATIONSHIP: self._generate_relationship_analysis_prompt(file_info, content)
        }

        return prompts.get(analysis_type, "Analyze this file.")

    def _generate_content_analysis_prompt(self, file_info: Dict, content: str) -> str:
        """Generate content analysis prompt"""
        return f"""
Analyze the following file for content insights:

File Information:
- Name: {file_info.get('name', 'Unknown')}
- Size: {file_info.get('size', 0)} bytes
- Type: {file_info.get('mime_type', 'Unknown')}
- Extension: {file_info.get('extension', 'None')}

Content Preview:
{content[:2000] if content else '[No content available]'}

Please provide:
1. Content summary and main topics
2. File type and format analysis
3. Quality assessment (readability, structure, etc.)
4. Key insights or notable patterns
5. Suggestions for improvement or organization

Respond in JSON format with the following structure:
{{
    "summary": "Brief content summary",
    "file_type": "Detected file type",
    "quality_score": 0.0-1.0,
    "insights": ["insight1", "insight2"],
    "suggestions": ["suggestion1", "suggestion2"],
    "confidence": 0.0-1.0
}}
"""

    def _generate_metadata_analysis_prompt(self, file_info: Dict) -> str:
        """Generate metadata analysis prompt"""
        return f"""
Analyze the metadata of this file:

File Information:
- Name: {file_info.get('name', 'Unknown')}
- Size: {file_info.get('size', 0)} bytes
- Modified: {file_info.get('modified', 'Unknown')}
- Type: {file_info.get('mime_type', 'Unknown')}
- Extension: {file_info.get('extension', 'None')}

Please provide:
1. File naming convention analysis
2. Size appropriateness for file type
3. Age and modification patterns
4. Potential metadata issues
5. Organization suggestions

Respond in JSON format with the following structure:
{{
    "naming_analysis": "Analysis of file naming",
    "size_analysis": "Size appropriateness assessment",
    "age_analysis": "File age and modification analysis",
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1", "suggestion2"],
    "confidence": 0.0-1.0
}}
"""

    def _generate_security_analysis_prompt(self, file_info: Dict, content: str) -> str:
        """Generate security analysis prompt"""
        return f"""
Perform a security analysis of this file:

File Information:
- Name: {file_info.get('name', 'Unknown')}
- Size: {file_info.get('size', 0)} bytes
- Type: {file_info.get('mime_type', 'Unknown')}
- Extension: {file_info.get('extension', 'None')}

Content Preview:
{content[:1000] if content else '[No content available]'}

Please analyze for:
1. Potential security vulnerabilities
2. Suspicious patterns or content
3. File type mismatches
4. Embedded threats or malicious code
5. Privacy concerns (PII, credentials, etc.)

Respond in JSON format with the following structure:
{{
    "risk_level": "low|medium|high|critical",
    "vulnerabilities": ["vuln1", "vuln2"],
    "suspicious_patterns": ["pattern1", "pattern2"],
    "privacy_issues": ["issue1", "issue2"],
    "recommendations": ["rec1", "rec2"],
    "confidence": 0.0-1.0
}}
"""

    def _generate_performance_analysis_prompt(self, file_info: Dict, content: str) -> str:
        """Generate performance analysis prompt"""
        return f"""
Analyze this file for performance implications:

File Information:
- Name: {file_info.get('name', 'Unknown')}
- Size: {file_info.get('size', 0)} bytes
- Type: {file_info.get('mime_type', 'Unknown')}

Content Preview:
{content[:1000] if content else '[No content available]'}

Please analyze:
1. File size optimization opportunities
2. Format efficiency for intended use
3. Compression potential
4. Access pattern implications
5. Storage and transfer considerations

Respond in JSON format with the following structure:
{{
    "size_efficiency": 0.0-1.0,
    "compression_potential": "Estimated compression ratio",
    "optimization_opportunities": ["opp1", "opp2"],
    "performance_impact": "low|medium|high",
    "recommendations": ["rec1", "rec2"],
    "confidence": 0.0-1.0
}}
"""

    def _generate_organization_analysis_prompt(self, file_info: Dict) -> str:
        """Generate organization analysis prompt"""
        return f"""
Analyze this file for organization and categorization:

File Information:
- Name: {file_info.get('name', 'Unknown')}
- Size: {file_info.get('size', 0)} bytes
- Type: {file_info.get('mime_type', 'Unknown')}
- Extension: {file_info.get('extension', 'None')}

Please suggest:
1. Appropriate category/folder structure
2. Naming improvements
3. Tagging suggestions
4. Related file groupings
5. Archive/cleanup recommendations

Respond in JSON format with the following structure:
{{
    "suggested_category": "Category name",
    "folder_structure": ["folder1", "folder2"],
    "naming_suggestions": ["name1", "name2"],
    "tags": ["tag1", "tag2"],
    "cleanup_action": "keep|archive|delete",
    "confidence": 0.0-1.0
}}
"""

    def _generate_duplicate_analysis_prompt(self, file_info: Dict, content: str) -> str:
        """Generate duplicate analysis prompt"""
        return f"""
Analyze this file for duplicate detection:

File Information:
- Name: {file_info.get('name', 'Unknown')}
- Size: {file_info.get('size', 0)} bytes
- Type: {file_info.get('mime_type', 'Unknown')}

Content Hash/Preview:
{content[:500] if content else '[No content available]'}

Please provide:
1. Content fingerprint characteristics
2. Likely duplicate indicators
3. Similarity patterns to look for
4. Deduplication strategies
5. Uniqueness assessment

Respond in JSON format with the following structure:
{{
    "content_fingerprint": "Unique characteristics",
    "duplicate_indicators": ["indicator1", "indicator2"],
    "similarity_patterns": ["pattern1", "pattern2"],
    "uniqueness_score": 0.0-1.0,
    "dedup_strategy": "Strategy recommendation",
    "confidence": 0.0-1.0
}}
"""

    def _generate_relationship_analysis_prompt(self, file_info: Dict, content: str) -> str:
        """Generate relationship analysis prompt"""
        return f"""
Analyze this file for relationships with other files:

File Information:
- Name: {file_info.get('name', 'Unknown')}
- Size: {file_info.get('size', 0)} bytes
- Type: {file_info.get('mime_type', 'Unknown')}

Content Preview:
{content[:1000] if content else '[No content available]'}

Please identify:
1. Dependencies on other files
2. Files that might depend on this one
3. Related file patterns
4. Project/workflow relationships
5. Grouping suggestions

Respond in JSON format with the following structure:
{{
    "dependencies": ["file1", "file2"],
    "dependents": ["file3", "file4"],
    "related_patterns": ["pattern1", "pattern2"],
    "project_context": "Context description",
    "grouping_suggestions": ["group1", "group2"],
    "confidence": 0.0-1.0
}}
"""

    async def _call_model(self, model: AIModel, prompt: str,
                         analysis_type: AnalysisType) -> str:
        """Call AI model with prompt"""
        try:
            if model.provider == AIProvider.OLLAMA:
                return await self._call_ollama(model, prompt)
            elif model.provider == AIProvider.GPT4ALL:
                return await self._call_gpt4all(model, prompt)
            elif model.provider in [AIProvider.OPENROUTER, AIProvider.OPENAI, AIProvider.ANTHROPIC]:
                return await self._call_api_model(model, prompt)
            else:
                raise AIError(f"Unsupported provider: {model.provider}")

        except Exception as e:
            self.logger.error(f"Model call failed: {e}")
            raise

    async def _call_ollama(self, model: AIModel, prompt: str) -> str:
        """Call Ollama model"""
        try:
            import aiohttp

            base_url = model.base_url or "http://localhost:11434"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": model.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": model.temperature,
                            "num_predict": model.max_tokens
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=model.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '')
                    else:
                        raise AIError(f"Ollama API error: {response.status}")

        except Exception as e:
            raise AIError(f"Ollama call failed: {e}")

    async def _call_gpt4all(self, model: AIModel, prompt: str) -> str:
        """Call GPT4All model"""
        try:
            import gpt4all

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()

            def _generate():
                gpt4all_model = gpt4all.GPT4All(model.model_name)
                return gpt4all_model.generate(
                    prompt,
                    max_tokens=model.max_tokens,
                    temp=model.temperature
                )

            return await loop.run_in_executor(None, _generate)

        except Exception as e:
            raise AIError(f"GPT4All call failed: {e}")

    async def _call_api_model(self, model: AIModel, prompt: str) -> str:
        """Call API-based model (OpenRouter, OpenAI, Anthropic)"""
        try:
            import aiohttp

            if model.provider == AIProvider.OPENROUTER:
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {model.api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": model.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": model.max_tokens,
                    "temperature": model.temperature
                }
            elif model.provider == AIProvider.OPENAI:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {model.api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": model.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": model.max_tokens,
                    "temperature": model.temperature
                }
            elif model.provider == AIProvider.ANTHROPIC:
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "x-api-key": model.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
                data = {
                    "model": model.model_name,
                    "max_tokens": model.max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": model.temperature
                }
            else:
                raise AIError(f"Unsupported API provider: {model.provider}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=model.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        if model.provider == AIProvider.ANTHROPIC:
                            return result.get('content', [{}])[0].get('text', '')
                        else:
                            return result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    else:
                        error_text = await response.text()
                        raise AIError(f"API error {response.status}: {error_text}")

        except Exception as e:
            raise AIError(f"API call failed: {e}")

    def _parse_analysis_response(self, file_path: Path, analysis_type: AnalysisType,
                               response: str, model_name: str, processing_time: float) -> AnalysisResult:
        """Parse AI response into AnalysisResult"""
        try:
            # Try to parse as JSON
            if response.strip().startswith('{'):
                results = json.loads(response)
            else:
                # Fallback to text parsing
                results = {"raw_response": response}

            # Extract confidence if available
            confidence = results.get('confidence', 0.8)

            # Extract suggestions and warnings
            suggestions = results.get('suggestions', results.get('recommendations', []))
            warnings = results.get('warnings', results.get('issues', []))

            return AnalysisResult(
                file_path=file_path,
                analysis_type=analysis_type,
                results=results,
                confidence=confidence,
                timestamp=datetime.now(),
                model_used=model_name,
                processing_time=processing_time,
                suggestions=suggestions if isinstance(suggestions, list) else [],
                warnings=warnings if isinstance(warnings, list) else []
            )

        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            return AnalysisResult(
                file_path=file_path,
                analysis_type=analysis_type,
                results={"raw_response": response},
                confidence=0.5,
                timestamp=datetime.now(),
                model_used=model_name,
                processing_time=processing_time,
                suggestions=[],
                warnings=["Response was not in expected JSON format"]
            )

    def _add_to_history(self, result: AnalysisResult):
        """Add analysis result to history"""
        self.analysis_history.append(result)

        # Trim history if too large
        if len(self.analysis_history) > self.max_history_size:
            self.analysis_history = self.analysis_history[-self.max_history_size:]

    def _update_performance_stats(self, response_time: float, model: AIModel):
        """Update performance statistics"""
        self.performance_stats['total_requests'] += 1

        # Update average response time
        total_time = (self.performance_stats['average_response_time'] *
                     (self.performance_stats['total_requests'] - 1) + response_time)
        self.performance_stats['average_response_time'] = total_time / self.performance_stats['total_requests']

        # Estimate token usage and cost (simplified)
        estimated_tokens = len(str(response_time)) // 4  # Rough estimate
        self.performance_stats['total_tokens_used'] += estimated_tokens
        self.performance_stats['total_cost'] += estimated_tokens * model.cost_per_token

    async def get_analysis_history(self, file_path: Optional[Path] = None,
                                 analysis_type: Optional[AnalysisType] = None,
                                 limit: int = 100) -> List[AnalysisResult]:
        """Get analysis history with optional filtering"""
        results = self.analysis_history

        if file_path:
            results = [r for r in results if r.file_path == file_path]

        if analysis_type:
            results = [r for r in results if r.analysis_type == analysis_type]

        return results[-limit:] if limit > 0 else results

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        cache_stats = self.cache.get_stats()

        return {
            **self.performance_stats,
            'cache_stats': cache_stats,
            'available_models': len([m for m in self.model_manager.models.values() if m.is_available]),
            'total_models': len(self.model_manager.models)
        }

    async def clear_cache(self):
        """Clear response cache"""
        self.cache.cache.clear()
        self.cache.access_order.clear()

    async def refresh_models(self):
        """Refresh model availability"""
        for model_id, model in self.model_manager.models.items():
            is_available = self.model_manager._test_availability(model)
            self.model_manager.update_model_status(model_id, is_available)
            is_available = self.model_manager._test_availability(model)
            self.model_manager.update_model_status(model_id, is_available)

    async def initialize(self) -> None:
        """Initialize the AI assistant"""
        try:
            self.logger.info("Initializing AdvancedAIAssistant")

            # Refresh model availability
            await self.refresh_models()

            # Clear expired cache entries
            self.cache.clear_expired()

            self.logger.info("AdvancedAIAssistant initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize AdvancedAIAssistant: {e}")
            raise

    def set_file_manager(self, file_manager) -> None:
        """Set the file manager for context"""
        self.file_manager = file_manager
        self.logger.debug("File manager set for AI assistant")

    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a natural language query"""
        try:
            self.logger.debug(f"Processing query: {query[:100]}...")

            # Get best model for general queries
            model = self.model_manager.get_best_model(['text_generation'])
            if not model:
                return {
                    'success': False,
                    'response': 'No AI models available',
                    'error': 'No models configured'
                }

            # Create context-aware prompt
            prompt = self._create_query_prompt(query, context or {})

            # Call model
            response = await self._call_model(model, prompt, AnalysisType.CONTENT)

            return {
                'success': True,
                'response': response,
                'model': model.model_name,
                'query': query
            }

        except Exception as e:
            self.logger.error(f"Query processing failed: {e}")
            return {
                'success': False,
                'response': f'Error processing query: {e}',
                'error': str(e)
            }

    def _create_query_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Create a context-aware prompt for queries"""
        prompt = f"User query: {query}\n\n"

        # Add file context if available
        if 'current_directory' in context:
            prompt += f"Current directory: {context['current_directory']}\n"

        if 'selected_files' in context:
            files = context['selected_files']
            if files:
                prompt += f"Selected files: {', '.join(str(f) for f in files[:5])}\n"

        if 'file_count' in context:
            prompt += f"Total files in directory: {context['file_count']}\n"

        prompt += "\nPlease provide a helpful response based on the query and context."

        return prompt