"""
主窗口模块
"""
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QImage, QPixmap
from src.ui.components import LabelPair, DeviceControl, InfoGroup, ThemeButton, AngleVisualizer
from src.utils.i18n import i18n
from src.utils.theme_manager import theme_manager
from src.services.astronomy_service import astronomy_service
from src.services.device_service import device_service
from src.services.dss_image_fetcher import DSSImageFetcher
from src.config.settings import TELESCOPE_CONFIG, DEVICES, LAYOUT_CONFIG
from utils import load_config
import os
import time

class MainWindow(QMainWindow):
    def __init__(self, telescope_devices=None):
        super().__init__()
        # 创建中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建DSS图像获取线程
        self.dss_fetcher = DSSImageFetcher()
        self.dss_fetcher.image_ready.connect(self.update_dss_image)
        
        self.init_ui(telescope_devices)
        self.init_timer()

    def init_ui(self, telescope_devices):
        """初始化UI"""
        self.setWindowTitle(i18n.get_text('telescope_monitor'))
        self.setGeometry(100, 100, 1920, 1080)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(
            LAYOUT_CONFIG['window_margin'],
            LAYOUT_CONFIG['window_margin'],
            LAYOUT_CONFIG['window_margin'],
            LAYOUT_CONFIG['window_margin']
        )
        main_layout.setSpacing(LAYOUT_CONFIG['content_spacing'])

        content_layout = QHBoxLayout()
        content_layout.setSpacing(LAYOUT_CONFIG['section_spacing'])

        # 主题切换按钮布局
        theme_layout = QHBoxLayout()
        theme_layout.setContentsMargins(
            0, 0, 0, LAYOUT_CONFIG['header_margin']
        )
        theme_layout.addStretch()

        # 语言切换按钮
        self.lang_btn = ThemeButton(i18n.get_text('language')).get_widget()
        self.lang_btn.setFixedSize(60, 32)  # 设置固定大小
        self.lang_btn.clicked.connect(self.change_language)
        theme_layout.addWidget(self.lang_btn)

        # 主题切换按钮
        self.light_btn = ThemeButton(i18n.get_text('light_mode'), '☀️').get_widget()
        self.dark_btn = ThemeButton(i18n.get_text('dark_mode'), '🌙').get_widget()
        self.red_btn = ThemeButton(i18n.get_text('red_mode'), '🔴').get_widget()

        for btn, theme in [(self.light_btn, 'light'),
                          (self.dark_btn, 'dark'),
                          (self.red_btn, 'red')]:
            btn.setFixedSize(80, 32)  # 设置固定大小
            btn.clicked.connect(lambda checked, t=theme: self.change_theme(t))
            theme_layout.addWidget(btn)

        theme_layout.setSpacing(LAYOUT_CONFIG['widget_spacing'])
        main_layout.addLayout(theme_layout)
        main_layout.addLayout(content_layout)

        # 左侧栏
        left_layout = QVBoxLayout()
        left_layout.setSpacing(LAYOUT_CONFIG['group_spacing'])
        
        # 基本信息组
        self.basic_info = InfoGroup('basic_info')
        self.basic_info.layout.setSpacing(LAYOUT_CONFIG['widget_spacing'])
        self.basic_info.add_item('aperture', TELESCOPE_CONFIG['aperture'])
        self.basic_info.add_item('fov', TELESCOPE_CONFIG['field_of_view'])
        self.basic_info.add_item('longitude', f"{TELESCOPE_CONFIG['longitude']}°")
        self.basic_info.add_item('latitude', f"{TELESCOPE_CONFIG['latitude']}°")
        self.basic_info.add_item('altitude_text', f"{TELESCOPE_CONFIG['altitude']}m")
        left_layout.addWidget(self.basic_info.get_widget())

        # 设备控制组件列表
        self.device_controls = []
        
        # 设备连接状态组
        self.device_group = InfoGroup('device_connection')
        self.device_group.layout.setSpacing(LAYOUT_CONFIG['group_spacing'])
        
        # 添加望远镜设备控制组件（新的带下拉菜单的版本）
        self.mount_control = DeviceControl('mount', i18n.get_text('mount'))
        if telescope_devices:  # 如果有设备列表，更新到下拉菜单
            self.mount_control.update_devices(telescope_devices)
        # 连接位置更新信号
        self.mount_control.signals.location_updated.connect(self.update_location_info)
        # 连接坐标更新信号
        self.mount_control.signals.coordinates_updated.connect(self.update_coordinates)
        # 连接状态更新信号
        self.mount_control.signals.status_updated.connect(self.update_telescope_status)
        # 连接设备列表更新信号
        self.mount_control.telescope_monitor.devices_updated.connect(self.mount_control.update_devices)
        self.device_group.layout.addLayout(self.mount_control.get_layout())
        self.device_controls.append(self.mount_control)
        
        # 添加其他设备控制组件
        other_devices = [
            ('focuser', 'focuser'),
            ('rotator', 'rotator'),
            ('weather', 'weather')
        ]
        for device_id, name in other_devices:
            device_control = DeviceControl(device_id, i18n.get_text(device_id))
            if device_id == 'focuser':
                # 连接电调焦状态更新信号
                device_control.telescope_monitor.focuser_updated.connect(self.update_focuser_status)
                # 连接设备列表更新信号
                device_control.telescope_monitor.devices_updated.connect(device_control.update_devices)
                # 如果有设备列表，更新到下拉菜单
                if telescope_devices:
                    device_control.update_devices(telescope_devices)
            elif device_id == 'rotator':
                # 连接消旋器状态更新信号
                device_control.telescope_monitor.rotator_updated.connect(self.update_rotator_status)
                # 连接设备列表更新信号
                device_control.telescope_monitor.devices_updated.connect(device_control.update_devices)
                # 如果有设备列表，更新到下拉菜单
                if telescope_devices:
                    device_control.update_devices(telescope_devices)
            elif device_id == 'weather':
                # 连接气象站数据更新信号
                if device_control.telescope_monitor:
                    device_control.telescope_monitor.weather_updated.connect(self.update_weather_info)
                    # 连接设备列表更新信号
                    device_control.telescope_monitor.devices_updated.connect(device_control.update_devices)
                    # 如果有设备列表，更新到下拉菜单
                    if telescope_devices:
                        device_control.update_devices(telescope_devices)
                    else:
                        # 如果没有设备列表，添加一个默认设备
                        default_devices = [{
                            'DeviceName': 'ASCOM Observing Conditions Simulator',
                            'DeviceType': 'ObservingConditions',
                            'DeviceNumber': 0,
                            'ApiVersion': '1.0'
                        }]
                        device_control.update_devices(default_devices)
            self.device_controls.append(device_control)
            self.device_group.layout.addLayout(device_control.get_layout())
        
        left_layout.addWidget(self.device_group.get_widget())

        # 中间栏
        middle_layout = QVBoxLayout()
        middle_layout.setSpacing(LAYOUT_CONFIG['section_spacing'])

        # 消旋器角度组
        self.rotator_angle_group = InfoGroup('rotator_angle_group')
        self.rotator_angle_group.layout.setSpacing(LAYOUT_CONFIG['group_spacing'])
        
        # 添加角度可视化组件
        angle_layout = QHBoxLayout()
        
        # 左侧文本信息
        text_layout = QVBoxLayout()
        self.rotator_angle_group.add_item('frame_dec_angle', '45°', 'large-text')
        for pair in self.rotator_angle_group.pairs.values():
            text_layout.addLayout(pair.get_layout())
        angle_layout.addLayout(text_layout)
        
        # 右侧可视化组件
        self.angle_visualizer = AngleVisualizer()
        angle_layout.addWidget(self.angle_visualizer)
        
        self.rotator_angle_group.layout.addLayout(angle_layout)
        middle_layout.addWidget(self.rotator_angle_group.get_widget())

        # 望远镜状态组
        self.telescope_status = InfoGroup('telescope_status')
        self.telescope_status.layout.setSpacing(LAYOUT_CONFIG['group_spacing'])
        self.telescope_status.add_item('ra', '12:00:00', 'large-text')
        self.telescope_status.add_item('dec', '+30:00:00', 'large-text')
        self.telescope_status.add_item('alt', '60°', 'medium-text')
        self.telescope_status.add_item('az', '120°', 'medium-text')
        self.telescope_status.add_item('status', i18n.get_text('status_unknown'), 'medium-text')
        middle_layout.addWidget(self.telescope_status.get_widget())

        # 相机设置组
        self.camera_settings = InfoGroup('camera_settings')
        self.camera_settings.layout.setSpacing(LAYOUT_CONFIG['widget_spacing'])
        self.camera_settings.add_item('camera_temp', '-30.0°C', 'medium-text')
        self.camera_settings.add_item('readout_mode', i18n.get_text('high_dynamic_range_mode'))
        self.camera_settings.add_item('filter_position', i18n.get_text('filter_r'))
        middle_layout.addWidget(self.camera_settings.get_widget())

        # 调焦器状态组
        self.focuser_status = InfoGroup('focuser_status')
        self.focuser_status.layout.setSpacing(LAYOUT_CONFIG['widget_spacing'])
        self.focuser_status.add_item('position', '34000/60000', 'medium-text')
        self.focuser_status.add_item('angle', '0.0°', 'medium-text')
        self.focuser_status.add_item('moving', i18n.get_text('moving_yes'))
        self.focuser_status.add_item('temperature', '-10.0°C', 'medium-text')
        self.focuser_status.add_item('last_focus', '2025-02-23 12:00:00')
        middle_layout.addWidget(self.focuser_status.get_widget())

        # 右侧栏
        right_layout = QVBoxLayout()
        right_layout.setSpacing(LAYOUT_CONFIG['section_spacing'])

        # 全天相机组
        self.all_sky_camera = InfoGroup('all_sky_camera')
        self.all_sky_camera.layout.setSpacing(LAYOUT_CONFIG['group_spacing'])
        image_label = QLabel()
        image_label.setText('<img src="C:/Users/90811/Downloads/cutout2.jpg"/>')
        image_label.setAlignment(Qt.AlignCenter)  # 居中对齐
        self.all_sky_camera.layout.addWidget(image_label)
        
        # 添加提示文本标签，不使用 LabelPair
        tip_label = QLabel(i18n.get_text('all_sky_camera_tip'))
        tip_label.setProperty('class', 'small-text')
        tip_label.setAlignment(Qt.AlignCenter)  # 居中对齐
        tip_label.setWordWrap(True)  # 允许文本换行
        self.all_sky_camera.layout.addWidget(tip_label)
        self.all_sky_camera_tip_label = tip_label
        
        right_layout.addWidget(self.all_sky_camera.get_widget())

        # 环境监测组
        self.environment = InfoGroup('environment')
        self.environment.layout.setSpacing(LAYOUT_CONFIG['widget_spacing'])
        self.environment.add_item('cloud_cover', '30%', 'medium-text')
        self.environment.add_item('dew_point', '-15.0°C', 'medium-text')
        self.environment.add_item('humidity', '50%', 'medium-text')
        self.environment.add_item('pressure', '1000hPa', 'medium-text')
        self.environment.add_item('rain', '10mm/h', 'medium-text')
        self.environment.add_item('sky_brightness', '10lux', 'medium-text')
        self.environment.add_item('sky_temperature', '-10.0°C', 'medium-text')
        self.environment.add_item('seeing', '0.5arcsec', 'medium-text')
        self.environment.add_item('air_temp', '-10.0°C', 'medium-text')
        self.environment.add_item('wind_direction', '70°', 'medium-text')
        self.environment.add_item('wind_speed', '10m/s', 'medium-text')
        self.environment.add_item('avg_wind_speed', '10m/s', 'medium-text')
        right_layout.addWidget(self.environment.get_widget())

        # 时间显示组
        self.time_group = InfoGroup('current_time')
        self.time_group.layout.setSpacing(LAYOUT_CONFIG['widget_spacing'])
        self.time_group.add_item('utc8', '', 'medium-text')
        self.time_group.add_item('sunrise_sunset', '', 'medium-text')
        self.time_group.add_item('twilight', '', 'medium-text')
        self.time_group.add_item('moon_phase', '', 'medium-text')
        self.time_group.add_item('sun_altitude', '', 'medium-text')
        right_layout.addWidget(self.time_group.get_widget())

        # 设置布局比例
        content_layout.addLayout(left_layout, 2)    # 增加左侧栏比例
        content_layout.addLayout(middle_layout, 5)  # 减小中间栏比例
        content_layout.addLayout(right_layout, 3)   # 增加右侧栏比例

        # 设置中心部件的布局
        self.central_widget.setLayout(main_layout)

        # 设置默认主题
        self.change_theme('light')

        # 连接设备监控线程信号
        if self.mount_control.telescope_monitor:
            self.mount_control.telescope_monitor.coordinates_updated.connect(self.update_coordinates)
            self.mount_control.telescope_monitor.status_updated.connect(self.update_telescope_status)
            self.mount_control.telescope_monitor.devices_updated.connect(self.mount_control.update_devices)
            
            # 连接气象站数据信号
            self.mount_control.telescope_monitor.weather_updated.connect(self.update_weather_info)

    def init_timer(self):
        """初始化定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_info)
        self.timer.start(1000)  # 每秒更新

    def change_theme(self, theme):
        """切换主题"""
        theme_manager.switch_theme(theme)
        self.setStyleSheet(theme_manager.get_theme_style())

    def change_language(self):
        """切换语言"""
        i18n.switch_language()
        self.update_all_texts()

    def update_all_texts(self):
        """更新所有文本"""
        # 更新窗口标题
        self.setWindowTitle(i18n.get_text('telescope_monitor'))

        # 更新按钮文本
        self.lang_btn.setText(i18n.get_text('language'))
        self.light_btn.setText(f"☀️ {i18n.get_text('light_mode')}")
        self.dark_btn.setText(f"🌙 {i18n.get_text('dark_mode')}")
        self.red_btn.setText(f"🔴 {i18n.get_text('red_mode')}")

        # 更新所有组件的文本
        self.basic_info.update_text()
        self.device_group.update_text()
        
        # 更新消旋器角度组
        self.rotator_angle_group.update_text()
        
        # 更新望远镜状态组的动态值
        self.telescope_status.update_text()
        self.telescope_status.pairs['status'].set_value(i18n.get_text('status_unknown'))
        
        # 更新相机设置组的动态值
        self.camera_settings.update_text()
        self.camera_settings.pairs['readout_mode'].set_value(i18n.get_text('high_dynamic_range_mode'))
        self.camera_settings.pairs['filter_position'].set_value(i18n.get_text('filter_r'))
        
        # 更新调焦器状态组的动态值
        self.focuser_status.update_text()
        self.focuser_status.pairs['moving'].set_value(i18n.get_text('moving_yes'))
        
        # 更新全天相机组的动态值
        self.all_sky_camera.update_text()
        self.all_sky_camera_tip_label.setText(i18n.get_text('all_sky_camera_tip'))
        
        self.environment.update_text()
        self.time_group.update_text()

        # 更新设备控制组件
        for device_control in self.device_controls:
            device_control.update_text()

        # 更新时间信息
        self.update_time_info()

    def calculate_frame_dec_angle(self):
        """计算框架赤纬角度"""
        try:
            # 获取当前坐标
            ra_text = self.telescope_status.pairs['ra'].value_label.text()
            dec_text = self.telescope_status.pairs['dec'].value_label.text()
            
            # 转换坐标为度数
            ra_deg = astronomy_service._parse_time_format(ra_text)
            dec_deg = astronomy_service._parse_time_format(dec_text)
            
            # 只有当坐标变化超过阈值时才更新DSS图像
            if not hasattr(self, 'last_coords') or self.last_coords is None:
                self.last_coords = (ra_deg, dec_deg)
                self.dss_fetcher.set_coordinates(ra_text, dec_text)
            else:
                last_ra, last_dec = self.last_coords
                # 如果坐标变化超过0.5度才更新
                if abs(ra_deg - last_ra) > 0.5 or abs(dec_deg - last_dec) > 0.5:
                    self.last_coords = (ra_deg, dec_deg)
                    self.dss_fetcher.set_coordinates(ra_text, dec_text)
            
            # 计算框架赤纬角度
            frame_dec_angle = dec_deg
            self.frame_dec_angle = frame_dec_angle
            
            # 更新显示
            self.rotator_angle_group.pairs['frame_dec_angle'].set_value(f"{frame_dec_angle:.6f}°")
            
            # 更新角度可视化
            self.angle_visualizer.set_angles(0, frame_dec_angle)  # 使用0度作为赤纬参考线
            
        except Exception as e:
            print(f"计算框架赤纬角度失败: {e}")

    def update_dss_image(self, image_path):
        """更新DSS图像"""
        self.angle_visualizer.set_background(image_path)

    def update_time_info(self):
        """更新时间信息"""
        # 更新时间
        time_info = astronomy_service.get_current_time()
        self.time_group.pairs['utc8'].set_value(time_info['utc8'])

        # 更新太阳信息
        sun_info = astronomy_service.get_sun_info()
        self.time_group.pairs['sunrise_sunset'].set_value(
            f"{sun_info['sunrise']} / {sun_info['sunset']}"
        )
        self.time_group.pairs['sun_altitude'].set_value(sun_info['altitude'])

        # 更新晨昏信息
        twilight_info = astronomy_service.get_twilight_info()
        self.time_group.pairs['twilight'].set_value(
            f"{twilight_info['morning']} / {twilight_info['evening']}"
        )

        # 更新月相
        moon_phase = astronomy_service.calculate_moon_phase()
        self.time_group.pairs['moon_phase'].set_value(str(moon_phase))
        
        # 每30秒更新一次角度计算和星图
        if int(time.time()) % 30 == 0:
            self.calculate_frame_dec_angle() 

    def update_location_info(self, longitude, latitude, elevation):
        """更新位置信息"""
        self.basic_info.pairs['longitude'].set_value(f"{longitude:.6f}°")
        self.basic_info.pairs['latitude'].set_value(f"{latitude:.6f}°")
        self.basic_info.pairs['altitude_text'].set_value(f"{elevation:.1f}m")

    def update_coordinates(self, ra, dec, alt, az):
        """更新望远镜坐标信息"""
        # 将赤经转换为时分秒格式
        ra_h = int(ra)
        ra_m = int((ra - ra_h) * 60)
        ra_s = int(((ra - ra_h) * 60 - ra_m) * 60)
        ra_str = f"{ra_h:02d}:{ra_m:02d}:{ra_s:02d}"
        
        # 将赤纬转换为度分秒格式
        dec_sign = '+' if dec >= 0 else '-'
        dec_abs = abs(dec)
        dec_d = int(dec_abs)
        dec_m = int((dec_abs - dec_d) * 60)
        dec_s = int(((dec_abs - dec_d) * 60 - dec_m) * 60)
        dec_str = f"{dec_sign}{dec_d:02d}:{dec_m:02d}:{dec_s:02d}"
        
        # 更新界面显示
        self.telescope_status.pairs['ra'].set_value(ra_str)
        self.telescope_status.pairs['dec'].set_value(dec_str)
        self.telescope_status.pairs['alt'].set_value(f"{alt:.1f}°")
        self.telescope_status.pairs['az'].set_value(f"{az:.1f}°") 

    def update_telescope_status(self, status):
        """更新望远镜状态"""
        if not status:
            self.telescope_status.pairs['status'].set_value('Status Unknown')
            self.telescope_status.pairs['status'].value_label.setProperty('class', 'medium-text status-normal')
            return

        # 收集所有激活的状态
        active_states = []
        if status.get('slewing'):
            active_states.append('Slewing')
        if status.get('ispulseguiding'):
            active_states.append('Guiding')
        if status.get('tracking'):
            active_states.append('Tracking')
        if status.get('atpark'):
            active_states.append('AtPark')
        if status.get('athome'):
            active_states.append('AtHome')

        # 如果没有任何状态激活，显示未知状态
        if not active_states:
            self.telescope_status.pairs['status'].set_value('Status Unknown')
            self.telescope_status.pairs['status'].value_label.setProperty('class', 'medium-text status-normal')
            return

        # 根据状态设置样式类
        style_class = 'medium-text '  # 使用 medium-text 替代 status-text
        if 'Slewing' in active_states:
            style_class += 'status-warning'
        elif 'Guiding' in active_states or 'Tracking' in active_states:
            style_class += 'status-success'
        elif 'AtHome' in active_states or 'AtPark' in active_states:
            style_class += 'status-info'
        else:
            style_class += 'status-normal'

        # 更新状态显示
        self.telescope_status.pairs['status'].set_value(', '.join(active_states))
        self.telescope_status.pairs['status'].value_label.setProperty('class', style_class)
        self.telescope_status.pairs['status'].value_label.style().unpolish(self.telescope_status.pairs['status'].value_label)
        self.telescope_status.pairs['status'].value_label.style().polish(self.telescope_status.pairs['status'].value_label)

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止DSS图像获取线程
        self.dss_fetcher.stop()
        self.dss_fetcher.wait()
        
        # 停止所有设备的监控线程
        for device_control in self.device_controls:
            if hasattr(device_control, 'telescope_monitor') and device_control.telescope_monitor:
                device_control.telescope_monitor.stop()
                device_control.telescope_monitor.wait()
        
        super().closeEvent(event) 

    def update_focuser_status(self, status):
        """更新电调焦状态显示"""
        # 更新位置
        self.focuser_status.pairs['position'].set_value(f"{status['position']}/{status['maxstep']}")
        
        # 更新温度
        self.focuser_status.pairs['temperature'].set_value(f"{status['temperature']:.1f}°C")
        
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
        # 更新调焦器状态组中的消旋器角度
        self.focuser_status.pairs['angle'].set_value(f"{status['position']:.1f}°")
        
        # 更新角度可视化
        self.angle_visualizer.set_angles(0, status['position'])

    def update_weather_info(self, weather_data):
        """更新气象站信息"""
        # 打印完整的气象站数据到控制台
        print("\n气象站数据更新:")
        for key, value in weather_data.items():
            print(f"  {key}: {value}")
        
        # 更新环境监测组中的气象数据
        if 'cloudcover' in weather_data and weather_data['cloudcover'] is not None:
            self.environment.pairs['cloud_cover'].set_value(f"{weather_data['cloudcover']:.0f}%")
        else:
            self.environment.pairs['cloud_cover'].set_value("--")
        
        if 'dewpoint' in weather_data and weather_data['dewpoint'] is not None:
            self.environment.pairs['dew_point'].set_value(f"{weather_data['dewpoint']:.1f}°C")
        else:
            self.environment.pairs['dew_point'].set_value("--")
            
        if 'humidity' in weather_data and weather_data['humidity'] is not None:
            self.environment.pairs['humidity'].set_value(f"{weather_data['humidity']:.0f}%")
        else:
            self.environment.pairs['humidity'].set_value("--")
            
        if 'pressure' in weather_data and weather_data['pressure'] is not None:
            self.environment.pairs['pressure'].set_value(f"{weather_data['pressure']:.0f}hPa")
        else:
            self.environment.pairs['pressure'].set_value("--")
            
        if 'rainrate' in weather_data and weather_data['rainrate'] is not None:
            self.environment.pairs['rain'].set_value(f"{weather_data['rainrate']:.1f}mm/h")
        else:
            self.environment.pairs['rain'].set_value("--")
            
        if 'skybrightness' in weather_data and weather_data['skybrightness'] is not None:
            self.environment.pairs['sky_brightness'].set_value(f"{weather_data['skybrightness']:.1f}lux")
        else:
            self.environment.pairs['sky_brightness'].set_value("--")
            
        if 'skytemperature' in weather_data and weather_data['skytemperature'] is not None:
            self.environment.pairs['sky_temperature'].set_value(f"{weather_data['skytemperature']:.1f}°C")
        else:
            self.environment.pairs['sky_temperature'].set_value("--")
            
        if 'starfwhm' in weather_data and weather_data['starfwhm'] is not None:
            self.environment.pairs['seeing'].set_value(f"{weather_data['starfwhm']:.1f}arcsec")
        else:
            self.environment.pairs['seeing'].set_value("--")
            
        if 'temperature' in weather_data and weather_data['temperature'] is not None:
            self.environment.pairs['air_temp'].set_value(f"{weather_data['temperature']:.1f}°C")
        else:
            self.environment.pairs['air_temp'].set_value("--")
            
        if 'winddirection' in weather_data and weather_data['winddirection'] is not None:
            self.environment.pairs['wind_direction'].set_value(f"{weather_data['winddirection']:.0f}°")
        else:
            self.environment.pairs['wind_direction'].set_value("--")
            
        if 'windspeed' in weather_data and weather_data['windspeed'] is not None:
            self.environment.pairs['wind_speed'].set_value(f"{weather_data['windspeed']:.1f}m/s")
        else:
            self.environment.pairs['wind_speed'].set_value("--")
            
        if 'windgust' in weather_data and weather_data['windgust'] is not None:
            self.environment.pairs['avg_wind_speed'].set_value(f"{weather_data['windgust']:.1f}m/s")
        else:
            self.environment.pairs['avg_wind_speed'].set_value("--")