"""
Modern Theme Management System with comprehensive color schemes inspired by Superfile
Supports multiple popular themes from the terminal community
"""

from typing import Dict, Any, Optional
from rich.style import Style
from ..core.config import Config

class ThemeManager:
    """Advanced theme management system inspired by Superfile's extensive theme support"""

    def __init__(self, config: Config):
        self.config = config
        self.current_theme = config.get_theme()
        self._setup_themes()

    def _setup_themes(self):
        """Setup comprehensive theme collection inspired by popular terminal themes"""
        self.themes = {
            # Default theme - Modern and clean
            "default": {
                "header": "bold white on #44475A",
                "footer": "white on #6272A4",
                "border_active": "#8BE9FD",
                "border_inactive": "#6272A4",
                "background": "#282A36",
                "file": "#F8F8F2",
                "directory": "bold #8BE9FD",
                "selected": "#282A36 on #50FA7B",
                "current": "#282A36 on #FFB86C",
                "current_selected": "#282A36 on #FF79C6",
                "error": "bold #FF5555",
                "success": "bold #50FA7B",
                "warning": "bold #F1FA8C",
                "info": "bold #8BE9FD",
                "image": "bold #FF79C6",
                "video": "bold #BD93F9",
                "audio": "bold #FF6B6B",
                "code": "bold #50FA7B",
                "archive": "bold #F1FA8C",
                "document": "bold #8BE9FD",
                "executable": "bold #FF5555",
                "symlink": "bold #6BE5FD",
                "cursor": "#FFB86C",
                "hint": "#6272A4",
                "cancel": "#FF5555",
                "confirm": "#50FA7B",
                "file_fg": "#F8F8F2",
                "file_bg": "#282A36",
                "sidebar_title": "bold #FF79C6",
                "sidebar_divider": "#44475A",
                "help_menu_hotkey": "#FF79C6",
                "help_menu_title": "bold #8BE9FD",
                "gradient": ["#FF79C6", "#BD93F9", "#8BE9FD"],
                "directory_icon": "#8BE9FD",
            },

            # Ayu Dark
            "ayu-dark": {
                "header": "bold #B3B1AD on #0D1017",
                "footer": "#B3B1AD on #1A1F29",
                "border_active": "#FFB454",
                "border_inactive": "#3D424D",
                "background": "#0A0E14",
                "file": "#B3B1AD",
                "directory": "bold #39BAE6",
                "selected": "#0A0E14 on #C2D94C",
                "current": "#0A0E14 on #FFB454",
                "current_selected": "#0A0E14 on #F07178",
                "error": "bold #F07178",
                "success": "bold #C2D94C",
                "warning": "bold #E6B450",
                "info": "bold #39BAE6",
                "image": "bold #F07178",
                "video": "bold #39BAE6",
                "audio": "bold #FFB454",
                "code": "bold #C2D94C",
                "archive": "bold #E6B450",
                "document": "bold #B3B1AD",
                "executable": "bold #C2D94C",
                "symlink": "bold #39BAE6",
                "cursor": "#FFB454",
                "hint": "#5C6773",
                "cancel": "#F07178",
                "confirm": "#C2D94C",
                "file_fg": "#B3B1AD",
                "file_bg": "#0A0E14",
                "sidebar_title": "bold #FFB454",
                "sidebar_divider": "#1A1F29",
                "help_menu_hotkey": "#FFB454",
                "help_menu_title": "bold #39BAE6",
                "gradient": ["#F07178", "#FFB454", "#C2D94C"],
                "directory_icon": "#39BAE6",
            },

            # Blood
            "blood": {
                "header": "bold #f5f5f5 on #330000",
                "footer": "#f5f5f5 on #590000",
                "border_active": "#ff0000",
                "border_inactive": "#8b0000",
                "background": "#1a0000",
                "file": "#f5f5f5",
                "directory": "bold #ff4d4d",
                "selected": "#1a0000 on #b30000",
                "current": "#1a0000 on #ff6666",
                "current_selected": "#f5f5f5 on #ff0000",
                "error": "bold #ff0000",
                "success": "bold #99ff99",
                "warning": "bold #ffff99",
                "info": "bold #9999ff",
                "image": "bold #ffb3b3",
                "video": "bold #b3b3ff",
                "audio": "bold #ff8080",
                "code": "bold #d9d9d9",
                "archive": "bold #ffd9b3",
                "document": "bold #f5f5f5",
                "executable": "bold #ff0000",
                "symlink": "bold #ffad33",
                "cursor": "#ff0000",
                "hint": "#8b0000",
                "cancel": "#ff0000",
                "confirm": "#99ff99",
                "file_fg": "#f5f5f5",
                "file_bg": "#1a0000",
                "sidebar_title": "bold #ff0000",
                "sidebar_divider": "#330000",
                "help_menu_hotkey": "#ff0000",
                "help_menu_title": "bold #ff4d4d",
                "gradient": ["#ff0000", "#b30000", "#8b0000"],
                "directory_icon": "#ff4d4d",
            },

            # Catppuccin Frappe
            "catppuccin-frappe": {
                "header": "bold #c6d0f5 on #414559",
                "footer": "#c6d0f5 on #51576d",
                "border_active": "#ca9ee6",
                "border_inactive": "#626880",
                "background": "#303446",
                "file": "#c6d0f5",
                "directory": "bold #8caaee",
                "selected": "#303446 on #a6d189",
                "current": "#303446 on #e5c890",
                "current_selected": "#303446 on #f2d5cf",
                "error": "bold #e78284",
                "success": "bold #a6d189",
                "warning": "bold #e5c890",
                "info": "bold #8caaee",
                "image": "bold #f4b8e4",
                "video": "bold #ca9ee6",
                "audio": "bold #ea999c",
                "code": "bold #a6d189",
                "archive": "bold #e5c890",
                "document": "bold #8caaee",
                "executable": "bold #e78284",
                "symlink": "bold #81c8be",
                "cursor": "#ca9ee6",
                "hint": "#626880",
                "cancel": "#e78284",
                "confirm": "#a6d189",
                "file_fg": "#c6d0f5",
                "file_bg": "#303446",
                "sidebar_title": "bold #ca9ee6",
                "sidebar_divider": "#414559",
                "help_menu_hotkey": "#e5c890",
                "help_menu_title": "bold #8caaee",
                "gradient": ["#ca9ee6", "#8caaee", "#a6d189"],
                "directory_icon": "#8caaee",
            },

            # Catppuccin Latte
            "catppuccin-latte": {
                "header": "bold #4c4f69 on #e6e9ef",
                "footer": "#4c4f69 on #dce0e8",
                "border_active": "#8839ef",
                "border_inactive": "#bcc0cc",
                "background": "#eff1f5",
                "file": "#4c4f69",
                "directory": "bold #1e66f5",
                "selected": "#eff1f5 on #40a02b",
                "current": "#eff1f5 on #df8e1d",
                "current_selected": "#eff1f5 on #d20f39",
                "error": "bold #d20f39",
                "success": "bold #40a02b",
                "warning": "bold #df8e1d",
                "info": "bold #1e66f5",
                "image": "bold #ea76cb",
                "video": "bold #8839ef",
                "audio": "bold #e64553",
                "code": "bold #40a02b",
                "archive": "bold #df8e1d",
                "document": "bold #1e66f5",
                "executable": "bold #d20f39",
                "symlink": "bold #179299",
                "cursor": "#8839ef",
                "hint": "#bcc0cc",
                "cancel": "#d20f39",
                "confirm": "#40a02b",
                "file_fg": "#4c4f69",
                "file_bg": "#eff1f5",
                "sidebar_title": "bold #8839ef",
                "sidebar_divider": "#e6e9ef",
                "help_menu_hotkey": "#df8e1d",
                "help_menu_title": "bold #1e66f5",
                "gradient": ["#8839ef", "#1e66f5", "#40a02b"],
                "directory_icon": "#1e66f5",
            },

            # Catppuccin Macchiato
            "catppuccin-macchiato": {
                "header": "bold #cad3f5 on #363a4f",
                "footer": "#cad3f5 on #494d64",
                "border_active": "#c6a0f6",
                "border_inactive": "#5b6078",
                "background": "#24273a",
                "file": "#cad3f5",
                "directory": "bold #8aadf4",
                "selected": "#24273a on #a6da95",
                "current": "#24273a on #eed49f",
                "current_selected": "#24273a on #f5bde6",
                "error": "bold #ed8796",
                "success": "bold #a6da95",
                "warning": "bold #eed49f",
                "info": "bold #8aadf4",
                "image": "bold #f5bde6",
                "video": "bold #c6a0f6",
                "audio": "bold #f0c6c6",
                "code": "bold #a6da95",
                "archive": "bold #eed49f",
                "document": "bold #8aadf4",
                "executable": "bold #ed8796",
                "symlink": "bold #8bd5ca",
                "cursor": "#c6a0f6",
                "hint": "#5b6078",
                "cancel": "#ed8796",
                "confirm": "#a6da95",
                "file_fg": "#cad3f5",
                "file_bg": "#24273a",
                "sidebar_title": "bold #c6a0f6",
                "sidebar_divider": "#363a4f",
                "help_menu_hotkey": "#eed49f",
                "help_menu_title": "bold #8aadf4",
                "gradient": ["#c6a0f6", "#8aadf4", "#a6da95"],
                "directory_icon": "#8aadf4",
            },

            # Dracula theme - Popular dark theme
            "dracula": {
                "header": "bold #F8F8F2 on #44475A",
                "footer": "#F8F8F2 on #6272A4",
                "border_active": "#FF79C6",
                "border_inactive": "#44475A",
                "background": "#282A36",
                "file": "#F8F8F2",
                "directory": "bold #BD93F9",
                "selected": "#282A36 on #50FA7B",
                "current": "#282A36 on #FFB86C",
                "current_selected": "#282A36 on #FF79C6",
                "error": "bold #FF5555",
                "success": "bold #50FA7B",
                "warning": "bold #F1FA8C",
                "info": "bold #8BE9FD",
                "image": "bold #FF79C6",
                "video": "bold #BD93F9",
                "audio": "bold #FF6B6B",
                "code": "bold #50FA7B",
                "archive": "bold #F1FA8C",
                "document": "bold #8BE9FD",
                "executable": "bold #FF5555",
                "symlink": "bold #6BE5FD",
                "cursor": "#FF79C6",
                "hint": "#6272A4",
                "cancel": "#FF5555",
                "confirm": "#50FA7B",
                "file_fg": "#F8F8F2",
                "file_bg": "#282A36",
                "sidebar_title": "bold #FF79C6",
                "sidebar_divider": "#44475A",
                "help_menu_hotkey": "#FFB86C",
                "help_menu_title": "bold #BD93F9",
                "gradient": ["#FF79C6", "#BD93F9", "#8BE9FD", "#50FA7B"],
                "directory_icon": "#BD93F9",
            },

            # Everforest Dark Medium
            "everforest-dark": {
                "header": "bold #d3c6aa on #3a444a",
                "footer": "#d3c6aa on #4a555b",
                "border_active": "#dbbc7f",
                "border_inactive": "#5a656b",
                "background": "#2f383e",
                "file": "#d3c6aa",
                "directory": "bold #7fbbb3",
                "selected": "#2f383e on #a7c080",
                "current": "#2f383e on #dbbc7f",
                "current_selected": "#2f383e on #e67e80",
                "error": "bold #e67e80",
                "success": "bold #a7c080",
                "warning": "bold #dbbc7f",
                "info": "bold #7fbbb3",
                "image": "bold #d699b6",
                "video": "bold #7fbbb3",
                "audio": "bold #e67e80",
                "code": "bold #a7c080",
                "archive": "bold #dbbc7f",
                "document": "bold #d3c6aa",
                "executable": "bold #a7c080",
                "symlink": "bold #83c092",
                "cursor": "#dbbc7f",
                "hint": "#5a656b",
                "cancel": "#e67e80",
                "confirm": "#a7c080",
                "file_fg": "#d3c6aa",
                "file_bg": "#2f383e",
                "sidebar_title": "bold #d699b6",
                "sidebar_divider": "#3a444a",
                "help_menu_hotkey": "#dbbc7f",
                "help_menu_title": "bold #7fbbb3",
                "gradient": ["#e67e80", "#dbbc7f", "#a7c080"],
                "directory_icon": "#7fbbb3",
            },

            # Gruvbox Dark Hard
            "gruvbox-dark-hard": {
                "header": "bold #fbf1c7 on #32302f",
                "footer": "#fbf1c7 on #504945",
                "border_active": "#fabd2f",
                "border_inactive": "#7c6f64",
                "background": "#1d2021",
                "file": "#fbf1c7",
                "directory": "bold #83a598",
                "selected": "#1d2021 on #b8bb26",
                "current": "#1d2021 on #fabd2f",
                "current_selected": "#1d2021 on #fb4934",
                "error": "bold #fb4934",
                "success": "bold #b8bb26",
                "warning": "bold #fabd2f",
                "info": "bold #83a598",
                "image": "bold #d3869b",
                "video": "bold #8ec07c",
                "audio": "bold #fe8019",
                "code": "bold #b8bb26",
                "archive": "bold #fabd2f",
                "document": "bold #83a598",
                "executable": "bold #fb4934",
                "symlink": "bold #8ec07c",
                "cursor": "#fabd2f",
                "hint": "#7c6f64",
                "cancel": "#fb4934",
                "confirm": "#b8bb26",
                "file_fg": "#fbf1c7",
                "file_bg": "#1d2021",
                "sidebar_title": "bold #d3869b",
                "sidebar_divider": "#32302f",
                "help_menu_hotkey": "#fabd2f",
                "help_menu_title": "bold #83a598",
                "gradient": ["#fb4934", "#fabd2f", "#b8bb26"],
                "directory_icon": "#83a598",
            },

            # Hacks
            "hacks": {
                "header": "bold #00ff00 on #0f0f0f",
                "footer": "#00ff00 on #1a1a1a",
                "border_active": "#00ff00",
                "border_inactive": "#008000",
                "background": "#000000",
                "file": "#00ff00",
                "directory": "bold #33ff33",
                "selected": "#000000 on #008000",
                "current": "#000000 on #66ff66",
                "current_selected": "#000000 on #ffffff",
                "error": "bold #ff0000",
                "success": "bold #00ff00",
                "warning": "bold #ffff00",
                "info": "bold #00ffff",
                "image": "bold #ff00ff",
                "video": "bold #00ffff",
                "audio": "bold #ff0000",
                "code": "bold #00ff00",
                "archive": "bold #ffff00",
                "document": "bold #00ff00",
                "executable": "bold #ffffff",
                "symlink": "bold #00ffff",
                "cursor": "#00ff00",
                "hint": "#008000",
                "cancel": "#ff0000",
                "confirm": "#00ff00",
                "file_fg": "#00ff00",
                "file_bg": "#000000",
                "sidebar_title": "bold #00ff00",
                "sidebar_divider": "#0f0f0f",
                "help_menu_hotkey": "#00ff00",
                "help_menu_title": "bold #33ff33",
                "gradient": ["#00ff00", "#00cc00", "#008000"],
                "directory_icon": "#33ff33",
            },

            # Kaolin
            "kaolin": {
                "header": "bold #c4c7d1 on #2a2b2c",
                "footer": "#c4c7d1 on #3c3d3e",
                "border_active": "#a98813",
                "border_inactive": "#52545a",
                "background": "#181819",
                "file": "#c4c7d1",
                "directory": "bold #2d65ca",
                "selected": "#181819 on #388a3a",
                "current": "#181819 on #a98813",
                "current_selected": "#181819 on #c84739",
                "error": "bold #c84739",
                "success": "bold #388a3a",
                "warning": "bold #a98813",
                "info": "bold #2d65ca",
                "image": "bold #8434a4",
                "video": "bold #2d65ca",
                "audio": "bold #c84739",
                "code": "bold #388a3a",
                "archive": "bold #a98813",
                "document": "bold #c4c7d1",
                "executable": "bold #388a3a",
                "symlink": "bold #2d65ca",
                "cursor": "#a98813",
                "hint": "#52545a",
                "cancel": "#c84739",
                "confirm": "#388a3a",
                "file_fg": "#c4c7d1",
                "file_bg": "#181819",
                "sidebar_title": "bold #8434a4",
                "sidebar_divider": "#2a2b2c",
                "help_menu_hotkey": "#a98813",
                "help_menu_title": "bold #2d65ca",
                "gradient": ["#c84739", "#a98813", "#388a3a"],
                "directory_icon": "#2d65ca",
            },

            # Monokai theme - Sublime Text inspired
            "monokai": {
                "header": "bold #F8F8F2 on #49483E",
                "footer": "#F8F8F2 on #75715E",
                "border_active": "#A6E22E",
                "border_inactive": "#75715E",
                "background": "#272822",
                "file": "#F8F8F2",
                "directory": "bold #66D9EF",
                "selected": "#272822 on #A6E22E",
                "current": "#272822 on #E6DB74",
                "current_selected": "#272822 on #F92672",
                "error": "bold #F92672",
                "success": "bold #A6E22E",
                "warning": "bold #E6DB74",
                "info": "bold #66D9EF",
                "image": "bold #AE81FF",
                "video": "bold #FD971F",
                "audio": "bold #F92672",
                "code": "bold #A6E22E",
                "archive": "bold #E6DB74",
                "document": "bold #66D9EF",
                "executable": "bold #F92672",
                "symlink": "bold #66D9EF",
                "cursor": "#A6E22E",
                "hint": "#75715E",
                "cancel": "#F92672",
                "confirm": "#A6E22E",
                "file_fg": "#F8F8F2",
                "file_bg": "#272822",
                "sidebar_title": "bold #AE81FF",
                "sidebar_divider": "#49483E",
                "help_menu_hotkey": "#E6DB74",
                "help_menu_title": "bold #66D9EF",
                "gradient": ["#F92672", "#FD971F", "#E6DB74"],
                "directory_icon": "#66D9EF",
            },

            # Nord theme - Arctic, north-bluish color palette
            "nord": {
                "header": "bold #ECEFF4 on #434C5E",
                "footer": "#ECEFF4 on #5E81AC",
                "border_active": "#88C0D0",
                "border_inactive": "#4C566A",
                "background": "#2E3440",
                "file": "#ECEFF4",
                "directory": "bold #81A1C1",
                "selected": "#2E3440 on #A3BE8C",
                "current": "#2E3440 on #EBCB8B",
                "current_selected": "#2E3440 on #B48EAD",
                "error": "bold #BF616A",
                "success": "bold #A3BE8C",
                "warning": "bold #EBCB8B",
                "info": "bold #81A1C1",
                "image": "bold #B48EAD",
                "video": "bold #5E81AC",
                "audio": "bold #D08770",
                "code": "bold #A3BE8C",
                "archive": "bold #EBCB8B",
                "document": "bold #81A1C1",
                "executable": "bold #BF616A",
                "symlink": "bold #88C0D0",
                "cursor": "#88C0D0",
                "hint": "#4C566A",
                "cancel": "#BF616A",
                "confirm": "#A3BE8C",
                "file_fg": "#ECEFF4",
                "file_bg": "#2E3440",
                "sidebar_title": "bold #B48EAD",
                "sidebar_divider": "#434C5E",
                "help_menu_hotkey": "#EBCB8B",
                "help_menu_title": "bold #81A1C1",
                "gradient": ["#BF616A", "#D08770", "#EBCB8B"],
                "directory_icon": "#81A1C1",
            },

            # OneDark
            "onedark": {
                "header": "bold #abb2bf on #3a4048",
                "footer": "#abb2bf on #4b5263",
                "border_active": "#61afef",
                "border_inactive": "#3a4048",
                "background": "#282c34",
                "file": "#abb2bf",
                "directory": "bold #61afef",
                "selected": "#282c34 on #98c379",
                "current": "#282c34 on #e5c07b",
                "current_selected": "#282c34 on #e06c75",
                "error": "bold #e06c75",
                "success": "bold #98c379",
                "warning": "bold #e5c07b",
                "info": "bold #61afef",
                "image": "bold #c678dd",
                "video": "bold #61afef",
                "audio": "bold #e06c75",
                "code": "bold #98c379",
                "archive": "bold #e5c07b",
                "document": "bold #abb2bf",
                "executable": "bold #98c379",
                "symlink": "bold #56b6c2",
                "cursor": "#61afef",
                "hint": "#5c6370",
                "cancel": "#e06c75",
                "confirm": "#98c379",
                "file_fg": "#abb2bf",
                "file_bg": "#282c34",
                "sidebar_title": "bold #c678dd",
                "sidebar_divider": "#3a4048",
                "help_menu_hotkey": "#e5c07b",
                "help_menu_title": "bold #61afef",
                "gradient": ["#e06c75", "#e5c07b", "#98c379"],
                "directory_icon": "#61afef",
            },

            # Poimandres
            "poimandres": {
                "header": "bold #a6accd on #2c3040",
                "footer": "#a6accd on #3a4055",
                "border_active": "#72f1b8",
                "border_inactive": "#525875",
                "background": "#1b1e28",
                "file": "#a6accd",
                "directory": "bold #36a3d9",
                "selected": "#1b1e28 on #5de4c7",
                "current": "#1b1e28 on #fffac2",
                "current_selected": "#1b1e28 on #ff7597",
                "error": "bold #ff7597",
                "success": "bold #5de4c7",
                "warning": "bold #fffac2",
                "info": "bold #36a3d9",
                "image": "bold #ff7597",
                "video": "bold #36a3d9",
                "audio": "bold #ff7597",
                "code": "bold #5de4c7",
                "archive": "bold #fffac2",
                "document": "bold #a6accd",
                "executable": "bold #5de4c7",
                "symlink": "bold #72f1b8",
                "cursor": "#72f1b8",
                "hint": "#525875",
                "cancel": "#ff7597",
                "confirm": "#5de4c7",
                "file_fg": "#a6accd",
                "file_bg": "#1b1e28",
                "sidebar_title": "bold #ff7597",
                "sidebar_divider": "#2c3040",
                "help_menu_hotkey": "#fffac2",
                "help_menu_title": "bold #36a3d9",
                "gradient": ["#ff7597", "#fffac2", "#5de4c7"],
                "directory_icon": "#36a3d9",
            },

            # Rosé Pine
            "rose-pine": {
                "header": "bold #e0def4 on #2a273f",
                "footer": "#e0def4 on #403d52",
                "border_active": "#ebbcba",
                "border_inactive": "#6e6a86",
                "background": "#191724",
                "file": "#e0def4",
                "directory": "bold #31748f",
                "selected": "#191724 on #9ccfd8",
                "current": "#191724 on #f6c177",
                "current_selected": "#191724 on #eb6f92",
                "error": "bold #eb6f92",
                "success": "bold #9ccfd8",
                "warning": "bold #f6c177",
                "info": "bold #31748f",
                "image": "bold #c4a7e7",
                "video": "bold #31748f",
                "audio": "bold #eb6f92",
                "code": "bold #9ccfd8",
                "archive": "bold #f6c177",
                "document": "bold #e0def4",
                "executable": "bold #9ccfd8",
                "symlink": "bold #ebbcba",
                "cursor": "#ebbcba",
                "hint": "#6e6a86",
                "cancel": "#eb6f92",
                "confirm": "#9ccfd8",
                "file_fg": "#e0def4",
                "file_bg": "#191724",
                "sidebar_title": "bold #c4a7e7",
                "sidebar_divider": "#2a273f",
                "help_menu_hotkey": "#f6c177",
                "help_menu_title": "bold #31748f",
                "gradient": ["#eb6f92", "#f6c177", "#9ccfd8"],
                "directory_icon": "#31748f",
            },

            # Sugarplum
            "sugarplum": {
                "header": "bold #f2e8f4 on #3a2d40",
                "footer": "#f2e8f4 on #4d3c55",
                "border_active": "#a475dd",
                "border_inactive": "#6e5a78",
                "background": "#2b202f",
                "file": "#f2e8f4",
                "directory": "bold #82aaff",
                "selected": "#2b202f on #c792ea",
                "current": "#2b202f on #ffb8d1",
                "current_selected": "#2b202f on #a475dd",
                "error": "bold #ff8080",
                "success": "bold #c3e88d",
                "warning": "bold #ffcb6b",
                "info": "bold #82aaff",
                "image": "bold #ffb8d1",
                "video": "bold #82aaff",
                "audio": "bold #ffb8d1",
                "code": "bold #c3e88d",
                "archive": "bold #ffcb6b",
                "document": "bold #f2e8f4",
                "executable": "bold #c3e88d",
                "symlink": "bold #89ddff",
                "cursor": "#a475dd",
                "hint": "#6e5a78",
                "cancel": "#ff8080",
                "confirm": "#c3e88d",
                "file_fg": "#f2e8f4",
                "file_bg": "#2b202f",
                "sidebar_title": "bold #a475dd",
                "sidebar_divider": "#3a2d40",
                "help_menu_hotkey": "#ffcb6b",
                "help_menu_title": "bold #82aaff",
                "gradient": ["#a475dd", "#ffb8d1", "#82aaff"],
                "directory_icon": "#82aaff",
            },

            # Tokyonight
            "tokyonight": {
                "header": "bold #c0caf5 on #292e42",
                "footer": "#c0caf5 on #3b4261",
                "border_active": "#7aa2f7",
                "border_inactive": "#414868",
                "background": "#1a1b26",
                "file": "#c0caf5",
                "directory": "bold #7aa2f7",
                "selected": "#1a1b26 on #9ece6a",
                "current": "#1a1b26 on #e0af68",
                "current_selected": "#1a1b26 on #f7768e",
                "error": "bold #f7768e",
                "success": "bold #9ece6a",
                "warning": "bold #e0af68",
                "info": "bold #7aa2f7",
                "image": "bold #bb9af7",
                "video": "bold #7dcfff",
                "audio": "bold #f7768e",
                "code": "bold #9ece6a",
                "archive": "bold #e0af68",
                "document": "bold #c0caf5",
                "executable": "bold #9ece6a",
                "symlink": "bold #7dcfff",
                "cursor": "#7aa2f7",
                "hint": "#414868",
                "cancel": "#f7768e",
                "confirm": "#9ece6a",
                "file_fg": "#c0caf5",
                "file_bg": "#1a1b26",
                "sidebar_title": "bold #bb9af7",
                "sidebar_divider": "#292e42",
                "help_menu_hotkey": "#e0af68",
                "help_menu_title": "bold #7aa2f7",
                "gradient": ["#f7768e", "#e0af68", "#9ece6a"],
                "directory_icon": "#7aa2f7",
            },
        }

    def get_style(self, element: str, panel_active: bool = True) -> str:
        """Get style for UI element"""
        # Handle ThemeConfig object or string
        if hasattr(self.current_theme, 'name'):
            theme_name = self.current_theme.name
        else:
            theme_name = str(self.current_theme)

        if theme_name not in self.themes:
            theme_name = "default"

        theme = self.themes[theme_name]

        # Handle border styles based on panel state
        if element == "border":
            return theme.get("border_active" if panel_active else "border_inactive", "#808080")

        return theme.get(element, "white")

    def get_file_style(self, file_type: str, is_selected: bool = False, is_current: bool = False) -> str:
        """Get style for file type with state indicators"""
        theme_name = self.current_theme.name if hasattr(self.current_theme, 'name') else self.current_theme
        if theme_name not in self.themes:
            theme_name = "default"

        theme = self.themes[theme_name]

        # Priority: current + selected > current > selected > normal
        if is_current and is_selected:
            return theme.get("current_selected", "white on blue")
        elif is_current:
            return theme.get("current", "white on blue")
        elif is_selected:
            return theme.get("selected", "white on green")

        # Return file type specific style
        file_type_map = {
            "directory": "directory",
            "image": "image",
            "video": "video",
            "audio": "audio",
            "code": "code",
            "archive": "archive",
            "document": "document",
            "executable": "executable",
            "symlink": "symlink"
        }

        style_key = file_type_map.get(file_type, "file")
        return theme.get(style_key, "white")

    def set_theme(self, theme_name: str):
        """Set current theme"""
        if theme_name in self.themes:
            if hasattr(self.current_theme, 'name'):
                self.current_theme.name = theme_name
            else:
                self.current_theme = theme_name
            self.config.update_theme(theme_name)

    def get_available_themes(self) -> list:
        """Get list of available themes"""
        return list(self.themes.keys())

    def get_file_icon(self, file_type: str, file_name: str = "", is_dir: bool = False, is_symlink: bool = False) -> str:
        """Get beautiful unicode icons for file types"""
        if is_symlink:
            return "🔗"

        if is_dir:
            # Special directory icons
            dir_icons = {
                "home": "🏠", "documents": "📚", "downloads": "📥", "desktop": "🖥️",
                "pictures": "🖼️", "music": "🎵", "videos": "🎬", "public": "🌐",
                ".git": "📦", "node_modules": "📦", "__pycache__": "🗄️",
                ".vscode": "💻", ".config": "⚙️", "bin": "⚙️", "src": "📁",
                "test": "🧪", "tests": "🧪", "docs": "📖", "assets": "🎨"
            }

            name_lower = file_name.lower()
            for key, icon in dir_icons.items():
                if key in name_lower:
                    return icon

            # Default directory icons
            if file_name.startswith('.'):
                return "📁"  # Hidden directory
            return "📂"  # Regular directory

        # File type icons
        file_icons = {
            # Programming languages
            "py": "🐍", "js": "🟨", "ts": "🔷", "jsx": "⚛️", "tsx": "⚛️",
            "java": "☕", "cpp": "⚡", "c": "⚡", "h": "⚡", "hpp": "⚡",
            "rs": "🦀", "go": "🐹", "php": "🐘", "rb": "💎", "swift": "🍎",
            "kt": "🎯", "scala": "🔺", "clj": "🔵", "hs": "λ", "elm": "🌳",
            "dart": "🎯", "r": "📊", "matlab": "📊", "jl": "🔴",

            # Web technologies
            "html": "🌐", "htm": "🌐", "css": "🎨", "scss": "🎨", "sass": "🎨",
            "less": "🎨", "vue": "💚", "svelte": "🧡", "angular": "🔴",

            # Data formats
            "json": "📋", "yaml": "📄", "yml": "📄", "xml": "📄", "csv": "📊",
            "tsv": "📊", "sql": "🗃️", "db": "🗃️", "sqlite": "🗃️",

            # Images
            "jpg": "🖼️", "jpeg": "🖼️", "png": "🖼️", "gif": "🎞️", "svg": "🎨",
            "bmp": "🖼️", "webp": "🖼️", "ico": "🔲", "tiff": "🖼️", "psd": "🎨",
            "ai": "🎨", "sketch": "🎨", "fig": "🎨", "xd": "🎨",

            # Videos
            "mp4": "🎬", "avi": "🎬", "mkv": "🎬", "mov": "🎬", "wmv": "🎬",
            "flv": "🎬", "webm": "🎬", "m4v": "🎬", "3gp": "📱",

            # Audio
            "mp3": "🎵", "wav": "🎵", "flac": "🎵", "aac": "🎵", "ogg": "🎵",
            "m4a": "🎵", "wma": "🎵", "opus": "🎵",

            # Documents
            "pdf": "📕", "doc": "📘", "docx": "📘", "xls": "📗", "xlsx": "📗",
            "ppt": "📙", "pptx": "📙", "odt": "📄", "ods": "📊", "odp": "📊",
            "rtf": "📄", "tex": "📜", "md": "📝", "txt": "📄",

            # Archives
            "zip": "📦", "rar": "📦", "7z": "📦", "tar": "📦", "gz": "📦",
            "bz2": "📦", "xz": "📦", "deb": "📦", "rpm": "📦", "dmg": "💿",
            "iso": "💿", "img": "💿",

            # Executables
            "exe": "⚙️", "msi": "⚙️", "app": "📱", "deb": "📦", "rpm": "📦",
            "appimage": "📱", "flatpak": "📱", "snap": "📱",

            # Shell scripts
            "sh": "🐚", "bash": "🐚", "zsh": "🐚", "fish": "🐚", "csh": "🐚",
            "bat": "⚙️", "cmd": "⚙️", "ps1": "💙",

            # Configuration
            "conf": "⚙️", "config": "⚙️", "ini": "⚙️", "cfg": "⚙️",
            "env": "🔧", "gitignore": "🙈", "gitconfig": "🔧", "editorconfig": "🔧",
            "dockerfile": "🐳", "docker-compose": "🐳", "makefile": "🔨",

            # Fonts
            "ttf": "🔤", "otf": "🔤", "woff": "🔤", "woff2": "🔤", "eot": "🔤",

            # Certificates
            "pem": "🔐", "key": "🔑", "crt": "🔐", "cer": "🔐", "p12": "🔐",

            # Logs
            "log": "📜", "logs": "📜",

            # Temporary files
            "tmp": "🗂️", "temp": "🗂️", "cache": "🗄️", "bak": "💾", "backup": "💾",
        }

        # Get extension
        if '.' in file_name:
            ext = file_name.split('.')[-1].lower()
            if ext in file_icons:
                return file_icons[ext]

        # Check for specific file names
        name_lower = file_name.lower()
        special_files = {
            "readme": "📖", "license": "📜", "changelog": "📋", "makefile": "🔨",
            "dockerfile": "🐳", "vagrantfile": "📦", "procfile": "⚙️",
            "gemfile": "💎", "package.json": "📦", "composer.json": "🎼",
            "requirements.txt": "📋", "setup.py": "🐍", "main.py": "🐍",
            "index.html": "🌐", "index.js": "🟨", "app.js": "🟨"
        }

        for pattern, icon in special_files.items():
            if pattern in name_lower:
                return icon

        # Default based on file type
        if file_type == "executable":
            return "⚙️"
        elif file_type == "code":
            return "💻"
        elif file_type == "image":
            return "🖼️"
        elif file_type == "video":
            return "🎬"
        elif file_type == "audio":
            return "🎵"
        elif file_type == "archive":
            return "📦"
        elif file_type == "document":
            return "📄"

        return "📄"  # Default file icon

    def get_size_color(self, size: int) -> str:
        """Get color for file size based on size"""
        theme_name = self.current_theme.name if hasattr(self.current_theme, 'name') else self.current_theme
        if theme_name not in self.themes:
            theme_name = "default"

        if size < 1024:  # < 1KB
            return "dim white"
        elif size < 1024 * 1024:  # < 1MB
            return "green"
        elif size < 1024 * 1024 * 10:  # < 10MB
            return "yellow"
        elif size < 1024 * 1024 * 100:  # < 100MB
            return "orange"
        else:  # >= 100MB
            return "red"

    def format_file_size(self, size: int) -> str:
        """Format file size with beautiful colors"""
        color = self.get_size_color(size)

        if size < 1024:
            return f"[{color}]{size} B[/{color}]"

        size_float = float(size)
        for unit in ['KB', 'MB', 'GB', 'TB']:
            size_float /= 1024.0
            if size_float < 1024.0:
                return f"[{color}]{size_float:.1f} {unit}[/{color}]"

        return f"[red]{size_float:.1f} PB[/red]"

    def get_permission_style(self, permissions: str) -> str:
        """Get style for file permissions"""
        if permissions.startswith('d'):
            return "bold blue"  # Directory
        elif 'x' in permissions[1:4]:  # Owner executable
            return "bold green"  # Executable
        elif permissions[1] == 'r' and permissions[2] == 'w':
            return "yellow"  # Read-write
        elif permissions[1] == 'r':
            return "white"  # Read-only
        else:
            return "dim red"  # No permissions
