from api_client import AlpacaClient
from utils import load_config, log_message

class DeviceManager:
    """管理天文设备的基类"""
    def __init__(self, device_type):
        self.device_type = device_type
        self.config = load_config()
        self.device_config = self.config["devices"][device_type]
        
        self.api_url = self.device_config.get("api_url", self.config.get("default_api_base_url"))
        self.client = AlpacaClient(base_url=self.api_url)
        
        self.device = None
        self.device_number = 0
        self.enabled = self.device_config["enabled"]
        self.endpoints = self.device_config["endpoints"]

    def connect(self):
        """搜索并连接可用设备"""
        if not self.enabled:
            log_message(f"{self.device_type.capitalize()} 设备已禁用，跳过连接")
            return False

        devices = self.client.find_devices(self.device_type)
        if not devices:
            log_message(f"没有发现可用的 {self.device_type} 设备！")
            return False

        self.device = devices[0]  # 选择第一个
        self.device_number = self.device['DeviceNumber']
        log_message(f"已连接 {self.device_type}: {self.device['DeviceName']} (编号: {self.device_number})")
        return True

    def get_data(self):
        """获取设备数据"""
        if not self.enabled:
            return {}
            
        if not self.device:
            log_message(f"{self.device_type} 设备未连接，无法获取数据！")
            return {}

        results = {}
        for endpoint in self.endpoints:
            results[endpoint] = self.client.get(self.device_type, self.device_number, endpoint)

        log_message(f"{self.device_type.capitalize()} 数据:")
        for key, value in results.items():
            log_message(f"{key.capitalize()}: {value}")
        
        return results


class Telescope(DeviceManager):
    def __init__(self):
        super().__init__("telescope")

class Focuser(DeviceManager):
    def __init__(self):
        super().__init__("focuser")

class Rotator(DeviceManager):
    def __init__(self):
        super().__init__("rotator")

class ObservingConditions(DeviceManager):
    def __init__(self):
        super().__init__("ObservingConditions")


