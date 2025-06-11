#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
旋转器数据更新线程
用于定期轮询旋转器状态并更新数据
"""

import logging
import time
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

# 设置日志
logger = logging.getLogger(__name__)

class RotatorUpdater(QThread):
    """
    旋转器数据更新线程
    轮询旋转器状态并发送数据更新信号
    """
    # 定义信号
    data_updated = pyqtSignal(dict)  # 数据更新信号
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, update_interval=1.0):
        """
        初始化旋转器数据更新线程
        
        参数:
            update_interval: 更新间隔（秒）
        """
        super().__init__()
        
        self.rotator_model = None
        self.update_interval = update_interval
        self.running = False
        
    def set_model(self, model):
        """
        设置旋转器模型
        
        参数:
            model: 旋转器模型实例
        """
        self.rotator_model = model
        
    def stop(self):
        """
        停止线程
        """
        self.running = False
        self.wait(1000)  # 等待线程结束，最多1秒
        
    def run(self):
        """
        线程主函数
        """
        if not self.rotator_model:
            self.error_occurred.emit("未设置旋转器模型")
            return
            
        self.running = True
        logger.info("旋转器数据更新线程已启动")
        
        # 位置更新频率降低计数器，用于较少位置查询频率
        position_update_counter = 0
        
        while self.running:
            try:
                # 如果旋转器未连接，减少查询频率
                if not self.rotator_model.connected:
                    time.sleep(1.0)
                    continue
                
                # 每次循环都更新位置信息，确保UI显示最新状态
                self.rotator_model.update_position()
                    
                # 收集设备数据
                rotator_data = {
                    "position": self.rotator_model.position,
                    "is_moving": self.rotator_model.is_moving,
                    "connected": self.rotator_model.connected,
                    "can_reverse": self.rotator_model.can_reverse,
                    "is_reversed": self.rotator_model.is_reversed,
                    "step_size": self.rotator_model.step_size,
                    "target_position": self.rotator_model.target_position,
                    "mechanical_position": self.rotator_model.mechanical_position,
                    "name": self.rotator_model.name,
                    "description": self.rotator_model.description
                }
                
                # 发送数据更新信号
                self.data_updated.emit(rotator_data)
                
                # 更新计数器
                position_update_counter += 1
                
                # 等待下一次更新 - 移动状态应该更快更新
                sleep_interval = min(self.update_interval, 0.2) if self.rotator_model.is_moving else self.update_interval
                time.sleep(sleep_interval)
                
                # 处理Qt事件，避免线程阻塞界面
                QApplication.processEvents()
                
            except Exception as e:
                logger.error(f"旋转器数据更新线程错误: {str(e)}")
                self.error_occurred.emit(f"旋转器数据更新错误: {str(e)}")
                time.sleep(2.0)  # 出错时增加延迟
                
        logger.info("旋转器数据更新线程已停止") 