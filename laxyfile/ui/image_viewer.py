"""
Advanced Media Viewer - Display images, videos, and code in terminal with modern methods
"""

import os
import sys
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from io import StringIO

# Image processing
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Video processing
try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

# Syntax highlighting
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, guess_lexer
    from pygments.formatters import TerminalFormatter, Terminal256Formatter
    from pygments.util import ClassNotFound
    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False

# Rich components
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich.columns import Columns
from rich.syntax import Syntax

class MediaViewer:
    """Advanced media viewer supporting images, videos, and code"""

    def __init__(self, console: Console):
        self.console = console
        self.terminal_size = shutil.get_terminal_size()
        self._detect_terminal_capabilities()

    def _detect_terminal_capabilities(self):
        """Detect what the terminal supports"""
        self.supports_sixel = self._check_sixel_support()
        self.supports_kitty = self._check_kitty_support()
        self.supports_iterm2 = self._check_iterm2_support()
        self.supports_unicode = self._check_unicode_support()
        self.supports_truecolor = self._check_truecolor_support()

    def _check_sixel_support(self) -> bool:
        """Check if terminal supports sixel graphics"""
        term = os.environ.get('TERM', '')
        term_program = os.environ.get('TERM_PROGRAM', '')
        return ('xterm' in term or 'mlterm' in term or
                term_program in ['WezTerm', 'foot'])

    def _check_kitty_support(self) -> bool:
        """Check if terminal supports Kitty graphics protocol"""
        return os.environ.get('TERM') == 'xterm-kitty'

    def _check_iterm2_support(self) -> bool:
        """Check if running in iTerm2"""
        return os.environ.get('TERM_PROGRAM') == 'iTerm.app'

    def _check_unicode_support(self) -> bool:
        """Check if terminal supports Unicode"""
        return os.environ.get('LANG', '').find('UTF') != -1

    def _check_truecolor_support(self) -> bool:
        """Check if terminal supports 24-bit colors"""
        return os.environ.get('COLORTERM') in ['truecolor', '24bit']

    def can_display_file(self, file_path: Path) -> bool:
        """Check if file can be displayed"""
        if not file_path.exists():
            return False

        # Images
        if self._is_image(file_path):
            return HAS_PIL

        # Videos
        if self._is_video(file_path):
            return HAS_OPENCV

        # Code/text files
        if self._is_text_file(file_path):
            return True

        return False

    def _is_image(self, file_path: Path) -> bool:
        """Check if file is an image"""
        image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
            '.svg', '.ico', '.tiff', '.tif', '.psd'
        }
        return file_path.suffix.lower() in image_extensions

    def _is_video(self, file_path: Path) -> bool:
        """Check if file is a video"""
        video_extensions = {
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv',
            '.webm', '.m4v', '.3gp', '.mpg', '.mpeg'
        }
        return file_path.suffix.lower() in video_extensions

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is a text/code file"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # Check if file contains mostly text
                text_chars = sum(1 for byte in chunk if 32 <= byte <= 126 or byte in [9, 10, 13])
                return text_chars / len(chunk) > 0.8 if chunk else True
        except:
            return False

    def display_file(self, file_path: Path, max_width: int = 80, max_height: int = 30) -> Panel:
        """Display file content in terminal"""
        try:
            if self._is_image(file_path):
                return self.display_image(file_path, max_width, max_height)
            elif self._is_video(file_path):
                return self.display_video_preview(file_path, max_width, max_height)
            elif self._is_text_file(file_path):
                return self.display_code(file_path, max_width, max_height)
            else:
                return self._create_unsupported_panel(file_path)

        except Exception as e:
            return self._create_error_panel(f"Error displaying file: {e}")

    def display_image(self, file_path: Path, max_width: int = 80, max_height: int = 30) -> Panel:
        """Display image with multiple fallback methods"""
        if not HAS_PIL:
            return self._create_error_panel("PIL not available for image display")

        try:
            # Try advanced display methods first
            if self.supports_kitty:
                return self._display_image_kitty(file_path, max_width, max_height)
            elif self.supports_sixel:
                return self._display_image_sixel(file_path, max_width, max_height)
            elif self.supports_iterm2:
                return self._display_image_iterm2(file_path, max_width, max_height)
            else:
                return self._display_image_ascii(file_path, max_width, max_height)

        except Exception as e:
            return self._create_error_panel(f"Image display failed: {e}")

    def _display_image_kitty(self, file_path: Path, max_width: int, max_height: int) -> Panel:
        """Display image using Kitty graphics protocol"""
        try:
            # For now, fall back to ASCII until we implement the protocol
            return self._display_image_ascii(file_path, max_width, max_height)
        except Exception as e:
            return self._display_image_ascii(file_path, max_width, max_height)

    def _display_image_sixel(self, file_path: Path, max_width: int, max_height: int) -> Panel:
        """Display image using Sixel graphics"""
        try:
            # For now, fall back to ASCII until we implement sixel
            return self._display_image_ascii(file_path, max_width, max_height)
        except Exception as e:
            return self._display_image_ascii(file_path, max_width, max_height)

    def _display_image_iterm2(self, file_path: Path, max_width: int, max_height: int) -> Panel:
        """Display image using iTerm2 inline images"""
        try:
            # For now, fall back to ASCII until we implement iTerm2 protocol
            return self._display_image_ascii(file_path, max_width, max_height)
        except Exception as e:
            return self._display_image_ascii(file_path, max_width, max_height)

    def _display_image_ascii(self, file_path: Path, max_width: int, max_height: int) -> Panel:
        """Display image as beautiful ASCII art with colors"""
        try:
            img = Image.open(file_path)

            # Resize image
            img = self._resize_image(img, max_width, max_height)

            # Convert to ASCII with colors
            ascii_art = self._image_to_colored_ascii(img, max_width, max_height)

            # Get image metadata
            metadata = self._get_image_metadata(file_path, img)

            content = Text()
            content.append(ascii_art)
            content.append("\n\n")
            content.append(metadata, style="dim cyan")

            return Panel(
                content,
                title=f"🖼️ {file_path.name}",
                border_style="#FF69B4",  # Hot pink
                padding=(1, 2)
            )

        except Exception as e:
            return self._create_error_panel(f"ASCII image display failed: {e}")

    def _image_to_colored_ascii(self, img: Image.Image, max_width: int, max_height: int) -> Text:
        """Convert image to clean Unicode block art for better preview"""
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Use Unicode block characters for cleaner look
        block_chars = {
            0: ' ',      # Empty
            1: '░',      # Light shade
            2: '▒',      # Medium shade
            3: '▓',      # Dark shade
            4: '█',      # Full block
        }

        width, height = img.size
        ascii_art = Text()

        # Process image in pairs for half-block rendering
        for y in range(0, height, 2):
            for x in range(width):
                # Get upper pixel
                upper_pixel = img.getpixel((x, y))
                if isinstance(upper_pixel, tuple):
                    r1, g1, b1 = upper_pixel[:3]
                else:
                    r1 = g1 = b1 = int(upper_pixel) if upper_pixel is not None else 0

                upper_brightness = int(0.299 * r1 + 0.587 * g1 + 0.114 * b1)

                # Get lower pixel (or use upper if at bottom)
                if y + 1 < height:
                    lower_pixel = img.getpixel((x, y + 1))
                    if isinstance(lower_pixel, tuple):
                        r2, g2, b2 = lower_pixel[:3]
                    else:
                        r2 = g2 = b2 = int(lower_pixel) if lower_pixel is not None else 0
                    lower_brightness = int(0.299 * r2 + 0.587 * g2 + 0.114 * b2)
                else:
                    r2, g2, b2 = r1, g1, b1
                    lower_brightness = upper_brightness

                # Use half-block characters for better density
                if upper_brightness > 128 and lower_brightness > 128:
                    char = '█'
                    color = f"#{r1:02x}{g1:02x}{b1:02x}"
                elif upper_brightness > 128:
                    char = '▀'
                    color = f"#{r1:02x}{g1:02x}{b1:02x}"
                elif lower_brightness > 128:
                    char = '▄'
                    color = f"#{r2:02x}{g2:02x}{b2:02x}"
                else:
                    char = ' '
                    color = "black"

                # Add colored character
                if self.supports_truecolor:
                    ascii_art.append(char, style=color)
                else:
                    # Fallback to simple block chars without color
                    brightness_avg = (upper_brightness + lower_brightness) // 2
                    block_index = min(4, brightness_avg // 51)  # 0-4 range
                    ascii_art.append(block_chars[block_index])

            if y < height - 2:
                ascii_art.append("\n")

        return ascii_art

    def _resize_image(self, img: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """Resize image maintaining aspect ratio with better terminal character handling"""
        width, height = img.size
        aspect_ratio = width / height

        # Account for terminal character aspect ratio (roughly 2:1 height/width)
        # Adjust max_height to compensate for character dimensions
        adjusted_max_height = max_height * 2

        # Calculate new dimensions
        if width > max_width:
            new_width = max_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_width = width
            new_height = height

        if new_height > adjusted_max_height:
            new_height = adjusted_max_height
            new_width = int(new_height * aspect_ratio)

        # Ensure minimum size for visible preview
        new_width = max(10, min(new_width, max_width))
        new_height = max(5, min(new_height, adjusted_max_height))

        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _get_image_metadata(self, file_path: Path, img: Image.Image) -> str:
        """Get detailed image metadata"""
        file_size = file_path.stat().st_size
        size_str = self._format_file_size(file_size)

        metadata = f"Resolution: {img.width}x{img.height} | "
        metadata += f"Format: {img.format or 'Unknown'} | "
        metadata += f"Mode: {img.mode} | "
        metadata += f"File Size: {size_str}"

        return metadata

    def display_video_preview(self, file_path: Path, max_width: int = 80, max_height: int = 30) -> Panel:
        """Display video thumbnail and metadata"""
        if not HAS_OPENCV:
            return self._create_error_panel("OpenCV not available for video preview")

        try:
            # Get video metadata
            metadata = self._get_video_metadata(file_path)

            # Extract thumbnail
            thumbnail = self._extract_video_thumbnail(file_path)

            content = Text()

            if thumbnail:
                # Convert thumbnail to ASCII
                ascii_thumb = self._image_to_colored_ascii(thumbnail, max_width//2, max_height//2)
                content.append(ascii_thumb)
                content.append("\n\n")

            # Add metadata
            content.append("📊 Video Information:\n", style="bold cyan")
            for key, value in metadata.items():
                content.append(f"  {key}: ", style="dim")
                content.append(f"{value}\n", style="white")

            return Panel(
                content,
                title=f"🎬 {file_path.name}",
                border_style="#FF4500",  # Orange red
                padding=(1, 2)
            )

        except Exception as e:
            return self._create_error_panel(f"Video preview failed: {e}")

    def _extract_video_thumbnail(self, file_path: Path) -> Optional[Image.Image]:
        """Extract thumbnail from video"""
        try:
            cap = cv2.VideoCapture(str(file_path))

            # Go to 10% into the video for thumbnail
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 10)

            ret, frame = cap.read()
            cap.release()

            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return Image.fromarray(frame_rgb)

            return None

        except Exception:
            return None

    def _get_video_metadata(self, file_path: Path) -> Dict[str, str]:
        """Get video metadata"""
        try:
            cap = cv2.VideoCapture(str(file_path))

            if not cap.isOpened():
                return {"Error": "Cannot open video file"}

            metadata = {
                "Duration": self._format_duration(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)),
                "Resolution": f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}",
                "FPS": f"{cap.get(cv2.CAP_PROP_FPS):.2f}",
                "Frames": f"{int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}",
                "File Size": self._format_file_size(file_path.stat().st_size)
            }

            cap.release()
            return metadata

        except Exception as e:
            return {"Error": str(e)}

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def display_code(self, file_path: Path, max_width: int = 80, max_height: int = 30) -> Panel:
        """Display code with syntax highlighting"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Limit content size for display
            lines = content.split('\n')
            if len(lines) > max_height:
                content = '\n'.join(lines[:max_height])
                truncated = True
            else:
                truncated = False

            # Get file extension for syntax highlighting
            file_ext = file_path.suffix.lower()

            # Create syntax highlighted content
            if HAS_PYGMENTS:
                highlighted_content = self._highlight_with_pygments(content, file_path)
            else:
                # Fallback to Rich syntax highlighting
                highlighted_content = self._highlight_with_rich(content, file_ext)

            # Add metadata
            metadata_text = Text()
            metadata_text.append(f"📊 Lines: {len(lines)} | ", style="dim")
            metadata_text.append(f"Size: {self._format_file_size(file_path.stat().st_size)} | ", style="dim")
            metadata_text.append(f"Type: {file_ext or 'text'}", style="dim")

            if truncated:
                metadata_text.append(" | Truncated", style="dim red")

            # Combine content
            final_content = Text()
            final_content.append(highlighted_content)
            final_content.append("\n\n")
            final_content.append(metadata_text)

            return Panel(
                final_content,
                title=f"💻 {file_path.name}",
                border_style="#32CD32",  # Lime green
                padding=(1, 2)
            )

        except Exception as e:
            return self._create_error_panel(f"Code display failed: {e}")

    def _highlight_with_pygments(self, content: str, file_path: Path) -> Text:
        """Highlight code using Pygments"""
        try:
            # Try to get lexer by filename first
            try:
                lexer = get_lexer_for_filename(file_path.name)
            except ClassNotFound:
                # Fallback to guessing
                try:
                    lexer = guess_lexer(content)
                except ClassNotFound:
                    lexer = get_lexer_by_name('text')

            # Use 256-color formatter for better terminal support
            formatter = Terminal256Formatter(style='monokai')
            highlighted = highlight(content, lexer, formatter)

            return Text.from_ansi(highlighted)

        except Exception:
            return Text(content, style="white")

    def _highlight_with_rich(self, content: str, file_ext: str) -> Text:
        """Highlight code using Rich syntax"""
        try:
            # Map extensions to lexer names
            lexer_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.html': 'html',
                '.css': 'css',
                '.json': 'json',
                '.yaml': 'yaml',
                '.yml': 'yaml',
                '.xml': 'xml',
                '.sql': 'sql',
                '.sh': 'bash',
                '.bash': 'bash',
                '.zsh': 'bash',
                '.cpp': 'cpp',
                '.c': 'c',
                '.h': 'c',
                '.java': 'java',
                '.rs': 'rust',
                '.go': 'go',
                '.php': 'php',
                '.rb': 'ruby',
                '.swift': 'swift',
                '.kt': 'kotlin'
            }

            lexer_name = lexer_map.get(file_ext, 'text')

            # Create syntax object
            syntax = Syntax(content, lexer_name, theme="monokai", line_numbers=True)

            # Convert to text (this is a simplified approach)
            return Text(content, style="white")

        except Exception:
            return Text(content, style="white")

    def _format_file_size(self, size: int) -> str:
        """Format file size in human readable format"""
        size_float = float(size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_float < 1024.0:
                return f"{size_float:.1f} {unit}"
            size_float /= 1024.0
        return f"{size_float:.1f} PB"

    def _create_error_panel(self, message: str) -> Panel:
        """Create error panel"""
        return Panel(
            Align.center(Text(message, style="red")),
            title="❌ Viewer Error",
            border_style="red"
        )

    def _create_unsupported_panel(self, file_path: Path) -> Panel:
        """Create panel for unsupported files"""
        file_info = f"File: {file_path.name}\n"
        file_info += f"Size: {self._format_file_size(file_path.stat().st_size)}\n"
        file_info += f"Type: {file_path.suffix or 'No extension'}"

        return Panel(
            Align.center(Text(file_info, style="yellow")),
            title="⚠️ Unsupported File Type",
            border_style="yellow"
        )

    def create_preview_panel(self, file_path: Path, max_width: int = 40, max_height: int = 15) -> Panel:
        """Create a small preview panel for the sidebar"""
        try:
            if self._is_image(file_path) and HAS_PIL:
                return self._create_image_preview(file_path, max_width, max_height)
            elif self._is_video(file_path) and HAS_OPENCV:
                return self._create_video_preview(file_path, max_width, max_height)
            elif self._is_text_file(file_path):
                return self._create_text_preview(file_path, max_width, max_height)
            else:
                return self._create_file_info_preview(file_path)

        except Exception as e:
            return Panel(
                Align.center(Text("Preview failed", style="red")),
                title="Preview",
                border_style="red"
            )

    def _create_image_preview(self, file_path: Path, max_width: int, max_height: int) -> Panel:
        """Create enhanced image preview with multiple rendering methods"""
        try:
            img = Image.open(file_path)

            # Use more space for better preview - don't divide by 2
            preview_width = max_width - 4  # Account for panel borders
            preview_height = max_height - 4  # Account for panel borders and info line

            # Try different rendering methods based on terminal capabilities
            if shutil.which('chafa'):
                # Use chafa for best quality terminal image display
                content = self._create_chafa_preview(file_path, preview_width, preview_height)
            elif self.supports_kitty:
                # Kitty graphics protocol (best quality)
                content = self._create_kitty_image_preview(img, file_path, preview_width, preview_height)
            elif self.supports_sixel:
                # Sixel graphics (good quality)
                content = self._create_sixel_image_preview(img, file_path, preview_width, preview_height)
            else:
                # Fallback to enhanced ASCII art
                content = self._create_enhanced_ascii_preview(img, file_path, preview_width, preview_height)

            return Panel(
                content,
                title="🖼️ Preview",
                border_style="magenta"
            )

        except Exception as e:
            # Fallback to file info if image processing fails
            return self._create_file_info_preview(file_path)

    def _create_chafa_preview(self, file_path: Path, preview_width: int, preview_height: int) -> Text:
        """Create preview using chafa (best terminal image viewer)"""
        try:
            # Use conservative sizing to fit the preview panel properly
            # Subtract padding to account for panel borders and ensure clean fit
            actual_width = max(20, preview_width - 4)  # Account for panel padding
            actual_height = max(10, preview_height - 2)  # Account for panel padding

            # Run chafa with high-quality settings optimized for terminal panels
            cmd = [
                'chafa',
                '--size', f'{actual_width}x{actual_height}',
                '--format', 'symbols',
                '--symbols', 'block+border+space+solid+stipple+geometric',
                '--color-extractor', 'average',
                '--color-space', 'rgb',
                '--dither', 'bayer',
                '--dither-grain', '2',  # Balanced dithering
                '--optimize', '8',      # High optimization
                '--work', '8',          # High work factor
                '--stretch',            # Allow stretching for better fit
                '--animate', 'off',
                str(file_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and result.stdout:
                # Get original image info
                original_img = Image.open(file_path)
                info = f"\n{original_img.width}x{original_img.height} • {original_img.format or 'Unknown'}"

                # Create Rich Text object and use from_ansi to properly handle escape codes
                content = Text.from_ansi(result.stdout.rstrip())
                content.append(info, style="dim cyan")
                return content
            else:
                # Fallback if chafa fails
                img = Image.open(file_path)
                return self._create_enhanced_ascii_preview(img, file_path, preview_width, preview_height)

        except Exception:
            # Fallback if chafa fails
            img = Image.open(file_path)
            return self._create_enhanced_ascii_preview(img, file_path, preview_width, preview_height)

    def _create_enhanced_ascii_preview(self, img: Image.Image, file_path: Path, preview_width: int, preview_height: int) -> Text:
        """Create enhanced ASCII art preview with better colors and characters"""
        # Resize image
        resized_img = self._resize_image(img, preview_width, preview_height)

        # Convert to RGB if needed
        if resized_img.mode != 'RGB':
            resized_img = resized_img.convert('RGB')

        width, height = resized_img.size
        content = Text()

        # Enhanced character set for better detail
        density_chars = [' ', '░', '▒', '▓', '█']
        block_chars = ['▀', '▄', '█', '▌', '▐', '┌', '┐', '└', '┘']

        # Process image using half-block method for better detail
        for y in range(0, height, 2):
            for x in range(width):
                # Get upper pixel
                upper_pixel = resized_img.getpixel((x, y))
                if isinstance(upper_pixel, (tuple, list)) and len(upper_pixel) >= 3:
                    r1, g1, b1 = upper_pixel[:3]
                elif isinstance(upper_pixel, (int, float)):
                    r1 = g1 = b1 = int(upper_pixel)
                else:
                    r1 = g1 = b1 = 0

                upper_brightness = int(0.299 * r1 + 0.587 * g1 + 0.114 * b1)

                # Get lower pixel (or duplicate upper if at bottom)
                if y + 1 < height:
                    lower_pixel = resized_img.getpixel((x, y + 1))
                    if isinstance(lower_pixel, (tuple, list)) and len(lower_pixel) >= 3:
                        r2, g2, b2 = lower_pixel[:3]
                    elif isinstance(lower_pixel, (int, float)):
                        r2 = g2 = b2 = int(lower_pixel)
                    else:
                        r2 = g2 = b2 = 0
                    lower_brightness = int(0.299 * r2 + 0.587 * g2 + 0.114 * b2)
                else:
                    r2, g2, b2 = r1, g1, b1
                    lower_brightness = upper_brightness

                # Choose character and color based on brightness levels
                if self.supports_truecolor:
                    # Use half-block characters with true color for better quality
                    if upper_brightness > 128 and lower_brightness > 128:
                        char = '█'
                        color = f"rgb({r1},{g1},{b1})"
                    elif upper_brightness > 128:
                        char = '▀'
                        color = f"rgb({r1},{g1},{b1})"
                    elif lower_brightness > 128:
                        char = '▄'
                        color = f"rgb({r2},{g2},{b2})"
                    elif upper_brightness > 64 or lower_brightness > 64:
                        char = '░'
                        avg_r, avg_g, avg_b = (r1 + r2) // 2, (g1 + g2) // 2, (b1 + b2) // 2
                        color = f"rgb({avg_r},{avg_g},{avg_b})"
                    else:
                        char = ' '
                        color = "black"

                    content.append(char, style=color)
                else:
                    # Fallback to density-based characters without color
                    avg_brightness = (upper_brightness + lower_brightness) // 2
                    char_index = min(len(density_chars) - 1, avg_brightness // 51)
                    content.append(density_chars[char_index])

            # Add newline except for last row
            if y < height - 2:
                content.append("\n")

        # Add image info
        original_img = Image.open(file_path)
        info = f"\n{original_img.width}x{original_img.height} • {original_img.format or 'Unknown'}"
        content.append(info, style="dim cyan")

        return content

    def _create_kitty_image_preview(self, img: Image.Image, file_path: Path, preview_width: int, preview_height: int) -> Text:
        """Create preview using Kitty graphics protocol (if available)"""
        # For now, fallback to ASCII since Kitty protocol is complex
        # This can be implemented later with proper Kitty graphics support
        return self._create_enhanced_ascii_preview(img, file_path, preview_width, preview_height)

    def _create_sixel_image_preview(self, img: Image.Image, file_path: Path, preview_width: int, preview_height: int) -> Text:
        """Create preview using Sixel graphics (if available)"""
        # For now, fallback to ASCII since Sixel requires additional dependencies
        # This can be implemented later with proper Sixel support
        return self._create_enhanced_ascii_preview(img, file_path, preview_width, preview_height)

    def _create_video_preview(self, file_path: Path, max_width: int, max_height: int) -> Panel:
        """Create small video preview"""
        try:
            metadata = self._get_video_metadata(file_path)

            content = Text()
            content.append("🎬 Video\n", style="bold orange")
            content.append(f"{metadata.get('Resolution', 'Unknown')}\n", style="dim")
            content.append(f"{metadata.get('Duration', 'Unknown')}", style="dim")

            return Panel(
                content,
                title="🎬 Preview",
                border_style="red"
            )

        except Exception:
            return self._create_file_info_preview(file_path)

    def _create_text_preview(self, file_path: Path, max_width: int, max_height: int) -> Panel:
        """Create small text/code preview"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[:5]  # First 5 lines

            content = Text()
            for line in lines:
                content.append(line.rstrip()[:max_width-4] + "\n", style="dim white")

            return Panel(
                content,
                title="📄 Preview",
                border_style="green"
            )

        except Exception:
            return self._create_file_info_preview(file_path)

    def _create_file_info_preview(self, file_path: Path) -> Panel:
        """Create basic file info preview"""
        try:
            size = self._format_file_size(file_path.stat().st_size)
            ext = file_path.suffix or "No ext"

            content = Text()
            content.append(f"📄 {ext}\n", style="bold")
            content.append(f"Size: {size}", style="dim")

            return Panel(
                content,
                title="ℹ️ Info",
                border_style="blue"
            )

        except Exception:
            return Panel(
                Align.center(Text("No info", style="dim")),
                title="Info",
                border_style="dim"
            )