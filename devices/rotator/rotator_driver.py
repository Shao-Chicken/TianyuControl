#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
旋转器驱动模块
实现ASCOM Alpaca标准API旋转器控制接口
"""

import logging
import time
from typing import Dict, Any, Optional, Union, List, Tuple

# 导入基类
from common.alpaca_device import AlpacaDevice

# 设置日志
logger = logging.getLogger(__name__)

class RotatorDriver(AlpacaDevice):
    """
    旋转器驱动类
    继承自AlpacaDevice基类，添加旋转器特有功能
    """
    
    def __init__(self, host: str = "localhost", port: int = 11111, device_number: int = 0, client_id: int = 1, api_version: int = 1):
        """
        初始化旋转器驱动
        
        参数:
            host: Alpaca服务器主机名或IP
            port: Alpaca服务器端口
            device_number: 设备编号
            client_id: 客户端ID，用于跟踪请求
            api_version: API版本号
        """
        # 调用父类初始化方法，指定设备类型为rotator
        super().__init__(device_type="rotator", host=host, port=port, 
                        device_number=device_number, client_id=client_id, 
                        api_version=api_version)
        
        # 旋转器特有属性
        self.position = 0.0  # 当前位置（角度）
        self.is_moving = False  # 是否正在移动
        self._can_reverse = False  # 是否可以反转，使用下划线避免与方法名冲突
        self.is_reversed = False  # 是否反转
        self.step_size = 0.0  # 步长（角度）
        self.target_position = 0.0  # 目标位置
        self.mechanical_position = 0.0  # 机械位置
        self.sync_offset = 0.0  # 同步偏移
        
        # 连接重试参数
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 1  # 重试间隔（秒）
        
    # ---------------- 基本信息方法 ----------------
    
    def get_position(self) -> float:
        """
        获取旋转器当前位置
        
        返回:
            当前位置值（角度）
        """
        try:
            result = self._get_request("position")
            position = result.get("Value", 0.0)
            self.position = position
            
            return position
        except Exception as e:
            logger.error(f"获取旋转器位置失败: {str(e)}")
            return 0.0
            
    def get_mechanical_position(self) -> float:
        """
        获取旋转器机械位置（未应用同步偏移）
        
        返回:
            机械位置（角度）
        """
        try:
            result = self._get_request("mechanicalposition")
            position = result.get("Value", 0.0)
            self.mechanical_position = position
            
            return position
        except Exception as e:
            logger.error(f"获取旋转器机械位置失败: {str(e)}")
            return 0.0
            
    def get_step_size(self) -> float:
        """
        获取旋转器步长
        
        返回:
            步长（角度）
        """
        try:
            result = self._get_request("stepsize")
            self.step_size = result.get("Value", 0.0)
            
            return self.step_size
        except Exception as e:
            logger.error(f"获取旋转器步长失败: {str(e)}")
            return 0.0
            
    def get_target_position(self) -> float:
        """
        获取旋转器目标位置
        
        返回:
            目标位置（角度）
        """
        try:
            result = self._get_request("targetposition")
            self.target_position = result.get("Value", 0.0)
            
            return self.target_position
        except Exception as e:
            logger.error(f"获取旋转器目标位置失败: {str(e)}")
            return 0.0
            
    def is_moving(self) -> bool:
        """
        检查旋转器是否正在移动
        
        返回:
            是否正在移动
        """
        try:
            result = self._get_request("ismoving")
            moving_state = result.get("Value", False)
            self.is_moving = moving_state
            
            return moving_state
        except Exception as e:
            logger.error(f"检查旋转器移动状态失败: {str(e)}")
            return False
            
    def can_reverse(self) -> bool:
        """
        检查旋转器是否支持反转
        
        返回:
            是否支持反转
        """
        try:
            result = self._get_request("canreverse")
            can_reverse_value = result.get("Value", False)
            self._can_reverse = can_reverse_value
            
            return can_reverse_value
        except Exception as e:
            logger.error(f"检查旋转器反转能力失败: {str(e)}")
            return False
            
    def is_reversed(self) -> bool:
        """
        检查旋转器是否处于反转状态
        
        返回:
            是否反转
        """
        try:
            result = self._get_request("reverse")
            reversed_state = result.get("Value", False)
            self.is_reversed = reversed_state
            
            return reversed_state
        except Exception as e:
            logger.error(f"检查旋转器反转状态失败: {str(e)}")
            return False
            
    def set_reverse(self, reverse: bool) -> bool:
        """
        设置旋转器反转状态
        
        参数:
            reverse: 是否反转
            
        返回:
            操作是否成功
        """
        try:
            if not self._can_reverse:
                logger.warning("该旋转器不支持反转功能")
                return False
                
            # 使用布尔值的正确格式，确保与API要求匹配
            # Alpaca API规范：PUT /rotator/{device_number}/reverse
            # 参数应为Reverse=true或Reverse=false (注意大小写)
            self._put_request("reverse", data={"Reverse": str(reverse).lower()})
            self.is_reversed = reverse
            
            return True
        except Exception as e:
            logger.error(f"设置旋转器反转状态失败: {str(e)}")
            return False
            
    # ---------------- 移动控制方法 ----------------
    
    def move_to(self, position: float) -> bool:
        """
        移动旋转器到指定位置
        
        参数:
            position: 目标位置（角度）
            
        返回:
            操作是否成功
        """
        try:
            logger.info(f"移动旋转器到位置: {position}度")
            self._put_request("moveabsolute", data={"Position": str(position)})
            self.target_position = position
            
            return True
        except Exception as e:
            logger.error(f"移动旋转器失败: {str(e)}")
            return False
            
    def move_by(self, relative_position: float) -> bool:
        """
        移动旋转器相对位置
        
        参数:
            relative_position: 相对移动量（角度）
            
        返回:
            操作是否成功
        """
        try:
            logger.info(f"移动旋转器相对位置: {relative_position}度")
            self._put_request("move", data={"Position": str(relative_position)})
            
            return True
        except Exception as e:
            logger.error(f"移动旋转器相对位置失败: {str(e)}")
            return False
            
    def move_mechanical(self, position: float) -> bool:
        """
        移动旋转器到指定机械位置
        
        参数:
            position: 机械位置（角度）
            
        返回:
            操作是否成功
        """
        try:
            logger.info(f"移动旋转器到机械位置: {position}度")
            self._put_request("movemechanical", data={"Position": str(position)})
            
            return True
        except Exception as e:
            logger.error(f"移动旋转器到机械位置失败: {str(e)}")
            return False
            
    def halt(self) -> bool:
        """
        停止旋转器移动
        
        返回:
            操作是否成功
        """
        try:
            logger.info("停止旋转器移动")
            self._put_request("halt")
            
            return True
        except Exception as e:
            logger.error(f"停止旋转器移动失败: {str(e)}")
            return False
            
    def sync(self, position: float) -> bool:
        """
        同步旋转器到指定位置
        
        参数:
            position: 同步位置（角度）
            
        返回:
            操作是否成功
        """
        try:
            logger.info(f"同步旋转器到位置: {position}度")
            self._put_request("sync", data={"Position": str(position)})
            
            # 计算同步偏移
            mechanical_position = self.get_mechanical_position()
            self.sync_offset = position - mechanical_position
            
            return True
        except Exception as e:
            logger.error(f"同步旋转器位置失败: {str(e)}")
            return False
            
    def wait_for_movement_completion(self, timeout: int = 30) -> bool:
        """
        等待旋转器完成移动
        
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
                    logger.info("旋转器移动完成")
                    return True
                time.sleep(0.5)
                
            logger.warning("等待旋转器移动完成超时")
            return False
        except Exception as e:
            logger.error(f"等待旋转器移动完成失败: {str(e)}")
            return False 