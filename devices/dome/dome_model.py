#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
圆顶模型类
将DomeDriver封装为Qt友好的模型
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer

# 导入我们的圆顶驱动
from unified_driver import DomeDriver

# 设置日志
logger = logging.getLogger(__name__)

class DomeModel(QObject):
    """圆顶模型类，封装DomeDriver并提供Qt信号"""
    
    # 定义信号
    connected_changed = pyqtSignal(bool)
    position_changed = pyqtSignal(float)  # azimuth
    altitude_changed = pyqtSignal(float)  # altitude
    name_changed = pyqtSignal(str)
    description_changed = pyqtSignal(str)
    driver_info_changed = pyqtSignal(str)  # 驱动信息变更信号
    driver_version_changed = pyqtSignal(str)  # 驱动版本变更信号
    slewing_changed = pyqtSignal(bool)
    shutter_changed = pyqtSignal(int)
    parked_changed = pyqtSignal(bool)
    slaved_changed = pyqtSignal(bool)
    at_home_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super(DomeModel, self).__init__(parent)
        
        self.driver = None
        self.is_connected = False
        self.update_timer = None
        
        # 圆顶属性
        self.azimuth = 0.0
        self.altitude = 0.0
        self.name = ""
        self.description = ""
        self.driver_info = ""
        self.driver_version = ""
        self.is_slewing = False
        self.is_parked = False
        self.is_slaved = False
        self.shutter_status = 1  # 默认关闭
        self.is_at_home = False
        
    def initialize(self, host: str = "localhost", port: int = 11111, device_number: int = 0):
        """
        初始化圆顶驱动
        
        参数:
            host: Alpaca服务器主机名或IP
            port: Alpaca服务器端口
            device_number: 设备编号
        """
        try:
            logger.info(f"初始化圆顶驱动: {host}:{port}")
            
            # 断开现有连接
            self.disconnect()
            
            # 创建新的驱动实例
            self.driver = DomeDriver(host=host, port=port, device_number=device_number)
            
            # 重置属性
            self.is_connected = False
            self.azimuth = 0.0
            self.altitude = 0.0
            self.name = ""
            self.description = ""
            self.driver_info = ""
            self.driver_version = ""
            self.is_slewing = False
            self.is_parked = False
            self.is_slaved = False
            self.shutter_status = 1  # 默认关闭
            self.is_at_home = False
            
            return True
        except Exception as e:
            logger.error(f"圆顶模型初始化失败: {str(e)}")
            self.error_occurred.emit(f"初始化失败: {str(e)}")
            return False
    
    @pyqtSlot()
    def connect(self) -> bool:
        if not self.driver:
            logger.error("圆顶驱动未初始化")
            self.error_occurred.emit("圆顶驱动未初始化")
            return False
            
        try:
            # 调用驱动的连接方法
            logger.info("开始连接圆顶...")
            
            if self.driver.connect():
                self.is_connected = True
                
                # 获取设备信息
                try:
                    self.name = self.driver.get_name()
                    self.name_changed.emit(self.name)
                except Exception as e:
                    logger.warning(f"获取圆顶名称失败: {str(e)}")
                    
                try:
                    self.description = self.driver.get_description()
                    self.description_changed.emit(self.description)
                except Exception as e:
                    logger.warning(f"获取圆顶描述失败: {str(e)}")
                
                try:
                    self.driver_info = self.driver.get_driver_info()
                    self.driver_info_changed.emit(self.driver_info)
                except Exception as e:
                    logger.warning(f"获取驱动信息失败: {str(e)}")
                
                try:
                    self.driver_version = self.driver.get_driver_version()
                    self.driver_version_changed.emit(self.driver_version)
                except Exception as e:
                    logger.warning(f"获取驱动版本失败: {str(e)}")
                
                # 启动更新计时器
                if not self.update_timer:
                    self.update_timer = QTimer(self)
                    self.update_timer.timeout.connect(self.update_status)
                    self.update_timer.start(1000)  # 每秒更新一次
                
                # 发出连接状态变更信号
                self.connected_changed.emit(True)
                
                return True
            else:
                logger.error("圆顶连接失败")
                self.error_occurred.emit("圆顶连接失败")
                return False
                
        except Exception as e:
            logger.error(f"连接圆顶时出错: {str(e)}")
            self.error_occurred.emit(f"连接错误: {str(e)}")
            return False
    
    @pyqtSlot()
    def disconnect(self) -> bool:
        """
        断开圆顶连接
        
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
            logger.info("断开圆顶连接...")
            
            if self.driver.disconnect():
                logger.info("圆顶已断开连接")
                self.is_connected = False
                
                # 发出连接状态变更信号
                self.connected_changed.emit(False)
                
                return True
            else:
                logger.error("断开圆顶连接失败")
                return False
                
        except Exception as e:
            logger.error(f"断开圆顶连接时出错: {str(e)}")
            return False
    
    @pyqtSlot()
    def update_status(self):
        """更新圆顶状态"""
        if not self.driver or not self.is_connected:
            return
            
        try:
            # 获取位置信息
            try:
                azimuth = self.driver.get_azimuth()
                if azimuth != self.azimuth:
                    self.azimuth = azimuth
                    self.position_changed.emit(self.azimuth)
            except Exception as e:
                logger.debug(f"获取圆顶方位角失败: {str(e)}")
                
            try:
                altitude = self.driver.get_altitude()
                if altitude != self.altitude:
                    self.altitude = altitude
                    self.altitude_changed.emit(self.altitude)
            except Exception as e:
                logger.debug(f"获取圆顶高度角失败: {str(e)}")
            
            # 获取天窗状态
            try:
                shutter_status = self.driver.get_shutter_status()
                if shutter_status != self.shutter_status:
                    self.shutter_status = shutter_status
                    self.shutter_changed.emit(self.shutter_status)
            except Exception as e:
                logger.debug(f"获取天窗状态失败: {str(e)}")
            
            # 获取转向状态
            try:
                is_slewing = self.driver.is_slewing()
                if is_slewing != self.is_slewing:
                    self.is_slewing = is_slewing
                    self.slewing_changed.emit(self.is_slewing)
            except Exception as e:
                logger.debug(f"获取转向状态失败: {str(e)}")
            
            # 获取停靠状态
            try:
                is_parked = self.driver.is_parked()
                if is_parked != self.is_parked:
                    self.is_parked = is_parked
                    self.parked_changed.emit(self.is_parked)
            except Exception as e:
                logger.debug(f"获取停靠状态失败: {str(e)}")
            
            # 获取同步状态
            try:
                is_slaved = self.driver.get_slaved()
                if is_slaved != self.is_slaved:
                    self.is_slaved = is_slaved
                    self.slaved_changed.emit(self.is_slaved)
            except Exception as e:
                logger.debug(f"获取同步状态失败: {str(e)}")
            
            # 获取原点状态
            try:
                is_at_home = self.driver.is_at_home()
                if is_at_home != self.is_at_home:
                    self.is_at_home = is_at_home
                    self.at_home_changed.emit(self.is_at_home)
            except Exception as e:
                logger.debug(f"获取原点状态失败: {str(e)}")
                
        except Exception as e:
            logger.error(f"更新圆顶状态时出错: {str(e)}")
    
    @pyqtSlot(float)
    def slew_to_azimuth(self, azimuth: float) -> bool:
        """
        控制圆顶转向指定的方位角
        
        参数:
            azimuth: 目标方位角（度，0-359.99）
        返回:
            操作是否成功
        """
        if not self.driver or not self.is_connected:
            self.error_occurred.emit("圆顶未连接")
            return False
        
        try:
            logger.info(f"控制圆顶转向方位角: {azimuth}度")
            return self.driver.slew_to_azimuth(azimuth)
        except Exception as e:
            error_msg = f"转向失败: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    @pyqtSlot()
    def abort_slew(self) -> bool:
        """
        中止当前转向操作
        
        返回:
            操作是否成功
        """
        if not self.driver or not self.is_connected:
            self.error_occurred.emit("圆顶未连接")
            return False
            
        try:
            logger.info("中止圆顶转向")
            return self.driver.abort_slew()
        except Exception as e:
            error_msg = f"中止转向失败: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    @pyqtSlot()
    def open_shutter(self) -> bool:
        """
        打开圆顶天窗
        
        返回:
            操作是否成功
        """
        if not self.driver or not self.is_connected:
            self.error_occurred.emit("圆顶未连接")
            return False
            
        try:
            logger.info("打开圆顶天窗")
            return self.driver.open_shutter()
        except Exception as e:
            error_msg = f"打开天窗失败: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    @pyqtSlot()
    def close_shutter(self) -> bool:
        """
        关闭圆顶天窗
        
        返回:
            操作是否成功
        """
        if not self.driver or not self.is_connected:
            self.error_occurred.emit("圆顶未连接")
            return False
            
        try:
            logger.info("关闭圆顶天窗")
            return self.driver.close_shutter()
        except Exception as e:
            error_msg = f"关闭天窗失败: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    @pyqtSlot(bool)
    def set_slaved(self, slaved: bool) -> bool:
        """
        设置圆顶是否跟随望远镜
        
        参数:
            slaved: 是否跟随望远镜
        返回:
            操作是否成功
        """
        if not self.driver or not self.is_connected:
            self.error_occurred.emit("圆顶未连接")
            return False
            
        try:
            logger.info(f"设置圆顶跟随状态: {slaved}")
            result = self.driver.set_slaved(slaved)
            
            if result:
                # 更新状态并发送信号
                self.is_slaved = slaved
                self.slaved_changed.emit(self.is_slaved)
                
            return result
        except Exception as e:
            # 直接向上传递错误，让驱动层处理
            logger.error(f"设置跟随状态失败: {str(e)}")
            self.error_occurred.emit(f"设置跟随状态失败: {str(e)}")
            return False
    
