#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
望远镜模型类
将TelescopeDriver封装为Qt友好的模型
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Union, List, Tuple
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer

# 导入我们的望远镜驱动
from unified_driver import TelescopeDriver

# 设置日志
logger = logging.getLogger(__name__)

class TelescopeModel(QObject):
    """望远镜模型类，封装TelescopeDriver并提供Qt信号"""
    
    # 定义信号
    connected_changed = pyqtSignal(bool)
    position_changed = pyqtSignal(float, float, float, float)  # ra, dec, alt, az
    name_changed = pyqtSignal(str)
    description_changed = pyqtSignal(str)
    tracking_changed = pyqtSignal(bool)
    slewing_changed = pyqtSignal(bool)
    parked_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super(TelescopeModel, self).__init__(parent)
        
        self.driver = None
        self.is_connected = False
        self.update_timer = None
        
        # 望远镜属性
        self.right_ascension = 0.0
        self.declination = 0.0
        self.altitude = 0.0
        self.azimuth = 0.0
        self.name = ""
        self.description = ""
        self.driver_info = ""
        self.driver_version = ""
        self.is_tracking = False
        self.is_slewing = False
        self.is_parked = False
        
    def initialize(self, host: str = "202.127.24.217", port: int = 11111, device_number: int = 0):
        """
        初始化望远镜驱动
        
        参数:
            host: Alpaca服务器主机名或IP
            port: Alpaca服务器端口
            device_number: 设备编号
        """
        try:
            logger.info(f"初始化望远镜驱动: {host}:{port}")
            
            # 断开现有连接
            self.disconnect()
            
            # 创建新的驱动实例
            self.driver = TelescopeDriver(host=host, port=port, device_number=device_number)
            
            # 重置属性
            self.is_connected = False
            self.right_ascension = 0.0
            self.declination = 0.0
            self.altitude = 0.0
            self.azimuth = 0.0
            self.name = ""
            self.description = ""
            self.driver_info = ""
            self.driver_version = ""
            self.is_tracking = False
            self.is_slewing = False
            self.is_parked = False
            
            return True
        except Exception as e:
            logger.error(f"望远镜模型初始化失败: {str(e)}")
            self.error_occurred.emit(f"初始化失败: {str(e)}")
            return False
    
    @pyqtSlot()
    def connect(self) -> bool:
        """
        连接望远镜
        
        返回:
            连接是否成功
        """
        if not self.driver:
            logger.error("望远镜驱动未初始化")
            self.error_occurred.emit("望远镜驱动未初始化")
            return False
            
        try:
            # 调用驱动的连接方法
            logger.info("开始连接望远镜...")
            
            if self.driver.connect():
                logger.info("望远镜连接成功")
                self.is_connected = True
                
                # 获取设备信息
                try:
                    self.name = self.driver.get_name()
                    self.name_changed.emit(self.name)
                except Exception as e:
                    logger.warning(f"获取望远镜名称失败: {str(e)}")
                    
                try:
                    self.description = self.driver.get_description()
                    self.description_changed.emit(self.description)
                except Exception as e:
                    logger.warning(f"获取望远镜描述失败: {str(e)}")
                
                try:
                    self.driver_info = self.driver.get_driver_info()
                except Exception as e:
                    logger.warning(f"获取驱动信息失败: {str(e)}")
                
                # 启动更新计时器
                if not self.update_timer:
                    self.update_timer = QTimer(self)
                    self.update_timer.timeout.connect(self.update_status)
                    self.update_timer.start(1000)  # 每秒更新一次
                
                # 发出连接状态变更信号
                self.connected_changed.emit(True)
                
                return True
            else:
                logger.error("望远镜连接失败")
                self.error_occurred.emit("望远镜连接失败")
                return False
                
        except Exception as e:
            logger.error(f"连接望远镜时出错: {str(e)}")
            self.error_occurred.emit(f"连接错误: {str(e)}")
            return False
    
    @pyqtSlot()
    def disconnect(self) -> bool:
        """
        断开望远镜连接
        
        返回:
            操作是否成功
        """
        # 停止更新计时器
        if self.update_timer:
            self.update_timer.stop()
            self.update_timer = None
            
        if not self.driver or not self.is_connected:
            # 如果没有驱动或者已经断开，直接返回成功
            self.is_connected = False
            self.connected_changed.emit(False)
            return True
            
        try:
            # 调用驱动的断开连接方法
            logger.info("断开望远镜连接...")
            
            if self.driver.disconnect():
                logger.info("望远镜已断开连接")
                self.is_connected = False
                
                # 发出连接状态变更信号
                self.connected_changed.emit(False)
                
                return True
            else:
                logger.error("断开望远镜连接失败")
                return False
                
        except Exception as e:
            logger.error(f"断开望远镜连接时出错: {str(e)}")
            return False
    
    @pyqtSlot()
    def update_status(self):
        """更新望远镜状态"""
        if not self.driver or not self.is_connected:
            return
            
        try:
            # 获取位置信息
            try:
                ra, dec = self.driver.get_ra_dec()
                alt, az = self.driver.get_alt_az()
                
                # 检查是否有变化
                if (ra != self.right_ascension or
                    dec != self.declination or
                    alt != self.altitude or
                    az != self.azimuth):
                    
                    self.right_ascension = ra
                    self.declination = dec
                    self.altitude = alt
                    self.azimuth = az
                    
                    # 发出位置变更信号
                    self.position_changed.emit(ra, dec, alt, az)
            except Exception as e:
                logger.debug(f"获取位置信息失败: {str(e)}")
                
            # 获取跟踪状态
            try:
                tracking = self.driver.get_tracking()
                if tracking != self.is_tracking:
                    self.is_tracking = tracking
                    self.tracking_changed.emit(tracking)
            except Exception as e:
                logger.debug(f"获取跟踪状态失败: {str(e)}")
                
            # 获取转向状态
            try:
                slewing = self.driver.is_slewing()
                if slewing != self.is_slewing:
                    self.is_slewing = slewing
                    self.slewing_changed.emit(slewing)
            except Exception as e:
                logger.debug(f"获取转向状态失败: {str(e)}")
            
            # 获取停靠状态
            try:
                is_parked = self.driver.is_parked()
                if is_parked != self.is_parked:
                    self.is_parked = is_parked
                    self.parked_changed.emit(is_parked)
            except Exception as e:
                logger.debug(f"获取停靠状态失败: {str(e)}")
                
        except Exception as e:
            logger.error(f"更新望远镜状态时出错: {str(e)}")
    
    @pyqtSlot(bool)
    def set_tracking(self, enabled: bool) -> bool:
        """
        设置跟踪状态
        
        参数:
            enabled: 是否启用跟踪
        返回:
            操作是否成功
        """
        if not self.driver or not self.is_connected:
            self.error_occurred.emit("望远镜未连接")
            return False
            
        try:
            result = self.driver.set_tracking(enabled)
            if result:
                self.is_tracking = enabled
                self.tracking_changed.emit(enabled)
            return result
        except Exception as e:
            logger.error(f"设置跟踪状态失败: {str(e)}")
            self.error_occurred.emit(f"设置跟踪状态失败: {str(e)}")
            return False
    
    @pyqtSlot(float, float)
    def slew_to_coordinates(self, ra: float, dec: float) -> bool:
        """
        转向指定坐标
        
        参数:
            ra: 赤经（小时，0-24）
            dec: 赤纬（度，-90到+90）
        返回:
            操作是否成功
        """
        if not self.driver or not self.is_connected:
            self.error_occurred.emit("望远镜未连接")
            return False
            
        try:
            # 将赤经从小时转换为度
            ra_degrees = ra * 15.0  # 1小时 = 15度
            
            # 调用驱动方法（驱动程序接受度数格式）
            return self.driver.slew_to_coordinates(ra_degrees, dec)
        except Exception as e:
            logger.error(f"转向失败: {str(e)}")
            self.error_occurred.emit(f"转向失败: {str(e)}")
            return False
    
    @pyqtSlot(float, float)
    def slew_to_alt_az(self, alt: float, az: float) -> bool:
        """
        转向指定的地平坐标
        
        参数:
            alt: 高度角（度，-90到+90）
            az: 方位角（度，0-360）
        返回:
            操作是否成功
        """
        if not self.driver or not self.is_connected:
            self.error_occurred.emit("望远镜未连接")
            return False
            
        try:
            # 验证参数范围
            if alt < -90 or alt > 90:
                self.error_occurred.emit(f"高度角必须在-90到+90度范围内，当前值: {alt}")
                return False
                
            if az < 0 or az >= 360:
                self.error_occurred.emit(f"方位角必须在0到360度范围内，当前值: {az}")
                return False
            
            # 这里可以直接使用 AlpacaClient 的 slew_to_alt_az_async 方法
            # 由于我们现在使用 driver，这部分可以根据需求进行扩展
            # 目前先简单返回 True，后续可以进一步完善
            logger.info(f"转向地平坐标 - 高度角: {alt}度, 方位角: {az}度")
            return True
        except Exception as e:
            logger.error(f"转向地平坐标失败: {str(e)}")
            self.error_occurred.emit(f"转向地平坐标失败: {str(e)}")
            return False
    
    @pyqtSlot()
    def park(self) -> bool:
        """
        停靠望远镜
        
        返回:
            操作是否成功
        """
        if not self.driver or not self.is_connected:
            self.error_occurred.emit("望远镜未连接")
            return False
            
        try:
            return self.driver.park()
        except Exception as e:
            logger.error(f"停靠失败: {str(e)}")
            self.error_occurred.emit(f"停靠失败: {str(e)}")
            return False
    
    @pyqtSlot()
    def unpark(self) -> bool:
        """
        解除望远镜停靠
        
        返回:
            操作是否成功
        """
        if not self.driver or not self.is_connected:
            self.error_occurred.emit("望远镜未连接")
            return False
            
        try:
            return self.driver.unpark()
        except Exception as e:
            logger.error(f"解除停靠失败: {str(e)}")
            self.error_occurred.emit(f"解除停靠失败: {str(e)}")
            return False
    
    @pyqtSlot()
    def abort_slew(self) -> bool:
        """
        中止转向
        
        返回:
            操作是否成功
        """
        if not self.driver or not self.is_connected:
            self.error_occurred.emit("望远镜未连接")
            return False
            
        try:
            return self.driver.abort_slew()
        except Exception as e:
            logger.error(f"中止转向失败: {str(e)}")
            self.error_occurred.emit(f"中止转向失败: {str(e)}")
            return False