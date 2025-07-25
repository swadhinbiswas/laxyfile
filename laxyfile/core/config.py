"""
Enhanced Configuration Management System

This module provides comprehensive configuration management for LaxyFile
with SuperFile-inspired settings, validation, and migration support.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, validator
import shutil
from datetime import datetime

from .interfaces import ConfigInterface
from .exceptions import ConfigurationError, InvalidConfigValueError, MissingConfigError

class SuperFileThemeConfig(BaseModel):
    """SuperFile-inspired theme configuration with comprehensive styling"""
    name: str = "cappuccino"

    # Border styles (SuperFile-inspired)
    file_panel_border: str = "#D2691E"
    file_panel_border_active: str = "#8B4513"
    sidebar_border: str = "#A0522D"
    sidebar_border_active: str = "#8B4513"
    footer_border: str = "#CD853F"
    modal_border_active: str = "#DEB887"

    # Background colors
    full_screen_bg: str = "default"
    file_panel_bg: str = "default"
    sidebar_bg: str = "default"
    footer_bg: str = "default"
    modal_bg: str = "#F5F5DC"

    # Foreground colors
    full_screen_fg: str = "white"
    file_panel_fg: str = "white"
    sidebar_fg: str = "white"
    footer_fg: str = "white"
    modal_fg: str = "black"

    # Special colors
    cursor: str = "#DEB887"
    correct: str = "green"
    error: str = "red"
    hint: str = "yellow"
    cancel: str = "red"
    gradient_color: List[str] = ["#8B4513", "#A0522D", "#D2691E", "#CD853F", "#DEB887"]
    directory_icon_color: str = "#8B4513"

    # File panel specific
    file_panel_top_directory_icon: str = "#8B4513"
    file_panel_top_path: str = "bold #A0522D"
    file_panel_item_selected_fg: str = "black"
    file_panel_item_selected_bg: str = "#DEB887"

    # Sidebar specific
    sidebar_title: str = "bold #8B4513"
    sidebar_item_selected_fg: str = "black"
    sidebar_item_selected_bg: str = "#CD853F"
    sidebar_divider: str = "#A0522D"

    # Modal specific
    modal_cancel_fg: str = "white"
    modal_cancel_bg: str = "red"
    modal_confirm_fg: str = "white"
    modal_confirm_bg: str = "green"

    # Help menu
    help_menu_hotkey: str = "yellow"
    help_menu_title: str = "bold #8B4513"

    # Code syntax highlighting
    code_syntax_highlight_theme: str = "monokai"

    # Transparency and effects
    transparent_background: bool = False
    use_gradients: bool = True
    use_icons: bool = True

    @validator('name')
    def validate_theme_name(cls, v):
        valid_themes = ['cappuccino', 'neon', 'ocean', 'sunset', 'forest', 'catppuccin', 'dracula', 'nord']
        if v not in valid_themes:
            # Auto-fix invalid theme names to cappuccino
            return 'cappuccino'
        return v

class HotkeyConfig(BaseModel):
    """Advanced hotkey configuration"""
    # Navigation
    move_up: str = "k"
    move_down: str = "j"
    move_left: str = "h"
    move_right: str = "l"
    move_up_alt: str = "UP"
    move_down_alt: str = "DOWN"
    move_left_alt: str = "LEFT"
    move_right_alt: str = "RIGHT"

    # Panel switching
    switch_panel: str = "TAB"

    # Selection
    select_item: str = " "  # Space
    select_all: str = "a"
    invert_selection: str = "ctrl+a"

    # File operations
    copy_files: str = "c"
    move_files: str = "m"
    delete: str = "d"
    rename: str = "r"
    new_dir: str = "n"
    new_file: str = "ctrl+n"

    # View operations
    view_file: str = "v"
    edit_file: str = "e"
    open_file: str = "ENTER"
    preview_toggle: str = "p"

    # Navigation shortcuts
    go_home: str = "~"
    go_root: str = "/"
    go_parent: str = ".."
    go_top: str = "g"
    go_bottom: str = "G"
    page_up: str = "PAGE_UP"
    page_down: str = "PAGE_DOWN"

    # Search and filter
    search: str = "/"
    filter_files: str = "f"
    toggle_hidden: str = "."

    # Application
    quit: str = "q"
    help: str = "?"
    refresh: str = "F5"

    # Theme switching
    theme_next: str = "t"
    theme_cappuccino: str = "F1"
    theme_neon: str = "F2"
    theme_ocean: str = "F3"
    theme_sunset: str = "F4"
    theme_forest: str = "F5"

    # AI features
    ai_chat: str = "ctrl+i"
    ai_analyze: str = "ctrl+alt+a"

# AI Configuration Model
class AIConfig(BaseModel):
    """AI assistant configuration"""
    enabled: bool = True
    provider: str = "openrouter"  # Changed default to openrouter
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None  # Added OpenRouter specific key
    anthropic_api_key: Optional[str] = None
    model: str = "moonshotai/kimi-dev-72b:free"  # Default to Kimi model
    max_tokens: int = 4000  # Increased for better responses
    temperature: float = 0.7
    timeout: int = 60  # Increased timeout for complex analysis
    max_file_size_mb: int = 10  # Max file size to analyze content
    enable_content_analysis: bool = True
    enable_device_monitoring: bool = True
    cache_responses: bool = True

class UIConfig(BaseModel):
    """Enhanced UI configuration"""
    # File display
    show_hidden_files: bool = False
    dual_pane: bool = True
    preview_pane: bool = True
    file_icons: bool = True
    show_size: bool = True
    show_date: bool = True
    show_permissions: bool = False
    show_symlink_target: bool = True

    # Visual settings
    border_style: str = "rounded"  # rounded, heavy, double, ascii
    color_mode: str = "truecolor"  # truecolor, 256, 16, mono
    terminal_title: bool = True

    # Behavior
    auto_refresh: bool = True
    refresh_rate: int = 8  # FPS
    mouse_support: bool = True
    vim_keys: bool = True
    confirm_operations: bool = True

    # Image/Video display
    image_preview: bool = True
    video_thumbnails: bool = True
    ascii_art_width: int = 60
    ascii_art_height: int = 20

    # Performance
    max_files_display: int = 1000
    thumbnail_cache_size: int = 100
    lazy_loading: bool = True

class SuperFileConfig(BaseModel):
    """SuperFile-inspired configuration with comprehensive settings"""
    # SuperFile-like settings
    theme: str = "cappuccino"
    editor: str = "nano"
    dir_editor: str = ""
    auto_check_update: bool = True
    cd_on_quit: bool = True
    default_open_file_preview: bool = True
    show_image_preview: bool = True
    show_panel_footer_info: bool = True
    default_directory: str = "~"
    file_size_use_si: bool = False
    default_sort_type: int = 0  # 0: Name, 1: Size, 2: Date Modified
    sort_order_reversed: bool = False
    case_sensitive_sort: bool = False
    shell_close_on_success: bool = True
    debug: bool = False
    ignore_missing_fields: bool = False

    # Style settings
    nerdfont: bool = True
    transparent_background: bool = False
    file_preview_width: int = 0  # 0 means same as file panel
    code_previewer: str = ""  # "" for builtin, "bat" for bat
    sidebar_width: int = 20

    # Border styles
    border_top: str = "─"
    border_bottom: str = "─"
    border_left: str = "│"
    border_right: str = "│"
    border_top_left: str = "┌"
    border_top_right: str = "┐"
    border_bottom_left: str = "└"
    border_bottom_right: str = "┘"
    border_middle_left: str = "├"
    border_middle_right: str = "┤"

    # Plugins
    metadata: bool = True
    enable_md5_checksum: bool = False
    zoxide_support: bool = False

class AppConfig(BaseModel):
    """Enhanced application configuration"""
    theme: SuperFileThemeConfig = Field(default_factory=SuperFileThemeConfig)
    hotkeys: HotkeyConfig = Field(default_factory=HotkeyConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    superfile: SuperFileConfig = Field(default_factory=SuperFileConfig)

    # General settings
    startup_path: str = "~"
    startup_panel: str = "left"  # left, right
    remember_session: bool = True

    # External programs
    editor: str = "nano"
    image_viewer: str = "auto"  # auto, feh, eog, etc.
    video_player: str = "auto"  # auto, mpv, vlc, etc.
    terminal: str = "auto"  # auto, xterm, gnome-terminal, etc.

    # File operations
    use_trash: bool = True
    confirm_delete: bool = True
    confirm_overwrite: bool = True
    case_sensitive_search: bool = False
    follow_symlinks: bool = False

    # Advanced features
    plugin_directory: str = "~/.config/laxyfile/plugins"
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    log_file: str = "~/.config/laxyfile/laxyfile.log"

    # Performance tuning
    file_watcher: bool = True
    background_operations: bool = True
    multi_threading: bool = True

class EnhancedConfig(ConfigInterface):
    """Enhanced configuration manager with SuperFile-inspired features"""

    CONFIG_VERSION = "2.0"

    def __init__(self):
        self.config_dir = Path.home() / ".config" / "laxyfile"
        self.config_file = self.config_dir / "config.yaml"
        self.session_file = self.config_dir / "session.json"
        self.themes_dir = self.config_dir / "themes"
        self.plugins_dir = self.config_dir / "plugins"
        self.cache_dir = self.config_dir / "cache"
        self.backup_dir = self.config_dir / "backups"

        # Create directories
        self._create_directories()

        # Load configuration with migration support
        self.config = self._load_config_with_migration()
        self.session = self._load_session()

        # Validate configuration
        self._validate_and_fix_config()

    def _create_directories(self):
        """Create all necessary directories"""
        directories = [
            self.config_dir,
            self.themes_dir,
            self.plugins_dir,
            self.cache_dir,
            self.backup_dir
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _load_config_with_migration(self) -> AppConfig:
        """Load configuration with automatic migration support"""
        if not self.config_file.exists():
            # Create default config
            config = AppConfig()
            self.save_config(config)
            return config

        try:
            with open(self.config_file, 'r') as f:
                data = yaml.safe_load(f) or {}

            # Check if migration is needed
            current_version = data.get('config_version', '1.0')
            if current_version != self.CONFIG_VERSION:
                data = self._migrate_config(data, current_version)

            # Add version to data
            data['config_version'] = self.CONFIG_VERSION

            return AppConfig(**data)

        except Exception as e:
            # Backup corrupted config and create new one
            self._backup_config(f"corrupted_{datetime.now().isoformat()}")
            print(f"Error loading config: {e}, using defaults")
            return AppConfig()

    def _migrate_config(self, data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """Migrate configuration from older versions"""
        print(f"Migrating configuration from version {from_version} to {self.CONFIG_VERSION}")

        # Backup before migration
        self._backup_config(f"pre_migration_{from_version}")

        if from_version == "1.0":
            # Migrate from version 1.0 to 2.0
            data = self._migrate_from_1_0(data)

        return data

    def _migrate_from_1_0(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from version 1.0 to 2.0"""
        # Add new SuperFile-inspired settings
        if 'superfile' not in data:
            data['superfile'] = SuperFileConfig().dict()

        # Migrate theme settings
        if 'theme' in data and isinstance(data['theme'], str):
            theme_name = data['theme']
            data['theme'] = SuperFileThemeConfig(name=theme_name).dict()

        # Add new AI settings
        if 'ai' not in data:
            data['ai'] = AIConfig().dict()
        elif 'openrouter_api_key' not in data['ai']:
            data['ai']['openrouter_api_key'] = None
            data['ai']['provider'] = 'openrouter'
            data['ai']['model'] = 'moonshotai/kimi-dev-72b:free'

        return data

    def _backup_config(self, suffix: str = None):
        """Create a backup of the current configuration"""
        if not self.config_file.exists():
            return

        if suffix is None:
            suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_file = self.backup_dir / f"config_{suffix}.yaml"

        try:
            shutil.copy2(self.config_file, backup_file)
            print(f"Configuration backed up to: {backup_file}")
        except Exception as e:
            print(f"Failed to backup configuration: {e}")

    def _validate_and_fix_config(self):
        """Validate configuration and fix common issues"""
        errors = self.validate()

        if errors:
            print("Configuration validation errors found:")
            for error in errors:
                print(f"  - {error}")

            # Try to fix common issues
            self._fix_common_config_issues()

    def _fix_common_config_issues(self):
        """Fix common configuration issues automatically"""
        fixed = False

        # Fix invalid startup path
        startup_path = self.get_startup_path()
        if not startup_path.exists():
            self.config.startup_path = "~"
            fixed = True

        # Fix missing AI keys
        if self.config.ai.enabled and self.config.ai.provider == "openrouter":
            if not self.config.ai.openrouter_api_key:
                # Try to get from environment
                env_key = os.getenv("OPENROUTER_API_KEY")
                if env_key:
                    self.config.ai.openrouter_api_key = env_key
                    fixed = True

        if fixed:
            self.save_config()
            print("Some configuration issues were automatically fixed.")

    def _load_config(self) -> AppConfig:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = yaml.safe_load(f)
                return AppConfig(**data)
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
                return AppConfig()
        else:
            # Create default config
            config = AppConfig()
            self.save_config(config)
            return config

    def _load_session(self) -> Dict[str, Any]:
        """Load session data"""
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_config(self, config: Optional[AppConfig] = None):
        """Save configuration to file"""
        if config is None:
            config = self.config

        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(config.dict(), f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def save_session(self, session_data: Dict[str, Any]):
        """Save session data"""
        try:
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            print(f"Error saving session: {e}")

    def get_theme(self) -> SuperFileThemeConfig:
        """Get theme configuration"""
        return self.config.theme

    def get_superfile_config(self) -> SuperFileConfig:
        """Get SuperFile-specific configuration"""
        return self.config.superfile

    def get_hotkeys(self) -> HotkeyConfig:
        """Get hotkey configuration"""
        return self.config.hotkeys

    def get_ai(self) -> AIConfig:
        """Get AI configuration"""
        return self.config.ai

    def get_ui(self) -> UIConfig:
        """Get UI configuration"""
        return self.config.ui

    def update_theme(self, theme_name: str):
        """Update theme"""
        self.config.theme.name = theme_name
        self.save_config()

    def set_ai_key(self, provider: str, api_key: str):
        """Set AI API key"""
        if provider == "openai":
            self.config.ai.openai_api_key = api_key
        elif provider == "anthropic":
            self.config.ai.anthropic_api_key = api_key
        self.save_config()

    def get_startup_path(self) -> Path:
        """Get startup path"""
        path_str = os.path.expanduser(self.config.startup_path)
        return Path(path_str)

    def get_editor(self) -> str:
        """Get preferred editor"""
        editor = self.config.editor
        if editor == "auto":
            # Auto-detect editor
            for cmd in ["nvim", "vim", "nano", "emacs", "code"]:
                if shutil.which(cmd):
                    return cmd
            return "nano"  # Fallback
        return editor

    def get_image_viewer(self) -> str:
        """Get preferred image viewer"""
        viewer = self.config.image_viewer
        if viewer == "auto":
            # Auto-detect viewer
            for cmd in ["feh", "eog", "gwenview", "ristretto"]:
                if shutil.which(cmd):
                    return cmd
            return "xdg-open"  # Fallback
        return viewer

    def get_video_player(self) -> str:
        """Get preferred video player"""
        player = self.config.video_player
        if player == "auto":
            # Auto-detect player
            for cmd in ["mpv", "vlc", "totem", "dragon"]:
                if shutil.which(cmd):
                    return cmd
            return "xdg-open"  # Fallback
        return player

    def toggle_setting(self, setting_path: str):
        """Toggle a boolean setting"""
        try:
            # Navigate to the setting using dot notation
            parts = setting_path.split('.')
            obj = self.config

            for part in parts[:-1]:
                obj = getattr(obj, part)

            current_value = getattr(obj, parts[-1])
            setattr(obj, parts[-1], not current_value)
            self.save_config()

            return not current_value
        except Exception as e:
            print(f"Error toggling setting {setting_path}: {e}")
            return None

    def get_session_data(self, key: str, default=None):
        """Get session data"""
        return self.session.get(key, default)

    def set_session_data(self, key: str, value: Any):
        """Set session data"""
        self.session[key] = value
        if self.config.remember_session:
            self.save_session(self.session)

    def get_log_path(self) -> Path:
        """Get log file path"""
        log_path = os.path.expanduser(self.config.log_file)
        return Path(log_path)

    def export_config(self, export_path: Path):
        """Export configuration to file"""
        try:
            with open(export_path, 'w') as f:
                yaml.dump(self.config.dict(), f, default_flow_style=False, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False

    def import_config(self, import_path: Path):
        """Import configuration from file"""
        try:
            with open(import_path, 'r') as f:
                data = yaml.safe_load(f)
            self.config = AppConfig(**data)
            self.save_config()
            return True
        except Exception as e:
            print(f"Error importing config: {e}")
            return False

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = AppConfig()
        self.save_config()

    # ConfigInterface implementation
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        try:
            parts = key.split('.')
            obj = self.config

            for part in parts:
                obj = getattr(obj, part)

            return obj
        except (AttributeError, KeyError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        try:
            parts = key.split('.')
            obj = self.config

            # Navigate to the parent object
            for part in parts[:-1]:
                obj = getattr(obj, part)

            # Set the final value
            setattr(obj, parts[-1], value)

        except (AttributeError, KeyError) as e:
            raise ConfigurationError(key, f"Cannot set configuration value: {e}")

    def save(self) -> None:
        """Save configuration to disk"""
        self.save_config()

    def load(self) -> None:
        """Reload configuration from disk"""
        self.config = self._load_config_with_migration()
        self.session = self._load_session()
        self._validate_and_fix_config()

    def validate(self) -> List[str]:
        """Validate configuration and return errors"""
        errors = []

        try:
            # Check paths exist
            startup_path = self.get_startup_path()
            if not startup_path.exists():
                errors.append(f"Startup path does not exist: {startup_path}")

            # Check external programs
            if not shutil.which(self.get_editor()):
                errors.append(f"Editor not found: {self.get_editor()}")

            # Check AI configuration
            if self.config.ai.enabled:
                if self.config.ai.provider == "openrouter":
                    if not self.config.ai.openrouter_api_key and not os.getenv("OPENROUTER_API_KEY"):
                        errors.append("OpenRouter API key required when AI is enabled with OpenRouter provider")
                elif self.config.ai.provider == "openai":
                    if not self.config.ai.openai_api_key and not os.getenv("OPENAI_API_KEY"):
                        errors.append("OpenAI API key required when AI is enabled with OpenAI provider")
                elif self.config.ai.provider == "anthropic":
                    if not self.config.ai.anthropic_api_key and not os.getenv("ANTHROPIC_API_KEY"):
                        errors.append("Anthropic API key required when AI is enabled with Anthropic provider")

            # Validate theme
            try:
                SuperFileThemeConfig(name=self.config.theme.name)
            except ValueError as e:
                errors.append(f"Invalid theme configuration: {e}")

            # Validate numeric ranges
            if self.config.ui.refresh_rate < 1 or self.config.ui.refresh_rate > 60:
                errors.append("Refresh rate must be between 1 and 60 FPS")

            if self.config.ai.max_tokens < 100 or self.config.ai.max_tokens > 32000:
                errors.append("AI max_tokens must be between 100 and 32000")

            if self.config.ai.temperature < 0.0 or self.config.ai.temperature > 2.0:
                errors.append("AI temperature must be between 0.0 and 2.0")

            # Validate directories
            plugin_dir = Path(os.path.expanduser(self.config.plugin_directory))
            if not plugin_dir.parent.exists():
                errors.append(f"Plugin directory parent does not exist: {plugin_dir.parent}")

        except Exception as e:
            errors.append(f"Configuration validation error: {e}")

        return errors

    def get_available_themes(self) -> List[str]:
        """Get list of available themes"""
        return ['cappuccino', 'neon', 'ocean', 'sunset', 'forest', 'catppuccin', 'dracula', 'nord']

    def create_example_config(self) -> None:
        """Create an example configuration file"""
        example_file = self.config_dir / "example_config.yaml"

        try:
            example_config = AppConfig()
            with open(example_file, 'w') as f:
                yaml.dump(example_config.dict(), f, default_flow_style=False, indent=2)
            print(f"Example configuration created at: {example_file}")
        except Exception as e:
            print(f"Failed to create example configuration: {e}")

    def list_backups(self) -> List[Path]:
        """List available configuration backups"""
        try:
            return sorted(self.backup_dir.glob("config_*.yaml"), reverse=True)
        except Exception:
            return []

    def restore_backup(self, backup_file: Path) -> bool:
        """Restore configuration from backup"""
        try:
            if not backup_file.exists():
                return False

            # Backup current config before restore
            self._backup_config("pre_restore")

            # Copy backup to current config
            shutil.copy2(backup_file, self.config_file)

            # Reload configuration
            self.load()

            print(f"Configuration restored from: {backup_file}")
            return True

        except Exception as e:
            print(f"Failed to restore backup: {e}")
            return False


# Maintain backward compatibility
Config = EnhancedConfig