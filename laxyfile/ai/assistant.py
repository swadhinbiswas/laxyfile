"""
Advanced AI Assistant with OpenRouter Integration
Supports comprehensive file analysis, device monitoring, and intelligent automation
"""

import os
import sys
import json
import asyncio
import subprocess
import platform
import shutil
import mimetypes
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from datetime import datetime

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

from ..core.config import Config, AIConfig
from ..core.file_manager import FileInfo
from ..utils.logger import Logger

class AdvancedAIAssistant:
    """AI-powered assistant with OpenRouter integration and comprehensive system analysis"""

    def __init__(self, config: Config):
        self.config = config
        self.ai_config = config.get_ai()
        self.logger = Logger()

        # OpenRouter client
        self.client = None
        self.setup_openrouter_client()

        # Cache for performance
        self.file_cache = {}
        self.device_cache = {}
        self.analysis_cache = {}

    def setup_openrouter_client(self):
        """Setup OpenRouter client for Kimi AI"""
        if not HAS_OPENAI:
            self.logger.error("OpenAI library required for OpenRouter integration")
            return

        # Get API key from environment or config
        api_key = os.getenv("OPENROUTER_API_KEY") or self.ai_config.openai_api_key

        if api_key:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
            self.logger.info("OpenRouter client initialized successfully")
        else:
            self.logger.warning("No OpenRouter API key found")

    def is_configured(self) -> bool:
        """Check if AI is properly configured"""
        return self.client is not None

    async def query(self, user_query: str, current_path: Path,
                   selected_files: List[Path] = None, include_content: bool = False,
                   include_devices: bool = False) -> str:
        """Advanced query with comprehensive context"""
        if not self.is_configured():
            return "❌ AI assistant not configured. Please set OPENROUTER_API_KEY environment variable."

        try:
            # Build comprehensive context
            context = await self._build_comprehensive_context(
                current_path, selected_files or [], include_content, include_devices
            )

            # Create enhanced system prompt
            system_prompt = self._create_enhanced_system_prompt()

            # Create detailed user message
            user_message = self._create_detailed_user_message(user_query, context)

            # Query Kimi AI through OpenRouter
            response = await self._query_openrouter(system_prompt, user_message)

            # Cache the result
            cache_key = hashlib.md5(f"{user_query}{current_path}".encode()).hexdigest()
            self.analysis_cache[cache_key] = response

            return response

        except Exception as e:
            self.logger.error(f"AI query failed: {e}")
            return f"❌ AI query failed: {str(e)}"

    async def _build_comprehensive_context(self, current_path: Path, selected_files: List[Path],
                                         include_content: bool = False, include_devices: bool = False) -> Dict[str, Any]:
        """Build comprehensive context with file content and device information"""
        context = {
            "timestamp": datetime.now().isoformat(),
            "current_directory": str(current_path),
            "system_info": self._get_system_info(),
            "selected_files": [],
            "directory_contents": [],
            "file_statistics": {},
            "file_contents": {},
            "device_information": {},
            "network_info": {},
            "security_analysis": {}
        }

        # Add selected files with detailed analysis
        for file_path in selected_files:
            if file_path.exists():
                file_info = await self._analyze_file(file_path, include_content)
                context["selected_files"].append(file_info)

        # Add directory contents analysis
        context["directory_contents"] = await self._analyze_directory(current_path)
        context["file_statistics"] = await self._get_advanced_directory_stats(current_path)

        # Add device information if requested
        if include_devices:
            context["device_information"] = await self._get_device_information()
            context["network_info"] = await self._get_network_information()

        # Security analysis
        context["security_analysis"] = await self._perform_security_analysis(current_path)

        return context

    async def _analyze_file(self, file_path: Path, include_content: bool = False) -> Dict[str, Any]:
        """Comprehensive file analysis"""
        try:
            stat = file_path.stat()
            file_info = {
                "name": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "is_directory": file_path.is_dir(),
                "is_symlink": file_path.is_symlink(),
                "extension": file_path.suffix.lower(),
                "permissions": oct(stat.st_mode)[-3:],
                "mime_type": mimetypes.guess_type(str(file_path))[0],
                "file_type_analysis": {},
                "content_preview": "",
                "metadata": {}
            }

            # Enhanced file type detection
            if HAS_MAGIC:
                try:
                    file_info["magic_mime"] = magic.from_file(str(file_path), mime=True)
                    file_info["magic_description"] = magic.from_file(str(file_path))
                except:
                    pass

            # File-specific analysis
            if file_path.is_file():
                file_info["file_type_analysis"] = await self._analyze_file_type(file_path)

                if include_content:
                    file_info["content_preview"] = await self._get_file_content_preview(file_path)

            return file_info

        except Exception as e:
            self.logger.error(f"File analysis failed for {file_path}: {e}")
            return {"name": file_path.name, "error": str(e)}

    async def _analyze_file_type(self, file_path: Path) -> Dict[str, Any]:
        """Analyze specific file types"""
        analysis = {"type": "unknown", "details": {}}

        try:
            ext = file_path.suffix.lower()

            # Image analysis
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                analysis["type"] = "image"
                if HAS_OPENCV:
                    try:
                        img = cv2.imread(str(file_path))
                        if img is not None:
                            analysis["details"] = {
                                "dimensions": f"{img.shape[1]}x{img.shape[0]}",
                                "channels": img.shape[2] if len(img.shape) > 2 else 1,
                                "color_space": "BGR" if len(img.shape) > 2 else "Grayscale"
                            }
                    except:
                        pass

            # Video analysis
            elif ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
                analysis["type"] = "video"
                if HAS_OPENCV:
                    try:
                        cap = cv2.VideoCapture(str(file_path))
                        if cap.isOpened():
                            analysis["details"] = {
                                "fps": cap.get(cv2.CAP_PROP_FPS),
                                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                                "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
                                "resolution": f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}"
                            }
                        cap.release()
                    except:
                        pass

            # Code file analysis
            elif ext in ['.py', '.js', '.java', '.cpp', '.c', '.html', '.css', '.json', '.xml']:
                analysis["type"] = "code"
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(10000)  # First 10KB
                        lines = content.split('\n')
                        analysis["details"] = {
                            "language": ext[1:],
                            "line_count": len(lines),
                            "non_empty_lines": len([l for l in lines if l.strip()]),
                            "imports_detected": len([l for l in lines if 'import' in l or 'include' in l])
                        }
                except:
                    pass

            # Archive analysis
            elif ext in ['.zip', '.tar', '.gz', '.rar', '.7z']:
                analysis["type"] = "archive"
                # Could add archive content analysis here

        except Exception as e:
            analysis["error"] = str(e)

        return analysis

    async def _get_file_content_preview(self, file_path: Path, max_size: int = 50000) -> str:
        """Get file content preview with smart handling"""
        try:
            if file_path.stat().st_size > max_size:
                return f"[File too large: {file_path.stat().st_size} bytes]"

            # Try to read as text
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_size)
                    if len(content) > 1000:
                        return content[:1000] + "\n... [Content truncated] ..."
                    return content
            except:
                # Try binary analysis
                with open(file_path, 'rb') as f:
                    data = f.read(100)
                    return f"[Binary file - first 100 bytes]: {data.hex()}"

        except Exception as e:
            return f"[Cannot read file: {e}]"

    async def _analyze_directory(self, path: Path) -> List[Dict[str, Any]]:
        """Analyze directory contents with pattern detection"""
        contents = []

        try:
            items = list(path.iterdir())[:50]  # Limit for performance

            for item in items:
                try:
                    item_info = {
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else 0,
                        "extension": item.suffix.lower() if item.is_file() else "",
                        "hidden": item.name.startswith('.'),
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    }
                    contents.append(item_info)
                except (PermissionError, OSError):
                    continue

        except (PermissionError, OSError):
            pass

        return contents

    async def _get_advanced_directory_stats(self, path: Path) -> Dict[str, Any]:
        """Get comprehensive directory statistics"""
        stats = {
            "total_files": 0,
            "total_directories": 0,
            "total_size": 0,
            "largest_files": [],
            "file_types": {},
            "duplicate_analysis": {},
            "age_distribution": {"recent": 0, "old": 0, "ancient": 0}
        }

        try:
            now = datetime.now().timestamp()

            for item in path.rglob('*'):
                try:
                    if item.is_file():
                        size = item.stat().st_size
                        mtime = item.stat().st_mtime

                        stats["total_files"] += 1
                        stats["total_size"] += size

                        # Track largest files
                        stats["largest_files"].append({"name": item.name, "size": size, "path": str(item)})
                        stats["largest_files"] = sorted(stats["largest_files"], key=lambda x: x["size"], reverse=True)[:10]

                        # File type analysis
                        ext = item.suffix.lower()
                        if ext not in stats["file_types"]:
                            stats["file_types"][ext] = {"count": 0, "total_size": 0}
                        stats["file_types"][ext]["count"] += 1
                        stats["file_types"][ext]["total_size"] += size

                        # Age distribution
                        age_days = (now - mtime) / 86400
                        if age_days < 30:
                            stats["age_distribution"]["recent"] += 1
                        elif age_days < 365:
                            stats["age_distribution"]["old"] += 1
                        else:
                            stats["age_distribution"]["ancient"] += 1

                    elif item.is_dir():
                        stats["total_directories"] += 1

                except (PermissionError, OSError):
                    continue

        except (PermissionError, OSError):
            pass

        return stats

    def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node()
        }

        if HAS_PSUTIL:
            try:
                info.update({
                    "cpu_count": psutil.cpu_count(),
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_total": psutil.virtual_memory().total,
                    "memory_available": psutil.virtual_memory().available,
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage": {str(disk.mountpoint): {
                        "total": psutil.disk_usage(disk.mountpoint).total,
                        "used": psutil.disk_usage(disk.mountpoint).used,
                        "free": psutil.disk_usage(disk.mountpoint).free
                    } for disk in psutil.disk_partitions()},
                    "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
                })
            except:
                pass

        return info

    async def _get_device_information(self) -> Dict[str, Any]:
        """Get detailed device and hardware information"""
        devices = {
            "storage_devices": [],
            "network_interfaces": [],
            "usb_devices": [],
            "mounted_filesystems": [],
            "hardware_info": {}
        }

        if HAS_PSUTIL:
            try:
                # Storage devices
                partitions = psutil.disk_partitions()
                for partition in partitions:
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        devices["storage_devices"].append({
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": (usage.used / usage.total) * 100 if usage.total > 0 else 0
                        })
                    except:
                        continue

                # Network interfaces
                interfaces = psutil.net_if_addrs()
                for interface, addrs in interfaces.items():
                    interface_info = {"name": interface, "addresses": []}
                    for addr in addrs:
                        interface_info["addresses"].append({
                            "family": addr.family.name,
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast
                        })
                    devices["network_interfaces"].append(interface_info)

                # Running processes (top 10 by memory)
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                    try:
                        processes.append(proc.info)
                    except:
                        continue

                devices["top_processes"] = sorted(processes, key=lambda x: x.get('memory_percent', 0), reverse=True)[:10]

            except Exception as e:
                devices["error"] = str(e)

        # Additional hardware detection
        try:
            # USB devices (Linux)
            if platform.system() == "Linux":
                result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    devices["usb_devices"] = result.stdout.strip().split('\n')
        except:
            pass

        return devices

    async def _get_network_information(self) -> Dict[str, Any]:
        """Get network information and connectivity"""
        network = {
            "interfaces": [],
            "connections": [],
            "internet_connectivity": False,
            "dns_servers": []
        }

        if HAS_PSUTIL:
            try:
                # Network statistics
                net_io = psutil.net_io_counters(pernic=True)
                for interface, stats in net_io.items():
                    network["interfaces"].append({
                        "name": interface,
                        "bytes_sent": stats.bytes_sent,
                        "bytes_recv": stats.bytes_recv,
                        "packets_sent": stats.packets_sent,
                        "packets_recv": stats.packets_recv
                    })

                # Active connections (limited for security)
                connections = psutil.net_connections(kind='inet')[:20]
                for conn in connections:
                    try:
                        network["connections"].append({
                            "family": conn.family.name,
                            "type": conn.type.name,
                            "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                            "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                            "status": conn.status,
                            "pid": conn.pid
                        })
                    except:
                        continue

            except Exception as e:
                network["error"] = str(e)

        # Test internet connectivity
        try:
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'],
                                  capture_output=True, timeout=5)
            network["internet_connectivity"] = result.returncode == 0
        except:
            pass

        return network

    async def _perform_security_analysis(self, path: Path) -> Dict[str, Any]:
        """Perform security analysis of files and directories"""
        security = {
            "suspicious_files": [],
            "permission_issues": [],
            "large_files": [],
            "hidden_files": [],
            "executable_files": [],
            "recommendations": []
        }

        try:
            for item in path.rglob('*'):
                try:
                    if item.is_file():
                        stat = item.stat()

                        # Check for suspicious extensions
                        suspicious_exts = ['.exe', '.bat', '.cmd', '.scr', '.vbs', '.js']
                        if item.suffix.lower() in suspicious_exts:
                            security["suspicious_files"].append(str(item))

                        # Check for overly permissive permissions
                        if oct(stat.st_mode)[-3:] in ['777', '666']:
                            security["permission_issues"].append({
                                "file": str(item),
                                "permissions": oct(stat.st_mode)[-3:]
                            })

                        # Large files
                        if stat.st_size > 100 * 1024 * 1024:  # > 100MB
                            security["large_files"].append({
                                "file": str(item),
                                "size": stat.st_size
                            })

                        # Hidden files
                        if item.name.startswith('.') and item.name not in ['.', '..']:
                            security["hidden_files"].append(str(item))

                        # Executable files
                        if stat.st_mode & 0o111:  # Any execute permission
                            security["executable_files"].append(str(item))

                except (PermissionError, OSError):
                    continue

        except (PermissionError, OSError):
            pass

        return security

    def _create_enhanced_system_prompt(self) -> str:
        """Create comprehensive system prompt for Kimi AI"""
        return """You are LaxyFile Advanced AI Assistant, an intelligent file management and system analysis expert powered by Kimi AI.

Your comprehensive capabilities include:

📁 FILE MANAGEMENT:
- Deep file analysis with content inspection
- Intelligent file organization suggestions
- File type identification and metadata extraction
- Duplicate detection and cleanup recommendations
- Archive analysis and compression optimization

💻 SYSTEM ANALYSIS:
- Complete device and hardware monitoring
- Network connectivity and interface analysis
- Process monitoring and resource optimization
- Storage analysis and cleanup recommendations
- Security vulnerability assessment

🔒 SECURITY FEATURES:
- Suspicious file detection
- Permission analysis and recommendations
- Hidden file discovery
- Executable file tracking
- Security best practices guidance

🎬 MEDIA ANALYSIS:
- Image metadata and quality analysis
- Video file inspection and encoding details
- Audio file format and quality assessment
- Media organization and optimization suggestions

📊 INTELLIGENT INSIGHTS:
- Pattern recognition in file structures
- Automated organization suggestions
- Performance optimization recommendations
- Backup strategy development
- Workflow improvement suggestions

You have access to:
- Complete file system analysis with content reading
- Real-time system and device information
- Network and connectivity data
- Security analysis and threat assessment
- Media file technical details

Always provide:
- Practical, actionable recommendations
- Clear explanations of technical concepts
- Security-conscious advice
- Performance optimization tips
- Specific commands or steps when helpful

Format responses with emojis, clear sections, and actionable bullet points.
Be thorough but concise, and always prioritize user security and data integrity."""

    def _create_detailed_user_message(self, user_query: str, context: Dict[str, Any]) -> str:
        """Create comprehensive user message with full context"""
        message = f"🤖 USER QUERY: {user_query}\n\n"

        # System context
        message += "💻 SYSTEM INFORMATION:\n"
        sys_info = context["system_info"]
        message += f"- Platform: {sys_info.get('platform', 'Unknown')}\n"
        message += f"- CPU: {sys_info.get('processor', 'Unknown')} ({sys_info.get('cpu_count', '?')} cores)\n"
        if 'memory_total' in sys_info:
            memory_gb = sys_info['memory_total'] / (1024**3)
            message += f"- Memory: {memory_gb:.1f}GB ({sys_info.get('memory_percent', '?')}% used)\n"
        message += f"- Hostname: {sys_info.get('hostname', 'Unknown')}\n\n"

        # Current directory context
        message += f"📁 CURRENT DIRECTORY: {context['current_directory']}\n"

        # Directory statistics
        stats = context['file_statistics']
        if stats.get('total_files', 0) > 0:
            message += f"📊 DIRECTORY STATS:\n"
            message += f"- Files: {stats['total_files']}, Directories: {stats['total_directories']}\n"
            message += f"- Total Size: {stats['total_size'] / (1024**2):.1f} MB\n"

            # Top file types
            if stats.get('file_types'):
                top_types = sorted(stats['file_types'].items(),
                                 key=lambda x: x[1].get('count', 0), reverse=True)[:5]
                message += f"- Top file types: {', '.join([f'{ext}({info.get('count', 0)})' for ext, info in top_types])}\n"

            # Largest files
            if stats.get('largest_files'):
                message += f"- Largest files: {', '.join([f'{f['name']}({f['size']/(1024**2):.1f}MB)' for f in stats['largest_files'][:3]])}\n"

        message += "\n"

        # Selected files
        if context['selected_files']:
            message += f"📄 SELECTED FILES ({len(context['selected_files'])}):\n"
            for file_info in context['selected_files'][:10]:
                message += f"- {file_info['name']}"
                if 'size' in file_info:
                    message += f" ({file_info['size']/(1024**2):.1f}MB)"
                if 'file_type_analysis' in file_info:
                    analysis = file_info['file_type_analysis']
                    if analysis.get('type') != 'unknown':
                        message += f" [{analysis['type'].upper()}]"
                message += "\n"

                # Add content preview if available
                if file_info.get('content_preview'):
                    preview = file_info['content_preview'][:200]
                    message += f"  Preview: {preview}...\n"
            message += "\n"

        # Device information
        if context.get('device_information'):
            devices = context['device_information']
            message += "🖥️ DEVICE INFORMATION:\n"

            # Storage devices
            if devices.get('storage_devices'):
                message += "💾 Storage Devices:\n"
                for device in devices['storage_devices'][:5]:
                    free_gb = device['free'] / (1024**3)
                    total_gb = device['total'] / (1024**3)
                    message += f"- {device['device']}: {free_gb:.1f}GB free / {total_gb:.1f}GB total ({device['percent']:.1f}% used)\n"

            # Top processes
            if devices.get('top_processes'):
                message += "⚡ Top Processes (by memory):\n"
                for proc in devices['top_processes'][:3]:
                    message += f"- {proc.get('name', 'Unknown')} (PID: {proc.get('pid', '?')}, Memory: {proc.get('memory_percent', 0):.1f}%)\n"

            message += "\n"

        # Security analysis
        if context.get('security_analysis'):
            security = context['security_analysis']
            message += "🔒 SECURITY ANALYSIS:\n"

            if security.get('suspicious_files'):
                message += f"- Suspicious files found: {len(security['suspicious_files'])}\n"
            if security.get('permission_issues'):
                message += f"- Permission issues: {len(security['permission_issues'])}\n"
            if security.get('hidden_files'):
                message += f"- Hidden files: {len(security['hidden_files'])}\n"
            if security.get('executable_files'):
                message += f"- Executable files: {len(security['executable_files'])}\n"

            message += "\n"

        # Network information
        if context.get('network_info'):
            network = context['network_info']
            message += "🌐 NETWORK STATUS:\n"
            message += f"- Internet connectivity: {'✅ Connected' if network.get('internet_connectivity') else '❌ Disconnected'}\n"
            if network.get('interfaces'):
                message += f"- Network interfaces: {len(network['interfaces'])}\n"
            message += "\n"

        message += "Please analyze this information and provide intelligent recommendations based on the user's query."

        return message

    async def _query_openrouter(self, system_prompt: str, user_message: str) -> str:
        """Query Kimi AI through OpenRouter"""
        try:
            completion = await asyncio.to_thread(
                self.client.chat.completions.create,
                extra_headers={
                    "HTTP-Referer": "https://laxyfile.dev",
                    "X-Title": "LaxyFile AI Assistant",
                },
                model="moonshotai/kimi-dev-72b:free",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=self.ai_config.max_tokens,
                temperature=self.ai_config.temperature
            )

            return completion.choices[0].message.content.strip()

        except Exception as e:
            self.logger.error(f"OpenRouter API error: {e}")
            return f"❌ OpenRouter API error: {str(e)}"

    # Enhanced convenience methods

    async def analyze_complete_system(self, current_path: Path) -> str:
        """Complete system analysis with all features"""
        query = "Perform a comprehensive analysis of my entire system including files, devices, security, and performance. Provide detailed recommendations for optimization, security improvements, and file organization."
        return await self.query(query, current_path, include_content=True, include_devices=True)

    async def smart_file_organization(self, current_path: Path, selected_files: List[Path] = None) -> str:
        """AI-powered file organization suggestions"""
        query = "Analyze the file structure and contents, then suggest an intelligent organization strategy. Consider file types, creation dates, sizes, and usage patterns. Provide specific folder structures and naming conventions."
        return await self.query(query, current_path, selected_files, include_content=True)

    async def security_audit(self, current_path: Path) -> str:
        """Comprehensive security audit"""
        query = "Perform a detailed security audit of the current directory and system. Identify potential vulnerabilities, suspicious files, permission issues, and provide actionable security recommendations."
        return await self.query(query, current_path, include_devices=True)

    async def performance_optimization(self, current_path: Path) -> str:
        """System and storage performance analysis"""
        query = "Analyze system performance, storage usage, and file organization efficiency. Suggest optimizations for faster file access, storage cleanup, and system performance improvements."
        return await self.query(query, current_path, include_devices=True)

    async def create_video_analysis(self, video_files: List[Path]) -> str:
        """Analyze video files and suggest processing options"""
        query = "Analyze the selected video files including resolution, encoding, file sizes, and quality. Suggest optimization strategies, format conversions, or organization improvements for video files."
        return await self.query(query, Path.cwd(), video_files, include_content=True)

    async def duplicate_finder(self, current_path: Path) -> str:
        """Find and suggest duplicate file cleanup"""
        query = "Scan for duplicate files based on size, name patterns, and content analysis. Suggest which duplicates to keep and which to remove, considering file quality and relevance."
        return await self.query(query, current_path, include_content=True)

    async def media_organization(self, current_path: Path) -> str:
        """Organize media files intelligently"""
        query = "Analyze all media files (images, videos, audio) and suggest an optimal organization structure based on creation dates, quality, file types, and metadata. Include rename suggestions and folder structures."
        return await self.query(query, current_path, include_content=True)

    async def backup_strategy(self, current_path: Path) -> str:
        """Generate intelligent backup recommendations"""
        query = "Analyze file importance, change frequency, and storage requirements to suggest a comprehensive backup strategy. Include specific tools, schedules, and prioritization for different file types."
        return await self.query(query, current_path, include_content=True, include_devices=True)

# Backward compatibility alias
AIAssistant = AdvancedAIAssistant