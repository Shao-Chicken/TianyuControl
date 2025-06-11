#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
天气站模型类
用于管理ASCOM Alpaca天气站设备
"""

import logging
import time
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

# 设置日志
logger = logging.getLogger(__name__)

class WeatherStationModel(QObject):
    """
    天气站模型类，管理ASCOM Alpaca天气站设备
    """
    # 定义信号
    connected_changed = pyqtSignal(bool)  # 连接状态变化信号
    name_changed = pyqtSignal(str)  # 设备名称变化信号
    description_changed = pyqtSignal(str)  # 设备描述变化信号
    
    # 天气数据信号
    temperature_changed = pyqtSignal(float)  # 温度变化信号
    humidity_changed = pyqtSignal(float)  # 湿度变化信号
    pressure_changed = pyqtSignal(float)  # 气压变化信号
    wind_speed_changed = pyqtSignal(float)  # 风速变化信号
    wind_direction_changed = pyqtSignal(float)  # 风向变化信号
    rain_rate_changed = pyqtSignal(float)  # 降雨率变化信号
    cloud_cover_changed = pyqtSignal(float)  # 云量变化信号
    dew_point_changed = pyqtSignal(float)  # 露点变化信号
    sky_brightness_changed = pyqtSignal(float)  # 天空亮度变化信号
    sky_temperature_changed = pyqtSignal(float)  # 天空温度变化信号
    star_fwhm_changed = pyqtSignal(float)  # 星点FWHM变化信号
    
    # 天气状况信号
    safe_changed = pyqtSignal(bool)  # 安全状态变化信号
    
    error_occurred = pyqtSignal(str)  # 错误信号

    def __init__(self):
        super(WeatherStationModel, self).__init__()
        
        # 设备状态
        self._connected = False
        self._name = ""
        self._description = ""
        
        # 天气数据
        self._temperature = None  # 温度（摄氏度）
        self._humidity = None  # 湿度（百分比）
        self._pressure = None  # 气压（百帕）
        self._wind_speed = None  # 风速（米/秒）
        self._wind_direction = None  # 风向（度，北为0度，顺时针）
        self._rain_rate = None  # 降雨率（毫米/小时）
        self._cloud_cover = None  # 云量（百分比）
        self._dew_point = None  # 露点（摄氏度）
        self._sky_brightness = None  # 天空亮度（勒克斯）
        self._sky_temperature = None  # 天空温度（摄氏度）
        self._star_fwhm = None  # 星点FWHM（角秒）
        
        # 安全状态
        self._is_safe = None  # 是否安全
        
        # 传感器支持标志
        self._has_temperature = False
        self._has_humidity = False
        self._has_pressure = False
        self._has_wind_speed = False
        self._has_wind_direction = False
        self._has_rain_rate = False
        self._has_cloud_cover = False
        self._has_dew_point = False
        self._has_sky_brightness = False
        self._has_sky_temperature = False
        self._has_star_fwhm = False
        
        # 设备驱动
        self._device_driver = None
        
        # 设备连接参数
        self._host = "localhost"
        self._port = 11111
        self._device_number = 0
    
    # 属性getter
    @property
    def connected(self):
        return self._connected
    
    @property
    def name(self):
        return self._name
    
    @property
    def description(self):
        return self._description
    
    @property
    def temperature(self):
        return self._temperature
    
    @property
    def humidity(self):
        return self._humidity
    
    @property
    def pressure(self):
        return self._pressure
    
    @property
    def wind_speed(self):
        return self._wind_speed
    
    @property
    def wind_direction(self):
        return self._wind_direction
    
    @property
    def rain_rate(self):
        return self._rain_rate
    
    @property
    def cloud_cover(self):
        return self._cloud_cover
    
    @property
    def dew_point(self):
        return self._dew_point
    
    @property
    def sky_brightness(self):
        return self._sky_brightness
    
    @property
    def sky_temperature(self):
        return self._sky_temperature
    
    @property
    def star_fwhm(self):
        return self._star_fwhm
    
    @property
    def is_safe(self):
        return self._is_safe
    
    # 传感器支持标志属性
    @property
    def has_temperature(self):
        return self._has_temperature
    
    @property
    def has_humidity(self):
        return self._has_humidity
    
    @property
    def has_pressure(self):
        return self._has_pressure
    
    @property
    def has_wind_speed(self):
        return self._has_wind_speed
    
    @property
    def has_wind_direction(self):
        return self._has_wind_direction
    
    @property
    def has_rain_rate(self):
        return self._has_rain_rate
    
    @property
    def has_cloud_cover(self):
        return self._has_cloud_cover
    
    @property
    def has_dew_point(self):
        return self._has_dew_point
    
    @property
    def has_sky_brightness(self):
        return self._has_sky_brightness
    
    @property
    def has_sky_temperature(self):
        return self._has_sky_temperature
    
    @property
    def has_star_fwhm(self):
        return self._has_star_fwhm
    
    def set_device_params(self, host, port, device_number):
        """设置设备连接参数"""
        self._host = host
        self._port = port
        self._device_number = device_number
    
    def connect_device(self):
        """连接设备"""
        if self._connected:
            return True
        
        try:
            # 导入设备驱动（延迟导入，避免循环依赖）
            from common.alpaca_client import AlpacaClient
            
            # 创建AlpacaClient
            client = AlpacaClient(host=self._host, port=self._port)
            
            # 连接到ObservingConditions设备
            self._device_driver = client.get_device('observingconditions', self._device_number)
            
            # 确保设备真正连接
            try:
                connection_result = self._device_driver.connect()
                if not connection_result:
                    logger.error("天气站设备连接失败，无法继续初始化")
                    self.error_occurred.emit("天气站设备连接失败，请检查设备状态和连接设置")
                    return False
            except AttributeError:
                # AlpacaDevice类中connect方法不返回结果，所以需要特殊处理
                try:
                    self._device_driver.connect()
                    # 判断是否连接成功
                    if not self._device_driver.is_connected():
                        logger.error("天气站设备连接失败，无法继续初始化")
                        self.error_occurred.emit("天气站设备连接失败，请检查设备状态和连接设置")
                        return False
                except Exception as connect_e:
                    logger.error(f"天气站设备连接过程中出现错误: {str(connect_e)}")
                    self.error_occurred.emit(f"连接天气站设备失败: {str(connect_e)}")
                    return False
            
            # 获取设备信息
            try:
                # 尝试使用不同的方法获取名称和描述
                try:
                    self._name = self._device_driver.get_name()
                except AttributeError:
                    # AlpacaDevice实例可能使用不同的方法名
                    self._name = self._device_driver.name
                
                try:
                    self._description = self._device_driver.get_description()
                except AttributeError:
                    # AlpacaDevice实例可能使用不同的方法名
                    self._description = self._device_driver.description
            except Exception as info_e:
                logger.warning(f"获取设备信息失败，但继续连接过程: {str(info_e)}")
                self._name = "Unknown Weather Station"
                self._description = "Unknown Description"
            
            # 发送设备信息更新信号
            self.name_changed.emit(self._name)
            self.description_changed.emit(self._description)
            
            # 检查设备支持的传感器
            self.check_supported_sensors()
            
            # 更新设备状态
            self.update_device_state()
            
            # 设置连接状态
            self._connected = True
            self.connected_changed.emit(True)
            
            logger.info(f"成功连接天气站设备: {self._name}")
            return True
        
        except Exception as e:
            self.error_occurred.emit(f"连接天气站设备失败: {str(e)}")
            logger.error(f"连接天气站设备失败: {str(e)}")
            return False
    
    def disconnect_device(self):
        """断开设备连接"""
        if not self._connected:
            return True
        
        try:
            # 断开连接，释放资源
            self._device_driver = None
            
            # 重置状态
            self._connected = False
            self._name = ""
            self._description = ""
            
            # 重置天气数据
            self._temperature = None
            self._humidity = None
            self._pressure = None
            self._wind_speed = None
            self._wind_direction = None
            self._rain_rate = None
            self._cloud_cover = None
            self._dew_point = None
            self._sky_brightness = None
            self._sky_temperature = None
            self._star_fwhm = None
            self._is_safe = None
            
            # 发送信号
            self.connected_changed.emit(False)
            
            logger.info("天气站设备已断开连接")
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"断开天气站设备连接失败: {str(e)}")
            logger.error(f"断开天气站设备连接失败: {str(e)}")
            return False
    
    def check_supported_sensors(self):
        """检查设备支持的传感器"""
        if not self._connected and not self._device_driver:
            return
        
        try:
            # 由于AlpacaDevice直接使用has_temperature等方法，这里我们直接尝试设置所有传感器为支持状态
            # 后续读取数据时会自动处理读不到数据的情况
            self._has_temperature = True
            self._has_humidity = True
            self._has_pressure = True
            self._has_wind_speed = True
            self._has_wind_direction = True
            self._has_rain_rate = True
            self._has_cloud_cover = True
            self._has_dew_point = True
            self._has_sky_brightness = True
            self._has_sky_temperature = True
            self._has_star_fwhm = True
            
            logger.info("设置所有传感器为支持状态，具体读取时再判断")
        
        except Exception as e:
            logger.error(f"检查支持的传感器失败: {str(e)}")
    
    def update_device_state(self):
        """更新设备状态"""
        if not self._connected or not self._device_driver:
            return
        
        try:
            # 更新天气数据
            self.update_all_sensor_data()
            
            # 更新安全状态 - 不再尝试获取，因为已经从UI中删除了安全状态显示
        
        except Exception as e:
            logger.error(f"更新设备状态失败: {str(e)}")
    
    def update_all_sensor_data(self):
        """更新所有传感器数据"""
        if not self._connected or not self._device_driver:
            return
        
        try:
            # 尝试获取每个传感器的数据
            sensors = {
                "temperature": self._has_temperature,
                "humidity": self._has_humidity,
                "pressure": self._has_pressure,
                "wind_speed": self._has_wind_speed,
                "wind_direction": self._has_wind_direction,
                "rain_rate": self._has_rain_rate,
                "cloud_cover": self._has_cloud_cover,
                "dew_point": self._has_dew_point,
                "sky_brightness": self._has_sky_brightness,
                "sky_temperature": self._has_sky_temperature,
                "star_fwhm": self._has_star_fwhm
            }
            
            # 添加新的传感器数据
            try:
                self._wind_gust = self._device_driver.get_wind_gust() if hasattr(self._device_driver, "get_wind_gust") else None
                self._sky_quality = self._device_driver.get_sky_quality() if hasattr(self._device_driver, "get_sky_quality") else None
                self._average_period = self._device_driver.get_average_period() if hasattr(self._device_driver, "get_average_period") else None
                self._time_since_last_update = self._device_driver.get_time_since_last_update() if hasattr(self._device_driver, "get_time_since_last_update") else None
            except Exception as e:
                logger.warning(f"获取额外传感器数据失败: {str(e)}")
            
            for sensor, supported in sensors.items():
                if supported:
                    try:
                        # 调用驱动获取传感器数据
                        method_name = f"get_{sensor}"
                        value = getattr(self._device_driver, method_name)()
                        
                        # 更新模型数据
                        setattr(self, f"_{sensor}", value)
                        
                        # 发送信号
                        signal = getattr(self, f"{sensor}_changed")
                        signal.emit(value)
                    except Exception as e:
                        logger.warning(f"获取 {sensor} 数据失败: {str(e)}")
        
        except Exception as e:
            logger.error(f"更新传感器数据失败: {str(e)}")
            self.error_occurred.emit(f"更新传感器数据失败: {str(e)}")
    
    def refresh_data(self):
        """刷新所有数据"""
        if self._connected and self._device_driver:
            try:
                # 尝试使用AlpacaDevice的API直接调用refresh方法
                if hasattr(self._device_driver, 'refresh'):
                    self._device_driver.refresh()
                    #logger.info("已刷新天气站数据")
                elif hasattr(self._device_driver, '_put_request'):
                    # 如果没有refresh方法但有_put_request方法，尝试直接发送PUT请求
                    self._device_driver._put_request("refresh")
                    #logger.info("通过PUT请求刷新天气站数据")

                # 无论是否成功刷新，都尝试更新设备状态
                self.update_device_state()
                return True
                
            except Exception as e:
                logger.error(f"刷新天气站数据失败: {str(e)}")
                self.error_occurred.emit(f"刷新天气站数据失败: {str(e)}")
                return False
        return False
        
    def get_average_period(self):
        """获取平均周期"""
        if self._connected and self._device_driver:
            try:
                return self._device_driver.get_average_period()
            except Exception as e:
                logger.error(f"获取平均周期失败: {str(e)}")
                return None
        return None
        
    def set_average_period(self, period):
        """设置平均周期"""
        if self._connected and self._device_driver:
            try:
                self._device_driver.put_average_period(period)
                logger.info(f"设置平均周期为 {period}")
                return True
            except Exception as e:
                logger.error(f"设置平均周期失败: {str(e)}")
                self.error_occurred.emit(f"设置平均周期失败: {str(e)}")
                return False
        return False
    
    def get_sensor_description(self, sensor_name):
        """获取传感器描述"""
        if self._connected and self._device_driver:
            try:
                # 传感器名需要首字母大写
                sensor_name = sensor_name[0].upper() + sensor_name[1:]
                return self._device_driver.get_sensor_description(sensor_name)
            except Exception as e:
                logger.error(f"获取传感器描述失败: {str(e)}")
                return None
        return None
    
    def get_time_since_last_update(self, sensor_name=None):
        """获取自上次更新以来的时间"""
        if self._connected and self._device_driver:
            try:
                if sensor_name:
                    # 传感器名需要首字母大写
                    sensor_name = sensor_name[0].upper() + sensor_name[1:]
                    return self._device_driver.get_time_since_last_update(sensor_name)
                else:
                    return self._device_driver.get_time_since_last_update()
            except Exception as e:
                logger.error(f"获取自上次更新以来的时间失败: {str(e)}")
                return None
        return None
    
    def get_wind_gust(self):
        """获取风力峰值"""
        if self._connected and self._device_driver:
            try:
                return self._device_driver.get_wind_gust()
            except Exception as e:
                logger.error(f"获取风力峰值失败: {str(e)}")
                return None
        return None
    
    def get_sky_quality(self):
        """获取天空质量"""
        if self._connected and self._device_driver:
            try:
                return self._device_driver.get_sky_quality()
            except Exception as e:
                logger.error(f"获取天空质量失败: {str(e)}")
                return None
        return None 