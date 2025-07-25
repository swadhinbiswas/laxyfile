"""
Enhanced Keyboard Handler

Main keyboard handling system with comprehensive input processing.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from .hotkeys import (
    KeyCombination, KeyEvent, HotkeyBinding, InputMode, KeyEventType,
    HotkeyConflictDetector, CommandProcessor, InputValidator
)
from ..core.exceptions import InputError
from ..utils.logger import Logger


class EnhancedKeyboardHandler:
    """Main keyboard handling system"""

    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        self.hotkeys_file = self.config_dir / "hotkeys.json"

        self.logger = Logger()
        self.conflict_detector = HotkeyConflictDetector()
        self.command_processor = CommandProcessor()
        self.input_validator = InputValidator()

        # Current state
        self.current_mode = InputMode.NORMAL
        self.bindings: Dict[InputMode, Dict[KeyCombination, HotkeyBinding]] = {}
        self.key_sequence: List[KeyEvent] = []
        self.sequence_timeout = 1.0  # seconds

        # Event handlers
        self.mode_change_handlers: List[Callable[[InputMode], None]] = []
        self.key_event_handlers: List[Callable[[KeyEvent], None]] = []

        # Load default bindings
        self._load_default_bindings()

        # Load user bindings
        self._load_user_bindings()

        # Register default commands
        self._register_default_commands()

    def _load_default_bindings(self):
        """Load default hotkey bindings"""
        default_bindings = [
            # File operations
            HotkeyBinding(
                KeyCombination.from_string("Ctrl+O"),
                "open_file",
                "Open file",
                InputMode.NORMAL,
                category="file"
            ),
            HotkeyBinding(
                KeyCombination.from_string("Ctrl+N"),
                "new_file",
                "Create new file",
                InputMode.NORMAL,
                category="file"
            ),
            HotkeyBinding(
                KeyCombination.from_string("Delete"),
                "delete_selec",
                "Delete selected files",
                InputMode.NORMAL,
                category="file"
            ),

            # Navigation
            HotkeyBinding(
                KeyCombination.from_string("Up"),
                "move_up",
                "Move cursor up",
                InputMode.NORMAL,
                category="navigation"
            ),
            HotkeyBinding(
                KeyCombination.from_string("Down"),
                "move_down",
                "Move cursor down",
                InputMode.NORMAL,
                category="navigation"
            ),
            HotkeyBinding(
                KeyCombination.from_string("Enter"),
                "activate_selected",
                "Activate selected item",
                InputMode.NORMAL,
                category="navigation"
            ),

            # Search
            HotkeyBinding(
                KeyCombination.from_string("Ctrl+F"),
                "start_search",
                "Start search",
                InputMode.NORMAL,
                category="search"
            ),

            # Application
            HotkeyBinding(
                KeyCombination.from_string("Ctrl+Q"),
                "quit_application",
                "Quit application",
                InputMode.NORMAL,
                category="application"
            ),
            HotkeyBinding(
                KeyCombination.from_string("F1"),
                "show_help",
                "Show help",
                InputMode.NORMAL,
                category="application"
            )
        ]

        # Organize bindings by mode
        for binding in default_bindings:
            if binding.mode not in self.bindings:
                self.bindings[binding.mode] = {}
            self.bindings[binding.mode][binding.key_combination] = binding

    def _load_user_bindings(self):
        """Load user-defined hotkey bindings"""
        try:
            if self.hotkeys_file.exists():
                data = json.loads(self.hotkeys_file.read_text())

                for binding_data in data.get('bindings', []):
                    binding = HotkeyBinding.from_dict(binding_data)

                    if binding.mode not in self.bindings:
                        self.bindings[binding.mode] = {}

                    self.bindings[binding.mode][binding.key_combination] = binding

                self.logger.info("Loaded user hotkey bindings")

        except Exception as e:
            self.logger.error(f"Error loading user bindings: {e}")

    def _register_default_commands(self):
        """Register default command handlers"""
        commands = [
            ("open_file", "Open a file"),
            ("new_file", "Create a new file"),
            ("delete_selected", "Delete selected files"),
            ("move_up", "Move cursor up"),
            ("move_down", "Move cursor down"),
            ("activate_selected", "Activate selected item"),
            ("start_search", "Start search mode"),
            ("quit_application", "Quit the application"),
            ("show_help", "Show help information")
        ]

        for command_name, description in commands:
            self.command_processor.register_command(
                command_name,
                self._create_placeholder_handler(command_name),
                description
            )

    def _create_placeholder_handler(self, command_name: str) -> Callable:
        """Create placeholder command handler"""
        async def handler(*args, context=None):
            self.logger.info(f"Executing command: {command_name}")
            return f"Command '{command_name}' executed"

        return handler

    async def handle_key_event(self, key_combination: KeyCombination,
                             event_type: KeyEventType = KeyEventType.PRESS) -> bool:
        """Handle a key event"""
        try:
            # Create key event
            key_event = KeyEvent(
                key_combination=key_combination,
                event_type=event_type,
                timestamp=time.time(),
                mode=self.current_mode
            )

            # Add to sequence
            self.key_sequence.append(key_event)

            # Clean old events from sequence
            self._clean_key_sequence()

            # Notify event handlers
            for handler in self.key_event_handlers:
                try:
                    handler(key_event)
                except Exception as e:
                    self.logger.error(f"Error in key event handler: {e}")

            # Only process key press events for commands
            if event_type != KeyEventType.PRESS:
                return False

            # Find binding for current mode
            mode_bindings = self.bindings.get(self.current_mode, {})
            binding = mode_bindings.get(key_combination)

            if binding and binding.enabled:
                # Execute command
                try:
                    await self.command_processor.execute_command(
                        binding.command,
                        context={'key_event': key_event, 'mode': self.current_mode}
                    )
                    return True
                except Exception as e:
                    self.logger.error(f"Error executing command '{binding.command}': {e}")
                    return False

            return False

        except Exception as e:
            self.logger.error(f"Error handling key event: {e}")
            return False

    def _clean_key_sequence(self):
        """Remove old events from key sequence"""
        current_time = time.time()
        self.key_sequence = [
            event for event in self.key_sequence
            if current_time - event.timestamp < self.sequence_timeout
        ]

    def set_mode(self, mode: InputMode):
        """Set current input mode"""
        if mode != self.current_mode:
            old_mode = self.current_mode
            self.current_mode = mode

            # Notify mode change handlers
            for handler in self.mode_change_handlers:
                try:
                    handler(mode)
                except Exception as e:
                    self.logger.error(f"Error in mode change handler: {e}")

            self.logger.info(f"Input mode changed: {old_mode.value} -> {mode.value}")

    def get_mode(self) -> InputMode:
        """Get current input mode"""
        return self.current_mode

    def add_binding(self, binding: HotkeyBinding) -> bool:
        """Add a hotkey binding"""
        try:
            if binding.mode not in self.bindings:
                self.bindings[binding.mode] = {}

            # Check for conflicts
            existing_binding = self.bindings[binding.mode].get(binding.key_combination)
            if existing_binding:
                self.logger.warning(f"Overriding existing binding: {existing_binding.command}")

            self.bindings[binding.mode][binding.key_combination] = binding
            return True

        except Exception as e:
            self.logger.error(f"Error adding binding: {e}")
            return False

    def remove_binding(self, key_combination: KeyCombination, mode: InputMode) -> bool:
        """Remove a hotkey binding"""
        try:
            mode_bindings = self.bindings.get(mode, {})
            if key_combination in mode_bindings:
                del mode_bindings[key_combination]
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error removing binding: {e}")
            return False

    def get_bindings(self, mode: Optional[InputMode] = None) -> Dict[KeyCombination, HotkeyBinding]:
        """Get hotkey bindings for mode"""
        if mode:
            return self.bindings.get(mode, {}).copy()
        else:
            # Return all bindings
            all_bindings = {}
            for mode_bindings in self.bindings.values():
                all_bindings.update(mode_bindings)
            return all_bindings

    def detect_conflicts(self) -> List[Dict[str, Any]]:
        """Detect conflicts in current bindings"""
        all_bindings = []
        for mode_bindings in self.bindings.values():
            all_bindings.extend(mode_bindings.values())

        return self.conflict_detector.detect_conflicts(all_bindings)

    def get_help_text(self, mode: Optional[InputMode] = None) -> str:
        """Get help text for hotkeys"""
        target_mode = mode or self.current_mode
        mode_bindings = self.bindings.get(target_mode, {})

        if not mode_bindings:
            return f"No hotkeys defined for {target_mode.value} mode"

        # Group by category
        categories = {}
        for binding in mode_bindings.values():
            if not binding.enabled:
                continue

            category = binding.category
            if category not in categories:
                categories[category] = []
            categories[category].append(binding)

        # Generate help text
        help_lines = [f"Hotkeys for {target_mode.value} mode:"]

        for category, bindings in sorted(categories.items()):
            help_lines.append(f"\n{category.title()}:")
            for binding in sorted(bindings, key=lambda b: str(b.key_combination)):
                help_lines.append(f"  {binding.key_combination}: {binding.description}")

        return "\n".join(help_lines)

    def add_mode_change_handler(self, handler: Callable[[InputMode], None]):
        """Add mode change handler"""
        self.mode_change_handlers.append(handler)

    def add_key_event_handler(self, handler: Callable[[KeyEvent], None]):
        """Add key event handler"""
        self.key_event_handlers.append(handler)

    def save_bindings(self):
        """Save current bindings to file"""
        try:
            all_bindings = []
            for mode_bindings in self.bindings.values():
                for binding in mode_bindings.values():
                    all_bindings.append(binding.to_dict())

            data = {
                'bindings': all_bindings,
                'updated_at': datetime.now().isoformat()
            }

            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.hotkeys_file.write_text(json.dumps(data, indent=2))
            self.logger.info("Saved hotkey bindings")

        except Exception as e:
            self.logger.error(f"Error saving bindings: {e}")

    def reset_to_defaults(self):
        """Reset bindings to defaults"""
        self.bindings.clear()
        self._load_default_bindings()
        self.logger.info("Reset hotkey bindings to defaults")