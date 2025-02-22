import sys
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, QUrl, QTimer  # 从 PyQt5.QtCore 导入 Qt 和 QUrl 类以及 QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout  # 从 PyQt5.QtWidgets 导入 QApplication, QWidget 和 QVBoxLayout
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QWidget, QLabel
from qfluentwidgets import BodyLabel, setTheme, Theme, CaptionLabel
from qfluentwidgets import (CaptionLabel, BodyLabel, StrongBodyLabel, SubtitleLabel, TitleLabel,  # 从 qfluentwidgets 导入多个标签类
                            LargeTitleLabel, DisplayLabel, setTheme, Theme, HyperlinkLabel, setFont)  # 导入主题和字体设置函数

class TelescopeMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('天语望远镜总监控视')
        self.setGeometry(100, 100, 1920, 1080)
        # 设置默认的经纬度和海拔（单位：米）
        self.latitude = 31.0
        self.longitude = 121.0
        self.altitude = 50

        # 主布局
        main_layout = QHBoxLayout()  # 水平布局

        # 左侧栏
        left_layout = QVBoxLayout()

        title_group = QGroupBox()
        title_layout = QVBoxLayout()
        title_layout.addWidget(BodyLabel('天语望远镜总监控视'))  # 这里可以用实际时间替换
        title_layout.addWidget(BodyLabel('望远镜口径: 1m'))  # 这里可以用实际时间替换
        title_layout.addWidget(BodyLabel('视场大小: 1000 arcmin'))  # 这里可以用实际时间替换
        title_layout.addWidget(BodyLabel('焦距: 1000 mm'))  # 这里可以用实际时间替换
        title_layout.addWidget(BodyLabel('焦比: 1:1'))  # 这里可以用实际时间替换
        title_layout.addWidget(BodyLabel('像元大小： 10um'))  # 这里可以用实际时间替换
        title_layout.addWidget(BodyLabel('像元数量： 8120*8120'))  # 这里可以用实际时间替换
        title_layout.addWidget(BodyLabel('帧率： 100fps'))  # 这里可以用实际时间替换
        title_layout.addWidget(BodyLabel('相机官网地址：https://www.sky-watcher.com/'))  # 这里可以用实际时间替换
        title_layout.addWidget(BodyLabel('经度：121.0'))  # 这里可以用实际时间替换
        title_layout.addWidget(BodyLabel('纬度：31.0'))  # 这里可以用实际时间替换
        title_layout.addWidget(BodyLabel('海拔：50'))  # 这里可以用实际时间替换
        title_group.setLayout(title_layout)
        left_layout.addWidget(title_group)

        # 望远镜状态
        telescope_status_group = QGroupBox('望远镜状态')
        telescope_status_layout = QVBoxLayout()
        telescope_status_labels = ['RA', 'Dec', 'Alt', 'Az', '状态', '经度', '纬度', '海拔']
        for label in telescope_status_labels:
            row_layout = QHBoxLayout()
            row_layout.addWidget(BodyLabel(label))
            row_layout.addWidget(BodyLabel('0.0 (unit)'))  # 实际数值
            telescope_status_layout.addLayout(row_layout)
        telescope_status_group.setLayout(telescope_status_layout)
        left_layout.addWidget(telescope_status_group)

        # 中间栏
        middle_layout = QVBoxLayout()

        # 相机设置
        camera_settings_group = QGroupBox('相机设置')
        camera_settings_layout = QVBoxLayout()
        camera_settings_labels = ['相机温度', '制冷功率', '读出模式', '滤光片位置']
        for label in camera_settings_labels:
            row_layout = QHBoxLayout()
            row_layout.addWidget(BodyLabel(label))
            row_layout.addWidget(BodyLabel('0.0 (unit)'))  # 实际数值
            camera_settings_layout.addLayout(row_layout)
        camera_settings_group.setLayout(camera_settings_layout)
        middle_layout.addWidget(camera_settings_group)

        # 调焦器状态
        focuser_status_group = QGroupBox('调焦器状态')
        focuser_status_layout = QVBoxLayout()
        focuser_status_labels = ['调焦器总行程当前位置', '消旋器角度', '上次对焦时间']
        for label in focuser_status_labels:
            row_layout = QHBoxLayout()
            row_layout.addWidget(BodyLabel(label))
            row_layout.addWidget(BodyLabel('0.0 (unit)'))  # 实际数值
            focuser_status_layout.addLayout(row_layout)
        focuser_status_group.setLayout(focuser_status_layout)
        middle_layout.addWidget(focuser_status_group)

        # 右侧栏
        right_layout = QVBoxLayout()

        # 全天相机
        all_day_camera_group = QGroupBox('全天相机')
        all_day_camera_layout = QVBoxLayout()
        # all_day_camera_layout.addWidget(QLabel('图片显示区域'))  # 修改为 QLabel 显示图片
        all_day_camera_layout.addWidget(QLabel('<img src="C:/Users/90811/Downloads/cutout.jpg"/>'))  # 添加图片
        # all_day_camera_layout.addWidget(BodyLabel('视频显示区域'))
        
        # 添加视频显示区域
        video_label = QLabel()
        all_day_camera_layout.addWidget(BodyLabel('视频显示地址'))  # 实际数值
        # video_label.setText('<video width="320" height="240" controls><source src="C:/Users/90811/Downloads/videoplayback.mp4" type="video/mp4">您的浏览器不支持视频标签。</source></video>')
        all_day_camera_layout.addWidget(video_label)  # 添加视频
        
        full_screen_button = QPushButton('全屏显示')
        all_day_camera_layout.addWidget(full_screen_button)
        all_day_camera_group.setLayout(all_day_camera_layout)
        right_layout.addWidget(all_day_camera_group)

        # 环境监测
        environment_monitoring_group = QGroupBox('环境监测')
        environment_monitoring_layout = QVBoxLayout()
        environment_monitoring_labels = ['温度', '湿度', '气压', '风速', '风向', '降水量', '天光亮度', 'SQM', '红外云量']
        for label in environment_monitoring_labels:
            row_layout = QHBoxLayout()
            row_layout.addWidget(BodyLabel(label))
            row_layout.addWidget(BodyLabel('0.0 (unit)'))  # 实际数值
            environment_monitoring_layout.addLayout(row_layout)
        environment_monitoring_group.setLayout(environment_monitoring_layout)
        right_layout.addWidget(environment_monitoring_group)

        # 时间显示
        time_group = QGroupBox('当前时间')
        time_layout = QVBoxLayout()
        self.label_moon_phase = BodyLabel('月相')
        self.label_sunrise_sunset = BodyLabel('日出/日落')
        self.label_astronomy_twilight = BodyLabel('天文晨光/昏影')
        self.label_utc = BodyLabel('UTC: ')
        self.label_utc8 = BodyLabel('UTC+8: ')
        time_layout.addWidget(self.label_moon_phase)
        time_layout.addWidget(self.label_sunrise_sunset)
        time_layout.addWidget(self.label_astronomy_twilight)
        time_layout.addWidget(self.label_utc)
        time_layout.addWidget(self.label_utc8)
        time_group.setLayout(time_layout)
        right_layout.addWidget(time_group)
        

        # 将三栏布局添加到主布局
        main_layout.addLayout(left_layout)
        main_layout.addLayout(middle_layout)
        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)

        # 初始化定时器，每秒更新一次时间和天文信息
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_info)
        self.timer.start(1000)  # 每秒更新

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
        self.label_utc.setText("UTC: " + utc_time_str)
        self.label_utc8.setText("UTC+8: " + utc8_time_str)

        # 使用当前时间构造 astropy 时间对象
        current_astropy_time = Time(now)

        # 根据默认经纬度和海拔设定观察者位置
        location = EarthLocation(lat=self.latitude*u.deg, lon=self.longitude*u.deg, height=self.altitude*u.m)
        tz = pytz.timezone("Asia/Shanghai")
        observer = Observer(location=location, timezone=tz)

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

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)  # 设置高 DPI 缩放因子的舍入策略
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)  # 启用高 DPI 缩放
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)  # 启用高 DPI 像素图

    app = QApplication(sys.argv)  # 创建 QApplication 实例，传入命令行参数
    w = TelescopeMonitor()  # 创建 TelescopeMonitor 类的实例
    w.show()  # 显示 TelescopeMonitor 窗口
    app.exec_()  # 进入应用程序的主事件循环