"""
Intelligent Organization and Automation Engine

This module provides AI-powered file organization, automated workflows,
and intelligent suggestions for file management in LaxyFile.
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import shutil

from ..core.types import OperationResult
from ..core.exceptions import OrganizationError
from ..utils.logger import Logger
from .file_analyzer import (
    ComprehensiveFileAnalyzer, FileMetadata, FileCategory,
    DuplicateGroup, DirectoryAnalysis
)
from .advanced_assistant import AdvancedAIAssistant, AnalysisType


class OrganizationStrategy(Enum):
    """File organization strategies"""
    BY_TYPE = "by_type"
    BY_DATE = "by_date"
    BY_PROJECT = "by_project"
    BY_SIZE = "by_size"
    BY_USAGE = "by_usage"
    CUSTOM = "custom"
    AI_SUGGESTED = "ai_suggested"


class AutomationTrigger(Enum):
    """Automation triggers"""
    FILE_ADDED = "file_added"
    FILE_MODIFIED = "file_modified"
    DIRECTORY_SCAN = "directory_scan"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    SIZE_THRESHOLD = "size_threshold"
    AGE_THRESHOLD = "age_threshold"


class ActionType(Enum):
    """Types of automated actions"""
    MOVE = "move"
    COPY = "copy"
ETE = "delete"
    RENAME = "rename"
    COMPRESS = "compress"
    TAG = "tag"
    BACKUP = "backup"
    NOTIFY = "notify"


@dataclass
class OrganizationRule:
    """Rule for file organization"""
    rule_id: str
    name: str
    description: str
    strategy: OrganizationStrategy
    conditions: Dict[str, Any]  # Conditions that must be met
    actions: List[Dict[str, Any]]  # Actions to take
    priority: int = 0  # Higher priority rules are applied first
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0

    def matches_file(self, metadata: FileMetadata) -> bool:
        """Check if this rule matches a file"""
        try:
            for condition_type, condition_value in self.conditions.items():
                if not self._check_condition(metadata, condition_type, condition_value):
                    return False
            return True
        except Exception:
            return False

    def _check_condition(self, metadata: FileMetadata, condition_type: str, condition_value: Any) -> bool:
        """Check a single condition"""
        if condition_type == "extension":
            return metadata.extension.lower() in [ext.lower() for ext in condition_value]
        elif condition_type == "category":
            return metadata.category.value in condition_value
        elif condition_type == "size_min":
            return metadata.size >= condition_value
        elif condition_type == "size_max":
            return metadata.size <= condition_value
        elif condition_type == "age_days":
            age = (datetime.now() - metadata.modified).days
            return age >= condition_value
        elif condition_type == "name_pattern":
            return re.search(condition_value, metadata.name, re.IGNORECASE) is not None
        elif condition_type == "path_contains":
            return condition_value.lower() in str(metadata.path).lower()
        elif condition_type == "mime_type":
            return metadata.mime_type and metadata.mime_type in condition_value
        else:
            return True


@dataclass
class AutomationRule:
    """Rule for automated actions"""
    rule_id: str
    name: str
    description: str
    trigger: AutomationTrigger
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """Check if this rule should be triggered"""
        try:
            for condition_type, condition_value in self.trigger_conditions.items():
                if not self._check_trigger_condition(context, condition_type, condition_value):
                    return False
            return True
        except Exception:
            return False

    def _check_trigger_condition(self, context: Dict[str, Any], condition_type: str, condition_value: Any) -> bool:
        """Check a trigger condition"""
        if condition_type == "file_extension":
            file_path = context.get('file_path')
            if file_path:
                return Path(file_path).suffix.lower() in [ext.lower() for ext in condition_value]
        elif condition_type == "directory_path":
            file_path = context.get('file_path')
            if file_path:
                return condition_value.lower() in str(Path(file_path).parent).lower()
        elif condition_type == "file_size":
            file_size = context.get('file_size', 0)
            return file_size >= condition_value
        elif condition_type == "time_since_last":
            if self.last_triggered:
                time_diff = datetime.now() - self.last_triggered
                return time_diff.total_seconds() >= condition_value
            return True
        else:
            return True


@dataclass
class OrganizationPlan:
    """Plan for organizing files"""
    plan_id: str
    name: str
    description: str
    target_directory: Path
    rules: List[OrganizationRule]
    estimated_changes: int
    estimated_space_saved: int
    confidence_score: float
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'plan_id': self.plan_id,
            'name': self.name,
            'description': self.description,
            'target_directory': str(self.target_directory),
            'rules': [self._rule_to_dict(rule) for rule in self.rules],
            'estimated_changes': self.estimated_changes,
            'estimated_space_saved': self.estimated_space_saved,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat()
        }

    def _rule_to_dict(self, rule: OrganizationRule) -> Dict[str, Any]:
        """Convert rule to dictionary"""
        return {
            'rule_id': rule.rule_id,
            'name': rule.name,
            'description': rule.description,
            'strategy': rule.strategy.value,
            'conditions': rule.conditions,
            'actions': rule.actions,
            'priority': rule.priority,
            'enabled': rule.enabled
        }


class DirectoryStructureGenerator:
    """Generate optimal directory structures"""

    def __init__(self, ai_assistant: Optional[AdvancedAIAssistant] = None):
        self.ai_assistant = ai_assistant
        self.logger = Logger()

    async def suggest_structure(self, metadata_list: List[FileMetadata],
                              strategy: OrganizationStrategy = OrganizationStrategy.AI_SUGGESTED) -> Dict[str, List[Path]]:
        """Suggest directory structure for files"""
        try:
            if strategy == OrganizationStrategy.BY_TYPE:
                return self._organize_by_type(metadata_list)
            elif strategy == OrganizationStrategy.BY_DATE:
                return self._organize_by_date(metadata_list)
            elif strategy == OrganizationStrategy.BY_PROJECT:
                return await self._organize_by_project(metadata_list)
            elif strategy == OrganizationStrategy.BY_SIZE:
                return self._organize_by_size(metadata_list)
            elif strategy == OrganizationStrategy.BY_USAGE:
                return self._organize_by_usage(metadata_list)
            elif strategy == OrganizationStrategy.AI_SUGGESTED:
                return await self._ai_suggested_structure(metadata_list)
            else:
                return self._organize_by_type(metadata_list)  # Default fallback

        except Exception as e:
            self.logger.error(f"Error suggesting directory structure: {e}")
            return {}

    def _organize_by_type(self, metadata_list: List[FileMetadata]) -> Dict[str, List[Path]]:
        """Organize files by type/category"""
        structure = {}

        for metadata in metadata_list:
            category_name = metadata.category.value.title()

            # Create subcategories for some types
            if metadata.category == FileCategory.DOCUMENT:
                if metadata.extension in ['.pdf']:
                    folder = f"{category_name}/PDFs"
                elif metadata.extension in ['.doc', '.docx']:
                    folder = f"{category_name}/Word Documents"
                elif metadata.extension in ['.txt', '.md']:
                    folder = f"{category_name}/Text Files"
                else:
                    folder = category_name
            elif metadata.category == FileCategory.IMAGE:
                if metadata.extension in ['.jpg', '.jpeg']:
                    folder = f"{category_name}/JPEG"
                elif metadata.extension in ['.png']:
                    folder = f"{category_name}/PNG"
                elif metadata.extension in ['.svg']:
                    folder = f"{category_name}/Vector"
                else:
                    folder = category_name
            elif metadata.category == FileCategory.CODE:
                if metadata.language:
                    folder = f"{category_name}/{metadata.language}"
                else:
                    folder = category_name
            else:
                folder = category_name

            if folder not in structure:
                structure[folder] = []
            structure[folder].append(metadata.path)

        return structure

    def _organize_by_date(self, metadata_list: List[FileMetadata]) -> Dict[str, List[Path]]:
        """Organize files by date"""
        structure = {}

        for metadata in metadata_list:
            year = metadata.modified.year
            month = metadata.modified.strftime('%m-%B')
            folder = f"{year}/{month}"

            if folder not in structure:
                structure[folder] = []
            structure[folder].append(metadata.path)

        return structure

    async def _organize_by_project(self, metadata_list: List[FileMetadata]) -> Dict[str, List[Path]]:
        """Organize files by detected projects"""
        structure = {}

        # Group files by directory first
        dir_groups = {}
        for metadata in metadata_list:
            parent = metadata.path.parent
            if parent not in dir_groups:
                dir_groups[parent] = []
            dir_groups[parent].append(metadata)

        # Try to detect projects
        for directory, files in dir_groups.items():
            project_name = await self._detect_project_name(directory, files)

            if project_name not in structure:
                structure[project_name] = []

            for metadata in files:
                structure[project_name].append(metadata.path)

        return structure

    def _organize_by_size(self, metadata_list: List[FileMetadata]) -> Dict[str, List[Path]]:
        """Organize files by size"""
        structure = {
            "Large Files (>100MB)": [],
            "Medium Files (10-100MB)": [],
            "Small Files (1-10MB)": [],
            "Tiny Files (<1MB)": []
        }

        for metadata in metadata_list:
            size_mb = metadata.size / (1024 * 1024)

            if size_mb > 100:
                structure["Large Files (>100MB)"].append(metadata.path)
            elif size_mb > 10:
                structure["Medium Files (10-100MB)"].append(metadata.path)
            elif size_mb > 1:
                structure["Small Files (1-10MB)"].append(metadata.path)
            else:
                structure["Tiny Files (<1MB)"].append(metadata.path)

        return structure

    def _organize_by_usage(self, metadata_list: List[FileMetadata]) -> Dict[str, List[Path]]:
        """Organize files by usage patterns"""
        structure = {
            "Recently Used": [],
            "Frequently Accessed": [],
            "Archive": []
        }

        now = datetime.now()

        for metadata in metadata_list:
            days_since_access = (now - metadata.accessed).days
            days_since_modified = (now - metadata.modified).days

            if days_since_access <= 7 or days_since_modified <= 7:
                structure["Recently Used"].append(metadata.path)
            elif days_since_access <= 30:
                structure["Frequently Accessed"].append(metadata.path)
            else:
                structure["Archive"].append(metadata.path)

        return structure

    async def _ai_suggested_structure(self, metadata_list: List[FileMetadata]) -> Dict[str, List[Path]]:
        """Use AI to suggest optimal structure"""
        if not self.ai_assistant:
            return self._organize_by_type(metadata_list)  # Fallback

        try:
            # Prepare file information for AI
            file_info = []
            for metadata in metadata_list:
                file_info.append({
                    'name': metadata.name,
                    'path': str(metadata.path),
                    'category': metadata.category.value,
                    'size': metadata.size,
                    'extension': metadata.extension,
                    'language': metadata.language,
                    'modified': metadata.modified.isoformat()
                })

            # Create AI prompt
            prompt = f"""
Analyze the following {len(file_info)} files and suggest an optimal directory structure for organization:

Files:
{json.dumps(file_info[:50], indent=2)}  # Limit to first 50 files

Please suggest a directory structure that:
1. Groups related files together
2. Creates logical hierarchies
3. Considers file types, projects, and usage patterns
4. Minimizes deep nesting
5. Uses clear, descriptive folder names

Respond with a JSON structure where keys are folder paths and values are lists of file paths:
{{
    "folder1/subfolder": ["file1.txt", "file2.txt"],
    "folder2": ["file3.jpg", "file4.png"]
}}
"""

            # Get AI suggestion (simplified - would use actual AI call)
            # For now, return a hybrid approach
            type_structure = self._organize_by_type(metadata_list)
            project_structure = await self._organize_by_project(metadata_list)

            # Combine structures intelligently
            combined_structure = {}

            # Prioritize project-based organization for code files
            for folder, files in project_structure.items():
                code_files = [f for f in files if any(m.path == f and m.category == FileCategory.CODE for m in metadata_list)]
                if code_files:
                    combined_structure[f"Projects/{folder}"] = code_files

            # Add type-based organization for other files
            for folder, files in type_structure.items():
                non_code_files = [f for f in files if not any(m.path == f and m.category == FileCategory.CODE for m in metadata_list)]
                if non_code_files:
                    combined_structure[folder] = non_code_files

            return combined_structure

        except Exception as e:
            self.logger.error(f"AI structure suggestion failed: {e}")
            return self._organize_by_type(metadata_list)  # Fallback

    async def _detect_project_name(self, directory: Path, files: List[FileMetadata]) -> str:
        """Detect project name from directory and files"""
        # Check for common project indicators
        project_files = ['.git', 'package.json', 'requirements.txt', 'Cargo.toml', 'pom.xml', 'Makefile']

        for file_metadata in files:
            if file_metadata.name in project_files:
                return directory.name

        # Check for README files
        readme_files = [f for f in files if f.name.lower().startswith('readme')]
        if readme_files:
            return directory.name

        # Check for common project structure
        code_files = [f for f in files if f.category == FileCategory.CODE]
        if len(code_files) > 3:  # Likely a code project
            return directory.name

        return f"Misc/{directory.name}"


class OrganizationEngine:
    """Main engine for intelligent file organization"""

    def __init__(self, config: Dict[str, Any],
                 file_analyzer: ComprehensiveFileAnalyzer,
                 ai_assistant: Optional[AdvancedAIAssistant] = None):
        self.config = config
        self.file_analyzer = file_analyzer
        self.ai_assistant = ai_assistant
        self.logger = Logger()

        self.structure_generator = DirectoryStructureGenerator(ai_assistant)

        # Organization rules
        self.organization_rules: List[OrganizationRule] = []
        self.automation_rules: List[AutomationRule] = []

        # Load default rules
        self._load_default_rules()

    def _load_default_rules(self):
        """Load default organization and automation rules"""
        # Default organization rules
        self.organization_rules = [
            OrganizationRule(
                rule_id="organize_downloads",
                name="Organize Downloads",
                description="Organize files in Downloads folder by type",
                strategy=OrganizationStrategy.BY_TYPE,
                conditions={"path_contains": "downloads"},
                actions=[{"type": "move", "destination": "Organized/{category}"}],
                priority=10
            ),
            OrganizationRule(
                rule_id="archive_old_files",
                name="Archive Old Files",
                description="Move files older than 1 year to archive",
                strategy=OrganizationStrategy.BY_DATE,
                conditions={"age_days": 365},
                actions=[{"type": "move", "destination": "Archive/{year}"}],
                priority=5
            ),
            OrganizationRule(
                rule_id="organize_screenshots",
                name="Organize Screenshots",
                description="Move screenshot files to Screenshots folder",
                strategy=OrganizationStrategy.BY_TYPE,
                conditions={"name_pattern": r"screenshot|screen shot"},
                actions=[{"type": "move", "destination": "Screenshots"}],
                priority=15
            )
        ]

        # Default automation rules
        self.automation_rules = [
            AutomationRule(
                rule_id="auto_organize_new_files",
                name="Auto-organize New Files",
                description="Automatically organize new files when added",
                trigger=AutomationTrigger.FILE_ADDED,
                trigger_conditions={"file_extension": [".jpg", ".png", ".pdf", ".doc"]},
                actions=[{"type": "organize", "strategy": "by_type"}]
            ),
            AutomationRule(
                rule_id="cleanup_temp_files",
                name="Cleanup Temporary Files",
                description="Delete temporary files older than 7 days",
                trigger=AutomationTrigger.SCHEDULED,
                trigger_conditions={"time_since_last": 86400},  # 24 hours
                actions=[{"type": "delete", "conditions": {"extension": [".tmp", ".temp"], "age_days": 7}}]
            )
        ]

    async def analyze_and_suggest(self, directory_path: Path) -> OrganizationPlan:
        """Analyze directory and suggest organization plan"""
        try:
            # Perform comprehensive analysis
            analysis = await self.file_analyzer.analyze_directory(directory_path)

            # Get file metadata
            file_paths = [p for p in directory_path.rglob('*') if p.is_file()]
            metadata_list = []

            for file_path in file_paths:
                try:
                    metadata = await self.file_analyzer.metadata_extractor.extract_metadata(file_path)
                    metadata_list.append(metadata)
                except Exception as e:
                    self.logger.error(f"Error extracting metadata for {file_path}: {e}")

            # Generate organization suggestions
            suggestions = await self._generate_organization_suggestions(analysis, metadata_list)

            # Create organization plan
            plan = OrganizationPlan(
                plan_id=f"plan_{int(datetime.now().timestamp())}",
                name=f"Organization Plan for {directory_path.name}",
                description=f"Intelligent organization plan for {len(metadata_list)} files",
                target_directory=directory_path,
                rules=suggestions['rules'],
                estimated_changes=suggestions['estimated_changes'],
                estimated_space_saved=suggestions['estimated_space_saved'],
                confidence_score=suggestions['confidence_score']
            )

            return plan

        except Exception as e:
            self.logger.error(f"Error creating organization plan: {e}")
            raise OrganizationError(f"Failed to create organization plan: {e}")

    async def _generate_organization_suggestions(self, analysis: DirectoryAnalysis,
                                               metadata_list: List[FileMetadata]) -> Dict[str, Any]:
        """Generate intelligent organization suggestions"""
        suggestions = {
            'rules': [],
            'estimated_changes': 0,
            'estimated_space_saved': 0,
            'confidence_score': 0.8
        }

        try:
            # Suggest duplicate cleanup
            if analysis.duplicate_groups:
                duplicate_rule = OrganizationRule(
                    rule_id="cleanup_duplicates",
                    name="Remove Duplicate Files",
                    description=f"Remove {len(analysis.duplicate_groups)} groups of duplicate files",
                    strategy=OrganizationStrategy.CUSTOM,
                    conditions={},
                    actions=[{"type": "delete_duplicates"}],
                    priority=20
                )
                suggestions['rules'].append(duplicate_rule)
                suggestions['estimated_space_saved'] += sum(g.potential_savings for g in analysis.duplicate_groups)
                suggestions['estimated_changes'] += len(analysis.duplicate_groups)

            # Suggest organizing by type if many different categories
            if len(analysis.file_categories) > 3:
                type_rule = OrganizationRule(
                    rule_id="organize_by_type",
                    name="Organize by File Type",
                    description="Group files by their type/category",
                    strategy=OrganizationStrategy.BY_TYPE,
                    conditions={},
                    actions=[{"type": "move", "destination": "{category}"}],
                    priority=10
                )
                suggestions['rules'].append(type_rule)
                suggestions['estimated_changes'] += len(metadata_list)

            # Suggest archiving old files
            if analysis.old_files:
                archive_rule = OrganizationRule(
                    rule_id="archive_old",
                    name="Archive Old Files",
                    description=f"Archive {len(analysis.old_files)} old files",
                    strategy=OrganizationStrategy.BY_DATE,
                    conditions={"age_days": 365},
                    actions=[{"type": "move", "destination": "Archive/{year}"}],
                    priority=5
                )
                suggestions['rules'].append(archive_rule)
                suggestions['estimated_changes'] += len(analysis.old_files)

            # Suggest cleaning up empty files
            if analysis.empty_files:
                empty_rule = OrganizationRule(
                    rule_id="remove_empty",
                    name="Remove Empty Files",
                    description=f"Remove {len(analysis.empty_files)} empty files",
                    strategy=OrganizationStrategy.CUSTOM,
                    conditions={"size_max": 0},
                    actions=[{"type": "delete"}],
                    priority=15
                )
                suggestions['rules'].append(empty_rule)
                suggestions['estimated_changes'] += len(analysis.empty_files)

            # Suggest cleaning up temporary files
            if analysis.temporary_files:
                temp_rule = OrganizationRule(
                    rule_id="cleanup_temp",
                    name="Clean Temporary Files",
                    description=f"Remove {len(analysis.temporary_files)} temporary files",
                    strategy=OrganizationStrategy.CUSTOM,
                    conditions={"category": ["temporary"]},
                    actions=[{"type": "delete"}],
                    priority=12
                )
                suggestions['rules'].append(temp_rule)
                suggestions['estimated_changes'] += len(analysis.temporary_files)

            # Use AI for additional suggestions if available
            if self.ai_assistant:
                ai_suggestions = await self._get_ai_suggestions(analysis, metadata_list)
                suggestions['rules'].extend(ai_suggestions)

            return suggestions

        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")
            return suggestions

    async def _get_ai_suggestions(self, analysis: DirectoryAnalysis,
                                metadata_list: List[FileMetadata]) -> List[OrganizationRule]:
        """Get AI-powered organization suggestions"""
        try:
            # Prepare analysis summary for AI
            summary = {
                'total_files': analysis.total_files,
                'total_size': analysis.total_size,
                'categories': {cat.value: count for cat, count in analysis.file_categories.items()},
                'duplicates': len(analysis.duplicate_groups),
                'large_files': len(analysis.large_files),
                'old_files': len(analysis.old_files),
                'organization_score': analysis.organization_score
            }

            # This would use the AI assistant to generate suggestions
            # For now, return empty list
            return []

        except Exception as e:
            self.logger.error(f"AI suggestions failed: {e}")
            return []

    async def execute_plan(self, plan: OrganizationPlan,
                          dry_run: bool = True,
                          progress_callback: Optional[Callable] = None) -> OperationResult:
        """Execute an organization plan"""
        try:
            if dry_run:
                return await self._simulate_plan_execution(plan, progress_callback)
            else:
                return await self._execute_plan_real(plan, progress_callback)

        except Exception as e:
            self.logger.error(f"Error executing plan: {e}")
            return OperationResult(
                success=False,
                message=f"Plan execution failed: {e}",
                errors=[str(e)]
            )

    async def _simulate_plan_execution(self, plan: OrganizationPlan,
                                     progress_callback: Optional[Callable] = None) -> OperationResult:
        """Simulate plan execution (dry run)"""
        changes = []
        errors = []

        try:
            # Get all files in target directory
            file_paths = [p for p in plan.target_directory.rglob('*') if p.is_file()]
            total_files = len(file_paths)
            processed = 0

            for file_path in file_paths:
                try:
                    # Extract metadata
                    metadata = await self.file_analyzer.metadata_extractor.extract_metadata(file_path)

                    # Apply rules
                    for rule in sorted(plan.rules, key=lambda r: r.priority, reverse=True):
                        if rule.enabled and rule.matches_file(metadata):
                            # Simulate action
                            for action in rule.actions:
                                action_type = action.get('type')
                                if action_type == 'move':
                                    destination = self._resolve_destination(action.get('destination', ''), metadata)
                                    changes.append(f"MOVE: {file_path} -> {destination}")
                                elif action_type == 'delete':
                                    changes.append(f"DELETE: {file_path}")
                                elif action_type == 'delete_duplicates':
                                    changes.append(f"DELETE DUPLICATE: {file_path}")
                            break  # Apply only first matching rule

                    processed += 1
                    if progress_callback:
                        await progress_callback(processed / total_files * 100, f"Analyzed {processed}/{total_files} files")

                except Exception as e:
                    errors.append(f"Error processing {file_path}: {e}")

            return OperationResult(
                success=len(errors) == 0,
                message=f"Dry run completed: {len(changes)} changes planned, {len(errors)} errors",
                affected_files=[],
                errors=errors,
                metadata={'planned_changes': changes}
            )

        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Dry run failed: {e}",
                errors=[str(e)]
            )

    async def _execute_plan_real(self, plan: OrganizationPlan,
                               progress_callback: Optional[Callable] = None) -> OperationResult:
        """Execute plan with real file operations"""
        changes = []
        errors = []

        try:
            # Get all files in target directory
            file_paths = [p for p in plan.target_directory.rglob('*') if p.is_file()]
            total_files = len(file_paths)
            processed = 0

            for file_path in file_paths:
                try:
                    # Extract metadata
                    metadata = await self.file_analyzer.metadata_extractor.extract_metadata(file_path)

                    # Apply rules
                    for rule in sorted(plan.rules, key=lambda r: r.priority, reverse=True):
                        if rule.enabled and rule.matches_file(metadata):
                            # Execute action
                            for action in rule.actions:
                                success = await self._execute_action(file_path, action, metadata)
                                if success:
                                    changes.append(str(file_path))
                                    rule.usage_count += 1
                                    rule.last_used = datetime.now()
                            break  # Apply only first matching rule

                    processed += 1
                    if progress_callback:
                        await progress_callback(processed / total_files * 100, f"Processed {processed}/{total_files} files")

                except Exception as e:
                    errors.append(f"Error processing {file_path}: {e}")

            return OperationResult(
                success=len(errors) == 0,
                message=f"Plan executed: {len(changes)} files processed, {len(errors)} errors",
                affected_files=changes,
                errors=errors
            )

        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Plan execution failed: {e}",
                errors=[str(e)]
            )

    async def _execute_action(self, file_path: Path, action: Dict[str, Any], metadata: FileMetadata) -> bool:
        """Execute a single action on a file"""
        try:
            action_type = action.get('type')

            if action_type == 'move':
                destination = self._resolve_destination(action.get('destination', ''), metadata)
                destination_path = Path(destination)
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(destination_path))
                return True

            elif action_type == 'copy':
                destination = self._resolve_destination(action.get('destination', ''), metadata)
                destination_path = Path(destination)
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(file_path), str(destination_path))
                return True

            elif action_type == 'delete':
                file_path.unlink()
                return True

            elif action_type == 'rename':
                new_name = action.get('new_name', file_path.name)
                new_path = file_path.parent / new_name
                file_path.rename(new_path)
                return True

            else:
                self.logger.warning(f"Unknown action type: {action_type}")
                return False

        except Exception as e:
            self.logger.error(f"Error executing action {action_type} on {file_path}: {e}")
            return False

    def _resolve_destination(self, destination_template: str, metadata: FileMetadata) -> str:
        """Resolve destination path template with metadata"""
        try:
            # Replace placeholders
            destination = destination_template.replace('{category}', metadata.category.value.title())
            destination = destination.replace('{extension}', metadata.extension.lstrip('.'))
            destination = destination.replace('{year}', str(metadata.modified.year))
            destination = destination.replace('{month}', metadata.modified.strftime('%m-%B'))
            destination = destination.replace('{name}', metadata.path.stem)

            if metadata.language:
                destination = destination.replace('{language}', metadata.language)

            # Ensure it's relative to the base directory
            if not destination.startswith('/'):
                destination = str(metadata.path.parent / destination / metadata.name)

            return destination

        except Exception as e:
            self.logger.error(f"Error resolving destination template: {e}")
            return str(metadata.path)

    def add_organization_rule(self, rule: OrganizationRule):
        """Add a new organization rule"""
        self.organization_rules.append(rule)
        self.organization_rules.sort(key=lambda r: r.priority, reverse=True)

    def add_automation_rule(self, rule: AutomationRule):
        """Add a new automation rule"""
        self.automation_rules.append(rule)

    def get_organization_rules(self) -> List[OrganizationRule]:
        """Get all organization rules"""
        return self.organization_rules.copy()

    def get_automation_rules(self) -> List[AutomationRule]:
        """Get all automation rules"""
        return self.automation_rules.copy()

    async def trigger_automation(self, trigger: AutomationTrigger, context: Dict[str, Any]) -> List[OperationResult]:
        """Trigger automation rules based on context"""
        results = []

        for rule in self.automation_rules:
            if rule.enabled and rule.trigger == trigger and rule.should_trigger(context):
                try:
                    result = await self._execute_automation_rule(rule, context)
                    results.append(result)
                    rule.trigger_count += 1
                    rule.last_triggered = datetime.now()
                except Exception as e:
                    self.logger.error(f"Error executing automation rule {rule.name}: {e}")
                    results.append(OperationResult(
                        success=False,
                        message=f"Automation rule failed: {e}",
                        errors=[str(e)]
                    ))

        return results

    async def _execute_automation_rule(self, rule: AutomationRule, context: Dict[str, Any]) -> OperationResult:
        """Execute an automation rule"""
        try:
            # This would implement the actual automation logic
            # For now, return a success result
            return OperationResult(
                success=True,
                message=f"Automation rule '{rule.name}' executed successfully",
                affected_files=[]
            )

        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Automation rule execution failed: {e}",
                errors=[str(e)]
            )