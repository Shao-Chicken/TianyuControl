#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
电调焦驱动模块
实现ASCOM Alpaca标准API电调焦控制接口
"""

import logging
import time
from typing import Dict, Any, Optional, Union, List, Tuple

# 导入基类
from common.alpaca_device import AlpacaDevice

# 设置日志
logger = logging.getLogger(__name__)

class FocuserDriver(AlpacaDevice):
    """
    电调焦驱动类
    继承自AlpacaDevice基类，添加电调焦特有功能
    """
    
    def __init__(self, host: str = "localhost", port: int = 11111, device_number: int = 0, client_id: int = 1, api_version: int = 1):
        """
        初始化电调焦驱动
        
        参数:
            host: Alpaca服务器主机名或IP
            port: Alpaca服务器端口
            device_number: 设备编号
            client_id: 客户端ID，用于跟踪请求
            api_version: API版本号
        """
        # 调用父类初始化方法，指定设备类型为focuser
        super().__init__(device_type="focuser", host=host, port=port, 
                        device_number=device_number, client_id=client_id, 
                        api_version=api_version)
        
        # 电调焦特有属性
        self.position = 0  # 当前位置
        self.is_moving = False  # 是否正在移动
        self.max_step = 0  # 最大步数
        self.min_step = 0  # 最小步数
        self.step_size = 0  # 步长
        self.temperature_compensation = False  # 温度补偿
        self.temperature = 0.0  # 温度
        
        # 连接重试参数
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 1  # 重试间隔（秒）
        
    # ---------------- 基本信息方法 ----------------
    
    def get_position(self) -> int:
        """
        获取电调焦当前位置
        
        返回:
            当前位置值（步数）
        """
        try:
            result = self._get_request("position")
            position = result.get("Value", 0)
            self.position = position
            
            return position
        except Exception as e:
            logger.error(f"获取电调焦位置失败: {str(e)}")
            return 0
            
    def get_max_step(self) -> int:
        """
        获取电调焦最大步数
        
        返回:
            最大步数
        """
        try:
            result = self._get_request("maxstep")
            self.max_step = result.get("Value", 0)
            
            return self.max_step
        except Exception as e:
            logger.error(f"获取电调焦最大步数失败: {str(e)}")
            return 0
            
    def get_min_step(self) -> int:
        """
        获取电调焦最小步数
        
        返回:
            最小步数
        """
        return 0
            
    def get_step_size(self) -> float:
        """
        获取电调焦步长
        
        返回:
            步长（微米）
        """
        try:
            result = self._get_request("stepsize")
            self.step_size = result.get("Value", 0.00)
            
            return self.step_size
        except Exception as e:
            logger.error(f"获取电调焦步长失败: {str(e)}")
            return 0.00
            
    def get_temperature(self) -> float:
        """
        获取电调焦温度
        
        返回:
            温度（摄氏度）
        """
        try:
            result = self._get_request("temperature")
            self.temperature = result.get("Value", 0.00)
            
            return self.temperature
        except Exception as e:
            logger.error(f"获取电调焦温度失败: {str(e)}")
            return 0.00
            
    def is_temperature_compensation_available(self) -> bool:
        """
        检查电调焦是否支持温度补偿
        
        返回:
            是否支持温度补偿
        """
        try:
            logger.debug(f"正在获取温度补偿可用性，URL: {self._build_url('tempcompavailable')}")
            result = self._get_request("tempcompavailable")
            available = result.get("Value", False)
            logger.info(f"温度补偿可用性: {available}")
            
            return available
        except Exception as e:
            logger.error(f"检查温度补偿可用性失败: {str(e)}")
            return False
            
    def get_temperature_compensation(self) -> bool:
        """
        获取电调焦温度补偿状态
        
        返回:
            温度补偿是否开启
        """
        try:
            logger.debug(f"正在获取温度补偿状态，URL: {self._build_url('tempcomp')}")
            result = self._get_request("tempcomp")
            temp_comp_value = result.get("Value", False)
            # 保存为实例变量
            self.temperature_compensation = temp_comp_value
            logger.info(f"温度补偿状态: {temp_comp_value}")
            
            return temp_comp_value
        except Exception as e:
            logger.error(f"获取温度补偿状态失败: {str(e)}")
            return False
            
    def set_temperature_compensation(self, enabled: bool) -> bool:
        """
        设置电调焦温度补偿状态
        
        参数:
            enabled: 是否启用温度补偿
            
        返回:
            操作是否成功
        """
        try:
            self._put_request("tempcomp", data={"TempComp": "true" if enabled else "false"})
            self.temperature_compensation = enabled
            
            return True
        except Exception as e:
            logger.error(f"设置温度补偿状态失败: {str(e)}")
            return False
            
    # ---------------- 移动控制方法 ----------------
    
    def is_moving(self) -> bool:
        """
        检查电调焦是否正在移动
        
        返回:
            是否正在移动
        """
        try:
            result = self._get_request("ismoving")
            moving_state = result.get("Value", False)
            self.is_moving = moving_state
            
            return moving_state
        except Exception as e:
            logger.error(f"检查电调焦移动状态失败: {str(e)}")
            return False
            
    def move_to(self, position: int) -> bool:
        """
        移动电调焦到指定位置
        
        参数:
            position: 目标位置（步数）
            
        返回:
            操作是否成功
        """
        try:
            logger.info(f"移动电调焦到位置: {position}")
            self._put_request("move", data={"Position": str(position)})
            
            return True
        except Exception as e:
            logger.error(f"移动电调焦失败: {str(e)}")
            return False
            
    def halt(self) -> bool:
        """
        停止电调焦移动
        
        返回:
            操作是否成功
        """
        try:
            logger.info("停止电调焦移动")
            self._put_request("halt")
            
            return True
        except Exception as e:
            logger.error(f"停止电调焦移动失败: {str(e)}")
            return False
            
    def wait_for_movement_completion(self, timeout: int = 30) -> bool:
        """
        等待电调焦完成移动
        
        参数:
            timeout: 超时时间（秒）
            
        返回:
            是否成功完成移动
        """
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                # 获取当前移动状态
                result = self._get_request("ismoving")
                current_is_moving = result.get("Value", False)
                if not current_is_moving:
                    logger.info("电调焦移动完成")
                    return True
                time.sleep(0.5)
                
            logger.warning("等待电调焦移动完成超时")
            return False
        except Exception as e:
            logger.error(f"等待电调焦移动完成失败: {str(e)}")
            return False

    def get_absolute(self) -> bool:
        """
        获取电调焦是否支持绝对定位
        
        返回:
            bool: 是否支持绝对定位
        """
        try:
            logger.debug(f"正在获取绝对定位能力，URL: {self._build_url('absolute')}")
            result = self._get_request("absolute")
            absolute = result.get("Value", False)
            logger.info(f"绝对定位能力: {absolute}")
            
            return absolute
        except Exception as e:
            logger.error(f"获取绝对定位能力失败: {str(e)}")
            # 大多数电调焦驱动默认支持绝对定位，如果查询失败，返回True作为默认值
            return True 