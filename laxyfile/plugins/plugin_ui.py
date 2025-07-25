"""
Plugin Management UI

This module provides user interface components for managing plugins
within the LaxyFile application.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.align import Align

from .plugin_integration import PluginIntegration
from .base_plugin import PluginStatus, PluginType
from ..utils.logger import Logger


class PluginUIMode(Enum):
    """Plugin UI display modes"""
    LIST = "list"
    DETAILS = "details"
    INSTALL = "install"
    CONFIGURE = "configure"


@dataclass
class PluginUIState:
    """Plugin UI state"""
    mode: PluginUIMode = PluginUIMode.LIST
    selected_plugin: Optional[str] = None
    filter_type: Optional[PluginType] = None
    filter_status: Optional[PluginStatus] = None
    search_query: str = ""
    show_disabled: bool = True


class PluginManagementUI:
    """Plugin management user interface"""

    def __init__(self, plugin_integration: PluginIntegration):
        self.plugin_integration = plugin_integration
        self.console = Console()
        self.logger = Logger()

        # UI state
        self.state = PluginUIState()
        self.is_running = False

        # Key bindings
        self.key_bindings = {
            'q': self.quit,
            'r': self.refresh,
            'i': self.show_install_mode,
            'l': self.show_list_mode,
            'd': self.show_details_mode,
            'c': self.show_configure_mode,
            'e': self.enable_selected_plugin,
            'x': self.disable_selected_plugin,
            'u': self.uninstall_selected_plugin,
            '/': self.search_plugins,
            'f': self.filter_plugins,
            'h': self.show_help,
            '?': self.show_help
        }

    async def run(self):
        """Run the plugin management interface"""
        try:
            self.is_running = True
            self.console.clear()

            # Show welcome message
            self._show_welcome()

            # Main UI loop
            while self.is_running:
                try:
                    # Render current view
                    await self._render_current_view()

                    # Get user input
                    key = await self._get_user_input()

                    # Handle key press
                    await self._handle_key_press(key)

                except KeyboardInterrupt:
                    if Confirm.ask("Are you sure you want to quit?"):
                        break
                except Exception as e:
                    self.logger.error(f"Error in plugin UI: {e}")
                    self.console.print(f"[red]Error: {e}[/red]")
                    await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"Fatal error in plugin management UI: {e}")
            self.console.print(f"[red]Fatal error: {e}[/red]")

        finally:
            self.is_running = False
            self.console.clear()

    def _show_welcome(self):
        """Show welcome message"""
        welcome_text = Text("LaxyFile Plugin Manager", style="bold blue")
        welcome_panel = Panel(
            Align.center(welcome_text),
            title="Welcome",
            border_style="blue"
        )
        self.console.print(welcome_panel)
        self.console.print()

    async def _render_current_view(self):
        """Render the current view based on UI state"""
        self.console.clear()

        # Show header
        self._render_header()

        # Show main content based on mode
        if self.state.mode == PluginUIMode.LIST:
            await self._render_plugin_list()
        elif self.state.mode == PluginUIMode.DETAILS:
            await self._render_plugin_details()
        elif self.state.mode == PluginUIMode.INSTALL:
            await self._render_install_interface()
        elif self.state.mode == PluginUIMode.CONFIGURE:
            await self._render_configure_interface()

        # Show footer
        self._render_footer()

    def _render_header(self):
        """Render UI header"""
        status = self.plugin_integration.get_plugin_status()

        header_text = f"Plugin Manager - {status['plugin_count']} plugins ({status['enabled_count']} enabled)"
        if self.state.search_query:
            header_text += f" - Search: '{self.state.search_query}'"

        header_panel = Panel(
            header_text,
            title=f"Mode: {self.state.mode.value.title()}",
            border_style="green"
        )
        self.console.print(header_panel)
        self.console.print()

    async def _render_plugin_list(self):
        """Render plugin list view"""
        plugins = await self._get_filtered_plugins()

        if not plugins:
            self.console.print("[yellow]No plugins found matching current filters.[/yellow]")
            return

        # Create table
        table = Table(title="Installed Plugins")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Version", style="magenta")
        table.add_column("Type", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Author", style="blue")
        table.add_column("Description", style="white")

        for plugin_id, plugin_info in plugins.items():
            metadata = plugin_info['metadata']
            status_color = self._get_status_color(plugin_info['status'])

            # Highlight selected plugin
            name_style = "bold cyan" if plugin_id == self.state.selected_plugin else "cyan"

            table.add_row(
                f"[{name_style}]{metadata['name']}[/{name_style}]",
                metadata['version'],
                metadata['plugin_type'],
                f"[{status_color}]{plugin_info['status']}[/{status_color}]",
                metadata['author'],
                metadata['description'][:50] + "..." if len(metadata['description']) > 50 else metadata['description']
            )

        self.console.print(table)

        # Show selection info
        if self.state.selected_plugin:
            self.console.print(f"\\n[bold]Selected:[/bold] {self.state.selected_plugin}")

    async def _render_plugin_details(self):
        """Render plugin details view"""
        if not self.state.selected_plugin:
            self.console.print("[red]No plugin selected[/red]")
            return

        plugin_info = self.plugin_integration.get_plugin_info(self.state.selected_plugin)
        if not plugin_info:
            self.console.print(f"[red]Plugin '{self.state.selected_plugin}' not found[/red]")
            return

        metadata = plugin_info['metadata']

        # Create details layout
        layout = Layout()
        layout.split_column(
            Layout(name="info", size=10),
            Layout(name="config", size=8),
            Layout(name="actions")
        )

        # Plugin info
        info_table = Table(title=f"Plugin Details: {metadata['name']}")
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="white")

        info_table.add_row("Name", metadata['name'])
        info_table.add_row("Version", metadata['version'])
        info_table.add_row("Author", metadata['author'])
        info_table.add_row("Type", metadata['plugin_type'])
        info_table.add_row("Status", plugin_info['status'])
        info_table.add_row("Description", metadata['description'])
        info_table.add_row("Homepage", metadata.get('homepage', 'N/A'))
        info_table.add_row("License", metadata.get('license', 'N/A'))
        info_table.add_row("Tags", ', '.join(metadata.get('tags', [])))
        info_table.add_row("Capabilities", ', '.join(metadata.get('capabilities', [])))
        info_table.add_row("Dependencies", ', '.join(metadata.get('dependencies', [])))

        if plugin_info.get('load_time'):
            info_table.add_row("Load Time", plugin_info['load_time'])
        if plugin_info.get('error_message'):
            info_table.add_row("Last Error", f"[red]{plugin_info['error_message']}[/red]")

        layout["info"].update(Panel(info_table))

        # Configuration
        config_info = plugin_info.get('config', {})
        config_table = Table(title="Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="white")

        config_table.add_row("Enabled", str(config_info.get('enabled', False)))
        config_table.add_row("Priority", str(config_info.get('priority', 50)))

        settings = config_info.get('settings', {})
        for key, value in settings.items():
            config_table.add_row(f"  {key}", str(value))

        layout["config"].update(Panel(config_table))

        # Available actions
        actions = []
        if plugin_info['status'] == 'loaded':
            actions.append("[e] Enable plugin")
        elif plugin_info['status'] == 'enabled':
            actions.append("[x] Disable plugin")

        actions.extend([
            "[c] Configure plugin",
            "[u] Uninstall plugin",
            "[r] Reload plugin"
        ])

        actions_text = "\\n".join(actions)
        layout["actions"].update(Panel(actions_text, title="Available Actions"))

        self.console.print(layout)

    async def _render_install_interface(self):
        """Render plugin installation interface"""
        install_panel = Panel(
            "Plugin Installation\\n\\n"
            "Enter plugin source:\\n"
            "• Local file path: /path/to/plugin.py\\n"
            "• Local directory: /path/to/plugin/\\n"
            "• Remote URL: https://example.com/plugin.zip\\n"
            "• Git repository: https://github.com/user/plugin.git\\n"
            "• Plugin registry: plugin-name\\n\\n"
            "Press Enter to continue or 'q' to cancel",
            title="Install Plugin",
            border_style="blue"
        )
        self.console.print(install_panel)

    async def _render_configure_interface(self):
        """Render plugin configuration interface"""
        if not self.state.selected_plugin:
            self.console.print("[red]No plugin selected for configuration[/red]")
            return

        plugin_info = self.plugin_integration.get_plugin_info(self.state.selected_plugin)
        if not plugin_info:
            self.console.print(f"[red]Plugin '{self.state.selected_plugin}' not found[/red]")
            return

        config_panel = Panel(
            f"Configuration for: {plugin_info['metadata']['name']}\\n\\n"
            "Available configuration options:\\n"
            "• Enable/Disable plugin\\n"
            "• Set plugin priority\\n"
            "• Modify plugin settings\\n\\n"
            "Use arrow keys to navigate, Enter to edit, 'q' to cancel",
            title="Configure Plugin",
            border_style="yellow"
        )
        self.console.print(config_panel)

    def _render_footer(self):
        """Render UI footer with key bindings"""
        footer_text = (
            "[q] Quit  [r] Refresh  [i] Install  [l] List  [d] Details  [c] Configure  "
            "[e] Enable  [x] Disable  [u] Uninstall  [/] Search  [f] Filter  [h] Help"
        )

        footer_panel = Panel(
            footer_text,
            title="Key Bindings",
            border_style="dim"
        )
        self.console.print()
        self.console.print(footer_panel)

    async def _get_filtered_plugins(self) -> Dict[str, Any]:
        """Get plugins filtered by current criteria"""
        all_plugins = self.plugin_integration.get_plugin_status()['plugins']
        filtered_plugins = {}

        for plugin_id, plugin_info in all_plugins.items():
            # Apply status filter
            if self.state.filter_status and plugin_info['status'] != self.state.filter_status.value:
                continue

            # Apply type filter
            if self.state.filter_type and plugin_info['metadata']['plugin_type'] != self.state.filter_type.value:
                continue

            # Apply search filter
            if self.state.search_query:
                search_text = f"{plugin_info['metadata']['name']} {plugin_info['metadata']['description']}".lower()
                if self.state.search_query.lower() not in search_text:
                    continue

            # Apply disabled filter
            if not self.state.sled and plugin_info['status'] in ['disabled', 'error']:
                continue

            filtered_plugins[plugin_id] = plugin_info

        return filtered_plugins

    def _get_status_color(self, status: str) -> str:
        """Get color for plugin status"""
        color_map = {
            'enabled': 'green',
            'loaded': 'yellow',
            'disabled': 'red',
            'error': 'bright_red',
            'loading': 'blue',
            'unloading': 'blue'
        }
        return color_map.get(status, 'white')

    async def _get_user_input(self) -> str:
        """Get user input (simplified for demo)"""
        # In a real implementation, this would use proper async input handling
        return input("Press key: ").lower()

    async def _handle_key_press(self, key: str):
        """Handle key press"""
        if key in self.key_bindings:
            await self.key_bindings[key]()
        elif key.isdigit():
            await self._select_plugin_by_number(int(key))
        else:
            self.console.print(f"[yellow]Unknown key: {key}[/yellow]")

    # Key binding handlers
    async def quit(self):
        """Quit the plugin manager"""
        self.is_running = False

    async def refresh(self):
        """Refresh plugin list"""
        self.console.print("[blue]Refreshing plugin list...[/blue]")
        # Force refresh of plugin status
        await asyncio.sleep(0.5)  # Simulate refresh delay

    async def show_install_mode(self):
        """Show install mode"""
        self.state.mode = PluginUIMode.INSTALL

    async def show_list_mode(self):
        """Show list mode"""
        self.state.mode = PluginUIMode.LIST

    async def show_details_mode(self):
        """Show details mode"""
        if self.state.selected_plugin:
            self.state.mode = PluginUIMode.DETAILS
        else:
            self.console.print("[yellow]No plugin selected[/yellow]")

    async def show_configure_mode(self):
        """Show configure mode"""
        if self.state.selected_plugin:
            self.state.mode = PluginUIMode.CONFIGURE
        else:
            self.console.print("[yellow]No plugin selected[/yellow]")

    async def enable_selected_plugin(self):
        """Enable selected plugin"""
        if not self.state.selected_plugin:
            self.console.print("[yellow]No plugin selected[/yellow]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"Enabling {self.state.selected_plugin}...", total=None)

            result = await self.plugin_integration.enable_plugin(self.state.selected_plugin)

            if result['success']:
                self.console.print(f"[green]Plugin '{self.state.selected_plugin}' enabled successfully[/green]")
            else:
                self.console.print(f"[red]Failed to enable plugin: {result['message']}[/red]")

    async def disable_selected_plugin(self):
        """Disable selected plugin"""
        if not self.state.selected_plugin:
            self.console.print("[yellow]No plugin selected[/yellow]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"Disabling {self.state.selected_plugin}...", total=None)

            result = await self.plugin_integration.disable_plugin(self.state.selected_plugin)

            if result['success']:
                self.console.print(f"[green]Plugin '{self.state.selected_plugin}' disabled successfully[/green]")
            else:
                self.console.print(f"[red]Failed to disable plugin: {result['message']}[/red]")

    async def uninstall_selected_plugin(self):
        """Uninstall selected plugin"""
        if not self.state.selected_plugin:
            self.console.print("[yellow]No plugin selected[/yellow]")
            return

        if not Confirm.ask(f"Are you sure you want to uninstall '{self.state.selected_plugin}'?"):
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"Uninstalling {self.state.selected_plugin}...", total=None)

            result = await self.plugin_integration.uninstall_plugin(self.state.selected_plugin)

            if result['success']:
                self.console.print(f"[green]Plugin '{self.state.selected_plugin}' uninstalled successfully[/green]")
                self.state.selected_plugin = None
            else:
                self.console.print(f"[red]Failed to uninstall plugin: {result['message']}[/red]")

    async def search_plugins(self):
        """Search plugins"""
        query = Prompt.ask("Enter search query")
        self.state.search_query = query
        self.console.print(f"[blue]Searching for: {query}[/blue]")

    async def filter_plugins(self):
        """Filter plugins"""
        filter_options = [
            "1. Filter by type",
            "2. Filter by status",
            "3. Toggle show disabled",
            "4. Clear all filters"
        ]

        self.console.print("\\n".join(filter_options))
        choice = Prompt.ask("Select filter option", choices=["1", "2", "3", "4"])

        if choice == "1":
            type_options = [t.value for t in PluginType]
            selected_type = Prompt.ask("Select plugin type", choices=type_options + ["none"])
            self.state.filter_type = PluginType(selected_type) if selected_type != "none" else None

        elif choice == "2":
            status_options = [s.value for s in PluginStatus]
            selected_status = Prompt.ask("Select plugin status", choices=status_options + ["none"])
            self.state.filter_status = PluginStatus(selected_status) if selected_status != "none" else None

        elif choice == "3":
            self.state.show_disabled = not self.state.show_disabled
            self.console.print(f"[blue]Show disabled plugins: {self.state.show_disabled}[/blue]")

        elif choice == "4":
            self.state.filter_type = None
            self.state.filter_status = None
            self.state.search_query = ""
            self.state.show_disabled = True
            self.console.print("[blue]All filters cleared[/blue]")

    async def show_help(self):
        """Show help information"""
        help_text = \"\"\"
LaxyFile Plugin Manager Help

Key Bindings:
  q - Quit plugin manager
  r - Refresh plugin list
  i - Install new plugin
  l - Show plugin list
  d - Show plugin details
  c - Configure selected plugin
  e - Enable selected plugin
  x - Disable selected plugin
  u - Uninstall selected plugin
  / - Search plugins
  f - Filter plugins
  h, ? - Show this help

Navigation:
  Use number keys to select plugins
  Use arrow keys in configuration mode

Plugin Sources:
  • Local file: /path/to/plugin.py
  • Local directory: /path/to/plugin/
  • Remote URL: https://example.com/plugin.zip
  • Git repository: https://github.com/user/plugin.git
  • Plugin registry: plugin-name
        \"\"\"

        help_panel = Panel(
            help_text,
            title="Help",
            border_style="blue"
        )
        self.console.print(help_panel)
        input("Press Enter to continue...")

    async def _select_plugin_by_number(self, number: int):
        """Select plugin by number"""
        plugins = await self._get_filtered_plugins()
        plugin_list = list(plugins.keys())

        if 1 <= number <= len(plugin_list):
            self.state.selected_plugin = plugin_list[number - 1]
            self.console.print(f"[blue]Selected plugin: {self.state.selected_plugin}[/blue]")
        else:
            self.console.print(f"[red]Invalid plugin number: {number}[/red]")


# CLI command for plugin management
async def run_plugin_manager_cli(plugin_integration: PluginIntegration):
    """Run the plugin manager CLI"""
    ui = PluginManagementUI(plugin_integration)
    await ui.run()


# Integration with main LaxyFile application
def create_plugin_management_commands(plugin_integration: PluginIntegration) -> Dict[str, Callable]:
    """Create plugin management commands for LaxyFile"""

    async def list_plugins_command():
        """List all plugins"""
        status = plugin_integration.get_plugin_status()
        plugins = status['plugins']

        console = Console()
        table = Table(title="Installed Plugins")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="magenta")
        table.add_column("Status", style="yellow")
        table.add_column("Type", style="green")

        for plugin_id, plugin_info in plugins.items():
            metadata = plugin_info['metadata']
            table.add_row(
                metadata['name'],
                metadata['version'],
                plugin_info['status'],
                metadata['plugin_type']
            )

        console.print(table)

    async def install_plugin_command(source: str):
        """Install plugin from source"""
        console = Console()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Installing plugin from {source}...", total=None)

            result = await plugin_integration.install_plugin(source)

            if result['success']:
                console.print(f"[green]Plugin installed successfully: {result['plugin_id']}[/green]")
            else:
                console.print(f"[red]Installation failed: {result['message']}[/red]")

    async def enable_plugin_command(plugin_id: str):
        """Enable plugin"""
        console = Console()
        result = await plugin_integration.enable_plugin(plugin_id)

        if result['success']:
            console.print(f"[green]Plugin '{plugin_id}' enabled[/green]")
        else:
            console.print(f"[red]Failed to enable plugin: {result['message']}[/red]")

    async def disable_plugin_command(plugin_id: str):
        """Disable plugin"""
        console = Console()
        result = await plugin_integration.disable_plugin(plugin_id)

        if result['success']:
            console.print(f"[green]Plugin '{plugin_id}' disabled[/green]")
        else:
            console.print(f"[red]Failed to disable plugin: {result['message']}[/red]")

    return {
        'plugin_list': list_plugins_command,
        'plugin_install': install_plugin_command,
        'plugin_enable': enable_plugin_command,
        'plugin_disable': disable_plugin_command,
        'plugin_manager': lambda: run_plugin_manager_cli(plugin_integration)
    }