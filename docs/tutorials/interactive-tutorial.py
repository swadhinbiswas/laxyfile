#!/usr/bin/env python3
"""
LaxyFile Interactive Tutorial

An interactive tutorial that guides users through LaxyFile's key features
with hands-on exercises and real-time feedback.
"""

import os
import sys
import time
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.layout import Layout
from rich.live import Live

# Add LaxyFile to path for tutorial
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from laxyfile.core.config import Config
    from laxyfile.core.advanced_file_manager import AdvancedFileManager
    from laxyfile.ui.superfile_ui import SuperFileUI
    from laxyfile.ai.advanced_assistant import AdvancedAIAssistant
    LAXYFILE_AVAILABLE = True
except ImportError:
    LAXYFILE_AVAILABLE = False


@dataclass
class TutorialStep:
    """Represents a single tutorial step"""
    title: str
    description: str
    instructions: List[str]
    demo_function: Optional[str] = None
    validation_function: Optional[str] = None
    skip_if_unavailable: bool = False


class InteractiveTutorial:
    """Main tutorial class that guides users through LaxyFile features"""

    def __init__(self):
        self.console = Console()
        self.tutorial_dir = None
        self.config = None
        self.file_manager = None
        self.ui = None
        self.ai_assistant = None
        self.current_step = 0

        # Tutol steps
        self.steps = [
            TutorialStep(
                title="Welcome to LaxyFile",
                description="Introduction to LaxyFile and tutorial setup",
                instructions=[
                    "Welcome to the LaxyFile interactive tutorial!",
                    "This tutorial will guide you through LaxyFile's key features",
                    "We'll create a temporary workspace for hands-on practice",
                    "Press Enter to continue..."
                ],
                demo_function="demo_welcome"
            ),
            TutorialStep(
                title="Basic Navigation",
                description="Learn how to navigate files and folders",
                instructions=[
                    "Learn basic navigation in LaxyFile",
                    "Practice moving between directories",
                    "Understand the interface layout",
                    "Try keyboard shortcuts for navigation"
                ],
                demo_function="demo_navigation",
                validation_function="validate_navigation"
            ),
            TutorialStep(
                title="File Operations",
                description="Master copy, move, and delete operations",
                instructions=[
                    "Learn essential file operations",
                    "Practice copying and moving files",
                    "Understand batch operations",
                    "Try different selection methods"
                ],
                demo_function="demo_file_operations",
                validation_function="validate_file_operations"
            ),
            TutorialStep(
                title="Search and Filtering",
                description="Find files quickly with powerful search",
                instructions=[
                    "Learn LaxyFile's search capabilities",
                    "Practice different search patterns",
                    "Use filters to narrow results",
                    "Try advanced search operators"
                ],
                demo_function="demo_search",
                validation_function="validate_search"
            ),
            TutorialStep(
                title="AI Assistant Basics",
                description="Get started with AI-powered file management",
                instructions=[
                    "Introduction to LaxyFile's AI assistant",
                    "Learn how to analyze files with AI",
                    "Practice asking AI questions",
                    "Understand AI-powered organization"
                ],
                demo_function="demo_ai_basics",
                validation_function="validate_ai_basics",
                skip_if_unavailable=True
            ),
            TutorialStep(
                title="Theme Customization",
                description="Personalize LaxyFile's appearance",
                instructions=[
                    "Explore LaxyFile's theme system",
                    "Try different built-in themes",
                    "Learn about theme customization",
                    "Create your own theme variant"
                ],
                demo_function="demo_themes",
                validation_function="validate_themes"
            ),
            TutorialStep(
                title="Advanced Features",
                description="Discover powerful advanced capabilities",
                instructions=[
                    "Learn about advanced LaxyFile features",
                    "Practice with dual-pane mode",
                    "Try archive operations",
                    "Explore plugin system"
                ],
                demo_function="demo_advanced",
                validation_function="validate_advanced"
            ),
            TutorialStep(
                title="Tutorial Complete",
                description="Congratulations on completing the tutorial!",
                instructions=[
                    "🎉 Congratulations! You've completed the LaxyFile tutorial",
                    "You've learned the essential features of LaxyFile",
                    "Continue exploring with the full application",
                    "Check out the documentation for more advanced topics"
                ],
                demo_function="demo_completion"
            )
        ]

    def setup_tutorial_environment(self):
        """Set up a temporary environment for the tutorial"""
        self.console.print("\n[bold blue]Setting up tutorial environment...[/bold blue]")

        # Create temporary directory
        self.tutorial_dir = Path(tempfile.mkdtemp(prefix="laxyfile_tutorial_"))

        # Create sample directory structure
        sample_structure = {
            "Documents": {
                "reports": ["quarterly_report.pdf", "annual_summary.docx"],
                "presentations": ["project_overview.pptx", "team_meeting.pdf"],
                "notes": ["meeting_notes.txt", "ideas.md", "todo.txt"]
            },
            "Pictures": {
                "vacation": ["beach.jpg", "sunset.png", "family.jpg"],
                "work": ["screenshot1.png", "diagram.svg"],
                "misc": ["random.gif", "meme.jpg"]
            },
            "Downloads": [
                "installer.exe", "document.pdf", "music.mp3",
                "archive.zip", "readme.txt", "data.csv"
            ],
            "Projects": {
                "laxyfile": {
                    "src": ["main.py", "config.py", "utils.py"],
                    "docs": ["README.md", "CHANGELOG.md"],
                    "tests": ["test_main.py", "test_utils.py"]
                },
                "website": {
                    "html": ["index.html", "about.html"],
                    "css": ["style.css", "theme.css"],
                    "js": ["script.js", "utils.js"]
                }
            }
        }

        self._create_directory_structure(self.tutorial_dir, sample_structure)

        # Initialize LaxyFile components if available
        if LAXYFILE_AVAILABLE:
            try:
                self.config = Config()
                self.file_manager = AdvancedFileManager(self.config)
                self.ai_assistant = AdvancedAIAssistant(self.config)
                self.console.print("[green]✓[/green] LaxyFile components initialized")
            except Exception as e:
                self.console.print(f"[yellow]⚠[/yellow] LaxyFile components not fully available: {e}")

        self.console.print(f"[green]✓[/green] Tutorial environment created at: {self.tutorial_dir}")
        time.sleep(1)

    def _create_directory_structure(self, base_path: Path, structure: Dict):
        """Recursively create directory structure with sample files"""
        for name, content in structure.items():
            path = base_path / name

            if isinstance(content, dict):
                # It's a directory
                path.mkdir(exist_ok=True)
                self._create_directory_structure(path, content)
            elif isinstance(content, list):
                # It's a directory with files
                path.mkdir(exist_ok=True)
                for filename in content:
                    file_path = path / filename
                    self._create_sample_file(file_path)
            else:
                # It's a single file
                self._create_sample_file(path)

    def _create_sample_file(self, file_path: Path):
        """Create a sample file with appropriate content"""
        extension = file_path.suffix.lower()

        # Sample content based on file type
        content_templates = {
            '.txt': "This is a sample text file created for the LaxyFile tutorial.\nIt contains some example content for demonstration purposes.\n",
            '.md': "# Sample Markdown File\n\nThis is a **sample** markdown file for the tutorial.\n\n## Features\n- Easy to read\n- Supports formatting\n- Great for documentation\n",
            '.py': "#!/usr/bin/env python3\n\"\"\"\nSample Python file for LaxyFile tutorial\n\"\"\"\n\ndef hello_world():\n    print('Hello from LaxyFile tutorial!')\n\nif __name__ == '__main__':\n    hello_world()\n",
            '.js': "// Sample JavaScript file for LaxyFile tutorial\n\nfunction greetUser(name) {\n    console.log(`Hello, ${name}! Welcome to LaxyFile.`);\n}\n\ngreetUser('Tutorial User');\n",
            '.html': "<!DOCTYPE html>\n<html>\n<head>\n    <title>LaxyFile Tutorial</title>\n</head>\n<body>\n    <h1>Welcome to LaxyFile</h1>\n    <p>This is a sample HTML file.</p>\n</body>\n</html>\n",
            '.css': "/* Sample CSS file for LaxyFile tutorial */\n\nbody {\n    font-family: Arial, sans-serif;\n    margin: 20px;\n    background-color: #f0f0f0;\n}\n\nh1 {\n    color: #333;\n    text-align: center;\n}\n",
            '.json': '{\n  "name": "LaxyFile Tutorial",\n  "version": "1.0.0",\n  "description": "Sample JSON file for tutorial",\n  "features": ["file management", "AI assistant", "themes"]\n}\n',
            '.csv': "Name,Age,City,Occupation\nJohn Doe,30,New York,Developer\nJane Smith,25,San Francisco,Designer\nBob Johnson,35,Chicago,Manager\n"
        }

        # Default content for unknown extensions
        default_content = f"Sample file: {file_path.name}\nCreated for LaxyFile tutorial\nFile type: {extension or 'unknown'}\n"

        content = content_templates.get(extension, default_content)

        try:
            file_path.write_text(content, encoding='utf-8')
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not create {file_path}: {e}[/yellow]")

    def run_tutorial(self):
        """Run the complete interactive tutorial"""
        self.console.clear()
        self.show_tutorial_header()

        # Setup environment
        self.setup_tutorial_environment()

        # Run through tutorial steps
        while self.current_step < len(self.steps):
            step = self.steps[self.current_step]

            # Skip step if LaxyFile is not available and step requires it
            if step.skip_if_unavailable and not LAXYFILE_AVAILABLE:
                self.console.print(f"[yellow]Skipping step: {step.title} (LaxyFile not fully available)[/yellow]")
                self.current_step += 1
                continue

            if not self.run_tutorial_step(step):
                break  # User chose to exit

            self.current_step += 1

        # Cleanup
        self.cleanup_tutorial_environment()

    def show_tutorial_header(self):
        """Display the tutorial header"""
        header_text = Text()
        header_text.append("LaxyFile Interactive Tutorial", style="bold blue")
        header_text.append("\n")
        header_text.append("Learn LaxyFile's features with hands-on practice", style="italic")

        header_panel = Panel(
            header_text,
            title="🚀 Welcome",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(header_panel)
        self.console.print()

    def run_tutorial_step(self, step: TutorialStep) -> bool:
        """Run a single tutorial step"""
        self.console.rule(f"[bold blue]Step {self.current_step + 1}: {step.title}[/bold blue]")
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

        # Show instructions
        for i, instruction in enumerate(step.instructions, 1):
            self.console.print(f"[bold cyan]{i}.[/bold cyan] {instruction}")
        self.console.print()

        # Run demo if available
        if step.demo_function and hasattr(self, step.demo_function):
            if not Confirm.ask("Ready to start this step?", default=True):
                return False

            demo_func = getattr(self, step.demo_function)
            try:
                demo_func()
            except Exception as e:
                self.console.print(f"[red]Error in demo: {e}[/red]")

        # Run validation if available
        if step.validation_function and hasattr(self, step.validation_function):
            validation_func = getattr(self, step.validation_function)
            try:
                if not validation_func():
                    self.console.print("[yellow]Step validation failed, but continuing...[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error in validation: {e}[/red]")

        # Ask to continue
        self.console.print()
        if self.current_step < len(self.steps) - 1:
            return Confirm.ask("Continue to next step?", default=True)

        return True

    # Demo functions for each tutorial step

    def demo_welcome(self):
        """Welcome demo"""
        self.console.print("[bold green]Welcome to LaxyFile![/bold green]")
        self.console.print()

        # Show tutorial directory structure
        self.console.print("📁 Tutorial workspace created with sample files:")
        self._show_directory_tree(self.tutorial_dir, max_depth=2)

        self.console.print()
        self.console.print("This tutorial will teach you:")
        features = [
            "Basic file navigation and operations",
            "Advanced search and filtering",
            "AI-powered file management",
            "Theme customization",
            "Advanced features and plugins"
        ]

        for feature in features:
            self.console.print(f"  • {feature}")

        input("\nPress Enter to continue...")

    def demo_navigation(self):
        """Navigation demo"""
        self.console.print("[bold blue]File Navigation Demo[/bold blue]")
        self.console.print()

        if not LAXYFILE_AVAILABLE:
            self.console.print("This demo shows basic navigation concepts:")
            self.console.print("• Use arrow keys to move between files")
            self.console.print("• Press Enter to open files/folders")
            self.console.print("• Use Backspace to go to parent directory")
            self.console.print("• Ctrl+L to type a path directly")
            input("\nPress Enter to continue...")
            return

        # Simulate navigation through tutorial directory
        current_path = self.tutorial_dir

        self.console.print(f"Starting in: [bold]{current_path}[/bold]")
        self._show_directory_contents(current_path)

        # Simulate navigation steps
        navigation_steps = [
            ("Documents", "Let's navigate to the Documents folder"),
            ("reports", "Now let's look at the reports subfolder"),
            ("..", "Going back to Documents"),
            ("..", "Going back to the root tutorial directory")
        ]

        for target, description in navigation_steps:
            input(f"\n{description}. Press Enter to continue...")

            if target == "..":
                current_path = current_path.parent
            else:
                current_path = current_path / target

            self.console.print(f"Now in: [bold]{current_path}[/bold]")
            if current_path.exists():
                self._show_directory_contents(current_path)

    def demo_file_operations(self):
        """File operations demo"""
        self.console.print("[bold blue]File Operations Demo[/bold blue]")
        self.console.print()

        # Create a temporary workspace for operations
        ops_dir = self.tutorial_dir / "file_operations_demo"
        ops_dir.mkdir(exist_ok=True)

        # Create some test files
        test_files = ["test1.txt", "test2.txt", "test3.txt"]
        for filename in test_files:
            (ops_dir / filename).write_text(f"Content of {filename}")

        self.console.print("Created test files for operations demo:")
        self._show_directory_contents(ops_dir)

        # Demonstrate copy operation
        input("\nPress Enter to demonstrate file copying...")

        copy_dir = ops_dir / "copies"
        copy_dir.mkdir(exist_ok=True)

        for filename in test_files[:2]:  # Copy first two files
            src = ops_dir / filename
            dst = copy_dir / filename
            shutil.copy2(src, dst)
            self.console.print(f"[green]✓[/green] Copied {filename} to copies/")

        self.console.print("\nAfter copying:")
        self._show_directory_contents(ops_dir)

        # Demonstrate move operation
        input("\nPress Enter to demonstrate file moving...")

        move_dir = ops_dir / "moved"
        move_dir.mkdir(exist_ok=True)

        src = ops_dir / test_files[2]  # Move the third file
        dst = move_dir / test_files[2]
        shutil.move(str(src), str(dst))
        self.console.print(f"[green]✓[/green] Moved {test_files[2]} to moved/")

        self.console.print("\nAfter moving:")
        self._show_directory_contents(ops_dir)

        self.console.print("\n[bold green]File operations completed![/bold green]")

    def demo_search(self):
        """Search demo"""
        self.console.print("[bold blue]Search and Filtering Demo[/bold blue]")
        self.console.print()

        if not LAXYFILE_AVAILABLE:
            self.console.print("Search concepts in LaxyFile:")
            self.console.print("• Ctrl+F for quick search")
            self.console.print("• Use wildcards: *.txt, image.*")
            self.console.print("• Search by content with AI")
            self.console.print("• Filter by file type, size, date")
            input("\nPress Enter to continue...")
            return

        # Demonstrate different search patterns
        search_patterns = [
            ("*.txt", "Find all text files"),
            ("*.py", "Find all Python files"),
            ("*report*", "Find files with 'report' in name"),
            ("*.md", "Find all Markdown files")
        ]

        for pattern, description in search_patterns:
            self.console.print(f"\n[bold cyan]Search: {pattern}[/bold cyan] - {description}")

            # Simulate search results
            matches = []
            for file_path in self.tutorial_dir.rglob(pattern):
                if file_path.is_file():
                    matches.append(file_path.relative_to(self.tutorial_dir))

            if matches:
                self.console.print(f"Found {len(matches)} matches:")
                for match in matches[:5]:  # Show first 5 matches
                    self.console.print(f"  📄 {match}")
                if len(matches) > 5:
                    self.console.print(f"  ... and {len(matches) - 5} more")
            else:
                self.console.print("No matches found")

            time.sleep(1)

    def demo_ai_basics(self):
        """AI assistant demo"""
        self.console.print("[bold blue]AI Assistant Demo[/bold blue]")
        self.console.print()

        if not LAXYFILE_AVAILABLE or not self.ai_assistant:
            self.console.print("AI Assistant features (requires setup):")
            self.console.print("• Analyze files with AI")
            self.console.print("• Get organization suggestions")
            self.console.print("• Search by content meaning")
            self.console.print("• Ask questions about files")
            input("\nPress Enter to continue...")
            return

        # Simulate AI interactions
        ai_demos = [
            {
                "query": "What types of files do I have in my Documents folder?",
                "response": "I found several types of files in your Documents folder:\n• PDF reports (2 files)\n• Word documents (1 file)\n• PowerPoint presentations (2 files)\n• Text files and notes (3 files)"
            },
            {
                "query": "Help me organize my Downloads folder",
                "response": "I can help organize your Downloads folder! I found:\n• 1 executable file (installer.exe)\n• 2 document files (document.pdf, readme.txt)\n• 1 media file (music.mp3)\n• 1 archive (archive.zip)\n• 1 data file (data.csv)\n\nWould you like me to create folders by file type?"
            },
            {
                "query": "Find files related to 'project'",
                "response": "I found several project-related files:\n• Projects/laxyfile/ (entire project folder)\n• Documents/presentations/project_overview.pptx\n• Projects/website/ (web project)\n\nThese seem to be your active development projects."
            }
        ]

        for demo in ai_demos:
            self.console.print(f"[bold cyan]You:[/bold cyan] {demo['query']}")

            # Simulate AI thinking
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("AI is thinking...", total=None)
                time.sleep(2)

            self.console.print(f"[bold green]AI:[/bold green] {demo['response']}")
            self.console.print()

            input("Press Enter for next AI demo...")

    def demo_themes(self):
        """Theme customization demo"""
        self.console.print("[bold blue]Theme Customization Demo[/bold blue]")
        self.console.print()

        # Show available themes
        themes = [
            ("catppuccin", "Soothing pastel colors", "#1e1e2e"),
            ("dracula", "Dark with purple accents", "#282a36"),
            ("nord", "Arctic-inspired blues", "#2e3440"),
            ("gruvbox", "Retro warm colors", "#282828"),
            ("tokyo-night", "Neon-lit darkness", "#1a1b26")
        ]

        self.console.print("Available themes in LaxyFile:")

        theme_table = Table(show_header=True, header_style="bold magenta")
        theme_table.add_column("Theme", style="cyan")
        theme_table.add_column("Description", style="white")
        theme_table.add_column("Primary Color", style="green")

        for name, description, color in themes:
            theme_table.add_row(name, description, color)

        self.console.print(theme_table)
        self.console.print()

        # Simulate theme switching
        self.console.print("Theme switching demo:")
        for name, description, color in themes[:3]:
            self.console.print(f"\n[bold]Switching to {name} theme...[/bold]")
            time.sleep(1)

            # Show theme preview (simulated)
            theme_preview = Panel(
                f"LaxyFile with {name} theme\n{description}",
                title=f"🎨 {name.title()} Theme",
                border_style="blue",
                padding=(1, 2)
            )
            self.console.print(theme_preview)
            time.sleep(1)

        self.console.print("\n[bold green]Themes can be customized further in Settings![/bold green]")

    def demo_advanced(self):
        """Advanced features demo"""
        self.console.print("[bold blue]Advanced Features Demo[/bold blue]")
        self.console.print()

        advanced_features = [
            {
                "name": "Dual-Pane Mode",
                "description": "Work with two file panels side by side",
                "demo": "Press F6 to toggle dual-pane mode for easy file comparison and transfer"
            },
            {
                "name": "Archive Operations",
                "description": "Create and extract archives in multiple formats",
                "demo": "Right-click files → 'Create Archive' or extract with Enter key"
            },
            {
                "name": "Plugin System",
                "description": "Extend LaxyFile with custom functionality",
                "demo": "Settings → Plugins to browse and install extensions"
            },
            {
                "name": "Batch Operations",
                "description": "Perform operations on multiple files at once",
                "demo": "Select multiple files (Ctrl+Click) then apply operations to all"
            },
            {
                "name": "File Monitoring",
                "description": "Real-time updates when files change",
                "demo": "File list automatically updates when external changes occur"
            }
        ]

        for feature in advanced_features:
            feature_panel = Panel(
                f"[bold]{feature['description']}[/bold]\n\n💡 {feature['demo']}",
                title=f"🚀 {feature['name']}",
                border_style="green",
                padding=(1, 2)
            )
            self.console.print(feature_panel)
            self.console.print()
            time.sleep(1)

        self.console.print("[bold green]These are just some of LaxyFile's advanced capabilities![/bold green]")

    def demo_completion(self):
        """Tutorial completion demo"""
        self.console.print("[bold green]🎉 Tutorial Complete![/bold green]")
        self.console.print()

        completion_text = Text()
        completion_text.append("Congratulations! You've completed the LaxyFile tutorial.\n\n", style="bold green")
        completion_text.append("You've learned:\n", style="bold")
        completion_text.append("✓ Basic navigation and file operations\n", style="green")
        completion_text.append("✓ Search and filtering techniques\n", style="green")
        completion_text.append("✓ AI assistant capabilities\n", style="green")
        completion_text.append("✓ Theme customization\n", style="green")
        completion_text.append("✓ Advanced features overview\n", style="green")
        completion_text.append("\nNext steps:\n", style="bold")
        completion_text.append("• Explore LaxyFile with your own files\n", style="cyan")
        completion_text.append("• Check out the full documentation\n", style="cyan")
        completion_text.append("• Join the LaxyFile community\n", style="cyan")
        completion_text.append("• Try creating custom themes and plugins\n", style="cyan")

        completion_panel = Panel(
            completion_text,
            title="🏆 Well Done!",
            border_style="green",
            padding=(1, 2)
        )

        self.console.print(completion_panel)

        # Show resources
        self.console.print("\n[bold blue]Helpful Resources:[/bold blue]")
        resources = [
            ("📖 Documentation", "https://docs.laxyfile.com"),
            ("💬 Community Forum", "https://community.laxyfile.com"),
            ("🐛 Report Issues", "https://github.com/your-repo/laxyfile/issues"),
            ("💡 Feature Requests", "https://github.com/your-repo/laxyfile/discussions")
        ]

        for name, url in resources:
            self.console.print(f"  {name}: [link]{url}[/link]")

        input("\nPress Enter to finish the tutorial...")

    # Validation functions

    def validate_navigation(self) -> bool:
        """Validate navigation understanding"""
        self.console.print("\n[bold yellow]Quick Check:[/bold yellow]")

        questions = [
            ("What key combination opens the 'Go to Path' dialog?", "Ctrl+L"),
            ("How do you go to the parent directory?", "Backspace or Ctrl+Up"),
            ("What does Ctrl+H do?", "Go to home directory")
        ]

        correct = 0
        for question, expected in questions:
            answer = Prompt.ask(question)
            if expected.lower() in answer.lower():
                self.console.print("[green]✓ Correct![/green]")
                correct += 1
            else:
                self.console.print(f"[yellow]The answer is: {expected}[/yellow]")

        return correct >= 2

    def validate_file_operations(self) -> bool:
        """Validate file operations understanding"""
        self.console.print("\n[bold yellow]Quick Check:[/bold yellow]")
        return Confirm.ask("Do you understand how to copy, move, and delete files in LaxyFile?")

    def validate_search(self) -> bool:
        """Validate search understanding"""
        self.console.print("\n[bold yellow]Quick Check:[/bold yellow]")
        pattern = Prompt.ask("What search pattern would find all Python files?")
        return "*.py" in pattern.lower()

    def validate_ai_basics(self) -> bool:
        """Validate AI understanding"""
        self.console.print("\n[bold yellow]Quick Check:[/bold yellow]")
        return Confirm.ask("Do you understand how to use the AI assistant for file analysis and organization?")

    def validate_themes(self) -> bool:
        """Validate theme understanding"""
        self.console.print("\n[bold yellow]Quick Check:[/bold yellow]")
        return Confirm.ask("Do you know how to change themes in LaxyFile?")

    def validate_advanced(self) -> bool:
        """Validate advanced features understanding"""
        self.console.print("\n[bold yellow]Quick Check:[/bold yellow]")
        return Confirm.ask("Are you interested in exploring LaxyFile's advanced features further?")

    # Utility functions

    def _show_directory_tree(self, path: Path, max_depth: int = 3, current_depth: int = 0):
        """Show directory tree structure"""
        if current_depth >= max_depth:
            return

        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                prefix = "└── " if is_last else "├── "
                indent = "    " * current_depth

                if item.is_dir():
                    self.console.print(f"{indent}{prefix}📁 {item.name}/")
                    if current_depth < max_depth - 1:
                        next_indent = "    " if is_last else "│   "
                        self._show_directory_tree(item, max_depth, current_depth + 1)
                else:
                    icon = self._get_file_icon(item)
                    self.console.print(f"{indent}{prefix}{icon} {item.name}")
        except PermissionError:
            self.console.print(f"{indent}[Permission Denied]")

    def _show_directory_contents(self, path: Path):
        """Show contents of a directory"""
        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

            if not items:
                self.console.print("  [dim]Empty directory[/dim]")
                return

            for item in items:
                if item.is_dir():
                    self.console.print(f"  📁 {item.name}/")
                else:
                    icon = self._get_file_icon(item)
                    size = item.stat().st_size
                    size_str = self._format_file_size(size)
                    self.console.print(f"  {icon} {item.name} ({size_str})")
        except PermissionError:
            self.console.print("  [red]Permission denied[/red]")

    def _get_file_icon(self, file_path: Path) -> str:
        """Get appropriate icon for file type"""
        extension = file_path.suffix.lower()

        icon_map = {
            '.txt': '📄', '.md': '📝', '.pdf': '📕', '.doc': '📘', '.docx': '📘',
            '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨', '.json': '📋',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.svg': '🖼️',
            '.mp3': '🎵', '.wav': '🎵', '.mp4': '🎬', '.avi': '🎬',
            '.zip': '📦', '.tar': '📦', '.gz': '📦', '.rar': '📦',
            '.exe': '⚙️', '.msi': '⚙️', '.deb': '⚙️', '.rpm': '⚙️'
        }

        return icon_map.get(extension, '📄')

    def _format_file_size(self, size: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    def cleanup_tutorial_environment(self):
        """Clean up tutorial environment"""
        if self.tutorial_dir and self.tutorial_dir.exists():
            if Confirm.ask(f"\nRemove tutorial directory ({self.tutorial_dir})?", default=True):
                shutil.rmtree(self.tutorial_dir)
                self.console.print("[green]✓[/green] Tutorial directory cleaned up")
            else:
                self.console.print(f"[yellow]Tutorial files kept at: {self.tutorial_dir}[/yellow]")


def main():
    """Main entry point for the interactive tutorial"""
    tutorial = InteractiveTutorial()

    try:
        tutorial.run_tutorial()
    except KeyboardInterrupt:
        tutorial.console.print("\n[yellow]Tutorial interrupted by user[/yellow]")
    except Exception as e:
        tutorial.console.print(f"\n[red]Tutorial error: {e}[/red]")
    finally:
        tutorial.cleanup_tutorial_environment()


if __name__ == "__main__":
    main()