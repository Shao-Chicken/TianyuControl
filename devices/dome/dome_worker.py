#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import logging
import time
from PyQt5.QtCore import QObject, pyqtSignal

# 设置日志
logger = logging.getLogger(__name__)

class DomeWorker(QObject):
    """
    圆顶操作工作线程类
    
    用于在后台线程中执行可能阻塞的圆顶操作，避免阻塞主UI线程
    """
    
    # 定义信号
    operation_completed = pyqtSignal(bool, str)  # 操作完成信号: 成功状态, 消息
    shutter_status_changed = pyqtSignal(int)     # 天窗状态变化信号: 状态码
    slewing_changed = pyqtSignal(bool)  # 转向状态变化信号: 是否正在转向

    def __init__(self, dome_model):
        """初始化工作线程"""
        super(DomeWorker, self).__init__()
        self.dome_model = dome_model
        self.is_running = False
        self.current_thread = None
    
    def open_shutter(self):
        """开始打开天窗操作的线程"""
        if self.is_running:
            logger.warning("已有圆顶操作正在执行，忽略此次操作")
            return False
            
        self.is_running = True
        self.current_thread = threading.Thread(target=self._open_shutter_worker)
        self.current_thread.daemon = True
        self.current_thread.start()
        return True
        
    def close_shutter(self):
        """开始关闭天窗操作的线程"""
        if self.is_running:
            logger.warning("已有圆顶操作正在执行，忽略此次操作")
            return False
            
        self.is_running = True
        self.current_thread = threading.Thread(target=self._close_shutter_worker)
        self.current_thread.daemon = True
        self.current_thread.start()
        return True
        
    def _open_shutter_worker(self):
        """工作线程中执行打开天窗操作"""
        try:
            logger.info("开始打开天窗操作 (工作线程)")
            
            # 立即发送正在打开状态 (2)
            self.shutter_status_changed.emit(2)
            
            # 执行打开操作
            self.dome_model.open_shutter()
            
            # 操作后检查状态
            try:
                time.sleep(0.5)  # 短暂延时确保状态已更新
                shutter_status = self.dome_model.driver.get_shutter_status()
                logger.info(f"打开天窗后获取到的状态: {shutter_status}")
                self.shutter_status_changed.emit(shutter_status)
            except Exception as e:
                logger.error(f"获取打开天窗后的状态失败: {str(e)}")
                
            # 发送操作完成信号
            self.operation_completed.emit(True, "天窗打开操作已完成")
            
        except Exception as e:
            logger.error(f"打开天窗操作失败: {str(e)}")
            self.operation_completed.emit(False, f"打开天窗失败: {str(e)}")
        finally:
            self.is_running = False
            
    def _close_shutter_worker(self):
        """工作线程中执行关闭天窗操作"""
        try:
            logger.info("开始关闭天窗操作 (工作线程)")
            
            # 立即发送正在关闭状态 (3)
            self.shutter_status_changed.emit(3)
            
            # 执行关闭操作
            self.dome_model.close_shutter()
            
            # 操作后检查状态
            try:
                time.sleep(0.5)  # 短暂延时确保状态已更新
                shutter_status = self.dome_model.driver.get_shutter_status()
                logger.info(f"关闭天窗后获取到的状态: {shutter_status}")
                self.shutter_status_changed.emit(shutter_status)
            except Exception as e:
                logger.error(f"获取关闭天窗后的状态失败: {str(e)}")
                
            # 发送操作完成信号
            self.operation_completed.emit(True, "天窗关闭操作已完成")
            
        except Exception as e:
            logger.error(f"关闭天窗操作失败: {str(e)}")
            self.operation_completed.emit(False, f"关闭天窗失败: {str(e)}")
        finally:
            self.is_running = False

    def slew_to_azimuth(self, target_azimuth):
        """开始转向指定方位角的线程"""
        if self.is_running:
            logger.warning("已有圆顶操作正在执行，忽略此次操作")
            return False

        self.is_running = True
        self.current_thread = threading.Thread(target=self._slew_to_azimuth_worker, args=(target_azimuth,))
        self.current_thread.daemon = True
        self.current_thread.start()
        return True

    def _slew_to_azimuth_worker(self, target_azimuth):
        """工作线程中执行转向操作"""
        try:
            logger.info(f"开始转向方位角 {target_azimuth}° (工作线程)")
            
            # 立即发送正在转向状态
            self.slewing_changed.emit(True)
            
            try:
                # 执行转向操作
                logger.info("即将调用dome_model.slew_to_azimuth方法")
                self.dome_model.slew_to_azimuth(target_azimuth)
                logger.info("dome_model.slew_to_azimuth方法调用完成，等待转向过程结束...")
                
                # 等待转向完成 - 不使用固定时间，而是实际监测状态
                # 先等待一小段时间确保转向开始
                time.sleep(1)
                
                # 等待转向真正结束
                max_wait_time = 30  # 最长等待30秒
                wait_start_time = time.time()
                
                while time.time() - wait_start_time < max_wait_time:
                    try:
                        # 检查真实转向状态
                        if not self.dome_model.driver.is_slewing():
                            # 转向已完成
                            logger.info("检测到转向已完成")
                            break
                    except Exception as e:
                        logger.debug(f"检查转向状态时出现错误: {str(e)}")
                    
                    # 继续等待
                    time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"转向操作过程中出错: {str(e)}")
                self.operation_completed.emit(False, f"转向失败: {str(e)}")
                return
                
            # 发送操作完成信号
            self.operation_completed.emit(True, f"转向到方位角 {target_azimuth}° 操作已完成")
                
        except Exception as e:
            logger.error(f"转向工作线程出错: {str(e)}")
            self.operation_completed.emit(False, f"转向出错: {str(e)}")
        finally:
            # 确保在整个转向过程真正结束后才将状态设为false
            # 添加一小段延迟，确保其他状态更新已完成
            time.sleep(0.2)
            self.slewing_changed.emit(False)
            self.is_running = False

    def is_busy(self):
        """检查是否有操作正在执行"""
        return self.is_running