# Getting Started with LaxyFile

Welcome to LaxyFile! This guide will help you get up and running quickly with your new AI-powered file manager.

## Quick Start (5 Minutes)

### 1. Installation

Choose your preferred installation method:

#### Option A: Install from PyPI (Recommended)

```bash
pip install laxyfile
```

#### Option B: Install from Source

```bash
git clone https://github.com/your-repo/laxyfile.git
cd laxyfile
pip install -e .
```

#### Option C: Platform-Specific Installers

- **Windows**: Download `.msi` installer from [releases](https://github.com/your-repo/laxyfile/releases)
- **macOS**: `brew install laxyfile` or download `.dmg`
- **Linux**: Download `.deb`, `.rpm`, or `.AppImage` from releases

### 2. First Launch

Start LaxyFile:

```bash
laxyfile
```

You'll see the welcome screen with a quick setup wizard:

1. **Choose Theme**: Select from SuperFile-inspired themes
2. **Configure AI** (Optional): Set up AI assistant
3. **Import Settings** (Optional): Import from other file managers

### 3. Basic Navigation

LaxyFile's interface is intuitive and keyboard-friendly:

```
┌─────────────────────────────────────────────────────────────┐
│  📁 /home/user/Documents                    LaxyFile v2.0   │
├─────────────┬───────────────────────────────────────────────┤
│ Bookmarks   │  📄 README.md         2.1KB   Jan 15 10:30   │
│ • Home      │  📁 Projects/         --      Jan 14 15:45   │
│ • Documents │  🖼️ photo.jpg         1.2MB   Jan 13 09:15   │
│ • Downloads │  📊 data.csv          856B    Jan 12 14:20   │
│             │  📦 archive.zip       5.3MB   Jan 11 11:30   │
├─────────────┼───────────────────────────────────────────────┤
│ Preview     │  5 items • 8.7MB • AI Ready                  │
└─────────────┴───────────────────────────────────────────────┘
```

**Essential Keys:**

- `↑↓` - Navigate files
- `Enter` - Open file/folder
- `Backspace` - Go to parent directory
- `Ctrl+C/V` - Copy/paste files
- `F1` - AI assistant help

### 4. Try the AI Assistant

Press `F1` to open the AI assistant and try:

```
You: "Help me organize my Downloads folder"

AI: I can help! I found 23 files in your Downloads folder.
    Would you like me to organize them by type?

You: "Yes, please"

AI: ✅ Organized 23 files into 5 folders:
    • Documents (8 files)
    • Images (6 files)
    • Software (4 files)
    • Archives (3 files)
    • Other (2 files)
```

### 5. Customize Your Experience

Go to `Settings` (Ctrl+,) to customize:

- **Theme**: Choose colors and appearance
- **Shortcuts**: Customize keyboard shortcuts
- **AI**: Configure AI provider and model
- **Plugins**: Add extra functionality

## 10-Minute Deep Dive

### File Operations Mastery

#### Smart Selection

```bash
# Select multiple files
Ctrl+Click      # Add to selection
Shift+Click     # Select range
Ctrl+A          # Select all
*.txt           # Select by pattern (type in search)
```

#### Advanced Copy/Move

LaxyFile provides intelligent file operations:

1. **Smart Conflict Resolution**:

   ```
   Copying file.txt...
   ❓ file.txt already exists. What would you like to do?

   [R]eplace  [S]kip  [R]ename  [A]uto-rename  [C]ancel
   ```

2. **Progress Tracking**:

   ```
   📁 Copying 15 files (234 MB)
   ████████████████████████████████████████ 67%
   📄 Currently: large_video.mp4 (45 MB/s)
   ⏱️ ETA: 2m 15s
   ```

3. **Verification**:
   ```
   ✅ Copy completed successfully
   📊 15 files copied (234 MB)
   🔍 Verification: All files intact
   ```

#### Archive Operations

Create and extract archives with ease:

```bash
# Create archive
1. Select files
2. Right-click → "Create Archive"
3. Choose format: ZIP, TAR, 7Z
4. Set compression level

# Extract archive
1. Select archive file
2. Press Enter or right-click → "Extract"
3. Choose destination
4. Handle conflicts automatically
```

### AI-Powered Features

#### File Analysis

Right-click any file and select "Analyze with AI":

```
📄 report.pdf Analysis:

📊 Content Summary:
• Document type: Financial report
• Pages: 12
• Language: English
• Contains: Charts, tables, financial data

🔍 Key Insights:
• Q4 revenue increased 15%
• Marketing budget recommendations on page 8
• Action items highlighted on page 11

💡 Suggestions:
• Archive previous versions
• Share with finance team
• Schedule follow-up meeting
```

#### Smart Organization

Select messy folders and use AI organization:

```
Before:
📁 Downloads/
├── IMG_001.jpg
├── document.pdf
├── setup.exe
├── song.mp3
├── IMG_002.jpg
└── report.docx

After AI Organization:
📁 Downloads/
├── 📁 Images/
│   ├── IMG_001.jpg
│   └── IMG_002.jpg
├── 📁 Documents/
│   ├── document.pdf
│   └── report.docx
├── 📁 Software/
│   └── setup.exe
└── 📁 Media/
    └── song.mp3
```

#### Content Search

Use natural language to find files:

```bash
Ctrl+Shift+F: "Find documents about budget from last month"

🔍 AI Search Results:
📄 Q4_Budget_Report.pdf - Contains budget analysis
📊 Monthly_Expenses.xlsx - Budget tracking spreadsheet
📝 Budget_Meeting_Notes.txt - Meeting notes from Dec 15
```

### Customization Essentials

#### Theme Selection

LaxyFile includes beautiful SuperFile-inspired themes:

- **Catppuccin**: Soothing pastels 🎨
- **Dracula**: Dark with purple accents 🧛
- **Nord**: Arctic-inspired blues ❄️
- **Gruvbox**: Retro warm colors 🍂
- **Tokyo Night**: Neon-lit darkness 🌃

Change themes instantly: `Settings → Appearance → Theme`

#### Keyboard Shortcuts

Customize shortcuts to match your workflow:

```yaml
# Popular configurations
Default: Standard file manager shortcuts
Vim-like: hjkl navigation, modal editing
SuperFile: SuperFile-compatible shortcuts
Custom: Your personalized setup
```

#### Plugin System

Extend LaxyFile with plugins:

```bash
# Popular plugins
Git Integration    # Version control in file manager
Image Tools       # Advanced image manipulation
Text Editor       # Built-in code editor
Cloud Sync        # Enhanced cloud storage
Archive Plus      # Additional archive formats
```

## 30-Minute Power User Guide

### Advanced Navigation

#### Breadcrumb Power

The breadcrumb bar is more than just a path display:

```
Home > Documents > Projects > LaxyFile > docs
  ↑        ↑         ↑         ↑        ↑
Click   Right-click  Drag     Middle    Type
to go   for menu    files    click     path
```

#### Quick Navigation Tricks

```bash
Ctrl+L          # Type path directly: /home/user/Documents
Ctrl+H          # Jump to home directory
Ctrl+R          # Go to filesystem root
Alt+Left/Right  # Navigate history like a web browser
Ctrl+1-9        # Quick access to bookmarks 1-9
```

#### Directory Tree Navigation

Use the sidebar tree for efficient navigation:

- Click folders to navigate
- Right-click for context menu
- Drag files to tree folders
- Expand/collapse with arrow keys

### Advanced File Operations

#### Batch Operations

Select multiple files and perform batch operations:

```bash
# Batch rename
1. Select files
2. Press F2
3. Use patterns:
   Pattern: Document_{counter:03d}
   Result: Document_001.txt, Document_002.txt, ...

# Batch attribute changes
1. Select files
2. Right-click → Properties
3. Change permissions, timestamps, etc.
```

#### Smart Duplicate Handling

LaxyFile intelligently handles duplicates:

```
Duplicate Detection:
🔍 Found 3 duplicates of "photo.jpg"
📁 /Downloads/photo.jpg (original)
📁 /Pictures/photo.jpg (duplicate - same content)
📁 /Desktop/photo.jpg (duplicate - same content)

Actions:
[K]eep original  [M]erge all  [R]eview each  [C]ancel
```

#### Advanced Search Patterns

Master LaxyFile's search capabilities:

```bash
# File name patterns
*.{jpg,png,gif}     # Multiple extensions
[Dd]ocument*        # Case variations
*report*2024*       # Multiple wildcards

# Content search
content:"important data"     # Exact phrase
content:budget AND 2024     # Boolean operators
size:>10MB                  # Size filters
modified:last-week          # Date filters
type:image                  # File type filters
```

### AI Assistant Mastery

#### Advanced AI Queries

The AI assistant understands complex requests:

```
You: "Find all PDF files larger than 5MB that haven't been
     accessed in 6 months and suggest what to do with them"

AI: I found 12 PDF files matching your criteria:

📊 Analysis:
• Total size: 156 MB
• Oldest: annual_report_2022.pdf (18 months old)
• Largest: presentation_archive.pdf (23 MB)

💡 Recommendations:
1. Archive 8 files to external storage (save 89 MB)
2. Delete 3 temporary files (save 15 MB)
3. Keep 1 reference document in current location

Would you like me to execute these recommendations?
```

#### Custom AI Workflows

Create custom AI workflows for repetitive tasks:

```yaml
# Example workflow: Photo Organization
name: "Organize Photos"
trigger: "New files in Pictures folder"
actions:
  - analyze_image_content
  - extract_metadata
  - create_date_folders
  - move_to_appropriate_folder
  - generate_thumbnails
```

#### AI Learning and Adaptation

The AI learns from your preferences:

```
AI: I noticed you often move .pdf files from Downloads
    to Documents/Work. Would you like me to create a
    rule to do this automatically?

[Y]es, create rule  [N]o, ask each time  [C]ustomize rule
```

### Performance Optimization

#### Large Directory Handling

Optimize LaxyFile for large directories:

```yaml
# config.yaml
performance:
  lazy_loading: true # Load files as needed
  max_files_display: 1000 # Limit initial display
  background_processing: true # Non-blocking operations
  cache_size: 2000 # Increase cache for speed
```

#### Memory Management

Monitor and optimize memory usage:

```bash
# Check performance
Ctrl+Shift+P    # Performance monitor
F12             # Debug information

# Optimize settings
Settings → Performance → Memory Management
- Enable garbage collection
- Set cache limits
- Configure background processing
```

#### Network and Cloud Optimization

For network drives and cloud storage:

```yaml
network:
  timeout: 30 # Connection timeout
  retry_attempts: 3 # Retry failed operations
  cache_remote_listings: true # Cache directory listings
  background_sync: true # Sync in background
```

## Common Workflows

### Workflow 1: Daily File Organization

**Morning Routine (2 minutes):**

1. Open LaxyFile
2. Navigate to Downloads folder
3. Press `Ctrl+Shift+A` → "Organize my downloads"
4. AI automatically sorts files into appropriate folders
5. Review and confirm changes

### Workflow 2: Project Management

**Setting up a new project:**

1. Create project folder: `Ctrl+Shift+N`
2. Set up folder structure with AI: "Create a standard project structure"
3. Add folder to bookmarks: `Ctrl+B`
4. Configure project-specific settings

### Workflow 3: Media Management

**Organizing photos and videos:**

1. Select media files
2. Right-click → "AI Analysis"
3. AI extracts metadata and suggests organization
4. Create date-based folders automatically
5. Generate thumbnails and previews

### Workflow 4: Document Processing

**Processing work documents:**

1. Drag documents to LaxyFile
2. AI analyzes content and extracts key information
3. Auto-tag documents with relevant keywords
4. Move to appropriate project folders
5. Create backup copies if important

## Tips and Tricks

### Productivity Tips

1. **Use Keyboard Shortcuts**: Learn the essential shortcuts to work faster
2. **Customize Your Workspace**: Set up bookmarks for frequently used folders
3. **Leverage AI**: Let AI handle repetitive organization tasks
4. **Use Dual Pane Mode**: Compare and transfer files between locations
5. **Master Search**: Use advanced search patterns to find files quickly

### Hidden Features

1. **Quick Preview**: Hover over files for instant preview
2. **Drag and Drop**: Drag files to breadcrumb locations
3. **Middle-Click Navigation**: Middle-click folders to open in new tab
4. **Context-Aware Menus**: Right-click menus change based on file type
5. **Smart Suggestions**: AI provides contextual suggestions based on your actions

### Troubleshooting Quick Fixes

1. **Slow Performance**: Reduce cache size or disable animations
2. **AI Not Working**: Check internet connection and API key
3. **Files Not Showing**: Press F5 to refresh or check hidden file settings
4. **Shortcuts Not Working**: Check for conflicts in Settings → Keyboard
5. **Theme Issues**: Reset to default theme and restart

## Next Steps

Now that you're familiar with LaxyFile basics, explore these advanced topics:

1. **[Plugin Development](plugin-development.md)**: Create custom plugins
2. **[AI Configuration](ai-configuration.md)**: Advanced AI setup
3. **[Automation](automation.md)**: Create custom workflows
4. **[Integration](integration.md)**: Connect with other tools
5. **[Performance Tuning](performance-tuning.md)**: Optimize for your system

## Getting Help

- **Built-in Help**: Press `F1` for context-sensitive help
- **Documentation**: Visit [docs.laxyfile.com](https://docs.laxyfile.com)
- **Community**: Join our [Discord server](https://discord.gg/laxyfile)
- **Issues**: Report bugs on [GitHub](https://github.com/your-repo/laxyfile/issues)

Welcome to the LaxyFile community! We're excited to see how you'll use your new AI-powered file manager. 🚀
