"""
Media Preview Renderer

This module provides preview capabilities for images, videos, and audio files
with metadata extraction and thumbnail generation.
"""

import base64
import io
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import mimetypes

from .preview_system import BasePreviewRenderer, PreviewResult, PreviewType, PreviewConfig
from ..utils.logger import Logger
from .terminal_media import terminal_image_renderer, terminal_video_renderer


class MediaPreviewRenderer(BasePreviewRenderer):
    """Renderer for media files (images, videos, audio)"""

    def __init__(self, config: PreviewConfig):
        super().__init__(config)

        # Check for optional dependencies
        self.pil_available = False
        self.opencv_available = False
        self.mutagen_available = False

        try:
            from PIL import Image, ImageOps, ExifTags
            self.PIL_Image = Image
            self.PIL_ImageOps = ImageOps
            self.PIL_ExifTags = ExifTags
            self.pil_available = True
        except ImportError:
            self.logger.warning("PIL/Pillow not available, image preview limited")

        try:
            import cv2
            self.cv2 = cv2
            self.opencv_available = True
        except ImportError:
            self.logger.warning("OpenCV not available, video preview limited")

        try:
            from mutagen import File as MutagenFile
            from mutagen.id3 import ID3NoHeaderError
            self.MutagenFile = MutagenFile
            self.ID3NoHeaderError = ID3NoHeaderError
            self.mutagen_available = True
        except ImportError:
            self.logger.warning("Mutagen not available, audio metadata limited")

        # Supported formats
        self.image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
            '.webp', '.svg', '.ico', '.psd', '.raw', '.cr2', '.nef'
        }

        self.video_extensions = {
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            '.m4v', '.3gp', '.ogv', '.mpg', '.mpeg', '.ts', '.mts'
        }

        self.audio_extensions = {
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
            '.opus', '.ape', '.ac3', '.dts', '.amr'
        }

    def can_preview(self, file_path: Path) -> bool:
        """Check if file is a media file"""
        extension = file_path.suffix.lower()
        return (extension in self.image_extensions or
                extension in self.video_extensions or
                extension in self.audio_extensions)

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return list(self.image_extensions | self.video_extensions | self.audio_extensions)

    def get_preview_type(self, file_path: Path) -> PreviewType:
        """Get preview type for file"""
        extension = file_path.suffix.lower()
        if extension in self.image_extensions:
            return PreviewType.IMAGE
        elif extension in self.video_extensions:
            return PreviewType.VIDEO
        elif extension in self.audio_extensions:
            return PreviewType.AUDIO
        return PreviewType.UNKNOWN

    async def generate_preview(self, file_path: Path) -> PreviewResult:
        """Generate media preview"""
        start_time = time.time()

        try:
            if self._is_file_too_large(file_path):
                return self._create_error_result(file_path, "File too large for preview")

            extension = file_path.suffix.lower()

            if extension in self.image_extensions:
                return await self._generate_image_preview(file_path, start_time)
            elif extension in self.video_extensions:
                return await self._generate_video_preview(file_path, start_time)
            elif extension in self.audio_extensions:
                return await self._generate_audio_preview(file_path, start_time)
            else:
                return self._create_error_result(file_path, "Unsupported media format")

        except Exception as e:
            self.logger.error(f"Error generating media preview for {file_path}: {e}")
            return self._create_error_result(file_path, str(e))

    async def _generate_image_preview(self, file_path: Path, start_time: float) -> PreviewResult:
        """Gte image preview"""
        try:
            metadata = {}
            content = ""
            thumbnail = None

            # Basic file info
            stat = file_path.stat()
            metadata.update({
                'file_size': stat.st_size,
                'mime_type': mimetypes.guess_type(str(file_path))[0],
                'format': file_path.suffix.upper().lstrip('.')
            })

            if self.pil_available:
                try:
                    with self.PIL_Image.open(file_path) as img:
                        # Basic image info
                        metadata.update({
                            'width': img.width,
                            'height': img.height,
                            'mode': img.mode,
                            'format': img.format,
                            'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                        })

                        # Extract EXIF data
                        exif_data = self._extract_exif_data(img)
                        if exif_data:
                            metadata['exif'] = exif_data

                        # Generate thumbnail
                        if self.config.enable_thumbnails:
                            thumbnail = self._generate_image_thumbnail(img)

                        # Create text representation with terminal rendering
                        terminal_preview = terminal_image_renderer.render_image(
                            file_path, width=60, height=20
                        )
                        content = f"{terminal_preview}\n\n{self._create_image_text_preview(file_path, metadata)}"

                except Exception as e:
                    self.logger.error(f"PIL error processing {file_path}: {e}")
                    content = f"Image file: {file_path.name}\nError: Could not process image - {e}"
            else:
                content = f"Image file: {file_path.name}\n(PIL not available for detailed preview)"

            return PreviewResult(
                file_path=file_path,
                preview_type=PreviewType.IMAGE,
                content=content,
                metadata=metadata,
                thumbnail=thumbnail,
                generation_time=time.time() - start_time
            )

        except Exception as e:
            return self._create_error_result(file_path, str(e))

    async def _generate_video_preview(self, file_path: Path, start_time: float) -> PreviewResult:
        """Generate video preview"""
        try:
            metadata = {}
            content = ""
            thumbnail = None

            # Basic file info
            stat = file_path.stat()
            metadata.update({
                'file_size': stat.st_size,
                'mime_type': mimetypes.guess_type(str(file_path))[0],
                'format': file_path.suffix.upper().lstrip('.')
            })

            if self.opencv_available:
                try:
                    cap = self.cv2.VideoCapture(str(file_path))

                    if cap.isOpened():
                        # Extract video properties
                        fps = cap.get(self.cv2.CAP_PROP_FPS)
                        frame_count = int(cap.get(self.cv2.CAP_PROP_FRAME_COUNT))
                        width = int(cap.get(self.cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(self.cv2.CAP_PROP_FRAME_HEIGHT))

                        duration = frame_count / fps if fps > 0 else 0

                        metadata.update({
                            'width': width,
                            'height': height,
                            'fps': fps,
                            'frame_count': frame_count,
                            'duration': duration,
                            'duration_formatted': self._format_duration(duration)
                        })

                        # Generate thumbnail from video
                        if self.config.enable_thumbnails:
                            thumbnail = self._generate_video_thumbnail(cap, fps)

                        cap.release()

                    # Create text representation with terminal rendering
                    terminal_preview = terminal_video_renderer.render_video_preview(
                        file_path, width=60, height=20
                    )
                    content = f"{terminal_preview}\n\n{self._create_video_text_preview(file_path, metadata)}"

                except Exception as e:
                    self.logger.error(f"OpenCV error processing {file_path}: {e}")
                    content = f"Video file: {file_path.name}\nError: Could not process video - {e}"
            else:
                content = f"Video file: {file_path.name}\n(OpenCV not available for detailed preview)"

            return PreviewResult(
                file_path=file_path,
                preview_type=PreviewType.VIDEO,
                content=content,
                metadata=metadata,
                thumbnail=thumbnail,
                generation_time=time.time() - start_time
            )

        except Exception as e:
            return self._create_error_result(file_path, str(e))

    async def _generate_audio_preview(self, file_path: Path, start_time: float) -> PreviewResult:
        """Generate audio preview"""
        try:
            metadata = {}
            content = ""

            # Basic file info
            stat = file_path.stat()
            metadata.update({
                'file_size': stat.st_size,
                'mime_type': mimetypes.guess_type(str(file_path))[0],
                'format': file_path.suffix.upper().lstrip('.')
            })

            if self.mutagen_available:
                try:
                    audio_file = self.MutagenFile(file_path)

                    if audio_file is not None:
                        # Extract audio properties
                        if hasattr(audio_file, 'info'):
                            info = audio_file.info
                            metadata.update({
                                'duration': getattr(info, 'length', 0),
                                'duration_formatted': self._format_duration(getattr(info, 'length', 0)),
                                'bitrate': getattr(info, 'bitrate', 0),
                                'sample_rate': getattr(info, 'sample_rate', 0),
                                'channels': getattr(info, 'channels', 0)
                            })

                        # Extract tags/metadata
                        tags = {}
                        if audio_file.tags:
                            # Common tags
                            tag_mapping = {
                                'TIT2': 'title',
                                'TPE1': 'artist',
                                'TALB': 'album',
                                'TDRC': 'date',
                                'TCON': 'genre',
                                'TRCK': 'track',
                                'TPE2': 'album_artist'
                            }

                            for tag_key, tag_name in tag_mapping.items():
                                if tag_key in audio_file.tags:
                                    tags[tag_name] = str(audio_file.tags[tag_key][0])

                            # Also try common tag names
                            common_tags = ['title', 'artist', 'album', 'date', 'genre', 'track']
                            for tag in common_tags:
                                if tag in audio_file.tags and tag not in tags:
                                    tags[tag] = str(audio_file.tags[tag][0])

                        if tags:
                            metadata['tags'] = tags

                    content = self._create_audio_text_preview(file_path, metadata)

                except Exception as e:
                    self.logger.error(f"Mutagen error processing {file_path}: {e}")
                    content = f"Audio file: {file_path.name}\nError: Could not process audio - {e}"
            else:
                content = f"Audio file: {file_path.name}\n(Mutagen not available for detailed preview)"

            return PreviewResult(
                file_path=file_path,
                preview_type=PreviewType.AUDIO,
                content=content,
                metadata=metadata,
                generation_time=time.time() - start_time
            )

        except Exception as e:
            return self._create_error_result(file_path, str(e))

    def _extract_exif_data(self, img) -> Optional[Dict[str, Any]]:
        """Extract EXIF data from image"""
        try:
            exif_dict = {}

            if hasattr(img, '_getexif'):
                exif = img._getexif()
                if exif is not None:
                    for tag_id, value in exif.items():
                        tag = self.PIL_ExifTags.TAGS.get(tag_id, tag_id)

                        # Convert bytes to string for some tags
                        if isinstance(value, bytes):
                            try:
                                value = value.decode('utf-8', errors='ignore')
                            except:
                                value = str(value)

                        exif_dict[tag] = value

            return exif_dict if exif_dict else None

        except Exception as e:
            self.logger.error(f"Error extracting EXIF data: {e}")
            return None

    def _generate_image_thumbnail(self, img) -> Optional[str]:
        """Generate base64 encoded thumbnail for image"""
        try:
            # Create thumbnail
            thumbnail_size = (self.config.image_max_width, self.config.image_max_height)
            img_copy = img.copy()

            # Convert to RGB if necessary
            if img_copy.mode in ('RGBA', 'LA', 'P'):
                img_copy = img_copy.convert('RGB')

            # Generate thumbnail
            img_copy.thumbnail(thumbnail_size, self.PIL_Image.Resampling.LANCZOS)

            # Save to bytes
            buffer = io.BytesIO()
            img_copy.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)

            # Encode to base64
            thumbnail_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/jpeg;base64,{thumbnail_b64}"

        except Exception as e:
            self.logger.error(f"Error generating image thumbnail: {e}")
            return None

    def _generate_video_thumbnail(self, cap, fps: float) -> Optional[str]:
        """Generate thumbnail from video"""
        try:
            # Seek to thumbnail time (default 5 seconds)
            frame_number = int(fps * self.config.video_thumbnail_time)
            cap.set(self.cv2.CAP_PROP_POS_FRAMES, frame_number)

            ret, frame = cap.read()
            if not ret:
                # Try first frame if seeking failed
                cap.set(self.cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()

                if not ret:
                    return None

            # Convert BGR to RGB
            frame_rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)

            # Convert to PIL Image
            if self.pil_available:
                img = self.PIL_Image.fromarray(frame_rgb)
                return self._generate_image_thumbnail(img)

            return None

        except Exception as e:
            self.logger.error(f"Error generating video thumbnail: {e}")
            return None

    def _create_image_text_preview(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        """Create text preview for image"""
        lines = [
            f"📷 Image: {file_path.name}",
            f"Format: {metadata.get('format', 'Unknown')}",
            f"Size: {self._format_file_size(metadata.get('file_size', 0))}"
        ]

        if 'width' in metadata and 'height' in metadata:
            lines.append(f"Dimensions: {metadata['width']} × {metadata['height']} pixels")

        if 'mode' in metadata:
            lines.append(f"Color Mode: {metadata['mode']}")

        if metadata.get('has_transparency'):
            lines.append("✓ Has transparency")

        # EXIF data
        if 'exif' in metadata:
            exif = metadata['exif']
            lines.append("\n📋 EXIF Data:")

            # Show important EXIF fields
            important_fields = [
                ('Make', 'Camera Make'),
                ('Model', 'Camera Model'),
                ('DateTime', 'Date Taken'),
                ('ExposureTime', 'Exposure Time'),
                ('FNumber', 'F-Number'),
                ('ISOSpeedRatings', 'ISO'),
                ('FocalLength', 'Focal Length'),
                ('Flash', 'Flash'),
                ('Orientation', 'Orientation')
            ]

            for exif_key, display_name in important_fields:
                if exif_key in exif:
                    value = exif[exif_key]
                    lines.append(f"  {display_name}: {value}")

        return '\n'.join(lines)

    def _create_video_text_preview(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        """Create text preview for video"""
        lines = [
            f"🎬 Video: {file_path.name}",
            f"Format: {metadata.get('format', 'Unknown')}",
            f"Size: {self._format_file_size(metadata.get('file_size', 0))}"
        ]

        if 'width' in metadata and 'height' in metadata:
            lines.append(f"Resolution: {metadata['width']} × {metadata['height']}")

        if 'duration_formatted' in metadata:
            lines.append(f"Duration: {metadata['duration_formatted']}")

        if 'fps' in metadata:
            lines.append(f"Frame Rate: {metadata['fps']:.2f} fps")

        if 'frame_count' in metadata:
            lines.append(f"Total Frames: {metadata['frame_count']:,}")

        return '\n'.join(lines)

    def _create_audio_text_preview(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        """Create text preview for audio"""
        lines = [
            f"🎵 Audio: {file_path.name}",
            f"Format: {metadata.get('format', 'Unknown')}",
            f"Size: {self._format_file_size(metadata.get('file_size', 0))}"
        ]

        if 'duration_formatted' in metadata:
            lines.append(f"Duration: {metadata['duration_formatted']}")

        if 'bitrate' in metadata and metadata['bitrate'] > 0:
            lines.append(f"Bitrate: {metadata['bitrate']} kbps")

        if 'sample_rate' in metadata and metadata['sample_rate'] > 0:
            lines.append(f"Sample Rate: {metadata['sample_rate']} Hz")

        if 'channels' in metadata and metadata['channels'] > 0:
            channel_text = "Mono" if metadata['channels'] == 1 else f"{metadata['channels']} channels"
            lines.append(f"Channels: {channel_text}")

        # Tags/metadata
        if 'tags' in metadata:
            tags = metadata['tags']
            lines.append("\n🏷️ Tags:")

            tag_order = ['title', 'artist', 'album', 'album_artist', 'date', 'genre', 'track']
            for tag in tag_order:
                if tag in tags:
                    lines.append(f"  {tag.title()}: {tags[tag]}")

        return '\n'.join(lines)

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human readable format"""
        if seconds <= 0:
            return "0:00"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"