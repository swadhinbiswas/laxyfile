# LaxyFile Configuration Guide

This comprehensive guide covers all aspects of configuring LaxyFile to match your workflow and preferences.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Basic Settings](#basic-settings)
3. [Theme Configuration](#theme-configuration)
4. [AI Assistant Setup](#ai-assistant-setup)
5. [Keyboard Shortcuts](#keyboard-shortcuts)
6. [Performance Tuning](#performance-tuning)
7. [Plugin Configuration](#plugin-configuration)
8. [Advanced Settings](#advanced-settings)
9. [Import/Export Settings](#importexport-settings)

## Configuration Overview

LaxyFile stores configuration in platform-specific locations:

- **Linux**: `~/.config/laxyfile/`
- **macOS**: `~/Library/Application Support/LaxyFile/`
- **Windows**: `%APPDATA%\LaxyFile\`

### Configuration Files Structure

```
~/.config/laxyfile/
├── config.yaml          # Main configuration
├── themes/              # Custom themes
│   ├── my-theme.json
│   └── work-theme.json
├── plugins/             # Plugin configurations
│   ├── git-integration.yaml
│   └── image-tools.yaml
├── shortcuts.yaml       # Keyboard shortcuts
├── ai-cache/           # AI response cache
├── logs/               # Application logs
└── backups/            # Configuration backups
```

### Configuration Hierarchy

LaxyFile loads configuration in this order (later overrides earlier):

1. **Default settings** (built into application)
2. **System-wide config** (`/etc/laxyfile/config.yaml`)
3. **User config** (`~/.config/laxyfile/config.yaml`)
4. **Environment variables** (`LAXYFILE_*`)
5. **Command-line arguments** (`--config-option=value`)

## Basic Settings

### Main Configuration File

The main configuration file (`config.yaml`) uses YAML format:

```yaml
# ~/.config/laxyfile/config.yaml

# Application settings
app:
  version: "2.0.0"
  first_run: false
  check_updates: true
  telemetry: false

# User interface settings
ui:
  theme: "catppuccin"
  font_family: "SF Pro Display"
  font_size: 12
  show_hidden_files: false
  show_file_extensions: true
  dual_pane_mode: false
  sidebar_width: 200
  preview_panel: true
  status_bar: true
  toolbar: true
  animations: true
  animation_speed: "normal" # slow, normal, fast
  icon_size: "medium" # small, medium, large
  file_list_style: "detailed" # compact, detailed, grid

# File operations
file_operations:
  confirm_delete: true
  confirm_overwrite: true
  use_trash: true
  show_progress: true
  verify_copies: true
  default_permissions: "644"
  preserve_timestamps: true
  follow_symlinks: false

# Search settings
search:
  case_sensitive: false
  use_regex: false
  search_content: true
  max_results: 1000
  index_hidden_files: false
  exclude_patterns:
    - "*.tmp"
    - "*.log"
    - ".git/*"
    - "node_modules/*"

# Network settings
network:
  timeout: 30
  retry_attempts: 3
  proxy_url: ""
  user_agent: "LaxyFile/2.0"
```

### Environment Variables

Override settings with environment variables:

```bash
# Theme selection
export LAXYFILE_THEME="dracula"

# AI provider
export LAXYFILE_AI_PROVIDER="openrouter"
export LAXYFILE_AI_API_KEY="your-api-key"

# Performance settings
export LAXYFILE_CACHE_SIZE="2000"
export LAXYFILE_MAX_WORKERS="8"

# Debug settings
export LAXYFILE_DEBUG="true"
export LAXYFILE_LOG_LEVEL="DEBUG"
```

### Command-Line Configuration

Override settings via command-line arguments:

```bash
# Start with specific theme
laxyfile --theme=nord

# Disable AI features
laxyfile --no-ai

# Custom config file
laxyfile --config=/path/to/custom/config.yaml

# Debug mode
laxyfile --debug --log-level=DEBUG

# Safe mode (minimal features)
laxyfile --safe-mode
```

## Theme Configuration

### Built-in Themes

LaxyFile includes several SuperFile-inspired themes:

```yaml
ui:
  theme: "catppuccin" # Options:
  # - catppuccin      # Soothing pastels
  # - dracula         # Dark with purple accents
  # - nord            # Arctic blues
  # - gruvbox         # Retro warm colors
  # - tokyo-night     # Neon darkness
  # - one-dark        # Atom-inspired
  # - solarized-dark  # High contrast dark
  # - solarized-light # High contrast light
```

### Custom Theme Creation

Create custom themes in `~/.config/laxyfile/themes/`:

```json
{
  "name": "My Custom Theme",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "A custom theme for LaxyFile",

  "colors": {
    "background": "#1e1e2e",
    "foreground": "#cdd6f4",
    "accent": "#89b4fa",
    "selection": "#313244",
    "border": "#45475a",
    "error": "#f38ba8",
    "warning": "#f9e2af",
    "success": "#a6e3a1",
    "info": "#74c7ec",

    "file_panel": {
      "background": "#1e1e2e",
      "text": "#cdd6f4",
      "selected_bg": "#313244",
      "selected_text": "#cdd6f4",
      "header_bg": "#181825",
      "header_text": "#bac2de"
    },

    "sidebar": {
      "background": "#181825",
      "text": "#bac2de",
      "selected_bg": "#313244",
      "selected_text": "#cdd6f4"
    },

    "status_bar": {
      "background": "#181825",
      "text": "#bac2de"
    },

    "preview_panel": {
      "background": "#1e1e2e",
      "text": "#cdd6f4",
      "border": "#45475a"
    }
  },

  "fonts": {
    "ui": {
      "family": "SF Pro Display",
      "size": 12,
      "weight": "normal"
    },
    "monospace": {
      "family": "JetBrains Mono",
      "size": 11,
      "weight": "normal"
    }
  },

  "icons": {
    "style": "nerd-fonts",  # nerd-fonts, unicode, ascii
    "color_coding": true,
    "custom_mappings": {
      ".py": "🐍",
      ".js": "📜",
      ".md": "📝"
    }
  },

  "animations": {
    "enabled": true,
    "duration": 200,
    "easing": "ease-in-out"
  }
}
```

### Theme Inheritance

Create themes that inherit from existing ones:

```json
{
  "name": "Dark Catppuccin Variant",
  "inherits": "catppuccin",
  "colors": {
    "background": "#11111b",
    "file_panel": {
      "background": "#11111b"
    }
  }
}
```

### Dynamic Theme Switching

Configure automatic theme switching:

```yaml
ui:
  theme: "auto" # Automatically switch based on system
  theme_schedule:
    enabled: true
    light_theme: "solarized-light"
    dark_theme: "catppuccin"
    switch_time:
      to_light: "07:00"
      to_dark: "19:00"

  # Or use system theme detection
  follow_system_theme: true
```

## AI Assistant Setup

### Provider Configuration

Configure your preferred AI provider:

```yaml
ai:
  enabled: true
  provider: "openrouter" # openrouter, ollama, gpt4all, custom

  # OpenRouter configuration
  openrouter:
    api_key: "your-api-key-here"
    base_url: "https://openrouter.ai/api/v1"
    model: "anthropic/claude-3-haiku"
    max_tokens: 4000
    temperature: 0.1
    timeout: 30

  # Ollama configuration (local)
  ollama:
    base_url: "http://localhost:11434"
    model: "llama2"
    timeout: 60

  # GPT4All configuration (local)
  gpt4all:
    model_path: "~/.cache/gpt4all/orca-mini-3b.q4_0.bin"
    n_threads: 4

  # Custom provider
  custom:
    api_key: "your-key"
    base_url: "https://your-api.com/v1"
    model: "your-model"
    headers:
      "Custom-Header": "value"
```

### AI Feature Configuration

Control which AI features are enabled:

```yaml
ai:
  features:
    file_analysis: true
    content_search: true
    organization_suggestions: true
    security_analysis: true
    duplicate_detection: true
    smart_rename: true
    workflow_automation: true

  # Performance settings
  performance:
    cache_responses: true
    cache_ttl: 3600 # 1 hour
    max_concurrent_requests: 5
    background_processing: true

  # Privacy settings
  privacy:
    send_file_content: true
    send_metadata_only: false
    local_processing_preferred: false
    data_retention_days: 30
```

### AI Model Selection

Choose models based on your needs:

```yaml
ai:
  models:
    # Fast, cost-effective for basic tasks
    quick_analysis: "anthropic/claude-3-haiku"

    # Balanced performance and capability
    general_purpose: "anthropic/claude-3-sonnet"

    # Most capable for complex tasks
    advanced_analysis: "anthropic/claude-3-opus"

    # Local models for privacy
    local_fallback: "ollama/llama2"

  # Auto-select model based on task complexity
  auto_model_selection: true

  # Fallback chain if primary model fails
  fallback_models:
    - "anthropic/claude-3-haiku"
    - "ollama/llama2"
```

## Keyboard Shortcuts

### Default Shortcut Schemes

LaxyFile supports multiple shortcut schemes:

```yaml
shortcuts:
  scheme: "default" # Options:
  # - default      # Standard file manager shortcuts
  # - vim          # Vim-like navigation
  # - superfile    # SuperFile-compatible
  # - custom       # User-defined shortcuts
```

### Custom Shortcut Configuration

Define custom shortcuts in `shortcuts.yaml`:

```yaml
# ~/.config/laxyfile/shortcuts.yaml

# Navigation shortcuts
navigation:
  go_up: "Ctrl+Up"
  go_home: "Ctrl+H"
  go_root: "Ctrl+R"
  go_back: "Alt+Left"
  go_forward: "Alt+Right"
  go_to_path: "Ctrl+L"

# File operations
file_operations:
  copy: "Ctrl+C"
  cut: "Ctrl+X"
  paste: "Ctrl+V"
  delete: "Delete"
  rename: "F2"
  properties: "Alt+Enter"
  new_folder: "Ctrl+Shift+N"
  new_file: "Ctrl+N"

# Selection
selection:
  select_all: "Ctrl+A"
  deselect_all: "Ctrl+D"
  invert_selection: "Ctrl+I"
  select_by_pattern: "Ctrl+Shift+S"

# View options
view:
  refresh: "F5"
  toggle_preview: "F3"
  toggle_sidebar: "F9"
  toggle_dual_pane: "F6"
  list_view: "Ctrl+1"
  icon_view: "Ctrl+2"
  tree_view: "Ctrl+3"

# Search
search:
  quick_search: "Ctrl+F"
  advanced_search: "Ctrl+Shift+F"
  ai_search: "Ctrl+Alt+F"

# AI assistant
ai:
  open_chat: "F1"
  quick_query: "Ctrl+Shift+A"
  analyze_file: "Ctrl+I"
  organize_files: "Ctrl+O"

# Application
application:
  settings: "Ctrl+,"
  help: "F1"
  exit: "Ctrl+Q"

# Custom shortcuts
custom:
  my_workflow: "Ctrl+Shift+W"
  favorite_folder: "Ctrl+Shift+F"
```

### Shortcut Conflicts

LaxyFile automatically detects and resolves shortcut conflicts:

```yaml
shortcuts:
  conflict_resolution: "warn" # Options:
  # - ignore    # Allow conflicts
  # - warn      # Show warning but allow
  # - prevent   # Prevent conflicting shortcuts
  # - auto      # Automatically resolve conflicts

  # Show shortcut hints in UI
  show_hints: true
  hint_delay: 1000 # milliseconds
```

### Context-Sensitive Shortcuts

Define shortcuts that work only in specific contexts:

```yaml
shortcuts:
  contexts:
    file_panel:
      space: "select_toggle"
      enter: "open_file"
      backspace: "go_up"

    preview_panel:
      space: "scroll_down"
      shift_space: "scroll_up"

    search_mode:
      escape: "exit_search"
      enter: "search_execute"

    ai_chat:
      ctrl_enter: "send_message"
      escape: "close_chat"
```

## Performance Tuning

### General Performance Settings

```yaml
performance:
  # Cache settings
  cache_size: 1000 # Number of items to cache
  cache_ttl: 3600 # Cache time-to-live (seconds)
  memory_limit_mb: 500 # Maximum memory usage

  # File operations
  max_concurrent_operations: 8 # Parallel file operations
  chunk_size_kb: 64 # File copy chunk size
  use_sendfile: true # Use system sendfile() if available

  # UI performance
  lazy_loading: true # Load files as needed
  virtual_scrolling: true # Efficient large list handling
  max_files_display: 1000 # Limit initial file display

  # Background processing
  background_processing: true # Non-blocking operations
  worker_threads: 4 # Background worker threads

  # Network optimization
  network_timeout: 30 # Network operation timeout
  connection_pooling: true # Reuse network connections

  # AI performance
  ai_cache_size: 2000 # AI response cache size
  ai_background_analysis: true # Analyze files in background
```

### Memory Management

```yaml
performance:
  memory:
    # Garbage collection
    gc_enabled: true
    gc_threshold: 100 # MB before triggering GC
    gc_interval: 300 # Seconds between GC runs

    # Cache management
    cache_cleanup_interval: 600 # Seconds between cache cleanup
    max_cache_age: 3600 # Maximum cache entry age

    # Memory monitoring
    memory_monitoring: true
    memory_warning_threshold: 80 # Percent of limit
    memory_critical_threshold: 95 # Percent of limit
```

### Disk I/O Optimization

```yaml
performance:
  disk_io:
    # Read optimization
    read_ahead_kb: 128 # Read-ahead buffer size
    use_mmap: true # Memory-mapped file access

    # Write optimization
    write_buffer_kb: 64 # Write buffer size
    sync_writes: false # Synchronous writes

    # Directory scanning
    scan_batch_size: 100 # Files per batch
    scan_delay_ms: 10 # Delay between batches

    # File watching
    watch_enabled: true # Monitor file changes
    watch_recursive: true # Watch subdirectories
    watch_debounce_ms: 100 # Debounce file events
```

### Platform-Specific Optimizations

```yaml
performance:
  platform:
    # Windows-specific
    windows:
      use_long_paths: true # Support paths > 260 chars
      file_attributes_cache: true

    # macOS-specific
    macos:
      use_spotlight: true # Use Spotlight for search
      fsevents_latency: 0.1 # File system event latency

    # Linux-specific
    linux:
      use_inotify: true # Use inotify for file watching
      sendfile_threshold: 64 # KB threshold for sendfile
```

## Plugin Configuration

### Plugin Management

```yaml
plugins:
  enabled: true
  auto_update: false
  update_check_interval: 86400 # 24 hours

  # Plugin directories
  directories:
    - "~/.config/laxyfile/plugins"
    - "/usr/share/laxyfile/plugins"

  # Security settings
  security:
    allow_unsigned: false
    verify_checksums: true
    sandbox_plugins: true
```

### Individual Plugin Configuration

Configure specific plugins:

```yaml
# ~/.config/laxyfile/plugins/git-integration.yaml
git_integration:
  enabled: true
  show_status_icons: true
  auto_fetch: false
  fetch_interval: 300 # seconds

  # Git commands
  commands:
    status: "git status --porcelain"
    add: "git add"
    commit: "git commit -m"

  # UI integration
  ui:
    show_branch: true
    show_dirty_indicator: true
    status_colors:
      modified: "#f9e2af"
      added: "#a6e3a1"
      deleted: "#f38ba8"
      untracked: "#74c7ec"
```

```yaml
# ~/.config/laxyfile/plugins/image-tools.yaml
image_tools:
  enabled: true

  # Thumbnail generation
  thumbnails:
    enabled: true
    size: 128
    quality: 85
    cache_dir: "~/.cache/laxyfile/thumbnails"

  # Image formats
  supported_formats:
    - "jpg"
    - "jpeg"
    - "png"
    - "gif"
    - "webp"
    - "bmp"
    - "tiff"

  # External tools
  tools:
    image_viewer: "feh"
    image_editor: "gimp"
    batch_converter: "imagemagick"
```

## Advanced Settings

### Logging Configuration

```yaml
logging:
  enabled: true
  level: "INFO" # DEBUG, INFO, WARNING, ERROR, CRITICAL

  # Log files
  files:
    main: "~/.config/laxyfile/logs/laxyfile.log"
    ai: "~/.config/laxyfile/logs/ai.log"
    performance: "~/.config/laxyfile/logs/performance.log"

  # Log rotation
  rotation:
    max_size_mb: 10
    backup_count: 5

  # Log format
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  date_format: "%Y-%m-%d %H:%M:%S"

  # Console logging
  console:
    enabled: false
    level: "WARNING"
```

### Security Settings

```yaml
security:
  # File access
  file_access:
    restrict_to_home: false
    allow_system_files: true
    follow_symlinks: false

  # Network security
  network:
    verify_ssl: true
    allow_insecure_connections: false
    trusted_hosts:
      - "api.openrouter.ai"
      - "localhost"

  # AI security
  ai:
    sanitize_inputs: true
    filter_sensitive_data: true
    log_ai_requests: false

  # Plugin security
  plugins:
    verify_signatures: true
    sandbox_enabled: true
    allowed_permissions:
      - "file_read"
      - "file_write"
      - "network_access"
```

### Experimental Features

```yaml
experimental:
  # Enable experimental features
  enabled: false

  # Feature flags
  features:
    new_ui_engine: false
    advanced_ai_models: false
    cloud_sync: false
    collaborative_editing: false

  # Beta testing
  beta_testing:
    enabled: false
    feedback_url: "https://feedback.laxyfile.com"
    crash_reporting: false
```

## Import/Export Settings

### Exporting Configuration

Export your settings for backup or sharing:

```bash
# Export all settings
laxyfile --export-config=my-config.yaml

# Export specific sections
laxyfile --export-config=themes.yaml --section=ui.themes
laxyfile --export-config=shortcuts.yaml --section=shortcuts

# Export with encryption
laxyfile --export-config=secure-config.yaml --encrypt
```

### Importing Configuration

Import settings from backup or another user:

```bash
# Import all settings
laxyfile --import-config=my-config.yaml

# Import specific sections
laxyfile --import-config=themes.yaml --section=ui.themes

# Import with merge (don't overwrite existing)
laxyfile --import-config=config.yaml --merge

# Import from other file managers
laxyfile --import-from=ranger --config-path=~/.config/ranger/rc.conf
```

### Migration Between Versions

LaxyFile automatically migrates configuration between versions:

```yaml
migration:
  auto_migrate: true
  backup_before_migration: true
  backup_directory: "~/.config/laxyfile/backups"

  # Version-specific migrations
  migrations:
    "1.0_to_2.0":
      - "rename_theme_files"
      - "update_shortcut_format"
      - "migrate_ai_settings"
```

### Configuration Validation

Validate your configuration files:

```bash
# Validate main config
laxyfile --validate-config

# Validate specific file
laxyfile --validate-config=~/.config/laxyfile/themes/my-theme.json

# Check for common issues
laxyfile --config-doctor
```

## Configuration Examples

### Minimal Configuration

```yaml
# Minimal config for basic usage
ui:
  theme: "catppuccin"
  show_hidden_files: false

ai:
  enabled: false

performance:
  cache_size: 500
```

### Power User Configuration

```yaml
# Advanced configuration for power users
ui:
  theme: "tokyo-night"
  dual_pane_mode: true
  animations: true
  font_family: "JetBrains Mono"

ai:
  enabled: true
  provider: "openrouter"
  openrouter:
    model: "anthropic/claude-3-opus"
  features:
    file_analysis: true
    organization_suggestions: true
    security_analysis: true

performance:
  cache_size: 2000
  max_concurrent_operations: 16
  background_processing: true
  lazy_loading: true

shortcuts:
  scheme: "vim"

plugins:
  enabled: true
  directories:
    - "~/.config/laxyfile/plugins"
    - "~/dev/laxyfile-plugins"
```

### Development Configuration

```yaml
# Configuration for LaxyFile development
app:
  debug: true
  telemetry: false

logging:
  enabled: true
  level: "DEBUG"
  console:
    enabled: true
    level: "DEBUG"

experimental:
  enabled: true
  features:
    new_ui_engine: true
    advanced_ai_models: true

performance:
  memory_monitoring: true

security:
  plugins:
    sandbox_enabled: false # For plugin development
```

## Troubleshooting Configuration

### Common Configuration Issues

1. **Invalid YAML Syntax**:

   ```bash
   # Validate YAML syntax
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

2. **Permission Issues**:

   ```bash
   # Fix config directory permissions
   chmod 755 ~/.config/laxyfile
   chmod 644 ~/.config/laxyfile/config.yaml
   ```

3. **Missing Dependencies**:
   ```bash
   # Check for missing dependencies
   laxyfile --check-deps
   ```

### Configuration Reset

Reset configuration to defaults:

```bash
# Reset all settings
laxyfile --reset-config

# Reset specific sections
laxyfile --reset-config --section=ui
laxyfile --reset-config --section=shortcuts

# Interactive reset
laxyfile --reset-config --interactive
```

### Configuration Backup

Automatic configuration backup:

```yaml
backup:
  enabled: true
  interval: 86400 # 24 hours
  max_backups: 10
  backup_directory: "~/.config/laxyfile/backups"

  # What to backup
  include:
    - "config.yaml"
    - "shortcuts.yaml"
    - "themes/"
    - "plugins/"
```

---

This configuration guide covers all aspects of customizing LaxyFile. For specific use cases or advanced configurations, consult the [API documentation](api-reference.md) or ask in our [community forum](https://community.laxyfile.com).
