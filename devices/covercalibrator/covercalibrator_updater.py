#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
镜头盖/校准器数据更新器
定期从ASCOM Alpaca设备获取状态更新
"""

import logging
import time
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QMutex

# 设置日志
logger = logging.getLogger(__name__)

class CoverCalibratorUpdater(QThread):
    """
    镜头盖/校准器数据更新器，定期从ASCOM Alpaca设备获取状态更新
    """
    # 定义信号
    data_updated = pyqtSignal(dict)  # 数据更新信号
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, update_interval=1.0, parent=None):
        """
        初始化更新线程
        :param update_interval: 更新间隔（秒）
        :param parent: 父对象
        """
        super(CoverCalibratorUpdater, self).__init__(parent)
        
        # 设置线程名称和属性
        self.setObjectName("CoverCalibratorUpdater")
        
        # 设置更新间隔
        self.update_interval = update_interval
        
        # 设置线程运行标志
        self._running = False
        self._mutex = QMutex()
        
        # 设备模型引用
        self._model = None
    
    def set_model(self, model):
        """
        设置设备模型
        :param model: CoverCalibratorModel实例
        """
        self._model = model
    
    def run(self):
        """
        线程主函数
        """
        if self._model is None:
            self.error_occurred.emit("未设置设备模型")
            return
        
        # 设置运行标志
        self._mutex.lock()
        self._running = True
        self._mutex.unlock()
        
        while self._running:
            # 更新数据
            self.update_data()
            
            # 等待指定时间
            self.msleep(int(self.update_interval * 1000))
    
    def update_data(self):
        """更新设备数据"""
        if not self._model or not hasattr(self._model, "update_device_state"):
            return
            
        try:
            # 调用模型的更新方法
            try:
                self._model.update_device_state()
            except Exception as update_error:
                logger.warning(f"更新设备状态时出错: {str(update_error)}")
            
            # 获取更新后的数据（即使update_device_state失败，也尝试获取数据）
            data = {}
            
            # 逐个尝试获取属性，避免一个属性错误影响全部
            try:
                data["connected"] = self._model.connected
            except Exception:
                data["connected"] = False
            
            try:
                data["cover_state"] = self._model.cover_state
            except Exception:
                data["cover_state"] = "Unknown"
            
            try:
                data["cover_moving"] = self._model.cover_moving
            except Exception:
                data["cover_moving"] = False
            
            try:
                data["calibrator_state"] = self._model.calibrator_state
            except Exception:
                data["calibrator_state"] = "Unknown"
            
            try:
                data["calibrator_changing"] = self._model.calibrator_changing
            except Exception:
                data["calibrator_changing"] = False
            
            try:
                data["brightness"] = self._model.brightness
            except Exception:
                data["brightness"] = 0
            
            try:
                data["max_brightness"] = self._model.max_brightness
            except Exception:
                data["max_brightness"] = 100
            
            try:
                data["cover_present"] = self._model.cover_present
            except Exception:
                data["cover_present"] = False
            
            try:
                data["calibrator_present"] = self._model.calibrator_present
            except Exception:
                data["calibrator_present"] = False
            
            # 发送数据更新信号
            self.data_updated.emit(data)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            logger.error(f"更新镜头盖/校准器数据失败: {str(e)}")
    
    def stop(self):
        """
        停止线程
        """
        # 设置运行标志
        self._mutex.lock()
        self._running = False
        self._mutex.unlock()
        
        # 等待线程结束
        if self.isRunning():
            self.wait(1000)
            
            # 如果线程仍在运行，强制终止
            if self.isRunning():
                self.terminate()
                logger.warning("强制终止镜头盖/校准器数据更新线程") 