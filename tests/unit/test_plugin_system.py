"""
Unit tests for Plugin System

Tests the plugin architecture including plugin loading, management,
API interfaces, and integration with the main application.
"""

import pytest
import tempfile
import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from laxyfile.plugins.plugin_manager import PluginManager
from laxyfile.plugins.plugin_api import PluginAPI
from laxyfile.plugins.base_plugin import BasePlugin
from laxyfile.plugins.plugin_integration import PluginIntegration
from laxyfile.core.exceptions import PluginError


@pytest.mark.unit
class TestBasePlugin:
    """Test the BasePlugin abstract class"""

    def test_base_plugin_creation(self):
        """Test base plugin creation with required methods"""

        class TestPlugin(BasePlugin):
            def get_name(self) -> str:
                return "test_plugin"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Test plugin"

            def initialize(self, api: PluginAPI) -> None:
                self.api = api

            def cleanup(self) -> None:
                pass

        plugin = TestPlugin()
        assert plugin.get_name() == "test_plugin"
        assert plugin.get_version() == "1.0.0"
        assert plugin.get_description() == "Test plugin"
        assert not plugin.is_enabled()

    def test_base_plugin_enable_disable(self):
        """Test plugin enable/disable functionality"""

        class TestPlugin(BasePlugin):
            def get_name(self) -> str:
                return "test_plugin"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Test plugin"

            def initialize(self, api: PluginAPI) -> None:
                pass

            def cleanup(self) -> None:
                pass

        plugin = TestPlugin()

        # Initially disabled
        assert not plugin.is_enabled()

        # Enable
        plugin.enable()
        assert plugin.is_enabled()

        # Disable
        plugin.disable()
        assert not plugin.is_enabled()

    def test_base_plugin_abstract_methods(self):
        """Test that BasePlugin enforces abstract methods"""

        # Should not be able to instantiate without implementing abstract methods
        with pytest.raises(TypeError):
            BasePlugin()


@pytest.mark.unit
class TestPluginAPI:
    """Test the PluginAPI class"""

    def test_plugin_api_initialization(self, mock_config):
        """Test plugin API initialization"""
        api = PluginAPI(mock_config)

        assert api.config == mock_config
        assert api.file_manager is None  # Not set initially
        assert api.ui_manager is None
        assert api.ai_assistant is None

    def test_plugin_api_capabilities(self, mock_config):
        """Test plugin API capabilities"""
        api = PluginAPI(mock_config)

        capabilities = api.get_capabilities()

        expected_capabilities = [
            'file_operations',
            'ui_components',
            'ai_integration',
            'event_handling',
            'configuration',
            'theming',
            'keyboard_shortcuts',
            'context_menu'
        ]

        for capability in expected_capabilities:
            assert capability in capabilities

    def test_plugin_api_register_command(self, mock_config):
        """Test command registration"""
        api = PluginAPI(mock_config)

        def test_command():
            return "test result"

        api.register_command("test_cmd", test_command, "Test command")
ert "test_cmd" in api.commands
        assert api.commands["test_cmd"]["function"] == test_command
        assert api.commands["test_cmd"]["description"] == "Test command"

    def test_plugin_api_register_duplicate_command(self, mock_config):
        """Test duplicate command registration"""
        api = PluginAPI(mock_config)

        def test_command1():
            return "test1"

        def test_command2():
            return "test2"

        api.register_command("test_cmd", test_command1, "Test command 1")

        # Should raise error for duplicate command
        with pytest.raises(PluginError):
            api.register_command("test_cmd", test_command2, "Test command 2")

    def test_plugin_api_register_event_handler(self, mock_config):
        """Test event handler registration"""
        api = PluginAPI(mock_config)

        def test_handler(event_data):
            return f"handled: {event_data}"

        api.register_event_handler("file_selected", test_handler)

        assert "file_selected" in api.event_handlers
        assert test_handler in api.event_handlers["file_selected"]

    def test_plugin_api_emit_event(self, mock_config):
        """Test event emission"""
        api = PluginAPI(mock_config)

        results = []

        def handler1(data):
            results.append(f"handler1: {data}")

        def handler2(data):
            results.append(f"handler2: {data}")

        api.register_event_handler("test_event", handler1)
        api.register_event_handler("test_event", handler2)

        api.emit_event("test_event", "test_data")

        assert len(results) == 2
        assert "handler1: test_data" in results
        assert "handler2: test_data" in results

    def test_plugin_api_register_ui_component(self, mock_config):
        """Test UI component registration"""
        api = PluginAPI(mock_config)

        def test_component():
            return "UI Component"

        api.register_ui_component("test_panel", test_component, "Test Panel")

        assert "test_panel" in api.ui_components
        assert api.ui_components["test_panel"]["function"] == test_component

    def test_plugin_api_register_theme(self, mock_config):
        """Test theme registration"""
        api = PluginAPI(mock_config)

        test_theme = {
            "name": "test_theme",
            "colors": {
                "primary": "#ff0000",
                "secondary": "#00ff00"
            }
        }

        api.register_theme("test_theme", test_theme)

        assert "test_theme" in api.themes
        assert api.themes["test_theme"] == test_theme

    def test_plugin_api_register_keyboard_shortcut(self, mock_config):
        """Test keyboard shortcut registration"""
        api = PluginAPI(mock_config)

        def test_action():
            return "shortcut executed"

        api.register_keyboard_shortcut("ctrl+shift+t", test_action, "Test shortcut")

        assert "ctrl+shift+t" in api.keyboard_shortcuts
        assert api.keyboard_shortcuts["ctrl+shift+t"]["function"] == test_action

    def test_plugin_api_get_file_manager(self, mock_config):
        """Test file manager access"""
        api = PluginAPI(mock_config)

        mock_file_manager = Mock()
        api.file_manager = mock_file_manager

        assert api.get_file_manager() == mock_file_manager

    def test_plugin_api_get_ui_manager(self, mock_config):
        """Test UI manager access"""
        api = PluginAPI(mock_config)

        mock_ui_manager = Mock()
        api.ui_manager = mock_ui_manager

        assert api.get_ui_manager() == mock_ui_manager

    def test_plugin_api_get_ai_assistant(self, mock_config):
        """Test AI assistant access"""
        api = PluginAPI(mock_config)

        mock_ai_assistant = Mock()
        api.ai_assistant = mock_ai_assistant

        assert api.get_ai_assistant() == mock_ai_assistant


@pytest.mark.unit
class TestPluginManager:
    """Test the PluginManager class"""

    def test_plugin_manager_initialization(self, mock_config):
        """Test plugin manager initialization"""
        manager = PluginManager(mock_config)

        assert manager.config == mock_config
        assert len(manager.plugins) == 0
        assert len(manager.enabled_plugins) == 0

    def test_plugin_manager_load_plugin_from_file(self, mock_config, temp_dir):
        """Test loading plugin from file"""
        manager = PluginManager(mock_config)

        # Create a test plugin file
        plugin_file = temp_dir / "test_plugin.py"
        plugin_code = '''
from laxyfile.plugins.base_plugin import BasePlugin
from laxyfile.plugins.plugin_api import PluginAPI

class TestPlugin(BasePlugin):
    def get_name(self) -> str:
        return "test_plugin"

    def get_version(self) -> str:
        return "1.0.0"

    def get_description(self) -> str:
        return "Test plugin from file"

    def initialize(self, api: PluginAPI) -> None:
        self.api = api

    def cleanup(self) -> None:
        pass

# Plugin entry point
plugin_class = TestPlugin
'''
        plugin_file.write_text(plugin_code)

        # Load the plugin
        plugin = manager.load_plugin_from_file(plugin_file)

        assert plugin is not None
        assert plugin.get_name() == "test_plugin"
        assert plugin.get_version() == "1.0.0"

    def test_plugin_manager_load_invalid_plugin(self, mock_config, temp_dir):
        """Test loading invalid plugin file"""
        manager = PluginManager(mock_config)

        # Create an invalid plugin file
        plugin_file = temp_dir / "invalid_plugin.py"
        plugin_file.write_text("invalid python code !!!")

        # Should return None for invalid plugin
        plugin = manager.load_plugin_from_file(plugin_file)
        assert plugin is None

    def test_plugin_manager_register_plugin(self, mock_config):
        """Test plugin registration"""
        manager = PluginManager(mock_config)

        class TestPlugin(BasePlugin):
            def get_name(self) -> str:
                return "test_plugin"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Test plugin"

            def initialize(self, api: PluginAPI) -> None:
                pass

            def cleanup(self) -> None:
                pass

        plugin = TestPlugin()
        manager.register_plugin(plugin)

        assert "test_plugin" in manager.plugins
        assert manager.plugins["test_plugin"] == plugin

    def test_plugin_manager_register_duplicate_plugin(self, mock_config):
        """Test duplicate plugin registration"""
        manager = PluginManager(mock_config)

        class TestPlugin(BasePlugin):
            def get_name(self) -> str:
                return "test_plugin"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Test plugin"

            def initialize(self, api: PluginAPI) -> None:
                pass

            def cleanup(self) -> None:
                pass

        plugin1 = TestPlugin()
        plugin2 = TestPlugin()

        manager.register_plugin(plugin1)

        # Should raise error for duplicate plugin
        with pytest.raises(PluginError):
            manager.register_plugin(plugin2)

    def test_plugin_manager_enable_plugin(self, mock_config):
        """Test plugin enabling"""
        manager = PluginManager(mock_config)

        class TestPlugin(BasePlugin):
            def get_name(self) -> str:
                return "test_plugin"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Test plugin"

            def initialize(self, api: PluginAPI) -> None:
                self.initialized = True

            def cleanup(self) -> None:
                pass

        plugin = TestPlugin()
        manager.register_plugin(plugin)

        # Enable plugin
        result = manager.enable_plugin("test_plugin")

        assert result is True
        assert plugin.is_enabled()
        assert "test_plugin" in manager.enabled_plugins
        assert hasattr(plugin, 'initialized')

    def test_plugin_manager_disable_plugin(self, mock_config):
        """Test plugin disabling"""
        manager = PluginManager(mock_config)

        class TestPlugin(BasePlugin):
            def get_name(self) -> str:
                return "test_plugin"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Test plugin"

            def initialize(self, api: PluginAPI) -> None:
                pass

            def cleanup(self) -> None:
                self.cleaned_up = True

        plugin = TestPlugin()
        manager.register_plugin(plugin)
        manager.enable_plugin("test_plugin")

        # Disable plugin
        result = manager.disable_plugin("test_plugin")

        assert result is True
        assert not plugin.is_enabled()
        assert "test_plugin" not in manager.enabled_plugins
        assert hasattr(plugin, 'cleaned_up')

    def test_plugin_manager_get_plugin_info(self, mock_config):
        """Test getting plugin information"""
        manager = PluginManager(mock_config)

        class TestPlugin(BasePlugin):
            def get_name(self) -> str:
                return "test_plugin"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Test plugin"

            def get_author(self) -> str:
                return "Test Author"

            def get_dependencies(self) -> List[str]:
                return ["dependency1", "dependency2"]

            def initialize(self, api: PluginAPI) -> None:
                pass

            def cleanup(self) -> None:
                pass

        plugin = TestPlugin()
        manager.register_plugin(plugin)

        info = manager.get_plugin_info("test_plugin")

        assert info["name"] == "test_plugin"
        assert info["version"] == "1.0.0"
        assert info["description"] == "Test plugin"
        assert info["author"] == "Test Author"
        assert info["dependencies"] == ["dependency1", "dependency2"]
        assert info["enabled"] is False

    def test_plugin_manager_list_plugins(self, mock_config):
        """Test listing all plugins"""
        manager = PluginManager(mock_config)

        class TestPlugin1(BasePlugin):
            def get_name(self) -> str:
                return "plugin1"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Plugin 1"

            def initialize(self, api: PluginAPI) -> None:
                pass

            def cleanup(self) -> None:
                pass

        class TestPlugin2(BasePlugin):
            def get_name(self) -> str:
                return "plugin2"

            def get_version(self) -> str:
                return "2.0.0"

            def get_description(self) -> str:
                return "Plugin 2"

            def initialize(self, api: PluginAPI) -> None:
                pass

            def cleanup(self) -> None:
                pass

        plugin1 = TestPlugin1()
        plugin2 = TestPlugin2()

        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)
        manager.enable_plugin("plugin1")

        plugins = manager.list_plugins()

        assert len(plugins) == 2
        assert any(p["name"] == "plugin1" and p["enabled"] for p in plugins)
        assert any(p["name"] == "plugin2" and not p["enabled"] for p in plugins)

    def test_plugin_manager_discover_plugins(self, mock_config, temp_dir):
        """Test plugin discovery in directory"""
        manager = PluginManager(mock_config)

        # Create plugin directory
        plugin_dir = temp_dir / "plugins"
        plugin_dir.mkdir()

        # Create test plugin files
        plugin1_file = plugin_dir / "plugin1.py"
        plugin1_code = '''
from laxyfile.plugins.base_plugin import BasePlugin
from laxyfile.plugins.plugin_api import PluginAPI

class Plugin1(BasePlugin):
    def get_name(self) -> str:
        return "plugin1"

    def get_version(self) -> str:
        return "1.0.0"

    def get_description(self) -> str:
        return "Plugin 1"

    def initialize(self, api: PluginAPI) -> None:
        pass

    def cleanup(self) -> None:
        pass

plugin_class = Plugin1
'''
        plugin1_file.write_text(plugin1_code)

        plugin2_file = plugin_dir / "plugin2.py"
        plugin2_code = '''
from laxyfile.plugins.base_plugin import BasePlugin
from laxyfile.plugins.plugin_api import PluginAPI

class Plugin2(BasePlugin):
    def get_name(self) -> str:
        return "plugin2"

    def get_version(self) -> str:
        return "2.0.0"

    def get_description(self) -> str:
        return "Plugin 2"

    def initialize(self, api: PluginAPI) -> None:
        pass

    def cleanup(self) -> None:
        pass

plugin_class = Plugin2
'''
        plugin2_file.write_text(plugin2_code)

        # Discover plugins
        discovered = manager.discover_plugins(plugin_dir)

        assert len(discovered) == 2
        plugin_names = [p.get_name() for p in discovered]
        assert "plugin1" in plugin_names
        assert "plugin2" in plugin_names

    def test_plugin_manager_check_dependencies(self, mock_config):
        """Test plugin dependency checking"""
        manager = PluginManager(mock_config)

        class PluginWithDeps(BasePlugin):
            def get_name(self) -> str:
                return "plugin_with_deps"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Plugin with dependencies"

            def get_dependencies(self) -> List[str]:
                return ["requests", "nonexistent_package"]

            def initialize(self, api: PluginAPI) -> None:
                pass

            def cleanup(self) -> None:
                pass

        plugin = PluginWithDeps()

        # Check dependencies
        missing = manager.check_plugin_dependencies(plugin)

        # Should find nonexistent_package as missing
        assert "nonexistent_package" in missing
        # requests should be available (common package)
        assert "requests" not in missing

    def test_plugin_manager_unload_plugin(self, mock_config):
        """Test plugin unloading"""
        manager = PluginManager(mock_config)

        class TestPlugin(BasePlugin):
            def get_name(self) -> str:
                return "test_plugin"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Test plugin"

            def initialize(self, api: PluginAPI) -> None:
                pass

            def cleanup(self) -> None:
                self.cleaned_up = True

        plugin = TestPlugin()
        manager.register_plugin(plugin)
        manager.enable_plugin("test_plugin")

        # Unload plugin
        result = manager.unload_plugin("test_plugin")

        assert result is True
        assert "test_plugin" not in manager.plugins
        assert "test_plugin" not in manager.enabled_plugins
        assert hasattr(plugin, 'cleaned_up')

    def test_plugin_manager_reload_plugin(self, mock_config, temp_dir):
        """Test plugin reloading"""
        manager = PluginManager(mock_config)

        # Create initial plugin file
        plugin_file = temp_dir / "reload_test.py"
        plugin_code_v1 = '''
from laxyfile.plugins.base_plugin import BasePlugin
from laxyfile.plugins.plugin_api import PluginAPI

class ReloadTestPlugin(BasePlugin):
    def get_name(self) -> str:
        return "reload_test"

    def get_version(self) -> str:
        return "1.0.0"

    def get_description(self) -> str:
        return "Version 1"

    def initialize(self, api: PluginAPI) -> None:
        pass

    def cleanup(self) -> None:
        pass

plugin_class = ReloadTestPlugin
'''
        plugin_file.write_text(plugin_code_v1)

        # Load initial plugin
        plugin = manager.load_plugin_from_file(plugin_file)
        manager.register_plugin(plugin)

        assert plugin.get_description() == "Version 1"

        # Update plugin file
        plugin_code_v2 = plugin_code_v1.replace("Version 1", "Version 2").replace("1.0.0", "2.0.0")
        plugin_file.write_text(plugin_code_v2)

        # Reload plugin
        result = manager.reload_plugin("reload_test", plugin_file)

        assert result is True
        reloaded_plugin = manager.plugins["reload_test"]
        assert reloaded_plugin.get_description() == "Version 2"
        assert reloaded_plugin.get_version() == "2.0.0"


@pytest.mark.unit
class TestPluginIntegration:
    """Test the PluginIntegration class"""

    def test_plugin_integration_initialization(self, mock_config):
        """Test plugin integration initialization"""
        integration = PluginIntegration(mock_config)

        assert integration.config == mock_config
        assert integration.plugin_manager is not None
        assert integration.plugin_api is not None

    def test_plugin_integration_setup_api(self, mock_config):
        """Test API setup with core components"""
        integration = PluginIntegration(mock_config)

        mock_file_manager = Mock()
        mock_ui_manager = Mock()
        mock_ai_assistant = Mock()

        integration.setup_api(mock_file_manager, mock_ui_manager, mock_ai_assistant)

        assert integration.plugin_api.file_manager == mock_file_manager
        assert integration.plugin_api.ui_manager == mock_ui_manager
        assert integration.plugin_api.ai_assistant == mock_ai_assistant

    def test_plugin_integration_load_plugins_from_directory(self, mock_config, temp_dir):
        """Test loading plugins from directory"""
        integration = PluginIntegration(mock_config)

        # Create plugin directory with test plugin
        plugin_dir = temp_dir / "plugins"
        plugin_dir.mkdir()

        plugin_file = plugin_dir / "test_plugin.py"
        plugin_code = '''
from laxyfile.plugins.base_plugin import BasePlugin
from laxyfile.plugins.plugin_api import PluginAPI

class TestPlugin(BasePlugin):
    def get_name(self) -> str:
        return "integration_test"

    def get_version(self) -> str:
        return "1.0.0"

    def get_description(self) -> str:
        return "Integration test plugin"

    def initialize(self, api: PluginAPI) -> None:
        pass

    def cleanup(self) -> None:
        pass

plugin_class = TestPlugin
'''
        plugin_file.write_text(plugin_code)

        # Load plugins
        loaded_count = integration.load_plugins_from_directory(plugin_dir)

        assert loaded_count == 1
        assert "integration_test" in integration.plugin_manager.plugins

    def test_plugin_integration_enable_all_plugins(self, mock_config):
        """Test enabling all registered plugins"""
        integration = PluginIntegration(mock_config)

        # Create and register test plugins
        class TestPlugin1(BasePlugin):
            def get_name(self) -> str:
                return "plugin1"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Plugin 1"

            def initialize(self, api: PluginAPI) -> None:
                pass

            def cleanup(self) -> None:
                pass

        class TestPlugin2(BasePlugin):
            def get_name(self) -> str:
                return "plugin2"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Plugin 2"

            def initialize(self, api: PluginAPI) -> None:
                pass

            def cleanup(self) -> None:
                pass

        integration.plugin_manager.register_plugin(TestPlugin1())
        integration.plugin_manager.register_plugin(TestPlugin2())

        # Enable all plugins
        enabled_count = integration.enable_all_plugins()

        assert enabled_count == 2
        assert len(integration.plugin_manager.enabled_plugins) == 2

    def test_plugin_integration_get_plugin_commands(self, mock_config):
        """Test getting commands from plugins"""
        integration = PluginIntegration(mock_config)

        # Register test command
        def test_command():
            return "test result"

        integration.plugin_api.register_command("test_cmd", test_command, "Test command")

        commands = integration.get_plugin_commands()

        assert "test_cmd" in commands
        assert commands["test_cmd"]["description"] == "Test command"

    def test_plugin_integration_execute_plugin_command(self, mock_config):
        """Test executing plugin command"""
        integration = PluginIntegration(mock_config)

        # Register test command
        def test_command(arg1, arg2=None):
            return f"result: {arg1}, {arg2}"

        integration.plugin_api.register_command("test_cmd", test_command, "Test command")

        # Execute command
        result = integration.execute_plugin_command("test_cmd", "value1", arg2="value2")

        assert result == "result: value1, value2"

    def test_plugin_integration_get_plugin_ui_components(self, mock_config):
        """Test getting UI components from plugins"""
        integration = PluginIntegration(mock_config)

        # Register test UI component
        def test_component():
            return "UI Component"

        integration.plugin_api.register_ui_component("test_panel", test_component, "Test Panel")

        components = integration.get_plugin_ui_components()

        assert "test_panel" in components
        assert components["test_panel"]["description"] == "Test Panel"

    def test_plugin_integration_get_plugin_themes(self, mock_config):
        """Test getting themes from plugins"""
        integration = PluginIntegration(mock_config)

        # Register test theme
        test_theme = {
            "name": "plugin_theme",
            "colors": {"primary": "#ff0000"}
        }

        integration.plugin_api.register_theme("plugin_theme", test_theme)

        themes = integration.get_plugin_themes()

        assert "plugin_theme" in themes
        assert themes["plugin_theme"]["colors"]["primary"] == "#ff0000"

    def test_plugin_integration_cleanup(self, mock_config):
        """Test plugin integration cleanup"""
        integration = PluginIntegration(mock_config)

        class TestPlugin(BasePlugin):
            def get_name(self) -> str:
                return "cleanup_test"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Cleanup test plugin"

            def initialize(self, api: PluginAPI) -> None:
                pass

            def cleanup(self) -> None:
                self.cleaned_up = True

        plugin = TestPlugin()
        integration.plugin_manager.register_plugin(plugin)
        integration.plugin_manager.enable_plugin("cleanup_test")

        # Cleanup
        integration.cleanup()

        assert hasattr(plugin, 'cleaned_up')
        assert not plugin.is_enabled()

    def test_plugin_integration_error_handling(self, mock_config):
        """Test error handling in plugin integration"""
        integration = PluginIntegration(mock_config)

        class FaultyPlugin(BasePlugin):
            def get_name(self) -> str:
                return "faulty_plugin"

            def get_version(self) -> str:
                return "1.0.0"

            def get_description(self) -> str:
                return "Faulty plugin"

            def initialize(self, api: PluginAPI) -> None:
                raise Exception("Initialization failed")

            def cleanup(self) -> None:
                pass

        plugin = FaultyPlugin()
        integration.plugin_manager.register_plugin(plugin)

        # Should handle initialization error gracefully
        result = integration.plugin_manager.enable_plugin("faulty_plugin")

        assert result is False
        assert not plugin.is_enabled()

    def test_plugin_integration_event_system(self, mock_config):
        """Test plugin event system integration"""
        integration = PluginIntegration(mock_config)

        # Register event handler
        results = []

        def test_handler(data):
            results.append(f"handled: {data}")

        integration.plugin_api.register_event_handler("test_event", test_handler)

        # Emit event
        integration.emit_event("test_event", "test_data")

        assert len(results) == 1
        assert results[0] == "handled: test_data"