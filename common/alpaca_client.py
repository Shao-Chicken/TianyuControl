#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Alpaca API客户端模块
实现ASCOM Alpaca Remote API协议的客户端
支持ASCOM标准设备通用方法和Alpaca管理接口
"""

import logging
import requests
from typing import List, Dict, Any, Optional, Tuple, Union
import json
import time

# 设置日志
logger = logging.getLogger(__name__)

class AlpacaClient:
    """
    ASCOM Alpaca API客户端类
    实现所有设备通用的ASCOM方法和Alpaca特定的管理接口
    """
    
    def __init__(self, host: str = "localhost", port: int = 11111, client_id: int = 1, device_type: str = "telescope"):
        """
        初始化Alpaca客户端
        
        参数:
            host: Alpaca服务器主机名或IP
            port: Alpaca服务器端口
            client_id: 客户端ID，用于跟踪请求
            device_type: 设备类型，如"telescope"、"camera"等
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.device_type = device_type.lower()
        self.base_url = f"http://{host}:{port}"
        self.transaction_id = 0
        self.connected = False
        self.selected_device_number = 0
        
    def _get_next_transaction_id(self) -> int:
        """获取下一个事务ID"""
        self.transaction_id += 1
        return self.transaction_id
        
    def _build_url(self, endpoint: str, device_number: Optional[int] = None) -> str:
        """构建API URL"""
        if device_number is None:
            device_number = self.selected_device_number
            
        if endpoint.startswith("/"):
            return f"{self.base_url}{endpoint}"
        else:
            # 为设备API添加标准前缀/api/v1/
            return f"{self.base_url}/api/v1/{self.device_type}/{device_number}/{endpoint}"
            
    def _build_params(self, extra_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """构建请求参数"""
        params = {
            "ClientID": self.client_id,
            "ClientTransactionID": self._get_next_transaction_id()
        }
        
        if extra_params:
            params.update(extra_params)
            
        return params
        
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """处理API响应"""
        if response.status_code != 200:
            error_message = f"HTTP错误: {response.status_code}"
            try:
                # 尝试获取响应内容
                response_text = response.text
                logger.error(f"响应内容: {response_text[:500]}")  # 只打印前500个字符
                
                try:
                    error_data = response.json()
                    error_message = f"{error_message} - {error_data.get('ErrorMessage', '')}"
                except:
                    error_message = f"{error_message} - 无法解析JSON响应"
            except:
                error_message = f"{error_message} - 无法获取响应内容"
                
            logger.error(error_message)
            logger.error(f"请求URL: {response.url}")
            logger.error(f"请求方法: {response.request.method}")
            logger.error(f"请求头: {response.request.headers}")
            
            raise Exception(error_message)
            
        try:
            data = response.json()
            
            # 检查Alpaca错误码
            if data.get("ErrorNumber", 0) != 0:
                error_message = f"Alpaca错误: {data.get('ErrorNumber')} - {data.get('ErrorMessage', '')}"
                logger.error(error_message)
                raise Exception(error_message)
                
            return data
        except json.JSONDecodeError:
            logger.error("无法解析响应JSON数据")
            logger.error(f"响应内容: {response.text[:500]}")  # 只打印前500个字符
            raise Exception("无法解析响应JSON数据")
    
    # ==================== 设备通用方法 ====================
    
    def action(self, action_name: str, parameters: str, device_number: Optional[int] = None) -> None:
        """
        调用设备特定的动作
        
        参数:
            action_name: 动作名称
            parameters: 动作参数
            device_number: 设备编号
        """
        url = self._build_url("action", device_number)
        params = self._build_params()
        data = {
            "Action": action_name,
            "Parameters": parameters
        }
        
        response = requests.put(url, params=params, json=data)
        return self._handle_response(response)
    
    def command_blind(self, command: str, raw_params: str, device_number: Optional[int] = None) -> None:
        """
        发送命令到设备，不返回任何值
        
        参数:
            command: 命令字符串
            raw_params: 原始参数
            device_number: 设备编号
        """
        url = self._build_url("commandblind", device_number)
        params = self._build_params()
        data = {
            "Command": command,
            "Raw": raw_params
        }
        
        response = requests.put(url, params=params, json=data)
        return self._handle_response(response)
    
    def command_bool(self, command: str, raw_params: str, device_number: Optional[int] = None) -> bool:
        """
        发送命令到设备，返回布尔值
        
        参数:
            command: 命令字符串
            raw_params: 原始参数
            device_number: 设备编号
        返回:
            布尔结果
        """
        url = self._build_url("commandbool", device_number)
        params = self._build_params()
        data = {
            "Command": command,
            "Raw": raw_params
        }
        
        response = requests.put(url, params=params, json=data)
        result = self._handle_response(response)
        return result.get("Value", False)
    
    def command_string(self, command: str, raw_params: str, device_number: Optional[int] = None) -> str:
        """
        发送命令到设备，返回字符串
        
        参数:
            command: 命令字符串
            raw_params: 原始参数
            device_number: 设备编号
        返回:
            字符串结果
        """
        url = self._build_url("commandstring", device_number)
        params = self._build_params()
        data = {
            "Command": command,
            "Raw": raw_params
        }
        
        response = requests.put(url, params=params, json=data)
        result = self._handle_response(response)
        return result.get("Value", "")
    
    def connect(self, device_number: Optional[int] = None) -> None:
        """
        连接到设备
        
        参数:
            device_number: 设备编号
        """
        url = self._build_url("connect", device_number)
        params = self._build_params()
        data = {
            "Connected": True
        }
        
        response = requests.put(url, params=params, json=data)
        self._handle_response(response)
        self.connected = True
        self.selected_device_number = device_number if device_number is not None else self.selected_device_number
    
    def disconnect(self, device_number: Optional[int] = None) -> None:
        """
        断开设备连接
        
        参数:
            device_number: 设备编号
        """
        url = self._build_url("disconnect", device_number)
        params = self._build_params()
        
        response = requests.put(url, params=params)
        self._handle_response(response)
        self.connected = False
    
    def get_connected(self, device_number: Optional[int] = None) -> bool:
        """
        获取设备连接状态
        
        参数:
            device_number: 设备编号
        返回:
            是否已连接
        """
        url = self._build_url("connected", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        self.connected = result.get("Value", False)
        return self.connected
    
    def set_connected(self, connected: bool, device_number: Optional[int] = None) -> None:
        """
        设置设备连接状态
        
        参数:
            connected: 是否连接
            device_number: 设备编号
        """
        url = self._build_url("connected", device_number)
        params = self._build_params()
        data = {
            "Connected": connected
        }
        
        response = requests.put(url, params=params, json=data)
        self._handle_response(response)
        self.connected = connected
    
    def get_connecting(self, device_number: Optional[int] = None) -> bool:
        """
        获取设备是否正在连接中
        
        参数:
            device_number: 设备编号
        返回:
            是否正在连接中
        """
        url = self._build_url("connecting", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", False)
    
    def get_description(self, device_number: Optional[int] = None) -> str:
        """
        获取设备描述
        
        参数:
            device_number: 设备编号
        返回:
            设备描述
        """
        url = self._build_url("description", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", "")
    
    def get_device_state(self, device_number: Optional[int] = None) -> Dict[str, Any]:
        """
        获取设备状态
        
        参数:
            device_number: 设备编号
        返回:
            设备状态字典
        """
        url = self._build_url("devicestate", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", {})
    
    def get_driver_info(self, device_number: Optional[int] = None) -> str:
        """
        获取驱动信息
        
        参数:
            device_number: 设备编号
        返回:
            驱动信息
        """
        url = self._build_url("driverinfo", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", "")
    
    def get_driver_version(self, device_number: Optional[int] = None) -> str:
        """
        获取驱动版本
        
        参数:
            device_number: 设备编号
        返回:
            驱动版本
        """
        url = self._build_url("driverversion", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", "")
    
    def get_interface_version(self, device_number: Optional[int] = None) -> int:
        """
        获取接口版本
        
        参数:
            device_number: 设备编号
        返回:
            接口版本号
        """
        url = self._build_url("interfaceversion", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", 0)
    
    def get_name(self, device_number: Optional[int] = None) -> str:
        """
        获取设备名称
        
        参数:
            device_number: 设备编号
        返回:
            设备名称
        """
        url = self._build_url("name", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", "")
    
    def get_supported_actions(self, device_number: Optional[int] = None) -> List[str]:
        """
        获取设备支持的动作列表
        
        参数:
            device_number: 设备编号
        返回:
            支持的动作名称列表
        """
        url = self._build_url("supportedactions", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", [])
    
    # ==================== 管理接口 ====================
    
    def get_api_versions(self) -> List[int]:
        """
        获取支持的Alpaca API版本
        
        返回:
            API版本号列表
        """
        try:
            # 管理API无需设备类型和编号
            url = f"{self.base_url}/management/apiversions"
            logger.info(f"正在请求API版本，URL: {url}")
            
            # 增加超时时间到5秒
            response = requests.get(url, timeout=5)
            result = self._handle_response(response)
            return result.get("Value", [])
        except Exception as e:
            logger.error(f"获取API版本失败: {str(e)}")
            # 返回一个假定的版本号列表，让程序能继续运行
            return [1]
    
    def get_server_description(self) -> Dict[str, Any]:
        """
        获取服务器描述信息
        
        返回:
            服务器描述信息字典
        """
        url = self._build_url("/management/v1/description")
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", {})
    
    def get_configured_devices(self) -> List[Dict[str, Any]]:
        """
        获取所有配置的设备列表
        
        返回:
            设备信息字典列表
        """
        url = self._build_url("/management/v1/configureddevices")
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", [])
    
    def get_device(self, device_type, device_number=0):
        """
        获取指定类型和编号的设备接口实例
        
        参数:
            device_type: 设备类型，如telescope、camera、dome、focuser等
            device_number: 设备编号
        
        返回:
            设备接口实例
        """
        # 导入设备驱动器类型映射（延迟导入，避免循环引用）
        from .device_factory import get_device_driver
        
        # 创建并返回对应的设备驱动实例
        return get_device_driver(device_type, self.host, self.port, device_number, self.client_id)
    
    # ==================== 浏览器UI接口 ====================
    
    def get_setup_url(self, device_number: Optional[int] = None) -> str:
        """
        获取设备设置页面URL
        
        参数:
            device_number: 设备编号
        返回:
            设置页面URL
        """
        if device_number is None:
            device_number = self.selected_device_number
            
        return f"{self.base_url}/setup/v1/{self.device_type}/{device_number}/setup"
    
    def get_server_setup_url(self) -> str:
        """
        获取服务器设置页面URL
        
        返回:
            服务器设置页面URL
        """
        return f"{self.base_url}/setup"
        
    # ==================== 标准设备信息接口 ====================
    
    def get_device_description(self, device_number: Optional[int] = None) -> str:
        """
        获取设备描述信息 - 直接使用标准Alpaca API路径
        
        参数:
            device_number: 设备编号
        返回:
            设备描述信息
        """
        if device_number is None:
            device_number = self.selected_device_number
            
        try:
            url = f"{self.base_url}/api/v1/{self.device_type}/{device_number}/description"
            params = self._build_params()
            
            logger.debug(f"获取设备描述，URL: {url}")
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    return result.get("Value", "")
                except Exception as e:
                    logger.error(f"解析设备描述响应失败: {str(e)}")
                    return "获取设备描述失败: 响应格式错误"
            else:
                logger.error(f"获取设备描述请求失败，状态码: {response.status_code}")
                return f"获取设备描述失败: HTTP {response.status_code}"
                
        except Exception as e:
            logger.error(f"获取设备描述失败: {str(e)}")
            return f"获取设备描述失败: {str(e)}"
    
    def get_alpaca_api_versions(self) -> List[int]:
        """
        获取支持的Alpaca API版本 - 直接使用标准管理API路径
        
        返回:
            API版本号列表
        """
        try:
            # 管理API无需设备类型和编号
            url = f"{self.base_url}/management/apiversions"
            
            logger.debug(f"获取API版本，URL: {url}")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    versions = result.get("Value", [])
                    if isinstance(versions, list):
                        return versions
                    else:
                        logger.error(f"API版本格式错误: {versions}")
                        return [1]  # 默认返回版本1
                except Exception as e:
                    logger.error(f"解析API版本响应失败: {str(e)}")
                    return [1]
            else:
                logger.error(f"获取API版本请求失败，状态码: {response.status_code}")
                return [1]
                
        except Exception as e:
            logger.error(f"获取API版本失败: {str(e)}")
            return [1]
    
    # ==================== 望远镜特定方法 ====================
    
    def get_altitude(self, device_number: Optional[int] = None) -> float:
        """
        获取望远镜当前高度（海拔角）
        
        参数:
            device_number: 设备编号
        返回:
            高度角，单位为度
        """
        url = self._build_url("altitude", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", 0.0)
    
    def get_sidereal_time(self, device_number: Optional[int] = None) -> float:
        """
        获取当地恒星时
        
        参数:
            device_number: 设备编号
        返回:
            恒星时，单位为小时
        """
        url = self._build_url("siderealtime", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", 0.0)
    
    def get_right_ascension(self, device_number: Optional[int] = None) -> float:
        """
        获取赤经坐标
        
        参数:
            device_number: 设备编号
        返回:
            赤经，单位为小时
        """
        url = self._build_url("rightascension", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", 0.0)
    
    def get_declination(self, device_number: Optional[int] = None) -> float:
        """
        获取赤纬坐标
        
        参数:
            device_number: 设备编号
        返回:
            赤纬，单位为度
        """
        url = self._build_url("declination", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", 00.0)
    
    def get_site_latitude(self, device_number: Optional[int] = None) -> float:
        """
        获取观测站点纬度
        
        参数:
            device_number: 设备编号
        返回:
            纬度，单位为度
        """
        url = self._build_url("sitelatitude", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", 0.0)
    
    def get_site_longitude(self, device_number: Optional[int] = None) -> float:
        """
        获取观测站点经度（WGS84，东经为正）
        
        参数:
            device_number: 设备编号
        返回:
            经度，单位为度
        """
        url = self._build_url("sitelongitude", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", 0.0)
    
    def get_site_elevation(self, device_number: Optional[int] = None) -> float:
        """
        获取观测站点海拔高度
        
        参数:
            device_number: 设备编号
        返回:
            海拔高度，单位为米
        """
        url = self._build_url("siteelevation", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", 0.0)
    
    def get_azimuth(self, device_number: Optional[int] = None) -> float:
        """
        获取望远镜当前方位角
        
        参数:
            device_number: 设备编号
        返回:
            方位角，单位为度（0-360度）
        """
        url = self._build_url("azimuth", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", 0.0)
    
    def get_tracking(self, device_number: Optional[int] = None) -> bool:
        """
        获取望远镜跟踪状态
        
        参数:
            device_number: 设备编号
        返回:
            是否在跟踪
        """
        url = self._build_url("tracking", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", False)
    
    def set_tracking(self, tracking: bool, device_number: Optional[int] = None) -> None:
        """
        设置望远镜跟踪状态
        
        参数:
            tracking: 是否启用跟踪
            device_number: 设备编号
        """
        url = self._build_url("tracking", device_number)
        params = self._build_params()
        data = {
            "Tracking": tracking
        }
        
        response = requests.put(url, params=params, json=data)
        self._handle_response(response)
    
    def get_slewing(self, device_number: Optional[int] = None) -> bool:
        """
        获取望远镜转向状态
        
        参数:
            device_number: 设备编号
        返回:
            是否正在转向
        """
        url = self._build_url("slewing", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", False)
    
    def get_parked(self, device_number: Optional[int] = None) -> bool:
        """
        获取望远镜停靠状态
        
        参数:
            device_number: 设备编号
        返回:
            是否已停靠
        """
        url = self._build_url("atpark", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", False)
        
    def park(self, device_number: Optional[int] = None) -> Dict[str, Any]:
        """
        停靠望远镜
        
        参数:
            device_number: 设备编号
            
        返回:
            服务器响应字典，包含ErrorNumber和ErrorMessage等信息
        """
        url = self._build_url("park", device_number)
        params = self._build_params()
        
        response = requests.put(url, params=params)
        result = self._handle_response(response)
        return result
    
    def unpark(self, device_number: Optional[int] = None) -> Dict[str, Any]:
        """
        解除望远镜停靠
        
        参数:
            device_number: 设备编号
            
        返回:
            服务器响应字典，包含ErrorNumber和ErrorMessage等信息
        """
        url = self._build_url("unpark", device_number)
        params = self._build_params()
        
        response = requests.put(url, params=params)
        result = self._handle_response(response)
        return result
    
    def get_equatorial_system(self, device_number: Optional[int] = None) -> str:
        """
        获取望远镜当前使用的赤道坐标系统
        
        参数:
            device_number: 设备编号
        返回:
            坐标系统（例如"J2000"、"JNOW"等）
        """
        url = self._build_url("equatorialsystem", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", "Unknown")

    def get_supported_tracking_rates(self, device_number: Optional[int] = None) -> List[float]:
        """
        获取望远镜支持的跟踪速率
        
        参数:
            device_number: 设备编号
        返回：
            支持的跟踪速率列表
        """
        url = self._build_url("trackingrates", device_number)
        params = self._build_params()

        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", [])

    def get_tracking_rate(self, device_number: Optional[int] = None, as_text: bool = False) -> Union[float, str]:
        """
        获取望远镜当前跟踪速率
        
        参数:
            device_number: 设备编号
            as_text: 是否返回描述性文本而非数值
        返回:
            当前跟踪速率值或描述性文本
        """
        url = self._build_url("trackingrate", device_number)
        params = self._build_params()

        response = requests.get(url, params=params)
        result = self._handle_response(response)
        rate_value = result.get("Value", 0)
        
        if as_text:
            return self.get_tracking_rate_description(rate_value)
        return rate_value
    
    def get_tracking_rate_description(self, rate_value: int) -> str:
        """
        获取跟踪速率的描述性文本
        
        参数:
            rate_value: 跟踪速率值
        返回:
            描述性文本
        """
        tracking_rates = {
            0: "Sidereal rate",
            1: "Lunar rate",
            2: "Solar rate",
            3: "King rate"
        }
        
        return tracking_rates.get(rate_value, f"未知速率 ({rate_value})")

    def set_tracking_rate(self, rate_value, device_number=0):
        """
        设置望远镜跟踪速率
        
        参数:
            rate_value: 跟踪速率值
            device_number: 设备编号
        """
        url = self._build_url("trackingrate", device_number)
        
        # 使用表单编码格式发送请求，而不是JSON格式
        data = {
            "ClientID": self.client_id,
            "ClientTransactionID": self._get_next_transaction_id(),
            "TrackingRate": rate_value
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        logger.info(f"设置跟踪速率为: {rate_value}，使用表单编码格式")
        response = requests.put(url, data=data, headers=headers)
        self._handle_response(response)
        logger.info(f"成功设置跟踪速率为: {rate_value}")
    
    def slew_to_coordinates_async(self, right_ascension, declination, device_number=0):
        """
        异步指向给定的赤道坐标
        
        参数:
            right_ascension: 赤经（小时，0.0到23.9999999999）
            declination: 赤纬（度，-90到+90）
            device_number: 设备编号
        
        返回:
            无返回值，操作成功时不抛出异常
        
        抛出:
            ValueError: 参数值无效时
            RequestException: 请求失败时
        """
        # 验证参数
        if right_ascension < 0 or right_ascension >= 24:
            raise ValueError(f"赤经必须在0到24小时范围内，当前值: {right_ascension}")
            
        if declination < -90 or declination > 90:
            raise ValueError(f"赤纬必须在-90到+90度范围内，当前值: {declination}")
        
        # 构建URL
        url = self._build_url("slewtocoordinatesasync", device_number)
        
        # 使用表单编码格式发送请求
        data = {
            "ClientID": self.client_id,
            "ClientTransactionID": self._get_next_transaction_id(),
            "RightAscension": right_ascension,
            "Declination": declination
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        logger.info(f"异步指向坐标 - 赤经: {right_ascension}小时, 赤纬: {declination}度")
        response = requests.put(url, data=data, headers=headers)
        self._handle_response(response)
        logger.info(f"异步指向请求已成功发送")
    
    def slew_to_alt_az_async(self, altitude, azimuth, device_number=0):
        """
        异步指向给定的地平坐标
        
        参数:
            altitude: 高度角（度，-90到+90）
            azimuth: 方位角（度，0到360）
            device_number: 设备编号
        
        返回:
            无返回值，操作成功时不抛出异常
        
        抛出:
            ValueError: 参数值无效时
            RequestException: 请求失败时
        """
        # 验证参数
        if altitude < -90 or altitude > 90:
            raise ValueError(f"高度角必须在-90到+90度范围内，当前值: {altitude}")
            
        if azimuth < 0 or azimuth >= 360:
            raise ValueError(f"方位角必须在0到360度范围内，当前值: {azimuth}")
        
        # 构建URL
        url = self._build_url("slewtoaltazasync", device_number)
        
        # 使用表单编码格式发送请求
        data = {
            "ClientID": self.client_id,
            "ClientTransactionID": self._get_next_transaction_id(),
            "Altitude": altitude,
            "Azimuth": azimuth
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        logger.info(f"异步指向地平坐标 - 高度角: {altitude}度, 方位角: {azimuth}度")
        response = requests.put(url, data=data, headers=headers)
        self._handle_response(response)
        logger.info(f"异步指向地平坐标请求已成功发送")
    
    def move_axis(self, axis: int, rate: float, device_number: Optional[int] = None) -> None:
        """
        控制望远镜的机械轴以指定速率移动
        
        参数:
            axis: 轴编号，0=主轴(RA/赤经)，1=次轴(DEC/赤纬)，2=第三轴(如果有)
            rate: 移动速率(度/秒)，正值表示一个方向，负值表示相反方向，0表示停止
            device_number: 设备编号
            
        返回:
            无返回值，操作成功时不抛出异常
            
        说明:
            此方法按照ASCOM标准实现，控制望远镜机械轴的移动。
            设置速率为0将停止该轴的移动并恢复先前状态(如果跟踪开启，则恢复跟踪)。
            移动期间，只有指定轴的跟踪会暂停，其他轴不受影响。
        """
        # 验证参数
        if axis not in [0, 1, 2]:
            raise ValueError(f"轴编号必须是0(主轴)、1(次轴)或2(第三轴)，当前值: {axis}")
            
        # 构建URL
        url = self._build_url("moveaxis", device_number)
        
        # 使用表单编码格式发送请求
        data = {
            "ClientID": self.client_id,
            "ClientTransactionID": self._get_next_transaction_id(),
            "Axis": axis,
            "Rate": rate
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        logger.info(f"移动轴 - 轴: {axis}, 速率: {rate}度/秒")
        response = requests.put(url, data=data, headers=headers)
        self._handle_response(response)
        logger.info(f"移动轴请求已成功发送")

    def set_park(self, device_number: Optional[int] = None) -> Dict[str, Any]:
        """
        将当前位置设置为望远镜的停靠位置
        
        参数:
            device_number: 设备编号
            
        返回:
            服务器响应字典，包含ErrorNumber和ErrorMessage等信息
        """
        url = self._build_url("setpark", device_number)
        params = self._build_params()
        
        response = requests.put(url, params=params)
        result = self._handle_response(response)
        return result

    def get_at_home(self, device_number: Optional[int] = None) -> bool:
        """
        获取望远镜是否在home位置
        
        参数:
            device_number: 设备编号
        返回:
            是否在home位置
        """
        url = self._build_url("athome", device_number)
        params = self._build_params()
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        return result.get("Value", False)
    
    def find_home(self, device_number: Optional[int] = None) -> Dict[str, Any]:
        """
        移动望远镜到home位置
        
        参数:
            device_number: 设备编号
            
        返回:
            服务器响应字典，包含ErrorNumber和ErrorMessage等信息
        """
        url = self._build_url("findhome", device_number)
        params = self._build_params()
        
        response = requests.put(url, params=params)
        result = self._handle_response(response)
        return result

    def abort_slew(self, device_number: Optional[int] = None) -> Dict[str, Any]:
        """
        立即停止正在进行的转向操作
        
        参数:
            device_number: 设备编号
            
        返回:
            服务器响应字典，包含ErrorNumber和ErrorMessage等信息
        """
        url = self._build_url("abortslew", device_number)
        params = self._build_params()
        
        response = requests.put(url, params=params)
        result = self._handle_response(response)
        return result

 