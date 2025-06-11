#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
镜头盖/校准器模型类
用于管理ASCOM Alpaca镜头盖/校准器设备
"""

import logging
import time
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

# 设置日志
logger = logging.getLogger(__name__)

class CoverCalibratorModel(QObject):
    """
    镜头盖/校准器模型类，管理ASCOM Alpaca镜头盖/校准器设备
    """
    # 定义信号
    connected_changed = pyqtSignal(bool)  # 连接状态变化信号
    name_changed = pyqtSignal(str)  # 设备名称变化信号
    description_changed = pyqtSignal(str)  # 设备描述变化信号
    cover_state_changed = pyqtSignal(str)  # 盖板状态变化信号
    cover_moving_changed = pyqtSignal(bool)  # 盖板移动状态变化信号
    calibrator_state_changed = pyqtSignal(str)  # 校准器状态变化信号
    calibrator_changing_changed = pyqtSignal(bool)  # 校准器变化状态变化信号
    brightness_changed = pyqtSignal(int)  # 亮度变化信号
    error_occurred = pyqtSignal(str)  # 错误信号

    def __init__(self):
        super(CoverCalibratorModel, self).__init__()
        
        # 设备状态
        self._connected = False
        self._name = ""
        self._description = ""
        self._cover_state = "Unknown"  # 盖板状态：Unknown, NotPresent, Closed, Moving, Open
        self._cover_moving = False  # 盖板是否移动中
        self._calibrator_state = "Unknown"  # 校准器状态：Unknown, NotPresent, Off, Ready, CalibrationRequired, On
        self._calibrator_changing = False  # 校准器是否变化中
        self._brightness = 0  # 校准器亮度（0-100）
        
        # 设备功能标志
        self._cover_present = False
        self._calibrator_present = False
        self._max_brightness = 100
        
        # 设备驱动
        self._device_driver = None
        
        # 设备连接参数
        self._host = "localhost"
        self._port = 11111
        self._device_number = 0
    
    # 属性getter/setter
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
    def cover_state(self):
        return self._cover_state
    
    @property
    def cover_moving(self):
        return self._cover_moving
    
    @property
    def calibrator_state(self):
        return self._calibrator_state
    
    @property
    def calibrator_changing(self):
        return self._calibrator_changing
    
    @property
    def brightness(self):
        return self._brightness
        
    @property
    def cover_present(self):
        return self._cover_present
    
    @property
    def calibrator_present(self):
        return self._calibrator_present
    
    @property
    def max_brightness(self):
        return self._max_brightness
    
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
            
            # 连接到CoverCalibrator设备
            self._device_driver = client.get_device('covercalibrator', self._device_number)
            
            # 使用新的connect_device方法确保设备真正连接
            connection_result = self._device_driver.connect_device()
            if not connection_result:
                logger.error("设备连接失败，无法继续初始化")
                self.error_occurred.emit("设备连接失败，请检查设备状态和连接设置")
                return False
            
            # 获取设备信息
            try:
                self._name = self._device_driver.get_name()
                self._description = self._device_driver.get_description()
            except Exception as info_e:
                logger.warning(f"获取设备信息失败，但继续连接过程: {str(info_e)}")
                self._name = "Unknown Device"
                self._description = "Unknown Description"
            
            # 发送设备信息更新信号
            self.name_changed.emit(self._name)
            self.description_changed.emit(self._description)
            
            # 检查设备功能
            try:
                self._cover_present = self._device_driver.get_cover_state() != "NotPresent"
                self._calibrator_present = self._device_driver.get_calibrator_state() != "NotPresent"
            except Exception as feature_e:
                logger.warning(f"检查设备功能失败，假设功能可用: {str(feature_e)}")
                self._cover_present = True
                self._calibrator_present = True
            
            # 获取最大亮度
            if self._calibrator_present:
                try:
                    self._max_brightness = self._device_driver.get_max_brightness()
                except Exception as max_e:
                    logger.warning(f"获取最大亮度失败，使用默认值100: {str(max_e)}")
                    self._max_brightness = 100
            
            # 更新设备状态
            self.update_device_state()
            
            # 设置连接状态
            self._connected = True
            self.connected_changed.emit(True)
            
            logger.info(f"成功连接镜头盖/校准器设备: {self._name}")
            return True
        
        except Exception as e:
            self.error_occurred.emit(f"连接镜头盖/校准器设备失败: {str(e)}")
            logger.error(f"连接镜头盖/校准器设备失败: {str(e)}")
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
            self._cover_state = "Unknown"
            self._cover_moving = False
            self._calibrator_state = "Unknown"
            self._calibrator_changing = False
            self._brightness = 0
            
            # 发送信号
            self.connected_changed.emit(False)
            self.cover_state_changed.emit(self._cover_state)
            self.cover_moving_changed.emit(self._cover_moving)
            self.calibrator_state_changed.emit(self._calibrator_state)
            self.calibrator_changing_changed.emit(self._calibrator_changing)
            self.brightness_changed.emit(self._brightness)
            
            logger.info("镜头盖/校准器设备已断开连接")
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"断开镜头盖/校准器设备连接失败: {str(e)}")
            logger.error(f"断开镜头盖/校准器设备连接失败: {str(e)}")
            return False
    
    def update_device_state(self):
        """更新设备状态"""
        if not self._connected or not self._device_driver:
            return
        
        try:
            # 获取盖板状态
            if self._cover_present:
                new_cover_state = self._device_driver.get_cover_state()
                if new_cover_state != self._cover_state:
                    self._cover_state = new_cover_state
                    self.cover_state_changed.emit(self._cover_state)
                
                # 根据cover_state判断是否移动中
                self._cover_moving = (self._cover_state == "Moving")
                self.cover_moving_changed.emit(self._cover_moving)
            
            # 获取校准器状态
            if self._calibrator_present:
                new_calibrator_state = self._device_driver.get_calibrator_state()
                if new_calibrator_state != self._calibrator_state:
                    self._calibrator_state = new_calibrator_state
                    self.calibrator_state_changed.emit(self._calibrator_state)
                
                # 根据状态变化来判断是否在变化中
                self._calibrator_changing = (self._calibrator_state == "On" and self._brightness == 0) or \
                                           (self._calibrator_state == "Off" and self._brightness > 0)
                self.calibrator_changing_changed.emit(self._calibrator_changing)
                
                # 如果校准器开启，获取亮度
                if new_calibrator_state == "On":
                    new_brightness = self._device_driver.get_brightness()
                    if new_brightness != self._brightness:
                        self._brightness = new_brightness
                        self.brightness_changed.emit(self._brightness)
        
        except Exception as e:
            logger.error(f"更新镜头盖/校准器状态失败: {str(e)}")
    
    def open_cover(self):
        """打开镜头盖"""
        if not self._connected or not self._device_driver:
            self.error_occurred.emit("设备未连接")
            return False
            
        if not self._cover_present:
            self.error_occurred.emit("此设备没有盖板功能")
            return False
            
        try:
            self._device_driver.open_cover()
            logger.info("发送打开镜头盖命令")
            
            # 更新状态
            self._cover_state = "Moving"
            self.cover_state_changed.emit(self._cover_state)
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"打开镜头盖失败: {str(e)}")
            logger.error(f"打开镜头盖失败: {str(e)}")
            return False
    
    def close_cover(self):
        """关闭镜头盖"""
        if not self._connected or not self._device_driver:
            self.error_occurred.emit("设备未连接")
            return False
            
        if not self._cover_present:
            self.error_occurred.emit("此设备没有盖板功能")
            return False
            
        try:
            self._device_driver.close_cover()
            logger.info("发送关闭镜头盖命令")
            
            # 更新状态
            self._cover_state = "Moving"
            self.cover_state_changed.emit(self._cover_state)
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"关闭镜头盖失败: {str(e)}")
            logger.error(f"关闭镜头盖失败: {str(e)}")
            return False
    
    def halt_cover(self):
        """停止镜头盖操作"""
        if not self._connected or not self._device_driver:
            self.error_occurred.emit("设备未连接")
            return False
            
        if not self._cover_present:
            self.error_occurred.emit("此设备没有盖板功能")
            return False
            
        try:
            self._device_driver.halt_cover()
            logger.info("发送停止镜头盖操作命令")
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"停止镜头盖操作失败: {str(e)}")
            logger.error(f"停止镜头盖操作失败: {str(e)}")
            return False
    
    def calibrator_on(self, brightness=None):
        """开启校准器"""
        if not self._connected or not self._device_driver:
            self.error_occurred.emit("设备未连接")
            return False
            
        if not self._calibrator_present:
            self.error_occurred.emit("此设备没有校准器功能")
            return False
            
        try:
            # 如果提供了亮度参数，使用指定亮度开启
            if brightness is not None:
                # 确保亮度在有效范围内（允许亮度为0）
                brightness = max(0, min(brightness, self._max_brightness))
                # 记录日志
                logger.info(f"调用calibrator_on方法，亮度: {brightness}")
                success = self._device_driver.calibrator_on(brightness)
                if not success:
                    self.error_occurred.emit(f"开启校准器失败，亮度: {brightness}")
                    logger.error(f"开启校准器失败，亮度: {brightness}")
                    return False
                
                logger.info(f"校准器已成功开启，亮度: {brightness}")
            else:
                # 否则使用默认亮度（最大值）
                logger.info(f"调用calibrator_on方法，使用最大亮度: {self._max_brightness}")
                success = self._device_driver.calibrator_on(self._max_brightness)
                if not success:
                    self.error_occurred.emit(f"开启校准器失败，使用最大亮度: {self._max_brightness}")
                    logger.error(f"开启校准器失败，使用最大亮度: {self._max_brightness}")
                    return False
                
                logger.info(f"校准器已成功开启，使用最大亮度: {self._max_brightness}")
                brightness = self._max_brightness
            
            # 更新状态
            self._calibrator_state = "On"
            self.calibrator_state_changed.emit(self._calibrator_state)
            
            # 更新亮度
            if brightness is not None:
                self._brightness = brightness
                self.brightness_changed.emit(self._brightness)
                
            # 校验状态和亮度是否正确更新
            try:
                # 获取最新状态
                new_state = self._device_driver.get_calibrator_state()
                if new_state != "On":
                    logger.warning(f"校准器状态不一致：预期为On，实际为{new_state}")
                
                # 获取最新亮度
                new_brightness = self._device_driver.get_brightness()
                if new_brightness != brightness:
                    logger.warning(f"校准器亮度不一致：预期为{brightness}，实际为{new_brightness}")
                    # 更新为实际亮度
                    self._brightness = new_brightness
                    self.brightness_changed.emit(self._brightness)
            except Exception as e:
                logger.warning(f"校验校准器状态失败: {str(e)}")
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"开启校准器失败: {str(e)}")
            logger.error(f"开启校准器失败: {str(e)}")
            return False
    
    def calibrator_off(self):
        """关闭校准器"""
        if not self._connected or not self._device_driver:
            self.error_occurred.emit("设备未连接")
            return False
            
        if not self._calibrator_present:
            self.error_occurred.emit("此设备没有校准器功能")
            return False
            
        try:
            self._device_driver.calibrator_off()
            logger.info("发送关闭校准器命令")
            
            # 更新状态
            self._calibrator_state = "Off"
            self._brightness = 0
            
            self.calibrator_state_changed.emit(self._calibrator_state)
            self.brightness_changed.emit(self._brightness)
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"关闭校准器失败: {str(e)}")
            logger.error(f"关闭校准器失败: {str(e)}")
            return False
    
    def set_brightness(self, brightness):
        """设置校准器亮度"""
        if not self._connected or not self._device_driver:
            self.error_occurred.emit("设备未连接")
            return False
            
        if not self._calibrator_present:
            self.error_occurred.emit("此设备没有校准器功能")
            return False
            
        try:
            # 确保亮度在有效范围内
            brightness = max(0, min(brightness, self._max_brightness))
            
            # 检查校准器当前状态
            if self._calibrator_state == "On":
                logger.info(f"校准器已开启，设置亮度: {brightness}")
                # 如果校准器已开启，使用set_brightness方法设置亮度
                result = self._device_driver.set_brightness(brightness)
                if not result:
                    self.error_occurred.emit(f"设置亮度失败: {brightness}")
                    logger.error(f"设置亮度失败: {brightness}")
                    return False
            else:
                logger.info(f"校准器未开启，需要先调用calibrator_on方法开启校准器，亮度: {brightness}")
                # 校准器未开启，不能设置亮度，只通过calibrator_on方法开启时才能设置亮度
                self.error_occurred.emit("校准器未开启，请先点击'开启校准器'按钮")
                return False
                
            # 更新亮度状态
            self._brightness = brightness
            self.brightness_changed.emit(self._brightness)
            logger.info(f"亮度已成功设置为: {brightness}")
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"设置校准器亮度失败: {str(e)}")
            logger.error(f"设置校准器亮度失败: {str(e)}")
            return False 