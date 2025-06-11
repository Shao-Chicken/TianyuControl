#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
电调焦模型模块
管理电调焦状态和数据，并提供信号通知视图层
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal

# 导入电调焦驱动
from devices.focuser.focuser_driver import FocuserDriver

# 设置日志
logger = logging.getLogger(__name__)

class FocuserModel(QObject):
    """
    电调焦模型类
    管理电调焦状态和数据，并提供信号通知视图层
    """
    # 定义信号
    connected_changed = pyqtSignal(bool)  # 连接状态变化信号
    position_changed = pyqtSignal(int)  # 位置变化信号
    name_changed = pyqtSignal(str)  # 名称变化信号
    description_changed = pyqtSignal(str)  # 描述变化信号
    moving_changed = pyqtSignal(bool)  # 移动状态变化信号
    temperature_changed = pyqtSignal(float)  # 温度变化信号
    temp_comp_changed = pyqtSignal(bool)  # 温度补偿状态变化信号
    absolute_changed = pyqtSignal(bool)  # 绝对定位能力信号
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, host: str = "localhost", port: int = 11111, device_number: int = 1):
        """
        初始化电调焦模型
        """
        super(FocuserModel, self).__init__()
        
        # 初始化电调焦驱动
        self.focuser_driver = None
        self.host = host
        self.port = port
        self.device_number = device_number
        
        # 电调焦状态
        self.connected = False  # 连接状态
        self.position = 0  # 当前位置
        self.is_moving = False  # 移动状态
        self.is_move_monitored = False  # 是否有移动监控线程正在运行
        self.temperature = 0.0  # 当前温度
        self.min_step = 0  # 最小位置
        self.max_step = 10000  # 最大位置
        self.step_size = 0.0  # 步长（微米）
        self.temp_comp = False
        self.temp_comp_available = False
        self.absolute = False  # 添加绝对定位能力属性
        
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
            # 创建电调焦驱动实例
            self.focuser_driver = FocuserDriver(
                host=self.host,
                port=self.port,
                device_number=self.device_number
            )
        except Exception as e:
            logger.error(f"初始化电调焦模型失败: {str(e)}")
            self.error_occurred.emit(f"初始化电调焦模型失败: {str(e)}")
    
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
        连接电调焦设备
        """
        if not self.focuser_driver:
            logger.error("电调焦驱动未初始化")
            self.error_occurred.emit("电调焦驱动未初始化")
            return False
        
        try:
            # 记录连接参数
            logger.info(f"正在连接电调焦设备: {self.host}:{self.port}/{self.device_number}")
            
            # 尝试连接，最多重试3次
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"尝试连接 (第{attempt}/{max_retries}次)...")
                    
                    # 连接设备
                    result = self.focuser_driver.connect(timeout=10)
                    
                    if result:
                        self.connected = True
                        self.connected_changed.emit(True)
                        
                        # 连接后获取设备信息
                        try:
                            logger.info("正在获取电调焦设备信息...")
                            self._update_device_info()
                            logger.info("电调焦设备信息获取成功")
                        except Exception as info_err:
                            logger.error(f"获取电调焦设备信息失败: {str(info_err)}")
                            # 获取信息失败不影响连接状态
                        
                        logger.info("电调焦设备连接成功")
                        return True
                    else:
                        logger.warning(f"第{attempt}次连接尝试失败")
                        if attempt < max_retries:
                            import time
                            logger.info(f"等待1秒后重试...")
                            time.sleep(1)
                        else:
                            logger.error("电调焦设备连接失败，已达到最大重试次数")
                            self.error_occurred.emit("电调焦设备连接失败，请检查设备状态")
                
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
            error_msg = f"连接电调焦设备时发生错误: {str(e)}"
            logger.error(error_msg)
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            self.error_occurred.emit(error_msg)
            return False
    
    def disconnect_device(self) -> bool:
        """
        断开电调焦设备连接
        """
        if not self.focuser_driver:
            return False
        
        try:
            # 断开设备连接
            result = self.focuser_driver.disconnect()
            
            if result:
                self.connected = False
                self.connected_changed.emit(False)
                logger.info("电调焦设备已断开连接")
                return True
            else:
                logger.error("断开电调焦设备连接失败")
                return False
        except Exception as e:
            logger.error(f"断开电调焦设备连接时发生错误: {str(e)}")
            return False
    
    def _update_device_info(self):
        """
        更新设备信息
        """
        if not self.connected or not self.focuser_driver:
            return
        
        # 分步骤获取设备信息，每一步单独处理异常
        
        # 获取设备名称
        try:
            self.name = self.focuser_driver.get_name()
            self.name_changed.emit(self.name)
        except Exception as e:
            logger.warning(f"获取电调焦名称失败: {str(e)}")
        
        # 获取设备描述
        try:
            self.description = self.focuser_driver.get_description()
            self.description_changed.emit(self.description)
        except Exception as e:
            logger.warning(f"获取电调焦描述失败: {str(e)}")
        
        # 获取最大步数
        try:
            self.max_step = self.focuser_driver.get_max_step()
        except Exception as e:
            logger.warning(f"获取电调焦最大步数失败: {str(e)}")
        
        # 获取最小步数
        try:
            self.min_step = self.focuser_driver.get_min_step()
        except Exception as e:
            logger.warning(f"获取电调焦最小步数失败: {str(e)}")
        
        # 获取步长
        try:
            self.step_size = self.focuser_driver.get_step_size()
        except Exception as e:
            logger.warning(f"获取电调焦步长失败: {str(e)}")
        
        # 获取温度补偿可用性
        try:
            self.temp_comp_available = self.focuser_driver.is_temperature_compensation_available()
        except TypeError:
            # 如果这是一个布尔值而不是方法
            logger.warning("is_temperature_compensation_available可能是属性而非方法")
            try:
                self.temp_comp_available = getattr(self.focuser_driver, "temp_comp_available", False)
            except:
                self.temp_comp_available = False
        except Exception as e:
            logger.warning(f"获取温度补偿可用性失败: {str(e)}")
            self.temp_comp_available = False
        
        # 获取温度补偿状态
        if self.temp_comp_available:
            try:
                temp_comp_value = self.focuser_driver.get_temperature_compensation()
                self.temp_comp = temp_comp_value
                self.temp_comp_changed.emit(self.temp_comp)
            except TypeError:
                # 如果这是一个布尔值而不是方法
                logger.warning("get_temperature_compensation可能是属性而非方法")
                try:
                    self.temp_comp = getattr(self.focuser_driver, "temperature_compensation", False)
                    self.temp_comp_changed.emit(self.temp_comp)
                except:
                    self.temp_comp = False
                    self.temp_comp_changed.emit(False)
            except Exception as e:
                logger.warning(f"获取温度补偿状态失败: {str(e)}")
                self.temp_comp = False
                self.temp_comp_changed.emit(False)
        
        # 获取当前位置
        try:
            self.position = self.focuser_driver.get_position()
            self.position_changed.emit(self.position)
        except Exception as e:
            logger.warning(f"获取电调焦位置失败: {str(e)}")
        
        # 获取当前温度
        try:
            self.temperature = self.focuser_driver.get_temperature()
            self.temperature_changed.emit(self.temperature)
        except Exception as e:
            logger.warning(f"获取电调焦温度失败: {str(e)}")
        
        # 获取移动状态，但如果有监控线程在运行，则不更新
        if not self.is_move_monitored:
            try:
                self.is_moving = self.focuser_driver.is_moving()
                self.moving_changed.emit(self.is_moving)
            except TypeError:
                # 如果这是一个布尔值而不是方法
                logger.warning("is_moving可能是属性而非方法")
                try:
                    self.is_moving = getattr(self.focuser_driver, "is_moving", False)
                    self.moving_changed.emit(self.is_moving)
                except:
                    self.is_moving = False
                    self.moving_changed.emit(False)
            except Exception as e:
                logger.warning(f"获取移动状态失败: {str(e)}")
                self.is_moving = False
                self.moving_changed.emit(False)
        
        # 获取绝对定位能力
        try:
            self.absolute = self.focuser_driver.get_absolute()
            self.absolute_changed.emit(self.absolute)
            logger.info(f"电调焦绝对定位能力: {self.absolute}")
        except TypeError:
            # 如果这是一个布尔值而不是方法
            logger.warning("get_absolute可能是属性而非方法")
            try:
                self.absolute = getattr(self.focuser_driver, "absolute", False)
                self.absolute_changed.emit(self.absolute)
            except:
                self.absolute = False
                self.absolute_changed.emit(False)
        except Exception as e:
            logger.warning(f"获取电调焦绝对定位能力失败: {str(e)}")
            self.absolute = False
            self.absolute_changed.emit(False)
    
    def update_position(self):
        """
        更新位置信息
        """
        if not self.connected or not self.focuser_driver:
            return
        
        # 获取位置
        try:
            position = self.focuser_driver.get_position()
            
            # 如果位置发生变化，发送信号
            if position != self.position:
                self.position = position
                self.position_changed.emit(self.position)
        except Exception as e:
            logger.warning(f"更新电调焦位置失败: {str(e)}")
        
        # 获取移动状态，但如果有监控线程在运行，则不要覆盖移动状态
        if not self.is_move_monitored:
            try:
                is_moving = self.focuser_driver.is_moving()
                
                # 如果移动状态发生变化，发送信号
                if is_moving != self.is_moving:
                    self.is_moving = is_moving
                    self.moving_changed.emit(self.is_moving)
            except TypeError:
                # 如果这是一个布尔值而不是方法
                logger.debug("is_moving可能是属性而非方法")
                try:
                    is_moving = getattr(self.focuser_driver, "is_moving", self.is_moving)
                    if is_moving != self.is_moving:
                        self.is_moving = is_moving
                        self.moving_changed.emit(self.is_moving)
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"更新电调焦移动状态失败: {str(e)}")
    
    def update_temperature(self):
        """
        更新温度信息
        """
        if not self.connected or not self.focuser_driver:
            return
        
        try:
            # 获取当前温度
            temperature = self.focuser_driver.get_temperature()
            
            # 如果温度发生变化，发送信号
            if temperature != self.temperature:
                self.temperature = temperature
                self.temperature_changed.emit(self.temperature)
        except Exception as e:
            logger.warning(f"更新电调焦温度信息失败: {str(e)}")
    
    def move_to_position(self, position: int) -> bool:
        """
        移动电调焦到指定位置
        
        参数:
            position: 目标位置（步数）
        """
        if not self.connected or not self.focuser_driver:
            self.error_occurred.emit("电调焦未连接")
            return False
        
        try:
            # 确保位置在允许范围内
            if position < self.min_step:
                position = self.min_step
                logger.warning(f"位置已调整为最小值: {self.min_step}")
            elif position > self.max_step:
                position = self.max_step
                logger.warning(f"位置已调整为最大值: {self.max_step}")
                
            # 移动到指定位置
            result = self.focuser_driver.move_to(position)
            
            if result:
                # 更新移动状态
                self.is_moving = True
                self.moving_changed.emit(True)
                return True
            else:
                self.error_occurred.emit("移动电调焦失败")
                return False
                
        except Exception as e:
            logger.error(f"移动电调焦时发生错误: {str(e)}")
            self.error_occurred.emit(f"移动电调焦时发生错误: {str(e)}")
            return False
    
    def halt(self) -> bool:
        """
        停止电调焦移动
        """
        if not self.connected or not self.focuser_driver:
            return False
        
        try:
            # 停止移动
            result = self.focuser_driver.halt()
            
            if result:
                # 更新移动状态
                self.is_moving = False
                self.moving_changed.emit(False)
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"停止电调焦移动时发生错误: {str(e)}")
            return False
    
    def set_temperature_compensation(self, enabled: bool) -> bool:
        """
        设置温度补偿状态
        
        参数:
            enabled: 是否启用温度补偿
        """
        if not self.connected or not self.focuser_driver:
            return False
        
        if not self.temp_comp_available:
            self.error_occurred.emit("此电调焦设备不支持温度补偿")
            return False
        
        try:
            # 设置温度补偿状态
            result = self.focuser_driver.set_temperature_compensation(enabled)
            
            if result:
                # 更新温度补偿状态
                self.temp_comp = enabled
                self.temp_comp_changed.emit(enabled)
                return True
            else:
                return False
        except TypeError:
            # 如果这是一个属性而不是方法
            logger.warning("set_temperature_compensation可能是属性而非方法")
            try:
                # 尝试直接设置属性
                self.focuser_driver.temperature_compensation = enabled
                self.temp_comp = enabled
                self.temp_comp_changed.emit(enabled)
                return True
            except Exception as attr_err:
                logger.error(f"设置温度补偿属性失败: {str(attr_err)}")
                return False
        except Exception as e:
            logger.error(f"设置温度补偿状态时发生错误: {str(e)}")
            return False
    
    def is_absolute(self) -> bool:
        """
        返回电调焦是否支持绝对定位
        
        返回:
            bool: 是否支持绝对定位
        """
        return self.absolute 

    def set_move_monitored(self, monitored):
        """
        设置是否有移动监控线程正在运行
        
        参数:
            monitored: 布尔值，是否有监控线程在运行
        """
        self.is_move_monitored = monitored 