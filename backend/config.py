import os
from cryptography.fernet import Fernet

ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key().decode()
cipher = Fernet(ENCRYPTION_KEY.encode())

def encrypt_password(p): return cipher.encrypt(p.encode()).decode()
def decrypt_password(e): return cipher.decrypt(e.encode()).decode()

DEFAULT_SERVERS = {}
COMMON_COMMANDS = {
    "系统状态": {"uptime":"查看运行时间","free -h":"查看内存","df -h":"查看磁盘"},
    "网络相关": {"ip addr":"查看IP","netstat -tlnp":"查看端口"},
    "服务管理": {"systemctl status ssh":"SSH状态","systemctl status nginx":"Nginx状态"},
    "Docker相关": {"docker ps":"运行容器","docker images":"镜像列表"},
    "日志查看": {"tail -30 /var/log/syslog":"系统日志","dmesg | tail -20":"内核日志"},
    "用户相关": {"who":"在线用户","last -10":"登录记录"},
}
COLLECT_INTERVAL = 2
