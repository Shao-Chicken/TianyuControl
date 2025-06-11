#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ASCOM Alpaca设备基础模块
提供所有ASCOM设备通用的API调用和连接管理功能
"""

import logging
import requests
import json
import time
from typing import Dict, Any, Optional, Union, List, Tuple

# 设置日志
logger = logging.getLogger(__name__)

class AlpacaDevice:
    """
    ASCOM Alpaca设备基类
    实现标准ASCOM Alpaca API的设备连接和基础控制功能
    """
    
    def __init__(self, 
                 device_type: str,
                 host: str = "localhost", 
                 port: int = 11111, 
                 device_number: int = 0, 
                 client_id: int = 1, 
                 api_version: int = 1):
        """
        初始化Alpaca设备
        
        参数:
            device_type: 设备类型，如"telescope"、"camera"、"focuser"等
            host: Alpaca服务器主机名或IP
            port: Alpaca服务器端口
            device_number: 设备编号
            client_id: 客户端ID，用于跟踪请求
            api_version: API版本号
        """
        self.host = host
        self.port = port
        self.device_number = device_number
        self.client_id = client_id
        self.api_version = api_version
        self.transaction_id = 0
        self.base_url = f"http://{host}:{port}"
        self.device_type = device_type.lower()  # 确保设备类型为小写
        self.connected = False
        
        # 初始化HTTP会话，用于所有API请求
        self._session = requests.Session()
        
        logger.info(f"初始化Alpaca {device_type}设备: {host}:{port}, 设备: {device_number}, API版本: v{api_version}")
    
    def _get_transaction_id(self) -> int:
        """获取下一个事务ID"""
        self.transaction_id += 1
        return self.transaction_id
    
    def _build_url(self, command: str) -> str:
        """
        构建标准Alpaca API URL
        
        参数:
            command: 设备命令
        返回:
            完整的API URL
        """
        # 标准Alpaca API格式: /api/v{api_version}/{device_type}/{device_number}/{command}
        # 确保所有URL部分都是小写，因为服务器要求URL必须是小写
        url = f"{self.base_url}/api/v{self.api_version}/{self.device_type.lower()}/{self.device_number}/{command.lower()}"
        logger.debug(f"构建URL: {url}")
        return url
    
    def _build_params(self, extra_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        构建请求参数
        
        参数:
            extra_params: 额外的请求参数
        返回:
            完整的请求参数字典
        """
        params = {
            "ClientID": self.client_id,
            "ClientTransactionID": self._get_transaction_id()
        }
        
        if extra_params:
            params.update(extra_params)
            
        return params
    
    def _handle_response(self, response: requests.Response, log_error: bool = True) -> Dict[str, Any]:
        """
        处理API响应
        
        参数:
            response: HTTP响应对象
            log_error: 是否记录错误日志
        返回:
            解析后的响应数据
        异常:
            如果请求失败，抛出异常
        """
        try:
            # 检查HTTP状态码
            if response.status_code != 200:
                error_message = f"HTTP错误: {response.status_code}"
                if log_error:
                    logger.error(error_message)
                    logger.error(f"请求URL: {response.url}")
                    logger.error(f"请求方法: {response.request.method}")
                    logger.error(f"响应内容: {response.text[:500]}")
                raise Exception(error_message)
            
            # 解析JSON响应
            data = response.json()
            
            # 检查Alpaca错误码
            if data.get("ErrorNumber", 0) != 0:
                error_message = f"Alpaca错误: {data.get('ErrorNumber')} - {data.get('ErrorMessage', '')}"
                if log_error:
                    logger.error(error_message)
                raise Exception(error_message)
                
            return data
            
        except json.JSONDecodeError:
            # 响应不是有效的JSON格式
            error_message = f"HTTP错误: {response.status_code} - 无法解析JSON响应"
            if log_error:
                logger.error(error_message)
                logger.error(f"响应内容: {response.text[:500]}")  # 只打印前500个字符
                logger.error(f"请求URL: {response.url}")
                logger.error(f"请求方法: {response.request.method}")
                logger.error(f"请求头: {response.request.headers}")
            raise Exception(error_message)
    
    def _get_request(self, command: str, extra_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送GET请求到设备API
        
        参数:
            command: API命令
            extra_params: 额外的请求参数
        返回:
            解析后的响应数据
        """
        url = self._build_url(command)
        params = self._build_params(extra_params)
        
        logger.debug(f"发送GET请求: {url}")
        response = self._session.get(url, params=params)
        return self._handle_response(response)
    
    def _put_request(self, command: str, data: Optional[Dict[str, Any]] = None, 
                    extra_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送PUT请求到设备API
        
        参数:
            command: API命令
            data: 请求体数据
            extra_params: 额外的请求参数
        返回:
            解析后的响应数据
        """
        url = self._build_url(command)
        
        # 构建基本参数
        params = self._build_params(extra_params)
        
        # 记录请求详情
        logger.debug(f"发送PUT请求: {url}")
        logger.debug(f"请求参数: {params}")
        if data:
            logger.debug(f"请求数据: {data}")
        
        # 尝试两种方式发送请求：
        # 1. 参数作为URL参数，数据作为表单数据
        # 2. 所有参数都作为表单数据
        try:
            # 方法1：URL参数 + 表单数据
            response = self._session.put(url, params=params, data=data)
            return self._handle_response(response)
        except Exception as e:
            logger.warning(f"方法1请求失败: {str(e)}，尝试方法2...")
            
            # 方法2：所有参数作为表单数据
            try:
                # 合并所有参数到表单数据中
                all_data = {}
                if data:
                    all_data.update(data)
                if params:
                    all_data.update(params)
                
                logger.debug(f"尝试方法2，合并所有参数: {all_data}")
                response = self._session.put(url, data=all_data)
                return self._handle_response(response)
            except Exception as e2:
                # 如果两种方法都失败，抛出第一个异常
                logger.error(f"方法2也失败: {str(e2)}")
                raise e
    
    def connect_async(self) -> bool:
        """
        异步连接到设备
        PUT /api/v{version}/{device_type}/{device_number}/connect
        
        返回:
            操作是否成功
        """
        try:
            logger.info(f"正在发起异步连接请求到{self.device_type}设备...")
            
            # Alpaca API的connect端点不需要请求体
            self._put_request("connect")
            
            logger.info("异步连接请求已发送")
            return True
        except Exception as e:
            logger.error(f"发起异步连接请求失败: {str(e)}")
            return False
    
    def is_connected(self) -> bool:
        """
        获取设备连接状态
        GET /api/v{version}/{device_type}/{device_number}/connected
        
        返回:
            设备是否已连接
        """
        try:
            logger.info(f"正在获取{self.device_type}设备连接状态...")
            
            result = self._get_request("connected")
            
            connected = result.get("Value", False)
            self.connected = connected
            
            logger.info(f"{self.device_type}设备连接状态: {'已连接' if connected else '未连接'}")
            return connected
        except Exception as e:
            logger.error(f"获取连接状态失败: {str(e)}")
            return False
    
    def set_connected(self, connected: bool) -> bool:
        """
        设置设备连接状态
        PUT /api/v{version}/{device_type}/{device_number}/connected
        
        参数:
            connected: 是否连接
        返回:
            操作是否成功
        """
        try:
            # 根据Alpaca API规范：
            # 1. 使用form-urlencoded格式传递参数
            # 2. 布尔值需要用小写的字符串 "true" 或 "false"
            # 3. 参数名称大小写敏感
            # 4. 不同的ASCOM实现可能需要不同的参数名称
            
            # 创建参数字典，尝试多种可能的参数名称
            form_data = {
                "Connected": "true" if connected else "false",
                # 附加其他可能的参数形式，以防API期望不同的名称
                "connected": "true" if connected else "false",
                "isConnected": "true" if connected else "false"
            }
            
            state_str = "连接" if connected else "断开连接"
            logger.info(f"正在设置{self.device_type}设备状态为: {state_str}")
            
            self._put_request("connected", data=form_data)
            
            # 验证连接状态是否更改成功
            current_connected = self.is_connected()
            if current_connected == connected:
                self.connected = connected
                logger.info(f"{self.device_type}设备状态已更新为: {'已连接' if connected else '已断开'}")
                return True
            else:
                logger.error(f"设置{self.device_type}设备状态失败：期望 {connected}，实际 {current_connected}")
                return False
                
        except Exception as e:
            logger.error(f"设置连接状态失败: {str(e)}")
            return False
    
    def is_connecting(self) -> bool:
        """
        获取设备是否正在连接中
        GET /api/v{version}/{device_type}/{device_number}/connecting
        
        返回:
            设备是否正在连接中
        """
        try:
            result = self._get_request("connecting")
            connecting = result.get("Value", False)
            
            logger.debug(f"正在检查{self.device_type}设备连接进度...")
            return connecting
        except Exception as e:
            logger.debug(f"检查连接进度失败: {str(e)}")
            return False
    
    def connect(self, timeout: int = 30) -> bool:
        """
        连接到设备并等待连接完成
        
        参数:
            timeout: 连接超时时间（秒）
        返回:
            是否成功连接
        """
        try:
            # 检查当前连接状态
            logger.info(f"检查{self.device_type}设备是否已连接...")
            if self.is_connected():
                logger.info(f"{self.device_type}设备已连接")
                return True
                
            # 直接设置Connected属性为true代替使用connect方法
            # 有些ASCOM驱动不支持connect方法，但支持设置Connected属性
            logger.info(f"正在连接到{self.device_type}设备 {self.host}:{self.port}/{self.device_number}...")
            
            # 直接设置Connected=true
            result = self.set_connected(True)
            if not result:
                logger.error("连接设备失败")
                return False
                
            # 确认连接是否成功
            if self.is_connected():
                logger.info(f"{self.device_type}设备已成功连接")
                return True
            else:
                logger.error(f"{self.device_type}设备连接失败")
                return False
            
        except Exception as e:
            logger.error(f"连接{self.device_type}设备时出错: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    def disconnect(self) -> bool:
        """
        断开与设备的连接
        
        返回:
            操作是否成功
        """
        try:
            logger.info(f"正在断开与{self.device_type}设备的连接...")
            
            # 设置连接状态为False
            success = self.set_connected(False)
            
            if success:
                logger.info(f"已断开与{self.device_type}设备的连接")
            
            return success
        except Exception as e:
            logger.error(f"断开连接失败: {str(e)}")
            return False
    
    def get_description(self) -> str:
        """
        获取设备描述
        
        返回:
            设备描述
        """
        try:
            result = self._get_request("description")
            description = result.get("Value", "")
            
            logger.info(f"{self.device_type}设备描述: {description}")
            return description
        except Exception as e:
            logger.error(f"获取设备描述失败: {str(e)}")
            return ""
    
    def get_driver_info(self) -> str:
        """
        获取驱动程序信息
        
        返回:
            驱动程序信息
        """
        try:
            result = self._get_request("driverinfo")
            driver_info = result.get("Value", "")
            
            logger.info(f"{self.device_type}驱动程序信息: {driver_info}")
            return driver_info
        except Exception as e:
            logger.error(f"获取驱动程序信息失败: {str(e)}")
            return ""
    
    def get_driver_version(self) -> str:
        """
        获取驱动程序版本
        
        返回:
            驱动程序版本
        """
        try:
            result = self._get_request("driverversion")
            driver_version = result.get("Value", "")
            
            logger.info(f"{self.device_type}驱动程序版本: {driver_version}")
            return driver_version
        except Exception as e:
            logger.error(f"获取驱动程序版本失败: {str(e)}")
            return ""
    
    def get_name(self) -> str:
        """
        获取设备名称
        
        返回:
            设备名称
        """
        try:
            result = self._get_request("name")
            name = result.get("Value", "")
            
            logger.info(f"{self.device_type}设备名称: {name}")
            return name
        except Exception as e:
            logger.error(f"获取设备名称失败: {str(e)}")
            return ""
    
    def refresh(self):
        """
        刷新设备数据，特别是针对ObservingConditions设备
        
        返回:
            操作是否成功
        """
        try:
            logger.info(f"刷新{self.device_type}设备数据...")
            self._put_request("refresh")
            logger.info(f"{self.device_type}设备数据已刷新")
            return True
        except Exception as e:
            logger.error(f"刷新设备数据失败: {str(e)}")
            return False
            
    # 天气站传感器支持检查方法
    def has_temperature(self):
        """检查是否支持温度传感器"""
        try:
            return bool(self._get_request("hastemperature").get("Value", False))
        except Exception as e:
            logger.debug(f"检查温度传感器支持失败: {str(e)}")
            return False
    
    def has_humidity(self):
        """检查是否支持湿度传感器"""
        try:
            return bool(self._get_request("hashumidity").get("Value", False))
        except Exception as e:
            logger.debug(f"检查湿度传感器支持失败: {str(e)}")
            return False
    
    def has_pressure(self):
        """检查是否支持气压传感器"""
        try:
            return bool(self._get_request("haspressure").get("Value", False))
        except Exception as e:
            logger.debug(f"检查气压传感器支持失败: {str(e)}")
            return False
    
    def has_wind_speed(self):
        """检查是否支持风速传感器"""
        try:
            return bool(self._get_request("haswindspeed").get("Value", False))
        except Exception as e:
            logger.debug(f"检查风速传感器支持失败: {str(e)}")
            return False
    
    def has_wind_direction(self):
        """检查是否支持风向传感器"""
        try:
            return bool(self._get_request("haswinddirection").get("Value", False))
        except Exception as e:
            logger.debug(f"检查风向传感器支持失败: {str(e)}")
            return False
    
    def has_rain_rate(self):
        """检查是否支持降雨率传感器"""
        try:
            return bool(self._get_request("hasrainrate").get("Value", False))
        except Exception as e:
            logger.debug(f"检查降雨率传感器支持失败: {str(e)}")
            return False
    
    def has_cloud_cover(self):
        """检查是否支持云量传感器"""
        try:
            return bool(self._get_request("hascloudcover").get("Value", False))
        except Exception as e:
            logger.debug(f"检查云量传感器支持失败: {str(e)}")
            return False
    
    def has_dew_point(self):
        """检查是否支持露点传感器"""
        try:
            return bool(self._get_request("hasdewpoint").get("Value", False))
        except Exception as e:
            logger.debug(f"检查露点传感器支持失败: {str(e)}")
            return False
    
    def has_sky_brightness(self):
        """检查是否支持天空亮度传感器"""
        try:
            return bool(self._get_request("hasskybrightness").get("Value", False))
        except Exception as e:
            logger.debug(f"检查天空亮度传感器支持失败: {str(e)}")
            return False
    
    def has_sky_temperature(self):
        """检查是否支持天空温度传感器"""
        try:
            return bool(self._get_request("hasskytemperature").get("Value", False))
        except Exception as e:
            logger.debug(f"检查天空温度传感器支持失败: {str(e)}")
            return False
    
    def has_star_fwhm(self):
        """检查是否支持星点FWHM传感器"""
        try:
            return bool(self._get_request("hasstarfwhm").get("Value", False))
        except Exception as e:
            logger.debug(f"检查星点FWHM传感器支持失败: {str(e)}")
            return False
    
    # 天气站数据获取方法
    def get_temperature(self):
        """获取温度数据"""
        try:
            # 确保获取的是原始浮点数值，不做任何四舍五入或截断
            result = self._get_request("temperature")
            if "Value" in result:
                return float(result.get("Value"))
            return 0.0
        except Exception as e:
            logger.debug(f"获取温度数据失败: {str(e)}")
            return None
    
    def get_humidity(self):
        """获取湿度数据"""
        try:
            result = self._get_request("humidity")
            if "Value" in result:
                return float(result.get("Value"))
            return 0.0
        except Exception as e:
            logger.debug(f"获取湿度数据失败: {str(e)}")
            return None
    
    def get_pressure(self):
        """获取气压数据"""
        try:
            result = self._get_request("pressure")
            if "Value" in result:
                return float(result.get("Value"))
            return 0.0
        except Exception as e:
            logger.debug(f"获取气压数据失败: {str(e)}")
            return None
    
    def get_wind_speed(self):
        """获取风速数据"""
        try:
            result = self._get_request("windspeed")
            if "Value" in result:
                return float(result.get("Value"))
            return 0.0
        except Exception as e:
            logger.debug(f"获取风速数据失败: {str(e)}")
            return None
    
    def get_wind_direction(self):
        """获取风向数据"""
        try:
            result = self._get_request("winddirection")
            if "Value" in result:
                return float(result.get("Value"))
            return 0.0
        except Exception as e:
            logger.debug(f"获取风向数据失败: {str(e)}")
            return None
    
    def get_rain_rate(self):
        """获取降雨率数据"""
        try:
            result = self._get_request("rainrate")
            if "Value" in result:
                return float(result.get("Value"))
            return 0.0
        except Exception as e:
            logger.debug(f"获取降雨率数据失败: {str(e)}")
            return None
    
    def get_cloud_cover(self):
        """获取云量数据"""
        try:
            result = self._get_request("cloudcover")
            if "Value" in result:
                return float(result.get("Value"))
            return 0.0
        except Exception as e:
            logger.debug(f"获取云量数据失败: {str(e)}")
            return None
    
    def get_dew_point(self):
        """获取露点数据"""
        try:
            result = self._get_request("dewpoint")
            if "Value" in result:
                return float(result.get("Value"))
            return 0.0
        except Exception as e:
            logger.debug(f"获取露点数据失败: {str(e)}")
            return None
    
    def get_sky_brightness(self):
        """获取天空亮度数据"""
        try:
            result = self._get_request("skybrightness")
            if "Value" in result:
                return float(result.get("Value"))
            return 0.0
        except Exception as e:
            logger.debug(f"获取天空亮度数据失败: {str(e)}")
            return None
    
    def get_sky_temperature(self):
        """获取天空温度数据"""
        try:
            result = self._get_request("skytemperature")
            if "Value" in result:
                return float(result.get("Value"))
            return 0.0
        except Exception as e:
            logger.debug(f"获取天空温度数据失败: {str(e)}")
            return None
    
    def get_star_fwhm(self):
        """获取星点FWHM数据"""
        try:
            result = self._get_request("starfwhm")
            if "Value" in result:
                return float(result.get("Value"))
            return 0.0
        except Exception as e:
            logger.debug(f"获取星点FWHM数据失败: {str(e)}")
            return None
    
    def get_wind_gust(self):
        """获取风力峰值数据"""
        try:
            result = self._get_request("windgust")
            if "Value" in result:
                return float(result.get("Value"))
            return 0.0
        except Exception as e:
            logger.debug(f"获取风力峰值数据失败: {str(e)}")
            return None
    
    def get_sky_quality(self):
        """获取天空质量数据"""
        try:
            result = self._get_request("skyquality")
            if "Value" in result:
                return float(result.get("Value"))
            return 0.0
        except Exception as e:
            logger.debug(f"获取天空质量数据失败: {str(e)}")
            return None
    
    def get_sensor_description(self, sensor_name):
        """获取传感器描述"""
        try:
            params = {"SensorName": sensor_name}
            return str(self._get_request("sensordescription", params).get("Value", ""))
        except Exception as e:
            logger.debug(f"获取传感器描述失败: {str(e)}")
            return None
    
    def get_time_since_last_update(self, sensor_name=None):
        """获取自上次更新以来的时间"""
        try:
            # 由于ASCOM Alpaca API需要传递SensorName参数，这里我们使用一个默认值
            # 如果不传递，很多驱动器会返回400错误
            if not sensor_name:
                # 默认使用Temperature作为传感器名，这是大多数设备都支持的
                sensor_name = "Temperature"
            
            params = {"SensorName": sensor_name}
            return float(self._get_request("timesincelastupdate", params).get("Value", 0.0))
        except Exception as e:
            logger.debug(f"获取自上次更新以来的时间失败: {str(e)}")
            return None
    
    def get_average_period(self):
        """获取平均周期"""
        try:
            return float(self._get_request("averageperiod").get("Value", 0.0))
        except Exception as e:
            logger.debug(f"获取平均周期失败: {str(e)}")
            return None
    
    def put_average_period(self, period):
        """设置平均周期"""
        try:
            data = {"AveragePeriod": str(period)}
            self._put_request("averageperiod", data)
            return True
        except Exception as e:
            logger.debug(f"设置平均周期失败: {str(e)}")
            return False
    
    def is_safe(self):
        """获取安全状态"""
        try:
            # ObservingConditions API 中的 IsSafe 方法通常被设计用来检查天气是否允许观测
            # 但在一些ASCOM驱动中可能不支持，忽略这个错误
            try:
                return bool(self._get_request("issafe").get("Value", True))
            except Exception:
                # 如果发生错误，默认为安全
                logger.debug("IsSafe方法不受支持，默认返回安全")
                return True
        except Exception as e:
            logger.debug(f"获取安全状态失败: {str(e)}")
            return True  # 默认为安全
    
    # 站点位置信息方法
    def get_site_latitude(self) -> float:
        """
        获取站点纬度
        
        返回:
            纬度（度，正值表示北纬，负值表示南纬）
        """
        try:
            result = self._get_request("sitelatitude")
            latitude = result.get("Value", 0.0)
            return latitude
        except Exception as e:
            logger.debug(f"获取站点纬度失败: {str(e)}")
            return 0.0
    
    def get_site_longitude(self) -> float:
        """
        获取站点经度
        
        返回:
            经度（度，正值表示东经，负值表示西经）
        """
        try:
            result = self._get_request("sitelongitude")
            longitude = result.get("Value", 0.0)
            return longitude
        except Exception as e:
            logger.debug(f"获取站点经度失败: {str(e)}")
            return 0.0
    
    def get_site_elevation(self) -> float:
        """
        获取站点海拔高度
        
        返回:
            海拔高度（米）
        """
        try:
            result = self._get_request("siteelevation")
            elevation = result.get("Value", 0.0)
            return elevation
        except Exception as e:
            logger.debug(f"获取站点海拔高度失败: {str(e)}")
            return 0.0 