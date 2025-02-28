"""
天文计算服务模块
"""
from datetime import datetime, timezone, timedelta
import pytz
from astropy.time import Time
import astropy.units as u
from astroplan import Observer
from astropy.coordinates import EarthLocation, get_sun, SkyCoord
from src.config.settings import TELESCOPE_CONFIG, TIMEZONE
import requests
import tempfile
import os
from PyQt5.QtGui import QImage

class AstronomyService:
    def __init__(self):
        self.latitude = TELESCOPE_CONFIG['latitude']
        self.longitude = TELESCOPE_CONFIG['longitude']
        self.altitude = TELESCOPE_CONFIG['altitude']
        self.location = EarthLocation(
            lat=self.latitude*u.deg,
            lon=self.longitude*u.deg,
            height=self.altitude*u.m
        )
        self.timezone = pytz.timezone(TIMEZONE)
        self.observer = Observer(location=self.location, timezone=self.timezone)
        self.dss_url = "https://archive.stsci.edu/cgi-bin/dss_search"
        self.temp_dir = tempfile.gettempdir()

    def get_current_time(self):
        """获取当前时间（UTC和UTC+8）"""
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        tz_utc8 = timezone(timedelta(hours=8))
        utc8_now = now.astimezone(tz_utc8)
        return {
            'utc': now.strftime("%Y-%m-%d %H:%M:%S"),
            'utc8': utc8_now.strftime("%Y-%m-%d %H:%M:%S")
        }

    def get_sun_info(self):
        """获取太阳相关信息"""
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        current_time = Time(now)
        
        try:
            sunrise = self.observer.sun_rise_time(
                current_time, which='next'
            ).to_datetime(timezone=self.timezone)
            
            sunset = self.observer.sun_set_time(
                current_time, which='next'
            ).to_datetime(timezone=self.timezone)
            
            sun_altaz = self.observer.altaz(
                current_time,
                target=get_sun(current_time)
            )
            
            return {
                'sunrise': sunrise.strftime("%H:%M:%S"),
                'sunset': sunset.strftime("%H:%M:%S"),
                'altitude': f"{sun_altaz.alt:.2f}°"
            }
        except Exception as e:
            return {
                'sunrise': "计算错误",
                'sunset': "计算错误",
                'altitude': "计算错误"
            }

    def get_twilight_info(self):
        """获取晨昏信息"""
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        current_time = Time(now)
        
        try:
            morning = self.observer.twilight_morning_astronomical(
                current_time, which='next'
            ).to_datetime(timezone=self.timezone)
            
            evening = self.observer.twilight_evening_astronomical(
                current_time, which='next'
            ).to_datetime(timezone=self.timezone)
            
            return {
                'morning': morning.strftime("%H:%M:%S"),
                'evening': evening.strftime("%H:%M:%S")
            }
        except Exception as e:
            return {
                'morning': "计算错误",
                'evening': "计算错误"
            }

    def calculate_moon_phase(self):
        """计算月相"""
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        reference = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
        diff = now - reference
        days = diff.total_seconds() / 86400.0
        synodic_month = 29.53058867
        phase = (days % synodic_month) / synodic_month
        return round(phase, 2)

    def parse_coordinates(self, ra_str, dec_str):
        """
        解析赤经赤纬字符串
        :param ra_str: 赤经字符串 (HH:MM:SS)
        :param dec_str: 赤纬字符串 (+/-DD:MM:SS)
        :return: (ra_deg, dec_deg) 转换后的度数
        """
        try:
            # 解析赤经
            ra_parts = ra_str.split(':')
            if len(ra_parts) == 3:
                ra_hours = float(ra_parts[0])
                ra_minutes = float(ra_parts[1])
                ra_seconds = float(ra_parts[2])
                ra_deg = (ra_hours + ra_minutes/60 + ra_seconds/3600) * 15  # 转换为度
            else:
                raise ValueError("赤经格式错误")

            # 解析赤纬
            dec_parts = dec_str.split(':')
            if len(dec_parts) == 3:
                dec_sign = 1 if dec_str[0] != '-' else -1
                dec_degrees = float(dec_parts[0].replace('+', ''))
                dec_minutes = float(dec_parts[1])
                dec_seconds = float(dec_parts[2])
                dec_deg = dec_sign * (abs(dec_degrees) + dec_minutes/60 + dec_seconds/3600)
            else:
                raise ValueError("赤纬格式错误")

            return ra_deg, dec_deg
        except Exception as e:
            print(f"坐标解析错误: {e}")
            return None, None

    def get_dss_image(self, ra, dec, size=15):
        """
        获取DSS星图
        :param ra: 赤经 (格式: HH:MM:SS)
        :param dec: 赤纬 (格式: DD:MM:SS)
        :param size: 图像大小（角分）
        :return: 图像路径或None
        """
        try:
            # 解析坐标
            ra_deg, dec_deg = self.parse_coordinates(ra, dec)
            if ra_deg is None or dec_deg is None:
                return None

            # 生成安全的文件名
            safe_ra = f"{ra_deg:.6f}".replace('.', '_')
            safe_dec = f"{dec_deg:.6f}".replace('.', '_')
            temp_path = os.path.join(self.temp_dir, f"dss_image_{safe_ra}_{safe_dec}.gif")
            
            # 检查缓存
            if os.path.exists(temp_path):
                return temp_path
            
            # 构建请求参数
            params = {
                'r': ra_deg,
                'd': dec_deg,
                'e': 'J2000',
                'h': size,
                'w': size,
                'f': 'gif',
                'v': 'poss2ukstu_red'  # 使用POSS2/UKSTU Red作为默认调查
            }
            
            print(f"请求DSS图像: RA={ra_deg:.6f}°, Dec={dec_deg:.6f}°")
            
            # 发送请求获取图像
            response = requests.get(self.dss_url, params=params)
            if response.status_code == 200:
                # 保存图像到临时文件
                with open(temp_path, 'wb') as f:
                    f.write(response.content)
                return temp_path
            
            return None
        except Exception as e:
            print(f"获取DSS图像失败: {e}")
            return None

    def calculate_position_angle(self, ra_str, dec_str, rotator_angle):
        """
        计算画幅与赤纬的夹角
        :param ra_str: 赤经字符串 (HH:MM:SS)
        :param dec_str: 赤纬字符串 (+/-DD:MM:SS)
        :param rotator_angle: 消旋器角度（度）
        :return: 夹角（度）
        """
        try:
            # 创建天球坐标对象
            coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg), frame='icrs')
            
            # 获取位置角（与北天极的夹角）
            # 在赤道坐标系中，位置角是从北向东测量的角度
            position_angle = coord.position_angle(coord).deg
            
            # 计算画幅与赤纬的夹角
            # 消旋器角度需要考虑与位置角的关系
            frame_dec_angle = (rotator_angle - position_angle) % 360
            
            # 将角度规范化到 0-180 度范围内
            if frame_dec_angle > 180:
                frame_dec_angle = 360 - frame_dec_angle
                
            return frame_dec_angle
            
        except Exception as e:
            print(f"位置角计算错误: {e}")
            return None

# 创建全局实例
astronomy_service = AstronomyService() 