#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
望远镜数据更新线程
用于定期获取望远镜数据（恒星时、赤经、赤纬、高度角、方位角等）
并将数据保存到共享变量中，供其他组件使用
"""

import sys
import os
import logging
import time
import threading
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入客户端扩展类
from telescope_ui.models.alpaca_client_extension import AlpacaClientExtension

# 设置日志
logger = logging.getLogger(__name__)

class TelescopeUpdater(QObject):
    """
    望远镜数据更新线程类
    管理望远镜数据的定期获取和更新
    """
    # 定义信号
    data_updated = pyqtSignal(dict)  # 发送更新后的数据
    error_occurred = pyqtSignal(str)  # 发送错误信息
    tracking_rates_updated = pyqtSignal(dict)  # 发送支持的跟踪速率
    
    def __init__(self, update_interval: float = 1.0):
        """
        初始化望远镜数据更新器
        
        参数:
            update_interval: 更新间隔时间（秒）
        """
        super(TelescopeUpdater, self).__init__()
        self.update_interval = update_interval
        self.running = False
        self.thread = None
        self.telescope_data = {
            "sidereal_time": 0.0,       # 恒星时（小时）
            "right_ascension": 0.0,     # 赤经（小时）
            "declination": 0.0,         # 赤纬（度）
            "altitude": 0.0,            # 高度角（度）
            "azimuth": 0.0,             # 方位角（度）
            "tracking": False,          # 跟踪状态
            "slewing": False,          # 转向状态
            "parked": False,            # 停靠状态
            "at_home": False,           # 是否在home位置
            "site_latitude": 0.0,       # 站点纬度（度）
            "site_longitude": 0.0,      # 站点经度（度）
            "site_elevation": 0.0,      # 站点海拔（米）
            "equatorial_system": "Unknown" # 赤道坐标系统
        }
        self.alpaca_client = None
        self.client_extension = None
        self.device_number = 0
        
        # 使用线程锁保护状态和数据
        self._lock = threading.RLock()
        # 使用事件来安全停止线程
        self._stop_event = threading.Event()
        
    def set_client(self, client, device_number: int = 0):
        """
        设置Alpaca客户端
        
        参数:
            client: AlpacaClient实例
            device_number: 设备编号
        """
        with self._lock:
            self.alpaca_client = client
            self.device_number = device_number
            # 创建客户端扩展
            self.client_extension = AlpacaClientExtension(client)
    
    def start(self):
        """启动更新线程"""
        with self._lock:
            if self.running:
                return
                
            if not self.alpaca_client:
                logger.error("未设置Alpaca客户端，无法启动更新线程")
                self._safe_emit_error("未设置Alpaca客户端，无法启动更新线程")
                return
                
            # 重置停止事件
            self._stop_event.clear()
            self.running = True
            
            # 创建并启动线程
            self.thread = threading.Thread(target=self._update_loop, daemon=True)
            self.thread.start()
            logger.info("望远镜数据更新线程已启动")
        
    def stop(self):
        """停止更新线程"""
        with self._lock:
            if not self.running:
                return
                
            # 设置停止事件
            self._stop_event.set()
            self.running = False
            
        # 等待线程结束，但不要无限等待
        if self.thread and self.thread.is_alive():
            # 先给线程一些时间自行退出
            start_time = time.time()
            while self.thread.is_alive() and (time.time() - start_time) < 2.0:
                time.sleep(0.1)  # 小间隔等待
                
            # 如果线程仍在运行，记录警告但不再尝试强制终止
            if self.thread.is_alive():
                logger.warning("望远镜数据更新线程未能在预期时间内退出")
            else:
                logger.info("望远镜数据更新线程已正常停止")
                
        # 清理线程引用
        self.thread = None
    
    def get_data(self) -> Dict[str, Any]:
        """
        获取当前望远镜数据
        
        返回:
            望远镜数据字典
        """
        with self._lock:
            return self.telescope_data.copy()  # 返回副本避免线程安全问题
            
    def _safe_emit_data(self, data):
        """安全地发射数据更新信号"""
        if not self._stop_event.is_set() and self.running:
            try:
                self.data_updated.emit(data)
            except RuntimeError as e:
                logger.error(f"发送数据更新信号时出错: {str(e)}")
                # 标记线程应该停止
                self._stop_event.set()
                self.running = False
                
    def _safe_emit_error(self, error_msg):
        """安全地发射错误信号"""
        if not self._stop_event.is_set() and self.running:
            try:
                self.error_occurred.emit(error_msg)
            except RuntimeError as e:
                logger.error(f"发送错误信号时出错: {str(e)}")
                # 如果发生错误，说明对象可能已被删除
                self._stop_event.set()
                self.running = False
                
    def _safe_emit_tracking_rates(self, rates):
        """安全地发射跟踪速率信号"""
        if not self._stop_event.is_set() and self.running:
            try:
                self.tracking_rates_updated.emit(rates)
            except RuntimeError as e:
                logger.error(f"发送跟踪速率信号时出错: {str(e)}")
                # 标记线程应该停止
                self._stop_event.set()
                self.running = False
    
    def _update_loop(self):
        """更新循环 - 在单独的线程中运行"""
        try:
            while not self._stop_event.is_set() and self.running:
                try:
                    if self._stop_event.is_set() or not self.running:
                        break
                        
                    self._update_telescope_data()
                    
                    # 使用事件等待，这样可以更快地响应停止请求
                    if self._stop_event.wait(self.update_interval):
                        break  # 如果事件被设置，立即退出循环
                        
                except Exception as e:
                    error_msg = f"更新望远镜数据时出错: {str(e)}"
                    logger.error(error_msg)
                    self._safe_emit_error(error_msg)
                    
                    # 发生错误后稍作暂停，但使用事件等待以便能及时退出
                    if self._stop_event.wait(2.0):  # 等待2秒或者停止信号
                        break
        except Exception as e:
            error_msg = f"更新线程异常终止: {str(e)}"
            logger.error(error_msg)
            self._safe_emit_error(error_msg)
        finally:
            logger.info("望远镜数据更新线程已退出")
    
    def _update_telescope_data(self):
        """从Alpaca API获取最新的望远镜数据"""
        if self._stop_event.is_set() or not self.running:
            return
            
        with self._lock:
            if not self.alpaca_client:
                return
                
        try:
            # 检查连接状态
            with self._lock:
                client = self.alpaca_client
                device_num = self.device_number
                
            if not client:
                return
                
            connected = client.get_connected(device_num)
            if not connected:
                logger.debug("望远镜未连接，跳过数据更新")
                return
                
            # 创建临时数据字典，避免频繁加锁
            temp_data = {}
                
            # 更新会变化的数据
            # 恒星时
            temp_data["sidereal_time"] = client.get_sidereal_time(device_num)
            
            # 赤经和赤纬
            temp_data["right_ascension"] = client.get_right_ascension(device_num)
            temp_data["declination"] = client.get_declination(device_num)
            
            # 高度角和方位角
            temp_data["altitude"] = client.get_altitude(device_num)
            temp_data["azimuth"] = client.get_azimuth(device_num)
            
            # 获取赤道坐标系统
            try:
                temp_data["equatorial_system"] = client.get_equatorial_system(device_num)
            except Exception as e:
                logger.error(f"获取赤道坐标系统失败: {str(e)}")
                self._safe_emit_error(f"获取赤道坐标系统失败: {str(e)}")
            
            # 获取状态
            try:
                temp_data["tracking"] = client.get_tracking(device_num)
            except Exception as e:
                logger.error(f"获取跟踪状态失败: {str(e)}")
                self._safe_emit_error(f"获取跟踪状态失败: {str(e)}")
                
            try:
                temp_data["slewing"] = client.get_slewing(device_num)
            except Exception as e:
                logger.error(f"获取转向状态失败: {str(e)}")
                self._safe_emit_error(f"获取转向状态失败: {str(e)}")
                
            # 获取client_extension
            with self._lock:
                client_ext = self.client_extension
                
            try:
                # 使用扩展类的安全方法获取停靠状态
                if client_ext:
                    temp_data["parked"] = client_ext.get_parked_safe(device_num)
                else:
                    # 如果扩展类不可用，使用原始方法
                    temp_data["parked"] = client.get_parked(device_num)
            except Exception as e:
                logger.error(f"获取停靠状态失败: {str(e)}")
                self._safe_emit_error(f"获取停靠状态失败: {str(e)}")
                
            # 获取是否在home位置
            try:
                # 使用扩展类的安全方法获取home状态
                if client_ext:
                    temp_data["at_home"] = client_ext.get_at_home_safe(device_num)
                else:
                    # 如果扩展类不可用，使用原始方法
                    temp_data["at_home"] = client.get_at_home(device_num)
            except Exception as e:
                logger.error(f"获取home状态失败: {str(e)}")
                self._safe_emit_error(f"获取home状态失败: {str(e)}")
            
            if self._stop_event.is_set() or not self.running:
                return

            # 获取支持的跟踪速率
            try:
                tracking_rates = client.get_supported_tracking_rates(device_num)
                logger.debug(f"获取到支持的跟踪速率: {tracking_rates}")
                # 发送支持的跟踪速率信号
                self._safe_emit_tracking_rates({"Value": tracking_rates})
            except Exception as e:
                logger.error(f"获取支持的跟踪速率失败: {str(e)}")
                self._safe_emit_error(f"获取支持的跟踪速率失败: {str(e)}")
                
            if self._stop_event.is_set() or not self.running:
                return
            
            # 获取当前跟踪速率
            try:
                # 使用扩展类的安全方法获取跟踪速率
                if client_ext:
                    tracking_rate_text = client_ext.get_tracking_rate_safe(device_num)
                    temp_data["tracking_rate"] = tracking_rate_text
                    logger.debug(f"使用安全方法获取到跟踪速率: {tracking_rate_text}")
                else:
                    # 如果扩展类不可用，尝试使用原始方法
                    tracking_rate_text = client.get_tracking_rate(device_num, as_text=True)
                    temp_data["tracking_rate"] = tracking_rate_text
            except Exception as e:
                logger.error(f"获取当前跟踪速率失败: {str(e)}")
                self._safe_emit_error(f"获取当前跟踪速率失败: {str(e)}")
                temp_data["tracking_rate"] = "Unknown"
                
            if self._stop_event.is_set() or not self.running:
                return
                
            # 获取站点位置信息
            try:
                # 获取站点纬度
                temp_data["site_latitude"] = client.get_site_latitude(device_num)
                logger.debug(f"获取赤道仪站点纬度: {temp_data['site_latitude']}")
                
                # 获取站点经度
                temp_data["site_longitude"] = client.get_site_longitude(device_num)
                logger.debug(f"获取赤道仪站点经度: {temp_data['site_longitude']}")
                
                # 获取站点海拔
                temp_data["site_elevation"] = client.get_site_elevation(device_num)
                logger.debug(f"获取赤道仪站点海拔: {temp_data['site_elevation']}")
            except Exception as e:
                logger.error(f"获取站点位置信息失败: {str(e)}")
                self._safe_emit_error(f"获取站点位置信息失败: {str(e)}")

            if self._stop_event.is_set() or not self.running:
                return
                
            # 更新内部数据字典
            with self._lock:
                # 更新内部状态数据
                for key, value in temp_data.items():
                    self.telescope_data[key] = value
                    
                # 创建一个副本发送到UI
                data_to_emit = self.telescope_data.copy()
                
            # 发送更新的数据信号
            self._safe_emit_data(data_to_emit)
            
        except Exception as e:
            logger.error(f"获取望远镜数据失败: {str(e)}")
            self._safe_emit_error(f"获取望远镜数据失败: {str(e)}") 