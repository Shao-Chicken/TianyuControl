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
import math
from typing import Tuple, Union
import numpy as np
from PyQt5.QtCore import QDateTime
import time

class AstronomyService:
    def __init__(self):
        """初始化天文服务"""
        # 设置观测者位置
        self.longitude = TELESCOPE_CONFIG['longitude']
        self.latitude = TELESCOPE_CONFIG['latitude']
        self.elevation = TELESCOPE_CONFIG['altitude']
        
        # 创建观测者对象
        self.observer = Observer(
            longitude=self.longitude * u.deg,
            latitude=self.latitude * u.deg,
            elevation=self.elevation * u.m
        )
        
        # 设置时区
        self.timezone = timezone(timedelta(hours=8))  # UTC+8
        
        # DSS服务配置
        self.dss_url = "https://archive.stsci.edu/cgi-bin/dss_search"
        self.temp_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 缓存管理
        self.image_cache = []  # 存储图像文件路径和时间戳的列表
        self.max_cache_size = 2  # 最多缓存2张图像

    def _manage_cache(self, new_image_path):
        """管理图像缓存"""
        # 添加新图像到缓存
        self.image_cache.append((new_image_path, time.time()))
        
        # 如果缓存超过限制，删除最早的图像
        while len(self.image_cache) > self.max_cache_size:
            oldest_image_path, _ = self.image_cache.pop(0)
            try:
                if os.path.exists(oldest_image_path):
                    os.remove(oldest_image_path)
                    print(f"已删除缓存图像: {oldest_image_path}")
            except Exception as e:
                print(f"删除缓存图像失败: {e}")

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

    def calculate_julian_date(self, utc_time: QDateTime) -> float:
        """计算儒略日"""
        try:
            # 转换为ISO格式的字符串
            iso_time = utc_time.toString("yyyy-MM-ddThh:mm:ss")
            
            # 使用astropy计算儒略日
            t = Time(iso_time, format='isot', scale='utc')
            return t.jd
            
        except Exception as e:
            print(f"计算儒略日失败: {e}")
            return 0.0

    def calculate_moon_phase(self):
        """计算月相"""
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        reference = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
        diff = now - reference
        days = diff.total_seconds() / 86400.0
        synodic_month = 29.53058867
        phase = (days % synodic_month) / synodic_month
        return round(phase, 2)

    def _parse_time_format(self, time_str: Union[str, float]) -> float:
        """将时角格式（[+-]HH:MM:SS）转换为度数"""
        try:
            # 如果已经是数字，直接返回
            if isinstance(time_str, (int, float)):
                return float(time_str)
                
            # 移除所有空格
            time_str = str(time_str).strip()
            
            # 检查是否已经是度数格式
            if time_str.replace('.', '', 1).replace('-', '', 1).isdigit():
                return float(time_str)
            
            # 处理加号前缀
            is_negative = time_str.startswith('-')
            time_str = time_str.lstrip('+-')
            
            # 解析时角格式
            parts = time_str.split(':')
            if len(parts) == 3:
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                
                # 计算总度数
                total_degrees = hours + minutes/60 + seconds/3600
                if is_negative:
                    total_degrees = -total_degrees
                    
                return total_degrees
            else:
                raise ValueError(f"无效的时角格式: {time_str}")
        except Exception as e:
            raise ValueError(f"坐标格式转换错误: {e}")

    def get_dss_image(self, ra: Union[str, float], dec: Union[str, float]) -> str:
        """获取DSS图像"""
        try:
            # 转换坐标为度数
            ra_deg = self._parse_time_format(ra)
            dec_deg = self._parse_time_format(dec)
            
            # 构建DSS请求参数
            params = {
                'r': ra_deg,
                'd': dec_deg,
                'e': 'J2000',
                'h': 15.0,  # 图像高度(角分)
                'w': 15.0,  # 图像宽度(角分)
                'f': 'gif',  # 输出格式
                'v': 1,     # DSS版本
                'format': 'GIF'
            }
            
            # 发送请求获取图像
            response = requests.get(self.dss_url, params=params, timeout=10)
            if response.status_code == 200:
                # 保存图像到临时文件
                temp_file = os.path.join(self.temp_dir, f'dss_image_{ra_deg:.2f}_{dec_deg:.2f}.gif')
                with open(temp_file, 'wb') as f:
                    f.write(response.content)
                print(f"DSS图像已保存到: {temp_file}")
                
                # 管理缓存
                self._manage_cache(temp_file)
                
                return temp_file
            else:
                print(f"获取DSS图像失败: HTTP {response.status_code}")
                return None
            
        except Exception as e:
            print(f"获取DSS图像错误: {e}")
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