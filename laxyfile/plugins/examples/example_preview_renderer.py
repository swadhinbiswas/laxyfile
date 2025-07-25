"""
Example Preview Renderer Plugin

This plugin demonstrates how to create a preview renderer plugin for
generating custom file previews.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import hashlib
import base64

from ..base_plugin import PreviewRendererPlugin, PluginMetadata, PluginType, PluginCapability


class MarkdownPreviewPlugin(PreviewRendererPlugin):
    """Example plugin for rendering Markdown file previews"""

    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata"""
        return PluginMetadata(
            name="Markdown Preview Renderer",
            version="1.0.0",
            author="LaxyFile Team",
            description="Renders Markdown files with syntax highlighting and HTML preview",
            plugin_type=PluginType.PREVIEW_RENDERER,
            capabilities={PluginCapability.PREVIEW_GENERATION},
            tags=["markdown", "preview", "html"],
            dependencies=["markdown", "pygments"],
            homepage="https://github.com/laxyfile/plugins/markdown-preview"
        )

    async def _load(self) -> bool:
        """Load the plugin"""
        try:
            # Check for required dependencies
            try:
                import markdown
                import pygments
                self.markdown = markdown
                self.pygments = pygments
            except ImportError as e:
                self.logger.error(f"Missing required dependency: {e}")
                return False

            # Register preview renderer
            if self.api:
                self.api.register_preview_renderer(
                    ['.md', '.markdown', '.mdown', '.mkd'],
                    self.generate_preview
                )

            # Create hooks for extending markdown re
            self.create_hook('markdown_preprocess', 'Preprocess markdown content')
            self.create_hook('markdown_postprocess', 'Postprocess rendered HTML')

            self.logger.info("Markdown Preview plugin loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error loading Markdown Preview plugin: {e}")
            return False

    async def _unload(self) -> bool:
        """Unload the plugin"""
        try:
            self.logger.info("Markdown Preview plugin unloaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error unloading Markdown Preview plugin: {e}")
            return False

    def can_preview(self, file_path: Path) -> bool:
        """Check if this plugin can preview the file"""
        return file_path.suffix.lower() in ['.md', '.markdown', '.mdown', '.mkd']

    async def generate_preview(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """Generate preview for Markdown file"""
        try:
            if not file_path.exists():
                return {'error': 'File does not exist'}

            if not self.can_preview(file_path):
                return {'error': 'Unsupported file type'}

            # Read file content
            content = file_path.read_text(encoding='utf-8')

            # Execute preprocessing hooks
            preprocess_results = []
            if 'markdown_preprocess' in self.hooks:
                preprocess_results = await self.hooks['markdown_preprocess'].execute(content)
                # Use the last result if any hooks modified the content
                if preprocess_results:
                    content = preprocess_results[-1] or content

            # Configure markdown processor
            extensions = kwargs.get('extensions', self.get_setting('extensions', [
                'codehilite',
                'fenced_code',
                'tables',
                'toc',
                'footnotes',
                'attr_list',
                'def_list'
            ]))

            extension_configs = kwargs.get('extension_configs', self.get_setting('extension_configs', {
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True
                },
                'toc': {
                    'permalink': True
                }
            }))\n            \n            # Create markdown processor\n            md = self.markdown.Markdown(\n                extensions=extensions,\n                extension_configs=extension_configs\n            )\n            \n            # Convert to HTML\n            html_content = md.convert(content)\n            \n            # Execute postprocessing hooks\n            postprocess_results = []\n            if 'markdown_postprocess' in self.hooks:\n                postprocess_results = await self.hooks['markdown_postprocess'].execute(html_content)\n                # Use the last result if any hooks modified the content\n                if postprocess_results:\n                    html_content = postprocess_results[-1] or html_content\n            \n            # Generate metadata\n            metadata = {\n                'title': self._extract_title(content),\n                'word_count': len(content.split()),\n                'line_count': len(content.splitlines()),\n                'headings': self._extract_headings(content),\n                'links': self._extract_links(content),\n                'images': self._extract_images(content)\n            }\n            \n            # Create preview data\n            preview_data = {\n                'type': 'markdown',\n                'file_path': str(file_path),\n                'raw_content': content,\n                'html_content': html_content,\n                'metadata': metadata,\n                'toc': getattr(md, 'toc', ''),\n                'toc_tokens': getattr(md, 'toc_tokens', []),\n                'preview_html': self._create_preview_html(html_content, metadata),\n                'cache_key': self._generate_cache_key(file_path, content),\n                'preprocess_results': preprocess_results,\n                'postprocess_results': postprocess_results\n            }\n            \n            return preview_data\n            \n        except Exception as e:\n            self.logger.error(f\"Error generating markdown preview for {file_path}: {e}\")\n            return {'error': str(e)}\n    \n    def _extract_title(self, content: str) -> Optional[str]:\n        \"\"\"Extract title from markdown content\"\"\"\n        lines = content.splitlines()\n        \n        for line in lines:\n            line = line.strip()\n            if line.startswith('# '):\n                return line[2:].strip()\n            elif line.startswith('='):\n                # Setext-style header\n                prev_line_idx = lines.index(line) - 1\n                if prev_line_idx >= 0:\n                    return lines[prev_line_idx].strip()\n        \n        return None\n    \n    def _extract_headings(self, content: str) -> list:\n        \"\"\"Extract headings from markdown content\"\"\"\n        headings = []\n        lines = content.splitlines()\n        \n        for i, line in enumerate(lines):\n            line = line.strip()\n            \n            # ATX-style headers\n            if line.startswith('#'):\n                level = 0\n                for char in line:\n                    if char == '#':\n                        level += 1\n                    else:\n                        break\n                \n                if level <= 6:\n                    text = line[level:].strip()\n                    headings.append({\n                        'level': level,\n                        'text': text,\n                        'line': i + 1\n                    })\n            \n            # Setext-style headers\n            elif line and i + 1 < len(lines):\n                next_line = lines[i + 1].strip()\n                if next_line and all(c in '=-' for c in next_line):\n                    level = 1 if next_line[0] == '=' else 2\n                    headings.append({\n                        'level': level,\n                        'text': line,\n                        'line': i + 1\n                    })\n        \n        return headings\n    \n    def _extract_links(self, content: str) -> list:\n        \"\"\"Extract links from markdown content\"\"\"\n        import re\n        \n        links = []\n        \n        # Inline links: [text](url)\n        inline_pattern = r'\\[([^\\]]+)\\]\\(([^\\)]+)\\)'\n        for match in re.finditer(inline_pattern, content):\n            links.append({\n                'type': 'inline',\n                'text': match.group(1),\n                'url': match.group(2),\n                'position': match.start()\n            })\n        \n        # Reference links: [text][ref]\n        ref_pattern = r'\\[([^\\]]+)\\]\\[([^\\]]+)\\]'\n        for match in re.finditer(ref_pattern, content):\n            links.append({\n                'type': 'reference',\n                'text': match.group(1),\n                'ref': match.group(2),\n                'position': match.start()\n            })\n        \n        # Reference definitions: [ref]: url\n        def_pattern = r'^\\s*\\[([^\\]]+)\\]:\\s*(.+)$'\n        for match in re.finditer(def_pattern, content, re.MULTILINE):\n            links.append({\n                'type': 'definition',\n                'ref': match.group(1),\n                'url': match.group(2).strip(),\n                'position': match.start()\n            })\n        \n        return links\n    \n    def _extract_images(self, content: str) -> list:\n        \"\"\"Extract images from markdown content\"\"\"\n        import re\n        \n        images = []\n        \n        # Inline images: ![alt](src)\n        inline_pattern = r'!\\[([^\\]]*)\\]\\(([^\\)]+)\\)'\n        for match in re.finditer(inline_pattern, content):\n            images.append({\n                'type': 'inline',\n                'alt': match.group(1),\n                'src': match.group(2),\n                'position': match.start()\n            })\n        \n        # Reference images: ![alt][ref]\n        ref_pattern = r'!\\[([^\\]]*)\\]\\[([^\\]]+)\\]'\n        for match in re.finditer(ref_pattern, content):\n            images.append({\n                'type': 'reference',\n                'alt': match.group(1),\n                'ref': match.group(2),\n                'position': match.start()\n            })\n        \n        return images\n    \n    def _create_preview_html(self, html_content: str, metadata: Dict[str, Any]) -> str:\n        \"\"\"Create complete HTML preview with styling\"\"\"\n        css_theme = self.get_setting('css_theme', 'github')\n        \n        html_template = f\"\"\"\n<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>{metadata.get('title', 'Markdown Preview')}</title>\n    <style>\n        {self._get_css_styles(css_theme)}\n    </style>\n</head>\n<body>\n    <div class=\"markdown-preview\">\n        <div class=\"metadata\">\n            <div class=\"stats\">\n                <span class=\"stat\">Words: {metadata.get('word_count', 0)}</span>\n                <span class=\"stat\">Lines: {metadata.get('line_count', 0)}</span>\n                <span class=\"stat\">Headings: {len(metadata.get('headings', []))}</span>\n            </div>\n        </div>\n        <div class=\"content\">\n            {html_content}\n        </div>\n    </div>\n</body>\n</html>\n        \"\"\"\n        \n        return html_template\n    \n    def _get_css_styles(self, theme: str) -> str:\n        \"\"\"Get CSS styles for the preview\"\"\"\n        # Basic GitHub-like styling\n        return \"\"\"\n        body {\n            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;\n            line-height: 1.6;\n            color: #24292e;\n            background-color: #ffffff;\n            margin: 0;\n            padding: 20px;\n        }\n        \n        .markdown-preview {\n            max-width: 800px;\n            margin: 0 auto;\n        }\n        \n        .metadata {\n            background-color: #f6f8fa;\n            border: 1px solid #e1e4e8;\n            border-radius: 6px;\n            padding: 10px;\n            margin-bottom: 20px;\n        }\n        \n        .stats {\n            display: flex;\n            gap: 15px;\n        }\n        \n        .stat {\n            font-size: 12px;\n            color: #586069;\n        }\n        \n        .content h1, .content h2, .content h3, .content h4, .content h5, .content h6 {\n            margin-top: 24px;\n            margin-bottom: 16px;\n            font-weight: 600;\n            line-height: 1.25;\n        }\n        \n        .content h1 {\n            font-size: 2em;\n            border-bottom: 1px solid #eaecef;\n            padding-bottom: 0.3em;\n        }\n        \n        .content h2 {\n            font-size: 1.5em;\n            border-bottom: 1px solid #eaecef;\n            padding-bottom: 0.3em;\n        }\n        \n        .content code {\n            background-color: rgba(27,31,35,0.05);\n            border-radius: 3px;\n            font-size: 85%;\n            margin: 0;\n            padding: 0.2em 0.4em;\n        }\n        \n        .content pre {\n            background-color: #f6f8fa;\n            border-radius: 6px;\n            font-size: 85%;\n            line-height: 1.45;\n            overflow: auto;\n            padding: 16px;\n        }\n        \n        .content blockquote {\n            border-left: 0.25em solid #dfe2e5;\n            color: #6a737d;\n            margin: 0;\n            padding: 0 1em;\n        }\n        \n        .content table {\n            border-collapse: collapse;\n            border-spacing: 0;\n            width: 100%;\n        }\n        \n        .content table th, .content table td {\n            border: 1px solid #dfe2e5;\n            padding: 6px 13px;\n        }\n        \n        .content table th {\n            background-color: #f6f8fa;\n            font-weight: 600;\n        }\n        \n        .highlight {\n            background-color: #f6f8fa;\n        }\n        \"\"\"\n    \n    def _generate_cache_key(self, file_path: Path, content: str) -> str:\n        \"\"\"Generate cache key for preview\"\"\"\n        content_hash = hashlib.md5(content.encode()).hexdigest()\n        file_stat = file_path.stat()\n        \n        cache_data = f\"{file_path}:{file_stat.st_mtime}:{content_hash}\"\n        return base64.b64encode(cache_data.encode()).decode()"