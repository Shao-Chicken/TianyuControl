import time
import re
from typing import Dict, Tuple, Union
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from src.services.astronomy_service import astronomy_service

class DSSImageFetcher(QThread):
    """DSS图像获取线程"""
    image_ready = pyqtSignal(str)  # 发送图像路径
    
    def __init__(self):
        super().__init__()
        self.ra = None
        self.dec = None
        self.running = True
        self.coord_threshold = 0.5  # 坐标变化阈值（度）
        self.cache = {}  # 坐标到图像路径的缓存
        
    def _get_cache_key(self, ra, dec):
        """获取缓存键（将坐标四舍五入到阈值精度）"""
        ra_rounded = round(ra / self.coord_threshold) * self.coord_threshold
        dec_rounded = round(dec / self.coord_threshold) * self.coord_threshold
        return (ra_rounded, dec_rounded)
        
    def set_coordinates(self, ra, dec):
        """设置要获取的坐标"""
        self.ra = ra
        self.dec = dec
        if not self.isRunning():
            self.start()
            
    def stop(self):
        """停止线程"""
        self.running = False
        
    def run(self):
        """线程主循环"""
        while self.running:
            if self.ra is not None and self.dec is not None:
                try:
                    # 获取DSS图像
                    image_path = astronomy_service.get_dss_image(self.ra, self.dec)
                    if image_path:
                        # 发送图像路径
                        self.image_ready.emit(image_path)
                        
                        # 清除坐标，等待下一次更新
                        self.ra = None
                        self.dec = None
                    
                except Exception as e:
                    print(f"获取DSS图像失败: {e}")
                    self.ra = None
                    self.dec = None
            
            # 休眠一段时间
            self.msleep(100)  # 100毫秒 