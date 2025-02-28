"""
设备管理服务模块
"""
from src.config.settings import DEVICES, SERIAL_PORTS

class DeviceService:
    def __init__(self):
        self.devices = {
            device[0]: {
                'name': device[1],
                'port': None,
                'connected': False,
                'status': 'disconnected'
            } for device in DEVICES
        }
        self.available_ports = SERIAL_PORTS

    def connect_device(self, device_id, port):
        """连接设备"""
        if device_id in self.devices:
            # TODO: 实现实际的设备连接逻辑
            self.devices[device_id]['port'] = port
            self.devices[device_id]['connected'] = True
            self.devices[device_id]['status'] = 'connected'
            return True
        return False

    def disconnect_device(self, device_id):
        """断开设备连接"""
        if device_id in self.devices:
            # TODO: 实现实际的设备断开逻辑
            self.devices[device_id]['port'] = None
            self.devices[device_id]['connected'] = False
            self.devices[device_id]['status'] = 'disconnected'
            return True
        return False

    def get_device_status(self, device_id):
        """获取设备状态"""
        return self.devices.get(device_id, {})

    def get_all_devices(self):
        """获取所有设备信息"""
        return self.devices

    def get_available_ports(self):
        """获取可用串口列表"""
        return self.available_ports

    def update_device_status(self, device_id, status):
        """更新设备状态"""
        if device_id in self.devices:
            self.devices[device_id]['status'] = status
            return True
        return False

# 创建全局实例
device_service = DeviceService() 