"""
Troubleshooting Wizard and Diagnostic Tools

This module provides interactive troubleshooting assistance and
diagnostic tools to help users resolve common issues with LaxyFile.
"""

import sys
import os
import platform
import subprocess
import psutil
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.tree import Tree

from ..core.config import Config
from ..utils.logger import Logger


class IssueCategory(Enum):
    """Categories of issues that can be diagnosed"""
    STARTUP = "startup"
    PERFORMANCE = "performance"
    AI_ASSISTANT = "ai_assistant"
    FILE_OPERATIONS = "file_operations"
    UI_DISPLAY = "ui_display"
    CONFIGURATION = "configuration"
    PLUGINS = "plugins"
    GENERAL = "general"


@dataclass
class DiagnosticTest:
    """Individual diagnostic test"""
    id: str
    name: str
    description: str
    category: IssueCategory
    test_function: Callable[[], Tuple[bool, str, Optional[str]]]
    fix_function: Optional[Callable[[], bool]] = None
    severity: str = "info"  # info, warning, error, critical


class TroubleshootingWizard:
    """Interactive troubleshooting wizard for LaxyFile"""

    def __init__(self, config: Config, console: Console):
        self.config = config
        self.console = console
        self.logger = Logger()

        # Diagnostic tests
        self.diagnostic_tests = {}
        self.test_results = {}

        # System information
        self.system_info = {}

        # Initialize diagnostic tests
        self._initialize_diagnostic_tests()

    def start_troubleshooting(self) -> None:
        """Start the interactive troubleshooting wizard"""
        self.console.print("[bold blue]LaxyFile Troubleshooting Wizard[/bold blue]\n")

        # Show welcome message
        welcome_text = """
This wizard will help you diagnose and resolve common issues with LaxyFile.
We'll run some diagnostic tests and provide solutions for any problems found.
"""

        welcome_panel = Panel(
      welcome_text.strip(),
            title="🔧 Troubleshooting Wizard",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(welcome_panel)
        self.console.print()

        # Ask what kind of issue they're experiencing
        issue_type = self._ask_issue_type()

        if issue_type:
            self._run_targeted_diagnostics(issue_type)
        else:
            self._run_full_diagnostics()

    def _ask_issue_type(self) -> Optional[IssueCategory]:
        """Ask user what type of issue they're experiencing"""
        self.console.print("[bold]What type of issue are you experiencing?[/bold]\n")

        issue_options = [
            ("1", "LaxyFile won't start or crashes", IssueCategory.STARTUP),
            ("2", "Slow performance or freezing", IssueCategory.PERFORMANCE),
            ("3", "AI assistant not working", IssueCategory.AI_ASSISTANT),
            ("4", "File operations failing", IssueCategory.FILE_OPERATIONS),
            ("5", "Display or UI problems", IssueCategory.UI_DISPLAY),
            ("6", "Configuration issues", IssueCategory.CONFIGURATION),
            ("7", "Plugin problems", IssueCategory.PLUGINS),
            ("8", "Other or not sure", IssueCategory.GENERAL),
            ("9", "Run full diagnostic", None)
        ]

        for option, description, _ in issue_options:
            self.console.print(f"  {option}. {description}")

        self.console.print()
        choice = Prompt.ask("Select an option", choices=[opt[0] for opt in issue_options])

        for option, _, category in issue_options:
            if option == choice:
                return category

        return None

    def _run_targeted_diagnostics(self, category: IssueCategory) -> None:
        """Run diagnostics for specific issue category"""
        self.console.print(f"\n[bold]Running diagnostics for {category.value.replace('_', ' ').title()} issues...[/bold]\n")

        # Get tests for this category
        category_tests = [test for test in self.diagnostic_tests.values()
                         if test.category == category]

        if not category_tests:
            self.console.print("[yellow]No specific tests available for this category. Running general diagnostics...[/yellow]")
            self._run_full_diagnostics()
            return

        # Run category-specific tests
        self._run_diagnostic_tests(category_tests)

        # Show results and solutions
        self._show_diagnostic_results()

    def _run_full_diagnostics(self) -> None:
        """Run complete diagnostic suite"""
        self.console.print("\n[bold]Running full diagnostic suite...[/bold]\n")

        all_tests = list(self.diagnostic_tests.values())
        self._run_diagnostic_tests(all_tests)
        self._show_diagnostic_results()

    def _run_diagnostic_tests(self, tests: List[DiagnosticTest]) -> None:
        """Run a list of diagnostic tests"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:

            for test in tests:
                task = progress.add_task(f"Running {test.name}...", total=None)

                try:
                    success, message, fix_suggestion = test.test_function()

                    self.test_results[test.id] = {
                        'test': test,
                        'success': success,
                        'message': message,
                        'fix_suggestion': fix_suggestion,
                        'severity': test.severity
                    }

                except Exception as e:
                    self.test_results[test.id] = {
                        'test': test,
                        'success': False,
                        'message': f"Test failed with error: {e}",
                        'fix_suggestion': "Please report this issue to the developers",
                        'severity': 'error'
                    }

                progress.remove_task(task)

    def _show_diagnostic_results(self) -> None:
        """Show diagnostic test results and offer solutions"""
        self.console.print("\n[bold blue]Diagnostic Results[/bold blue]\n")

        # Categorize results
        passed_tests = []
        failed_tests = []
        warnings = []

        for result in self.test_results.values():
            if result['success']:
                if result['severity'] == 'warning':
                    warnings.append(result)
                else:
                    passed_tests.append(result)
            else:
                failed_tests.append(result)

        # Show summary
        summary_text = f"""
Tests Run: {len(self.test_results)}
Passed: {len(passed_tests)}
Warnings: {len(warnings)}
Failed: {len(failed_tests)}
"""

        summary_panel = Panel(
            summary_text.strip(),
            title="📊 Test Summary",
            border_style="blue"
        )

        self.console.print(summary_panel)
        self.console.print()

        # Show failed tests first
        if failed_tests:
            self.console.print("[bold red]❌ Issues Found[/bold red]\n")

            for result in failed_tests:
                self._show_test_result(result, "red")

                # Offer to apply fix if available
                if result['test'].fix_function and result['fix_suggestion']:
                    if Confirm.ask(f"Would you like to try the suggested fix for '{result['test'].name}'?"):
                        self._apply_fix(result['test'])

        # Show warnings
        if warnings:
            self.console.print("\n[bold yellow]⚠️ Warnings[/bold yellow]\n")

            for result in warnings:
                self._show_test_result(result, "yellow")

        # Show passed tests (brief)
        if passed_tests:
            self.console.print(f"\n[bold green]✅ {len(passed_tests)} tests passed[/bold green]")

        # Offer additional help
        self._offer_additional_help()

    def _show_test_result(self, result: Dict[str, Any], color: str) -> None:
        """Show individual test result"""
        test = result['test']

        result_panel = Panel(
            f"**Issue**: {result['message']}\n\n**Suggestion**: {result['fix_suggestion'] or 'No automatic fix available'}",
            title=f"{test.name}",
            border_style=color,
            padding=(0, 1)
        )

        self.console.print(result_panel)
        self.console.print()

    def _apply_fix(self, test: DiagnosticTest) -> None:
        """Apply automatic fix for a test"""
        self.console.print(f"[bold]Applying fix for {test.name}...[/bold]")

        try:
            success = test.fix_function()

            if success:
                self.console.print(f"[green]✅ Fix applied successfully for {test.name}[/green]")
            else:
                self.console.print(f"[red]❌ Fix failed for {test.name}[/red]")

        except Exception as e:
            self.console.print(f"[red]❌ Error applying fix: {e}[/red]")

    def _offer_additional_help(self) -> None:
        """Offer additional help options"""
        self.console.print("\n[bold]Additional Help Options[/bold]\n")

        help_options = [
            "1. View system information",
            "2. Generate diagnostic report",
            "3. Reset configuration to defaults",
            "4. Contact support",
            "5. Exit troubleshooting"
        ]

        for option in help_options:
            self.console.print(f"  {option}")

        self.console.print()
        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5"], default="5")

        if choice == "1":
            self._show_system_information()
        elif choice == "2":
            self._generate_diagnostic_report()
        elif choice == "3":
            self._reset_configuration()
        elif choice == "4":
            self._show_support_information()

    def _show_system_information(self) -> None:
        """Show detailed system information"""
        self.console.print("\n[bold blue]System Information[/bold blue]\n")

        # Collect system info
        system_info = self._collect_system_information()

        # Create system info table
        info_table = Table(title="System Details")
        info_table.add_column("Component", style="cyan")
        info_table.add_column("Value", style="white")

        for key, value in system_info.items():
            info_table.add_row(key, str(value))

        self.console.print(info_table)

    def _collect_system_information(self) -> Dict[str, Any]:
        """Collect comprehensive system information"""
        info = {}

        try:
            # Basic system info
            info["Operating System"] = platform.system()
            info["OS Version"] = platform.version()
            info["Architecture"] = platform.machine()
            info["Python Version"] = sys.version.split()[0]
            info["LaxyFile Version"] = self.config.get('app.version', 'Unknown')

            # Hardware info
            info["CPU Cores"] = psutil.cpu_count()
            info["Total Memory"] = f"{psutil.virtual_memory().total // (1024**3)} GB"
            info["Available Memory"] = f"{psutil.virtual_memory().available // (1024**3)} GB"

            # Terminal info
            info["Terminal"] = os.environ.get('TERM', 'Unknown')
            info["Terminal Size"] = f"{os.get_terminal_size().columns}x{os.get_terminal_size().lines}"

            # LaxyFile specific
            info["Config Directory"] = str(self.config.config_dir)
            info["AI Enabled"] = self.config.get('ai.enabled', False)
            info["Theme"] = self.config.get('ui.theme', 'default')

        except Exception as e:
            info["Error"] = f"Could not collect system info: {e}"

        return info

   def _initialize_diagnostic_tests(self):
        """Initialize all diagnostic tests"""
        # Startup tests
        self.diagnostic_tests["python_version"] = DiagnosticTest(
            id="python_version",
            name="Python Version Check",
            description="Verify Python version compatibility",
            category=IssueCategory.STARTUP,
            test_function=self._test_python_version,
            severity="critical"
        )

        self.diagnostic_tests["dependencies"] = DiagnosticTest(
            id="dependencies",
            name="Dependencies Check",
            description="Verify required packages are installed",
            category=IssueCategory.STARTUP,
            test_function=self._test_dependencies,
            fix_function=self._fix_dependencies,
            severity="error"
        )

        self.diagnostic_tests["config_validity"] = DiagnosticTest(
            id="config_validity",
            name="Configuration Validity",
            description="Check configuration file integrity",
            category=IssueCategory.CONFIGURATION,
            test_function=self._test_config_validity,
            fix_function=self._fix_config_validity,
            severity="error"
        )

        # Performance tests
        self.diagnostic_tests["memory_usage"] = DiagnosticTest(
            id="memory_usage",
            name="Memory Usage Check",
            description="Check system memory availability",
            category=IssueCategory.PERFORMANCE,
            test_function=self._test_memory_usage,
            severity="warning"
        )

        self.diagnostic_tests["disk_space"] = DiagnosticTest(
            id="disk_space",
            name="Disk Space Check",
            description="Verify sufficient disk space",
            category=IssueCategory.PERFORMANCE,
            test_function=self._test_disk_space,
            severity="warning"
        )

        # AI tests
        self.diagnostic_tests["ai_configuration"] = DiagnosticTest(
            id="ai_configuration",
            name="AI Configuration",
            description="Check AI assistant configuration",
            category=IssueCategory.AI_ASSISTANT,
            test_function=self._test_ai_configuration,
            fix_function=self._fix_ai_configuration,
            severity="info"
        )

        # UI tests
        self.diagnostic_tests["terminal_support"] = DiagnosticTest(
            id="terminal_support",
            name="Terminal Support",
            descrip="Check terminal capabilities",
            category=IssueCategory.UI_DISPLAY,
            test_function=self._test_terminal_support,
            severity="warning"
        )

    # Diagnostic test functions

    def _test_python_version(self) -> Tuple[bool, str, Optional[str]]:
        """Test Python version compatibility"""
        current_version = sys.version_info
        min_version = (3, 8)
        recommended_version = (3, 11)

        if current_version < min_version:
            return (
                False,
                f"Python {current_version.major}.{current_version.minor} is not supported",
                f"Please upgrade to Python {min_version[0]}.{min_version[1]} or later"
            )
        elif current_version < recommended_version:
            return (
                True,
                f"Python {current_version.major}.{current_version.minor} works but newer version recommended",
                f"Consider upgrading to Python {recommended_version[0]}.{recommended_version[1]}+ for better performance"
            )
        else:
            return (
                True,
                f"Python {current_version.major}.{current_version.minor} is fully supported",
                None
            )

    def _test_dependencies(self) -> Tuple[bool, str, Optional[str]]:
        """Test required dependencies"""
        required_packages = [
            "rich",
            "asyncio",
            "pathlib",
            "psutil"
        ]

        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            return (
                False,
                f"Missing required packages: {', '.join(missing_packages)}",
                f"Install missing packages with: pip install {' '.join(missing_packages)}"
            )
        else:
            return (
                True,
                "All required dependencies are installed",
                None
            )

    def _test_config_validity(self) -> Tuple[bool, str, Optional[str]]:
        """Test configuration file validity"""
        try:
            # Try to access config
            config_dir = self.config.config_dir

            if not config_dir.exists():
                return (
                    False,
                    "Configuration directory does not exist",
                    "Configuration directory will be created automatically"
                )

            # Check if config is readable
            test_value = self.config.get('app.version', 'test')

            return (
                True,
                "Configuration is valid and accessible",
                None
            )

        except Exception as e:
            return (
                False,
                f"Configuration error: {e}",
                "Reset configuration to defaults or check file permissions"
            )

    def _test_memory_usage(self) -> Tuple[bool, str, Optional[str]]:
        """Test system memory usage"""
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)

        if available_gb < 1:
            return (
                False,
                f"Low memory: only {available_gb:.1f}GB available",
                "Close other applications or add more RAM"
            )
        elif available_gb < 2:
            return (
                True,
                f"Limited memory: {available_gb:.1f}GB available",
                "Consider closing other applications for better performance"
            )
        else:
            return (
                True,
                f"Sufficient memory: {available_gb:.1f}GB available",
                None
            )

    def _test_disk_space(self) -> Tuple[bool, str, Optional[str]]:
        """Test available disk space"""
        try:
            disk_usage = psutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)

            if free_gb < 1:
                return (
                    False,
                    f"Very low disk space: {free_gb:.1f}GB free",
                    "Free up disk space immediately"
                )
            elif free_gb < 5:
                return (
                    True,
                    f"Low disk space: {free_gb:.1f}GB free",
                    "Consider cleaning up files to free space"
                )
            else:
                return (
                    True,
                    f"Sufficient disk space: {free_gb:.1f}GB free",
                    None
                )

        except Exception as e:
            return (
                False,
                f"Could not check disk space: {e}",
                "Check disk permissions and availability"
            )

    def _test_ai_configuration(self) -> Tuple[bool, str, Optional[str]]:
        """Test AI assistant configuration"""
        ai_enabled = self.config.get('ai.enabled', False)

        if not ai_enabled:
            return (
                True,
                "AI assistant is disabled",
                "Enable AI in Settings → AI Assistant if you want to use AI features"
            )

        ai_provider = self.config.get('ai.provider', '')
        api_key = self.config.get('ai.api_key', '')

        if not ai_provider:
            return (
                False,
                "AI provider not configured",
                "Configure AI provider in Settings → AI Assistant"
            )

        if ai_provider == 'openrouter' and not api_key:
            return (
                False,
                "OpenRouter API key not configured",
                "Add your OpenRouter API key in Settings → AI Assistant"
            )

        return (
            True,
            f"AI assistant configured with {ai_provider}",
            None
        )

    def _test_terminal_support(self) -> Tuple[bool, str, Optional[str]]:
        """Test terminal capabilities"""
        terminal = os.environ.get('TERM', 'unknown')

        # Check terminal size
        try:
            size = os.get_terminal_size()
            if size.columns < 80 or size.lines < 24:
                return (
                    True,
                    f"Small terminal size: {size.columns}x{size.lines}",
                    "Increase terminal size for better experience (recommended: 120x40)"
                )
        except Exception:
            pass

        # Check color support
        if 'color' not in terminal.lower() and terminal != 'xterm-256color':
            return (
                True,
                f"Limited color support in terminal: {terminal}",
                "Use a terminal with better color support for optimal experience"
            )

        return (
            True,
            f"Terminal {terminal} has good LaxyFile support",
            None
        )

    # Fix functions

    def _fix_dependencies(self) -> bool:
        """Attempt to fix missing dependencies"""
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "rich", "psutil"],
                         check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def _fix_config_validity(self) -> bool:
        """Attempt to fix configuration issues"""
        try:
            # Create config directory if it doesn't exist
            self.config.config_dir.mkdir(parents=True, exist_ok=True)

            # Reset to default configuration
            self.config.reset_to_defaults()
            self.config.save()

            return True
        except Exception:
            return False

    def _fix_ai_configuration(self) -> bool:
        """Attempt to fix AI configuration"""
        try:
            # Enable AI and set default provider
            self.config.set('ai.enabled', True)
            self.config.set('ai.provider', 'ollama')  # Default to local provider
            self.config.save()

            return True
        except Exception:
            return False

    def _generate_diagnostic_report(self) -> None:
        """Generate comprehensive diagnostic report"""
        self.console.print("\n[bold]Generating diagnostic report...[/bold]\n")

        report_path = Path.home() / "laxyfile_diagnostic_report.txt"

        try:
            with open(report_path, 'w') as f:
                f.write("LaxyFile Diagnostic Report\n")
                f.write("=" * 50 + "\n\n")

                # System information
                f.write("System Information:\n")
                f.write("-" * 20 + "\n")
                system_info = self._collect_system_information()
                for key, value in system_info.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")

                # Test results
                f.write("Diagnostic Test Results:\n")
                f.write("-" * 25 + "\n")
                for test_id, result in self.test_results.items():
                    test = result['test']
                    status = "PASS" if result['success'] else "FAIL"
                    f.write(f"{test.name}: {status}\n")
                    f.write(f"  Message: {result['message']}\n")
                    if result['fix_suggestion']:
                        f.write(f"  Suggestion: {result['fix_suggestion']}\n")
                    f.write("\n")

            self.console.print(f"[green]✅ Diagnostic report saved to: {report_path}[/green]")

        except Exception as e:
            self.console.print(f"[red]❌ Failed to generate report: {e}[/red]")

    def _reset_configuration(self) -> None:
        """Reset configuration to defaults"""
        if Confirm.ask("This will reset all LaxyFile settings to defaults. Continue?"):
            try:
                self.config.reset_to_defaults()
                self.config.save()
                self.console.print("[green]✅ Configuration reset to defaults[/green]")
            except Exception as e:
                self.console.print(f"[red]❌ Failed to reset configuration: {e}[/red]")

    def _show_support_information(self) -> None:
        """Show support contact information"""
        support_info = """
# Getting Support

If you're still experiencing issues, here are ways to get help:

## Community Support
- **GitHub Issues**: https://github.com/your-repo/laxyfile/issues
- **Discord**: https://discord.gg/laxyfile
- **Discussions**: https://github.com/your-repo/laxyfile/discussions

## Before Contacting Support
Please include:
1. Your diagnostic report (generated above)
2. Steps to reproduce the issue
3. Expected vs actual behavior
4. Screenshots if applicable

## Documentation
- **User Manual**: docs/user-manual.md
- **FAQ**: docs/faq.md
- **Troubleshooting**: docs/troubleshooting.md
"""

        support_panel = Panel(
            support_info.strip(),
            title="📞 Support Information",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(support_panel)