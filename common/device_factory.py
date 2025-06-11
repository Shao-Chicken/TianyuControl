#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设备驱动工厂模块
负责创建不同类型的设备驱动实例
"""

import logging
from typing import Dict, Any, Optional, Union, List, Tuple

# 设置日志
logger = logging.getLogger(__name__)

def get_device_driver(device_type, host, port, device_number, client_id):
    """
    根据设备类型创建对应的设备驱动实例
    
    参数:
        device_type: 设备类型，例如telescope、dome、focuser、covercalibrator等
        host: 服务器主机名或IP
        port: 服务器端口
        device_number: 设备编号
        client_id: 客户端ID
    
    返回:
        设备驱动实例
    """
    # 将设备类型转为小写
    device_type = device_type.lower()
    
    try:
        if device_type == "telescope":
            from devices.telescope.telescope_driver import TelescopeDriver
            return TelescopeDriver(host, port, device_number, client_id)
        elif device_type == "dome":
            from devices.dome.dome_driver import DomeDriver
            return DomeDriver(host, port, device_number, client_id)
        elif device_type == "focuser":
            from devices.focuser.focuser_driver import FocuserDriver
            return FocuserDriver(host, port, device_number, client_id)
        elif device_type == "rotator":
            from devices.rotator.rotator_driver import RotatorDriver
            return RotatorDriver(host, port, device_number, client_id)
        elif device_type == "covercalibrator":
            # 导入镜头盖/校准器驱动
            from devices.covercalibrator.covercalibrator_driver import CoverCalibratorDriver
            
            # 使用专用的镜头盖/校准器驱动类
            logger.info(f"创建CoverCalibrator设备: host={host}, port={port}, device_number={device_number}")
            return CoverCalibratorDriver(host, port, device_number, client_id)
        elif device_type == "observingconditions":
            # 对于天气站设备(ObservingConditions)，使用通用设备类，因为我们尚未创建专用驱动
            from common.alpaca_device import AlpacaDevice
            logger.info(f"创建ObservingConditions设备: host={host}, port={port}, device_number={device_number}")
            return AlpacaDevice(device_type, host, port, device_number, client_id)
        else:
            # 对于未知设备类型，使用通用设备类
            from common.alpaca_device import AlpacaDevice
            logger.warning(f"未知设备类型 '{device_type}'，使用通用设备类")
            return AlpacaDevice(device_type, host, port, device_number, client_id)
    
    except Exception as e:
        logger.error(f"创建设备驱动实例失败: {str(e)}")
        # 返回通用设备类
        from common.alpaca_device import AlpacaDevice
        return AlpacaDevice(device_type, host, port, device_number, client_id) 