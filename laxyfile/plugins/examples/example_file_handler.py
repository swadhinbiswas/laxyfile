"""
Example File Handler Plugin

This plugin demonstrates how to create a file handler plugin that can
process specific file types.
"""

from pathlib import Path
from typing import Any, Dict
import json

from ..base_plugin import FileHandlerPlugin, PluginMetadata, PluginType, PluginCapability


class JSONFileHandlerPlugin(FileHandlerPlugin):
    """Example plugin for handling JSON files"""

    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata"""
        return PluginMetadata(
            name="JSON File Handler",
            version="1.0.0",
            author="LaxyFile Team",
            description="Handles JSON file operations with validation and formatting",
            plugin_type=PluginType.FILE_HANDLER,
            capabilities={PluginCapability.FILE_OPERATIONS, PluginCapability.ANALYSIS},
            tags=["json", "file-handler", "validation"],
            homepage="https://github.com/laxyfile/plugins/json-handler"
        )

    async def _load(self) -> bool:
        """Load the plugin"""
        try:
            # Register for JSON file handling
            if self.api:
                self.api.register_event_handler('file_open', self._handle_file_open)
                self.api.register_event_handler('file_save', self._handle_file_save)

            # Create hooks for other plugins to extend JSON handling
            self.create_hook('json_validate', 'Validate JSON content')
            self.create_hook('json_format', 'Format JSON content')

            self.logger.info("JSON File Handler plugin loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error loading JSON File Handler plugin: {e}")
            return False

    async def _unload(self) -> bool:
        """Unload the plugin"""
        try:
            # Unregister event handlers
            if self.api:
                self.api.remove_event_handler('file_open', self._handle_file_open)
                self.api.remove_event_handler('file_save', self._handle_file_save)

            self.logger.info("JSON File Handler plugin unloaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error unloading JSON File Handler plugin: {e}")
            return False

    def can_handle(self, file_path: Path) -> bool:
        """Check if this plugin can handle the file"""
        return file_path.suffix.lower() == '.json'

    async def handle_file(self, file_path: Path, action: str, **kwargs) -> Any:
        """Handle file operation"""
        try:
            if action == 'validate':
                return await self._validate_json(file_path)
            elif action == 'format':
                return await self._format_json(file_path, **kwargs)
            elif action == 'analyze':
                return await self._analyze_json(file_path)
            else:
                return {'error': f'Unsupported action: {action}'}

        except Exception as e:
            self.logger.error(f"Error handling JSON file {file_path}: {e}")
            return {'error': str(e)}

    async def _handle_file_open(self, event_name: str, data: Dict[str, Any]) -> Any:
        """Handle file open event"""
        file_path = Path(data.get('file_path', ''))

        if self.can_handle(file_path):
            # Validate JSON when opening
            validation_result = await self._validate_json(file_path)

            if not validation_result['valid']:
                if self.api:
                    await self.api.show_notification(
                        f"JSON validation warning: {validation_result['error']}",
                        level="warning"
                    )

            return validation_result

        return None

    async def _handle_file_save(self, event_name: str, data: Dict[str, Any]) -> Any:
        """Handle file save event"""
        file_path = Path(data.get('file_path', ''))

        if self.can_handle(file_path):
            # Auto-format JSON on save if enabled
            if self.get_setting('auto_format', True):
                format_result = await self._format_json(file_path)

                if format_result['success'] and self.api:
                    await self.api.show_notification(
                        "JSON file formatted automatically",
                        level="info"
                    )

            return {'handled': True}

        return None

    async def _validate_json(self, file_path: Path) -> Dict[str, Any]:
        """Validate JSON file"""
        try:
            if not file_path.exists():
                return {'valid': False, 'error': 'File does not exist'}

            content = file_path.read_text()

            # Execute validation hooks
            hook_results = []
            if 'json_validate' in self.hooks:
                hook_results = await self.hooks['json_validate'].execute(content)

            # Basic JSON validation
            try:
                json.loads(content)

                result = {
                    'valid': True,
                    'file_path': str(file_path),
                    'size': len(content),
                    'lines': len(content.splitlines()),
                    'hook_results': hook_results
                }

                return result

            except json.JSONDecodeError as e:
                return {
                    'valid': False,
                    'error': f'JSON syntax error: {e.msg} at line {e.lineno}, column {e.colno}',
                    'line': e.lineno,
                    'column': e.colno
                }

        except Exception as e:
            return {'valid': False, 'error': str(e)}

    async def _format_json(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """Format JSON file"""
        try:
            if not file_path.exists():
                return {'success': False, 'error': 'File does not exist'}

            content = file_path.read_text()

            # Parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f'Cannot format invalid JSON: {e.msg}'
                }

            # Get formatting options
            indent = kwargs.get('indent', self.get_setting('indent', 2))
            sort_keys = kwargs.get('sort_keys', self.get_setting('sort_keys', False))
            ensure_ascii = kwargs.get('ensure_ascii', self.get_setting('ensure_ascii', False))

            # Execute formatting hooks
            hook_results = []
            if 'json_format' in self.hooks:
                hook_results = await self.hooks['json_format'].execute(data, kwargs)

            # Format JSON
            formatted_content = json.dumps(
                data,
                indent=indent,
                sort_keys=sort_keys,
                ensure_ascii=ensure_ascii
            )

            # Write back to file if requested
            if kwargs.get('write_back', False):
                file_path.write_text(formatted_content)

            return {
                'success': True,
                'formatted_content': formatted_content,
                'original_size': len(content),
                'formatted_size': len(formatted_content),
                'hook_results': hook_results
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _analyze_json(self, file_path: Path) -> Dict[str, Any]:
        """Analyze JSON file structure"""
        try:
            if not file_path.exists():
                return {'error': 'File does not exist'}

            content = file_path.read_text()

            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                return {'error': f'Invalid JSON: {e.msg}'}

            # Analyze structure
            analysis = {
                'file_path': str(file_path),
                'file_size': len(content),
                'type': type(data).__name__,
                'structure': self._analyze_structure(data),
                'statistics': self._calculate_statistics(data)
            }

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def _analyze_structure(self, data: Any, depth: int = 0, max_depth: int = 5) -> Dict[str, Any]:
        """Analyze JSON data structure"""
        if depth > max_depth:
            return {'type': 'truncated', 'reason': 'max_depth_exceeded'}

        if isinstance(data, dict):
            return {
                'type': 'object',
                'keys': len(data),
                'properties': {
                    key: self._analyze_structure(value, depth + 1, max_depth)
                    for key, value in list(data.items())[:10]  # Limit to first 10 keys
                }
            }
        elif isinstance(data, list):
            return {
                'type': 'array',
                'length': len(data),
                'items': [
                    self._analyze_structure(item, depth + 1, max_depth)
                    for item in data[:5]  # Limit to first 5 items
                ]
            }
        else:
            return {
                'type': type(data).__name__,
                'value': str(data)[:100] if isinstance(data, str) else data
            }

    def _calculate_statistics(self, data: Any) -> Dict[str, Any]:
        """Calculate JSON statistics"""
        stats = {
            'total_keys': 0,
            'total_values': 0,
            'max_depth': 0,
            'types': {}
        }

        def count_recursive(obj, depth=0):
            stats['max_depth'] = max(stats['max_depth'], depth)

            if isinstance(obj, dict):
                stats['total_keys'] += len(obj)
                for value in obj.values():
                    count_recursive(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    count_recursive(item, depth + 1)
            else:
                stats['total_values'] += 1
                type_name = type(obj).__name__
                stats['types'][type_name] = stats['types'].get(type_name, 0) + 1

        count_recursive(data)
        return stats