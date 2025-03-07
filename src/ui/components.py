"""
UI组件模块
"""
from PyQt5.QtWidgets import (QLabel, QGroupBox, QVBoxLayout, QHBoxLayout,
                           QPushButton, QComboBox, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QImage
import math
from src.utils.i18n import i18n
from api_client import AlpacaClient
from src.services.telescope_monitor import TelescopeMonitor
from utils import load_config
import os

class DeviceSignals(QObject):
    """设备信号类"""
    location_updated = pyqtSignal(float, float, float)  # 经度、纬度、海拔
    coordinates_updated = pyqtSignal(float, float, float, float)  # 赤经、赤纬、高度角、方位角
    status_updated = pyqtSignal(dict)  # 望远镜状态信号

class LabelPair:
    """标签对组件"""
    def __init__(self, key, value=None, value_class='status-text'):
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
        self.is_connected = False
        self.signals = DeviceSignals()
        
        # 根据设备类型创建对应的 API 客户端
        config = load_config()
        # 修复 device_id 映射
        device_type = device_id
        if device_id == 'mount':
            device_type = 'telescope'
        elif device_id == 'weather':
            device_type = 'observingconditions'
        device_config = config.get("devices", {}).get(device_type, {})
        api_url = device_config.get("api_url")
        self.client = AlpacaClient(base_url=api_url)
        
        # 创建监控线程（用于望远镜、电调焦、消旋器和气象站设备）
        self.telescope_monitor = None
        if device_id in ['mount', 'focuser', 'rotator', 'weather']:
            device_type = 'telescope' if device_id == 'mount' else (
                'observingconditions' if device_id == 'weather' else device_id
            )
            self.telescope_monitor = TelescopeMonitor(device_type=device_type)
            # 连接监控线程的信号
            if device_id == 'mount':
                self.telescope_monitor.coordinates_updated.connect(
                    self.signals.coordinates_updated.emit
                )
                self.telescope_monitor.status_updated.connect(
                    self.signals.status_updated.emit
                )
            elif device_id == 'focuser':
                # 连接电调焦状态更新信号
                self.telescope_monitor.focuser_updated.connect(self.update_focuser_status)
            elif device_id == 'rotator':
                # 连接消旋器状态更新信号
                self.telescope_monitor.rotator_updated.connect(self.update_rotator_status)
            elif device_id == 'weather':
                # 连接气象站数据更新信号
                self.telescope_monitor.weather_updated.connect(self.update_weather_info)
            
            # 连接设备列表更新信号
            self.telescope_monitor.devices_updated.connect(self.update_devices)
        
        self.label = QLabel(name)
        self.label.setProperty('class', 'label-title')
        
        # 使用统一的下拉菜单和连接按钮界面
        if device_id in ['mount', 'focuser', 'rotator', 'weather']:
            self.combo = QComboBox()
            self.combo.setMinimumWidth(200)  # 设置最小宽度以便显示设备名称
            self.combo.setMaximumWidth(300)  # 设置最大宽度，避免过长
            self.combo.setStyleSheet("QComboBox { min-height: 25px; }")  # 确保高度足够
            
            self.connect_button = QPushButton(i18n.get_text("connected") if self.is_connected else i18n.get_text("disconnected"))
            self.connect_button.setProperty('class', 'primary-button')
            self.connect_button.clicked.connect(self.toggle_connection)
            self.connect_button.setMinimumWidth(100)  # 设置最小宽度
            
            self.layout.addWidget(self.label)
            self.layout.addWidget(self.combo, 1)  # 添加拉伸因子，使下拉菜单占据更多空间
            self.layout.addWidget(self.connect_button)
            
            # 打印布局信息，用于调试
            print(f"设备控制组件 {device_id} 布局: 标签宽度={self.label.sizeHint().width()}, 下拉菜单宽度={self.combo.sizeHint().width()}, 按钮宽度={self.connect_button.sizeHint().width()}")
        else:  # 其他设备保持原有的三按钮设计
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
        
        # 存储设备列表
        self.devices = []

    def update_devices(self, devices):
        """更新设备列表"""
        print(f"\n正在更新 {self.device_id} 的设备列表...")
        print(f"收到的设备列表: {devices}")
        
        if self.device_id in ['mount', 'focuser', 'rotator', 'weather']:
            # 过滤当前设备类型的设备
            device_type = {
                'mount': 'Telescope',
                'focuser': 'Focuser',
                'rotator': 'Rotator',
                'weather': 'ObservingConditions'
            }[self.device_id]
            
            # 过滤并确保每个设备都有必要的字段
            filtered_devices = []
            for d in devices:
                if d.get('DeviceType') == device_type:
                    device = {
                        'DeviceName': d.get('DeviceName', 'Unknown Device'),
                        'DeviceType': d.get('DeviceType', device_type),
                        'DeviceNumber': d.get('DeviceNumber', 0),
                        'ApiVersion': d.get('ApiVersion', '1.0')
                    }
                    filtered_devices.append(device)
            
            print(f"过滤后的设备列表: {filtered_devices}")
            
            self.devices = filtered_devices
            self.combo.clear()
            
            # 添加设备到下拉菜单
            for device in filtered_devices:
                device_name = device['DeviceName']
                device_type = device['DeviceType']
                device_number = device['DeviceNumber']
                api_version = device['ApiVersion']
                display_name = f"{device_name} ({device_type} #{device_number})"
                print(f"添加设备到下拉菜单: {display_name}")
                self.combo.addItem(display_name, device)
            
            # 如果没有设备，添加一个默认选项
            if not filtered_devices:
                default_device = {
                    'DeviceName': 'ASCOM Observing Conditions Simulator',
                    'DeviceType': device_type,
                    'DeviceNumber': 0,
                    'ApiVersion': '1.0'
                }
                display_name = f"{default_device['DeviceName']} ({device_type} #0)"
                print(f"添加默认设备到下拉菜单: {display_name}")
                self.combo.addItem(display_name, default_device)
            
            print(f"下拉菜单项数: {self.combo.count()}")
            
            # 如果有设备，默认选择第一个
            if self.combo.count() > 0:
                self.combo.setCurrentIndex(0)

    def get_telescope_location(self):
        """获取望远镜位置信息"""
        if not self.is_connected or self.device_id != 'mount':
            return
            
        # 获取当前选中的设备信息
        current_index = self.combo.currentIndex()
        if current_index >= 0:
            device_data = self.combo.itemData(current_index)
            if device_data:
                device_number = device_data['DeviceNumber']
                # 获取位置信息
                longitude = self.client.get('telescope', device_number, 'sitelongitude')
                latitude = self.client.get('telescope', device_number, 'sitelatitude')
                elevation = self.client.get('telescope', device_number, 'siteelevation')
                
                if all(v is not None for v in [longitude, latitude, elevation]):
                    print(f"获取到位置信息：经度 {longitude}°, 纬度 {latitude}°, 海拔 {elevation}m")
                    # 发送信号更新位置信息
                    self.signals.location_updated.emit(longitude, latitude, elevation)
                    return True
        return False

    def toggle_connection(self):
        """切换连接状态"""
        if self.device_id not in ['mount', 'focuser', 'rotator', 'weather']:  # 添加 'weather' 到支持的设备类型
            return
            
        self.is_connected = not self.is_connected
        self.connect_button.setText(i18n.get_text("connected") if self.is_connected else i18n.get_text("disconnected"))
        
        # 获取当前选中的设备信息
        current_index = self.combo.currentIndex()
        if current_index >= 0:
            device_data = self.combo.itemData(current_index)
            if device_data:
                device_number = device_data['DeviceNumber']
                if self.is_connected:
                    print(f"连接到设备: {device_data['DeviceName']}")
                    # 启动监控线程
                    if self.telescope_monitor:
                        self.telescope_monitor.set_device(device_number)
                        self.telescope_monitor.start()
                else:
                    print(f"断开设备: {device_data['DeviceName']}")
                    # 停止监控线程并标记为断开连接
                    if self.telescope_monitor:
                        self.telescope_monitor.disconnect_device()

    def update_text(self):
        """更新文本"""
        self.label.setText(i18n.get_text(self.device_id))
        if self.device_id == 'mount':  # 只有望远镜设备需要更新按钮文本
            self.connect_button.setText(i18n.get_text("connected") if self.is_connected else i18n.get_text("disconnected"))

    def get_layout(self):
        """获取布局"""
        return self.layout

    def update_focuser_status(self, status):
        """更新电调焦状态显示"""
        # 更新位置
        if hasattr(self, 'focuser_status'):
            self.focuser_status.pairs['position'].set_value(f"{status['position']:.1f}°")
            
            # 更新移动状态
            moving_text = i18n.get_text('moving_yes') if status['ismoving'] else i18n.get_text('moving_no')
            self.focuser_status.pairs['moving'].set_value(moving_text)
            
            # 设置移动状态的样式
            style_class = 'medium-text ' + ('status-warning' if status['ismoving'] else 'status-success')
            self.focuser_status.pairs['moving'].value_label.setProperty('class', style_class)
            self.focuser_status.pairs['moving'].value_label.style().unpolish(self.focuser_status.pairs['moving'].value_label)
            self.focuser_status.pairs['moving'].value_label.style().polish(self.focuser_status.pairs['moving'].value_label)

    def update_rotator_status(self, status):
        """更新消旋器状态显示"""
        # 更新位置
        if hasattr(self, 'rotator_status'):
            self.rotator_status.pairs['position'].set_value(f"{status['position']:.1f}°")
            
            # 更新移动状态
            moving_text = i18n.get_text('moving_yes') if status['ismoving'] else i18n.get_text('moving_no')
            self.rotator_status.pairs['moving'].set_value(moving_text)
            
            # 设置移动状态的样式
            style_class = 'medium-text ' + ('status-warning' if status['ismoving'] else 'status-success')
            self.rotator_status.pairs['moving'].value_label.setProperty('class', style_class)
            self.rotator_status.pairs['moving'].value_label.style().unpolish(self.rotator_status.pairs['moving'].value_label)
            self.rotator_status.pairs['moving'].value_label.style().polish(self.rotator_status.pairs['moving'].value_label)

    def update_weather_info(self, weather_info):
        """更新气象站数据"""
        # 实现气象站数据更新逻辑
        pass

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
        # 将所有参数转换为整数
        rect_size = int(size)
        painter.drawRect(-20, -rect_size//2, 40, rect_size)
        # 绘制标记箭头，同样确保使用整数
        arrow_y = -rect_size//2
        painter.drawLine(0, arrow_y-10, -10, arrow_y+10)
        painter.drawLine(0, arrow_y-10, 10, arrow_y+10)
        painter.restore()

        # 绘制画幅矩形（根据消旋器角度旋转）
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.rotator_angle)
        pen = QPen(QColor(255, 0, 0))  # 红色
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 200, 200, 50)))  # 淡红色半透明填充
        # 将所有参数转换为整数
        rect_size = int(size)
        painter.drawRect(-30, -rect_size//2, 60, rect_size)
        # 绘制标记箭头，同样确保使用整数
        arrow_y = -rect_size//2
        painter.drawLine(0, arrow_y-10, -10, arrow_y+10)
        painter.drawLine(0, arrow_y-10, 10, arrow_y+10)
        painter.restore()

        # 绘制夹角弧线
        painter.save()
        painter.translate(center_x, center_y)
        pen = QPen(QColor(0, 255, 0))  # 绿色
        pen.setWidth(2)
        painter.setPen(pen)
        radius = 50
        # 在 Qt 中，角度需要乘以 16（因为它使用 1/16 度作为单位）
        start_angle = int(min(self.dec_angle, self.rotator_angle) * 16)
        span_angle = int((max(self.dec_angle, self.rotator_angle) - min(self.dec_angle, self.rotator_angle)) * 16)
        painter.drawArc(-radius, -radius, radius*2, radius*2, start_angle, span_angle)
        painter.restore() 