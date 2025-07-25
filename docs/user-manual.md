# LaxyFile User Manual

Welcome to LaxyFile - the next-generation file manager that combines the power of SuperFile with advanced AI capabilities, modern UI design, and comprehensive file management features.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Interface Overview](#interface-overview)
3. [Basic File Operations](#basic-file-operations)
4. [Advanced Features](#advanced-features)
5. [AI Assistant](#ai-assistant)
6. [Customization](#customization)
7. [Keyboard Shortcuts](#keyboard-shortcuts)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

#### Quick Install (Recommended)

```bash
# Install from PyPI
pip install laxyfile

# Or install from source
git clone https://github.com/your-repo/laxyfile.git
cd laxyfile
pip install -e .
```

#### Platform-Specific Installation

**Windows:**

- Download the MSI installer from the releases page
- Run the installer and follow the setup wizard
- LaxyFile will be available in your Start Menu

**macOS:**

```bash
# Using Homebrew
brew install laxyfile

# Or download the .app bundle from releases
```

**Linux:**

```bash
# Ubuntu/Debian
sudo apt install laxyfile

# Arch Linux
yay -S laxyfile

# Or use the AppImage
chmod +x LaxyFile-x86_64.AppImage
./LaxyFile-x86_64.AppImage
```

### First Launch

When you first launch LaxyFile, you'll be greeted with:

1. **Welcome Screen**: Introduction to key features
2. **Configuration Wizard**: Set up your preferences
3. **AI Setup**: Configure AI assistant (optional)
4. **Theme Selection**: Choose your preferred theme

### System Requirements

- **Minimum**: Python 3.8+, 2GB RAM, 100MB disk space
- **Recommended**: Python 3.11+, 4GB RAM, 500MB disk space
- **For AI Features**: Internet connection, OpenRouter API key (optional)

## Interface Overview

LaxyFile features a modern, SuperFile-inspired interface with several key components:

### Main Layout

```
┌─────────────────────────────────────────────────────────────┐
│                    LaxyFile v2.0                            │
├─────────────┬───────────────────────────────────────────────┤
│   Sidebar   │              File Panel                       │
│             │                                               │
│ • Bookmarks │  📁 Documents/                               │
│ • Recent    │  📄 file1.txt        1.2KB   2024-01-15     │
│ • Drives    │  📁 Projects/        --       2024-01-14     │
│ • Tree      │  🖼️ image.jpg        2.5MB   2024-01-13     │
│             │  📊 data.csv         856B    2024-01-12     │
│             │                                               │
├─────────────┼───────────────────────────────────────────────┤
│   Preview   │              Status Bar                       │
│   Panel     │  📁 5 items • 3.7MB • AI: Ready             │
└─────────────┴───────────────────────────────────────────────┘
```

### Key Components

#### 1. Sidebar

- **Bookmarks**: Quick access to favorite locations
- **Recent**: Recently visited directories
- **Drives**: Available storage devices
- **Directory Tree**: Hierarchical folder navigation

#### 2. File Panel

- **File List**: Main file and folder display
- **Icons**: File type indicators with Nerd Font support
- **Metadata**: Size, date, permissions
- **Selection**: Multi-select with visual feedback

#### 3. Preview Panel

- **File Preview**: Content preview for selected files
- **Metadata**: Detailed file information
- **AI Insights**: Smart analysis and suggestions

#### 4. Status Bar

- **Current Path**: Active directory location
- **Selection Info**: Selected items count and size
- **AI Status**: Assistant availability and activity
- **System Info**: Performance and resource usage

### Navigation Modes

LaxyFile supports multiple navigation modes:

#### Classic Mode (Default)

- Traditional file manager layout
- Keyboard and mouse navigation
- Context menus and toolbars

#### SuperFile Mode

- SuperFile-inspired interface
- Vim-like keyboard shortcuts
- Minimal, efficient design

#### Dual-Pane Mode

- Side-by-side file panels
- Easy file comparison and transfer
- Independent navigation

## Basic File Operations

### File Selection

#### Single Selection

- **Click**: Select a single file
- **Arrow Keys**: Navigate and select
- **Enter**: Open file or enter directory

#### Multiple Selection

- **Ctrl+Click**: Add/remove from selection
- **Shift+Click**: Select range
- **Ctrl+A**: Select all files
- **Ctrl+D**: Deselect all

#### Selection Patterns

```bash
# Select by pattern
*.txt          # All text files
image.*        # All image files
[Dd]ocument*   # Files starting with Document or document
```

### File Operations

#### Copy and Move

```
Copy:   Ctrl+C → Navigate → Ctrl+V
Move:   Ctrl+X → Navigate → Ctrl+V
```

**Advanced Copy Options:**

- **Smart Copy**: Automatically handles conflicts
- **Progress Tracking**: Real-time operation status
- **Pause/Resume**: Control long operations
- **Verification**: Ensure data integrity

#### Delete Operations

```
Delete:         Delete key or Ctrl+D
Secure Delete:  Shift+Delete
Move to Trash:  Ctrl+Delete (platform-specific)
```

**Delete Options:**

- **Confirmation**: Prevent accidental deletion
- **Undo Support**: Recover deleted files
- **Secure Wipe**: Permanent data removal

#### Archive Operations

**Create Archives:**

1. Select files/folders
2. Right-click → "Create Archive"
3. Choose format: ZIP, TAR, 7Z, RAR
4. Set compression level and options

**Extract Archives:**

1. Select archive file
2. Right-click → "Extract"
3. Choose destination
4. Handle conflicts automatically

**Supported Formats:**

- **ZIP**: Universal compatibility
- **TAR/GZ**: Linux standard
- **7Z**: High compression
- **RAR**: Read-only support

### Search and Filtering

#### Quick Search

```
Ctrl+F: Open search bar
Type query and press Enter
```

#### Advanced Search

```
Name:     filename contains "document"
Content:  file content contains "important"
Size:     size > 1MB and size < 10MB
Date:     modified in last 7 days
Type:     type is image or video
```

#### Search Operators

```
AND:      document AND important
OR:       .txt OR .md
NOT:      NOT .tmp
REGEX:    /^[A-Z].*\.pdf$/
```

#### Filtering

- **File Type**: Show only specific types
- **Size Range**: Filter by file size
- **Date Range**: Filter by modification date
- **Attributes**: Hidden, read-only, executable

## Advanced Features

### Batch Operations

#### Rename Multiple Files

1. Select files to rename
2. Press F2 or right-click → "Batch Rename"
3. Choose rename pattern:

   ```
   Pattern:     Document_{counter:03d}
   Result:      Document_001.txt, Document_002.txt

   Pattern:     {name}_backup
   Result:      file1_backup.txt, file2_backup.txt
   ```

#### Batch File Operations

- **Change Permissions**: Apply to multiple files
- **Change Timestamps**: Modify creation/modification dates
- **Add Metadata**: Bulk metadata editing
- **Convert Formats**: Batch file conversion

### File Monitoring

LaxyFile automatically monitors directories for changes:

- **Real-time Updates**: File list updates automatically
- **Change Notifications**: Visual indicators for changes
- **Conflict Detection**: Handle external modifications
- **Sync Status**: Track synchronization with cloud services

### Advanced Navigation

#### Breadcrumb Navigation

```
Home > Documents > Projects > LaxyFile > docs
```

- Click any segment to navigate
- Right-click for context menu
- Drag files to breadcrumb locations

#### Quick Navigation

```
Ctrl+L:     Go to location (type path)
Ctrl+H:     Go to home directory
Ctrl+R:     Go to root directory
Alt+Left:   Navigate back
Alt+Right:  Navigate forward
```

#### Bookmarks and Favorites

```
Ctrl+B:     Add current location to bookmarks
Ctrl+1-9:   Quick access to bookmarks 1-9
```

### File Comparison

#### Visual Diff

- Compare text files side-by-side
- Highlight differences
- Merge changes interactively

#### Binary Comparison

- Compare binary files
- Show hexadecimal differences
- Detect file corruption

### Network and Cloud Integration

#### Remote File Systems

- **FTP/SFTP**: Connect to remote servers
- **SMB/CIFS**: Windows network shares
- **WebDAV**: Web-based file access

#### Cloud Storage

- **Google Drive**: Direct integration
- **Dropbox**: Sync status and management
- **OneDrive**: Microsoft cloud integration
- **Custom**: Configure additional providers

## AI Assistant

LaxyFile's AI assistant provides intelligent file management capabilities:

### Getting Started with AI

#### Setup

1. Go to Settings → AI Assistant
2. Choose AI provider:

   - **OpenRouter**: Cloud-based (recommended)
   - **Local Models**: Ollama, GPT4All
   - **Custom**: Your own API endpoint

3. Configure API key (if using cloud service)
4. Test connection and select model

#### AI Providers Comparison

| Provider   | Pros                        | Cons                     | Best For        |
| ---------- | --------------------------- | ------------------------ | --------------- |
| OpenRouter | Fast, accurate, many models | Requires internet, costs | General use     |
| Ollama     | Private, free, offline      | Slower, requires setup   | Privacy-focused |
| GPT4All    | Easy setup, free            | Limited capabilities     | Basic tasks     |

### AI Features

#### File Analysis

```
Right-click file → "Analyze with AI"
```

**Analysis Types:**

- **Quick**: Basic file information and suggestions
- **Comprehensive**: Detailed analysis with insights
- **Security**: Security vulnerabilities and risks
- **Performance**: Optimization recommendations

**Example Analysis:**

```
📄 report.pdf (2.3MB)

📊 Analysis Results:
• Document Type: Financial Report
• Language: English
• Pages: 15
• Contains: Charts, tables, financial data
• Security: Password protected
• Suggestions:
  - Archive older versions
  - Consider OCR for searchability
  - Backup to secure location
```

#### Smart Organization

```
Select files → Right-click → "AI Organization"
```

**Organization Features:**

- **Auto-categorize**: Sort files by type and content
- **Duplicate Detection**: Find and manage duplicates
- **Cleanup Suggestions**: Remove unnecessary files
- **Folder Structure**: Optimize directory organization

**Example Organization:**

```
📁 Downloads/ (messy)
├── document1.pdf
├── image.jpg
├── setup.exe
└── music.mp3

↓ AI Organization ↓

📁 Downloads/ (organized)
├── 📁 Documents/
│   └── document1.pdf
├── 📁 Images/
│   └── image.jpg
├── 📁 Software/
│   └── setup.exe
└── 📁 Media/
    └── music.mp3
```

#### Content Search

```
Ctrl+Shift+F: AI-powered content search
```

**Search Capabilities:**

- **Natural Language**: "Find documents about budget from last month"
- **Semantic Search**: Understand meaning, not just keywords
- **Content Analysis**: Search inside files (PDF, DOC, etc.)
- **Image Recognition**: Find images by content

#### File Recommendations

The AI assistant provides contextual recommendations:

- **Related Files**: Find files related to current selection
- **Next Actions**: Suggest what to do with files
- **Workflow Optimization**: Improve file management habits
- **Security Alerts**: Warn about potential risks

### AI Chat Interface

#### Accessing AI Chat

```
F1: Open AI assistant
Ctrl+Shift+A: Quick AI query
```

#### Example Conversations

```
You: "Help me organize my Downloads folder"

AI: I can help you organize your Downloads folder. I found:
• 45 files taking up 2.3GB
• 12 different file types
• Several duplicates

Would you like me to:
1. Create folders by file type
2. Remove duplicates
3. Archive old files
4. All of the above

You: "All of the above"

AI: Perfect! I'll organize your Downloads folder:
✅ Created 6 category folders
✅ Moved 45 files to appropriate folders
✅ Found and removed 8 duplicates (saved 156MB)
✅ Archived 15 files older than 6 months

Your Downloads folder is now organized and 156MB smaller!
```

### AI Settings and Privacy

#### Privacy Controls

- **Local Processing**: Keep data on your device
- **Data Retention**: Control how long AI remembers context
- **Opt-out Options**: Disable specific AI features
- **Audit Log**: See what data was sent to AI

#### Performance Tuning

- **Model Selection**: Choose speed vs. accuracy
- **Cache Settings**: Balance performance and storage
- **Batch Processing**: Handle multiple files efficiently
- **Background Processing**: Non-blocking AI operations

## Customization

### Themes and Appearance

#### Built-in Themes

LaxyFile includes several SuperFile-inspired themes:

- **Catppuccin**: Soothing pastel colors
- **Dracula**: Dark theme with purple accents
- **Nord**: Arctic-inspired color palette
- **Gruvbox**: Retro groove colors
- **Tokyo Night**: Dark theme with neon highlights
- **One Dark**: Atom editor inspired
- **Solarized**: High contrast, easy on eyes

#### Theme Customization

```
Settings → Appearance → Customize Theme
```

**Customizable Elements:**

- **Colors**: Background, text, accent colors
- **Fonts**: File list, UI elements, monospace
- **Icons**: File type icons, UI symbols
- **Layout**: Panel sizes, spacing, borders
- **Animations**: Transition effects, timing

#### Creating Custom Themes

```json
{
  "name": "My Custom Theme",
  "version": "1.0",
  "colors": {
    "background": "#1e1e2e",
    "foreground": "#cdd6f4",
    "accent": "#89b4fa",
    "selection": "#313244",
    "border": "#45475a"
  },
  "fonts": {
    "ui": "SF Pro Display",
    "monospace": "JetBrains Mono"
  }
}
```

### Keyboard Shortcuts

#### Default Shortcuts

```
Navigation:
Ctrl+L          Go to location
Ctrl+H          Home directory
Ctrl+R          Root directory
Alt+Left        Back
Alt+Right       Forward
Ctrl+Up         Parent directory

File Operations:
Ctrl+C          Copy
Ctrl+X          Cut
Ctrl+V          Paste
Delete          Delete
F2              Rename
Ctrl+A          Select all
Ctrl+D          Deselect all

Search and Filter:
Ctrl+F          Quick search
Ctrl+Shift+F    AI content search
Ctrl+G          Go to line/file
Ctrl+H          Find and replace

View Options:
F3              Preview toggle
F4              Edit file
F5              Refresh
F6              Dual pane toggle
F9              Menu toggle
F11             Fullscreen

AI Assistant:
F1              Open AI chat
Ctrl+Shift+A    Quick AI query
Ctrl+I          Analyze file
Ctrl+O          AI organization
```

#### Custom Shortcuts

```
Settings → Keyboard → Customize Shortcuts
```

**Shortcut Categories:**

- **Navigation**: Moving around the interface
- **File Operations**: Copy, move, delete, etc.
- **View**: Display options and modes
- **AI**: Assistant functions
- **Custom**: User-defined actions

#### Shortcut Profiles

Create different shortcut sets for different workflows:

- **Default**: Standard file manager shortcuts
- **Vim**: Vim-like navigation
- **SuperFile**: SuperFile-compatible shortcuts
- **Custom**: Your personalized shortcuts

### Plugin System

#### Installing Plugins

```
Settings → Plugins → Browse Plugins
```

**Popular Plugins:**

- **Git Integration**: Version control in file manager
- **Image Tools**: Advanced image manipulation
- **Text Editor**: Built-in code editor
- **Cloud Sync**: Enhanced cloud storage support
- **Archive Plus**: Additional archive formats

#### Plugin Development

```python
# Example plugin structure
from laxyfile.plugins import BasePlugin

class MyPlugin(BasePlugin):
    name = "My Custom Plugin"
    version = "1.0.0"

    def on_file_select(self, file_path):
        # Handle file selection
        pass

    def add_menu_items(self):
        return [
            ("My Action", self.my_action),
        ]

    def my_action(self):
        # Custom action implementation
        pass
```

### Configuration Files

#### Main Configuration

```yaml
# ~/.config/laxyfile/config.yaml
ui:
  theme: "catppuccin"
  font_size: 12
  show_hidden: false
  dual_pane: false

ai:
  provider: "openrouter"
  model: "anthropic/claude-3-haiku"
  enable_analysis: true
  cache_responses: true

performance:
  cache_size: 1000
  lazy_loading: true
  background_processing: true

shortcuts:
  copy: "Ctrl+C"
  paste: "Ctrl+V"
  # ... more shortcuts
```

#### Theme Configuration

```json
{
  "name": "Custom Theme",
  "colors": {
    "background": "#1e1e2e",
    "text": "#cdd6f4",
    "accent": "#89b4fa"
  }
}
```

## Keyboard Shortcuts Reference

### Essential Shortcuts

| Action              | Shortcut         | Description                 |
| ------------------- | ---------------- | --------------------------- |
| **Navigation**      |
| Go to location      | `Ctrl+L`         | Type path to navigate       |
| Home directory      | `Ctrl+H`         | Go to user home             |
| Parent directory    | `Ctrl+Up`        | Go up one level             |
| Back/Forward        | `Alt+Left/Right` | Navigate history            |
| **File Operations** |
| Copy                | `Ctrl+C`         | Copy selected files         |
| Cut                 | `Ctrl+X`         | Cut selected files          |
| Paste               | `Ctrl+V`         | Paste files                 |
| Delete              | `Delete`         | Delete selected files       |
| Rename              | `F2`             | Rename selected file        |
| **Selection**       |
| Select all          | `Ctrl+A`         | Select all files            |
| Deselect all        | `Ctrl+D`         | Clear selection             |
| Invert selection    | `Ctrl+I`         | Invert current selection    |
| **Search**          |
| Quick search        | `Ctrl+F`         | Search in current directory |
| AI search           | `Ctrl+Shift+F`   | AI-powered content search   |
| **View**            |
| Refresh             | `F5`             | Refresh current view        |
| Preview toggle      | `F3`             | Show/hide preview panel     |
| Dual pane           | `F6`             | Toggle dual pane mode       |
| **AI Assistant**    |
| AI chat             | `F1`             | Open AI assistant           |
| Quick AI query      | `Ctrl+Shift+A`   | Quick AI question           |
| Analyze file        | `Ctrl+Shift+I`   | AI file analysis            |

### Advanced Shortcuts

| Action                  | Shortcut       | Description             |
| ----------------------- | -------------- | ----------------------- |
| **Advanced Navigation** |
| Bookmark current        | `Ctrl+B`       | Add to bookmarks        |
| Quick bookmark          | `Ctrl+1-9`     | Go to bookmark 1-9      |
| Recent locations        | `Ctrl+R`       | Show recent directories |
| **File Operations**     |
| Batch rename            | `Ctrl+F2`      | Rename multiple files   |
| Properties              | `Alt+Enter`    | Show file properties    |
| Create folder           | `Ctrl+Shift+N` | New folder              |
| Create file             | `Ctrl+N`       | New file                |
| **Advanced Selection**  |
| Select by pattern       | `Ctrl+Shift+S` | Pattern-based selection |
| Select by type          | `Ctrl+T`       | Select files by type    |
| **View Options**        |
| List view               | `Ctrl+1`       | Detailed list view      |
| Icon view               | `Ctrl+2`       | Large icons view        |
| Tree view               | `Ctrl+3`       | Directory tree view     |
| **System**              |
| Settings                | `Ctrl+,`       | Open settings           |
| Help                    | `F1`           | Show help               |
| Exit                    | `Ctrl+Q`       | Quit application        |

## Troubleshooting

### Common Issues

#### LaxyFile Won't Start

**Symptoms:** Application fails to launch or crashes immediately

**Solutions:**

1. **Check Python Version:**

   ```bash
   python --version  # Should be 3.8+
   ```

2. **Verify Installation:**

   ```bash
   pip show laxyfile
   pip install --upgrade laxyfile
   ```

3. **Check Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Reset Configuration:**
   ```bash
   rm -rf ~/.config/laxyfile/
   ```

#### Slow Performance

**Symptoms:** Sluggish interface, slow file operations

**Solutions:**

1. **Reduce Cache Size:**

   ```yaml
   # config.yaml
   performance:
     cache_size: 500 # Reduce from default 1000
   ```

2. **Disable AI Features:**

   ```yaml
   ai:
     enable_analysis: false
     background_processing: false
   ```

3. **Enable Lazy Loading:**

   ```yaml
   performance:
     lazy_loading: true
     background_processing: true
   ```

4. **Check System Resources:**
   - Close other applications
   - Ensure sufficient RAM (4GB+ recommended)
   - Check disk space

#### AI Assistant Not Working

**Symptoms:** AI features unavailable or not responding

**Solutions:**

1. **Check Internet Connection:**

   - AI requires internet for cloud providers
   - Test with: `ping api.openrouter.ai`

2. **Verify API Key:**

   ```bash
   # Test API key
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://openrouter.ai/api/v1/models
   ```

3. **Try Local Models:**

   ```yaml
   ai:
     provider: "ollama"
     model: "llama2"
   ```

4. **Check Logs:**
   ```bash
   tail -f ~/.config/laxyfile/logs/ai.log
   ```

#### File Operations Failing

**Symptoms:** Copy, move, or delete operations fail

**Solutions:**

1. **Check Permissions:**

   ```bash
   ls -la /path/to/file
   chmod 755 /path/to/file  # If needed
   ```

2. **Verify Disk Space:**

   ```bash
   df -h
   ```

3. **Check File Locks:**

   - Close other applications using the files
   - Restart LaxyFile

4. **Use Safe Mode:**
   ```bash
   laxyfile --safe-mode
   ```

### Performance Optimization

#### For Large Directories

```yaml
performance:
  lazy_loading: true
  max_files_display: 1000
  background_processing: true
  cache_size: 2000
```

#### For Slow Systems

```yaml
ui:
  animations: false
  preview_auto: false

performance:
  cache_size: 500
  max_concurrent_operations: 2
```

#### For AI-Heavy Usage

```yaml
ai:
  cache_responses: true
  cache_ttl: 3600
  max_concurrent_requests: 3
  background_analysis: true
```

### Getting Help

#### Built-in Help

- Press `F1` for context-sensitive help
- Use `Ctrl+Shift+?` for keyboard shortcuts
- Check Settings → Help for tutorials

#### Online Resources

- **Documentation**: https://laxyfile.readthedocs.io
- **GitHub Issues**: https://github.com/your-repo/laxyfile/issues
- **Community Forum**: https://community.laxyfile.com
- **Discord**: https://discord.gg/laxyfile

#### Reporting Bugs

When reporting issues, include:

1. **System Information:**

   ```bash
   laxyfile --version
   python --version
   uname -a  # Linux/macOS
   ```

2. **Configuration:**

   ```bash
   cat ~/.config/laxyfile/config.yaml
   ```

3. **Log Files:**

   ```bash
   tail -n 50 ~/.config/laxyfile/logs/laxyfile.log
   ```

4. **Steps to Reproduce:**
   - Detailed steps to trigger the issue
   - Expected vs. actual behavior
   - Screenshots if applicable

---

_This manual covers the essential features of LaxyFile. For advanced topics and latest updates, visit our online documentation at https://laxyfile.readthedocs.io_
