"""
In-App Onboarding System

This module provides interactive onboarding and tutorial functionality
for new LaxyFile users, guiding them through key features and workflows.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import json

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table

from ..core.config import Config
from ..utils.logger import Logger


class OnboardingStep(Enum):
    """Onboarding step types"""
    WELCOME = "welcome"
    INTERFACE_TOUR = "interface_tour"
    BASIC_NAVIGATION = "basic_navigation"
    FILE_OPERATIONS = "file_operations"
    SEARCH_FEATURES = "search_features"
    AI_INTRODUCTION = "ai_introduction"
    CUSTOMIZATION = "customization"
    COMPLETION = "completion"


@dataclass
class TutorialStep:
    """Individual tutorial step configuration"""
    id: str
    title: str
    description: str
    content: str
    interactive: bool = False
    skippable: bool = True
    completion_check: Optional[Callable[[], bool]] = None
    demo_function: Optional[str] = None
    next_step: Optional[str] = None


class OnboardingManager:
    """Manages the onboarding experience for new users"""

    def __init__(self, config: Config, console: Console):
        self.config = config
        self.console = console
        self.logger = Logger()

        # Onboarding state
        self.current_step = 0
        self.completed_steps = set()
        self.user_preferences = {}
        self.onboarding_data = {}

        # UI components
        self.layout = None
        self.progress_tracker = None

        # Tutorial steps
        self.tutorial_steps = self._initialize_tutorial_steps()

        # Load previous onboarding state
        self._load_onboarding_state()

    def _initialize_tutorial_steps(self) -> List[TutorialStep]:
        """Initialize the tutorial step sequence"""
        return [
            TutorialStep(
                id="welcome",
                title="Welcome to LaxyFile",
                description="Introduction to LaxyFile's powerful features",
                content="""
Welcome to LaxyFile - the next-generation file manager that combines
traditional file management with AI-powered capabilities!

LaxyFile offers:
• SuperFile-inspired modern interface
• AI-powered file analysis and organization
• Comprehensive theme customization
• Powerful plugin system
• Cross-platform compatibility

This quick tutorial will help you get started with the essential features.
""",
                interactive=False,
                skippable=False
            ),

            TutorialStep(
                id="interface_tour",
                title="Interface Overview",
                description="Learn about LaxyFile's main interface components",
                content="""
LaxyFile's interface consists of four main areas:

1. Sidebar (Left): Bookmarks, recent locations, and directory tree
2. File Panel (Center): Main file listing and navigation
3. Preview Panel (Right): File preview and details
4. Status Bar (Bottom): Current status and information

Each component is designed for efficiency and can be customized to your needs.
""",
                interactive=True,
                demo_function="demo_interface_tour"
            ),

            TutorialStep(
                id="basic_navigation",
                title="Basic Navigation",
                description="Master file and folder navigation",
                content="""
Navigation in LaxyFile is intuitive and keyboard-friendly:

• Arrow keys: Move between files
• Enter: Open file or enter directory
• Backspace: Go to parent directory
• Ctrl+L: Type path directly
• Ctrl+H: Go to home directory

Try navigating through your files using these shortcuts!
""",
                interactive=True,
                demo_function="demo_navigation",
                completion_check=lambda: self._check_navigation_completion()
            ),

            TutorialStep(
                id="file_operations",
                title="File Operations",
                description="Learn essential file management operations",
                content="""
LaxyFile makes file operations simple and powerful:

• Ctrl+C: Copy selected files
• Ctrl+X: Cut selected files
• Ctrl+V: Paste files
• Delete: Delete selected files
• F2: Rename file
• Ctrl+A: Select all files

LaxyFile shows progress for long operations and handles conflicts intelligently.
""",
                interactive=True,
                demo_function="demo_file_operations",
                completion_check=lambda: self._check_file_operations_completion()
            ),

            TutorialStep(
                id="search_features",
                title="Search and Filtering",
                description="Discover powerful search capabilities",
                content="""
LaxyFile offers multiple ways to find your files:

• Ctrl+F: Quick search in current directory
• Ctrl+Shift+F: AI-powered content search
• Filter by file type, size, or date
• Use patterns like *.txt or image.*

The AI search understands meaning, not just keywords!
""",
                interactive=True,
                demo_function="demo_search_features"
            ),

            TutorialStep(
                id="ai_introduction",
                title="AI Assistant",
                description="Meet your intelligent file management assistant",
                content="""
LaxyFile's AI assistant can help you:

• Analyze file contents and provide insights
• Organize files automatically by type and content
• Find files using natural language queries
• Suggest optimizations and cleanup actions

Press F1 to open the AI chat anytime!
""",
                interactive=True,
                demo_function="demo_ai_features",
                skippable=True  # AI might not be configured
            ),

            TutorialStep(
                id="customization",
                title="Customization Options",
                description="Make LaxyFile truly yours",
                content="""
Customize LaxyFile to match your workflow:

• Themes: Choose from beautiful built-in themes or create your own
• Shortcuts: Customize keyboard shortcuts to your preference
• Layout: Adjust panel sizes and enable dual-pane mode
• Plugins: Extend functionality with community plugins

Access all customization options in Settings (Ctrl+,).
""",
                interactive=True,
                demo_function="demo_customization"
            ),

            TutorialStep(
                id="completion",
                title="You're All Set!",
                description="Congratulations on completing the tutorial",
                content="""
🎉 Congratulations! You've completed the LaxyFile tutorial.

You now know how to:
✓ Navigate efficiently through your files
✓ Perform essential file operations
✓ Use powerful search features
✓ Leverage AI assistance
✓ Customize your experience

Ready to explore LaxyFile with your own files?
You can always access help by pressing F1 or visiting the documentation.

Welcome to the LaxyFile community!
""",
                interactive=False,
                skippable=False
            )
        ]

    def should_show_onboarding(self) -> bool:
        """Check if onboarding should be shown to the user"""
        # Check if user has completed onboarding before
        if self.config.get('onboarding.completed', False):
            return False

        # Check if user explicitly disabled onboarding
        if self.config.get('onboarding.disabled', False):
            return False

        # Show onboarding for first-time users
        return self.config.get('app.first_run', True)

    async def start_onboarding(self) -> bool:
        """Start the interactive onboarding process"""
        if not self.should_show_onboarding():
            return False

        self.logger.info("Starting onboarding process")

        try:
            # Show welcome message
            self._show_onboarding_welcome()

            # Ask if user wants to take the tutorial
            if not Confirm.ask("Would you like to take a quick tutorial to learn LaxyFile's features?", default=True):
                self._skip_onboarding()
                return False

            # Run through tutorial steps
            success = await self._run_tutorial_sequence()

            if success:
                self._complete_onboarding()

            return success

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Tutorial interrupted. You can restart it anytime from the Help menu.[/yellow]")
            return False
        except Exception as e:
            self.logger.error(f"Error during onboarding: {e}")
            self.console.print(f"[red]An error occurred during the tutorial: {e}[/red]")
            return False

    def _show_onboarding_welcome(self):
        """Show the initial welcome screen"""
        welcome_text = Text()
        welcome_text.append("Welcome to LaxyFile!\n\n", style="bold blue")
        welcome_text.append("LaxyFile is a powerful file manager that combines traditionae management ")
        welcome_text.append("with AI-powered capabilities and a modern, customizable interface.\n\n")
        welcome_text.append("This tutorial will help you get started with the essential features in just a few minutes.")

        welcome_panel = Panel(
            Align.center(welcome_text),
            title="🚀 Getting Started",
            border_style="blue",
            padding=(2, 4)
        )

        self.console.print(welcome_panel)
        self.console.print()

    async def _run_tutorial_sequence(self) -> bool:
        """Run through the complete tutorial sequence"""
        total_steps = len(self.tutorial_steps)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
            transient=False
        ) as progress:

            tutorial_progress = progress.add_task(
                "Tutorial Progress",
                total=total_steps
            )

            for i, step in enumerate(self.tutorial_steps):
                progress.update(
                    tutorial_progress,
                    description=f"Step {i+1}/{total_steps}: {step.title}",
                    completed=i
                )

                # Show step content
                success = await self._run_tutorial_step(step, i+1, total_steps)

                if not success:
                    if step.skippable:
                        self.console.print(f"[yellow]Skipped: {step.title}[/yellow]")
                        continue
                    else:
                        return False

                # Mark step as completed
                self.completed_steps.add(step.id)
                self._save_onboarding_state()

                # Small delay for better UX
                await asyncio.sleep(0.5)

            progress.update(tutorial_progress, completed=total_steps)

        return True

    async def _run_tutorial_step(self, step: TutorialStep, step_num: int, total_steps: int) -> bool:
        """Run an individual tutorial step"""
        self.console.rule(f"[bold blue]Step {step_num}: {step.title}[/bold blue]")
        self.console.print()

        # Show step description
        description_panel = Panel(
            step.description,
            title="📋 What you'll learn",
            border_style="green",
            padding=(0, 1)
        )
        self.console.print(description_panel)
        self.console.print()

        # Show step content
        content_panel = Panel(
            step.content.strip(),
            title=f"📖 {step.title}",
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(content_panel)
        self.console.print()

        # Run interactive demo if available
        if step.interactive and step.demo_function:
            if hasattr(self, step.demo_function):
                demo_func = getattr(self, step.demo_function)
                try:
                    await demo_func()
                except Exception as e:
                    self.logger.error(f"Error in demo function {step.demo_function}: {e}")
                    self.console.print(f"[yellow]Demo unavailable: {e}[/yellow]")

        # Check completion if required
        if step.completion_check:
            try:
                if not step.completion_check():
                    self.console.print("[yellow]Step not fully completed, but continuing...[/yellow]")
            except Exception as e:
                self.logger.error(f"Error in completion check: {e}")

        # Ask to continue or skip
        self.console.print()
        if step.skippable and step_num < total_steps:
            choices = ["Continue", "Skip", "Exit Tutorial"]
            choice = Prompt.ask(
                "What would you like to do?",
                choices=choices,
                default="Continue"
            )

            if choice == "Skip":
                return True
            elif choice == "Exit Tutorial":
                return False
        else:
            if step_num < total_steps:
                input("Press Enter to continue to the next step...")

        return True

    # Demo functions for interactive steps

    async def demo_interface_tour(self):
        """Demo the interface components"""
        self.console.print("[bold green]Interface Tour Demo[/bold green]")
        self.console.print()

        # Show ASCII representation of the interface
        interface_layout = """
┌─────────────────────────────────────────────────────────────┐
│                    LaxyFile v2.0                            │
├─────────────┬───────────────────────────────────────────────┤
│   Sidebar   │              File Panel                       │
│             │                                               │
│ • Bookmarks │  📁 Documents/                               │
│ • Recent    │  📄 file1.txt        1.2KB   2024-01-15     │
│ • Drives    │  📁 Projects/        --       2024-01-14     │
│ • Tree      │  🖼️ image.jpg        2.5MB   2024-01-13     │
│             │  📊 data.csv         856B    2024-01-12     │
│             │                                               │
├─────────────┼───────────────────────────────────────────────┤
│   Preview   │              Status Bar                       │
│   Panel     │  📁 5 items • 3.7MB • AI: Ready             │
└─────────────┴───────────────────────────────────────────────┘
"""

        interface_panel = Panel(
            interface_layout,
            title="🖥️ LaxyFile Interface Layout",
            border_style="blue"
        )
        self.console.print(interface_panel)

        # Explain each component
        components = [
            ("Sidebar", "Quick access to bookmarks, recent locations, and directory tree"),
            ("File Panel", "Main area showing files and folders in the current directory"),
            ("Preview Panel", "Shows preview and details of the selected file"),
            ("Status Bar", "Displays current status, file count, and AI assistant status")
        ]

        self.console.print("\n[bold]Interface Components:[/bold]")
        for name, description in components:
            self.console.print(f"• [cyan]{name}[/cyan]: {description}")

        input("\nPress Enter to continue...")

    async def demo_navigation(self):
        """Demo basic navigation features"""
        self.console.print("[bold green]Navigation Demo[/bold green]")
        self.console.print()

        # Show navigation shortcuts table
        nav_table = Table(title="Navigation Shortcuts")
        nav_table.add_column("Shortcut", style="cyan", no_wrap=True)
        nav_table.add_column("Action", style="white")
        nav_table.add_column("Description", style="dim")

        shortcuts = [
            ("↑↓", "Navigate files", "Move selection up and down"),
            ("Enter", "Open/Enter", "Open file or enter directory"),
            ("Backspace", "Go up", "Go to parent directory"),
            ("Ctrl+L", "Go to path", "Type path directly"),
            ("Ctrl+H", "Home", "Go to home directory"),
            ("Alt+←→", "History", "Navigate back and forward")
        ]

        for shortcut, action, description in shortcuts:
            nav_table.add_row(shortcut, action, description)

        self.console.print(nav_table)

        self.console.print("\n[bold yellow]Try It:[/bold yellow]")
        self.console.print("• Use arrow keys to navigate through files")
        self.console.print("• Press Enter to open a file or folder")
        self.console.print("• Use Backspace to go back to the parent directory")

        input("\nPress Enter when you've tried the navigation shortcuts...")

    async def demo_file_operations(self):
        """Demo file operations"""
        self.console.print("[bold green]File Operations Demo[/bold green]")
        self.console.print()

        # Show file operations table
        ops_table = Table(title="File Operations")
        ops_table.add_column("Shortcut", style="cyan", no_wrap=True)
        ops_table.add_column("Operation", style="white")
        ops_table.add_column("Description", style="dim")

        operations = [
            ("Ctrl+C", "Copy", "Copy selected files to clipboard"),
            ("Ctrl+X", "Cut", "Cut selected files to clipboard"),
            ("Ctrl+V", "Paste", "Paste files from clipboard"),
            ("Delete", "Delete", "Delete selected files"),
            ("F2", "Rename", "Rename selected file"),
            ("Ctrl+A", "Select All", "Select all files in current directory")
        ]

        for shortcut, operation, description in operations:
            ops_table.add_row(shortcut, operation, description)

        self.console.print(ops_table)

        # Show operation features
        features_panel = Panel(
            """
LaxyFile's file operations include:

• Progress tracking for long operations
• Intelligent conflict resolution
• Undo support for most operations
• Batch operations for multiple files
• Verification to ensure data integrity
""",
            title="🚀 Advanced Features",
            border_style="green"
        )
        self.console.print(features_panel)

        input("\nPress Enter to continue...")

    async def demo_search_features(self):
        """Demo search and filtering features"""
        self.console.print("[bold green]Search Features Demo[/bold green]")
        self.console.print()

        # Show search types
        search_types = [
            ("Quick Search (Ctrl+F)", "Search by filename in current directory"),
            ("AI Content Search (Ctrl+Shift+F)", "Search by file content using AI"),
            ("Pattern Search", "Use wildcards like *.txt or image.*"),
            ("Advanced Filters", "Filter by type, size, date, or attributes")
        ]

        search_table = Table(title="Search Options")
        search_table.add_column("Search Type", style="cyan")
        search_table.add_column("Description", style="white")

        for search_type, description in search_types:
            search_table.add_row(search_type, description)

        self.console.print(search_table)

        # Show search examples
        examples_panel = Panel(
            """
Search Examples:

• "*.pdf" - Find all PDF files
• "image.*" - Find all image files
• "report" - Find files with "report" in the name
• AI: "vacation photos" - Find vacation-related images
• AI: "important documents" - Find important documents by content
""",
            title="🔍 Search Examples",
            border_style="yellow"
        )
        self.console.print(examples_panel)

        input("\nPress Enter to continue...")

    async def demo_ai_features(self):
        """Demo AI assistant features"""
        self.console.print("[bold green]AI Assistant Demo[/bold green]")
        self.console.print()

        # Check if AI is available
        ai_available = self.config.get('ai.enabled', False)

        if not ai_available:
            self.console.print("[yellow]AI features are not currently configured.[/yellow]")
            self.console.print("You can set up AI assistance in Settings → AI Assistant")
            input("\nPress Enter to continue...")
            return

        # Show AI capabilities
        ai_features = [
            ("File Analysis", "Analyze file content and provide insights"),
            ("Smart Organization", "Automatically organize files by type and content"),
            ("Content Search", "Find files using natural language queries"),
            ("Security Analysis", "Scan files for potential security issues"),
            ("Cleanup Suggestions", "Suggest files to delete or archive")
        ]

        ai_table = Table(title="AI Assistant Capabilities")
        ai_table.add_column("Feature", style="cyan")
        ai_table.add_column("Description", style="white")

        for feature, description in ai_features:
            ai_table.add_row(feature, description)

        self.console.print(ai_table)

        # Show AI interaction examples
        examples_panel = Panel(
            """
AI Interaction Examples:

• "Help me organize my Downloads folder"
• "What are my largest files?"
• "Find documents about budget from last month"
• "Which photos were taken on vacation?"
• "Analyze this file for security issues"

Press F1 anytime to open the AI chat!
""",
            title="🤖 AI Examples",
            border_style="magenta"
        )
        self.console.print(examples_panel)

        input("\nPress Enter to continue...")

    async def demo_customization(self):
        """Demo customization options"""
        self.console.print("[bold green]Customization Demo[/bold green]")
        self.console.print()

        # Show customization categories
        customization_options = [
            ("Themes", "Choose from built-in themes or create custom ones"),
            ("Keyboard Shortcuts", "Customize shortcuts to match your workflow"),
            ("Interface Layout", "Adjust panel sizes and enable dual-pane mode"),
            ("File Operations", "Configure default behaviors and confirmations"),
            ("AI Settings", "Configure AI providers and analysis options"),
            ("Plugins", "Extend functionality with community plugins")
        ]

        custom_table = Table(title="Customization Options")
        custom_table.add_column("Category", style="cyan")
        custom_table.add_column("Description", style="white")

        for category, description in customization_options:
            custom_table.add_row(category, description)

        self.console.print(custom_table)

        # Show popular themes
        themes_panel = Panel(
            """
Popular Themes:

• Catppuccin - Soothing pastel colors
• Dracula - Dark theme with purple accents
• Nord - Arctic-inspired color palette
• Gruvbox - Retro warm colors
• Tokyo Night - Neon-lit darkness

Access all customization options with Ctrl+, (Settings)
""",
            title="🎨 Themes & More",
            border_style="blue"
        )
        self.console.print(themes_panel)

        input("\nPress Enter to continue...")

    # Completion check functions

    def _check_navigation_completion(self) -> bool:
        """Check if user has tried navigation features"""
        # This would integrate with the actual UI to check if navigation was used
        # For now, we'll assume completion
        return True

    def _check_file_operations_completion(self) -> bool:
        """Check if user has tried file operations"""
        # This would integrate with the actual UI to check if operations were performed
        # For now, we'll assume completion
        return True

    # State management

    def _load_onboarding_state(self):
        """Load previous onboarding state from config"""
        self.completed_steps = set(self.config.get('onboarding.completed_steps', []))
        self.user_preferences = self.config.get('onboarding.preferences', {})
        self.onboarding_data = self.config.get('onboarding.data', {})

    def _save_onboarding_state(self):
        """Save current onboarding state to config"""
        self.config.set('onboarding.completed_steps', list(self.completed_steps))
        self.config.set('onboarding.preferences', self.user_preferences)
        self.config.set('onboarding.data', self.onboarding_data)
        self.config.save()

    def _skip_onboarding(self):
        """Mark onboarding as skipped"""
        self.config.set('onboarding.skipped', True)
        self.config.set('app.first_run', False)
        self.config.save()
        self.console.print("[yellow]Onboarding skipped. You can access the tutorial anytime from the Help menu.[/yellow]")

    def _complete_onboarding(self):
        """Mark onboarding as completed"""
        self.config.set('onboarding.completed', True)
        self.config.set('app.first_run', False)
        self.config.save()

        # Show completion message
        completion_text = Text()
        completion_text.append("🎉 Tutorial Complete!\n\n", style="bold green")
        completion_text.append("You're now ready to use LaxyFile effectively. ")
        completion_text.append("Remember, you can always access help by pressing F1 or ")
        completion_text.append("visiting the documentation.\n\n")
        completion_text.append("Welcome to the LaxyFile community!", style="bold blue")

        completion_panel = Panel(
            Align.center(completion_text),
            title="🏆 Congratulations!",
            border_style="green",
            padding=(2, 4)
        )

        self.console.print(completion_panel)
        input("\nPress Enter to start using LaxyFile...")

    def restart_onboarding(self):
        """Restart the onboarding process"""
        self.config.set('onboarding.completed', False)
        self.config.set('onboarding.skipped', False)
        self.completed_steps.clear()
        self._save_onboarding_state()
        self.logger.info("Onboarding reset - will show on next startup")

    def get_onboarding_progress(self) -> Dict[str, Any]:
        """Get current onboarding progress"""
        total_steps = len(self.tutorial_steps)
        completed_count = len(self.completed_steps)

        return {
            'total_steps': total_steps,
            'completed_steps': completed_count,
            'progress_percentage': (completed_count / total_steps) * 100 if total_steps > 0 else 0,
            'completed_step_ids': list(self.completed_steps),
            'is_completed': self.config.get('onboarding.completed', False),
            'is_skipped': self.config.get('onboarding.skipped', False)
        }