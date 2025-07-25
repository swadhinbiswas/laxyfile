"""
Code Preview Renderer

This module provides syntax highlighting and code analysis for various
programming languages using Pygments and custom analysis.
"""

import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass

from .preview_system import BasePreviewRenderer, PreviewResult, PreviewType, PreviewConfig
from ..utils.logger import Logger


@dataclass
class CodeStructure:
    """Represents code structure information"""
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    imports: List[str]
    comments: List[str]
    complexity_score: float
    line_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'functions': self.functions,
            'classes': self.classes,
            'imports': self.imports,
            'comments': self.comments,
            'complexity_score': self.complexity_score,
            'line_count': self.line_count
        }


class LanguageDetector:
    """Detect programming language from file content and extension"""

    def __init__(self):
        self.logger = Logger()

        # Language patterns for content-based detection
        self.language_patterns = {
            'python': [
                r'^\s*def\s+\w+\s*\(',
                r'^\s*class\s+\w+\s*[:\(]',
                r'^\s*import\s+\w+',
                r'^\s*from\s+\w+\s+import',
                r'if\s+__name__\s*==\s*["\']__main__["\']'
            ],
            'javascript': [
                r'function\s+\w+\s*\(',
                r'const\s+\w+\s*=',
                r'let\s+\w+\s*=',
                r'var\s+\w+\s*=',
                r'=>\s*{',
                r'require\s*\(',
                r'module\.exports'
            ],
            'java': [
                r'public\s+class\s+\w+',
                r'private\s+\w+\s+\w+',
                r'public\s+static\s+void\s+main',
                r'import\s+java\.',
                r'@Override',
                r'System\.out\.println'
            ],
            'cpp': [
#include\s*<\w+>',
                r'int\s+main\s*\(',
                r'std::\w+',
                r'using\s+namespace\s+std',
                r'cout\s*<<',
                r'cin\s*>>'
            ],
            'c': [
                r'#include\s*<\w+\.h>',
                r'int\s+main\s*\(',
                r'printf\s*\(',
                r'scanf\s*\(',
                r'malloc\s*\(',
                r'free\s*\('
            ],
            'go': [
                r'package\s+\w+',
                r'import\s+\(',
                r'func\s+\w+\s*\(',
                r'fmt\.Print',
                r'go\s+\w+\s*\(',
                r'chan\s+\w+'
            ],
            'rust': [
                r'fn\s+\w+\s*\(',
                r'let\s+mut\s+\w+',
                r'use\s+std::',
                r'impl\s+\w+',
                r'match\s+\w+',
                r'println!\s*\('
            ],
            'php': [
                r'<\?php',
                r'function\s+\w+\s*\(',
                r'\$\w+\s*=',
                r'echo\s+',
                r'require_once',
                r'class\s+\w+'
            ],
            'ruby': [
                r'def\s+\w+',
                r'class\s+\w+',
                r'require\s+["\']',
                r'puts\s+',
                r'@\w+\s*=',
                r'end\s*$'
            ],
            'shell': [
                r'#!/bin/bash',
                r'#!/bin/sh',
                r'if\s*\[\s*',
                r'for\s+\w+\s+in',
                r'while\s*\[\s*',
                r'echo\s+'
            ]
        }

        # Extension to language mapping
        self.extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.cc': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell',
            '.fish': 'shell',
            '.ps1': 'powershell',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.xml': 'xml',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'ini',
            '.conf': 'ini',
            '.sql': 'sql',
            '.r': 'r',
            '.R': 'r',
            '.m': 'matlab',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.clj': 'clojure',
            '.hs': 'haskell',
            '.ml': 'ocaml',
            '.fs': 'fsharp',
            '.cs': 'csharp',
            '.vb': 'vbnet',
            '.pl': 'perl',
            '.lua': 'lua',
            '.dart': 'dart',
            '.elm': 'elm'
        }

    def detect_language(self, file_path: Path, content: str) -> Optional[str]:
        """Detect programming language from file and content"""
        try:
            # First try extension-based detection
            extension = file_path.suffix.lower()
            if extension in self.extension_map:
                return self.extension_map[extension]

            # Try shebang detection
            lines = content.split('\n')
            if lines and lines[0].startswith('#!'):
                shebang = lines[0].lower()
                if 'python' in shebang:
                    return 'python'
                elif 'node' in shebang or 'javascript' in shebang:
                    return 'javascript'
                elif 'bash' in shebang or 'sh' in shebang:
                    return 'shell'
                elif 'ruby' in shebang:
                    return 'ruby'
                elif 'php' in shebang:
                    return 'php'

            # Content-based detection
            content_lower = content.lower()
            scores = {}

            for language, patterns in self.language_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, content, re.MULTILINE))
                    score += matches

                if score > 0:
                    scores[language] = score

            if scores:
                # Return language with highest score
                return max(scores, key=scores.get)

            return None

        except Exception as e:
            self.logger.error(f"Error detecting language: {e}")
            return None


class CodeAnalyzer:
    """Analyze code structure and extract information"""

    def __init__(self):
        self.logger = Logger()

    def analyze_code(self, content: str, language: str) -> CodeStructure:
        """Analyze code structure"""
        try:
            if language == 'python':
                return self._analyze_python(content)
            elif language in ['javascript', 'typescript']:
                return self._analyze_javascript(content)
            elif language == 'java':
                return self._analyze_java(content)
            elif language in ['cpp', 'c']:
                return self._analyze_c_cpp(content)
            else:
                return self._analyze_generic(content)

        except Exception as e:
            self.logger.error(f"Error analyzing {language} code: {e}")
            return self._analyze_generic(content)

    def _analyze_python(self, content: str) -> CodeStructure:
        """Analyze Python code"""
        lines = content.split('\n')
        functions = []
        classes = []
        imports = []
        comments = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Functions
            if stripped.startswith('def '):
                match = re.match(r'def\s+(\w+)\s*\((.*?)\):', stripped)
                if match:
                    functions.append({
                        'name': match.group(1),
                        'parameters': match.group(2),
                        'line': i + 1,
                        'docstring': self._extract_docstring(lines, i + 1)
                    })

            # Classes
            elif stripped.startswith('class '):
                match = re.match(r'class\s+(\w+)(?:\((.*?)\))?:', stripped)
                if match:
                    classes.append({
                        'name': match.group(1),
                        'inheritance': match.group(2) or '',
                        'line': i + 1,
                        'docstring': self._extract_docstring(lines, i + 1)
                    })

            # Imports
            elif stripped.startswith(('import ', 'from ')):
                imports.append(stripped)

            # Comments
            elif stripped.startswith('#'):
                comments.append(stripped[1:].strip())

        complexity_score = self._calculate_complexity(content)

        return CodeStructure(
            functions=functions,
            classes=classes,
            imports=imports,
            comments=comments,
            complexity_score=complexity_score,
            line_count=len(lines)
        )

    def _analyze_javascript(self, content: str) -> CodeStructure:
        """Analyze JavaScript/TypeScript code"""
        lines = content.split('\n')
        functions = []
        classes = []
        imports = []
        comments = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Functions
            function_patterns = [
                r'function\s+(\w+)\s*\((.*?)\)',
                r'const\s+(\w+)\s*=\s*\((.*?)\)\s*=>',
                r'let\s+(\w+)\s*=\s*\((.*?)\)\s*=>',
                r'var\s+(\w+)\s*=\s*function\s*\((.*?)\)'
            ]

            for pattern in function_patterns:
                match = re.search(pattern, stripped)
                if match:
                    functions.append({
                        'name': match.group(1),
                        'parameters': match.group(2),
                        'line': i + 1,
                        'type': 'function'
                    })
                    break

            # Classes
            if stripped.startswith('class '):
                match = re.match(r'class\s+(\w+)(?:\s+extends\s+(\w+))?', stripped)
                if match:
                    classes.append({
                        'name': match.group(1),
                        'inheritance': match.group(2) or '',
                        'line': i + 1
                    })

            # Imports
            elif stripped.startswith(('import ', 'const ', 'require(')):
                if 'import' in stripped or 'require' in stripped:
                    imports.append(stripped)

            # Comments
            elif stripped.startswith('//'):
                comments.append(stripped[2:].strip())

        complexity_score = self._calculate_complexity(content)

        return CodeStructure(
            functions=functions,
            classes=classes,
            imports=imports,
            comments=comments,
            complexity_score=complexity_score,
            line_count=len(lines)
        )

    def _analyze_java(self, content: str) -> CodeStructure:
        """Analyze Java code"""
        lines = content.split('\n')
        functions = []
        classes = []
        imports = []
        comments = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Methods
            method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\((.*?)\)'
            match = re.search(method_pattern, stripped)
            if match and not stripped.startswith('class'):
                functions.append({
                    'name': match.group(1),
                    'parameters': match.group(2),
                    'line': i + 1,
                    'type': 'method'
                })

            # Classes
            elif 'class ' in stripped:
                match = re.search(r'class\s+(\w+)(?:\s+extends\s+(\w+))?', stripped)
                if match:
                    classes.append({
                        'name': match.group(1),
                        'inheritance': match.group(2) or '',
                        'line': i + 1
                    })

            # Imports
            elif stripped.startswith('import '):
                imports.append(stripped)

            # Comments
            elif stripped.startswith('//'):
                comments.append(stripped[2:].strip())

        complexity_score = self._calculate_complexity(content)

        return CodeStructure(
            functions=functions,
            classes=classes,
            imports=imports,
            comments=comments,
            complexity_score=complexity_score,
            line_count=len(lines)
        )

    def _analyze_c_cpp(self, content: str) -> CodeStructure:
        """Analyze C/C++ code"""
        lines = content.split('\n')
        functions = []
        classes = []
        imports = []
        comments = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Functions
            if '(' in stripped and ')' in stripped and not stripped.startswith('#'):
                # Simple function detection
                match = re.search(r'\w+\s+(\w+)\s*\((.*?)\)', stripped)
                if match and not any(keyword in stripped for keyword in ['if', 'while', 'for', 'switch']):
                    functions.append({
                        'name': match.group(1),
                        'parameters': match.group(2),
                        'line': i + 1,
                        'type': 'function'
                    })

            # Classes (C++)
            elif stripped.startswith('class '):
                match = re.match(r'class\s+(\w+)', stripped)
                if match:
                    classes.append({
                        'name': match.group(1),
                        'line': i + 1
                    })

            # Includes
            elif stripped.startswith('#include'):
                imports.append(stripped)

            # Comments
            elif stripped.startswith('//'):
                comments.append(stripped[2:].strip())

        complexity_score = self._calculate_complexity(content)

        return CodeStructure(
            functions=functions,
            classes=classes,
            imports=imports,
            comments=comments,
            complexity_score=complexity_score,
            line_count=len(lines)
        )

    def _analyze_generic(self, content: str) -> CodeStructure:
        """Generic code analysis for unknown languages"""
        lines = content.split('\n')
        comments = []

        for line in lines:
            stripped = line.strip()
            # Common comment patterns
            if stripped.startswith(('#', '//', '--', '%', ';')):
                comments.append(stripped[1:].strip())

        complexity_score = self._calculate_complexity(content)

        return CodeStructure(
            functions=[],
            classes=[],
            imports=[],
            comments=comments,
            complexity_score=complexity_score,
            line_count=len(lines)
        )

    def _extract_docstring(self, lines: List[str], start_line: int) -> Optional[str]:
        """Extract docstring from Python code"""
        try:
            if start_line >= len(lines):
                return None

            line = lines[start_line].strip()
            if line.startswith('"""') or line.startswith("'''"):
                quote = line[:3]
                if line.endswith(quote) and len(line) > 6:
                    return line[3:-3].strip()

                # Multi-line docstring
                docstring_lines = [line[3:]]
                for i in range(start_line + 1, len(lines)):
                    line = lines[i].strip()
                    if line.endswith(quote):
                        docstring_lines.append(line[:-3])
                        break
                    docstring_lines.append(line)

                return '\n'.join(docstring_lines).strip()

            return None

        except Exception:
            return None

    def _calculate_complexity(self, content: str) -> float:
        """Calculate cyclomatic complexity (simplified)"""
        try:
            # Count decision points
            decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'case', 'catch', 'except']
            complexity = 1  # Base complexity

            for keyword in decision_keywords:
                complexity += len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE))

            # Normalize by lines of code
            lines = len([line for line in content.split('\n') if line.strip()])
            if lines > 0:
                return min(complexity / lines * 100, 100.0)  # Cap at 100

            return 0.0

        except Exception:
            return 0.0


class CodePreviewRenderer(BasePreviewRenderer):
    """Renderer for code files with syntax highlighting"""

    def __init__(self, config: PreviewConfig):
        super().__init__(config)
        self.language_detector = LanguageDetector()
        self.code_analyzer = CodeAnalyzer()

        # Try to import Pygments for syntax highlighting
        self.pygments_available = False
        try:
            import pygments
            from pygments import highlight
            from pygments.lexers import get_lexer_by_name, guess_lexer
            from pygments.formatters import TerminalFormatter, Terminal256Formatter
            from pygments.util import ClassNotFound

            self.pygments = pygments
            self.highlight = highlight
            self.get_lexer_by_name = get_lexer_by_name
            self.guess_lexer = guess_lexer
            self.TerminalFormatter = TerminalFormatter
            self.Terminal256Formatter = Terminal256Formatter
            self.ClassNotFound = ClassNotFound
            self.pygments_available = True

        except ImportError:
            self.logger.warning("Pygments not available, syntax highlighting disabled")

    def can_preview(self, file_path: Path) -> bool:
        """Check if file is a code file"""
        # Check by extension
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.cxx', '.cc', '.c', '.h', '.hpp',
            '.go', '.rs', '.php', '.rb', '.sh', '.bash', '.zsh', '.fish', '.ps1', '.html', '.htm',
            '.css', '.scss', '.sass', '.less', '.xml', '.json', '.yaml', '.yml', '.toml', '.ini',
            '.cfg', '.conf', '.sql', '.r', '.R', '.m', '.swift', '.kt', '.scala', '.clj', '.hs',
            '.ml', '.fs', '.cs', '.vb', '.pl', '.lua', '.dart', '.elm'
        }

        if file_path.suffix.lower() in code_extensions:
            return True

        # Check by content (for files without extensions)
        try:
            if self._is_file_too_large(file_path):
                return False

            content = file_path.read_text(encoding='utf-8', errors='ignore')[:1000]  # Sample first 1KB
            language = self.language_detector.detect_language(file_path, content)
            return language is not None

        except Exception:
            return False

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return list(self.language_detector.extension_map.keys())

    def get_preview_type(self, file_path: Path) -> PreviewType:
        """Get preview type for file"""
        return PreviewType.CODE

    async def generate_preview(self, file_path: Path) -> PreviewResult:
        """Generate code preview with syntax highlighting"""
        start_time = time.time()

        try:
            if self._is_file_too_large(file_path):
                return self._create_error_result(file_path, "File too large for preview")

            # Read file content
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except UnicodeDecodeError:
                # Try other encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        content = file_path.read_text(encoding=encoding, errors='ignore')
                        break
                    except:
                        continue
                else:
                    return self._create_error_result(file_path, "Could not decode file")

            # Detect language
            language = self.language_detector.detect_language(file_path, content)

            # Truncate if too long
            lines = content.split('\n')
            original_line_count = len(lines)

            if len(lines) > self.config.max_lines:
                lines = lines[:self.config.max_lines]
                lines.append(f"... (truncated, showing first {self.config.max_lines} of {original_line_count} lines)")
                content = '\n'.join(lines)

            if len(content) > self.config.max_text_length:
                content = content[:self.config.max_text_length] + "\n... (truncated)"

            # Apply syntax highlighting if enabled and available
            highlighted_content = content
            if self.config.enable_syntax_highlighting and self.pygments_available and language:
                highlighted_content = self._apply_syntax_highlighting(content, language)

            # Analyze code structure
            code_structure = None
            if language:
                code_structure = self.code_analyzer.analyze_code(content, language)

            # Extract metadata
            metadata = {
                'language': language,
                'detected_language': language,
                'line_count': original_line_count,
                'character_count': len(content),
                'file_size': file_path.stat().st_size,
                'syntax_highlighted': self.config.enable_syntax_highlighting and self.pygments_available,
                'encoding': 'utf-8'
            }

            if code_structure:
                metadata['code_structure'] = code_structure.to_dict()
                metadata['function_count'] = len(code_structure.functions)
                metadata['class_count'] = len(code_structure.classes)
                metadata['import_count'] = len(code_structure.imports)
                metadata['complexity_score'] = code_structure.complexity_score

            return PreviewResult(
                file_path=file_path,
                preview_type=PreviewType.CODE,
                content=highlighted_content,
                metadata=metadata,
                generation_time=time.time() - start_time
            )

        except Exception as e:
            self.logger.error(f"Error generating code preview for {file_path}: {e}")
            return self._create_error_result(file_path, str(e))

    def _apply_syntax_highlighting(self, content: str, language: str) -> str:
        """Apply syntax highlighting using Pygments"""
        try:
            # Map our language names to Pygments lexer names
            lexer_map = {
                'javascript': 'javascript',
                'typescript': 'typescript',
                'python': 'python',
                'java': 'java',
                'cpp': 'cpp',
                'c': 'c',
                'go': 'go',
                'rust': 'rust',
                'php': 'php',
                'ruby': 'ruby',
                'shell': 'bash',
                'html': 'html',
                'css': 'css',
                'json': 'json',
                'yaml': 'yaml',
                'xml': 'xml',
                'sql': 'sql'
            }

            lexer_name = lexer_map.get(language, language)

            try:
                lexer = self.get_lexer_by_name(lexer_name)
            except self.ClassNotFound:
                # Try to guess lexer from content
                try:
                    lexer = self.guess_lexer(content)
                except:
                    return content  # Return unhighlighted content

            # Use terminal formatter for colored output
            if self.config.quality == PreviewQuality.HIGH:
                formatter = self.Terminal256Formatter(style='monokai')
            else:
                formatter = self.TerminalFormatter()

            highlighted = self.highlight(content, lexer, formatter)
            return highlighted.rstrip()  # Remove trailing newline

        except Exception as e:
            self.logger.error(f"Error applying syntax highlighting: {e}")
            return content  # Return unhighlighted content on error