from PyQt5.QtCore import QThread, pyqtSignal
from api_client import AlpacaClient
from utils import load_config, log_message
import time
import requests

class TelescopeMonitor(QThread):
    """设备监控线程"""
    # 定义信号
    coordinates_updated = pyqtSignal(float, float, float, float)  # 赤经、赤纬、高度角、方位角
    status_updated = pyqtSignal(dict)  # 望远镜状态信号
    devices_updated = pyqtSignal(list)  # 设备列表更新信号
    focuser_updated = pyqtSignal(dict)  # 电调焦状态信号
    rotator_updated = pyqtSignal(dict)  # 消旋器状态信号
    weather_updated = pyqtSignal(dict)  # 气象站数据信号
    
    def __init__(self, device_number=0, device_type='telescope'):
        super().__init__()
        config = load_config()
        device_config = config.get("devices", {}).get(device_type, {})
        api_url = device_config.get("api_url")
        self.client = AlpacaClient(base_url=api_url)
        self.device_number = device_number
        self.device_type = device_type
        self.is_running = True
        self.is_connected = False
        self.update_interval = 0.05  # 更新间隔50毫秒
        self.device_scan_interval = 2  # 未连接时每2秒扫描一次设备列表
        self.last_device_scan = 0
        
    def set_device(self, device_number, device_type=None):
        """设置设备编号和类型"""
        self.device_number = device_number
        if device_type:
            self.device_type = device_type
        self.is_connected = True
        
    def disconnect_device(self):
        """断开设备连接"""
        self.is_connected = False
        self.device_number = 0
        
    def stop(self):
        """停止线程"""
        self.is_running = False
        
    def run(self):
        """线程运行方法"""
        config = load_config()
        
        # 定义不同设备类型的端点
        endpoints = {
            'telescope': {
                'coordinate': ['rightascension', 'declination', 'altitude', 'azimuth'],
                'status': ['athome', 'atpark', 'ispulseguiding', 'slewing', 'tracking']
            },
            'focuser': {
                'status': ['position', 'ismoving', 'temperature', 'maxstep']
            },
            'rotator': {
                'status': ['position', 'ismoving', 'reverse', 'stepsize', 'targetposition']
            },
            'ObservingConditions': {
                'status': [
                    'cloudcover', 'dewpoint', 'humidity', 'pressure', 'rainrate',
                    'skybrightness', 'skytemperature', 'starfwhm', 'temperature',
                    'winddirection', 'windspeed', 'windgust'
                ]
            }
        }
        
        # 主循环
        while self.is_running:
            try:
                # 只在未连接状态下扫描设备列表
                if not self.is_connected:
                    current_time = time.time()
                    if current_time - self.last_device_scan >= self.device_scan_interval:
                        devices = self.client.find_devices(device_type=self.device_type)
                        if devices:
                            self.devices_updated.emit(devices)
                        self.last_device_scan = current_time
                        time.sleep(self.device_scan_interval)  # 未连接时降低扫描频率
                        continue  # 跳过数据获取
                
                # 根据设备类型获取相应的数据
                if self.device_type == 'telescope':
                    # 获取望远镜数据
                    results = self.client.get_multiple('telescope', self.device_number,
                                                    endpoints['telescope']['coordinate'] +
                                                    endpoints['telescope']['status'])
                    
                    # 获取坐标值
                    ra = results.get('rightascension')
                    dec = results.get('declination')
                    alt = results.get('altitude')
                    az = results.get('azimuth')
                    
                    # 获取状态值
                    status = {
                        'athome': results.get('athome', False),
                        'atpark': results.get('atpark', False),
                        'ispulseguiding': results.get('ispulseguiding', False),
                        'slewing': results.get('slewing', False),
                        'tracking': results.get('tracking', False)
                    }
                    
                    # 如果坐标数据获取成功，发送坐标信号
                    if all(x is not None for x in [ra, dec, alt, az]):
                        self.coordinates_updated.emit(ra, dec, alt, az)
                    
                    # 发送状态信号
                    self.status_updated.emit(status)
                    
                elif self.device_type == 'focuser':
                    # 获取电调焦数据
                    results = self.client.get_multiple('focuser', self.device_number,
                                                    endpoints['focuser']['status'])
                    
                    # 获取状态值
                    status = {
                        'position': results.get('position', 0),
                        'ismoving': results.get('ismoving', False),
                        'temperature': results.get('temperature', 0.0),
                        'maxstep': results.get('maxstep', 60000)
                    }
                    
                    # 发送电调焦状态信号
                    self.focuser_updated.emit(status)
                    
                elif self.device_type == 'rotator':
                    # 获取消旋器数据
                    results = self.client.get_multiple('rotator', self.device_number,
                                                    endpoints['rotator']['status'])
                    
                    # 获取状态值
                    status = {
                        'position': results.get('position', 0),
                        'ismoving': results.get('ismoving', False),
                        'reverse': results.get('reverse', False),
                        'stepsize': results.get('stepsize', 1.0),
                        'targetposition': results.get('targetposition', 0)
                    }
                    
                    # 发送消旋器状态信号
                    self.rotator_updated.emit(status)
                    
                elif self.device_type == 'observingconditions':
                    try:
                        # 从配置中获取气象站端点
                        config = load_config()
                        endpoints_list = config.get("devices", {}).get("ObservingConditions", {}).get("endpoints", [])
                        
                        # 记录请求的端点
                        # log_message(f"正在请求气象站数据，端点列表: {endpoints_list}")
                        
                        # 使用正确的 API URL
                        base_url = config.get("devices", {}).get("ObservingConditions", {}).get("api_url")
                        if not base_url:
                            base_url = "http://202.127.24.217:11111"  # 默认 URL
                        
                        # 获取所有气象站数据
                        results = {}
                        
                        # 遍历查询每个属性
                        for prop in endpoints_list:
                            try:
                                # 构造完整的URL
                                url = f"{base_url}/api/v1/observingconditions/{self.device_number}/{prop}?ClientID={config.get('client_id', 1)}&ClientTransactionID={config.get('transaction_id', 1)}"
                                response = requests.get(url, timeout=5)
                                response.raise_for_status()
                                data = response.json()
                                
                                if data.get("ErrorNumber", 0) != 0:
                                    error_number = data.get("ErrorNumber")
                                    error_message = data.get("ErrorMessage", "Unknown error")
                                    # log_message(f"获取气象站数据 '{prop}' 失败: [ErrorNumber={error_number}] {error_message}")
                                else:
                                    value = data.get("Value", None)
                                    results[prop] = value
                                    # log_message(f"气象站数据 '{prop}' = {value}")
                            except (requests.exceptions.RequestException, ValueError) as e:
                                # log_message(f"获取气象站数据 '{prop}' 失败: {e}")
                                continue
                        
                        # 详细记录气象站数据到日志
                        # log_message(f"气象站数据获取完成，共 {len(results)} 项")
                        
                        # 发送气象站数据信号
                        if results:
                            # print("\n气象站数据更新:")
                            # for key, value in results.items():
                            #     print(f"  {key}: {value}")
                            self.weather_updated.emit(results)
                    except Exception as e:
                        # log_message(f"获取气象站数据失败: {e}")
                        pass
            except Exception as e:
                # print(f"获取设备数据失败: {e}")
                # log_message(f"获取设备数据失败: {e}")
                time.sleep(0.5)  # 发生错误时等待0.5秒再重试
                continue
                
            # 线程休眠
            time.sleep(self.update_interval) 