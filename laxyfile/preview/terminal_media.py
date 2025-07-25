"""
Terminal-Compatible Media Preview System

This module provides image and video preview capabilities optimized for terminal display
using ASCII art, Unicode blocks, and ANSI escape sequences.
"""

import base64
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import mimetypes
import shutil

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table

from ..utils.logger import Logger


class TerminalImageRenderer:
    """Renders images in terminal using various methods"""

    def __init__(self):
        self.logger = Logger("TerminalImageRenderer")

        # Check available image rendering methods
        self.methods = self._detect_available_methods()
        self.console = Console()

        # Unicode block characters for image rendering
        self.block_chars = {
            0: ' ',      # Empty
            1: '▁',      # Lower 1/8
            2: '▂',      # Lower 2/8
            3: '▃',      # Lower 3/8
            4: '▄',      # Lower 4/8
            5: '▅',      # Lower 5/8
            6: '▆',      # Lower 6/8
            7: '▇',      # Lower 7/8
            8: '█',      # Full block
        }

        # Color mapping for 256-color terminals
        self.color_palette = self._generate_color_palette()

    def _detect_available_methods(self) -> Dict[str, bool]:
        """Detect available image rendering methods"""
        methods = {
            'chafa': False,
            'catimg': False,
            'img2txt': False,
            'timg': False,
            'viu': False,
            'pixterm': False,
            'unicode_blocks': True,  # Always available
            'ascii_art': True,       # Always available
        }

        # Check for external tools
        for tool in ['chafa', 'catimg', 'img2txt', 'timg', 'viu', 'pixterm']:
            if shutil.which(tool):
                methods[tool] = True
                self.logger.debug(f"Found image tool: {tool}")

        return methods

    def _generate_color_palette(self) -> List[Tuple[int, int, int]]:
        """Generate 256-color terminal palette"""
        palette = []

        # Standard 16 colors (simplified)
        standard_colors = [
            (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0),
            (0, 0, 128), (128, 0, 128), (0, 128, 128), (192, 192, 192),
            (128, 128, 128), (255, 0, 0), (0, 255, 0), (255, 255, 0),
            (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)
        ]
        palette.extend(standard_colors)

        # 216 color cube (6x6x6)
        for r in range(6):
            for g in range(6):
                for b in range(6):
                    palette.append((
                        0 if r == 0 else 55 + r * 40,
                        0 if g == 0 else 55 + g * 40,
                        0 if b == 0 else 55 + b * 40
                    ))

        # 24 grayscale colors
        for i in range(24):
            gray = 8 + i * 10
            palette.append((gray, gray, gray))

        return palette

    def render_image(self, image_path: Path, width: int = 40, height: int = 20) -> str:
        """Render image for terminal display"""
        try:
            # Try external tools first (best quality)
            if self.methods['chafa']:
                return self._render_with_chafa(image_path, width, height)
            elif self.methods['catimg']:
                return self._render_with_catimg(image_path, width)
            elif self.methods['viu']:
                return self._render_with_viu(image_path, width, height)
            elif self.methods['timg']:
                return self._render_with_timg(image_path, width, height)
            else:
                # Fallback to built-in methods
                return self._render_with_unicode_blocks(image_path, width, height)

        except Exception as e:
            self.logger.error(f"Error rendering image {image_path}: {e}")
            return self._create_fallback_preview(image_path)

    def _render_with_chafa(self, image_path: Path, width: int, height: int) -> str:
        """Render image using chafa (best quality)"""
        try:
            cmd = [
                'chafa',
                '--size', f'{width}x{height}',
                '--symbols', 'block',
                '--colors', '256',
                str(image_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout
            else:
                self.logger.warning(f"Chafa failed: {result.stderr}")
                return self._render_with_unicode_blocks(image_path, width, height)

        except subprocess.TimeoutExpired:
            self.logger.warning("Chafa timeout")
            return self._create_fallback_preview(image_path)
        except Exception as e:
            self.logger.error(f"Chafa error: {e}")
            return self._render_with_unicode_blocks(image_path, width, height)

    def _render_with_catimg(self, image_path: Path, width: int) -> str:
        """Render image using catimg"""
        try:
            cmd = ['catimg', '-w', str(width), str(image_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                return result.stdout
            else:
                return self._create_fallback_preview(image_path)

        except Exception as e:
            self.logger.error(f"Catimg error: {e}")
            return self._create_fallback_preview(image_path)

    def _render_with_viu(self, image_path: Path, width: int, height: int) -> str:
        """Render image using viu"""
        try:
            cmd = ['viu', '-w', str(width), '-h', str(height), str(image_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                return result.stdout
            else:
                return self._create_fallback_preview(image_path)

        except Exception as e:
            self.logger.error(f"Viu error: {e}")
            return self._create_fallback_preview(image_path)

    def _render_with_timg(self, image_path: Path, width: int, height: int) -> str:
        """Render image using timg"""
        try:
            cmd = ['timg', f'--width={width}', f'--height={height}', str(image_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                return result.stdout
            else:
                return self._create_fallback_preview(image_path)

        except Exception as e:
            self.logger.error(f"Timg error: {e}")
            return self._create_fallback_preview(image_path)

    def _render_with_unicode_blocks(self, image_path: Path, width: int, height: int) -> str:
        """Render image using Unicode block characters (fallback)"""
        try:
            # Try to use PIL if available
            try:
                from PIL import Image

                with Image.open(image_path) as img:
                    # Convert to RGB if needed
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # Resize image
                    img = img.resize((width, height // 2), Image.Resampling.LANCZOS)

                    # Convert to block characters
                    result = []
                    for y in range(0, img.height, 2):
                        line = []
                        for x in range(img.width):
                            # Get pixel colors
                            upper_pixel = img.getpixel((x, y))
                            lower_pixel = img.getpixel((x, min(y + 1, img.height - 1)))

                            # Convert to grayscale and determine block
                            if isinstance(upper_pixel, tuple):
                                upper_gray = sum(upper_pixel) // 3
                            else:
                                upper_gray = int(upper_pixel) if upper_pixel is not None else 0

                            if isinstance(lower_pixel, tuple):
                                lower_gray = sum(lower_pixel) // 3
                            else:
                                lower_gray = int(lower_pixel) if lower_pixel is not None else 0

                            # Use half-block characters
                            if upper_gray > 128 and lower_gray > 128:
                                line.append('█')
                            elif upper_gray > 128:
                                line.append('▀')
                            elif lower_gray > 128:
                                line.append('▄')
                            else:
                                line.append(' ')

                        result.append(''.join(line))

                    return '\n'.join(result)

            except ImportError:
                # PIL not available, create a simple placeholder
                return self._create_simple_image_placeholder(image_path, width, height // 2)

        except Exception as e:
            self.logger.error(f"Unicode block rendering error: {e}")
            return self._create_fallback_preview(image_path)

    def _create_simple_image_placeholder(self, image_path: Path, width: int, height: int) -> str:
        """Create a simple image placeholder"""
        lines = []
        name = image_path.name

        # Create border
        lines.append('┌' + '─' * (width - 2) + '┐')

        # Add filename (centered)
        if len(name) > width - 4:
            name = name[:width - 7] + '...'
        padding = (width - len(name) - 2) // 2
        lines.append('│' + ' ' * padding + name + ' ' * (width - len(name) - padding - 2) + '│')

        # Fill with pattern
        for i in range(height - 3):
            if i % 2 == 0:
                lines.append('│' + '▓▒' * ((width - 2) // 2) + '▓' * ((width - 2) % 2) + '│')
            else:
                lines.append('│' + '▒▓' * ((width - 2) // 2) + '▒' * ((width - 2) % 2) + '│')

        lines.append('└' + '─' * (width - 2) + '┘')

        return '\n'.join(lines)

    def _create_fallback_preview(self, image_path: Path) -> str:
        """Create fallback preview when image rendering fails"""
        try:
            stat = image_path.stat()
            size_mb = stat.st_size / (1024 * 1024)

            return f"""┌─ 🖼️  IMAGE FILE ─┐
│ Name: {image_path.name[:20]}
│ Size: {size_mb:.1f} MB
│ Type: {image_path.suffix.upper()}
│
│ [Preview not available]
│ Try installing: chafa, viu,
│ catimg, or PIL for better
│ image preview support
└─────────────────────┘"""

        except Exception:
            return f"""┌─ 🖼️  IMAGE FILE ─┐
│ {image_path.name[:20]}
│ [Cannot read file]
└─────────────────────┘"""


class TerminalVideoRenderer:
    """Renders video previews in terminal"""

    def __init__(self):
        self.logger = Logger("TerminalVideoRenderer")
        self.image_renderer = TerminalImageRenderer()

        # Check for video tools
        self.ffmpeg_available = shutil.which('ffmpeg') is not None
        self.ffprobe_available = shutil.which('ffprobe') is not None

    def render_video_preview(self, video_path: Path, width: int = 40, height: int = 20) -> str:
        """Render video preview with thumbnail and metadata"""
        try:
            # Extract metadata
            metadata = self._extract_video_metadata(video_path)

            # Try to extract thumbnail
            thumbnail_path = None
            if self.ffmpeg_available:
                thumbnail_path = self._extract_video_thumbnail(video_path)

            # Create preview content
            lines = []

            # Title
            lines.append("🎬 VIDEO PREVIEW")
            lines.append("─" * width)

            # Video thumbnail
            if thumbnail_path and thumbnail_path.exists():
                try:
                    thumbnail_preview = self.image_renderer.render_image(
                        thumbnail_path, width - 2, height - 10
                    )
                    lines.extend(thumbnail_preview.split('\n'))
                    # Clean up temporary thumbnail
                    thumbnail_path.unlink()
                except Exception as e:
                    self.logger.error(f"Error rendering video thumbnail: {e}")
                    lines.extend(self._create_video_placeholder(width - 2, height - 10))
            else:
                lines.extend(self._create_video_placeholder(width - 2, height - 10))

            lines.append("─" * width)

            # Metadata
            if metadata:
                lines.append(f"📁 {video_path.name[:width-4]}")
                if 'duration' in metadata:
                    lines.append(f"⏱️  {metadata['duration']}")
                if 'resolution' in metadata:
                    lines.append(f"📐 {metadata['resolution']}")
                if 'format' in metadata:
                    lines.append(f"🎞️  {metadata['format']}")
                if 'size' in metadata:
                    lines.append(f"💾 {metadata['size']}")
            else:
                lines.append(f"📁 {video_path.name}")
                lines.append("⚠️  Metadata unavailable")

            return '\n'.join(lines)

        except Exception as e:
            self.logger.error(f"Error creating video preview: {e}")
            return self._create_fallback_video_preview(video_path, width)

    def _extract_video_metadata(self, video_path: Path) -> Dict[str, str]:
        """Extract video metadata using ffprobe"""
        if not self.ffprobe_available:
            return {}

        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(video_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)

                metadata = {}

                # Get format info
                if 'format' in data:
                    format_info = data['format']
                    if 'duration' in format_info:
                        duration = float(format_info['duration'])
                        metadata['duration'] = self._format_duration(duration)
                    if 'size' in format_info:
                        size = int(format_info['size'])
                        metadata['size'] = self._format_size(size)
                    if 'format_long_name' in format_info:
                        metadata['format'] = format_info['format_long_name']

                # Get video stream info
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        width = stream.get('width')
                        height = stream.get('height')
                        if width and height:
                            metadata['resolution'] = f"{width}x{height}"
                        break

                return metadata

        except Exception as e:
            self.logger.error(f"Error extracting video metadata: {e}")

        return {}

    def _extract_video_thumbnail(self, video_path: Path) -> Optional[Path]:
        """Extract thumbnail from video"""
        if not self.ffmpeg_available:
            return None

        try:
            # Create temporary file for thumbnail
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                thumbnail_path = Path(tmp.name)

            cmd = [
                'ffmpeg', '-i', str(video_path), '-ss', '00:00:05',
                '-vframes', '1', '-q:v', '2', str(thumbnail_path), '-y'
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 and thumbnail_path.exists():
                return thumbnail_path
            else:
                # Clean up failed thumbnail
                if thumbnail_path.exists():
                    thumbnail_path.unlink()
                return None

        except Exception as e:
            self.logger.error(f"Error extracting video thumbnail: {e}")
            return None

    def _create_video_placeholder(self, width: int, height: int) -> List[str]:
        """Create video placeholder when thumbnail extraction fails"""
        lines = []
        for i in range(height):
            if i == height // 2:
                # Center play button
                play_symbol = " ▶️  PLAY "
                padding = (width - len(play_symbol)) // 2
                line = "▓" * padding + play_symbol + "▓" * (width - padding - len(play_symbol))
            else:
                # Create pattern
                if i % 2 == 0:
                    line = "▓▒" * (width // 2) + "▓" * (width % 2)
                else:
                    line = "▒▓" * (width // 2) + "▒" * (width % 2)
            lines.append(line)
        return lines

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def _format_size(self, bytes_size: int) -> str:
        """Format file size in human-readable format"""
        size = float(bytes_size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _create_fallback_video_preview(self, video_path: Path, width: int) -> str:
        """Create fallback video preview"""
        try:
            stat = video_path.stat()
            size_mb = stat.st_size / (1024 * 1024)

            return f"""┌─ 🎬 VIDEO FILE {"─" * (width-15)}┐
│ Name: {video_path.name[:width-8]}
│ Size: {size_mb:.1f} MB
│ Type: {video_path.suffix.upper()}
│
│ [Preview not available]
│ Try installing ffmpeg for
│ better video preview support
└{"─" * (width-2)}┘"""

        except Exception:
            return f"""┌─ 🎬 VIDEO FILE ─┐
│ {video_path.name[:width-4]}
│ [Cannot read file]
└{"─" * (width-2)}┘"""


# Global instances
terminal_image_renderer = TerminalImageRenderer()
terminal_video_renderer = TerminalVideoRenderer()
