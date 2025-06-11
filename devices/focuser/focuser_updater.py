#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
电调焦数据更新线程
周期性获取电调焦数据并更新模型
"""

import logging
import time
from typing import Dict, Any, Optional
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

# 设置日志
logger = logging.getLogger(__name__)

class FocuserUpdater(QThread):
    """
    电调焦数据更新线程
    周期性获取电调焦数据并更新模型
    """
    # 定义信号
    data_updated = pyqtSignal(dict)  # 数据更新信号
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, update_interval: float = 1.0):
        """
        初始化电调焦数据更新线程
        
        参数:
            update_interval: 更新间隔（秒）
        """
        super(FocuserUpdater, self).__init__()
        
        self.update_interval = update_interval
        self.focuser_model = None  # 将在外部设置
        self.running = False  # 运行标志
        self.connected = False  # 连接状态
        
    def set_model(self, model):
        """
        设置电调焦模型
        
        参数:
            model: 电调焦模型实例
        """
        self.focuser_model = model
        
        # 连接信号
        if self.focuser_model:
            self.focuser_model.connected_changed.connect(self.handle_connected_changed)
            
    def handle_connected_changed(self, connected: bool):
        """
        处理连接状态变化
        
        参数:
            connected: 是否已连接
        """
        self.connected = connected
        
        # 如果已连接且未运行，则开始运行
        if connected and not self.running and not self.isRunning():
            self.start()
        elif not connected and self.running:
            self.stop()
            
    def run(self):
        """
        线程主函数
        """
        self.running = True
        logger.info("电调焦数据更新线程已启动")
        
        # 计时器，用于控制不同属性的更新频率
        position_update_counter = 0  # 位置更新计数器
        
        while self.running:
            try:
                # 如果已连接且模型有效
                if self.connected and self.focuser_model:
                    # 确保连接仍然有效
                    if not self.focuser_model.connected:
                        logger.warning("电调焦连接已断开，但更新线程仍在运行")
                        time.sleep(2.0)
                        continue
                        
                    try:
                        # 获取移动状态 - 每次循环都更新，确保UI反应灵敏
                        self.focuser_model.update_position()
                    except Exception as e:
                        logger.error(f"更新位置信息失败: {str(e)}")
                    
                    # 温度信息每3次循环更新一次(温度变化较慢)
                    if position_update_counter % 3 == 0:
                        try:
                            # 更新温度信息
                            self.focuser_model.update_temperature()
                        except Exception as e:
                            logger.error(f"更新温度信息失败: {str(e)}")
                    
                    try:
                        # 收集设备数据
                        focuser_data = {
                            "position": self.focuser_model.position,
                            "is_moving": self.focuser_model.is_moving,
                            "temperature": self.focuser_model.temperature,
                            "temp_comp": self.focuser_model.temp_comp if hasattr(self.focuser_model, "temp_comp") else False,
                            "absolute": self.focuser_model.absolute if hasattr(self.focuser_model, "absolute") else False,
                            "connected": self.focuser_model.connected
                        }
                        
                        # 发送数据更新信号
                        self.data_updated.emit(focuser_data)
                    except Exception as e:
                        logger.error(f"发送数据更新信号失败: {str(e)}")
                    
                    # 更新计数器
                    position_update_counter += 1
                    
                # 等待下一次更新 - 移动状态应该更快更新
                sleep_interval = min(self.update_interval, 0.2)  # 最快200ms更新一次
                time.sleep(sleep_interval)
                
                # 处理Qt事件，避免线程阻塞界面
                QApplication.processEvents()
                
            except Exception as e:
                logger.error(f"电调焦数据更新线程错误: {str(e)}")
                self.error_occurred.emit(f"电调焦数据更新错误: {str(e)}")
                time.sleep(2.0)  # 出错时增加延迟
                
        logger.info("电调焦数据更新线程已停止")
            
    def stop(self):
        """
        停止线程
        """
        self.running = False
        
        # 等待线程完成
        if self.isRunning():
            self.wait(2000)  # 最多等待2秒 