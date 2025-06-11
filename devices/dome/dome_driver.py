#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
圆顶驱动模块
实现ASCOM Alpaca标准API圆顶控制接口
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Union, List, Tuple

# 导入基类
from common.alpaca_device import AlpacaDevice

# 设置日志
logger = logging.getLogger(__name__)

class DomeDriver(AlpacaDevice):
    """
    圆顶驱动类
    继承自AlpacaDevice基类，添加圆顶特有功能
    """
    
    def __init__(self, host: str = "localhost", port: int = 11111, device_number: int = 0, client_id: int = 1, api_version: int = 1):
        """
        初始化圆顶驱动
        
        参数:
            host: Alpaca服务器主机名或IP
            port: Alpaca服务器端口
            device_number: 设备编号
            client_id: 客户端ID，用于跟踪请求
            api_version: API版本号
        """
        # 调用父类初始化方法，指定设备类型为dome
        super().__init__(device_type="dome", host=host, port=port, 
                        device_number=device_number, client_id=client_id, 
                        api_version=api_version)
        
        # 圆顶特有属性
        self.altitude = 0.0
        self.azimuth = 0.0
        self.is_parked = False
        self._slewing_status = False
        self.is_shutter_open = False
        self._follows_telescope = False

    # ---------------- 位置信息方法 ----------------
    
    def get_azimuth(self) -> float:
        """
        获取圆顶当前方位角
        
        返回:
            方位角 - 单位：度（0-359.99）
        """
        try:
            # 获取方位角
            result = self._get_request("azimuth")
            self.azimuth = result.get("Value", 0.0)
            
            return self.azimuth
        except Exception as e:
            logger.error(f"获取圆顶方位角失败: {str(e)}")
            return 0.0
    
    
    # ---------------- 圆顶控制方法 ----------------
    
    def slew_to_azimuth(self, azimuth: float) -> bool:
        """
        控制圆顶转向指定的方位角

        参数:
            azimuth: 目标方位角（度，0-359.99）
        返回:
            操作是否成功
        """
        try:
            logger.info(f"控制圆顶转向方位角: {azimuth}度")
            self._put_request("slewtoazimuth", data={"Azimuth": azimuth})
            return True
        except Exception as e:
            logger.error(f"控制圆顶转向失败: {str(e)}")
            return False
    
    def abort_slew(self) -> bool:
        """
        中止当前转向操作
        
        返回:
            操作是否成功
        """
        try:
            logger.info("中止圆顶转向")
            self._put_request("abortslew")
            return True
        except Exception as e:
            logger.error(f"中止转向失败: {str(e)}")
            return False
    
    def is_slewing(self) -> bool:
        """
        检查圆顶是否正在转向中
        
        返回:
            是否正在转向
        """
        try:
            result = self._get_request("slewing")
            #logger.info(f"【调试】is_slewing API返回原始数据: {result}")
            
            slewing = result.get("Value", False)
            #logger.info(f"【调试】is_slewing 解析后的值: {slewing}, 类型: {type(slewing)}")
            
            self._slewing_status = slewing
            
            return slewing
        except Exception as e:
            logger.error(f"检查圆顶转向状态失败: {str(e)}")
            return False
    
    # ---------------- 天窗控制 ----------------
    
    def open_shutter(self) -> bool:
        """
        打开圆顶天窗
        
        返回:
            操作是否成功
        """
        try:
            logger.info("打开圆顶天窗")
            self._put_request("openshutter")
            
            # 等待天窗打开完成
            while True:
                # 周期性检查转向状态
                slewing_status = self.is_slewing()
                #logger.info(f"【调试】打开天窗过程中的转向状态: {slewing_status}")
                
                # 检查天窗状态
                shutter_status = self.get_shutter_status()
                #logger.info(f"【调试】当前天窗状态: {shutter_status}")
                
                if shutter_status == 0:  # 天窗已打开
                    break
                time.sleep(1)
                
            self.is_shutter_open = True
            return True
        except Exception as e:
            logger.error(f"打开圆顶天窗失败: {str(e)}")
            return False
    
    def close_shutter(self) -> bool:
        """
        关闭圆顶天窗
        
        返回:
            操作是否成功
        """
        try:
            logger.info("关闭圆顶天窗")
            self._put_request("closeshutter")
            
            # 等待天窗关闭完成
            while True:
                # 周期性检查转向状态
                slewing_status = self.is_slewing()
                #logger.info(f"【调试】关闭天窗过程中的转向状态: {slewing_status}")
                
                # 检查天窗状态
                shutter_status = self.get_shutter_status()
                #logger.info(f"【调试】当前天窗状态: {shutter_status}")
                
                if shutter_status == 1:  # 天窗已关闭
                    break
                time.sleep(1)
                
            self.is_shutter_open = False
            return True
        except Exception as e:
            logger.error(f"关闭圆顶天窗失败: {str(e)}")
            return False

    # ---------------- 获取天窗状态 ----------------
    def get_shutter_status(self) -> int:
        """
        获取天窗状态
        
        返回:
            天窗状态码:
            0=shutterOpen (已打开)
            1=shutterClosed (已关闭)
            2=shutterOpening (正在打开)
            3=shutterClosing (正在关闭)
            4=shutterError (错误)
        """
        try:
            result = self._get_request("shutterstatus")
            #logger.info(f"【调试】get_shutter_status API返回原始数据: {result}")
            
            status = result.get("Value", 1)  # 默认关闭
            #logger.info(f"【调试】get_shutter_status 解析后的值: {status}, 类型: {type(status)}")
            
            # 更新天窗状态
            if status == 0:
                self.is_shutter_open = True
            elif status == 1:
                self.is_shutter_open = False
                
            return status
        except Exception as e:
            logger.error(f"获取天窗状态失败: {str(e)}")
            return 1  # 默认为关闭
    
    # ---------------- 停靠功能 ----------------
    
    def park(self) -> bool:
        """
        停靠圆顶到安全位置
        
        返回:
            操作是否成功
        """
        try:
            logger.info("停靠圆顶")
            self._put_request("park")
            
            # 等待停靠完成
            while not self.is_parked():
                logger.info("圆顶正在停靠...")
                time.sleep(1)
                
            logger.info("圆顶已停靠")
            self.is_parked = True
            return True
        except Exception as e:
            logger.error(f"停靠圆顶失败: {str(e)}")
            return False
    
    def unpark(self) -> bool:
        """
        解除圆顶停靠状态
        
        返回:
            操作是否成功
        """
        try:
            logger.info("解除圆顶停靠")
            self._put_request("unpark")
            
            # 等待解除停靠完成
            while self.is_parked():
                logger.info("圆顶正在解除停靠...")
                time.sleep(1)
                
            logger.info("圆顶已解除停靠")
            self.is_parked = False
            return True
        except Exception as e:
            logger.error(f"解除圆顶停靠失败: {str(e)}")
            return False
    
    def is_parked(self) -> bool:
        """
        检查圆顶是否处于停靠状态
        
        返回:
            是否停靠
        """
        try:
            result = self._get_request("atpark")
            parked = result.get("Value", False)
            self.is_parked = parked
            
            return parked
        except Exception as e:
            logger.error(f"检查圆顶停靠状态失败: {str(e)}")
            return False
    
    # ---------------- 同步功能 ----------------
    
    def get_slaved(self) -> bool:
        """
        获取圆顶是否与望远镜同步
        
        返回:
            是否同步
        """
        try:
            result = self._get_request("slaved")
            slaved = result.get("Value", False)
            self._follows_telescope = slaved
            
            return slaved
        except Exception as e:
            logger.error(f"获取圆顶同步状态失败: {str(e)}")
            return False
    
    def set_slaved(self, slaved: bool) -> bool:
        """
        设置圆顶是否与望远镜同步
        
        参数:
            slaved: 是否同步
        返回:
            操作是否成功
        """
        try:
            state_str = "开启" if slaved else "关闭"
            logger.info(f"{state_str}圆顶与望远镜同步")
            
            # 根据Alpaca API规范，布尔值需要用小写的字符串 "true" 或 "false"
            self._put_request("slaved", data={"Slaved": "true" if slaved else "false"})
            
            # 验证设置结果
            current = self.get_slaved()
            if current == slaved:
                logger.info(f"已{state_str}圆顶与望远镜同步")
                self._follows_telescope = slaved
                return True
            else:
                logger.error(f"{state_str}圆顶与望远镜同步失败")
                return False
                
        except Exception as e:
            logger.error(f"设置圆顶同步状态失败: {str(e)}")
            return False
    
    # ---------------- 原点和校准 ----------------
    
    def find_home(self) -> bool:
        """
        控制圆顶寻找原点位置
        
        返回:
            操作是否成功
        """
        try:
            logger.info("控制圆顶寻找原点位置")
            self._put_request("findhome")
            
            # 等待寻找原点完成
            while self.is_slewing():
                logger.info("圆顶正在寻找原点...")
                time.sleep(1)
                
            logger.info("圆顶已找到原点位置")
            return True
        except Exception as e:
            logger.error(f"控制圆顶寻找原点失败: {str(e)}")
            return False
    
    def is_at_home(self) -> bool:
        """
        检查圆顶是否在原点位置
        
        返回:
            是否在原点
        """
        try:
            result = self._get_request("athome")
            at_home = result.get("Value", False)
            
            return at_home
        except Exception as e:
            logger.error(f"检查圆顶原点状态失败: {str(e)}")
            return False 