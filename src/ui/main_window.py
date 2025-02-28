"""
主窗口模块
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from src.ui.components import LabelPair, DeviceControl, InfoGroup, ThemeButton, AngleVisualizer
from src.utils.i18n import i18n
from src.utils.theme_manager import theme_manager
from src.services.astronomy_service import astronomy_service
from src.services.device_service import device_service
from src.config.settings import TELESCOPE_CONFIG, DEVICES, LAYOUT_CONFIG
import os
import time

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_timer()

    def init_ui(self):
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
        for device_id, name in DEVICES:
            device_control = DeviceControl(device_id, i18n.get_text(device_id))
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
        self.telescope_status.add_item('status', i18n.get_text('tracking'))
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
        self.focuser_status.add_item('angle', '90°', 'medium-text')
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

        self.setLayout(main_layout)

        # 设置默认主题
        self.change_theme('light')

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
        self.telescope_status.pairs['status'].set_value(i18n.get_text('tracking'))
        
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
        """计算画幅与赤纬夹角并更新DSS星图"""
        try:
            # 从调焦器状态中获取消旋器角度
            rotator_text = self.focuser_status.pairs['angle'].value_label.text()
            rotator_angle = float(rotator_text.replace('°', ''))
            
            # 从望远镜状态中获取赤经和赤纬
            ra_text = self.telescope_status.pairs['ra'].value_label.text()
            dec_text = self.telescope_status.pairs['dec'].value_label.text()
            
            # 计算位置角和夹角
            frame_dec_angle = astronomy_service.calculate_position_angle(
                ra_text, dec_text, rotator_angle
            )
            
            if frame_dec_angle is not None:
                # 更新显示
                self.rotator_angle_group.pairs['frame_dec_angle'].set_value(f"{frame_dec_angle:.1f}°")
                
                # 获取并更新DSS星图
                dss_image_path = astronomy_service.get_dss_image(ra_text, dec_text)
                
                # 更新可视化组件
                self.angle_visualizer.set_background(dss_image_path)
                # 使用赤纬作为参考方向，消旋器角度作为画幅方向
                _, dec_deg = astronomy_service.parse_coordinates(ra_text, dec_text)
                if dec_deg is not None:
                    self.angle_visualizer.set_angles(0, rotator_angle)  # 使用0度作为赤纬参考线
            
        except (ValueError, IndexError) as e:
            print(f"角度计算错误: {e}")

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
        
        # 每5秒更新一次角度计算和星图
        if int(time.time()) % 5 == 0:
            self.calculate_frame_dec_angle() 