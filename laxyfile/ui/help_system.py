"""
Context-Sensitive Help System

This module provides context-aware help functionality, keyboard shortcut
discovery, and interactive assistance throughout the LaxyFile interface.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.markdown import Markdown

from ..core.config import Config
from ..utils.logger import Logger


class HelpContext(Enum):
    """Different contexts where help can be shown"""
    MAIN_INTERFACE = "main_interface"
    FILE_PANEL = "file_panel"
    SIDEBAR = "sidebar"
    PREVIEW_PANEL = "preview_panel"
    SEARCH_MODE = "search_mode"
    AI_CHAT = "ai_chat"
    SETTINGS = "settings"
    PLUGIN_MANAGER = "plugin_manager"
    THEME_EDITOR = "theme_editor"


@dataclass
class HelpItem:
    """Individual help item"""
    id: str
    title: str
    description: str
    content: str
    shortcuts: List[Tuple[str, str]] = None
    context: HelpContext = HelpContext.MAIN_INTERFACE
    tags: List[str] = None
    related_items: List[str] = None


class HelpSystem:
    """Context-sensitive help system for LaxyFile"""

    def __init__(self, config: Config, console: Console):
        self.config = config
        self.console = console
        self.logger = Logger()

        # Help content
        self.help_items = {}
        self.context_help = {}
        self.shortcut_help = {}

        # Current context
        self.current_context = HelpContext.MAIN_INTERFACE

        # Initialize help content
        self._initialize_help_content()

    def _initialize_help_content(self):
        """Initialize all help content"""
        self._load_main_interface_help()
        self._load_file_operations_help()
        self._load_search_help()
        self._load_ai_help()
        self._load_customization_help()
        self._load_keyboard_shortcuts()

   def show_context_help(self, context: Optional[HelpContext] = None) -> None:
        """Show help for the current or specified context"""
        if context:
            self.current_context = context

        help_content = self._get_context_help(self.current_context)

        if not help_content:
            self._show_general_help()
            return

        # Create help panel
        help_panel = Panel(
            help_content,
            title=f"📖 Help - {self.current_context.value.replace('_', ' ').title()}",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(help_panel)

    def show_keyboard_shortcuts(self, context: Optional[HelpContext] = None) -> None:
        """Show keyboard shortcuts for current or specified context"""
        shortcuts = self._get_context_shortcuts(context or self.current_context)

        if not shortcuts:
            self._show_all_shortcuts()
            return

        # Create shortcuts table
        shortcuts_table = Table(title="Keyboard Shortcuts")
        shortcuts_table.add_column("Shortcut", style="cyan", no_wrap=True)
        shortcuts_table.add_column("Action", style="white")
        shortcuts_table.add_column("Description", style="dim")

        for shortcut, action, description in shortcuts:
            shortcuts_table.add_row(shortcut, action, description)

        self.console.print(shortcuts_table)

    def search_help(self, query: str) -> List[HelpItem]:
        """Search help content by query"""
        query_lower = query.lower()
        results = []

        for help_item in self.help_items.values():
            # Search in title, description, content, and tags
            searchable_text = " ".join([
                help_item.title,
                help_item.description,
                help_item.content,
                " ".join(help_item.tags or [])
            ]).lower()

            if query_lower in searchable_text:
                results.append(help_item)

        return results

    def show_help_item(self, item_id: str) -> None:
        """Show specific help item"""
        if item_id not in self.help_items:
            self.console.print(f"[red]Help item '{item_id}' not found[/red]")
            return

        item = self.help_items[item_id]

        # Create content with shortcuts if available
        content_parts = [item.content]

        if item.shortcuts:
            shortcuts_text = "\n\n**Keyboard Shortcuts:**\n"
            for shortcut, description in item.shortcuts:
                shortcuts_text += f"• `{shortcut}`: {description}\n"
            content_parts.append(shortcuts_text)

        if item.related_items:
            related_text = "\n\n**Related Topics:**\n"
            for related_id in item.related_items:
                if related_id in self.help_items:
                    related_item = self.help_items[related_id]
                    related_text += f"• {related_item.title}\n"
            content_parts.append(related_text)

        content = "".join(content_parts)

        # Show as markdown panel
        help_panel = Panel(
            Markdown(content),
            title=f"📖 {item.title}",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(help_panel)

    def show_feature_discovery(self) -> None:
        """Show feature discovery tips"""
        tips = [
            "💡 Press F1 anytime to get context-sensitive help",
            "🔍 Use Ctrl+Shift+F for AI-powered content search",
            "🎨 Try different themes with Ctrl+T",
            "🤖 Ask the AI assistant anything with F1",
            "⚡ Create custom shortcuts in Settings",
            "🔧 Extend functionality with plugins",
            "📊 View file statistics in the preview panel",
            "🗂️ Use dual-pane mode with F6 for file comparison"
        ]

        tips_text = "\n".join(tips)

        discovery_panel = Panel(
            tips_text,
            title="💡 Feature Discovery Tips",
            border_style="yellow",
            padding=(1, 2)
        )

        self.console.print(discovery_panel)

    def _get_context_help(self, context: HelpContext) -> Optional[str]:
        """Get help content for specific context"""
        return self.context_help.get(context)

    def _get_context_shortcuts(self, context: HelpContext) -> List[Tuple[str, str, str]]:
        """Get shortcuts for specific context"""
        return self.shortcut_help.get(context, [])

    def _show_general_help(self) -> None:
        """Show general help overview"""
        general_help = """
# LaxyFile Help

Welcome to LaxyFile's help system! Here are the main areas where you can get assistance:

## Getting Help
- **F1**: Context-sensitive help
- **Ctrl+?**: Show all keyboard shortcuts
- **Help Menu**: Access tutorials and documentation

## Main Features
- **File Management**: Copy, move, delete, and organize files
- **AI Assistant**: Intelligent file analysis and organization
- **Search**: Powerful search with AI content understanding
- **Themes**: Customize appearance with built-in or custom themes
- **Plugins**: Extend functionality with community plugins

## Quick Start
1. Use arrow keys to navigate files
2. Press Enter to open files or folders
3. Use Ctrl+C/V to copy and paste files
4. Press F1 for context-specific help
5. Try Ctrl+Shift+F for AI-powered search

For more detailed help, use the specific help commands or visit the documentation.
"""

        help_panel = Panel(
            Markdown(general_help),
            title="📖 LaxyFile Help",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(help_panel)

    def _load_main_interface_help(self):
        """Load main interface help content"""
        main_help = HelpItem(
            id="main_interface",
            title="Main Interface",
            description="Overview of LaxyFile's main interface components",
            content="""
# Main Interface

LaxyFile's interface consists of four main components:

## Sidebar (Left Panel)
- **Bookmarks**: Quick access to favorite locations
- **Recent**: Recently visited directories
- **Drives**: Available storage devices
- **Directory Tree**: Hierarchical folder navigation

## File Panel (Center)
- **File List**: Main file and folder display
- **Selection**: Multi-select with visual feedback
- **Sorting**: Sort by name, size, date, or type
- **Filtering**: Filter files by various criteria

## Preview Panel (Right)
- **File Preview**: Content preview for selected files
- **Metadata**: Detailed file information
- **AI Insights**: Smart analysis and suggestions

## Status Bar (Bottom)
- **Current Path**: Active directory location
- **Selection Info**: Selected items count and size
- **AI Status**: Assistant availability and activity
- **System Info**: Performance and resource usage
""",
            shortcuts=[
                ("F9", "Toggle sidebar"),
                ("F3", "Toggle preview panel"),
                ("F6", "Toggle dual-pane mode"),
                ("Ctrl+,", "Open settings")
            ],
            context=HelpContext.MAIN_INTERFACE,
            tags=["interface", "layout", "panels", "overview"]
        )

        self.help_items[main_help.id] = main_help
        self.context_help[HelpContext.MAIN_INTERFACE] = main_help.content

    def _load_file_operations_help(self):
        """Load file operations help content"""
        file_ops_help = HelpItem(
            id="file_operations",
            title="File Operations",
            description="Essential file management operations",
            content="""
# File Operations

LaxyFile provides comprehensive file management capabilities:

## Basic Operations
- **Copy**: Duplicate files to another location
- **Move**: Transfer files to a new location
- **Delete**: Remove files (with trash support)
- **Rename**: Change file or folder names

## Advanced Features
- **Progress Tracking**: Real-time operation progress
- **Conflict Resolution**: Smart handling of duplicate names
- **Batch Operations**: Process multiple files at once
- **Undo Support**: Reverse most operations
- **Verification**: Ensure data integrity

## Archive Operations
- **Create Archives**: ZIP, TAR, 7Z formats
- **Extract Archives**: Automatic format detection
- **Preview Contents**: View archive contents without extracting
""",
            shortcuts=[
                ("Ctrl+C", "Copy selected files"),
                ("Ctrl+X", "Cut selected files"),
                ("Ctrl+V", "Paste files"),
                ("Delete", "Delete selected files"),
                ("F2", "Rename file"),
                ("Ctrl+A", "Select all files")
            ],
            context=HelpContext.FILE_PANEL,
            tags=["files", "copy", "move", "delete", "operations"]
        )

        self.help_items[file_ops_help.id] = file_ops_help

    def _load_search_help(self):
        """Load search help content"""
        search_help = HelpItem(
            id="search_features",
            title="Search and Filtering",
            description="Powerful search capabilities in LaxyFile",
            content="""
# Search and Filtering

LaxyFile offers multiple ways to find your files:

## Quick Search (Ctrl+F)
- Search by filename in current directory
- Use wildcards: `*.txt`, `image.*`
- Case-insensitive by default
- Real-time results as you type

## AI Content Search (Ctrl+Shift+F)
- Search by file content using AI
- Natural language queries
- Semantic understanding
- Cross-format content analysis

## Advanced Filtering
- **File Type**: Filter by extension or category
- **Size Range**: Find files within size limits
- **Date Range**: Filter by modification date
- **Attributes**: Hidden, read-only, executable files

## Search Examples
- `*.pdf` - All PDF files
- `image.*` - All image files
- `report` - Files with "report" in name
- AI: "vacation photos" - Vacation-related images
- AI: "important documents" - Important docs by content
""",
            shortcuts=[
                ("Ctrl+F", "Quick search"),
                ("Ctrl+Shift+F", "AI content search"),
                ("Escape", "Clear search"),
                ("F3", "Find next"),
                ("Shift+F3", "Find previous")
            ],
            context=HelpContext.SEARCH_MODE,
            tags=["search", "filter", "find", "ai", "content"]
        )

        self.help_items[search_help.id] = search_help
        self.context_help[HelpContext.SEARCH_MODE] = search_help.content

    def _load_ai_help(self):
        """Load AI assistant help content"""
        ai_help = HelpItem(
            id="ai_assistant",
            title="AI Assistant",
            description="Intelligent file management with AI",
            content="""
# AI Assistant

LaxyFile's AI assistant provides intelligent file management:

## File Analysis
- **Content Analysis**: Understand what files contain
- **Metadata Extraction**: Get detailed file information
- **Security Scanning**: Identify potential security issues
- **Duplicate Detection**: Find similar or identical files

## Smart Organization
- **Auto-categorization**: Sort files by type and content
- **Folder Suggestions**: Recommend directory structures
- **Cleanup Recommendations**: Suggest files to delete or archive
- **Workflow Automation**: Create custom organization rules

## Natural Language Interaction
- Ask questions about your files
- Request specific actions
- Get recommendations and insights
- Search by content meaning

## AI Providers
- **OpenRouter**: Cloud-based AI with multiple models
- **Ollama**: Local AI models for privacy
- **GPT4All**: Offline AI capabilities
- **Custom**: Your own AI endpoints
""",
            shortcuts=[
                ("F1", "Open AI chat"),
                ("Ctrl+Shift+A", "Quick AI query"),
                ("Ctrl+I", "Analyze selected file"),
                ("Ctrl+O", "AI organization suggestions")
            ],
            context=HelpContext.AI_CHAT,
            tags=["ai", "assistant", "analysis", "organization", "chat"]
        )

        self.help_items[ai_help.id] = ai_help
        self.context_help[HelpContext.AI_CHAT] = ai_help.content

    def _load_customization_help(self):
        """Load customization help content"""
        custom_help = HelpItem(
            id="customization",
            title="Customization",
            description="Personalize LaxyFile to match your workflow",
            content="""
# Customization

Make LaxyFile truly yours with extensive customization options:

## Themes
- **Built-in Themes**: Catppuccin, Dracula, Nord, Gruvbox, Tokyo Night
- **Custom Themes**: Create your own color schemes
- **Theme Editor**: Visual theme customization
- **Import/Export**: Share themes with the community

## Keyboard Shortcuts
- **Customizable Shortcuts**: Modify any keyboard shortcut
- **Shortcut Profiles**: Different sets for different workflows
- **Conflict Detection**: Prevent shortcut conflicts
- **Import/Export**: Share shortcut configurations

## Interface Layout
- **Panel Sizes**: Adjust sidebar and preview panel widths
- **Dual-Pane Mode**: Side-by-side file panels
- **Hide/Show Panels**: Toggle interface components
- **Responsive Design**: Adapts to terminal size

## Behavior Settings
- **File Operations**: Configure default behaviors
- **AI Settings**: Customize AI provider and models
- **Performance**: Tune for your system
- **Privacy**: Control data sharing and logging
""",
            shortcuts=[
                ("Ctrl+,", "Open settings"),
                ("Ctrl+T", "Quick theme switch"),
                ("F6", "Toggle dual-pane"),
                ("F9", "Toggle sidebar")
            ],
            context=HelpContext.SETTINGS,
            tags=["customization", "themes", "shortcuts", "settings", "layout"]
        )

        self.help_items[custom_help.id] = custom_help
        self.context_help[HelpContext.SETTINGS] = custom_help.content

    def _load_keyboard_shortcuts(self):
        """Load keyboard shortcuts for all contexts"""
        # Main interface shortcuts
        self.shortcut_help[HelpContext.MAIN_INTERFACE] = [
            ("F1", "Help", "Show context-sensitive help"),
            ("Ctrl+,", "Settings", "Open settings dialog"),
            ("Ctrl+Q", "Quit", "Exit LaxyFile"),
            ("F5", "Refresh", "Refresh current view"),
            ("F11", "Fullscreen", "Toggle fullscreen mode")
        ]

        # File panel shortcuts
        self.shortcut_help[HelpContext.FILE_PANEL] = [
            ("↑↓", "Navigate", "Move selection up/down"),
            ("Enter", "Open", "Open file or enter directory"),
            ("Backspace", "Go Up", "Go to parent directory"),
            ("Ctrl+C", "Copy", "Copy selected files"),
            ("Ctrl+V", "Paste", "Paste files"),
            ("Delete", "Delete", "Delete selected files"),
            ("F2", "Rename", "Rename selected file"),
            ("Ctrl+A", "Select All", "Select all files")
        ]

        # Search shortcuts
        self.shortcut_help[HelpContext.SEARCH_MODE] = [
            ("Ctrl+F", "Quick Search", "Search by filename"),
            ("Ctrl+Shift+F", "AI Search", "AI-powered content search"),
            ("Escape", "Clear", "Clear search and exit"),
            ("Enter", "Execute", "Execute search"),
            ("F3", "Next", "Find next result")
        ]

        # AI chat shortcuts
        self.shortcut_help[HelpContext.AI_CHAT] = [
            ("F1", "Open Chat", "Open AI assistant chat"),
            ("Ctrl+Enter", "Send", "Send message to AI"),
            ("Escape", "Close", "Close AI chat"),
            ("↑↓", "History", "Navigate message history"),
            ("Ctrl+L", "Clear", "Clear chat history")
        ]

    def _show_all_shortcuts(self):
        """Show all keyboard shortcuts organized by context"""
        self.console.print("[bold blue]All Keyboard Shortcuts[/bold blue]\n")

        for context, shortcuts in self.shortcut_help.items():
            if not shortcuts:
                continue

            context_name = context.value.replace('_', ' ').title()

            shortcuts_table = Table(title=f"{context_name} Shortcuts")
            shortcuts_table.add_column("Shortcut", style="cyan", no_wrap=True)
            shortcuts_table.add_column("Action", style="white")
            shortcuts_table.add_column("Description", style="dim")

            for shortcut, action, description in shortcuts:
                shortcuts_table.add_row(shortcut, action, description)

            self.console.print(shortcuts_table)
            self.console.print()