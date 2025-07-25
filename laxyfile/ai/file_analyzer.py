"""
Comprehensive File Analysis System

This module provides deep file analysis capabilities including content analysis,
metadata extraction, duplicate detection, and relationship mapping.
"""

import asyncio
import hashlib
import mimetypes
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import sqlite3
from datetime import datetime, timedelta
import difflib

from ..core.types import OperationResult
from ..core.exceptions import AnalysisError
from ..utils.logger import Logger
from .advanced_assistant import AdvancedAIAssistant, AnalysisType, AnalysisResult


class FileCategory(Enum):
    """File categories for organization"""
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CODE = "code"
    ARCHIVE = "archive"
    DATA = "data"
    EXECUTABLE = "executable"
    SYSTEM = "system"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


class DuplicateType(Enum):
    """Types of file duplicates"""
    EXACT = "exact"          # Identical content
    SIMILAR = "similar"      # Similar content
    NAME_SIMILAR = "name_similar"  # Similar names
    SIZE_MATCH = "size_match"      # Same size, different content


@dataclass
class FileMetadata:
    """Comprehensive file metadata"""
    path: Path
    name: str
    size: int
    created: datetime
    modified: datetime
    accessed: datetime
    extension: str
    mime_type: Optional[str]
    category: FileCategory

    # Content hashes
    md5_hash: Optional[str] = None
    sha256_hash: Optional[str] = None
    content_hash: Optional[str] = None  # Fuzzy hash for similarity

    # Analysis results
    encoding: Optional[str] = None
    line_count: Optional[int] = None
    word_count: Optional[int] = None
    language: Optional[str] = None  # Programming language or natural language

    # Permissions and ownership
    permissions: O[str] = None
    owner: Optional[str] = None
    group: Optional[str] = None

    # Custom attributes
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    importance_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'path': str(self.path),
            'name': self.name,
            'size': self.size,
            'created': self.created.isoformat(),
            'modified': self.modified.isoformat(),
            'accessed': self.accessed.isoformat(),
            'extension': self.extension,
            'mime_type': self.mime_type,
            'category': self.category.value,
            'md5_hash': self.md5_hash,
            'sha256_hash': self.sha256_hash,
            'content_hash': self.content_hash,
            'encoding': self.encoding,
            'line_count': self.line_count,
            'word_count': self.word_count,
            'language': self.language,
            'permissions': self.permissions,
            'owner': self.owner,
            'group': self.group,
            'tags': self.tags,
            'notes': self.notes,
            'importance_score': self.importance_score
        }


@dataclass
class DuplicateGroup:
    """Group of duplicate files"""
    group_id: str
    duplicate_type: DuplicateType
    files: List[Path]
    similarity_score: float
    total_size: int
    potential_savings: int
    recommended_action: str

    def get_primary_file(self) -> Path:
        """Get the primary file (usually the oldest or in preferred location)"""
        if not self.files:
            raise ValueError("No files in duplicate group")

        # Prefer files not in temp directories
        non_temp_files = [f for f in self.files if 'temp' not in str(f).lower()]
        if non_temp_files:
            # Return oldest non-temp file
            return min(non_temp_files, key=lambda f: f.stat().st_mtime)

        # Return oldest file overall
        return min(self.files, key=lambda f: f.stat().st_mtime)


@dataclass
class FileRelationship:
    """Relationship between files"""
    source_file: Path
    target_file: Path
    relationship_type: str  # "depends_on", "includes", "references", "similar_to"
    strength: float  # 0.0 to 1.0
    description: str
    discovered_by: str  # Method that discovered the relationship


@dataclass
class DirectoryAnalysis:
    """Analysis of a directory structure"""
    path: Path
    total_files: int
    total_size: int
    file_categories: Dict[FileCategory, int]
    duplicate_groups: List[DuplicateGroup]
    large_files: List[Tuple[Path, int]]  # Files over threshold
    old_files: List[Tuple[Path, datetime]]  # Files older than threshold
    empty_files: List[Path]
    temporary_files: List[Path]
    organization_score: float  # 0.0 to 1.0
    suggestions: List[str]


class FileHasher:
    """Efficient file hashing utilities"""

    def __init__(self, chunk_size: int = 8192):
        self.chunk_size = chunk_size
        self.logger = Logger()

    async def calculate_hashes(self, file_path: Path) -> Dict[str, str]:
        """Calculate multiple hashes for a file"""
        try:
            if not file_path.exists() or not file_path.is_file():
                return {}

            # Use thread pool for I/O intensive operations
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._calculate_hashes_sync, file_path)

        except Exception as e:
            self.logger.error(f"Error calculating hashes for {file_path}: {e}")
            return {}

    def _calculate_hashes_sync(self, file_path: Path) -> Dict[str, str]:
        """Synchronous hash calculation"""
        hashes = {
            'md5': hashlib.md5(),
            'sha256': hashlib.sha256()
        }

        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(self.chunk_size):
                    for hasher in hashes.values():
                        hasher.update(chunk)

            return {name: hasher.hexdigest() for name, hasher in hashes.items()}

        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return {}

    async def calculate_fuzzy_hash(self, file_path: Path) -> Optional[str]:
        """Calculate fuzzy hash for similarity detection"""
        try:
            # Simple content-based fuzzy hash
            # In practice, you might use ssdeep or similar
            content = await self._read_file_sample(file_path)
            if not content:
                return None

            # Create a simple fuzzy hash based on content patterns
            words = content.lower().split()[:100]  # First 100 words
            word_hash = hashlib.md5(' '.join(sorted(set(words))).encode()).hexdigest()

            return word_hash[:16]  # Shorter hash for fuzzy matching

        except Exception as e:
            self.logger.error(f"Error calculating fuzzy hash for {file_path}: {e}")
            return None

    async def _read_file_sample(self, file_path: Path, max_size: int = 10240) -> str:
        """Read a sample of file content for analysis"""
        try:
            if file_path.stat().st_size > max_size:
                # Read from beginning and end for large files
                with open(file_path, 'rb') as f:
                    start_content = f.read(max_size // 2)
                    f.seek(-max_size // 2, 2)
                    end_content = f.read(max_size // 2)
                    content = start_content + b'\n...\n' + end_content
            else:
                content = file_path.read_bytes()

            # Try to decode as text
            try:
                return content.decode('utf-8', errors='ignore')
            except:
                return content.decode('latin-1', errors='ignore')

        except Exception:
            return ""


class MetadataExtractor:
    """Extract comprehensive metadata from files"""

    def __init__(self):
        self.logger = Logger()
        self.hasher = FileHasher()

    async def extract_metadata(self, file_path: Path) -> FileMetadata:
        """Extract comprehensive metadata from a file"""
        try:
            if not file_path.exists():
                raise AnalysisError(f"File does not exist: {file_path}")

            stat = file_path.stat()

            # Basic metadata
            metadata = FileMetadata(
                path=file_path,
                name=file_path.name,
                size=stat.st_size,
                created=datetime.fromtimestamp(stat.st_ctime),
                modified=datetime.fromtimestamp(stat.st_mtime),
                accessed=datetime.fromtimestamp(stat.st_atime),
                extension=file_path.suffix.lower(),
                mime_type=mimetypes.guess_type(str(file_path))[0],
                category=self._categorize_file(file_path)
            )

            # Calculate hashes
            hashes = await self.hasher.calculate_hashes(file_path)
            metadata.md5_hash = hashes.get('md5')
            metadata.sha256_hash = hashes.get('sha256')
            metadata.content_hash = await self.hasher.calculate_fuzzy_hash(file_path)

            # Content analysis for text files
            if self._is_text_file(file_path):
                await self._analyze_text_content(file_path, metadata)

            # Permissions (Unix-like systems)
            if hasattr(stat, 'st_mode'):
                metadata.permissions = oct(stat.st_mode)[-3:]

            # Owner information (Unix-like systems)
            try:
                import pwd
                import grp
                metadata.owner = pwd.getpwuid(stat.st_uid).pw_name
                metadata.group = grp.getgrgid(stat.st_gid).gr_name
            except (ImportError, KeyError):
                pass

            return metadata

        except Exception as e:
            self.logger.error(f"Error extracting metadata from {file_path}: {e}")
            raise AnalysisError(f"Metadata extraction failed: {e}")

    def _categorize_file(self, file_path: Path) -> FileCategory:
        """Categorize file based on extension and content"""
        extension = file_path.suffix.lower()

        # Document files
        if extension in ['.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt', '.md', '.rst']:
            return FileCategory.DOCUMENT

        # Image files
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff']:
            return FileCategory.IMAGE

        # Video files
        if extension in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']:
            return FileCategory.VIDEO

        # Audio files
        if extension in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a']:
            return FileCategory.AUDIO

        # Code files
        if extension in ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.php', '.rb', '.go', '.rs', '.ts']:
            return FileCategory.CODE

        # Archive files
        if extension in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz']:
            return FileCategory.ARCHIVE

        # Data files
        if extension in ['.json', '.xml', '.csv', '.sql', '.db', '.sqlite']:
            return FileCategory.DATA

        # Executable files
        if extension in ['.exe', '.msi', '.deb', '.rpm', '.dmg', '.app']:
            return FileCategory.EXECUTABLE

        # System files
        if extension in ['.sys', '.dll', '.so', '.dylib', '.ini', '.cfg', '.conf']:
            return FileCategory.SYSTEM

        # Temporary files
        if extension in ['.tmp', '.temp', '.bak', '.swp', '.~'] or file_path.name.startswith('.'):
            return FileCategory.TEMPORARY

        return FileCategory.UNKNOWN

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is likely a text file"""
        if file_path.stat().st_size > 10 * 1024 * 1024:  # Skip files > 10MB
            return False

        # Check by extension first
        text_extensions = {'.txt', '.md', '.rst', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.log'}
        if file_path.suffix.lower() in text_extensions:
            return True

        # Check MIME type
        mime_type = mimetypes.guess_type(str(file_path))[0]
        if mime_type and mime_type.startswith('text/'):
            return True

        # Check content (sample first few bytes)
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(1024)
                # Check if sample is mostly printable ASCII
                printable_ratio = sum(1 for b in sample if 32 <= b <= 126 or b in [9, 10, 13]) / len(sample)
                return printable_ratio > 0.7
        except:
            return False

    async def _analyze_text_content(self, file_path: Path, metadata: FileMetadata):
        """Analyze text file content"""
        try:
            # Read file content
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Basic text statistics
            lines = content.split('\n')
            metadata.line_count = len(lines)
            metadata.word_count = len(content.split())

            # Detect encoding
            try:
                import chardet
                with open(file_path, 'rb') as f:
                    raw_data = f.read(10240)  # Read first 10KB
                    result = chardet.detect(raw_data)
                    metadata.encoding = result.get('encoding')
            except ImportError:
                metadata.encoding = 'utf-8'  # Default assumption

            # Detect programming language
            metadata.language = self._detect_language(file_path, content)

        except Exception as e:
            self.logger.error(f"Error analyzing text content of {file_path}: {e}")

    def _detect_language(self, file_path: Path, content: str) -> Optional[str]:
        """Detect programming language or natural language"""
        extension = file_path.suffix.lower()

        # Programming language by extension
        lang_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++ Header',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.html': 'HTML',
            '.css': 'CSS',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.ps1': 'PowerShell'
        }

        if extension in lang_map:
            return lang_map[extension]

        # Try to detect by content patterns
        content_lower = content.lower()

        if 'def ' in content and 'import ' in content:
            return 'Python'
        elif 'function ' in content and ('var ' in content or 'let ' in content):
            return 'JavaScript'
        elif 'public class ' in content and 'import java' in content:
            return 'Java'
        elif '#include' in content and ('int main' in content or 'void main' in content):
            return 'C/C++'

        return None


class DuplicateDetector:
    """Detect duplicate and similar files"""

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.logger = Logger()

    async def find_duplicates(self, file_paths: List[Path]) -> List[DuplicateGroup]:
        """Find duplicate files in the given list"""
        try:
            # Extract metadata for all files
            metadata_list = []
            for file_path in file_paths:
                try:
                    extractor = MetadataExtractor()
                    metadata = await extractor.extract_metadata(file_path)
                    metadata_list.append(metadata)
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")

            duplicate_groups = []

            # Find exact duplicates (same hash)
            exact_groups = self._find_exact_duplicates(metadata_list)
            duplicate_groups.extend(exact_groups)

            # Find similar files (fuzzy hash similarity)
            similar_groups = self._find_similar_files(metadata_list)
            duplicate_groups.extend(similar_groups)

            # Find files with similar names
            name_groups = self._find_similar_names(metadata_list)
            duplicate_groups.extend(name_groups)

            # Find files with same size but different content
            size_groups = self._find_same_size_files(metadata_list)
            duplicate_groups.extend(size_groups)

            return duplicate_groups

        except Exception as e:
            self.logger.error(f"Error finding duplicates: {e}")
            return []

    def _find_exact_duplicates(self, metadata_list: List[FileMetadata]) -> List[DuplicateGroup]:
        """Find files with identical content (same hash)"""
        hash_groups = {}

        for metadata in metadata_list:
            if metadata.sha256_hash:
                if metadata.sha256_hash not in hash_groups:
                    hash_groups[metadata.sha256_hash] = []
                hash_groups[metadata.sha256_hash].append(metadata)

        duplicate_groups = []
        for hash_value, files in hash_groups.items():
            if len(files) > 1:
                file_paths = [f.path for f in files]
                total_size = sum(f.size for f in files)
                potential_savings = total_size - files[0].size  # Keep one copy

                group = DuplicateGroup(
                    group_id=f"exact_{hash_value[:8]}",
                    duplicate_type=DuplicateType.EXACT,
                    files=file_paths,
                    similarity_score=1.0,
                    total_size=total_size,
                    potential_savings=potential_savings,
                    recommended_action="Keep oldest file, delete others"
                )
                duplicate_groups.append(group)

        return duplicate_groups

    def _find_similar_files(self, metadata_list: List[FileMetadata]) -> List[DuplicateGroup]:
        """Find files with similar content using fuzzy hashes"""
        similar_groups = []
        processed = set()

        for i, metadata1 in enumerate(metadata_list):
            if i in processed or not metadata1.content_hash:
                continue

            similar_files = [metadata1]

            for j, metadata2 in enumerate(metadata_list[i+1:], i+1):
                if j in processed or not metadata2.content_hash:
                    continue

                # Calculate similarity based on fuzzy hash
                similarity = self._calculate_hash_similarity(
                    metadata1.content_hash, metadata2.content_hash
                )

                if similarity >= self.similarity_threshold:
                    similar_files.append(metadata2)
                    processed.add(j)

            if len(similar_files) > 1:
                file_paths = [f.path for f in similar_files]
                total_size = sum(f.size for f in similar_files)
                avg_similarity = 0.9  # Approximate

                group = DuplicateGroup(
                    group_id=f"similar_{metadata1.content_hash[:8]}",
                    duplicate_type=DuplicateType.SIMILAR,
                    files=file_paths,
                    similarity_score=avg_similarity,
                    total_size=total_size,
                    potential_savings=total_size - max(f.size for f in similar_files),
                    recommended_action="Review manually, keep best version"
                )
                similar_groups.append(group)
                processed.add(i)

        return similar_groups

    def _find_similar_names(self, metadata_list: List[FileMetadata]) -> List[DuplicateGroup]:
        """Find files with similar names"""
        name_groups = []
        processed = set()

        for i, metadata1 in enumerate(metadata_list):
            if i in processed:
                continue

            similar_files = [metadata1]

            for j, metadata2 in enumerate(metadata_list[i+1:], i+1):
                if j in processed:
                    continue

                # Calculate name similarity
                similarity = difflib.SequenceMatcher(
                    None, metadata1.name.lower(), metadata2.name.lower()
                ).ratio()

                if similarity >= 0.8:  # High name similarity threshold
                    similar_files.append(metadata2)
                    processed.add(j)

            if len(similar_files) > 1:
                file_paths = [f.path for f in similar_files]
                total_size = sum(f.size for f in similar_files)

                group = DuplicateGroup(
                    group_id=f"name_similar_{i}",
                    duplicate_type=DuplicateType.NAME_SIMILAR,
                    files=file_paths,
                    similarity_score=0.8,
                    total_size=total_size,
                    potential_savings=0,  # Names similar doesn't mean content duplicate
                    recommended_action="Check if files serve different purposes"
                )
                name_groups.append(group)
                processed.add(i)

        return name_groups

    def _find_same_size_files(self, metadata_list: List[FileMetadata]) -> List[DuplicateGroup]:
        """Find files with same size but potentially different content"""
        size_groups = {}

        for metadata in metadata_list:
            if metadata.size not in size_groups:
                size_groups[metadata.size] = []
            size_groups[metadata.size].append(metadata)

        duplicate_groups = []
        for size, files in size_groups.items():
            if len(files) > 1 and size > 0:  # Ignore empty files
                # Filter out files that are already exact duplicates
                unique_hashes = set()
                unique_files = []

                for file in files:
                    if file.sha256_hash not in unique_hashes:
                        unique_hashes.add(file.sha256_hash)
                        unique_files.append(file)

                if len(unique_files) > 1:  # Same size, different content
                    file_paths = [f.path for f in unique_files]

                    group = DuplicateGroup(
                        group_id=f"size_match_{size}",
                        duplicate_type=DuplicateType.SIZE_MATCH,
                        files=file_paths,
                        similarity_score=0.5,  # Same size but different content
                        total_size=size * len(unique_files),
                        potential_savings=0,  # No savings expected
                        recommended_action="Investigate why files have same size"
                    )
                    duplicate_groups.append(group)

        return duplicate_groups

    def _calculate_hash_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two fuzzy hashes"""
        if not hash1 or not hash2:
            return 0.0

        # Simple Hamming distance for short hashes
        if len(hash1) != len(hash2):
            return 0.0

        matches = sum(1 for a, b in zip(hash1, hash2) if a == b)
        return matches / len(hash1)


class RelationshipAnalyzer:
    """Analyze relationships between files"""

    def __init__(self, ai_assistant: Optional[AdvancedAIAssistant] = None):
        self.ai_assistant = ai_assistant
        self.logger = Logger()

    async def analyze_relationships(self, file_paths: List[Path]) -> List[FileRelationship]:
        """Analyze relationships between files"""
        relationships = []

        try:
            # Content-based relationships
            content_relationships = await self._find_content_relationships(file_paths)
            relationships.extend(content_relationships)

            # Name-based relationships
            name_relationships = self._find_name_relationships(file_paths)
            relationships.extend(name_relationships)

            # Directory-based relationships
            directory_relationships = self._find_directory_relationships(file_paths)
            relationships.extend(directory_relationships)

            # AI-powered relationship detection
            if self.ai_assistant:
                ai_relationships = await self._find_ai_relationships(file_paths)
                relationships.extend(ai_relationships)

            return relationships

        except Exception as e:
            self.logger.error(f"Error analyzing relationships: {e}")
            return []

    async def _find_content_relationships(self, file_paths: List[Path]) -> List[FileRelationship]:
        """Find relationships based on file content"""
        relationships = []

        # Look for import/include statements in code files
        for file_path in file_paths:
            if self._is_code_file(file_path):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    referenced_files = self._extract_file_references(content, file_path.parent)

                    for ref_file in referenced_files:
                        if ref_file in file_paths:
                            relationships.append(FileRelationship(
                                source_file=file_path,
                                target_file=ref_file,
                                relationship_type="depends_on",
                                strength=0.9,
                                description=f"{file_path.name} imports/includes {ref_file.name}",
                                discovered_by="content_analysis"
                            ))
                except Exception as e:
                    self.logger.error(f"Error analyzing content of {file_path}: {e}")

        return relationships

    def _find_name_relationships(self, file_paths: List[Path]) -> List[FileRelationship]:
        """Find relationships based on file names"""
        relationships = []

        for i, file1 in enumerate(file_paths):
            for file2 in file_paths[i+1:]:
                # Check for common naming patterns
                similarity = self._calculate_name_similarity(file1.name, file2.name)

                if similarity > 0.7:
                    relationships.append(FileRelationship(
                        source_file=file1,
                        target_file=file2,
                        relationship_type="similar_to",
                        strength=similarity,
                        description=f"Files have similar names: {file1.name} and {file2.name}",
                        discovered_by="name_analysis"
                    ))

        return relationships

    def _find_directory_relationships(self, file_paths: List[Path]) -> List[FileRelationship]:
        """Find relationships based on directory structure"""
        relationships = []

        # Group files by directory
        dir_groups = {}
        for file_path in file_paths:
            parent = file_path.parent
            if parent not in dir_groups:
                dir_groups[parent] = []
            dir_groups[parent].append(file_path)

        # Files in same directory are related
        for directory, files in dir_groups.items():
            if len(files) > 1:
                for i, file1 in enumerate(files):
                    for file2 in files[i+1:]:
                        relationships.append(FileRelationship(
                            source_file=file1,
                            target_file=file2,
                            relationship_type="same_directory",
                            strength=0.5,
                            description=f"Files are in the same directory: {directory}",
                            discovered_by="directory_analysis"
                        ))

        return relationships

    async def _find_ai_relationships(self, file_paths: List[Path]) -> List[FileRelationship]:
        """Use AI to find complex relationships"""
        relationships = []

        if not self.ai_assistant:
            return relationships

        try:
            # Analyze files in batches to avoid overwhelming the AI
            batch_size = 10
            for i in range(0, len(file_paths), batch_size):
                batch = file_paths[i:i+batch_size]

                for file_path in batch:
                    try:
                        # Use AI to analyze relationships
                        analysis_results = await self.ai_assistant.analyze_file_comprehensive(
                            file_path, [AnalysisType.RELATIONSHIP]
                        )

                        for result in analysis_results:
                            if result.analysis_type == AnalysisType.RELATIONSHIP:
                                ai_relationships = self._parse_ai_relationships(file_path, result)
                                relationships.extend(ai_relationships)

                    except Exception as e:
                        self.logger.error(f"AI relationship analysis failed for {file_path}: {e}")

        except Exception as e:
            self.logger.error(f"Error in AI relationship analysis: {e}")

        return relationships

    def _is_code_file(self, file_path: Path) -> bool:
        """Check if file is a code file"""
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.php', '.rb', '.go', '.rs'}
        return file_path.suffix.lower() in code_extensions

    def _extract_file_references(self, content: str, base_dir: Path) -> List[Path]:
        """Extract file references from code content"""
        references = []
        lines = content.split('\n')

        for line in lines:
            line = line.strip()

            # Python imports
            if line.startswith('import ') or line.startswith('from '):
                # Extract module name and try to find corresponding file
                pass  # Simplified for now

            # JavaScript/TypeScript imports
            elif 'import' in line and 'from' in line:
                # Extract file path from import statement
                pass  # Simplified for now

            # C/C++ includes
            elif line.startswith('#include'):
                # Extract header file name
                pass  # Simplified for now

        return references

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two file names"""
        return difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()

    def _parse_ai_relationships(self, file_path: Path, result: AnalysisResult) -> List[FileRelationship]:
        """Parse AI analysis results to extract relationships"""
        relationships = []

        try:
            results_data = result.results

            # Extract dependencies
            dependencies = results_data.get('dependencies', [])
            for dep in dependencies:
                if isinstance(dep, str):
                    dep_path = file_path.parent / dep
                    if dep_path.exists():
                        relationships.append(FileRelationship(
                            source_file=file_path,
                            target_file=dep_path,
                            relationship_type="depends_on",
                            strength=result.confidence,
                            description=f"AI detected dependency: {dep}",
                            discovered_by="ai_analysis"
                        ))

            # Extract related files
            related_patterns = results_data.get('related_patterns', [])
            for pattern in related_patterns:
                # This would need more sophisticated parsing
                pass

        except Exception as e:
            self.logger.error(f"Error parsing AI relationships: {e}")

        return relationships


class ComprehensiveFileAnalyzer:
    """Main class for comprehensive file analysis"""

    def __init__(self, config: Dict[str, Any], ai_assistant: Optional[AdvancedAIAssistant] = None):
        self.config = config
        self.ai_assistant = ai_assistant
        self.logger = Logger()

        self.metadata_extractor = MetadataExtractor()
        self.duplicate_detector = DuplicateDetector(
            similarity_threshold=config.get('similarity_threshold', 0.8)
        )
        self.relationship_analyzer = RelationshipAnalyzer(ai_assistant)

        # Database for caching analysis results
        self.db_path = Path(config.get('cache_db', 'file_analysis.db'))
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for caching"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS file_metadata (
                        path TEXT PRIMARY KEY,
                        metadata TEXT,
                        last_modified REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT,
                        analysis_type TEXT,
                        results TEXT,
                        confidence REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")

    async def analyze_directory(self, directory_path: Path,
                              recursive: bool = True,
                              include_ai_analysis: bool = True) -> DirectoryAnalysis:
        """Perform comprehensive analysis of a directory"""
        try:
            if not directory_path.exists() or not directory_path.is_dir():
                raise AnalysisError(f"Directory does not exist: {directory_path}")

            # Collect all files
            file_paths = []
            if recursive:
                file_paths = list(directory_path.rglob('*'))
            else:
                file_paths = list(directory_path.iterdir())

            # Filter to only files
            file_paths = [p for p in file_paths if p.is_file()]

            self.logger.info(f"Analyzing {len(file_paths)} files in {directory_path}")

            # Extract metadata for all files
            metadata_list = []
            for file_path in file_paths:
                try:
                    metadata = await self._get_cached_metadata(file_path)
                    if metadata:
                        metadata_list.append(metadata)
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")

            # Calculate statistics
            total_files = len(metadata_list)
            total_size = sum(m.size for m in metadata_list)

            # Categorize files
            file_categories = {}
            for category in FileCategory:
                file_categories[category] = sum(1 for m in metadata_list if m.category == category)

            # Find duplicates
            duplicate_groups = await self.duplicate_detector.find_duplicates(file_paths)

            # Identify large files (top 10% by size)
            sorted_by_size = sorted(metadata_list, key=lambda m: m.size, reverse=True)
            large_files_count = max(1, len(sorted_by_size) // 10)
            large_files = [(m.path, m.size) for m in sorted_by_size[:large_files_count]]

            # Identify old files (older than 1 year)
            one_year_ago = datetime.now() - timedelta(days=365)
            old_files = [(m.path, m.modified) for m in metadata_list if m.modified < one_year_ago]

            # Identify empty files
            empty_files = [m.path for m in metadata_list if m.size == 0]

            # Identify temporary files
            temporary_files = [m.path for m in metadata_list if m.category == FileCategory.TEMPORARY]

            # Calculate organization score
            organization_score = self._calculate_organization_score(metadata_list, duplicate_groups)

            # Generate suggestions
            suggestions = self._generate_suggestions(
                metadata_list, duplicate_groups, large_files, old_files, empty_files, temporary_files
            )

            return DirectoryAnalysis(
                path=directory_path,
                total_files=total_files,
                total_size=total_size,
                file_categories=file_categories,
                duplicate_groups=duplicate_groups,
                large_files=large_files,
                old_files=old_files,
                empty_files=empty_files,
                temporary_files=temporary_files,
                organization_score=organization_score,
                suggestions=suggestions
            )

        except Exception as e:
            self.logger.error(f"Error analyzing directory {directory_path}: {e}")
            raise AnalysisError(f"Directory analysis failed: {e}")

    async def _get_cached_metadata(self, file_path: Path) -> Optional[FileMetadata]:
        """Get metadata from cache or extract if not cached"""
        try:
            # Check cache first
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT metadata, last_modified FROM file_metadata WHERE path = ?',
                    (str(file_path),)
                )
                row = cursor.fetchone()

                if row:
                    cached_metadata, cached_mtime = row
                    current_mtime = file_path.stat().st_mtime

                    # Use cached data if file hasn't been modified
                    if abs(current_mtime - cached_mtime) < 1.0:  # 1 second tolerance
                        metadata_dict = json.loads(cached_metadata)
                        # Convert back to FileMetadata object
                        return self._dict_to_metadata(metadata_dict)

            # Extract fresh metadata
            metadata = await self.metadata_extractor.extract_metadata(file_path)

            # Cache the result
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    'INSERT OR REPLACE INTO file_metadata (path, metadata, last_modified) VALUES (?, ?, ?)',
                    (str(file_path), json.dumps(metadata.to_dict()), file_path.stat().st_mtime)
                )
                conn.commit()

            return metadata

        except Exception as e:
            self.logger.error(f"Error getting metadata for {file_path}: {e}")
            return None

    def _dict_to_metadata(self, metadata_dict: Dict[str, Any]) -> FileMetadata:
        """Convert dictionary back to FileMetadata object"""
        return FileMetadata(
            path=Path(metadata_dict['path']),
            name=metadata_dict['name'],
            size=metadata_dict['size'],
            created=datetime.fromisoformat(metadata_dict['created']),
            modified=datetime.fromisoformat(metadata_dict['modified']),
            accessed=datetime.fromisoformat(metadata_dict['accessed']),
            extension=metadata_dict['extension'],
            mime_type=metadata_dict['mime_type'],
            category=FileCategory(metadata_dict['category']),
            md5_hash=metadata_dict.get('md5_hash'),
            sha256_hash=metadata_dict.get('sha256_hash'),
            content_hash=metadata_dict.get('content_hash'),
            encoding=metadata_dict.get('encoding'),
            line_count=metadata_dict.get('line_count'),
            word_count=metadata_dict.get('word_count'),
            language=metadata_dict.get('language'),
            permissions=metadata_dict.get('permissions'),
            owner=metadata_dict.get('owner'),
            group=metadata_dict.get('group'),
            tags=metadata_dict.get('tags', []),
            notes=metadata_dict.get('notes', ''),
            importance_score=metadata_dict.get('importance_score', 0.0)
        )

    def _calculate_organization_score(self, metadata_list: List[FileMetadata],
                                    duplicate_groups: List[DuplicateGroup]) -> float:
        """Calculate organization score (0.0 to 1.0)"""
        if not metadata_list:
            return 1.0

        score = 1.0

        # Penalize for duplicates
        duplicate_penalty = len(duplicate_groups) * 0.1
        score -= min(duplicate_penalty, 0.3)

        # Penalize for too many temporary files
        temp_files = sum(1 for m in metadata_list if m.category == FileCategory.TEMPORARY)
        temp_ratio = temp_files / len(metadata_list)
        score -= temp_ratio * 0.2

        # Penalize for too many unknown file types
        unknown_files = sum(1 for m in metadata_list if m.category == FileCategory.UNKNOWN)
        unknown_ratio = unknown_files / len(metadata_list)
        score -= unknown_ratio * 0.1

        # Bonus for good categorization
        categories_used = len(set(m.category for m in metadata_list))
        if categories_used > 3:  # Good variety of file types
            score += 0.1

        return max(0.0, min(1.0, score))

    def _generate_suggestions(self, metadata_list: List[FileMetadata],
                            duplicate_groups: List[DuplicateGroup],
                            large_files: List[Tuple[Path, int]],
                            old_files: List[Tuple[Path, datetime]],
                            empty_files: List[Path],
                            temporary_files: List[Path]) -> List[str]:
        """Generate organization and cleanup suggestions"""
        suggestions = []

        # Duplicate file suggestions
        if duplicate_groups:
            exact_duplicates = [g for g in duplicate_groups if g.duplicate_type == DuplicateType.EXACT]
            if exact_duplicates:
                total_savings = sum(g.potential_savings for g in exact_duplicates)
                suggestions.append(f"Remove {len(exact_duplicates)} groups of exact duplicates to save {total_savings:,} bytes")

        # Large file suggestions
        if large_files:
            suggestions.append(f"Review {len(large_files)} large files for archival or compression")

        # Old file suggestions
        if old_files:
            suggestions.append(f"Consider archiving {len(old_files)} old files (>1 year)")

        # Empty file suggestions
        if empty_files:
            suggestions.append(f"Remove {len(empty_files)} empty files")

        # Temporary file suggestions
        if temporary_files:
            suggestions.append(f"Clean up {len(temporary_files)} temporary files")

        # Category-based suggestions
        categories = {}
        for metadata in metadata_list:
            if metadata.category not in categories:
                categories[metadata.category] = 0
            categories[metadata.category] += 1

        if categories.get(FileCategory.UNKNOWN, 0) > len(metadata_list) * 0.2:
            suggestions.append("Many files have unknown types - consider adding file extensions")

        if not suggestions:
            suggestions.append("Directory is well organized!")

        return suggestions

    async def analyze_file_relationships(self, directory_path: Path) -> List[FileRelationship]:
        """Analyze relationships between files in a directory"""
        try:
            file_paths = [p for p in directory_path.rglob('*') if p.is_file()]
            return await self.relationship_analyzer.analyze_relationships(file_paths)
        except Exception as e:
            self.logger.error(f"Error analyzing file relationships: {e}")
            return []

    async def get_file_insights(self, file_path: Path) -> Dict[str, Any]:
        """Get comprehensive insights for a single file"""
        try:
            metadata = await self.metadata_extractor.extract_metadata(file_path)

            insights = {
                'metadata': metadata.to_dict(),
                'category': metadata.category.value,
                'size_human': self._format_size(metadata.size),
                'age_days': (datetime.now() - metadata.modified).days,
                'suggestions': []
            }

            # Add AI analysis if available
            if self.ai_assistant:
                try:
                    ai_results = await self.ai_assistant.analyze_file_comprehensive(
                        file_path, [AnalysisType.CONTENT, AnalysisType.SECURITY, AnalysisType.ORGANIZATION]
                    )
                    insights['ai_analysis'] = [result.results for result in ai_results]
                except Exception as e:
                    self.logger.error(f"AI analysis failed for {file_path}: {e}")

            return insights

        except Exception as e:
            self.logger.error(f"Error getting insights for {file_path}: {e}")
            return {}

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"