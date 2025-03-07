import yaml
import datetime

# 读取 YAML 配置
def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# 记录日志（修复 Unicode 问题）
def log_message(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"

    print(log_entry.strip())  # 终端输出

    with open("app.log", "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)
