"""
主程序入口
"""
import sys
import os

# 将项目根目录添加到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.ui.main_window import MainWindow
from device_manager import Telescope, Focuser, Rotator, ObservingConditions

def connect_and_get_device(device_manager):
    """连接设备并返回设备信息"""
    if device_manager.connect():
        return device_manager.device
    return None

def search_telescope():
    """搜索 Alpaca 望远镜和电调焦设备"""
    all_devices = []
    
    # 搜索望远镜设备
    print("\n正在搜索 Alpaca 设备...")
    telescope = Telescope()
    if telescope.connect():
        all_devices.append(telescope.device)
        print("✓ 望远镜设备已连接")
    
    # 搜索电调焦设备
    focuser = Focuser()
    if focuser.connect():
        all_devices.append(focuser.device)
        print("✓ 电调焦设备已连接")
    
    # 搜索消旋器设备
    rotator = Rotator()
    if rotator.connect():
        all_devices.append(rotator.device)
        print("✓ 消旋器设备已连接")
    
    # 搜索气象站设备
    weather = ObservingConditions()
    if weather.connect():
        # 确保气象站设备信息包含所有必要字段
        weather_device = {
            'DeviceName': weather.device.get('DeviceName', 'ASCOM Observing Conditions Simulator'),
            'DeviceType': 'ObservingConditions',
            'DeviceNumber': weather.device.get('DeviceNumber', 0),
            'ApiVersion': weather.device.get('ApiVersion', '1.0')
        }
        all_devices.append(weather_device)
        print("✓ 气象站设备已连接")
    
    print("\n开始启动主程序...\n")
    return all_devices

def main():
    # 首先搜索设备
    devices = search_telescope()
    
    # 设置高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 创建主窗口，并传入设备列表
    window = MainWindow(telescope_devices=devices)
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 