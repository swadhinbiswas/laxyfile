# 🚀 LaxyFile - Advanced Terminal File Manager

**A beautiful, AI-powered terminal file manager inspired by Superfile with advanced media support and intelligent automation**

## ✨ Features

### 🎨 **Beautiful Interface**

- **5 Gorgeous Themes**: Cappuccino (default), Neon, Ocean, Sunset, Forest
- **Modern UI**: Rounded borders, colorful file listings, beautiful header with rainbow gradient
- **Smart Icons**: File type icons for 50+ formats with Unicode support
- **Dual-Pane**: Side-by-side directory browsing with preview panel
- **Responsive**: Adapts to terminal size with optimal layout

### 🤖 **AI Assistant (Powered by Kimi AI)**

- **Complete System Analysis**: Monitor devices, processes, storage, and network
- **Intelligent File Organization**: AI suggests optimal directory structures and file management
- **Security Audits**: Vulnerability detection, permission analysis, suspicious file identification
- **Performance Optimization**: Storage cleanup, resource monitoring, speed improvements
- **Video & Media Analysis**: Metadata extraction, encoding details, organization suggestions
- **Duplicate Detection**: Smart file comparison and cleanup recommendations
- **Content Analysis**: Read and understand file contents for better suggestions
- **Real-time Insights**: Instant analysis and actionable recommendations

### 📁 **Advanced File Management**

- **Smart Operations**: Copy, move, delete, rename with progress feedback
- **Multi-Selection**: Select multiple files with visual indicators
- **Quick Navigation**: Vim-style (hjkl) + arrow keys, instant directory jumping
- **Hidden Files**: Toggle visibility with smart filtering
- **File Operations**: Create directories, batch operations, trash support

### 🎬 **Media & Content Viewing**

- **Image Support**: ASCII art conversion with color preservation, metadata display
- **Video Analysis**: Thumbnail generation, metadata extraction, format details
- **Code Highlighting**: Syntax highlighting for 100+ programming languages
- **Preview Panel**: Real-time file preview with smart content detection
- **Terminal Graphics**: Sixel, Kitty, iTerm2 support for high-quality images

### ⚡ **Performance & Usability**

- **Fast Navigation**: Instant directory switching, efficient file loading
- **Session Memory**: Remember last directories and settings
- **Configurable**: YAML configuration with extensive customization
- **Error Handling**: Graceful failure recovery, comprehensive logging
- **Cross-Platform**: Linux, macOS, Windows support

## 🛠️ Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/laxyfile.git
cd laxyfile

# Install dependencies
pip install -r requirements.txt

# Run LaxyFile
python run_laxyfile.py
```

### Dependencies

```bash
# Core dependencies (required)
pip install rich pydantic PyYAML Pillow opencv-python pygments

# AI features (recommended)
pip install openai psutil python-magic requests aiofiles
```

## 🤖 AI Setup (Free!)

### 1. Get OpenRouter API Key

1. Visit [https://openrouter.ai/](https://openrouter.ai/)
2. Create a free account
3. Get your API key (free tier includes Kimi AI model)

### 2. Configure Environment

```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export OPENROUTER_API_KEY="your-api-key-here"

# Reload your shell
source ~/.bashrc
```

### 3. Verify AI Setup

```bash
# Launch LaxyFile
python run_laxyfile.py

# Look for: "🤖 AI Assistant: Ready with Kimi AI model"
```

## 🎯 Usage

### Basic Navigation

- **hjkl** or **Arrow Keys**: Navigate files
- **Tab**: Switch between panels
- **Enter**: Open file/directory
- **Space**: Select/deselect files
- **g/G**: Jump to top/bottom

### File Operations

- **c**: Copy selected files
- **m**: Move selected files
- **d**: Delete files
- **r**: Rename file
- **n**: New directory
- **v**: View file with media viewer
- **e**: Edit file

### 🤖 AI Features

- **i**: Open AI Assistant menu
- **F9**: Quick AI analysis of current directory

#### AI Assistant Menu Options:

1. **💬 Chat**: Ask AI anything about your files
2. **🔍 System Analysis**: Complete device and file analysis
3. **📁 File Organization**: Smart organization suggestions
4. **🔒 Security Audit**: Vulnerability and security analysis
5. **⚡ Performance**: Optimization recommendations
6. **🎬 Video Analysis**: Media file analysis and optimization
7. **🔄 Duplicates**: Find and manage duplicate files
8. **📸 Media Organization**: Organize photos and videos intelligently
9. **💾 Backup Strategy**: Intelligent backup recommendations

### Themes & UI

- **t**: Cycle through themes
- **F1-F5**: Set specific theme (Cappuccino, Neon, Ocean, Sunset, Forest)
- **p**: Toggle preview panel
- **.**: Toggle hidden files

### Quick Navigation

- **~**: Go to home directory
- **/**: Go to root directory
- **?**: Show help

## 🎨 Themes

### 🟤 Cappuccino (Default)

Warm browns and golden colors for a cozy coding experience

### 🌈 Neon

Bright electric colors with high contrast

### 🌊 Ocean

Cool blues and teals for a calming experience

### 🌅 Sunset

Warm oranges and reds for vibrant browsing

### 🌲 Forest

Natural greens and earth tones

## 🔧 Configuration

Create `~/.config/laxyfile/config.yaml`:

```yaml
# AI Configuration
ai:
  enabled: true
  provider: "openrouter"
  model: "moonshotai/kimi-dev-72b:free"
  max_tokens: 4000
  enable_content_analysis: true
  enable_device_monitoring: true

# Theme and UI
theme:
  name: "cappuccino"
  use_icons: true

ui:
  preview_pane: true
  refresh_rate: 30

# Keyboard shortcuts
hotkeys:
  ai_assistant: ["i"]
  quick_ai_analysis: ["F9"]
```

See `example_config.yaml` for complete configuration options.

## 🚀 AI Examples

### System Analysis

```
🤖 AI analyzing your system...

📊 SYSTEM OVERVIEW:
• CPU: Intel i7 (8 cores) - 15% usage
• Memory: 16GB (45% used)
• Storage: 512GB SSD (78% full)
• Network: Connected, 50+ Mbps

📁 DIRECTORY ANALYSIS:
• 1,247 files across 89 directories
• Top types: .js (234), .py (156), .jpg (89)
• Large files: video.mp4 (2.1GB), dataset.csv (456MB)

🔍 RECOMMENDATIONS:
• Clean up old videos to free 3.2GB space
• Archive old project files to external storage
• Consider organizing code files by project
• Update system packages for security
```

### Smart File Organization

```
🤖 Analyzing file structure...

📂 CURRENT STRUCTURE:
Downloads/
├── 234 mixed files (docs, images, code)
├── No clear organization pattern
└── 15 duplicate files detected

✨ RECOMMENDED STRUCTURE:
Downloads/
├── Documents/
│   ├── PDFs/
│   └── Spreadsheets/
├── Media/
│   ├── Images/2024/
│   └── Videos/
├── Code/
│   ├── Python/
│   └── JavaScript/
└── Archive/old_files/

🎯 ACTIONS:
1. Move 89 images to Media/Images/2024/
2. Organize 45 documents by type
3. Remove 15 duplicate files (saves 234MB)
4. Archive files older than 1 year
```

### Security Audit

```
🔒 SECURITY ANALYSIS:

⚠️  VULNERABILITIES FOUND:
• 3 executable files with 777 permissions
• 12 hidden files in system directories
• 1 suspicious .exe file detected
• Weak permissions on SSH keys

🛡️  RECOMMENDATIONS:
• Fix file permissions: chmod 644 suspicious_files
• Review hidden files for malware
• Move executables to secure location
• Strengthen SSH key permissions (600)
• Enable firewall for additional protection

🔍 MONITORING:
• No active suspicious processes
• Network connections appear normal
• File integrity checks passed
```

## 🎬 Video Features

LaxyFile includes advanced video analysis capabilities:

- **Format Detection**: Automatically identify video codecs and containers
- **Metadata Extraction**: Resolution, framerate, duration, bitrate
- **Thumbnail Generation**: Preview frames for quick identification
- **Quality Analysis**: Bitrate analysis and compression recommendations
- **Organization**: Smart sorting by resolution, date, or quality
- **Conversion Suggestions**: AI recommends optimal formats for different uses

## 📋 System Requirements

- **Python**: 3.8 or higher
- **Terminal**: Any modern terminal with color support
- **OS**: Linux, macOS, Windows (with proper terminal)
- **Memory**: 256MB+ RAM
- **Storage**: 50MB+ free space

### Recommended

- **Terminal**: Kitty, iTerm2, or modern terminal with truecolor support
- **Size**: 120x30 characters or larger
- **Fonts**: Nerd Fonts or Unicode-compatible monospace font

## 🤝 Contributing

We welcome contributions! See `CONTRIBUTING.md` for guidelines.

### Development Setup

```bash
git clone https://github.com/yourusername/laxyfile.git
cd laxyfile
pip install -r requirements.txt
python run_laxyfile.py
```

## 📄 License

MIT License - see `LICENSE` file for details.

## 🙏 Acknowledgments

- **Superfile**: Inspiration for the beautiful terminal interface
- **Rich**: Amazing terminal rendering library
- **OpenRouter**: AI API platform providing access to Kimi AI
- **Kimi AI**: Powerful language model for intelligent file analysis

## 🆘 Troubleshooting

### AI Not Working?

```bash
# Check API key
echo $OPENROUTER_API_KEY

# Verify dependencies
pip install openai psutil python-magic

# Test connection
python -c "import openai; print('OpenAI client available')"
```

### Display Issues?

```bash
# Set terminal variables
export TERM="xterm-256color"
export COLORTERM="truecolor"

# Resize terminal to 120x30 or larger
```

### Permission Errors?

```bash
# Check file permissions
ls -la laxyfile/

# Fix if needed
chmod +x run_laxyfile.py
```

---

_Experience the future of terminal file management!_ 🚀
