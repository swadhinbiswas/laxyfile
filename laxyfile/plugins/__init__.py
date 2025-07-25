"""
LaxyFile Plugin System

This package provides a comprehensive plugin architecture with dynamic loading,
API management, and extensibility features for LaxyFile.
"""

from .plugin_manager import PluginManager, PluginInfo, PluginStatus
from .plugin_api import PluginAPI, APIVersion, APICapability
from .base_plugin import (
    BasePlugin, PluginType, PluginCapability, PluginPriority,
    PluginMetadata, PluginConfig, PluginHook,
    FileHandlerPlugin, PreviewRendererPlugin, ThemeProviderPlugin, CommandExtensionPlugin
)
from .plugin_loader import PluginLoader, LoadResult, InstallResult, PluginPackage, PluginSource
from .plugin_integration import PluginIntegration, PluginIntegrationConfig

__all__ = [
    # Core plugin system
    'PluginManager',
    'PluginInfo',
    'PluginStatus',
    'PluginAPI',
    'APIVersion',
    'APICapability',

    # Base plugin classes
    'BasePlugin',
    'FileHandlerPlugin',
    'PreviewRendererPlugin',
    'ThemeProviderPlugin',
    'CommandExtensionPlugin',

    # Plugin metadata and configuration
    'PluginType',
    'PluginCapability',
    'PluginPriority',
    'PluginMetadata',
    'PluginConfig',
    'PluginHook',

    # Plugin loading and installation
    'PluginLoader',
    'LoadResult',
    'InstallResult',
    'PluginPackage',
    'PluginSource',

    # Plugin integration
    'PluginIntegration',
    'PluginIntegrationConfig'
]