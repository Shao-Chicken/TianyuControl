#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Alpaca客户端扩展
扩展原有AlpacaClient类的功能，提供更稳定的API访问方法
"""

import logging
from typing import Union, Optional
from telescope_ui.models.alpaca_client import AlpacaClient

# 设置日志
logger = logging.getLogger(__name__)

class AlpacaClientExtension:
    """
    扩展Alpaca客户端功能的工具类
    不继承AlpacaClient，而是使用组合方式扩展功能
    """
    
    def __init__(self, client: AlpacaClient):
        """
        初始化扩展类
        
        参数:
            client: 原始AlpacaClient实例
        """
        self.client = client
    
    def get_tracking_rate_safe(self, device_number: Optional[int] = None) -> Union[str, int]:
        """
        安全地获取当前跟踪速率，如果直接API失败，尝试使用命令方式获取
        
        参数:
            device_number: 设备编号
        返回:
            跟踪速率描述或值
        """
        try:
            # 首先尝试直接使用trackingrate端点
            #logger.info("尝试使用直接API获取跟踪速率")
            tracking_rate = self.client.get_tracking_rate(device_number)
            return self._get_tracking_rate_text(tracking_rate)
        except Exception as e:
            #logger.warning(f"使用直接API获取跟踪速率失败: {str(e)}")
            
            try:
                # 尝试使用命令字符串方法
                #logger.info("尝试使用命令获取跟踪速率")
                rate_str = self.client.command_string("GetTrackingRate", "", device_number)
                
                # 尝试将返回的字符串转换为数字
                try:
                    rate_value = int(rate_str.strip())
                    return self._get_tracking_rate_text(rate_value)
                except ValueError:
                    # 如果无法转换为整数，则直接返回字符串
                    return rate_str
            except Exception as e2:
                #logger.warning(f"使用命令获取跟踪速率失败: {str(e2)}")
                
                # 如果所有方法都失败，返回未知
                return "Unknown"
    
    def _get_tracking_rate_text(self, rate_value) -> str:
        """
        根据跟踪速率值获取描述文本
        
        参数:
            rate_value: 速率值
        返回:
            描述文本
        """
        tracking_rates = {
            0: "Sidereal Rate",
            1: "Lunar Rate",
            2: "Solar Rate", 
            3: "King Rate"
        }
        
        # 处理可能的字符串格式
        if isinstance(rate_value, str):
            try:
                rate_value = int(rate_value.strip())
            except ValueError:
                return rate_value
                
        return tracking_rates.get(rate_value, f"King Rate ({rate_value})")

    def get_parked_safe(self, device_number: Optional[int] = None) -> bool:
        """
        安全地获取当前停靠状态，如果直接API失败，尝试使用命令方式获取
        
        参数:
            device_number: 设备编号
        返回:
            是否处于停靠状态
        """
        try:
            # 首先尝试直接使用atpark端点
            parked = self.client.get_parked(device_number)
            return parked
        except Exception as e:
            logger.warning(f"使用直接API获取停靠状态失败: {str(e)}")
            
            try:
                # 尝试使用命令字符串方法
                logger.info("尝试使用命令获取停靠状态")
                parked_str = self.client.command_string("AtPark", "", device_number)
                
                # 尝试将返回的字符串转换为布尔值
                if parked_str.lower() in ["true", "1", "yes"]:
                    return True
                elif parked_str.lower() in ["false", "0", "no"]:
                    return False
                else:
                    logger.warning(f"无法解析停靠状态: {parked_str}")
                    return False
            except Exception as e2:
                logger.warning(f"使用命令获取停靠状态失败: {str(e2)}")
                
                # 如果所有方法都失败，默认返回False
                return False 

    def get_at_home_safe(self, device_number: Optional[int] = None) -> bool:
        """
        安全地获取望远镜是否在home位置，如果直接API失败，尝试使用命令方式获取
        
        参数:
            device_number: 设备编号
        返回:
            是否在home位置
        """
        try:
            # 首先尝试直接使用athome端点
            at_home = self.client.get_at_home(device_number)
            return at_home
        except Exception as e:
            logger.warning(f"使用直接API获取home状态失败: {str(e)}")
            
            try:
                # 尝试使用命令字符串方法
                logger.info("尝试使用命令获取home状态")
                at_home_str = self.client.command_string("AtHome", "", device_number)
                
                # 尝试将返回的字符串转换为布尔值
                if at_home_str.lower() in ["true", "1", "yes"]:
                    return True
                elif at_home_str.lower() in ["false", "0", "no"]:
                    return False
                else:
                    logger.warning(f"无法解析home状态: {at_home_str}")
                    return False
            except Exception as e2:
                logger.warning(f"使用命令获取home状态失败: {str(e2)}")
                
                # 如果所有方法都失败，默认返回False
                return False 