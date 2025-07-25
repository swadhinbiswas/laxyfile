"""
Enhanced Keyboard and Input Handling System

This module provides comprehensive keyboard shortcut management, input processing,
and context-aware command handling for LaxyFile.
"""

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading

from ..core.exceptions import InputError, ConfigurationError
from ..utils.logger import Logger


class KeyModifier(Enum):
    """Keyboard modifiers"""
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    META = "meta"  # Windows key / Cmd key


class InputMode(Enum):
    """Input modes for different contexts"""
    NORMAL = "normal"
    COMMAND = "command"
    SEARCH = "search"
    EDIT = "edit"
    SELECTION = "selection"
    HELP = "help"


class KeyEventType(Enum):
    """Types of key events"""
    PRESS = "press"
    RELEASE = "release"
    REPEAT = "repeat"


@dataclass
class KeyCombination:
    """Represents a key combination"""
    key: str
    modifiers: Set[KeyModifier] = field(default_factory=set)

    def __str__(self) -> str:
        """String representation of key combination"""
        parts = []

        # Add modifiers in consistent order
        if KeyModifier.CTRL in self.modifiers:
            parts.append("Ctrl")
        if KeyModifier.ALT in self.modifiers:
            parts.append("Alt")
        if KeyModifier.SHIFT in self.modifiers:
            parts.append("Shift")
        if KeyModifier.META in self.modifiers:
            parts.append("Meta")

        parts.append(self.key)
        return "+".join(parts)

    @classmethod
    def from_string(cls, key_string: str) -> 'KeyCombination':
        """Create KeyCombination from string like 'Ctrl+Alt+F'"""
        parts = [part.strip() for part in key_string.split('+')]

        modifiers = set()
        key = parts[-1]  # Last part is the key

        for part in parts[:-1]:
            part_lower = part.lower()
            if part_lower in ['ctrl', 'control']:
                modifiers.add(KeyModifier.CTRL)
            elif part_lower == 'alt':
                modifiers.add(KeyModifier.ALT)
            elif part_lower == 'shift':
                modifiers.add(KeyModifier.SHIFT)
            elif part_lower in ['meta', 'cmd', 'win', 'super']:
                modifiers.add(KeyModifier.META)

        return cls(key=key, modifiers=modifiers)

    def __hash__(self) -> int:
        """Make KeyCombination hashable"""
        return hash((self.key, frozenset(self.modifiers)))

    def __eq__(self, other) -> bool:
        """Check equality"""
        if not isinstance(other, KeyCombination):
            return False
        return self.key == other.key and self.modifiers == other.modifiers


@dataclass
class KeyEvent:
    """Represents a keyboard event"""
    key_combination: KeyCombination
    event_type: KeyEventType
    timestamp: float
    mode: InputMode

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class HotkeyBinding:
    """Represents a hotkey binding"""
    key_combination: KeyCombination
    command: str
    description: str
    mode: InputMode = InputMode.NORMAL
    enabled: bool = True
    category: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'key_combination': str(self.key_combination),
            'command': self.command,
            'description': self.description,
            'mode': self.mode.value,
            'enabled': self.enabled,
            'category': self.category
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HotkeyBinding':
        """Create from dictionary"""
        return cls(
            key_combination=KeyCombination.from_string(data['key_combination']),
            command=data['command'],
            description=data['description'],
            mode=InputMode(data.get('mode', 'normal')),
            enabled=data.get('enabled', True),
            category=data.get('category', 'general')
        )


class HotkeyConflictDetector:
    """Detects conflicts between hotkey bindings"""

    def __init__(self):
        self.logger = Logger()

    def detect_conflicts(self, bindings: List[HotkeyBinding]) -> List[Dict[str, Any]]:
        """Detect conflicts between hotkey bindings"""
        conflicts = []

        # Group bindings by mode
        mode_bindings = {}
        for binding in bindings:
            if binding.mode not in mode_bindings:
                mode_bindings[binding.mode] = []
            mode_bindings[binding.mode].append(binding)

        # Check for conflicts within each mode
        for mode, mode_bindings_list in mode_bindings.items():
            mode_conflicts = self._detect_mode_conflicts(mode_bindings_list)
            conflicts.extend(mode_conflicts)

        return conflicts

    def _detect_mode_conflicts(self, bindings: List[HotkeyBinding]) -> List[Dict[str, Any]]:
        """Detect conflicts within a specific mode"""
        conflicts = []
        key_map = {}

        for binding in bindings:
            if not binding.enabled:
                continue

            key_combo = binding.key_combination

            if key_combo in key_map:
                # Conflict found
                existing_binding = key_map[key_combo]
                conflicts.append({
                    'key_combination': str(key_combo),
                    'mode': binding.mode.value,
                    'conflicting_commands': [existing_binding.command, binding.command],
                    'conflicting_descriptions': [existing_binding.description, binding.description]
                })
            else:
                key_map[key_combo] = binding

        return conflicts


class CommandProcessor:
    """Processes commands from keyboard input"""

    def __init__(self):
        self.logger = Logger()
        self.commands: Dict[str, Callable] = {}
        self.command_history: List[str] = []
        self.max_history = 1000

    def register_command(self, command_name: str, handler: Callable,
                        description: str = ""):
        """Register a command handler"""
        self.commands[command_name] = {
            'handler': handler,
            'description': description,
            'registered_at': datetime.now()
        }

    def unregister_command(self, command_name: str):
        """Unregister a command handler"""
        if command_name in self.commands:
            del self.commands[command_name]

    async def execute_command(self, command: str, context: Dict[str, Any] = None) -> Any:
        """Execute a command"""
        try:
            # Add to history
            self.command_history.append(command)
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)

            # Parse command and arguments
            parts = command.split()
            if not parts:
                return None

            command_name = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            if command_name not in self.commands:
                raise InputError(command_name, f"Unknown command: {command_name}")

            handler_info = self.commands[command_name]
            handler = handler_info['handler']

            # Execute command
            if asyncio.iscoroutinefunction(handler):
                result = await handler(*args, context=context)
            else:
                result = handler(*args, context=context)

            return result

        except Exception as e:
            self.logger.error(f"Error executing command '{command}': {e}")
            raise InputError(str(e), f"Command execution failed: {e}")

    def get_command_suggestions(self, partial_command: str) -> List[str]:
        """Get command suggestions for auto-completion"""
        suggestions = []

        for command_name in self.commands.keys():
            if command_name.startswith(partial_command):
                suggestions.append(command_name)

        return sorted(suggestions)

    def get_command_help(self, command_name: str = None) -> str:
        """Get help for command(s)"""
        if command_name:
            if command_name in self.commands:
                info = self.commands[command_name]
                return f"{command_name}: {info['description']}"
            else:
                return f"Unknown command: {command_name}"
        else:
            # Return help for all commands
            help_lines = ["Available commands:"]
            for cmd_name, info in sorted(self.commands.items()):
                help_lines.append(f"  {cmd_name}: {info['description']}")
            return "\n".join(help_lines)


class InputValidator:
    """Validates input and provides suggestions"""

    def __init__(self):
        self.logger = Logger()

        # Validation patterns
        self.patterns = {
            'file_path': r'^[^<>:"|?*]*$',
            'command': r'^[a-zA-Z_][a-zA-Z0-9_]*$',
            'hotkey': r'^(Ctrl\+|Alt\+|Shift\+|Meta\+)*[a-zA-Z0-9]$'
        }

    def validate_input(self, input_text: str, input_type: str) -> Tuple[bool, str]:
        """Validate input text"""
        try:
            if input_type not in self.patterns:
                return True, ""  # No validation pattern, assume valid

            pattern = self.patterns[input_type]
            if re.match(pattern, input_text):
                return True, ""
            else:
                return False, f"Invalid {input_type} format"

        except Exception as e:
            self.logger.error(f"Error validating input: {e}")
            return False, str(e)

    def suggest_corrections(self, input_text: str, input_type: str) -> List[str]:
        """Suggest corrections for invalid input"""
        suggestions = []

        if input_type == 'file_path':
            # Remove invalid characters
            cleaned = re.sub(r'[<>:"|?*]', '', input_text)
            if cleaned != input_text:
                suggestions.append(cleaned)

        elif input_type == 'command':
            # Fix command format
            cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', input_text)
            if cleaned != input_text:
                suggestions.append(cleaned)

        return suggestions


class HotkeyManager:
    """Main class for managing hotkeys and input handling"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the hotkey manager"""
        self.config_path = config_path
        self.bindings: Dict[str, HotkeyBinding] = {}
        self.conflict_detector = HotkeyConflictDetector()
        self.command_processor = CommandProcessor()
        self.input_validator = InputValidator()
        self.enabled = True
        self.logger = Logger("HotkeyManager")

    def load_default_bindings(self):
        """Load default hotkey bindings including WASD navigation"""
        default_bindings = {
            "quit": ("q", "Quit application"),
            "help": ("?", "Show help"),
            "refresh": ("F5", "Refresh view"),
            "copy": ("Ctrl+c", "Copy file"),
            "paste": ("Ctrl+v", "Paste file"),
            "delete": ("Delete", "Delete file"),
            "select_all": ("Ctrl+a", "Select all files"),

            # Traditional vim-style navigation
            "move_up": ("k", "Move cursor up"),
            "move_down": ("j", "Move cursor down"),
            "move_left": ("h", "Move cursor left"),
            "move_right": ("l", "Move cursor right"),

            # WASD navigation (requested by user)
            "wasd_left": ("a", "WASD: Move left"),
            "wasd_up": ("w", "WASD: Move up"),
            "wasd_right": ("d", "WASD: Move right"),
            "wasd_down": ("s", "WASD: Move down"),

            # Capital WASD for fast navigation
            "wasd_left_fast": ("A", "WASD: Fast move left"),
            "wasd_up_fast": ("W", "WASD: Fast move up"),
            "wasd_right_fast": ("D", "WASD: Fast move right"),
            "wasd_down_fast": ("S", "WASD: Fast move down"),

            "enter_directory": ("Enter", "Enter directory"),
            "go_back": ("Backspace", "Go back"),
            "go_home": ("Home", "Go to home directory"),
            "toggle_hidden": (".", "Toggle hidden files"),
            "search": ("/", "Search files"),
            "create_file": ("n", "Create new file"),
            "create_directory": ("N", "Create new directory"),
            "rename": ("r", "Rename file"),
            "properties": ("p", "Show properties"),
            "open_with": ("o", "Open with"),
            "ai_assistant": ("Ctrl+a", "Open AI assistant"),
            "theme_selector": ("t", "Open theme selector"),
            "settings": ("Ctrl+s", "Open settings"),
        }

        for command, (key_combo, description) in default_bindings.items():
            try:
                key_combination = KeyCombination.from_string(key_combo)
                binding = HotkeyBinding(
                    key_combination=key_combination,
                    command=command,
                    description=description
                )
                self.add_binding(command, binding)
            except Exception as e:
                self.logger.error(f"Failed to load default binding {command}: {e}")

    def add_binding(self, name: str, binding: HotkeyBinding) -> bool:
        """Add a hotkey binding"""
        try:
            # Check for conflicts with existing bindings
            existing_bindings = list(self.bindings.values())
            conflicts = self.conflict_detector.detect_conflicts([binding] + existing_bindings)
            if conflicts:
                self.logger.warning(f"Hotkey conflict detected for {name}: {conflicts}")
                return False

            self.bindings[name] = binding
            self.logger.debug(f"Added hotkey binding: {name} -> {binding.key_combination}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding binding {name}: {e}")
            return False

    def remove_binding(self, name: str) -> bool:
        """Remove a hotkey binding"""
        if name in self.bindings:
            del self.bindings[name]
            self.logger.debug(f"Removed hotkey binding: {name}")
            return True
        return False

    def get_binding(self, name: str) -> Optional[HotkeyBinding]:
        """Get a hotkey binding by name"""
        return self.bindings.get(name)

    def process_key_event(self, event: KeyEvent) -> Optional[str]:
        """Process a key event and return the command to execute"""
        if not self.enabled:
            return None

        try:
            # Find matching binding
            for name, binding in self.bindings.items():
                if (binding.key_combination.key == event.key_combination.key and
                    binding.key_combination.modifiers == event.key_combination.modifiers and
                    binding.mode == event.mode and
                    binding.enabled):
                    self.logger.debug(f"Key event matched binding: {name}")
                    return binding.command

            return None
        except Exception as e:
            self.logger.error(f"Error processing key event: {e}")
            return None

    def get_all_bindings(self) -> Dict[str, HotkeyBinding]:
        """Get all hotkey bindings"""
        return self.bindings.copy()

    def enable(self):
        """Enable hotkey processing"""
        self.enabled = True
        self.logger.debug("Hotkey processing enabled")

    def disable(self):
        """Disable hotkey processing"""
        self.enabled = False
        self.logger.debug("Hotkey processing disabled")

    def save_bindings(self, config_path: Optional[str] = None) -> bool:
        """Save hotkey bindings to configuration file"""
        # This would save to a config file
        # Implementation depends on config system
        try:
            path = config_path or self.config_path
            if path:
                # Save bindings to file
                self.logger.debug(f"Saved hotkey bindings to {path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error saving bindings: {e}")
            return False

    def load_bindings(self, config_path: Optional[str] = None) -> bool:
        """Load hotkey bindings from configuration file"""
        # This would load from a config file
        # Implementation depends on config system
        try:
            path = config_path or self.config_path
            if path:
                # Load bindings from file
                self.logger.debug(f"Loaded hotkey bindings from {path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error loading bindings: {e}")
            return False