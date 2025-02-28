"""
主题管理模块
"""
from src.config.settings import THEMES, FONT_SIZES

class ThemeManager:
    def __init__(self):
        self.current_theme = 'light'
        self.themes = THEMES
        self.font_sizes = FONT_SIZES

    def get_theme_style(self):
        """获取当前主题的样式表"""
        theme = self.themes[self.current_theme]
        return f"""
            QWidget {{
                background-color: {theme['background']};
                color: {theme['text']};
            }}
            QGroupBox {{
                border: 2px solid {theme['border']};
                border-radius: 8px;
                margin-top: 1ex;
                font-size: {self.font_sizes['normal']}px;
                padding: 20px;
                background-color: transparent;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                color: {theme['title']};
                font-size: {self.font_sizes['group_title']}px;
            }}
            QPushButton {{
                background-color: {theme['button']};
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: {self.font_sizes['normal']}px;
                color: {theme['text']};
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover']};
            }}
            QLabel {{
                background-color: transparent;
                font-size: {self.font_sizes['normal']}px;
                color: {theme['text']};
            }}
            QComboBox {{
                font-size: {self.font_sizes['normal']}px;
                padding: 8px;
                color: {theme['text']};
                background-color: {theme['button']};
            }}
            .theme-button {{
                padding: 8px 16px;
                font-size: {self.font_sizes['normal']-4}px;
                border-radius: 4px;
                margin: 4px;
                min-width: 80px;
            }}
            .info-value {{
                margin-left: 30px;
                font-size: {self.font_sizes['title']}px;
                color: {theme['text']};
            }}
            .small-text {{
                font-size: {self.font_sizes['small']}px;
                color: {theme['title']};
            }}
            .large-text {{
                font-size: {self.font_sizes['large']}px;
                color: {theme['text']};
            }}
            .medium-text {{
                font-size: {self.font_sizes['medium']}px;
                color: {theme['text']};
            }}
            .label-title {{
                font-size: {self.font_sizes['title']}px;
                color: {theme['text']};
                margin-right: 15px;
            }}
            .square-button {{
                width: 32px;
                height: 32px;
                padding: 0px;
                border-radius: 4px;
            }}
        """

    def switch_theme(self, theme_name):
        """切换主题"""
        if theme_name in self.themes:
            self.current_theme = theme_name

    def get_current_theme(self):
        """获取当前主题名称"""
        return self.current_theme

# 创建全局实例
theme_manager = ThemeManager() 