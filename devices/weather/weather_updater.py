#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
天气站数据更新器
定期从ASCOM Alpaca设备获取状态更新
"""

import logging
import time
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QMutex

# 设置日志
logger = logging.getLogger(__name__)

class WeatherStationUpdater(QThread):
    """
    天气站数据更新器，定期从ASCOM Alpaca设备获取状态更新
    """
    # 定义信号
    data_updated = pyqtSignal(dict)  # 数据更新信号
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, update_interval=1.0, parent=None):
        """
        初始化更新线程
        :param update_interval: 更新间隔（秒）
        :param parent: 父对象
        """
        super(WeatherStationUpdater, self).__init__(parent)
        
        # 设置线程名称和属性
        self.setObjectName("WeatherStationUpdater")
        
        # 设置更新间隔
        self.update_interval = update_interval
        
        # 设置线程运行标志
        self._running = False
        self._mutex = QMutex()
        
        # 设备模型引用
        self._model = None
    
    def set_model(self, model):
        """
        设置设备模型
        :param model: WeatherStationModel实例
        """
        self._model = model
    
    def run(self):
        """
        线程主函数
        """
        if self._model is None:
            self.error_occurred.emit("未设置设备模型")
            return
        
        # 设置运行标志
        self._mutex.lock()
        self._running = True
        self._mutex.unlock()
        
        while self._running:
            # 更新数据
            self.update_data()
            
            # 等待指定时间
            self.msleep(int(self.update_interval * 1000))
    
    def update_data(self):
        """更新设备数据"""
        if not self._model or not hasattr(self._model, "update_device_state"):
            return
            
        try:
            # 调用模型的更新方法
            try:
                # 直接调用refresh_data，它内部会处理刷新和更新设备状态
                if hasattr(self._model, "refresh_data"):
                    self._model.refresh_data()
                else:
                    # 如果没有refresh_data方法，则直接调用update_device_state
                    self._model.update_device_state()
            except Exception as update_error:
                logger.warning(f"更新设备状态时出错: {str(update_error)}")
            
            # 获取更新后的数据
            data = {}
            
            # 基本连接状态
            try:
                data["connected"] = self._model.connected
            except Exception:
                data["connected"] = False
            
            # 获取各种天气数据
            weather_sensors = [
                "temperature", "humidity", "pressure", "wind_speed", 
                "wind_direction", "rain_rate", "cloud_cover", "dew_point",
                "sky_brightness", "sky_temperature", "star_fwhm"
            ]
            
            for sensor in weather_sensors:
                try:
                    # 尝试获取传感器数据
                    sensor_value = getattr(self._model, sensor)
                    data[sensor] = sensor_value
                    
                    # 同时获取传感器支持状态
                    has_sensor = getattr(self._model, f"has_{sensor}")
                    data[f"has_{sensor}"] = has_sensor
                except Exception:
                    data[sensor] = None
                    data[f"has_{sensor}"] = False
            
            # 单独处理特殊传感器数据
            try:
                data["wind_gust"] = self._model.get_wind_gust()
                data["sky_quality"] = self._model.get_sky_quality()
            except Exception:
                data["wind_gust"] = None
                data["sky_quality"] = None
            
            # 获取安全状态
            try:
                data["is_safe"] = self._model.is_safe
            except Exception:
                data["is_safe"] = None
                
            # 获取额外的传感器数据（风力峰值和天空质量已在weather_sensors中）
            extra_sensors = ["average_period", "time_since_last_update"]
            for sensor in extra_sensors:
                try:
                    # 尝试获取额外传感器数据
                    if hasattr(self._model, f"_{sensor}"):
                        data[sensor] = getattr(self._model, f"_{sensor}")
                    elif hasattr(self._model, f"get_{sensor}"):
                        data[sensor] = getattr(self._model, f"get_{sensor}")()
                except Exception:
                    data[sensor] = None
            
            # 不再从天气站获取站点位置信息，这些信息应该从赤道仪获取
            
            # 发送数据更新信号
            self.data_updated.emit(data)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            logger.error(f"更新天气站数据失败: {str(e)}")
    
    def stop(self):
        """
        停止线程
        """
        # 设置运行标志
        self._mutex.lock()
        self._running = False
        self._mutex.unlock()
        
        # 等待线程结束
        if self.isRunning():
            self.wait(1000)
            
            # 如果线程仍在运行，强制终止
            if self.isRunning():
                self.terminate()
                logger.warning("强制终止天气站数据更新线程") 