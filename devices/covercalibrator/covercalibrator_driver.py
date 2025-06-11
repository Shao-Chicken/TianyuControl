#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
镜头盖设备驱动模块
实现ASCOM Alpaca标准API镜头盖控制接口
"""


import logging
import time
from typing import Dict, Any, Optional, Union, List, Tuple

# 导入基类
from common.alpaca_device import AlpacaDevice

# 设置日志
logger = logging.getLogger(__name__)

class CoverCalibratorDriver(AlpacaDevice):
    """
    镜头盖/校准器驱动类
    实现ASCOM标准的镜头盖/校准器功能
    """
    
    def __init__(self, host, port, device_number=0, client_id=1):
        """
        初始化镜头盖/校准器驱动
        
        参数:
            host: Alpaca服务器主机名或IP
            port: Alpaca服务器端口
            device_number: 设备编号
            client_id: 客户端ID
        """
        super(CoverCalibratorDriver, self).__init__("covercalibrator", host, port, device_number, client_id)
        logger.info(f"初始化镜头盖/校准器驱动: host={host}, port={port}, device_number={device_number}")
        
        # 记录API支持情况
        self._supports_cover_moving_api = None  # 初始为None表示未测试
        self._supports_calibrator_changing_api = None  # 初始为None表示未测试
    
    def connect_device(self):
        """确保设备成功连接并准备好接收命令"""
        try:
            # 调用基类的connect方法
            connected = super().connect()
            if not connected:
                logger.error("基础连接方法失败，尝试直接设置Connected属性...")
                
            # 无论基类connect方法是否成功，都明确设置Connected属性
            url = self._build_url("connected")
            params = self._build_params()
            data = {"Connected": "true"}
            
            try:
                logger.info("明确发送Connected=True请求...")
                response = self._session.put(url, params=params, data=data)
                self._handle_response(response)
                logger.info("成功设置Connected=True")
                
                # 短暂延迟，让ASCOM设备有时间完成连接流程
                time.sleep(1)
                
                # 验证连接状态
                current_status = self.is_connected()
                if current_status:
                    logger.info("验证成功：设备确实已连接")
                    return True
                else:
                    logger.warning("验证失败：设备仍显示为未连接")
                    return False
                    
            except Exception as e2:
                logger.error(f"设置Connected属性失败: {str(e2)}")
                return False
                
            return connected
        except Exception as e:
            logger.error(f"连接设备失败: {str(e)}")
            return False
    
    # ======== 镜头盖特定方法 ========
    
    def get_cover_state(self) -> str:
        """
        获取镜头盖状态
        
        返回:
            镜头盖状态: NotPresent, Closed, Moving, Open, Unknown
        """
        url = self._build_url("coverstate")
        params = self._build_params()
        
        try:
            response = self._session.get(url, params=params)
            result = self._handle_response(response)
            value = result.get("Value")
            
            # 确保返回字符串类型
            if isinstance(value, int):
                # 整数状态码映射到字符串
                state_map = {
                    0: "NotPresent",
                    1: "Closed",
                    2: "Moving",
                    3: "Open",
                    -1: "Unknown"
                }
                return state_map.get(value, "Unknown")
            elif isinstance(value, str):
                return value
            else:
                return "Unknown"
        except Exception as e:
            logger.error(f"获取镜头盖状态失败: {str(e)}")
            return "Unknown"
    
    def open_cover(self) -> None:
        """打开镜头盖"""
        url = self._build_url("opencover")
        params = self._build_params()
        
        try:
            response = self._session.put(url, params=params)
            self._handle_response(response)
            logger.info("发送打开镜头盖命令")
        except Exception as e:
            logger.error(f"打开镜头盖失败: {str(e)}")
            raise
    
    def close_cover(self) -> None:
        """关闭镜头盖"""
        url = self._build_url("closecover")
        params = self._build_params()
        
        try:
            response = self._session.put(url, params=params)
            self._handle_response(response)
            logger.info("发送关闭镜头盖命令")
        except Exception as e:
            logger.error(f"关闭镜头盖失败: {str(e)}")
            raise
    
    def halt_cover(self) -> None:
        """停止镜头盖操作"""
        url = self._build_url("haltcover")
        params = self._build_params()
        
        try:
            response = self._session.put(url, params=params)
            self._handle_response(response)
            logger.info("发送停止镜头盖操作命令")
        except Exception as e:
            logger.error(f"停止镜头盖操作失败: {str(e)}")
            raise
    
    # ======== 校准器特定方法 ========
    
    def get_calibrator_state(self) -> str:
        """
        获取校准器状态
        
        返回:
            校准器状态: NotPresent, Off, Ready, CalibrationRequired, On, Unknown
        """
        url = self._build_url("calibratorstate")
        params = self._build_params()
        
        try:
            response = self._session.get(url, params=params)
            result = self._handle_response(response)
            value = result.get("Value")
            
            # 确保返回字符串类型
            if isinstance(value, int):
                # 整数状态码映射到字符串
                state_map = {
                    0: "NotPresent",
                    1: "Off",
                    2: "Ready",
                    3: "CalibrationRequired",
                    4: "On",
                    -1: "Unknown"
                }
                return state_map.get(value, "Unknown")
            elif isinstance(value, str):
                return value
            else:
                return "Unknown"
        except Exception as e:
            logger.error(f"获取校准器状态失败: {str(e)}")
            return "Unknown"
    
    def get_max_brightness(self) -> int:
        """
        获取校准器最大亮度
        
        返回:
            校准器最大亮度
        """
        url = self._build_url("maxbrightness")
        params = self._build_params()
        
        try:
            response = self._session.get(url, params=params)
            result = self._handle_response(response)
            return result.get("Value", 100)
        except Exception as e:
            logger.error(f"获取校准器最大亮度失败: {str(e)}")
            return 100
    
    def get_brightness(self) -> int:
        """
        获取当前校准器亮度
        
        返回:
            当前校准器亮度
        """
        url = self._build_url("brightness")
        params = self._build_params()
        
        try:
            response = self._session.get(url, params=params)
            result = self._handle_response(response)
            return result.get("Value", 0)
        except Exception as e:
            logger.error(f"获取校准器亮度失败: {str(e)}")
            return 0
    
    def set_brightness(self, brightness: int) -> bool:
        """
        设置校准器亮度
        
        参数:
            brightness: 亮度值
        返回:
            bool: 操作是否成功
        """
        # 记录详细日志
        logger.info(f"设置校准器亮度: {brightness}")
        
        try:
            # 校准器亮度必须使用calibratoron端点
            data = {"Brightness": str(brightness)}  # 参数必须作为字符串传递
            self._put_request("calibratoron", data=data)
            logger.info(f"成功设置校准器亮度: {brightness}")
            return True
        except Exception as e:
            logger.error(f"设置校准器亮度失败: {str(e)}")
            return False
    
    def calibrator_on(self, brightness: int) -> bool:
        """
        开启校准器
        
        参数:
            brightness: 亮度值
        返回:
            bool: 操作是否成功
        """
        # 记录详细日志
        logger.info(f"开启校准器，亮度: {brightness}")
        
        try:
            # 使用_put_request方法，让基类处理请求格式
            data = {"Brightness": str(brightness)}  # 参数必须作为字符串传递
            self._put_request("calibratoron", data=data)
            logger.info(f"成功开启校准器，亮度: {brightness}")
            return True
        except Exception as e:
            logger.error(f"开启校准器失败: {str(e)}")
            return False
    
    def calibrator_off(self) -> bool:
        """
        关闭校准器
        
        返回:
            bool: 操作是否成功
        """
        url = self._build_url("calibratoroff")
        params = self._build_params()
        
        try:
            response = self._session.put(url, params=params)
            self._handle_response(response)
            logger.info("成功关闭校准器")
            return True
        except Exception as e:
            logger.error(f"关闭校准器失败: {str(e)}")
            return False
    
    def get_calibrator_changing(self) -> bool:
        """
        获取校准器是否正在变化中（亮度变化或开关过程中）
        
        返回:
            True表示校准器正在变化，False表示校准器稳定
        """
        # 如果已确定API不支持，直接使用备选方案
        if self._supports_calibrator_changing_api is False:
            try:
                # 从calibratorstate判断状态
                state = self.get_calibrator_state()
                # 使用正确的状态值来判断是否在变化中
                return state == "CalibrationRequired"
            except Exception as e:
                logger.error(f"备选方案获取校准器变化状态失败: {str(e)}")
                return False
        
        # 首次调用或API可能支持
        if self._supports_calibrator_changing_api is None or self._supports_calibrator_changing_api is True:
            try:
                # 尝试直接获取calibratorchanging属性
                url = self._build_url("calibratorchanging")
                params = self._build_params()
                
                response = self._session.get(url, params=params)
                result = self._handle_response(response)
                
                # 标记API为支持
                self._supports_calibrator_changing_api = True
                
                return bool(result.get("Value", False))
            except Exception as e:
                # 如果API不支持，标记并使用备选方案
                self._supports_calibrator_changing_api = False
                logger.info(f"检测到calibratorchanging API不受支持，将使用备选方案: {str(e)}")
                
                try:
                    # 从calibratorstate判断状态
                    state = self.get_calibrator_state()
                    # 使用正确的状态值来判断是否在变化中
                    return state == "CalibrationRequired"
                except Exception as inner_e:
                    logger.error(f"备选方案获取校准器变化状态也失败: {str(inner_e)}")
                    return False
    
    def get_cover_moving(self) -> bool:
        """
        获取盖板是否正在移动
        
        返回:
            True表示盖板正在移动，False表示盖板静止
        """
        # 如果已确定API不支持，直接使用备选方案
        if self._supports_cover_moving_api is False:
            try:
                state = self.get_cover_state()
                return state == "Moving"
            except Exception as e:
                logger.error(f"备选方案获取盖板移动状态失败: {str(e)}")
                return False
        
        # 首次调用或API可能支持
        if self._supports_cover_moving_api is None or self._supports_cover_moving_api is True:
            try:
                # 尝试直接获取covermoving属性
                url = self._build_url("covermoving")
                params = self._build_params()
                
                response = self._session.get(url, params=params)
                result = self._handle_response(response)
                
                # 标记API为支持
                self._supports_cover_moving_api = True
                
                return bool(result.get("Value", False))
            except Exception as e:
                # 如果API不支持，标记并使用备选方案
                self._supports_cover_moving_api = False
                logger.info(f"检测到covermoving API不受支持，将使用备选方案: {str(e)}")
                
                try:
                    # 从coverstate判断，如果状态是Moving则表示在移动
                    state = self.get_cover_state()
                    return state == "Moving"
                except Exception as inner_e:
                    logger.error(f"备选方案获取盖板移动状态也失败: {str(inner_e)}")
                    return False