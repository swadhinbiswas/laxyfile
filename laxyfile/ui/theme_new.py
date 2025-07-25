"""
Enhanced Theme System

This module provides a comprehensive theming system with SuperFile-inspired themes,
dynamic switching, customization, and theme management capabilities.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import hashlib
import colorsys

from ..core.exceptions import ThemeError, ConfigurationError
from ..utils.logger import Logger


class ColorFormat(Enum):
    """Supported color formats"""
    HEX = "hex"
    RGB = "rgb"
    HSL = "hsl"
    ANSI = "ansi"


class ThemeType(Enum):
    """Theme types"""
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"


@dataclass
class Color:
    """Represents a color with multiple format support"""
    hex: str
    rgb: tuple = field(default_factory=tuple)
    hsl: tuple = field(default_factory=tuple)
    ansi: int = 0

    def __post_init__(self):
        if self.hex and not self.rgb:
            self.rgb = self._hex_to_rgb(self.hex)
        if self.rgb and not self.hsl:
            self.hsl = self._rgb_to_hsl(self.rgb)
        if not self.ansi:
            self.ansi = self._rgb_to_ansi(self.rgb)

    @classmethod
    def from_hex(cls, hex_color: str) -> 'Color':
        """Create color from hex string"""
        return cls(hex=hex_color)

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> 'Color':
        """Create color from RGB values"""
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        return cls(hex=hex_color, rgb=(r, g, b))

    @classmethod
    def from_hsl(cls, h: float, s: float, l: float) -> 'Color':
        """Create color from HSL values"""
        rgb = cls._hsl_to_rgb((h, s, l))
        return cls.from_rgb(*rgb)

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex to RGBby
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hsl(self, rgb: tuple) -> tuple:
        """Convert RGB to HSL"""
        r, g, b = [x/255.0 for x in rgb]
        return colorsys.rgb_to_hls(r, g, b)

    @staticmethod
    def _hsl_to_rgb(hsl: tuple) -> tuple:
        """Convert HSL to RGB"""
        h, l, s = hsl  # Note: colorsys uses HLS order
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return tuple(int(x * 255) for x in (r, g, b))

    def _rgb_to_ansi(self, rgb: tuple) -> int:
        """Convert RGB to closest ANSI color"""
        # Simplified ANSI color mapping
        r, g, b = rgb

        # Standard ANSI colors
        ansi_colors = [
            (0, 0, 0),      # 0: Black
            (128, 0, 0),    # 1: Red
            (0, 128, 0),    # 2: Green
            (128, 128, 0),  # 3: Yellow
            (0, 0, 128),    # 4: Blue
            (128, 0, 128),  # 5: Magenta
            (0, 128, 128),  # 6: Cyan
            (192, 192, 192), # 7: White
            (128, 128, 128), # 8: Bright Black
            (255, 0, 0),    # 9: Bright Red
            (0, 255, 0),    # 10: Bright Green
            (255, 255, 0),  # 11: Bright Yellow
            (0, 0, 255),    # 12: Bright Blue
            (255, 0, 255),  # 13: Bright Magenta
            (0, 255, 255),  # 14: Bright Cyan
            (255, 255, 255) # 15: Bright White
        ]

        # Find closest color
        min_distance = float('inf')
        closest_ansi = 0

        for i, (ar, ag, ab) in enumerate(ansi_colors):
            distance = ((r - ar) ** 2 + (g - ag) ** 2 + (b - ab) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_ansi = i

        return closest_ansi

    def lighten(self, amount: float = 0.1) -> 'Color':
        """Lighten color by amount (0.0 to 1.0)"""
        h, l, s = self.hsl
        new_l = min(1.0, l + amount)
        return Color.from_hsl(h, s, new_l)

    def darken(self, amount: float = 0.1) -> 'Color':
        """Darken color by amount (0.0 to 1.0)"""
        h, l, s = self.hsl
        new_l = max(0.0, l - amount)
        return Color.from_hsl(h, s, new_l)

    def saturate(self, amount: float = 0.1) -> 'Color':
        """Increase saturation by amount"""
        h, l, s = self.hsl
        new_s = min(1.0, s + amount)
        return Color.from_hsl(h, new_s, l)

    def desaturate(self, amount: float = 0.1) -> 'Color':
        """Decrease saturation by amount"""
        h, l, s = self.hsl
        new_s = max(0.0, s - amount)
        return Color.from_hsl(h, new_s, l)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'hex': self.hex,
            'rgb': self.rgb,
            'hsl': self.hsl,
            'ansi': self.ansi
        }


@dataclass
class ColorPalette:
    """Color palette for theme"""
    # Base colors
    background: Color
    foreground: Color

    # UI colors
    border: Color
    selection: Color
    cursor: Color
    highlight: Color

    # Status colors
    success: Color
    warning: Color
    error: Color
    info: Color

    # File type colors
    directory: Color
    executable: Color
    archive: Color
    image: Color
    video: Color
    audio: Color
    document: Color
    code: Color

    # Accent colors
    accent1: Color
    accent2: Color
    accent3: Color
    accent4: Color

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {key: value.to_dict() for key, value in asdict(self).items()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColorPalette':
        """Create from dictionary"""
        colors = {}
        for key, value in data.items():
            if isinstance(value, dict):
                colors[key] = Color(**value)
            else:
                colors[key] = Color.from_hex(value)
        return cls(**colors)


@dataclass
class ThemeMetadata:
    """Theme metadata"""
    name: str
    author: str
    version: str
    description: str
    theme_type: ThemeType
    created_at: datetime
    updated_at: datetime
    tags: List[str] = field(default_factory=list)
    homepage: Optional[str] = None
    license: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'author': self.author,
            'version': self.version,
            'description': self.description,
            'theme_type': self.theme_type.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags,
            'homepage': self.homepage,
            'license': self.license
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThemeMetadata':
        """Create from dictionary"""
        return cls(
            name=data['name'],
            author=data['author'],
            version=data['version'],
            description=data['description'],
            theme_type=ThemeType(data['theme_type']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            tags=data.get('tags', []),
            homepage=data.get('homepage'),
            license=data.get('license')
        )


@dataclass
class Theme:
    """Complete theme definition"""
    metadata: ThemeMetadata
    colors: ColorPalette
    styles: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'metadata': self.metadata.to_dict(),
            'colors': self.colors.to_dict(),
            'styles': self.styles
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Theme':
        """Create from dictionary"""
        return cls(
            metadata=ThemeMetadata.from_dict(data['metadata']),
            colors=ColorPalette.from_dict(data['colors']),
            styles=data.get('styles', {})
        )

    def get_color(self, color_name: str) -> Optional[Color]:
        """Get color by name"""
        return getattr(self.colors, color_name, None)

    def set_color(self, color_name: str, color: Color):
        """Set color by name"""
        if hasattr(self.colors, color_name):
            setattr(self.colors, color_name, color)

    def generate_variants(self) -> Dict[str, 'Theme']:
        """Generate theme variants (light/dark)"""
        variants = {}

        if self.metadata.theme_type == ThemeType.DARK:
            # Generate light variant
            light_colors = self._generate_light_variant()
            light_metadata = ThemeMetadata(
                name=f"{self.metadata.name} Light",
                author=self.metadata.author,
                version=self.metadata.version,
                description=f"Light variant of {self.metadata.name}",
                theme_type=ThemeType.LIGHT,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=self.metadata.tags + ['auto-generated', 'light-variant']
            )
            variants['light'] = Theme(light_metadata, light_colors, self.styles.copy())

        elif self.metadata.theme_type == ThemeType.LIGHT:
            # Generate dark variant
            dark_colors = self._generate_dark_variant()
            dark_metadata = ThemeMetadata(
                name=f"{self.metadata.name} Dark",
                author=self.metadata.author,
                version=self.metadata.version,
                description=f"Dark variant of {self.metadata.name}",
                theme_type=ThemeType.DARK,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=self.metadata.tags + ['auto-generated', 'dark-variant']
            )
            variants['dark'] = Theme(dark_metadata, dark_colors, self.styles.copy())

        return variants

    def _generate_light_variant(self) -> ColorPalette:
        """Generate light variant of dark theme"""
        # Invert background/foreground and adjust other colors
        return ColorPalette(
            background=self.colors.foreground.lighten(0.9),
            foreground=self.colors.background.darken(0.8),
            border=self.colors.border.lighten(0.3),
            selection=self.colors.selection.lighten(0.4),
            cursor=self.colors.cursor,
            highlight=self.colors.highlight.lighten(0.3),
            success=self.colors.success.darken(0.2),
            warning=self.colors.warning.darken(0.2),
            error=self.colors.error.darken(0.2),
            info=self.colors.info.darken(0.2),
            directory=self.colors.directory.darken(0.3),
            executable=self.colors.executable.darken(0.3),
            archive=self.colors.archive.darken(0.3),
            image=self.colors.image.darken(0.3),
            video=self.colors.video.darken(0.3),
            audio=self.colors.audio.darken(0.3),
            document=self.colors.document.darken(0.3),
            code=self.colors.code.darken(0.3),
            accent1=self.colors.accent1.darken(0.2),
            accent2=self.colors.accent2.darken(0.2),
            accent3=self.colors.accent3.darken(0.2),
            accent4=self.colors.accent4.darken(0.2)
        )

    def _generate_dark_variant(self) -> ColorPalette:
        """Generate dark variant of light theme"""
        # Invert background/foreground and adjust other colors
        return ColorPalette(
            background=self.colors.foreground.darken(0.9),
            foreground=self.colors.background.lighten(0.8),
            border=self.colors.border.darken(0.3),
            selection=self.colors.selection.darken(0.4),
            cursor=self.colors.cursor,
            highlight=self.colors.highlight.darken(0.3),
            success=self.colors.success.lighten(0.2),
            warning=self.colors.warning.lighten(0.2),
            error=self.colors.error.lighten(0.2),
            info=self.colors.info.lighten(0.2),
            directory=self.colors.directory.lighten(0.3),
            executable=self.colors.executable.lighten(0.3),
            archive=self.colors.archive.lighten(0.3),
            image=self.colors.image.lighten(0.3),
            video=self.colors.video.lighten(0.3),
            audio=self.colors.audio.lighten(0.3),
            document=self.colors.document.lighten(0.3),
            code=self.colors.code.lighten(0.3),
            accent1=self.colors.accent1.lighten(0.2),
            accent2=self.colors.accent2.lighten(0.2),
            accent3=self.colors.accent3.lighten(0.2),
            accent4=self.colors.accent4.lighten(0.2)
        )


class ThemeValidator:
    """Validates theme definitions"""

    def __init__(self):
        self.logger = Logger()

        # Required color fields
        self.required_colors = [
            'background', 'foreground', 'border', 'selection', 'cursor',
            'highlight', 'success', 'warning', 'error', 'info',
            'directory', 'executable', 'archive', 'image', 'video',
            'audio', 'document', 'code', 'accent1', 'accent2', 'accent3', 'accent4'
        ]

        # Required metadata fields
        self.required_metadata = [
            'name', 'author', 'version', 'description', 'theme_type'
        ]

    def validate_theme(self, theme_data: Dict[str, Any]) -> List[str]:
        """Validate theme data and return list of errors"""
        errors = []

        # Check structure
        if 'metadata' not in theme_data:
            errors.append("Missing 'metadata' section")
        if 'colors' not in theme_data:
            errors.append("Missing 'colors' section")

        if errors:
            return errors

        # Validate metadata
        metadata_errors = self._validate_metadata(theme_data['metadata'])
        errors.extend(metadata_errors)

        # Validate colors
        color_errors = self._validate_colors(theme_data['colors'])
        errors.extend(color_errors)

        return errors

    def _validate_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Validate metadata section"""
        errors = []

        for field in self.required_metadata:
            if field not in metadata:
                errors.append(f"Missing required metadata field: {field}")
            elif not metadata[field]:
                errors.append(f"Empty required metadata field: {field}")

        # Validate theme_type
        if 'theme_type' in metadata:
            try:
                ThemeType(metadata['theme_type'])
            except ValueError:
                errors.append(f"Invalid theme_type: {metadata['theme_type']}")

        return errors

    def _validate_colors(self, colors: Dict[str, Any]) -> List[str]:
        """Validate colors section"""
        errors = []

        for color_name in self.required_colors:
            if color_name not in colors:
                errors.append(f"Missing required color: {color_name}")
                continue

            color_data = colors[color_name]
            color_errors = self._validate_color(color_name, color_data)
            errors.extend(color_errors)

        return errors

    def _validate_color(self, color_name: str, color_data: Any) -> List[str]:
        """Validate individual color"""
        errors = []

        if isinstance(color_data, str):
            # Hex color string
            if not self._is_valid_hex_color(color_data):
                errors.append(f"Invalid hex color for {color_name}: {color_data}")
        elif isinstance(color_data, dict):
            # Color object
            if 'hex' not in color_data:
                errors.append(f"Missing hex value for color {color_name}")
            elif not self._is_valid_hex_color(color_data['hex']):
                errors.append(f"Invalid hex color for {color_name}: {color_data['hex']}")
        else:
            errors.append(f"Invalid color format for {color_name}")

        return errors

    def _is_valid_hex_color(self, hex_color: str) -> bool:
        """Check if string is valid hex color"""
        if not hex_color.startswith('#'):
            return False

        hex_part = hex_color[1:]
        if len(hex_part) not in [3, 6]:
            return False

        try:
            int(hex_part, 16)
            return True
        except ValueError:
            return False


class ThemeManager:
    """Manages themes, loading, saving, and switching"""

    def __init__(self, themes_directory: Path):
        self.themes_directory = Path(themes_directory)
        self.themes_directory.mkdir(parents=True, exist_ok=True)

        self.logger = Logger()
        self.validator = ThemeValidator()

        # Loaded themes
        self.themes: Dict[str, Theme] = {}
        self.current_theme: Optional[Theme] = None

        # Theme change callbacks
        self.change_callbacks: List[Callable[[Theme], None]] = []

        # Load built-in themes
        self._load_builtin_themes()

        # Load user themes
        self._load_user_themes()

    def _load_builtin_themes(self):
        """Load built-in SuperFile-inspired themes"""
        builtin_themes = {
            'catppuccin_mocha': self._create_catppuccin_mocha(),
            'catppuccin_latte': self._create_catppuccin_latte(),
            'dracula': self._create_dracula(),
            'nord': self._create_nord(),
            'gruvbox_dark': self._create_gruvbox_dark(),
            'gruvbox_light': self._create_gruvbox_light(),
            'tokyo_night': self._create_tokyo_night(),
            'one_dark': self._create_one_dark(),
            'solarized_dark': self._create_solarized_dark(),
            'solarized_light': self._create_solarized_light()
        }

        for theme_id, theme in builtin_themes.items():
            self.themes[theme_id] = theme

    def _create_catppuccin_mocha(self) -> Theme:
        """Create Catppuccin Mocha theme"""
        metadata = ThemeMetadata(
            name="Catppuccin Mocha",
            author="LaxyFile",
            version="1.0.0",
            description="Soothing pastel theme for the high-spirited!",
            theme_type=ThemeType.DARK,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=["dark", "pastel", "popular", "builtin"]
        )

        colors = ColorPalette(
            background=Color.from_hex("#1e1e2e"),
            foreground=Color.from_hex("#cdd6f4"),
            border=Color.from_hex("#585b70"),
            selection=Color.from_hex("#313244"),
            cursor=Color.from_hex("#f5e0dc"),
            highlight=Color.from_hex("#45475a"),
            success=Color.from_hex("#a6e3a1"),
            warning=Color.from_hex("#f9e2af"),
            error=Color.from_hex("#f38ba8"),
            info=Color.from_hex("#89b4fa"),
            directory=Color.from_hex("#89b4fa"),
            executable=Color.from_hex("#a6e3a1"),
            archive=Color.from_hex("#f9e2af"),
            image=Color.from_hex("#f5c2e7"),
            video=Color.from_hex("#cba6f7"),
            audio=Color.from_hex("#94e2d5"),
            document=Color.from_hex("#fab387"),
            code=Color.from_hex("#f38ba8"),
            accent1=Color.from_hex("#f5c2e7"),
            accent2=Color.from_hex("#cba6f7"),
            accent3=Color.from_hex("#94e2d5"),
            accent4=Color.from_hex("#fab387")
        )

        return Theme(metadata, colors)

    def _create_catppuccin_latte(self) -> Theme:
        """Create Catppuccin Latte theme"""
        metadata = ThemeMetadata(
            name="Catppuccin Latte",
            author="LaxyFile",
            version="1.0.0",
            description="Soothing pastel theme for the high-spirited! (Light variant)",
            theme_type=ThemeType.LIGHT,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=["light", "pastel", "popular", "builtin"]
        )

        colors = ColorPalette(
            background=Color.from_hex("#eff1f5"),
            foreground=Color.from_hex("#4c4f69"),
            border=Color.from_hex("#acb0be"),
            selection=Color.from_hex("#dce0e8"),
            cursor=Color.from_hex("#dc8a78"),
            highlight=Color.from_hex("#bcc0cc"),
            success=Color.from_hex("#40a02b"),
            warning=Color.from_hex("#df8e1d"),
            error=Color.from_hex("#d20f39"),
            info=Color.from_hex("#1e66f5"),
            directory=Color.from_hex("#1e66f5"),
            executable=Color.from_hex("#40a02b"),
            archive=Color.from_hex("#df8e1d"),
            image=Color.from_hex("#ea76cb"),
            video=Color.from_hex("#8839ef"),
            audio=Color.from_hex("#179299"),
            document=Color.from_hex("#fe640b"),
            code=Color.from_hex("#d20f39"),
            accent1=Color.from_hex("#ea76cb"),
            accent2=Color.from_hex("#8839ef"),
            accent3=Color.from_hex("#179299"),
            accent4=Color.from_hex("#fe640b")
        )

        return Theme(metadata, colors)

    def _create_dracula(self) -> Theme:
        """Create Dracula theme"""
        metadata = ThemeMetadata(
            name="Dracula",
            author="LaxyFile",
            version="1.0.0",
            description="A dark theme for those who live on the edge",
            theme_type=ThemeType.DARK,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=["dark", "vampire", "popular", "builtin"]
        )

        colors = ColorPalette(
            background=Color.from_hex("#282a36"),
            foreground=Color.from_hex("#f8f8f2"),
            border=Color.from_hex("#6272a4"),
            selection=Color.from_hex("#44475a"),
            cursor=Color.from_hex("#f8f8f0"),
            highlight=Color.from_hex("#44475a"),
            success=Color.from_hex("#50fa7b"),
            warning=Color.from_hex("#f1fa8c"),
            error=Color.from_hex("#ff5555"),
            info=Color.from_hex("#8be9fd"),
            directory=Color.from_hex("#bd93f9"),
            executable=Color.from_hex("#50fa7b"),
            archive=Color.from_hex("#f1fa8c"),
            image=Color.from_hex("#ff79c6"),
            video=Color.from_hex("#bd93f9"),
            audio=Color.from_hex("#8be9fd"),
            document=Color.from_hex("#ffb86c"),
            code=Color.from_hex("#ff5555"),
            accent1=Color.from_hex("#ff79c6"),
            accent2=Color.from_hex("#bd93f9"),
            accent3=Color.from_hex("#8be9fd"),
            accent4=Color.from_hex("#ffb86c")
        )

        return Theme(metadata, colors)

    def _create_nord(self) -> Theme:
        """Create Nord theme"""
        metadata = ThemeMetadata(
            name="Nord",
            author="LaxyFile",
            version="1.0.0",
            description="An arctic, north-bluish color palette",
            theme_type=ThemeType.DARK,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=["dark", "blue", "arctic", "builtin"]
        )

        colors = ColorPalette(
            background=Color.from_hex("#2e3440"),
            foreground=Color.from_hex("#d8dee9"),
            border=Color.from_hex("#4c566a"),
            selection=Color.from_hex("#3b4252"),
            cursor=Color.from_hex("#d8dee9"),
            highlight=Color.from_hex("#434c5e"),
            success=Color.from_hex("#a3be8c"),
            warning=Color.from_hex("#ebcb8b"),
            error=Color.from_hex("#bf616a"),
            info=Color.from_hex("#81a1c1"),
            directory=Color.from_hex("#5e81ac"),
            executable=Color.from_hex("#a3be8c"),
            archive=Color.from_hex("#ebcb8b"),
            image=Color.from_hex("#b48ead"),
            video=Color.from_hex("#88c0d0"),
            audio=Color.from_hex("#8fbcbb"),
            document=Color.from_hex("#d08770"),
            code=Color.from_hex("#bf616a"),
            accent1=Color.from_hex("#88c0d0"),
            accent2=Color.from_hex("#81a1c1"),
            accent3=Color.from_hex("#5e81ac"),
            accent4=Color.from_hex("#b48ead")
        )

        return Theme(metadata, colors)

    def _create_gruvbox_dark(self) -> Theme:
        """Create Gruvbox Dark theme"""
        metadata = ThemeMetadata(
            name="Gruvbox Dark",
            author="LaxyFile",
            version="1.0.0",
            description="Retro groove color scheme",
            theme_type=ThemeType.DARK,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=["dark", "retro", "warm", "builtin"]
        )

        colors = ColorPalette(
            background=Color.from_hex("#282828"),
            foreground=Color.from_hex("#ebdbb2"),
            border=Color.from_hex("#665c54"),
            selection=Color.from_hex("#3c3836"),
            cursor=Color.from_hex("#ebdbb2"),
            highlight=Color.from_hex("#504945"),
            success=Color.from_hex("#b8bb26"),
            warning=Color.from_hex("#fabd2f"),
            error=Color.from_hex("#fb4934"),
            info=Color.from_hex("#83a598"),
            directory=Color.from_hex("#83a598"),
            executable=Color.from_hex("#b8bb26"),
            archive=Color.from_hex("#fabd2f"),
            image=Color.from_hex("#d3869b"),
            video=Color.from_hex("#8ec07c"),
            audio=Color.from_hex("#fe8019"),
            document=Color.from_hex("#d65d0e"),
            code=Color.from_hex("#fb4934"),
            accent1=Color.from_hex("#d3869b"),
            accent2=Color.from_hex("#8ec07c"),
            accent3=Color.from_hex("#fe8019"),
            accent4=Color.from_hex("#d65d0e")
        )

        return Theme(metadata, colors)

    def _create_gruvbox_light(self) -> Theme:
        """Create Gruvbox Light theme"""
        metadata = ThemeMetadata(
            name="Gruvbox Light",
            author="LaxyFile",
            version="1.0.0",
            description="Retro groove color scheme (Light variant)",
            theme_type=ThemeType.LIGHT,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=["light", "retro", "warm", "builtin"]
        )

        colors = ColorPalette(
            background=Color.from_hex("#fbf1c7"),
            foreground=Color.from_hex("#3c3836"),
            border=Color.from_hex("#bdae93"),
            selection=Color.from_hex("#ebdbb2"),
            cursor=Color.from_hex("#3c3836"),
            highlight=Color.from_hex("#d5c4a1"),
            success=Color.from_hex("#79740e"),
            warning=Color.from_hex("#b57614"),
            error=Color.from_hex("#cc241d"),
            info=Color.from_hex("#076678"),
            directory=Color.from_hex("#076678"),
            executable=Color.from_hex("#79740e"),
            archive=Color.from_hex("#b57614"),
            image=Color.from_hex("#8f3f71"),
            video=Color.from_hex("#427b58"),
            audio=Color.from_hex("#af3a03"),
            document=Color.from_hex("#d65d0e"),
            code=Color.from_hex("#cc241d"),
            accent1=Color.from_hex("#8f3f71"),
            accent2=Color.from_hex("#427b58"),
            accent3=Color.from_hex("#af3a03"),
            accent4=Color.from_hex("#d65d0e")
        )

        return Theme(metadata, colors)

    def _create_tokyo_night(self) -> Theme:
        """Create Tokyo Night theme"""
        metadata = ThemeMetadata(
            name="Tokyo Night",
            author="LaxyFile",
            version="1.0.0",
            description="A clean, dark theme that celebrates the lights of downtown Tokyo at night",
            theme_type=ThemeType.DARK,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=["dark", "neon", "city", "builtin"]
        )

        colors = ColorPalette(
            background=Color.from_hex("#1a1b26"),
            foreground=Color.from_hex("#c0caf5"),
            border=Color.from_hex("#414868"),
            selection=Color.from_hex("#283457"),
            cursor=Color.from_hex("#c0caf5"),
            highlight=Color.from_hex("#364a82"),
            success=Color.from_hex("#9ece6a"),
            warning=Color.from_hex("#e0af68"),
            error=Color.from_hex("#f7768e"),
            info=Color.from_hex("#7aa2f7"),
            directory=Color.from_hex("#7aa2f7"),
            executable=Color.from_hex("#9ece6a"),
            archive=Color.from_hex("#e0af68"),
            image=Color.from_hex("#bb9af7"),
            video=Color.from_hex("#7dcfff"),
            audio=Color.from_hex("#73daca"),
            document=Color.from_hex("#ff9e64"),
            code=Color.from_hex("#f7768e"),
            accent1=Color.from_hex("#bb9af7"),
            accent2=Color.from_hex("#7dcfff"),
            accent3=Color.from_hex("#73daca"),
            accent4=Color.from_hex("#ff9e64")
        )

        return Theme(metadata, colors)

    def _create_one_dark(self) -> Theme:
        """Create One Dark theme"""
        metadata = ThemeMetadata(
            name="One Dark",
            author="LaxyFile",
            version="1.0.0",
            description="Atom's iconic One Dark theme",
            theme_type=ThemeType.DARK,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=["dark", "atom", "popular", "builtin"]
        )

        colors = ColorPalette(
            background=Color.from_hex("#282c34"),
            foreground=Color.from_hex("#abb2bf"),
            border=Color.from_hex("#4b5263"),
            selection=Color.from_hex("#3e4451"),
            cursor=Color.from_hex("#528bff"),
            highlight=Color.from_hex("#2c313c"),
            success=Color.from_hex("#98c379"),
            warning=Color.from_hex("#e5c07b"),
            error=Color.from_hex("#e06c75"),
            info=Color.from_hex("#61afef"),
            directory=Color.from_hex("#61afef"),
            executable=Color.from_hex("#98c379"),
            archive=Color.from_hex("#e5c07b"),
            image=Color.from_hex("#c678dd"),
            video=Color.from_hex("#56b6c2"),
            audio=Color.from_hex("#d19a66"),
            document=Color.from_hex("#e06c75"),
            code=Color.from_hex("#be5046"),
            accent1=Color.from_hex("#c678dd"),
            accent2=Color.from_hex("#56b6c2"),
            accent3=Color.from_hex("#d19a66"),
            accent4=Color.from_hex("#be5046")
        )

        return Theme(metadata, colors)

    def _create_solarized_dark(self) -> Theme:
        """Create Solarized Dark theme"""
        metadata = ThemeMetadata(
            name="Solarized Dark",
            author="LaxyFile",
            version="1.0.0",
            description="Precision colors for machines and people",
            theme_type=ThemeType.DARK,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=["dark", "solarized", "classic", "builtin"]
        )

        colors = ColorPalette(
            background=Color.from_hex("#002b36"),
            foreground=Color.from_hex("#839496"),
            border=Color.from_hex("#586e75"),
            selection=Color.from_hex("#073642"),
            cursor=Color.from_hex("#93a1a1"),
            highlight=Color.from_hex("#073642"),
            success=Color.from_hex("#859900"),
            warning=Color.from_hex("#b58900"),
            error=Color.from_hex("#dc322f"),
            info=Color.from_hex("#268bd2"),
            directory=Color.from_hex("#268bd2"),
            executable=Color.from_hex("#859900"),
            archive=Color.from_hex("#b58900"),
            image=Color.from_hex("#d33682"),
            video=Color.from_hex("#2aa198"),
            audio=Color.from_hex("#cb4b16"),
            document=Color.from_hex("#6c71c4"),
            code=Color.from_hex("#dc322f"),
            accent1=Color.from_hex("#d33682"),
            accent2=Color.from_hex("#2aa198"),
            accent3=Color.from_hex("#cb4b16"),
            accent4=Color.from_hex("#6c71c4")
        )

        return Theme(metadata, colors)

    def _create_solarized_light(self) -> Theme:
        """Create Solarized Light theme"""
        metadata = ThemeMetadata(
            name="Solarized Light",
            author="LaxyFile",
            version="1.0.0",
            description="Precision colors for machines and people (Light variant)",
            theme_type=ThemeType.LIGHT,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=["light", "solarized", "classic", "builtin"]
        )

        colors = ColorPalette(
            background=Color.from_hex("#fdf6e3"),
            foreground=Color.from_hex("#657b83"),
            border=Color.from_hex("#93a1a1"),
            selection=Color.from_hex("#eee8d5"),
            cursor=Color.from_hex("#586e75"),
            highlight=Color.from_hex("#eee8d5"),
            success=Color.from_hex("#859900"),
            warning=Color.from_hex("#b58900"),
            error=Color.from_hex("#dc322f"),
            info=Color.from_hex("#268bd2"),
            directory=Color.from_hex("#268bd2"),
            executable=Color.from_hex("#859900"),
            archive=Color.from_hex("#b58900"),
            image=Color.from_hex("#d33682"),
            video=Color.from_hex("#2aa198"),
            audio=Color.from_hex("#cb4b16"),
            document=Color.from_hex("#6c71c4"),
            code=Color.from_hex("#dc322f"),
            accent1=Color.from_hex("#d33682"),
            accent2=Color.from_hex("#2aa198"),
            accent3=Color.from_hex("#cb4b16"),
            accent4=Color.from_hex("#6c71c4")
        )

        return Theme(metadata, colors)

    def _load_user_themes(self):
        """Load user-created themes from themes directory"""
        try:
            for theme_file in self.themes_directory.glob("*.json"):
                try:
                    theme_data = json.loads(theme_file.read_text())

                    # Validate theme
                    errors = self.validator.validate_theme(theme_data)
                    if errors:
                        self.logger.error(f"Invalid theme {theme_file.name}: {errors}")
                        continue

                    theme = Theme.from_dict(theme_data)
                    theme_id = theme_file.stem
                    self.themes[theme_id] = theme

                    self.logger.info(f"Loaded user theme: {theme.metadata.name}")

                except Exception as e:
                    self.logger.error(f"Error loading theme {theme_file.name}: {e}")

        except Exception as e:
            self.logger.error(f"Error loading user themes: {e}")

    def get_theme(self, theme_id: str) -> Optional[Theme]:
        """Get theme by ID"""
        return self.themes.get(theme_id)

    def get_all_themes(self) -> Dict[str, Theme]:
        """Get all available themes"""
        return self.themes.copy()

    def get_themes_by_type(self, theme_type: ThemeType) -> Dict[str, Theme]:
        """Get themes by type"""
        return {
            theme_id: theme for theme_id, theme in self.themes.items()
            if theme.metadata.theme_type == theme_type
        }

    def set_current_theme(self, theme_id: str) -> bool:
        """Set current theme"""
        theme = self.get_theme(theme_id)
        if not theme:
            self.logger.error(f"Theme not found: {theme_id}")
            return False

        old_theme = self.current_theme
        self.current_theme = theme

        # Notify callbacks
        for callback in self.change_callbacks:
            try:
                callback(theme)
            except Exception as e:
                self.logger.error(f"Error in theme change callback: {e}")

        self.logger.info(f"Theme changed to: {theme.metadata.name}")
        return True

    def get_current_theme(self) -> Optional[Theme]:
        """Get current theme"""
        return self.current_theme

    def add_theme_change_callback(self, callback: Callable[[Theme], None]):
        """Add theme change callback"""
        self.change_callbacks.append(callback)

    def remove_theme_change_callback(self, callback: Callable[[Theme], None]):
        """Remove theme change callback"""
        if callback in self.change_callbacks:
            self.change_callbacks.remove(callback)

    def save_theme(self, theme: Theme, theme_id: Optional[str] = None) -> bool:
        """Save theme to file"""
        try:
            if not theme_id:
                # Generate ID from theme name
                theme_id = theme.metadata.name.lower().replace(' ', '_').replace('-', '_')
                theme_id = ''.join(c for c in theme_id if c.isalnum() or c == '_')

            theme_file = self.themes_directory / f"{theme_id}.json"

            # Update timestamp
            theme.metadata.updated_at = datetime.now()

            # Save to file
            theme_data = theme.to_dict()
            theme_file.write_text(json.dumps(theme_data, indent=2))

            # Add to loaded themes
            self.themes[theme_id] = theme

            self.logger.info(f"Theme saved: {theme.metadata.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving theme: {e}")
            return False

    def delete_theme(self, theme_id: str) -> bool:
        """Delete theme"""
        try:
            # Don't delete built-in themes
            theme = self.get_theme(theme_id)
            if theme and 'builtin' in theme.metadata.tags:
                self.logger.error(f"Cannot delete built-in theme: {theme_id}")
                return False

            # Remove from file system
            theme_file = self.themes_directory / f"{theme_id}.json"
            if theme_file.exists():
                theme_file.unlink()

            # Remove from loaded themes
            if theme_id in self.themes:
                del self.themes[theme_id]

            # Switch to default if current theme was deleted
            if self.current_theme and theme_id == self._get_theme_id(self.current_theme):
                self.set_current_theme('catppuccin_mocha')  # Default fallback

            self.logger.info(f"Theme deleted: {theme_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting theme: {e}")
            return False

    def _get_theme_id(self, theme: Theme) -> Optional[str]:
        """Get theme ID from theme object"""
        for theme_id, t in self.themes.items():
            if t == theme:
                return theme_id
        return None

    def export_theme(self, theme_id: str, export_path: Path) -> bool:
        """Export theme to file"""
        try:
            theme = self.get_theme(theme_id)
            if not theme:
                return False

            theme_data = theme.to_dict()
            export_path.write_text(json.dumps(theme_data, indent=2))

            self.logger.info(f"Theme exported: {theme.metadata.name} -> {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting theme: {e}")
            return False

    def import_theme(self, import_path: Path, theme_id: Optional[str] = None) -> bool:
        """Import theme from file"""
        try:
            theme_data = json.loads(import_path.read_text())

            # Validate theme
            errors = self.validator.validate_theme(theme_data)
            if errors:
                self.logger.error(f"Invalid theme file: {errors}")
                return False

            theme = Theme.from_dict(theme_data)

            # Save theme
            return self.save_theme(theme, theme_id)

        except Exception as e:
            self.logger.error(f"Error importing theme: {e}")
            return False

    def create_custom_theme(self, base_theme_id: str, name: str,
                          color_overrides: Dict[str, str]) -> Optional[Theme]:
        """Create custom theme based on existing theme"""
        try:
            base_theme = self.get_theme(base_theme_id)
            if not base_theme:
                return None

            # Create new metadata
            metadata = ThemeMetadata(
                name=name,
                author="User",
                version="1.0.0",
                description=f"Custom theme based on {base_theme.metadata.name}",
                theme_type=base_theme.metadata.theme_type,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=["custom", "user-created"]
            )

            # Copy colors and apply overrides
            colors_dict = base_theme.colors.to_dict()
            for color_name, hex_color in color_overrides.items():
                if color_name in colors_dict:
                    colors_dict[color_name] = Color.from_hex(hex_color).to_dict()

            colors = ColorPalette.from_dict(colors_dict)

            # Create theme
            custom_theme = Theme(metadata, colors, base_theme.styles.copy())

            return custom_theme

        except Exception as e:
            self.logger.error(f"Error creating custom theme: {e}")
            return None

    def get_theme_preview(self, theme_id: str) -> str:
        """Get theme preview as colored text"""
        theme = self.get_theme(theme_id)
        if not theme:
            return "Theme not found"

        # Create a simple preview
        preview = f"""
Theme: {theme.metadata.name}
Author: {theme.metadata.author}
Type: {theme.metadata.theme_type.value.title()}

Colors:
  Background: {theme.colors.background.hex}
  Foreground: {theme.colors.foreground.hex}
  Success: {theme.colors.success.hex}
  Warning: {theme.colors.warning.hex}
  Error: {theme.colors.error.hex}
  Directory: {theme.colors.directory.hex}
  Executable: {theme.colors.executable.hex}
"""

        return preview.strip()


class EnhancedThemeSystem:
    """Main theme system class"""

    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        self.themes_dir = self.config_dir / "themes"

        self.logger = Logger()
        self.theme_manager = ThemeManager(self.themes_dir)

        # Set default theme
        if not self.theme_manager.get_current_theme():
            self.theme_manager.set_current_theme('catppuccin_mocha')

    def get_manager(self) -> ThemeManager:
        """Get theme manager"""
        return self.theme_manager

    def apply_theme_to_ui(self, ui_component: Any):
        """Apply current theme to UI component"""
        current_theme = self.theme_manager.get_current_theme()
        if not current_theme:
            return

        try:
            # This would apply theme colors to the UI component
            # Implementation depends on the UI framework being used
            if hasattr(ui_component, 'apply_theme'):
                ui_component.apply_theme(current_theme)
            elif hasattr(ui_component, 'set_colors'):
                ui_component.set_colors(current_theme.colors)

        except Exception as e:
            self.logger.error(f"Error applying theme to UI: {e}")

    def get_color_for_file_type(self, file_extension: str) -> Color:
        """Get color for file type based on current theme"""
        current_theme = self.theme_manager.get_current_theme()
        if not current_theme:
            return Color.from_hex("#ffffff")  # Default white

        # Map file extensions to color categories
        extension = file_extension.lower()

        if extension in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']:
            return current_theme.colors.code
        elif extension in ['.jpg', '.png', '.gif', '.bmp', '.svg']:
            return current_theme.colors.image
        elif extension in ['.mp4', '.avi', '.mkv', '.mov']:
            return current_theme.colors.video
        elif extension in ['.mp3', '.wav', '.flac', '.ogg']:
            return current_theme.colors.audio
        elif extension in ['.pdf', '.doc', '.docx', '.txt', '.md']:
            return current_theme.colors.document
        elif extension in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            return current_theme.colors.archive
        else:
            return current_theme.colors.foreground

    def get_ansi_color_code(self, color_name: str) -> str:
        """Get ANSI color code for terminal output"""
        current_theme = self.theme_manager.get_current_theme()
        if not current_theme:
            return "\033[0m"  # Reset

        color = current_theme.get_color(color_name)
        if not color:
            return "\033[0m"

        # Convert to ANSI escape code
        return f"\033[38;5;{color.ansi}m"

    def reset_to_defaults(self):
        """Reset theme system to defaults"""
        try:
            # Clear user themes (keep built-in)
            for theme_id in list(self.theme_manager.themes.keys()):
                theme = self.theme_manager.themes[theme_id]
                if 'builtin' not in theme.metadata.tags:
                    self.theme_manager.delete_theme(theme_id)

            # Set default theme
            self.theme_manager.set_current_theme('catppuccin_mocha')

            self.logger.info("Theme system reset to defaults")

        except Exception as e:
            self.logger.error(f"Error resetting theme system: {e}")