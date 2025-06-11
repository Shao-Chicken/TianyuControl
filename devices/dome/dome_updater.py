#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
圆顶数据更新线程
用于定期获取圆顶数据（方位角、天窗状态等）
并将数据保存到共享变量中，供其他组件使用
"""

import threading
import time
import logging
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal

# 导入客户端扩展类
from telescope_ui.models.alpaca_client_extension import AlpacaClientExtension

# 设置日志
logger = logging.getLogger(__name__)

class DomeUpdater(QObject):
    """
    圆顶数据更新线程类
    管理圆顶数据的定期获取和更新
    """
    # 定义信号
    data_updated = pyqtSignal(dict)  # 发送更新后的数据
    error_occurred = pyqtSignal(str)  # 发送错误信息
    
    def __init__(self, update_interval: float = 1.0):
        """
        初始化圆顶数据更新器
        
        参数:
            update_interval: 更新间隔时间（秒）
        """
        super(DomeUpdater, self).__init__()
        self.update_interval = update_interval
        self.running = False
        self.thread = None
        self.dome_data = {
            "azimuth": 0.0,             # 方位角（度）
            "altitude": 0.0,            # 高度角（度）
            "shutter_status": 1,        # 天窗状态（0=打开，1=关闭，2=打开中，3=关闭中）
            "slewing": False,           # 转向状态
            "parked": False,            # 停靠状态
            "at_home": False,           # 是否在home位置
            "slaved": False,            # 是否跟随望远镜
            "driver_info": "",          # 驱动信息
            "driver_version": "",       # 驱动版本
        }
        self.alpaca_client = None
        self.client_extension = None
        self.device_number = 0
        
    def set_client(self, client, device_number: int = 0):
        """
        设置Alpaca客户端
        
        参数:
            client: AlpacaClient实例
            device_number: 设备编号
        """
        self.alpaca_client = client
        self.device_number = device_number
        # 创建客户端扩展
        self.client_extension = AlpacaClientExtension(client)
    
    def start(self):
        """启动更新线程"""
        if self.running:
            return
            
        if not self.alpaca_client:
            logger.error("未设置Alpaca客户端，无法启动更新线程")
            self.error_occurred.emit("未设置Alpaca客户端，无法启动更新线程")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        logger.info("圆顶数据更新线程已启动")
        
    def stop(self):
        """停止更新线程"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(2.0)  # 等待线程最多2秒
        logger.info("圆顶数据更新线程已停止")
    
    def get_data(self) -> Dict[str, Any]:
        """
        获取当前圆顶数据
        
        返回:
            圆顶数据字典
        """
        return self.dome_data.copy()  # 返回副本避免线程安全问题
    
    def _update_loop(self):
        """更新循环 - 在单独的线程中运行"""
        try:
            while self.running:
                try:
                    self._update_dome_data()
                    time.sleep(self.update_interval)
                except Exception as e:
                    error_msg = f"更新圆顶数据时出错: {str(e)}"
                    logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    time.sleep(2.0)  # 发生错误后暂停2秒
        except Exception as e:
            logger.error(f"更新线程异常终止: {str(e)}")
            self.error_occurred.emit(f"更新线程异常终止: {str(e)}")
    
    def _update_dome_data(self):
        """从Alpaca API获取最新的圆顶数据"""
        if not self.alpaca_client:
            return
            
        try:
            # 检查连接状态
            connected = self.alpaca_client.get_connected(self.device_number)
            if not connected:
                logger.debug("圆顶未连接，跳过数据更新")
                return
                
            # 更新方位角
            try:
                self.dome_data["azimuth"] = self.alpaca_client.get_azimuth(self.device_number)
            except Exception as e:
                logger.error(f"获取方位角失败: {str(e)}")
                self.error_occurred.emit(f"获取方位角失败: {str(e)}")
            
            # 更新高度角（如果支持）
            try:
                self.dome_data["altitude"] = self.alpaca_client.get_altitude(self.device_number)
            except Exception as e:
                # 很多圆顶不支持高度角，所以这个错误可以忽略
                pass
            
            # 获取天窗状态
            try:
                self.dome_data["shutter_status"] = self.alpaca_client.get_shutter_status(self.device_number)
            except Exception as e:
                logger.error(f"获取天窗状态失败: {str(e)}")
                self.error_occurred.emit(f"获取天窗状态失败: {str(e)}")
                
            # 获取转向状态
            try:
                previous_slewing = self.dome_data.get("slewing", False)
                current_slewing = self.alpaca_client.get_slewing(self.device_number)
                
                # 如果转向状态发生变化，记录详细日志
                if previous_slewing != current_slewing:
                    logger.info(f"圆顶转向状态变更: {previous_slewing} -> {current_slewing}")
                
                self.dome_data["slewing"] = current_slewing
            except Exception as e:
                logger.error(f"获取转向状态失败: {str(e)}")
                self.error_occurred.emit(f"获取转向状态失败: {str(e)}")
                
            # 获取停靠状态
            try:
                # 使用扩展类的安全方法获取停靠状态
                if self.client_extension:
                    self.dome_data["parked"] = self.client_extension.get_dome_parked_safe(self.device_number)
                else:
                    # 如果扩展类不可用，使用原始方法
                    self.dome_data["parked"] = self.alpaca_client.get_at_park(self.device_number)
            except Exception as e:
                logger.error(f"获取停靠状态失败: {str(e)}")
                self.error_occurred.emit(f"获取停靠状态失败: {str(e)}")
                
            # 获取是否在home位置
            try:
                # 使用扩展类的安全方法获取home状态
                if self.client_extension:
                    self.dome_data["at_home"] = self.client_extension.get_dome_at_home_safe(self.device_number)
                else:
                    # 如果扩展类不可用，使用原始方法
                    self.dome_data["at_home"] = self.alpaca_client.get_at_home(self.device_number)
            except Exception as e:
                logger.error(f"获取home状态失败: {str(e)}")
                self.error_occurred.emit(f"获取home状态失败: {str(e)}")
                
            # 获取是否跟随望远镜
            try:
                self.dome_data["slaved"] = self.alpaca_client.get_slaved(self.device_number)
            except Exception as e:
                logger.error(f"获取跟随状态失败: {str(e)}")
                self.error_occurred.emit(f"获取跟随状态失败: {str(e)}")
            
            # 每10秒更新一次驱动信息和版本 (不需要频繁更新)
            current_time = time.time()
            if not hasattr(self, 'last_driver_info_update') or current_time - getattr(self, 'last_driver_info_update', 0) > 10:
                # 获取驱动信息
                try:
                    self.dome_data["driver_info"] = self.alpaca_client.get_driver_info(self.device_number)
                except Exception as e:
                    logger.debug(f"获取驱动信息失败: {str(e)}")
                
                # 获取驱动版本
                try:
                    self.dome_data["driver_version"] = self.alpaca_client.get_driver_version(self.device_number)
                except Exception as e:
                    logger.debug(f"获取驱动版本失败: {str(e)}")
                
                self.last_driver_info_update = current_time
                
            # 发送更新后的数据
            self.data_updated.emit(self.dome_data)
                
        except Exception as e:
            logger.error(f"更新圆顶数据时出错: {str(e)}")
            self.error_occurred.emit(f"更新圆顶数据时出错: {str(e)}") 