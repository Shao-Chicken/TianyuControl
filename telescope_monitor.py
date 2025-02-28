import sys
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, QUrl, QTimer  # 从 PyQt5.QtCore 导入 Qt 和 QUrl 类以及 QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, QButtonGroup
from qfluentwidgets import setTheme, Theme, PrimaryPushButton, TransparentToolButton
from qfluentwidgets import (CaptionLabel, BodyLabel, StrongBodyLabel, SubtitleLabel, TitleLabel,  # 从 qfluentwidgets 导入多个标签类
                            LargeTitleLabel, DisplayLabel, setTheme, Theme, HyperlinkLabel, setFont)  # 导入主题和字体设置函数
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtWidgets import QApplication, QLabel
import os

class TelescopeMonitor(QWidget):
    def __init__(self):
        super().__init__()
        
        # 设置默认的经纬度和海拔（单位：米）
        self.latitude = 38.614595
        self.longitude = 93.897782
        self.altitude = 4300

        # 加载自定义字体
        font_dir = r"C:\Users\90811\Downloads\TianyuControl\font"
        added_fonts = []
        for file in os.listdir(font_dir):
            if file.lower().endswith(".ttf") or file.lower().endswith(".otf"):
                font_path = os.path.join(font_dir, file)
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    added_fonts.extend(families)
        for font in added_fonts:
            print(font)

        # 在类的开头添加语言设置
        self.is_chinese = True
        self.translations = {
            'telescope_status': {'cn': '望远镜状态', 'en': 'Telescope Status'},
            'camera_settings': {'cn': '相机设置', 'en': 'Camera Settings'},
            'focuser_status': {'cn': '调焦器状态', 'en': 'Focuser Status'},
            'all_sky_camera': {'cn': '全天相机', 'en': 'All Sky Camera'},
            'environment': {'cn': '环境监测', 'en': 'Environment'},
            'current_time': {'cn': '当前时间', 'en': 'Current Time'},
            'light_mode': {'cn': '日间', 'en': 'Light'},
            'dark_mode': {'cn': '夜间', 'en': 'Dark'},
            'red_mode': {'cn': '红光', 'en': 'Red'},
            'language': {'cn': '中文', 'en': 'EN'},
            'device_connection': {'cn': '设备连接状态', 'en': 'Device Connection'},
            'mount': {'cn': '赤道仪', 'en': 'Mount'},
            'focuser': {'cn': '电调焦', 'en': 'Focuser'},
            'weather': {'cn': '气象站', 'en': 'Weather Station'},
            'camera_temp': {'cn': '相机温度', 'en': 'Camera Temperature'},
            'readout_mode': {'cn': '读出模式', 'en': 'Readout Mode'},
            'filter_position': {'cn': '滤光片位置', 'en': 'Filter Position'},
            'position': {'cn': '调焦器当前位置/总行程', 'en': 'Current/Total Position'},
            'angle': {'cn': '消旋器角度', 'en': 'Rotator Angle'},
            'moving': {'cn': '是否在移动', 'en': 'Moving'},
            'temperature': {'cn': '温度', 'en': 'Temperature'},
            'last_focus': {'cn': '上次对焦时间', 'en': 'Last Focus Time'},
            'cloud_cover': {'cn': '红外云量', 'en': 'Cloud Cover'},
            'dew_point': {'cn': '露点', 'en': 'Dew Point'},
            'humidity': {'cn': '湿度', 'en': 'Humidity'},
            'pressure': {'cn': '气压', 'en': 'Pressure'},
            'rain': {'cn': '雨量', 'en': 'Precipitation'},
            'sky_brightness': {'cn': '天空亮度', 'en': 'Sky Brightness'},
            'sky_temperature': {'cn': '天空温度', 'en': 'Sky Temperature'},
            'seeing': {'cn': '视宁度', 'en': 'Seeing'},
            'air_temp': {'cn': '气温', 'en': 'Air Temperature'},
            'wind_direction': {'cn': '风向', 'en': 'Wind Direction'},
            'wind_speed': {'cn': '瞬时风速', 'en': 'Wind Speed'},
            'avg_wind_speed': {'cn': '5分钟平均风速', 'en': '5-min Avg Wind Speed'},
            'fullscreen': {'cn': '全屏显示', 'en': 'Fullscreen'},
            'status': {'cn': '状态', 'en': 'Status'},
            'running': {'cn': '运行中', 'en': 'Running'},
            'rotator': {'cn': '消旋器', 'en': 'Rotator'},
            'ra': {'cn': '赤经', 'en': 'RA'},
            'dec': {'cn': '赤纬', 'en': 'Dec'},
            'alt': {'cn': '高度角', 'en': 'Altitude'},
            'az': {'cn': '方位角', 'en': 'Azimuth'}
        }

        # 修改主题样式，移除加粗
        self.light_theme = """
            QWidget {
                background-color: #f0f0f0;
                color: #333333;
            }
            QGroupBox {
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                font-size: 24px;
                padding: 20px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                color: #666666;
                font-size: 28px;
            }
            QPushButton {
                background-color: #e0e0e0;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QLabel {
                background-color: transparent;
                font-size: 20px;
                color: #333333;
            }
            QComboBox {
                font-size: 20px;
                padding: 8px;
            }
            .theme-button {
                padding: 8px 16px;
                font-size: 16px;
                border-radius: 4px;
                margin: 4px;
                min-width: 80px;
            }
            .info-value {
                margin-left: 30px;
                font-size: 24px;
                color: #333333;
            }
            .small-text {
                font-size: 18px;
                color: #666666;
            }
            .large-text {
                font-size: 96px;
                font-weight: bold;
                color: #333333;
            }
            .medium-text {
                font-size: 28px;
                color: #333333;
            }
            .label-title {
                font-size: 24px;
                color: #333333;
                margin-right: 15px;
            }
            .square-button {
                width: 32px;
                height: 32px;
                padding: 0px;
                border-radius: 4px;
            }
        """
        
        self.dark_theme = """
            QWidget {
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 2px solid #404040;
                border-radius: 8px;
                margin-top: 1ex;
                font-size: 24px;
                padding: 20px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                color: #ffffff;
                font-size: 28px;
            }
            QPushButton {
                background-color: #404040;
                border: none;
                padding: 12px;
                border-radius: 6px;
                color: #ffffff;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QLabel {
                background-color: transparent;
                color: #e0e0e0;
                font-size: 20px;
            }
            QComboBox {
                font-size: 20px;
                padding: 8px;
                color: #e0e0e0;
                background-color: #404040;
            }
            .theme-button {
                padding: 8px 16px;
                font-size: 16px;
                border-radius: 4px;
                margin: 4px;
                min-width: 80px;
            }
            .info-value {
                margin-left: 30px;
                font-size: 24px;
                color: #ffffff;
            }
            .small-text {
                font-size: 18px;
                color: #b0b0b0;
            }
            .large-text {
                font-size: 96px;
                color: #ffffff;
            }
            .medium-text {
                font-size: 28px;
                color: #ffffff;
            }
            .label-title {
                font-size: 24px;
                color: #ffffff;
                margin-right: 15px;
            }
            .square-button {
                width: 32px;
                height: 32px;
                padding: 0px;
                border-radius: 4px;
            }
        """
        
        self.red_theme = """
            QWidget {
                background-color: #1a0000;
                color: #ff9999;
            }
            QGroupBox {
                border: 2px solid #400000;
                border-radius: 8px;
                margin-top: 1ex;
                font-size: 24px;
                padding: 20px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                color: #ff6666;
                font-size: 28px;
            }
            QPushButton {
                background-color: #400000;
                border: none;
                padding: 12px;
                border-radius: 6px;
                color: #ff9999;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #500000;
            }
            QLabel {
                background-color: transparent;
                color: #ff9999;
                font-size: 20px;
            }
            QComboBox {
                font-size: 20px;
                padding: 8px;
                color: #ff9999;
                background-color: #400000;
            }
            .theme-button {
                padding: 8px 16px;
                font-size: 16px;
                border-radius: 4px;
                margin: 4px;
                min-width: 80px;
            }
            .info-value {
                margin-left: 30px;
                font-size: 24px;
                color: #ff6666;
            }
            .small-text {
                font-size: 18px;
                color: #ff8080;
            }
            .large-text {
                font-size: 96px;
                color: #ff4444;
            }
            .medium-text {
                font-size: 28px;
                color: #ff6666;
            }
            .label-title {
                font-size: 24px;
                color: #ff6666;
                margin-right: 15px;
            }
            .square-button {
                width: 32px;
                height: 32px;
                padding: 0px;
                border-radius: 4px;
            }
        """

        # 修改主题切换按钮布局
        theme_layout = QHBoxLayout()
        theme_layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加弹性空间，使按钮靠右对齐
        theme_layout.addStretch()

        # 创建语言切换按钮
        self.lang_btn = QPushButton('中文')
        self.lang_btn.setProperty('class', 'theme-button')
        self.lang_btn.clicked.connect(self.change_language)
        theme_layout.addWidget(self.lang_btn)
        
        self.light_btn = QPushButton('日间')
        self.dark_btn = QPushButton('夜间')
        self.red_btn = QPushButton('红光')
        
        for btn in [self.light_btn, self.dark_btn, self.red_btn]:
            btn.setProperty('class', 'theme-button')
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda checked, b=btn: self.change_theme('light' if b == self.light_btn else 'dark' if b == self.dark_btn else 'red'))
            theme_layout.addWidget(btn)

        # 修改布局
        main_layout = QVBoxLayout()
        content_layout = QHBoxLayout()
        
        # 添加主题按钮到顶部
        main_layout.addLayout(theme_layout)
        main_layout.addLayout(content_layout)
        
        self.setWindowTitle('天语望远镜总监控视')
        self.setGeometry(100, 100, 1920, 1080)

        # 左侧栏
        left_layout = QVBoxLayout()

        title_group = QGroupBox()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)  # 减小行间距
        
        # 使用小号字体显示基本信息
        basic_info = [
            '望远镜口径: 1m',
            '视场大小: xx',
            f'经度：{self.longitude}',
            f'纬度：{self.latitude}',
            f'海拔：{self.altitude}m'
        ]
        
        for info in basic_info:
            label = QLabel(info)
            label.setProperty('class', 'small-text')
            title_layout.addWidget(label)
            
        title_group.setLayout(title_layout)
        left_layout.addWidget(title_group)

        # 修改设备连接状态部分
        device_connection_group = QGroupBox(self.get_text('device_connection'))
        device_connection_layout = QVBoxLayout()

        devices = [
            ('mount', "赤道仪"),
            ('focuser', "电调焦"),
            ('rotator', "消旋器"),
            ('weather', "气象站")
        ]

        for key, _ in devices:
            row_layout = QHBoxLayout()
            device_label = QLabel(self.get_text(key))
            device_label.setProperty('class', 'label-title')
            row_layout.addWidget(device_label)
            
            combo_box = QtWidgets.QComboBox()
            combo_box.addItems(["COM1", "COM2", "COM3"])
            row_layout.addWidget(combo_box)
            
            for i in range(1, 4):
                btn = QPushButton(str(i))
                btn.setProperty('class', 'square-button')
                btn.setFixedSize(32, 32)
                row_layout.addWidget(btn)
            
            device_connection_layout.addLayout(row_layout)

        device_connection_group.setLayout(device_connection_layout)
        left_layout.addWidget(device_connection_group)

        # 中间栏
        middle_layout = QVBoxLayout()

        # 望远镜状态
        telescope_status_group = QGroupBox(self.get_text('telescope_status'))
        telescope_status_layout = QVBoxLayout()

        # RA/Dec 显示
        row_layout_ra, self.time_label_ra = self.create_label_pair('ra', '<span style="font-family:Sablon Up; font-size:96pt;">12:00:00</span>', 'large-text')
        self.time_label_ra.setTextFormat(Qt.RichText)
        telescope_status_layout.addLayout(row_layout_ra)

        row_layout_dec, self.time_label_dec = self.create_label_pair('dec', '<span style="font-family:Sablon Up; font-size:96pt;">+30:00:00</span>', 'large-text')
        self.time_label_dec.setTextFormat(Qt.RichText)
        telescope_status_layout.addLayout(row_layout_dec)

        # Alt/Az 显示
        row_layout_alt, self.alt_label = self.create_label_pair('alt', '60°')
        telescope_status_layout.addLayout(row_layout_alt)

        row_layout_az, self.az_label = self.create_label_pair('az', '120°')
        telescope_status_layout.addLayout(row_layout_az)

        # 状态显示
        row_layout_status, self.status_label = self.create_label_pair('status', self.get_text('running'))
        telescope_status_layout.addLayout(row_layout_status)

        telescope_status_group.setLayout(telescope_status_layout)
        middle_layout.insertWidget(0, telescope_status_group)

        # 相机设置
        camera_settings_group = QGroupBox('相机设置')
        camera_settings_layout = QVBoxLayout()

        row_layout_temp = QHBoxLayout()
        row_layout_temp.addWidget(QLabel('相机温度'))
        row_layout_temp.addWidget(QLabel('-30.0°C'))  # 实际数值
        camera_settings_layout.addLayout(row_layout_temp)

        # row_layout_power = QHBoxLayout()
        # row_layout_power.addWidget(QLabel('制冷功率'))
        # row_layout_power.addWidget(QLabel('0.0 (unit)'))  # 实际数值
        # camera_settings_layout.addLayout(row_layout_power)

        row_layout_mode = QHBoxLayout()
        row_layout_mode.addWidget(QLabel('读出模式'))
        row_layout_mode.addWidget(QLabel('高动态范围模式'))  # 实际数值
        camera_settings_layout.addLayout(row_layout_mode)

        row_layout_filter = QHBoxLayout()
        row_layout_filter.addWidget(QLabel('滤光片位置'))
        row_layout_filter.addWidget(QLabel('r-band'))  # 实际数值
        camera_settings_layout.addLayout(row_layout_filter)

        camera_settings_group.setLayout(camera_settings_layout)
        middle_layout.addWidget(camera_settings_group)

        # 调焦器状态
        focuser_status_group = QGroupBox('调焦器状态')
        focuser_status_layout = QVBoxLayout()

        # 调焦器总行程当前位置
        row_layout_position = QHBoxLayout()
        row_layout_position.addWidget(QLabel('调焦器当前位置/总行程'))
        row_layout_position.addWidget(QLabel('34000/60000'))  # 实际数值
        focuser_status_layout.addLayout(row_layout_position)

        # 消旋器角度
        row_layout_angle = QHBoxLayout()
        row_layout_angle.addWidget(QLabel('消旋器角度'))
        row_layout_angle.addWidget(QLabel('90°'))  # 实际数值
        focuser_status_layout.addLayout(row_layout_angle)

        # 是否在移动
        row_layout_moving = QHBoxLayout()
        row_layout_moving.addWidget(QLabel('是否在移动'))
        row_layout_moving.addWidget(QLabel('是'))  # 实际数值
        focuser_status_layout.addLayout(row_layout_moving)
        
        # 温度
        row_layout_temperature = QHBoxLayout()
        row_layout_temperature.addWidget(QLabel('温度'))
        row_layout_temperature.addWidget(QLabel('-10.0 °C'))  # 实际数值
        focuser_status_layout.addLayout(row_layout_temperature)

        # 上次对焦时间
        row_layout_focus_time = QHBoxLayout()
        row_layout_focus_time.addWidget(QLabel('上次对焦时间'))
        row_layout_focus_time.addWidget(QLabel('2025-02-23 12:00:00'))  # 实际数值
        focuser_status_layout.addLayout(row_layout_focus_time)

        focuser_status_group.setLayout(focuser_status_layout)
        middle_layout.addWidget(focuser_status_group)

        # 右侧栏
        right_layout = QVBoxLayout()

        # 全天相机
        all_day_camera_group = QGroupBox('全天相机')
        all_day_camera_layout = QVBoxLayout()
        # all_day_camera_layout.addWidget(QLabel('图片显示区域'))  # 修改为 QLabel 显示图片
        all_day_camera_layout.addWidget(QLabel('<img src="C:/Users/90811/Downloads/cutout2.jpg"/>'))  # 添加图片
        # all_day_camera_layout.addWidget(QLabel('视频显示区域'))
        
        # 添加视频显示区域
        video_label = QLabel()
        all_day_camera_layout.addWidget(QLabel('视频显示历史云量?'))  # 实际数值
        # video_label.setText('<video width="320" height="240" controls><source src="C:/Users/90811/Downloads/videoplayback.mp4" type="video/mp4">您的浏览器不支持视频标签。</source></video>')
        all_day_camera_layout.addWidget(video_label)  # 添加视频
        
        full_screen_button = QPushButton('全屏显示')
        all_day_camera_layout.addWidget(full_screen_button)
        all_day_camera_group.setLayout(all_day_camera_layout)
        right_layout.addWidget(all_day_camera_group)

        # 环境监测
        environment_monitoring_group = QGroupBox('环境监测')
        environment_monitoring_layout = QVBoxLayout()
        
        # 云量
        cloud_cover_layout = QHBoxLayout()
        cloud_label = QLabel('红外云量')
        cloud_label.setProperty('class', 'label-title')
        cloud_cover_layout.addWidget(cloud_label)
        cloud_value = QLabel('30%')
        cloud_value.setProperty('class', 'medium-text')
        cloud_cover_layout.addWidget(cloud_value)
        environment_monitoring_layout.addLayout(cloud_cover_layout)

        # 露点
        dew_point_layout = QHBoxLayout()
        dew_label = QLabel('露点')
        dew_label.setProperty('class', 'label-title')
        dew_point_layout.addWidget(dew_label)
        dew_value = QLabel('-15.0 °C')
        dew_value.setProperty('class', 'medium-text')
        dew_point_layout.addWidget(dew_value)
        environment_monitoring_layout.addLayout(dew_point_layout)
        
        # 湿度
        humidity_layout = QHBoxLayout()
        humidity_label = QLabel('湿度')
        humidity_label.setProperty('class', 'label-title')
        humidity_layout.addWidget(humidity_label)
        humidity_value = QLabel('50%')
        humidity_value.setProperty('class', 'medium-text')
        humidity_layout.addWidget(humidity_value)
        environment_monitoring_layout.addLayout(humidity_layout)

        # 气压
        pressure_layout = QHBoxLayout()
        pressure_label = QLabel('气压')
        pressure_label.setProperty('class', 'label-title')
        pressure_layout.addWidget(pressure_label)
        pressure_value = QLabel('1000 hPa')
        pressure_value.setProperty('class', 'medium-text')
        pressure_layout.addWidget(pressure_value)
        environment_monitoring_layout.addLayout(pressure_layout)

        # 降水量
        precipitation_layout = QHBoxLayout()
        precipitation_layout.addWidget(QLabel('雨量'))
        precipitation_layout.addWidget(QLabel('10 mm/h'))  # 实际数值
        environment_monitoring_layout.addLayout(precipitation_layout)
        
        # 天空亮度
        sky_brightness_layout = QHBoxLayout()
        sky_brightness_layout.addWidget(QLabel('天空亮度'))
        sky_brightness_layout.addWidget(QLabel('10 lux'))  # 实际数值
        environment_monitoring_layout.addLayout(sky_brightness_layout)

        # SQM背景天空质量
        sqm_layout = QHBoxLayout()
        sqm_layout.addWidget(QLabel('SQM'))
        sqm_layout.addWidget(QLabel('18.0 mag/arcsec^2'))  # 实际数值
        environment_monitoring_layout.addLayout(sqm_layout)

        # 天空温度
        sky_temperature_layout = QHBoxLayout()
        sky_temperature_layout.addWidget(QLabel('天空温度'))
        sky_temperature_layout.addWidget(QLabel('-10.0 °C'))  # 实际数值
        environment_monitoring_layout.addLayout(sky_temperature_layout)

        # 视宁度
        seeing_layout = QHBoxLayout()
        seeing_layout.addWidget(QLabel('视宁度'))
        seeing_layout.addWidget(QLabel('0.5 arcsec'))  # 实际数值
        environment_monitoring_layout.addLayout(seeing_layout)

        # 温度
        temperature_layout = QHBoxLayout()
        temperature_layout.addWidget(QLabel('气温'))
        temperature_layout.addWidget(QLabel('-10.0 °C'))  # 实际数值
        environment_monitoring_layout.addLayout(temperature_layout)

        # 风向
        wind_direction_layout = QHBoxLayout()
        wind_direction_layout.addWidget(QLabel('风向'))
        wind_direction_layout.addWidget(QLabel('70°'))  # 实际数值
        environment_monitoring_layout.addLayout(wind_direction_layout)
        
        # 风速
        wind_speed_layout = QHBoxLayout()
        wind_speed_layout.addWidget(QLabel('瞬时风速'))
        wind_speed_layout.addWidget(QLabel('10 m/s'))  # 实际数值
        environment_monitoring_layout.addLayout(wind_speed_layout)

        # 5分钟平均风速
        five_minute_average_wind_speed_layout = QHBoxLayout()
        five_minute_average_wind_speed_layout.addWidget(QLabel('5分钟平均风速'))
        five_minute_average_wind_speed_layout.addWidget(QLabel('10 m/s'))  # 实际数值
        environment_monitoring_layout.addLayout(five_minute_average_wind_speed_layout)

        environment_monitoring_group.setLayout(environment_monitoring_layout)
        right_layout.addWidget(environment_monitoring_group)

        # 时间显示
        time_group = QGroupBox('当前时间')
        time_layout = QVBoxLayout()
        self.label_moon_phase = QLabel('月相')
        self.label_sunrise_sunset = QLabel('日出/日落')
        self.label_astronomy_twilight = QLabel('天文晨光/昏影')
        self.label_utc8 = QLabel('UTC+8: ')
        self.label_sun_altitude = QLabel('太阳高度: ')
        time_layout.addWidget(self.label_utc8)
        time_layout.addWidget(self.label_sunrise_sunset)
        time_layout.addWidget(self.label_astronomy_twilight)
        time_layout.addWidget(self.label_moon_phase)
        time_layout.addWidget(self.label_sun_altitude)
        time_group.setLayout(time_layout)
        right_layout.addWidget(time_group)
        

        # 将三栏布局添加到主布局
        content_layout.addLayout(left_layout,1)
        content_layout.addLayout(middle_layout,6)
        content_layout.addLayout(right_layout,2)

        self.setLayout(main_layout)

        # 初始化定时器，每秒更新一次时间和天文信息
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_info)
        self.timer.start(1000)  # 每秒更新

        # 设置默认主题
        self.change_theme('light')

        # 修改布局间距
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # 调整标签样式
        for label in self.findChildren(QLabel):
            if "°" in label.text() or "m/s" in label.text():
                label.setProperty('class', 'medium-text')
            elif any(x in label.text() for x in ['UTC', '日出', '月相']):
                label.setProperty('class', 'info-value')

        # 调整组件间距
        telescope_status_layout.setSpacing(20)
        device_connection_layout.setSpacing(15)
        environment_monitoring_layout.setSpacing(10)
        
        # 设置组件对齐
        for layout in [telescope_status_layout, device_connection_layout, environment_monitoring_layout]:
            layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    def change_theme(self, theme):
        if theme == 'light':
            self.setStyleSheet(self.light_theme)
        elif theme == 'dark':
            self.setStyleSheet(self.dark_theme)
        else:
            self.setStyleSheet(self.red_theme)

    def update_time_info(self):
        from datetime import datetime, timezone, timedelta
        import pytz
        from astropy.time import Time
        import astropy.units as u
        from astroplan import Observer
        from astropy.coordinates import EarthLocation

        # 获取当前UTC时间，并计算UTC+8时间
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        tz_utc8 = timezone(timedelta(hours=8))
        utc8_now = now.astimezone(tz_utc8)
        utc_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        utc8_time_str = utc8_now.strftime("%Y-%m-%d %H:%M:%S")
        # self.label_utc.setText("UTC: " + utc_time_str)
        self.label_utc8.setText("UTC+8: " + utc8_time_str)

        # 使用当前时间构造 astropy 时间对象
        current_astropy_time = Time(now)

        # 根据默认经纬度和海拔设定观察者位置
        location = EarthLocation(lat=self.latitude*u.deg, lon=self.longitude*u.deg, height=self.altitude*u.m)
        tz = pytz.timezone("Asia/Shanghai")
        observer = Observer(location=location, timezone=tz)  # 使用之前定义的参数

        try:
            sunrise_time = observer.sun_rise_time(current_astropy_time, which='next').to_datetime(timezone=tz)
            sunset_time = observer.sun_set_time(current_astropy_time, which='next').to_datetime(timezone=tz)
            sunrise_sunset_str = sunrise_time.strftime("%H:%M:%S") + " / " + sunset_time.strftime("%H:%M:%S")
            self.label_sunrise_sunset.setText("日出/日落: " + sunrise_sunset_str)
        except Exception as e:
            self.label_sunrise_sunset.setText("日出/日落: 计算错误")

        try:
            astr_twilight_morning = observer.twilight_morning_astronomical(current_astropy_time, which='next').to_datetime(timezone=tz)
            astr_twilight_evening = observer.twilight_evening_astronomical(current_astropy_time, which='next').to_datetime(timezone=tz)
            astr_twilight_str = astr_twilight_morning.strftime("%H:%M:%S") + " / " + astr_twilight_evening.strftime("%H:%M:%S")
            self.label_astronomy_twilight.setText("天文晨光/昏影: " + astr_twilight_str)
        except Exception as e:
            self.label_astronomy_twilight.setText("天文晨光/昏影: 计算错误")

        # 计算月相信息
        moon_phase_value = self.calculate_moon_phase(now)
        self.label_moon_phase.setText("月相: " + str(moon_phase_value))

        # 计算太阳高度，使用Observer的altaz方法传入目标get_sun(current_astropy_time)
        from astropy.coordinates import get_sun
        sun_altaz = observer.altaz(current_astropy_time, target=get_sun(current_astropy_time))
        self.label_sun_altitude.setText(f'太阳高度: {sun_altaz.alt:.2f}°')

    def calculate_moon_phase(self, date):
        from datetime import datetime, timezone
        # 以2000年1月6日18:14 UTC作为新月参考
        reference = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
        diff = date - reference
        days = diff.total_seconds() / 86400.0
        synodic_month = 29.53058867
        phase = (days % synodic_month) / synodic_month

        # 返回相位的数值
        return round(phase, 2)  # 保留两位小数

    def get_text(self, key):
        return self.translations[key]['cn' if self.is_chinese else 'en']

    def update_all_labels(self):
        # 更新所有组标题
        for group in self.findChildren(QGroupBox):
            if group.title() in self.translations:
                group.setTitle(self.get_text(group.title()))

        # 更新所有标签文本
        for label in self.findChildren(QLabel):
            text = label.text()
            for key in self.translations:
                if text == self.translations[key]['cn'] or text == self.translations[key]['en']:
                    label.setText(self.get_text(key))
                    break

        # 更新按钮文本
        self.light_btn.setText(f"☀️ {self.get_text('light_mode')}")
        self.dark_btn.setText(f"🌙 {self.get_text('dark_mode')}")
        self.red_btn.setText(f"🔴 {self.get_text('red_mode')}")
        self.lang_btn.setText(self.get_text('language'))

    def change_language(self):
        self.is_chinese = not self.is_chinese
        self.update_all_labels()

    def create_label_pair(self, key, value=None, value_class='medium-text'):
        label = QLabel(self.get_text(key))
        label.setProperty('class', 'label-title')
        
        if value is None:
            value = ''
        value_label = QLabel(value)
        value_label.setProperty('class', value_class)
        
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(value_label)
        return layout, value_label

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)  # 设置高 DPI 缩放因子的舍入策略
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)  # 启用高 DPI 缩放
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)  # 启用高 DPI 像素图

    app = QApplication(sys.argv)  # 创建 QApplication 实例，传入命令行参数
    w = TelescopeMonitor()  # 创建 TelescopeMonitor 类的实例
    w.show()  # 显示 TelescopeMonitor 窗口
    app.exec_()  # 进入应用程序的主事件循环