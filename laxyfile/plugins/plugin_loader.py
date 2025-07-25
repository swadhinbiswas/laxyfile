"""
Plugin Loader System

This module provides utilities for loading and managing plugin files,
including validation, dependency resolution, and installation.
"""

import asyncio
import zipfile
import tarfile
import shutil
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import yaml
import tempfile
from urllib.parse import urlparse

from .base_plugin import BasePlugin, PluginMetadata, PluginConfig
from .plugin_manager import PluginManager, LoadResult
from ..core.exceptions import PluginError
from ..utils.logger import Logger


class PluginSource(Enum):
    """Plugin source types"""
    LOCAL_FILE = "local_file"
    LOCAL_DIRECTORY = "local_directory"
    REMOTE_URL = "remote_url"
    PLUGIN_REGISTRY = "plugin_registry"
    GIT_REPOSITORY = "git_repository"


@dataclass
class PluginPackage:
    """Plugin package information"""
    name: str
    version: str
    source: PluginSource
    location: str
    metadata: Optional[PluginMetadata] = None
    dependencies: List[str] = None
    size: Optional[int] = None
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'version': self.version,
            'source': self.source.value,
            'location': self.location,
            'metadata': self.metadata.to_dict() if self.metadata else None,
            'dependencies': self.dependencies or [],
            'size': self.size,
            'checksum': self.checksum
        }


@dataclass
class InstallResult:
    """Result of plugin installation"""
    success: bool
    plugin_id: str
    message: str
    installed_path: Optional[Path] = None
    error: Optional[Exception] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'plugin_id': self.plugin_id,
            'message': self.message,
            'installed_path': str(self.installed_path) if self.installed_path else None,
            'error': str(self.error) if self.error else None
        }


class PluginValidator:
    """Plugin validation utilities"""

    def __init__(self):
        self.logger = Logger()

    def validate_plugin_structure(self, plugin_path: Path) -> Tuple[bool, List[str]]:
        """Validate plugin directory structure"""
        errors = []

        try:
            if not plugin_path.exists():
                errors.append("Plugin path does not exist")
                return False, errors

            if plugin_path.is_file():
                # Single file plugin
                if not plugin_path.name.endswith('.py'):
                    errors.append("Plugin file must be a Python file")

                # Check if file contains a plugin class
                if not self._contains_plugin_class(plugin_path):
                    errors.append("Plugin file does not contain a valid plugin class")

            else:
                # Directory plugin
                plugin_file = plugin_path / "plugin.py"
                init_file = plugin_path / "__init__.py"

                if not plugin_file.exists() and not init_file.exists():
                    errors.append("Plugin directory must contain plugin.py or __init__.py")

                # Check for metadata file
                metadata_file = plugin_path / "plugin.yaml"
                if metadata_file.exists():
                    if not self._validate_metadata_file(metadata_file):
                        errors.append("Invalid plugin metadata file")

                # Check for required files
                main_file = plugin_file if plugin_file.exists() else init_file
                if main_file and not self._contains_plugin_class(main_file):
                    errors.append("Plugin does not contain a valid plugin class")

            return len(errors) == 0, errors

        except Exception as e:
            self.logger.error(f"Error validating plugin structure: {e}")
            errors.append(f"Validation error: {e}")
            return False, errors

    def _contains_plugin_class(self, file_path: Path) -> bool:
        """Check if file contains a valid plugin class"""
        try:
            content = file_path.read_text()

            # Simple check for BasePlugin import and class definition
            has_import = ('from laxyfile.plugins' in content or
                         'import laxyfile.plugins' in content or
                         'BasePlugin' in content)

            has_class = 'class ' in content and 'BasePlugin' in content

            return has_import and has_class

        except Exception as e:
            self.logger.error(f"Error checking plugin class in {file_path}: {e}")
            return False

    def _validate_metadata_file(self, metadata_file: Path) -> bool:
        """Validate plugin metadata file"""
        try:
            with open(metadata_file, 'r') as f:
                metadata = yaml.safe_load(f)

            required_fields = ['name', 'version', 'author', 'description']

            for field in required_fields:
                if field not in metadata:
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating metadata file: {e}")
            return False

    def validate_dependencies(self, plugin_metadata: PluginMetadata,
                            available_plugins: Set[str]) -> Tuple[bool, List[str]]:
        """Validate plugin dependencies"""
        errors = []

        for dependency in plugin_metadata.dependencies:
            if dependency not in available_plugins:
                errors.append(f"Missing dependency: {dependency}")

        return len(errors) == 0, errors

    def validate_compatibility(self, plugin_metadata: PluginMetadata) -> Tuple[bool, List[str]]:
        """Validate plugin compatibility with current LaxyFile version"""
        errors = []

        # This would check again LaxyFile version
        current_version = "1.0.0"  # Would be imported from main package

        if plugin_metadata.min_laxyfile_version:
            # Version comparison logic would go here
            pass

        if plugin_metadata.max_laxyfile_version:
            # Version comparison logic would go here
            pass

        return len(errors) == 0, errors


class PluginLoader:
    """Plugin loading and installation utilities"""

    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        self.validator = PluginValidator()
        self.logger = Logger()

        # Plugin installation directory
        self.install_dir = Path.home() / ".laxyfile" / "plugins"
        self.install_dir.mkdir(parents=True, exist_ok=True)

        # Temporary directory for downloads
        self.temp_dir = Path(tempfile.gettempdir()) / "laxyfile_plugins"
        self.temp_dir.mkdir(exist_ok=True)

    async def install_plugin(self, source: str, source_type: PluginSource = None) -> InstallResult:
        """Install plugin from various sources"""
        try:
            # Auto-detect source type if not provided
            if source_type is None:
                source_type = self._detect_source_type(source)

            self.logger.info(f"Installing plugin from {source_type.value}: {source}")

            # Download/extract plugin to temporary location
            temp_plugin_path = await self._prepare_plugin(source, source_type)
            if not temp_plugin_path:
                return InstallResult(
                    success=False,
                    plugin_id="unknown",
                    message="Failed to prepare plugin for installation"
                )

            # Validate plugin structure
            is_valid, validation_errors = self.validator.validate_plugin_structure(temp_plugin_path)
            if not is_valid:
                return InstallResult(
                    success=False,
                    plugin_id="unknown",
                    message=f"Plugin validation failed: {'; '.join(validation_errors)}"
                )

            # Load plugin metadata
            metadata = await self._load_plugin_metadata(temp_plugin_path)
            if not metadata:
                return InstallResult(
                    success=False,
                    plugin_id="unknown",
                    message="Failed to load plugin metadata"
                )

            plugin_id = metadata.name.lower().replace(' ', '_')

            # Check if plugin already exists
            if plugin_id in self.plugin_manager.plugins:
                return InstallResult(
                    success=False,
                    plugin_id=plugin_id,
                    message="Plugin already installed"
                )

            # Validate dependencies
            available_plugins = set(self.plugin_manager.plugins.keys())
            deps_valid, dep_errors = self.validator.validate_dependencies(metadata, available_plugins)
            if not deps_valid:
                return InstallResult(
                    success=False,
                    plugin_id=plugin_id,
                    message=f"Dependency validation failed: {'; '.join(dep_errors)}"
                )

            # Validate compatibility
            compat_valid, compat_errors = self.validator.validate_compatibility(metadata)
            if not compat_valid:
                return InstallResult(
                    success=False,
                    plugin_id=plugin_id,
                    message=f"Compatibility check failed: {'; '.join(compat_errors)}"
                )

            # Install plugin to final location
            final_plugin_path = self.install_dir / plugin_id
            if final_plugin_path.exists():
                shutil.rmtree(final_plugin_path)

            if temp_plugin_path.is_file():
                # Single file plugin
                final_plugin_path.mkdir(parents=True)
                shutil.copy2(temp_plugin_path, final_plugin_path / "plugin.py")
            else:
                # Directory plugin
                shutil.copytree(temp_plugin_path, final_plugin_path)

            # Load the plugin
            plugin_file = final_plugin_path / "plugin.py"
            if not plugin_file.exists():
                plugin_file = final_plugin_path / "__init__.py"

            load_result = await self.plugin_manager.load_plugin(plugin_file)

            if load_result.success:
                self.logger.info(f"Successfully installed plugin: {plugin_id}")
                return InstallResult(
                    success=True,
                    plugin_id=plugin_id,
                    message="Plugin installed successfully",
                    installed_path=final_plugin_path
                )
            else:
                # Clean up on load failure
                if final_plugin_path.exists():
                    shutil.rmtree(final_plugin_path)

                return InstallResult(
                    success=False,
                    plugin_id=plugin_id,
                    message=f"Plugin installation failed: {load_result.message}"
                )

        except Exception as e:
            self.logger.error(f"Error installing plugin: {e}")
            return InstallResult(
                success=False,
                plugin_id="unknown",
                message=f"Installation error: {e}",
                error=e
            )

        finally:
            # Clean up temporary files
            if 'temp_plugin_path' in locals() and temp_plugin_path.exists():
                if temp_plugin_path.is_file():
                    temp_plugin_path.unlink()
                else:
                    shutil.rmtree(temp_plugin_path)

    async def uninstall_plugin(self, plugin_id: str) -> InstallResult:
        """Uninstall a plugin"""
        try:
            if plugin_id not in self.plugin_manager.plugins:
                return InstallResult(
                    success=False,
                    plugin_id=plugin_id,
                    message="Plugin not found"
                )

            plugin_info = self.plugin_manager.plugins[plugin_id]

            # Unload plugin first
            unload_result = await self.plugin_manager.unload_plugin(plugin_id)
            if not unload_result.success:
                return InstallResult(
                    success=False,
                    plugin_id=plugin_id,
                    message=f"Failed to unload plugin: {unload_result.message}"
                )

            # Remove plugin files
            plugin_path = plugin_info.plugin_path.parent
            if plugin_path.exists() and plugin_path.is_relative_to(self.install_dir):
                shutil.rmtree(plugin_path)

            self.logger.info(f"Successfully uninstalled plugin: {plugin_id}")
            return InstallResult(
                success=True,
                plugin_id=plugin_id,
                message="Plugin uninstalled successfully"
            )

        except Exception as e:
            self.logger.error(f"Error uninstalling plugin {plugin_id}: {e}")
            return InstallResult(
                success=False,
                plugin_id=plugin_id,
                message=f"Uninstallation error: {e}",
                error=e
            )

    def _detect_source_type(self, source: str) -> PluginSource:
        """Auto-detect plugin source type"""
        path = Path(source)

        if path.exists():
            if path.is_file():
                return PluginSource.LOCAL_FILE
            else:
                return PluginSource.LOCAL_DIRECTORY

        parsed_url = urlparse(source)
        if parsed_url.scheme in ['http', 'https']:
            if source.endswith('.git'):
                return PluginSource.GIT_REPOSITORY
            else:
                return PluginSource.REMOTE_URL

        # Default to plugin registry
        return PluginSource.PLUGIN_REGISTRY

    async def _prepare_plugin(self, source: str, source_type: PluginSource) -> Optional[Path]:
        """Prepare plugin for installation based on source type"""
        try:
            if source_type == PluginSource.LOCAL_FILE:
                return Path(source)

            elif source_type == PluginSource.LOCAL_DIRECTORY:
                return Path(source)

            elif source_type == PluginSource.REMOTE_URL:
                return await self._download_plugin(source)

            elif source_type == PluginSource.GIT_REPOSITORY:
                return await self._clone_git_plugin(source)

            elif source_type == PluginSource.PLUGIN_REGISTRY:
                return await self._download_from_registry(source)

            return None

        except Exception as e:
            self.logger.error(f"Error preparing plugin from {source}: {e}")
            return None

    async def _download_plugin(self, url: str) -> Optional[Path]:
        """Download plugin from URL"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Determine file type from URL or content-type
            if url.endswith('.zip') or 'zip' in response.headers.get('content-type', ''):
                temp_file = self.temp_dir / f"plugin_{hash(url)}.zip"

                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # Extract zip file
                extract_dir = self.temp_dir / f"plugin_{hash(url)}_extracted"
                with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                temp_file.unlink()  # Clean up zip file
                return extract_dir

            elif url.endswith('.tar.gz') or 'tar' in response.headers.get('content-type', ''):
                temp_file = self.temp_dir / f"plugin_{hash(url)}.tar.gz"

                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # Extract tar file
                extract_dir = self.temp_dir / f"plugin_{hash(url)}_extracted"
                with tarfile.open(temp_file, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_dir)

                temp_file.unlink()  # Clean up tar file
                return extract_dir

            else:
                # Assume it's a single Python file
                temp_file = self.temp_dir / f"plugin_{hash(url)}.py"

                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                return temp_file

        except Exception as e:
            self.logger.error(f"Error downloading plugin from {url}: {e}")
            return None

    async def _clone_git_plugin(self, git_url: str) -> Optional[Path]:
        """Clone plugin from Git repository"""
        try:
            import subprocess

            clone_dir = self.temp_dir / f"git_plugin_{hash(git_url)}"

            # Clone repository
            result = subprocess.run([
                'git', 'clone', git_url, str(clone_dir)
            ], capture_output=True, text=True)

            if result.returncode != 0:
                self.logger.error(f"Git clone failed: {result.stderr}")
                return None

            return clone_dir

        except Exception as e:
            self.logger.error(f"Error cloning git plugin from {git_url}: {e}")
            return None

    async def _download_from_registry(self, plugin_name: str) -> Optional[Path]:
        """Download plugin from plugin registry"""
        try:
            # This would integrate with a plugin registry service
            # For now, just return None to indicate not implemented
            self.logger.warning(f"Plugin registry not implemented for: {plugin_name}")
            return None

        except Exception as e:
            self.logger.error(f"Error downloading from registry: {e}")
            return None

    async def _load_plugin_metadata(self, plugin_path: Path) -> Optional[PluginMetadata]:
        """Load plugin metadata from plugin path"""
        try:
            # Try to load from plugin.yaml first
            metadata_file = plugin_path / "plugin.yaml"
            if plugin_path.is_dir() and metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata_data = yaml.safe_load(f)
                    return PluginMetadata.from_dict(metadata_data)

            # Fallback to loading from Python file
            if plugin_path.is_file():
                main_file = plugin_path
            else:
                main_file = plugin_path / "plugin.py"
                if not main_file.exists():
                    main_file = plugin_path / "__init__.py"

            if main_file.exists():
                # This would use the same logic as in plugin_manager
                # For now, return a basic metadata object
                return PluginMetadata(
                    name=plugin_path.stem,
                    version="1.0.0",
                    author="Unknown",
                    description="Plugin loaded from file",
                    plugin_type="utility",
                    capabilities=set()
                )

            return None

        except Exception as e:
            self.logger.error(f"Error loading plugin metadata: {e}")
            return None

    def list_available_plugins(self) -> List[PluginPackage]:
        """List available plugins from various sources"""
        plugins = []

        # List local plugins in install directory
        if self.install_dir.exists():
            for plugin_dir in self.install_dir.iterdir():
                if plugin_dir.is_dir():
                    metadata_file = plugin_dir / "plugin.yaml"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata_data = yaml.safe_load(f)
                                metadata = PluginMetadata.from_dict(metadata_data)

                                plugins.append(PluginPackage(
                                    name=metadata.name,
                                    version=metadata.version,
                                    source=PluginSource.LOCAL_DIRECTORY,
                                    location=str(plugin_dir),
                                    metadata=metadata
                                ))
                        except Exception as e:
                            self.logger.error(f"Error reading plugin metadata: {e}")

        return plugins

    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(exist_ok=True)
        except Exception as e:
            self.logger.error(f"Error cleaning up temp files: {e}")

    def __str__(self) -> str:
        """String representation"""
        return f"PluginLoader: install_dir={self.install_dir}"

    def __repr__(self) -> str:
        """Detailed representation"""
        return f"<PluginLoader: install_dir={self.install_dir}>"