#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
望远镜赤道仪驱动模块
实现ASCOM Alpaca标准API赤道仪控制接口
"""

import logging
import time
from typing import Dict, Any, Optional, Union, List, Tuple

# 导入基类
from common.alpaca_device import AlpacaDevice

# 设置日志
logger = logging.getLogger(__name__)

class TelescopeDriver(AlpacaDevice):
    """
    望远镜赤道仪驱动类
    继承自AlpacaDevice基类，添加望远镜特有功能
    """
    
    def __init__(self, host: str = "localhost", port: int = 11111, device_number: int = 0, client_id: int = 1, api_version: int = 1):
        """
        初始化望远镜驱动
        
        参数:
            host: Alpaca服务器主机名或IP
            port: Alpaca服务器端口
            device_number: 设备编号
            client_id: 客户端ID，用于跟踪请求
            api_version: API版本号
        """
        # 调用父类初始化方法，指定设备类型为telescope
        super().__init__(device_type="telescope", host=host, port=port, 
                        device_number=device_number, client_id=client_id, 
                        api_version=api_version)
        
        # 望远镜特有属性
        self.right_ascension = 0.0
        self.declination = 0.0
        self.altitude = 0.0
        self.azimuth = 0.0
        self.is_parked = False
        self.is_tracking = False
        self.target_right_ascension = 0.0
        self.target_declination = 0.0
        
        #logger.info(f"初始化望远镜驱动: {host}:{port}")

    # ---------------- 位置信息方法 ----------------
    
    def get_ra_dec(self) -> Tuple[float, float]:
        """
        获取望远镜当前赤经赤纬坐标
        
        返回:
            (赤经, 赤纬) - 单位：度
        """
        try:
            # 获取赤经
            ra_result = self._get_request("rightascension")
            self.right_ascension = ra_result.get("Value", 0.0)
            
            # 获取赤纬
            dec_result = self._get_request("declination")
            self.declination = dec_result.get("Value", 0.0)
            
            #logger.info(f"望远镜坐标 - 赤经: {self.right_ascension}度, 赤纬: {self.declination}度")
            return (self.right_ascension, self.declination)
        except Exception as e:
            #logger.error(f"获取望远镜赤经赤纬坐标失败: {str(e)}")
            return (0.0, 0.0)
    
    def get_alt_az(self) -> Tuple[float, float]:
        """
        获取望远镜当前地平坐标（高度角和方位角）
        
        返回:
            (高度角, 方位角) - 单位：度
        """
        try:
            # 获取高度角
            alt_result = self._get_request("altitude")
            self.altitude = alt_result.get("Value", 0.0)
            
            # 获取方位角
            az_result = self._get_request("azimuth")
            self.azimuth = az_result.get("Value", 0.0)
            
            #logger.info(f"望远镜坐标 - 高度角: {self.altitude}度, 方位角: {self.azimuth}度")
            return (self.altitude, self.azimuth)
        except Exception as e:
            #logger.error(f"获取望远镜地平坐标失败: {str(e)}")
            return (0.0, 0.0)
    
    # ---------------- 望远镜控制方法 ----------------
    
    def slew_to_coordinates(self, ra: float, dec: float) -> bool:
        """
        控制望远镜转向指定的赤经赤纬坐标
        
        参数:
            ra: 目标赤经（度）
            dec: 目标赤纬（度）
        返回:
            操作是否成功
        """
        try:
            # 先设置目标坐标
            self.set_target_coordinates(ra, dec)
            
            # 发送转向命令
            #logger.info(f"控制望远镜转向坐标 - 赤经: {ra}度, 赤纬: {dec}度")
            self._put_request("slewtocoordinates", data={"RightAscension": str(ra), "Declination": str(dec)})
            
            # 等待望远镜完成转向
            while self.is_slewing():
                #logger.info("望远镜正在转向目标位置...")
                time.sleep(1)
                
            #logger.info("望远镜已完成转向")
            return True
        except Exception as e:
            #logger.error(f"控制望远镜转向失败: {str(e)}")
            return False
    
    def set_target_coordinates(self, ra: float, dec: float) -> bool:
        """
        设置望远镜目标坐标
        
        参数:
            ra: 目标赤经（度）
            dec: 目标赤纬（度）
        返回:
            操作是否成功
        """
        try:
            # 设置目标赤经
            #logger.info(f"设置目标赤经: {ra}度")
            self._put_request("targetrightascension", data={"TargetRightAscension": str(ra)})
            self.target_right_ascension = ra
            
            # 设置目标赤纬
            #logger.info(f"设置目标赤纬: {dec}度")
            self._put_request("targetdeclination", data={"TargetDeclination": str(dec)})
            self.target_declination = dec
            
            return True
        except Exception as e:
            #logger.error(f"设置目标坐标失败: {str(e)}")
            return False
    
    def is_slewing(self) -> bool:
        """
        检查望远镜是否正在转向中
        
        返回:
            是否正在转向
        """
        try:
            result = self._get_request("slewing")
            slewing = result.get("Value", False)
            
            return slewing
        except Exception as e:
            #logger.error(f"检查望远镜转向状态失败: {str(e)}")
            return False
    
    def abort_slew(self) -> bool:
        """
        中止当前转向操作
        
        返回:
            操作是否成功
        """
        try:
            #logger.info("中止望远镜转向")
            self._put_request("abortslew")
            return True
        except Exception as e:
            #logger.error(f"中止转向失败: {str(e)}")
            return False
    
    # ---------------- 望远镜跟踪控制 ----------------
    
    def get_tracking(self) -> bool:
        """
        获取望远镜跟踪状态
        
        返回:
            是否开启跟踪
        """
        try:
            result = self._get_request("tracking")
            tracking = result.get("Value", False)
            self.is_tracking = tracking
            
            #logger.info(f"望远镜跟踪状态: {'已开启' if tracking else '已关闭'}")
            return tracking
        except Exception as e:
            #logger.error(f"获取跟踪状态失败: {str(e)}")
            return False
    
    def set_tracking(self, tracking: bool) -> bool:
        """
        设置望远镜跟踪状态
        
        参数:
            tracking: 是否开启跟踪
        返回:
            操作是否成功
        """
        try:
            state_str = "开启" if tracking else "关闭"
            #logger.info(f"{state_str}望远镜跟踪")
            
            self._put_request("tracking", data={"Tracking": "true" if tracking else "false"})
            self.is_tracking = tracking
            
            #logger.info(f"已{state_str}望远镜跟踪")
            return True
        except Exception as e:
            #logger.error(f"设置跟踪状态失败: {str(e)}")
            return False
    
    # ---------------- 停靠控制 ----------------
    
    def park(self) -> bool:
        """
        将望远镜停靠到停靠位置
        
        返回:
            操作是否成功
        """
        try:
            #logger.info("正在将望远镜停靠到停靠位置")
            self._put_request("park")
            
            # 等待停靠操作完成
            while self.is_slewing():
                #logger.info("等待望远镜完成停靠...")
                time.sleep(1)
                
            self.is_parked = True
            #logger.info("望远镜已停靠")
            return True
        except Exception as e:
            #logger.error(f"停靠望远镜失败: {str(e)}")
            return False
    
    def unpark(self) -> bool:
        """
        解除望远镜停靠状态
        
        返回:
            操作是否成功
        """
        try:
            #logger.info("正在解除望远镜停靠状态")
            self._put_request("unpark")
            
            self.is_parked = False
            #logger.info("已解除望远镜停靠状态")
            return True
        except Exception as e:
            #logger.error(f"解除停靠状态失败: {str(e)}")
            return False
    
    def is_parked(self) -> bool:
        """
        检查望远镜是否处于停靠状态
        
        返回:
            是否停靠
        """
        try:
            result = self._get_request("atpark")
            parked = result.get("Value", False)
            self.is_parked = parked
            
            return parked
        except Exception as e:
            #logger.error(f"检查停靠状态失败: {str(e)}")
            return False
    
    # ---------------- 脉冲导星 ----------------
    
    def is_pulseguiding(self) -> bool:
        """
        检查望远镜是否正在进行脉冲导星
        
        返回:
            是否正在脉冲导星
        """
        try:
            result = self._get_request("ispulseguiding")
            pulseguiding = result.get("Value", False)
            
            return pulseguiding
        except Exception as e:
            #logger.error(f"检查脉冲导星状态失败: {str(e)}")
            return False
    
    # ---------------- 站点信息 ----------------
    
    def get_site_latitude(self) -> float:
        """
        获取观测站纬度
        
        返回:
            纬度（度）
        """
        try:
            result = self._get_request("sitelatitude")
            latitude = result.get("Value", 0.0)
            
            #logger.info(f"观测站纬度: {latitude}度")
            return latitude
        except Exception as e:
            #logger.error(f"获取观测站纬度失败: {str(e)}")
            return 0.0
    
    def get_site_longitude(self) -> float:
        """
        获取观测站经度
        
        返回:
            经度（度）
        """
        try:
            result = self._get_request("sitelongitude")
            longitude = result.get("Value", 0.0)
            
            #logger.info(f"观测站经度: {longitude}度")
            return longitude
        except Exception as e:
            #logger.error(f"获取观测站经度失败: {str(e)}")
            return 0.0
    
    def get_site_elevation(self) -> float:
        """
        获取观测站海拔
        
        返回:
            海拔（米）
        """
        try:
            result = self._get_request("siteelevation")
            elevation = result.get("Value", 0.0)
            
            #logger.info(f"观测站海拔: {elevation}米")
            return elevation
        except Exception as e:
            #logger.error(f"获取观测站海拔失败: {str(e)}")
            return 0.0
    
    def get_sidereal_time(self) -> str:
        """
        获取当地恒星时
        
        返回:
            当地恒星时（小时）
        """
        try:
            result = self._get_request("siderealtime")
            sidereal_time = result.get("Value", "0.0")
            
            #logger.info(f"当地恒星时: {sidereal_time}小时")
            return sidereal_time
        except Exception as e:
            #logger.error(f"获取当地恒星时失败: {str(e)}")
            return "0.0" 