#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
旋转器模型模块
管理旋转器状态和数据，并提供信号通知视图层
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal

# 导入旋转器驱动
from devices.rotator.rotator_driver import RotatorDriver

# 设置日志
logger = logging.getLogger(__name__)

class RotatorModel(QObject):
    """
    旋转器模型类
    管理旋转器状态和数据，并提供信号通知视图层
    """
    # 定义信号
    connected_changed = pyqtSignal(bool)  # 连接状态变化信号
    position_changed = pyqtSignal(float)  # 位置变化信号
    name_changed = pyqtSignal(str)  # 名称变化信号
    description_changed = pyqtSignal(str)  # 描述变化信号
    moving_changed = pyqtSignal(bool)  # 移动状态变化信号
    reverse_changed = pyqtSignal(bool)  # 反转状态变化信号
    can_reverse_changed = pyqtSignal(bool)  # 反转能力变化信号
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, host: str = "localhost", port: int = 11111, device_number: int = 0):
        """
        初始化旋转器模型
        """
        super(RotatorModel, self).__init__()
        
        # 初始化旋转器驱动
        self.rotator_driver = None
        self.host = host
        self.port = port
        self.device_number = device_number
        
        # 旋转器状态
        self.connected = False  # 连接状态
        self.position = 0.0  # 当前位置（角度）
        self.is_moving = False  # 移动状态
        self.can_reverse = False  # 是否可以反转
        self.is_reversed = False  # 是否反转
        self.step_size = 0.0  # 步长（角度）
        self.target_position = 0.0  # 目标位置
        self.mechanical_position = 0.0  # 机械位置
        
        # 设备信息
        self.name = ""
        self.description = ""
        
        # 初始化实例
        self._initialize()
        
    def _initialize(self):
        """
        初始化模型
        """
        try:
            # 创建旋转器驱动实例
            self.rotator_driver = RotatorDriver(
                host=self.host,
                port=self.port,
                device_number=self.device_number
            )
        except Exception as e:
            logger.error(f"初始化旋转器模型失败: {str(e)}")
            self.error_occurred.emit(f"初始化旋转器模型失败: {str(e)}")
    
    def set_device_params(self, host: str, port: int, device_number: int):
        """
        设置设备参数
        """
        if (self.host != host or self.port != port or 
            self.device_number != device_number):
            
            # 如果已连接，先断开
            if self.connected:
                self.disconnect_device()
            
            # 更新参数
            self.host = host
            self.port = port
            self.device_number = device_number
            
            # 重新初始化
            self._initialize()
            
    def connect_device(self) -> bool:
        """
        连接旋转器设备
        """
        if not self.rotator_driver:
            logger.error("旋转器驱动未初始化")
            self.error_occurred.emit("旋转器驱动未初始化")
            return False
        
        try:
            # 记录连接参数
            logger.info(f"正在连接旋转器设备: {self.host}:{self.port}/{self.device_number}")
            
            # 尝试连接，最多重试3次
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"尝试连接 (第{attempt}/{max_retries}次)...")
                    
                    # 连接设备
                    result = self.rotator_driver.connect(timeout=10)
                    
                    if result:
                        self.connected = True
                        self.connected_changed.emit(True)
                        
                        # 连接后获取设备信息
                        try:
                            logger.info("正在获取旋转器设备信息...")
                            self._update_device_info()
                            logger.info("旋转器设备信息获取成功")
                        except Exception as info_err:
                            logger.error(f"获取旋转器设备信息失败: {str(info_err)}")
                            # 获取信息失败不影响连接状态
                        
                        logger.info("旋转器设备连接成功")
                        return True
                    else:
                        logger.warning(f"第{attempt}次连接尝试失败")
                        if attempt < max_retries:
                            import time
                            logger.info(f"等待1秒后重试...")
                            time.sleep(1)
                        else:
                            logger.error("旋转器设备连接失败，已达到最大重试次数")
                            self.error_occurred.emit("旋转器设备连接失败，请检查设备状态")
                
                except Exception as retry_err:
                    logger.error(f"第{attempt}次连接尝试出错: {str(retry_err)}")
                    if attempt < max_retries:
                        import time
                        logger.info(f"等待1秒后重试...")
                        time.sleep(1)
                    else:
                        raise  # 重新抛出异常，让外层处理
            
            return False
            
        except Exception as e:
            import traceback
            error_msg = f"连接旋转器设备时发生错误: {str(e)}"
            logger.error(error_msg)
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            self.error_occurred.emit(error_msg)
            return False
    
    def disconnect_device(self) -> bool:
        """
        断开旋转器设备连接
        """
        if not self.rotator_driver:
            return False
        
        try:
            # 断开设备连接
            result = self.rotator_driver.disconnect()
            
            if result:
                self.connected = False
                self.connected_changed.emit(False)
                logger.info("旋转器设备已断开连接")
                return True
            else:
                logger.error("断开旋转器设备连接失败")
                return False
        except Exception as e:
            logger.error(f"断开旋转器设备连接时发生错误: {str(e)}")
            return False
    
    def _update_device_info(self):
        """
        更新设备信息
        """
        if not self.connected or not self.rotator_driver:
            return
        
        # 分步骤获取设备信息，每一步单独处理异常
        
        # 获取设备名称
        try:
            self.name = self.rotator_driver.get_name()
            self.name_changed.emit(self.name)
        except Exception as e:
            logger.warning(f"获取旋转器名称失败: {str(e)}")
        
        # 获取设备描述
        try:
            self.description = self.rotator_driver.get_description()
            self.description_changed.emit(self.description)
        except Exception as e:
            logger.warning(f"获取旋转器描述失败: {str(e)}")
        
        # 获取步长
        try:
            self.step_size = self.rotator_driver.get_step_size()
        except Exception as e:
            logger.warning(f"获取旋转器步长失败: {str(e)}")
        
        # 获取当前位置
        try:
            self.position = self.rotator_driver.get_position()
            self.position_changed.emit(self.position)
        except Exception as e:
            logger.warning(f"获取旋转器位置失败: {str(e)}")
        
        # 获取目标位置
        try:
            self.target_position = self.rotator_driver.get_target_position()
        except Exception as e:
            logger.warning(f"获取旋转器目标位置失败: {str(e)}")
        
        # 获取机械位置
        try:
            self.mechanical_position = self.rotator_driver.get_mechanical_position()
        except Exception as e:
            logger.warning(f"获取旋转器机械位置失败: {str(e)}")
        
        # 获取移动状态
        try:
            # 直接通过API获取状态，避免调用is_moving()方法
            result = self.rotator_driver._get_request("ismoving")
            moving_status = result.get("Value", False)
            self.is_moving = moving_status
            self.moving_changed.emit(self.is_moving)
        except Exception as e:
            logger.warning(f"获取旋转器移动状态失败: {str(e)}")
            self.is_moving = False
            self.moving_changed.emit(False)
        
        # 获取反转能力
        try:
            # 直接通过API获取状态，避免调用can_reverse()方法
            result = self.rotator_driver._get_request("canreverse")
            can_reverse_status = result.get("Value", False)
            self.can_reverse = can_reverse_status
            self.can_reverse_changed.emit(self.can_reverse)
        except Exception as e:
            logger.warning(f"获取旋转器反转能力失败: {str(e)}")
            self.can_reverse = False
            self.can_reverse_changed.emit(False)
        
        # 获取反转状态
        try:
            # 直接通过API获取状态，避免调用is_reversed()方法
            result = self.rotator_driver._get_request("reverse")
            is_reversed_status = result.get("Value", False)
            self.is_reversed = is_reversed_status
            self.reverse_changed.emit(self.is_reversed)
        except Exception as e:
            logger.warning(f"获取旋转器反转状态失败: {str(e)}")
            self.is_reversed = False
            self.reverse_changed.emit(False)
    
    def update_position(self):
        """
        更新位置信息
        """
        if not self.connected or not self.rotator_driver:
            return
        
        # 获取位置
        try:
            position = self.rotator_driver.get_position()
            
            # 如果位置发生变化，发送信号
            if position != self.position:
                self.position = position
                self.position_changed.emit(self.position)
        except Exception as e:
            logger.warning(f"更新旋转器位置失败: {str(e)}")
        
        # 获取机械位置
        try:
            mechanical_position = self.rotator_driver.get_mechanical_position()
            self.mechanical_position = mechanical_position
        except Exception as e:
            logger.warning(f"更新旋转器机械位置失败: {str(e)}")
            
        # 获取目标位置
        try:
            target_position = self.rotator_driver.get_target_position()
            self.target_position = target_position
        except Exception as e:
            logger.warning(f"更新旋转器目标位置失败: {str(e)}")
        
        # 获取移动状态 - 不要直接调用is_moving()方法，而是直接获取API数据
        try:
            # 直接通过API获取状态
            result = self.rotator_driver._get_request("ismoving")
            moving_status = result.get("Value", False)
            
            # 如果移动状态发生变化，发送信号
            if moving_status != self.is_moving:
                self.is_moving = moving_status
                self.moving_changed.emit(self.is_moving)
        except Exception as e:
            logger.warning(f"更新旋转器移动状态失败: {str(e)}")
    
    def move_to_position(self, position: float) -> bool:
        """
        移动旋转器到指定位置
        
        参数:
            position: 目标位置（角度）
        """
        if not self.connected or not self.rotator_driver:
            self.error_occurred.emit("旋转器未连接")
            return False
        
        try:
            # 移动到指定位置
            result = self.rotator_driver.move_to(position)
            
            if result:
                # 更新移动状态
                self.is_moving = True
                self.moving_changed.emit(True)
                # 更新目标位置
                self.target_position = position
                
                # 立即更新所有位置信息
                try:
                    # 更新目标位置（再次确认）
                    self.target_position = self.rotator_driver.get_target_position()
                    # 更新机械位置
                    self.mechanical_position = self.rotator_driver.get_mechanical_position()
                except Exception as update_err:
                    logger.warning(f"移动后更新位置信息失败: {str(update_err)}")
                
                return True
            else:
                self.error_occurred.emit("移动旋转器失败")
                return False
                
        except Exception as e:
            logger.error(f"移动旋转器时发生错误: {str(e)}")
            self.error_occurred.emit(f"移动旋转器时发生错误: {str(e)}")
            return False
    
    def move_by(self, relative_position: float) -> bool:
        """
        移动旋转器相对位置
        
        参数:
            relative_position: 相对移动量（角度）
        """
        if not self.connected or not self.rotator_driver:
            self.error_occurred.emit("旋转器未连接")
            return False
        
        try:
            # 移动相对位置
            result = self.rotator_driver.move_by(relative_position)
            
            if result:
                # 更新移动状态
                self.is_moving = True
                self.moving_changed.emit(True)
                return True
            else:
                self.error_occurred.emit("移动旋转器相对位置失败")
                return False
                
        except Exception as e:
            logger.error(f"移动旋转器相对位置时发生错误: {str(e)}")
            self.error_occurred.emit(f"移动旋转器相对位置时发生错误: {str(e)}")
            return False
    
    def halt(self) -> bool:
        """
        停止旋转器移动
        """
        if not self.connected or not self.rotator_driver:
            return False
        
        try:
            # 停止移动
            result = self.rotator_driver.halt()
            
            if result:
                # 更新移动状态
                self.is_moving = False
                self.moving_changed.emit(False)
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"停止旋转器移动时发生错误: {str(e)}")
            return False
    
    def sync_position(self, position: float) -> bool:
        """
        同步旋转器位置
        
        参数:
            position: 同步位置（角度）
        """
        if not self.connected or not self.rotator_driver:
            self.error_occurred.emit("旋转器未连接")
            return False
        
        try:
            # 同步位置
            result = self.rotator_driver.sync(position)
            
            if result:
                # 更新位置
                self.position = position
                self.position_changed.emit(position)
                
                # 同步后立即更新所有位置信息
                try:
                    # 更新机械位置
                    self.mechanical_position = self.rotator_driver.get_mechanical_position()
                    # 更新目标位置
                    self.target_position = self.rotator_driver.get_target_position()
                except Exception as update_err:
                    logger.warning(f"同步后更新位置信息失败: {str(update_err)}")
                
                return True
            else:
                self.error_occurred.emit("同步旋转器位置失败")
                return False
                
        except Exception as e:
            logger.error(f"同步旋转器位置时发生错误: {str(e)}")
            self.error_occurred.emit(f"同步旋转器位置时发生错误: {str(e)}")
            return False
    
    def set_reverse(self, reverse: bool) -> bool:
        """
        设置旋转器反转状态
        
        参数:
            reverse: 是否反转
        """
        if not self.connected or not self.rotator_driver:
            self.error_occurred.emit("旋转器未连接")
            return False
        
        if not self.can_reverse:
            self.error_occurred.emit("此旋转器不支持反转功能")
            return False
        
        try:
            # 设置反转状态
            result = self.rotator_driver.set_reverse(reverse)
            
            if result:
                # 更新反转状态
                self.is_reversed = reverse
                self.reverse_changed.emit(reverse)
                return True
            else:
                self.error_occurred.emit("设置旋转器反转状态失败")
                return False
                
        except Exception as e:
            logger.error(f"设置旋转器反转状态时发生错误: {str(e)}")
            self.error_occurred.emit(f"设置旋转器反转状态时发生错误: {str(e)}")
            return False
    
    def move_to_mechanical_position(self, position: float) -> bool:
        """
        移动旋转器到指定机械位置
        
        参数:
            position: 机械位置（角度）
        """
        if not self.connected or not self.rotator_driver:
            self.error_occurred.emit("旋转器未连接")
            return False
        
        try:
            # 使用正确的机械位置移动API
            result = self.rotator_driver.move_mechanical(position)
            
            if result:
                # 更新移动状态
                self.is_moving = True
                self.moving_changed.emit(True)
                self.target_position = position
                logger.info(f"开始移动旋转器到机械位置: {position}°")
                return True
            else:
                self.error_occurred.emit("移动旋转器到机械位置失败")
                return False
                
        except Exception as e:
            logger.error(f"移动旋转器到机械位置时发生错误: {str(e)}")
            self.error_occurred.emit(f"移动旋转器到机械位置时发生错误: {str(e)}")
            return False 