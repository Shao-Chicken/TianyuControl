import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils import load_config, log_message
import concurrent.futures
import time

class AlpacaClient:
    """ 处理 Alpaca API 交互 """
    def __init__(self, base_url=None):
        config = load_config()
        self.base_url = base_url if base_url else config.get("default_api_base_url")
        self.client_id = int(config["client_id"])
        self.transaction_id = int(config["transaction_id"])
        
        # 配置会话
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=5,  # 最多重试5次
            backoff_factor=0.5,  # 增加重试间隔
            status_forcelist=[500, 502, 503, 504]  # 这些HTTP状态码会触发重试
        )
        
        # 配置适配器
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.timeout = (2, 5)  # 连接超时2秒，读取超时5秒

    def get(self, device_type, device_number, endpoint):
        """ 发送 GET 请求到指定设备类型和端点 """
        url = f"{self.base_url}/api/v1/{device_type}/{device_number}/{endpoint}"
        params = {"ClientID": self.client_id, "ClientTransactionID": self.transaction_id}

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            if data["ErrorNumber"] == 0:
                return data["Value"]
            else:
                log_message(f"API 失败: {data['ErrorMessage']}")
                return None
        except requests.exceptions.RequestException as e:
            log_message(f"连接 API 失败: {e}")
            return None

    def get_multiple(self, device_type, device_number, endpoints):
        """ 并行获取多个端点的数据 """
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                endpoint: executor.submit(self.get, device_type, device_number, endpoint)
                for endpoint in endpoints
            }
            
            results = {}
            for endpoint, future in futures.items():
                try:
                    results[endpoint] = future.result(timeout=10)  # 设置更长的总超时时间
                except Exception as e:
                    log_message(f"获取 {endpoint} 数据失败: {e}")
                    results[endpoint] = None
                    
            return results

    def find_devices(self, device_type=None):
        """ 获取可用的 Alpaca 设备 """
        url = f"{self.base_url}/management/v1/configureddevices"
        print(f"正在请求 Alpaca 设备列表: {url}")  # 调试信息
        log_message(f"尝试从 {url} 获取设备列表...")
        
        try:
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    print(f"尝试连接 (尝试 {retry_count + 1}/{max_retries})...")
                    response = requests.get(url, timeout=10)  # 增加超时时间到10秒
                    print(f"API 响应状态码: {response.status_code}")  # 调试信息
                    response.raise_for_status()
                    
                    data = response.json()
                    print(f"获取到的设备数据: {data}")  # 调试信息
                    log_message(f"成功获取设备列表: {data}")
                    
                    if "Value" in data and isinstance(data["Value"], list):
                        devices = data["Value"]
                        if device_type:
                            devices = [device for device in devices if device["DeviceType"].lower() == device_type.lower()]
                        print(f"过滤后的设备列表 ({device_type}): {devices}")  # 调试信息
                        return devices
                    else:
                        print("未发现可用设备！数据格式不正确")  # 调试信息
                        log_message("未发现可用设备！数据格式不正确")
                        return []
                
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    print(f"连接失败 ({retry_count}/{max_retries}): {e}")
                    log_message(f"连接失败 ({retry_count}/{max_retries}): {e}")
                    if retry_count >= max_retries:
                        break
                    time.sleep(2)  # 等待2秒后重试
            
            print(f"连接服务器失败，已达到最大重试次数: {max_retries}")
            log_message(f"连接服务器失败，已达到最大重试次数: {max_retries}")
            return []
            
        except Exception as e:
            print(f"未知错误: {e}")
            log_message(f"未知错误: {e}")
            return []
        
    def get_ra_dec(self):
        """ 获取赤经和赤纬 """
        results = self.get_multiple('telescope', 0, ['rightascension', 'declination'])
        return results.get('rightascension'), results.get('declination')