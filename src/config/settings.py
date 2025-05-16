"""
全局配置文件
"""

# 望远镜基本信息
TELESCOPE_CONFIG = {
    'latitude': 38.614595,
    'longitude': 93.897782,
    'altitude': 4300,
    'aperture': '1m',
    'field_of_view': 'xx'
}

# 主题配置
THEMES = {
    'light': {
        'background': '#f0f0f0',
        'text': '#333333',
        'border': '#cccccc',
        'button': '#e0e0e0',
        'button_hover': '#d0d0d0',
        'title': '#666666'
    },
    'dark': {
        'background': '#1a1a1a',
        'text': '#e0e0e0',
        'border': '#404040',
        'button': '#404040',
        'button_hover': '#505050',
        'title': '#ffffff'
    },
    'red': {
        'background': '#1a0000',
        'text': '#ff9999',
        'border': '#400000',
        'button': '#400000',
        'button_hover': '#500000',
        'title': '#ff6666'
    }
}

# 字体大小配置
FONT_SIZES = {
    'small': 14,          # 次要信息（如提示文本）
    'normal': 16,         # 普通文本
    'medium': 20,         # 重要数值
    'large': 72,          # 时间显示
    'title': 18,          # 标签标题
    'group_title': 20     # 组标题
}

# 布局配置
LAYOUT_CONFIG = {
    'window_margin': 20,           # 窗口边距
    'content_spacing': 20,         # 主要内容间距
    'group_margin': 15,            # 组件内边距
    'group_spacing': 12,           # 组件内元素间距
    'button_padding': 10,          # 按钮内边距
    'label_spacing': 8,            # 标签间距
    'section_spacing': 18,         # 分区间距
    'header_margin': 10,           # 顶部按钮区域边距
    'widget_spacing': 8            # 小部件间距
}

# 串口配置
SERIAL_PORTS = ["COM1", "COM2", "COM3"]

# 设备列表
DEVICES = [
    ('mount', "赤道仪"),
    ('focuser', "电调焦"),
    ('rotator', "消旋器"),
    ('weather', "气象站")
]

# 时区配置
TIMEZONE = "Asia/Shanghai" 