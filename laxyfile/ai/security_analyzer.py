"""
Security and Performance Analysis System

This module provides comprehensive security auditing, threat detection,
performance analysis, and optimization recommendations for LaxyFile.
"""

import asyncio
import hashlib
import re
import os
import psutil
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import mimetypes
import subprocess

from ..core.types import OperationResult
from ..core.exceptions import SecurityError, PerformanceError
from ..utils.logger import Logger
from .file_analyzer import FileMetadata, ComprehensiveFileAnalyzer
from .advanced_assistant import AdvancedAIAssistant, AnalysisType


class SecurityRiskLevel(Enum):
    """Security risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of security threats"""
    MALWARE = "malware"
    SUSPICIOUS_EXTENSION = "suspicious_extension"
    EXECUTABLE_IN_TEMP = "executable_in_temp"
    HIDDEN_FILE = "hidden_file"
    LARGE_EXECUTABLE = "large_executable"
    SCRIPT_INJECTION = "script_injection"
    DATA_EXPOSURE = "data_exposure"
    PERMISSION_ISSUE = "permission_issue"
    OUTDATED_SOFTWARE = "outdated_software"
    WEAK_ENCRYPTION = "weak_encryption"


class PerformanceIssueType(Enum):
    """Types of performance issues"""
    LARGE_FILE = "large_file"
    DUPLICATE_FILE = "duplicate_file"
    FRAGMENTED_STORAGE = "fragmented_storage"
    INEFFICIENT_FORMAT = "inefficient_format"
    EXCESSIVE_NESTING = "excessive_nesting"
    SLOW_ACCESS_PATTERN = "slow_access_pattern"
    MEMORY_INTENSIVE = "memory_intensive"
    DISK_SPACE_WASTE = "disk_space_waste"


@dataclass
class SecurityThreat:
    """Represents a security threat"""
    threat_id: str
    file_path: Path
    threat_type: ThreatType
    risk_level: SecurityRiskLevel
    description: str
    evidence: List[str]
    recommendations: List[str]
    confidence: float
    detected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'threat_id': self.threat_id,
            'file_path': str(self.file_path),
            'threat_type': self.threat_type.value,
            'risk_level': self.risk_level.value,
            'description': self.description,
            'evidence': self.evidence,
            'recommendations': self.recommendations,
            'confidence': self.confidence,
            'detected_at': self.detected_at.isoformat()
        }


@dataclass
class PerformanceIssue:
    """Represents a performance issue"""
    issue_id: str
    file_path: Optional[Path]
    issue_type: PerformanceIssueType
    severity: str  # "low", "medium", "high"
    description: str
    impact: str
    recommendations: List[str]
    potential_savings: Dict[str, Any]  # space, time, etc.
    detected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'issue_id': self.issue_id,
            'file_path': str(self.file_path) if self.file_path else None,
            'issue_type': self.issue_type.value,
            'severity': self.severity,
            'description': self.description,
       'impact': self.impact,
            'recommendations': self.recommendations,
            'potential_savings': self.potential_savings,
            'detected_at': self.detected_at.isoformat()
        }


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: Dict[str, float]  # path -> usage percentage
    disk_io: Dict[str, Any]
    network_io: Dict[str, Any]
    process_count: int
    uptime: float
    timestamp: datetime = field(default_factory=datetime.now)


class MalwareDetector:
    """Detect potential malware and suspicious files"""

    def __init__(self):
        self.logger = Logger()

        # Known malicious file signatures (simplified)
        self.malicious_signatures = {
            # Example signatures - in practice, use proper antivirus databases
            'eicar_test': b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*',
        }

        # Suspicious file extensions
        self.suspicious_extensions = {
            '.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.vbs', '.js', '.jar',
            '.app', '.deb', '.rpm', '.msi', '.dmg', '.pkg'
        }

        # Suspicious file patterns
        self.suspicious_patterns = [
            r'eval\s*\(',  # JavaScript eval
            r'exec\s*\(',  # Python exec
            r'system\s*\(',  # System calls
            r'shell_exec\s*\(',  # PHP shell execution
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'data:.*base64',  # Base64 data URLs
        ]

    async def scan_file(self, file_path: Path) -> List[SecurityThreat]:
        """Scan a single file for security threats"""
        threats = []

        try:
            if not file_path.exists() or not file_path.is_file():
                return threats

            # Check file extension
            if file_path.suffix.lower() in self.suspicious_extensions:
                threats.append(SecurityThreat(
                    threat_id=f"suspicious_ext_{int(time.time())}",
                    file_path=file_path,
                    threat_type=ThreatType.SUSPICIOUS_EXTENSION,
                    risk_level=SecurityRiskLevel.MEDIUM,
                    description=f"File has suspicious extension: {file_path.suffix}",
                    evidence=[f"Extension: {file_path.suffix}"],
                    recommendations=["Verify file source", "Scan with antivirus"],
                    confidence=0.7
                ))

            # Check if executable in temp directory
            if self._is_executable(file_path) and self._is_in_temp_directory(file_path):
                threats.append(SecurityThreat(
                    threat_id=f"exec_in_temp_{int(time.time())}",
                    file_path=file_path,
                    threat_type=ThreatType.EXECUTABLE_IN_TEMP,
                    risk_level=SecurityRiskLevel.HIGH,
                    description="Executable file found in temporary directory",
                    evidence=[f"Location: {file_path.parent}"],
                    recommendations=["Remove file", "Check for malware"],
                    confidence=0.8
                ))

            # Check for hidden files with suspicious characteristics
            if file_path.name.startswith('.') and file_path.suffix.lower() in self.suspicious_extensions:
                threats.append(SecurityThreat(
                    threat_id=f"hidden_suspicious_{int(time.time())}",
                    file_path=file_path,
                    threat_type=ThreatType.HIDDEN_FILE,
                    risk_level=SecurityRiskLevel.MEDIUM,
                    description="Hidden file with suspicious extension",
                    evidence=[f"Hidden file: {file_path.name}"],
                    recommendations=["Investigate file purpose", "Consider removal"],
                    confidence=0.6
                ))

            # Check file size for executables
            if self._is_executable(file_path):
                file_size = file_path.stat().st_size
                if file_size > 100 * 1024 * 1024:  # > 100MB
                    threats.append(SecurityThreat(
                        threat_id=f"large_exec_{int(time.time())}",
                        file_path=file_path,
                        threat_type=ThreatType.LARGE_EXECUTABLE,
                        risk_level=SecurityRiskLevel.MEDIUM,
                        description=f"Unusually large executable file ({file_size:,} bytes)",
                        evidence=[f"Size: {file_size:,} bytes"],
                        recommendations=["Verify file legitimacy", "Check with antivirus"],
                        confidence=0.5
                    ))

            # Scan file content for suspicious patterns
            content_threats = await self._scan_file_content(file_path)
            threats.extend(content_threats)

            # Check file signatures
            signature_threats = await self._check_file_signatures(file_path)
            threats.extend(signature_threats)

        except Exception as e:
            self.logger.error(f"Error scanning file {file_path}: {e}")

        return threats

    def _is_executable(self, file_path: Path) -> bool:
        """Check if file is executable"""
        executable_extensions = {'.exe', '.app', '.deb', '.rpm', '.msi', '.dmg'}
        return (file_path.suffix.lower() in executable_extensions or
                os.access(file_path, os.X_OK))

    def _is_in_temp_directory(self, file_path: Path) -> bool:
        """Check if file is in a temporary directory"""
        temp_indicators = ['temp', 'tmp', 'cache', 'downloads']
        path_str = str(file_path).lower()
        return any(indicator in path_str for indicator in temp_indicators)

    async def _scan_file_content(self, file_path: Path) -> List[SecurityThreat]:
        """Scan file content for suspicious patterns"""
        threats = []

        try:
            # Only scan text files and small files
            if file_path.stat().st_size > 10 * 1024 * 1024:  # Skip files > 10MB
                return threats

            # Try to read as text
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except:
                # Try binary read for pattern matching
                content = file_path.read_bytes().decode('latin-1', errors='ignore')

            # Check for suspicious patterns
            for pattern in self.suspicious_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                if matches:
                    threats.append(SecurityThreat(
                        threat_id=f"script_injection_{int(time.time())}",
                        file_path=file_path,
                        threat_type=ThreatType.SCRIPT_INJECTION,
                        risk_level=SecurityRiskLevel.HIGH,
                        description=f"Suspicious code pattern detected: {pattern}",
                        evidence=[f"Pattern: {pattern}", f"Matches: {len(matches)}"],
                        recommendations=["Review code manually", "Isolate file"],
                        confidence=0.8
                    ))

            # Check for potential data exposure
            data_patterns = [
                r'password\s*[=:]\s*["\']?[\w@#$%^&*]+["\']?',
                r'api[_-]?key\s*[=:]\s*["\']?[\w-]+["\']?',
                r'secret\s*[=:]\s*["\']?[\w-]+["\']?',
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card pattern
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
            ]

            for pattern in data_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    threats.append(SecurityThreat(
                        threat_id=f"data_exposure_{int(time.time())}",
                        file_path=file_path,
                        threat_type=ThreatType.DATA_EXPOSURE,
                        risk_level=SecurityRiskLevel.HIGH,
                        description="File may contain sensitive data",
                        evidence=[f"Pattern detected: {pattern}"],
                        recommendations=["Encrypt file", "Remove sensitive data", "Restrict access"],
                        confidence=0.7
                    ))
                    break  # Only report once per file

        except Exception as e:
            self.logger.error(f"Error scanning content of {file_path}: {e}")

        return threats

    async def _check_file_signatures(self, file_path: Path) -> List[SecurityThreat]:
        """Check file against known malicious signatures"""
        threats = []

        try:
            # Read first few KB for signature matching
            with open(file_path, 'rb') as f:
                header = f.read(8192)

            for sig_name, signature in self.malicious_signatures.items():
                if signature in header:
                    threats.append(SecurityThreat(
                        threat_id=f"malware_{sig_name}_{int(time.time())}",
                        file_path=file_path,
                        threat_type=ThreatType.MALWARE,
                        risk_level=SecurityRiskLevel.CRITICAL,
                        description=f"Known malicious signature detected: {sig_name}",
                        evidence=[f"Signature: {sig_name}"],
                        recommendations=["Quarantine file immediately", "Run full system scan"],
                        confidence=0.95
                    ))

        except Exception as e:
            self.logger.error(f"Error checking signatures for {file_path}: {e}")

        return threats


class PermissionAnalyzer:
    """Analyze file and directory permissions for security issues"""

    def __init__(self):
        self.logger = Logger()

    async def analyze_permissions(self, file_path: Path) -> List[SecurityThreat]:
        """Analyze file permissions for security issues"""
        threats = []

        try:
            if not file_path.exists():
                return threats

            stat = file_path.stat()
            mode = stat.st_mode

            # Check for world-writable files
            if mode & 0o002:  # World writable
                threats.append(SecurityThreat(
                    threat_id=f"world_writable_{int(time.time())}",
                    file_path=file_path,
                    threat_type=ThreatType.PERMISSION_ISSUE,
                    risk_level=SecurityRiskLevel.HIGH,
                    description="File is world-writable",
                    evidence=[f"Permissions: {oct(mode)[-3:]}"],
                    recommendations=["Remove world write permission", "Review file ownership"],
                    confidence=0.9
                ))

            # Check for executable files with broad permissions
            if (mode & 0o111) and (mode & 0o022):  # Executable and group/world writable
                threats.append(SecurityThreat(
                    threat_id=f"exec_writable_{int(time.time())}",
                    file_path=file_path,
                    threat_type=ThreatType.PERMISSION_ISSUE,
                    risk_level=SecurityRiskLevel.HIGH,
                    description="Executable file with broad write permissions",
                    evidence=[f"Permissions: {oct(mode)[-3:]}"],
                    recommendations=["Restrict write permissions", "Verify file integrity"],
                    confidence=0.8
                ))

            # Check for setuid/setgid files
            if mode & 0o4000:  # Setuid
                threats.append(SecurityThreat(
                    threat_id=f"setuid_{int(time.time())}",
                    file_path=file_path,
                    threat_type=ThreatType.PERMISSION_ISSUE,
                    risk_level=SecurityRiskLevel.MEDIUM,
                    description="File has setuid bit set",
                    evidence=[f"Permissions: {oct(mode)[-4:]}"],
                    recommendations=["Verify setuid necessity", "Monitor file usage"],
                    confidence=0.7
                ))

            if mode & 0o2000:  # Setgid
                threats.append(SecurityThreat(
                    threat_id=f"setgid_{int(time.time())}",
                    file_path=file_path,
                    threat_type=ThreatType.PERMISSION_ISSUE,
                    risk_level=SecurityRiskLevel.MEDIUM,
                    description="File has setgid bit set",
                    evidence=[f"Permissions: {oct(mode)[-4:]}"],
                    recommendations=["Verify setgid necessity", "Monitor file usage"],
                    confidence=0.7
                ))

        except Exception as e:
            self.logger.error(f"Error analyzing permissions for {file_path}: {e}")

        return threats


class PerformanceAnalyzer:
    """Analyze system and file performance issues"""

    def __init__(self):
        self.logger = Logger()

    async def analyze_file_performance(self, file_path: Path, metadata: FileMetadata) -> List[PerformanceIssue]:
        """Analyze performance issues for a single file"""
        issues = []

        try:
            # Check for large files
            if metadata.size > 1024 * 1024 * 1024:  # > 1GB
                issues.append(PerformanceIssue(
                    issue_id=f"large_file_{int(time.time())}",
                    file_path=file_path,
                    issue_type=PerformanceIssueType.LARGE_FILE,
                    severity="high",
                    description=f"Very large file ({metadata.size:,} bytes)",
                    impact="Slow file operations, high memory usage",
                    recommendations=["Consider compression", "Split into smaller files", "Move to archive storage"],
                    potential_savings={"space": metadata.size * 0.3, "time": "50% faster operations"}
                ))

            # Check for inefficient formats
            format_issues = self._check_format_efficiency(file_path, metadata)
            issues.extend(format_issues)

            # Check access patterns
            access_issues = await self._analyze_access_patterns(file_path, metadata)
            issues.extend(access_issues)

        except Exception as e:
            self.logger.error(f"Error analyzing file performance for {file_path}: {e}")

        return issues

    def _check_format_efficiency(self, file_path: Path, metadata: FileMetadata) -> List[PerformanceIssue]:
        """Check if file format is efficient for its use case"""
        issues = []

        try:
            # Check for uncompressed images
            if metadata.extension.lower() in ['.bmp', '.tiff'] and metadata.size > 10 * 1024 * 1024:
                issues.append(PerformanceIssue(
                    issue_id=f"inefficient_image_{int(time.time())}",
                    file_path=file_path,
                    issue_type=PerformanceIssueType.INEFFICIENT_FORMAT,
                    severity="medium",
                    description="Large uncompressed image file",
                    impact="Excessive disk space usage, slow loading",
                    recommendations=["Convert to JPEG or PNG", "Use image compression"],
                    potential_savings={"space": metadata.size * 0.7}
                ))

            # Check for uncompressed audio
            if metadata.extension.lower() in ['.wav', '.aiff'] and metadata.size > 50 * 1024 * 1024:
                issues.append(PerformanceIssue(
                    issue_id=f"inefficient_audio_{int(time.time())}",
                    file_path=file_path,
                    issue_type=PerformanceIssueType.INEFFICIENT_FORMAT,
                    severity="medium",
                    description="Large uncompressed audio file",
                    impact="Excessive disk space usage",
                    recommendations=["Convert to MP3 or AAC", "Use audio compression"],
                    potential_savings={"space": metadata.size * 0.8}
                ))

        except Exception as e:
            self.logger.error(f"Error checking format efficiency: {e}")

        return issues

    async def _analyze_access_patterns(self, file_path: Path, metadata: FileMetadata) -> List[PerformanceIssue]:
        """Analyze file access patterns for performance issues"""
        issues = []

        try:
            # Check if file hasn't been accessed in a long time
            days_since_access = (datetime.now() - metadata.accessed).days

            if days_since_access > 365 and metadata.size > 100 * 1024 * 1024:  # > 100MB
                issues.append(PerformanceIssue(
                    issue_id=f"cold_storage_{int(time.time())}",
                    file_path=file_path,
                    issue_type=PerformanceIssueType.SLOW_ACCESS_PATTERN,
                    severity="low",
                    description=f"Large file not accessed for {days_since_access} days",
                    impact="Occupying fast storage unnecessarily",
                    recommendations=["Move to archive storage", "Consider compression"],
                    potential_savings={"space": "Free up fast storage"}
                ))

        except Exception as e:
            self.logger.error(f"Error analyzing access patterns: {e}")

        return issues

    async def analyze_system_performance(self) -> Tuple[SystemMetrics, List[PerformanceIssue]]:
        """Analyze overall system performance"""
        issues = []

        try:
            # Collect system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk_usage = {}

            # Get disk usage for all mounted drives
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = (usage.used / usage.total) * 100
                except:
                    continue

            disk_io = psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
            net_io = psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}

            metrics = SystemMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk_usage,
                disk_io=disk_io,
                network_io=net_io,
                process_count=len(psutil.pids()),
                uptime=time.time() - psutil.boot_time()
            )

            # Analyze for issues
            if cpu_percent > 80:
                issues.append(PerformanceIssue(
                    issue_id=f"high_cpu_{int(time.time())}",
                    file_path=None,
                    issue_type=PerformanceIssueType.MEMORY_INTENSIVE,
                    severity="high",
                    description=f"High CPU usage: {cpu_percent:.1f}%",
                    impact="System slowdown, reduced responsiveness",
                    recommendations=["Close unnecessary applications", "Check for background processes"],
                    potential_savings={"performance": "Improved system responsiveness"}
                ))

            if memory.percent > 85:
                issues.append(PerformanceIssue(
                    issue_id=f"high_memory_{int(time.time())}",
                    file_path=None,
                    issue_type=PerformanceIssueType.MEMORY_INTENSIVE,
                    severity="high",
                    description=f"High memory usage: {memory.percent:.1f}%",
                    impact="System slowdown, potential swapping",
                    recommendations=["Close memory-intensive applications", "Add more RAM"],
                    potential_savings={"performance": "Reduced swapping, faster operations"}
                ))

            for mount, usage_percent in disk_usage.items():
                if usage_percent > 90:
                    issues.append(PerformanceIssue(
                        issue_id=f"disk_full_{mount}_{int(time.time())}",
                        file_path=None,
                        issue_type=PerformanceIssueType.DISK_SPACE_WASTE,
                        severity="critical",
                        description=f"Disk almost full: {mount} ({usage_percent:.1f}%)",
                        impact="System instability, cannot save files",
                        recommendations=["Clean up unnecessary files", "Move files to external storage"],
                        potential_savings={"space": "Critical disk space recovery"}
                    ))

            return metrics, issues

        except Exception as e:
            self.logger.error(f"Error analyzing system performance: {e}")
            return SystemMetrics(0, 0, {}, {}, {}, 0, 0), []

    async def analyze_directory_performance(self, directory_path: Path) -> List[PerformanceIssue]:
        """Analyze performance issues in a directory"""
        issues = []

        try:
            # Check directory depth
            max_depth = 0
            file_count = 0

            for root, dirs, files in os.walk(directory_path):
                depth = len(Path(root).relative_to(directory_path).parts)
                max_depth = max(max_depth, depth)
                file_count += len(files)

            if max_depth > 10:
                issues.append(PerformanceIssue(
                    issue_id=f"deep_nesting_{int(time.time())}",
                    file_path=directory_path,
                    issue_type=PerformanceIssueType.EXCESSIVE_NESTING,
                    severity="medium",
                    description=f"Directory structure too deep ({max_depth} levels)",
                    impact="Slow file operations, path length issues",
                    recommendations=["Flatten directory structure", "Reorganize files"],
                    potential_savings={"performance": "Faster file access"}
                ))

            if file_count > 10000:
                issues.append(PerformanceIssue(
                    issue_id=f"too_many_files_{int(time.time())}",
                    file_path=directory_path,
                    issue_type=PerformanceIssueType.SLOW_ACCESS_PATTERN,
                    severity="medium",
                    description=f"Too many files in directory tree ({file_count:,})",
                    impact="Slow directory listing, high memory usage",
                    recommendations=["Split into subdirectories", "Archive old files"],
                    potential_savings={"performance": "Faster directory operations"}
                ))

        except Exception as e:
            self.logger.error(f"Error analyzing directory performance: {e}")

        return issues


class SecurityPerformanceAnalyzer:
    """Main class combining security and performance analysis"""

    def __init__(self, file_analyzer: ComprehensiveFileAnalyzer,
                 ai_assistant: Optional[AdvancedAIAssistant] = None):
        self.file_analyzer = file_analyzer
        self.ai_assistant = ai_assistant
        self.logger = Logger()

        self.malware_detector = MalwareDetector()
        self.permission_analyzer = PermissionAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()

    async def comprehensive_security_scan(self, directory_path: Path) -> Dict[str, Any]:
        """Perform comprehensive security scan of directory"""
        try:
            threats = []
            scanned_files = 0

            # Get all files
            file_paths = [p for p in directory_path.rglob('*') if p.is_file()]
            total_files = len(file_paths)

            self.logger.info(f"Starting security scan of {total_files} files")

            for file_path in file_paths:
                try:
                    # Malware scan
                    malware_threats = await self.malware_detector.scan_file(file_path)
                    threats.extend(malware_threats)

                    # Permission analysis
                    permission_threats = await self.permission_analyzer.analyze_permissions(file_path)
                    threats.extend(permission_threats)

                    scanned_files += 1

                    if scanned_files % 100 == 0:
                        self.logger.info(f"Scanned {scanned_files}/{total_files} files")

                except Exception as e:
                    self.logger.error(f"Error scanning {file_path}: {e}")

            # Categorize threats by risk level
            threat_summary = {
                'critical': [t for t in threats if t.risk_level == SecurityRiskLevel.CRITICAL],
                'high': [t for t in threats if t.risk_level == SecurityRiskLevel.HIGH],
                'medium': [t for t in threats if t.risk_level == SecurityRiskLevel.MEDIUM],
                'low': [t for t in threats if t.risk_level == SecurityRiskLevel.LOW]
            }

            return {
                'total_files_scanned': scanned_files,
                'total_threats': len(threats),
                'threat_summary': {
                    level: len(threat_list) for level, threat_list in threat_summary.items()
                },
                'threats': [t.to_dict() for t in threats],
                'scan_completed_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error in security scan: {e}")
            raise SecurityError(f"Security scan failed: {e}")

    async def comprehensive_performance_analysis(self, directory_path: Path) -> Dict[str, Any]:
        """Perform comprehensive performance analysis"""
        try:
            file_issues = []

            # System performance analysis
            system_metrics, system_issues = await self.performance_analyzer.analyze_system_performance()

            # Directory performance analysis
            directory_issues = await self.performance_analyzer.analyze_directory_performance(directory_path)

            # File-level performance analysis
            file_paths = [p for p in directory_path.rglob('*') if p.is_file()]
            analyzed_files = 0

            for file_path in file_paths:
                try:
                    metadata = await self.file_analyzer.metadata_extractor.extract_metadata(file_path)
                    issues = await self.performance_analyzer.analyze_file_performance(file_path, metadata)
                    file_issues.extend(issues)
                    analyzed_files += 1

                    if analyzed_files % 100 == 0:
                        self.logger.info(f"Analyzed {analyzed_files}/{len(file_paths)} files")

                except Exception as e:
                    self.logger.error(f"Error analyzing {file_path}: {e}")

            all_issues = system_issues + directory_issues + file_issues

            # Categorize issues by severity
            issue_summary = {
                'critical': [i for i in all_issues if i.severity == 'critical'],
                'high': [i for i in all_issues if i.severity == 'high'],
                'medium': [i for i in all_issues if i.severity == 'medium'],
                'low': [i for i in all_issues if i.severity == 'low']
            }

            # Calculate potential savings
            total_space_savings = sum(
                i.potential_savings.get('space', 0)
                for i in all_issues
                if isinstance(i.potential_savings.get('space'), (int, float))
            )

            return {
                'system_metrics': {
                    'cpu_usage': system_metrics.cpu_usage,
                    'memory_usage': system_metrics.memory_usage,
                    'disk_usage': system_metrics.disk_usage,
                    'process_count': system_metrics.process_count,
                    'uptime': system_metrics.uptime
                },
                'total_files_analyzed': analyzed_files,
                'total_issues': len(all_issues),
                'issue_summary': {
                    level: len(issue_list) for level, issue_list in issue_summary.items()
                },
                'potential_savings': {
                    'disk_space': total_space_savings,
                    'performance_improvements': len([i for i in all_issues if 'performance' in i.potential_savings])
                },
                'issues': [i.to_dict() for i in all_issues],
                'analysis_completed_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error in performance analysis: {e}")
            raise PerformanceError(f"Performance analysis failed: {e}")

    async def generate_security_report(self, directory_path: Path) -> str:
        """Generate a comprehensive security report"""
        try:
            scan_results = await self.comprehensive_security_scan(directory_path)

            report = f"""
# Security Analysis Report
**Directory:** {directory_path}
**Scan Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Files Scanned:** {scan_results['total_files_scanned']:,}

## Threat Summary
- **Critical:** {scan_results['threat_summary']['critical']} threats
- **High:** {scan_results['threat_summary']['high']} threats
- **Medium:** {scan_results['threat_summary']['medium']} threats
- **Low:** {scan_results['threat_summary']['low']} threats

## Recommendations
"""

            if scan_results['threat_summary']['critical'] > 0:
                report += "⚠️ **IMMEDIATE ACTION REQUIRED** - Critical threats detected!\n"

            if scan_results['threat_summary']['high'] > 0:
                report += "🔴 High-risk threats require prompt attention\n"

            if scan_results['total_threats'] == 0:
                report += "✅ No security threats detected\n"

            return report

        except Exception as e:
            self.logger.error(f"Error generating security report: {e}")
            return f"Error generating security report: {e}"

    async def generate_performance_report(self, directory_path: Path) -> str:
        """Generate a comprehensive performance report"""
        try:
            analysis_results = await self.comprehensive_performance_analysis(directory_path)

            report = f"""
# Performance Analysis Report
**Directory:** {directory_path}
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Files Analyzed:** {analysis_results['total_files_analyzed']:,}

## System Metrics
- **CPU Usage:** {analysis_results['system_metrics']['cpu_usage']:.1f}%
- **Memory Usage:** {analysis_results['system_metrics']['memory_usage']:.1f}%
- **Process Count:** {analysis_results['system_metrics']['process_count']:,}

## Performance Issues
- **Critical:** {analysis_results['issue_summary']['critical']} issues
- **High:** {analysis_results['issue_summary']['high']} issues
- **Medium:** {analysis_results['issue_summary']['medium']} issues
- **Low:** {analysis_results['issue_summary']['low']} issues

## Potential Savings
- **Disk Space:** {analysis_results['potential_savings']['disk_space']:,} bytes
- **Performance Improvements:** {analysis_results['potential_savings']['performance_improvements']} opportunities

## Recommendations
"""

            if analysis_results['issue_summary']['critical'] > 0:
                report += "🚨 Critical performance issues detected - immediate action required\n"

            if analysis_results['potential_savings']['disk_space'] > 1024**3:  # > 1GB
                gb_savings = analysis_results['potential_savings']['disk_space'] / (1024**3)
                report += f"💾 Potential to save {gb_savings:.1f} GB of disk space\n"

            return report

        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return f"Error generating performance report: {e}"

    async def get_optimization_suggestions(self, directory_path: Path) -> List[Dict[str, Any]]:
        """Get AI-powered optimization suggestions"""
        suggestions = []

        try:
            # Get analysis results
            security_results = await self.comprehensive_security_scan(directory_path)
            performance_results = await self.comprehensive_performance_analysis(directory_path)

            # Generate suggestions based on findings
            if security_results['total_threats'] > 0:
                suggestions.append({
                    'type': 'security',
                    'priority': 'high',
                    'title': 'Security Threats Detected',
                    'description': f"Found {security_results['total_threats']} security threats",
                    'actions': ['Run full antivirus scan', 'Review file permissions', 'Remove suspicious files']
                })

            if performance_results['potential_savings']['disk_space'] > 1024**3:
                suggestions.append({
                    'type': 'performance',
                    'priority': 'medium',
                    'title': 'Disk Space Optimization',
                    'description': f"Can save {performance_results['potential_savings']['disk_space']/(1024**3):.1f} GB",
                    'actions': ['Remove duplicate files', 'Compress large files', 'Archive old files']
                })

            # Use AI for additional suggestions if available
            if self.ai_assistant:
                try:
                    ai_suggestions = await self._get_ai_optimization_suggestions(
                        security_results, performance_results
                    )
                    suggestions.extend(ai_suggestions)
                except Exception as e:
                    self.logger.error(f"AI suggestions failed: {e}")

            return suggestions

        except Exception as e:
            self.logger.error(f"Error getting optimization suggestions: {e}")
            return []

    async def _get_ai_optimization_suggestions(self, security_results: Dict[str, Any],
                                            performance_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get AI-powered optimization suggestions"""
        # This would use the AI assistant to generate intelligent suggestions
        # For now, return empty list
        return []