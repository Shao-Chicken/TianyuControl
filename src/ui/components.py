"""
UI组件模块
"""
from PyQt5.QtWidgets import (QLabel, QGroupBox, QVBoxLayout, QHBoxLayout,
                           QPushButton, QComboBox, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QImage
import math
from src.utils.i18n import i18n
import os

class LabelPair:
    """标签对组件"""
    def __init__(self, key, value=None, value_class='medium-text'):
        self.layout = QHBoxLayout()
        self.key = key
        
        self.label = QLabel(f"{i18n.get_text(key)}:")
        self.label.setProperty('class', 'label-title')
        
        self.value_label = QLabel(value if value else '')
        self.value_label.setProperty('class', value_class)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.value_label)
        
        # 设置布局属性
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

    def set_value(self, value):
        """设置值"""
        self.value_label.setText(str(value))

    def update_text(self):
        """更新文本"""
        self.label.setText(f"{i18n.get_text(self.key)}:")

    def get_layout(self):
        """获取布局"""
        return self.layout

class DeviceControl:
    """设备控制组件"""
    def __init__(self, device_id, name):
        self.layout = QHBoxLayout()
        self.device_id = device_id
        
        self.label = QLabel(name)
        self.label.setProperty('class', 'label-title')
        
        self.combo = QComboBox()
        self.combo.addItems(["COM1", "COM2", "COM3"])
        
        self.buttons = []
        for i in range(1, 4):
            btn = QPushButton(str(i))
            btn.setProperty('class', 'square-button')
            btn.setFixedSize(32, 32)
            self.buttons.append(btn)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.combo)
        for btn in self.buttons:
            self.layout.addWidget(btn)
            
        # 设置布局属性
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

    def update_text(self):
        """更新文本"""
        self.label.setText(i18n.get_text(self.device_id))

    def get_layout(self):
        """获取布局"""
        return self.layout

class InfoGroup:
    """信息组组件"""
    def __init__(self, title, items=None):
        self.title = title
        self.group = QGroupBox(i18n.get_text(title))
        self.layout = QVBoxLayout()
        self.pairs = {}
        
        if items:
            for key, value in items:
                pair = LabelPair(key, value)
                self.pairs[key] = pair
                self.layout.addLayout(pair.get_layout())
        
        self.group.setLayout(self.layout)
        
        # 设置布局属性
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

    def add_item(self, key, value, value_class='medium-text'):
        """添加项目"""
        pair = LabelPair(key, value, value_class)
        self.pairs[key] = pair
        self.layout.addLayout(pair.get_layout())

    def update_text(self):
        """更新文本"""
        self.group.setTitle(i18n.get_text(self.title))
        for pair in self.pairs.values():
            pair.update_text()

    def get_widget(self):
        """获取组件"""
        return self.group

class ThemeButton:
    """主题按钮组件"""
    def __init__(self, text, icon=None):
        self.button = QPushButton(text)
        self.button.setProperty('class', 'theme-button')
        self.button.setFixedHeight(32)
        if icon:
            self.button.setText(f"{icon} {text}")

    def get_widget(self):
        """获取组件"""
        return self.button

class AngleVisualizer(QWidget):
    """角度可视化组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dec_angle = 0  # 赤纬角度
        self.rotator_angle = 0  # 消旋器角度
        self.background_image = None  # 背景星图
        self.setMinimumSize(300, 300)  # 增大最小尺寸
        self.setMaximumSize(400, 400)  # 增大最大尺寸

    def set_background(self, image_path):
        """设置背景星图"""
        if image_path and os.path.exists(image_path):
            self.background_image = QImage(image_path)
            if not self.background_image.isNull():
                self.background_image = self.background_image.scaled(
                    self.width(), self.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            self.update()

    def set_angles(self, dec_angle, rotator_angle):
        """设置角度值"""
        self.dec_angle = dec_angle
        self.rotator_angle = rotator_angle
        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 计算中心点和大小
        center_x = self.width() / 2
        center_y = self.height() / 2
        size = min(self.width(), self.height()) - 20

        # 绘制背景星图
        if self.background_image and not self.background_image.isNull():
            scaled_image = self.background_image.scaled(
                self.width(), self.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            x = (self.width() - scaled_image.width()) // 2
            y = (self.height() - scaled_image.height()) // 2
            painter.drawImage(x, y, scaled_image)
        else:
            # 如果没有背景图，绘制灰色背景
            painter.fillRect(0, 0, self.width(), self.height(), QColor(240, 240, 240))

        # 设置半透明效果
        painter.setOpacity(0.7)

        # 绘制赤纬参考矩形（垂直）
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.dec_angle)
        pen = QPen(QColor(0, 0, 255))  # 蓝色
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(-20, -size/2, 40, size)
        # 绘制标记箭头
        painter.drawLine(0, -size/2-10, -10, -size/2+10)
        painter.drawLine(0, -size/2-10, 10, -size/2+10)
        painter.restore()

        # 绘制画幅矩形（根据消旋器角度旋转）
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.rotator_angle)
        pen = QPen(QColor(255, 0, 0))  # 红色
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 200, 200, 50)))  # 淡红色半透明填充
        painter.drawRect(-30, -size/2, 60, size)
        # 绘制标记箭头
        painter.drawLine(0, -size/2-10, -10, -size/2+10)
        painter.drawLine(0, -size/2-10, 10, -size/2+10)
        painter.restore()

        # 绘制夹角弧线
        painter.save()
        painter.translate(center_x, center_y)
        pen = QPen(QColor(0, 255, 0))  # 绿色
        pen.setWidth(2)
        painter.setPen(pen)
        radius = 50
        start_angle = min(self.dec_angle, self.rotator_angle) * 16
        span_angle = (max(self.dec_angle, self.rotator_angle) - min(self.dec_angle, self.rotator_angle)) * 16
        painter.drawArc(-radius, -radius, radius*2, radius*2, start_angle, span_angle)
        painter.restore() 