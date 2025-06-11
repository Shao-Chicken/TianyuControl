#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
电调焦工作线程模块
用于监控电调焦的移动状态
"""

import logging
import time
import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

# 设置日志
logger = logging.getLogger(__name__)

class FocuserMoveWorker(QThread):
    """
    电调焦移动监控线程
    监控电调焦的移动状态，直到移动完成
    """
    # 定义信号
    moving_changed = pyqtSignal(bool)  # 移动状态变化信号
    move_completed = pyqtSignal()  # 移动完成信号
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, focuser_driver=None, polling_interval=0.1):
        """
        初始化电调焦移动监控线程
        
        参数:
            focuser_driver: 电调焦驱动实例
            polling_interval: 轮询间隔（秒）
        """
        super().__init__()
        
        self.focuser_driver = focuser_driver
        self.polling_interval = polling_interval  # 轮询间隔
        self.running = False  # 运行标志
        self._last_position = None  # 上次位置，用于记录
        self._target_position = None  # 目标位置
        self._aborted = False  # 中止标志
        
    def set_driver(self, driver):
        """设置电调焦驱动"""
        self.focuser_driver = driver
        
    def set_target_position(self, position):
        """设置目标位置"""
        self._target_position = position
        
    def abort(self):
        """中止移动监控"""
        self._aborted = True
        # 设置移动状态为False（红灯），表示已停止移动
        self.moving_changed.emit(False)
        
        # 发送移动完成信号
        self.move_completed.emit()
        
        # 记录中止时间
        current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        logger.info(f"[{current_time}] 移动已被用户中止")
        
    def stop(self):
        """停止线程"""
        self.running = False
        self.wait(1000)  # 等待线程结束，最多1秒
        
    def run(self):
        """线程主函数"""
        if not self.focuser_driver:
            self.error_occurred.emit("电调焦驱动未设置")
            return
        
        if self._target_position is None:
            self.error_occurred.emit("未设置目标位置")
            return
            
        self.running = True
        self._aborted = False
        
        # 初始状态为移动中，发送移动状态变化信号
        self.moving_changed.emit(True)
        current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        logger.info(f"[{current_time}] 电调焦移动监控线程已启动")
        
        try:
            # 获取初始位置
            self._last_position = self.focuser_driver.get_position()
            
            # 记录开始时间和目标位置
            start_time = time.time()
            logger.info(f"[{current_time}] 监控电调焦移动：目标位置 = {self._target_position}, 初始位置 = {self._last_position}")
            
            # 判断移动方向
            moving_outward = self._target_position > self._last_position
            
            # 监控循环
            max_timeout = 600  # 最大60秒超时(600 * 0.1)
            timeout_counter = 0
            position_stable_counter = 0  # 添加位置稳定计数器
            stable_threshold = 5  # 位置稳定阈值，连续5次相同位置认为已停止
            last_stable_position = None  # 上次稳定位置
            
            while self.running and not self._aborted:
                # 处理Qt事件，避免UI冻结
                QApplication.processEvents()
                
                # 获取当前位置
                try:
                    current_position = self.focuser_driver.get_position()
                    
                    # 如果位置变化，记录日志
                    if current_position != self._last_position:
                        current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        logger.info(f"[{current_time}] 位置变化: {self._last_position} -> {current_position}")
                        self._last_position = current_position
                        # 重置稳定计数器
                        position_stable_counter = 0
                        last_stable_position = None
                    else:
                        # 相同位置，增加稳定计数
                        if last_stable_position is None:
                            last_stable_position = current_position
                            position_stable_counter = 1
                        elif current_position == last_stable_position:
                            position_stable_counter += 1
                        else:
                            last_stable_position = current_position
                            position_stable_counter = 1
                    
                    # 核心判断逻辑：根据移动方向判断是否到达目标位置
                    if moving_outward:
                        # 向外移动：当前位置 >= 目标位置时认为到达
                        reached_target = current_position >= self._target_position
                    else:
                        # 向内移动：当前位置 <= 目标位置时认为到达
                        reached_target = current_position <= self._target_position
                    
                    # 位置稳定判断：如果位置连续多次保持不变，也认为到达
                    position_stable = position_stable_counter >= stable_threshold
                        
                    if reached_target or position_stable:
                        current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        if reached_target:
                            logger.info(f"[{current_time}] 已到达目标位置: {self._target_position}，移动结束")
                        else:
                            logger.info(f"[{current_time}] 位置已稳定在 {current_position}，移动结束")
                        break
                    
                    # 超时检测
                    timeout_counter += 1
                    if timeout_counter >= max_timeout:
                        current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        logger.warning(f"[{current_time}] 电调焦移动监控超时，强制结束监控")
                        break
                        
                except Exception as e:
                    logger.error(f"获取电调焦状态失败: {str(e)}")
                    # 出现错误时不要立即退出，继续尝试
                
                # 等待下一次轮询
                time.sleep(self.polling_interval)
                
            # 如果是因为中止而退出循环
            if self._aborted:
                current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                logger.info(f"[{current_time}] 电调焦移动已中止")
                
            # 计算总运行时间
            total_time = time.time() - start_time
            current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            logger.info(f"[{current_time}] 电调焦移动监控完成，总运行时间: {total_time:.2f}秒")
            
            # 移动停止后发送移动状态变化信号
            self.moving_changed.emit(False)
            
            # 发送移动完成信号
            self.move_completed.emit()
            logger.info(f"[{current_time}] 电调焦移动完成")
            
        except Exception as e:
            logger.error(f"电调焦移动监控线程错误: {str(e)}")
            self.error_occurred.emit(f"电调焦移动监控错误: {str(e)}")
        
        self.running = False
        self._aborted = False 