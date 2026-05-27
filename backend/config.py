import os

# 预置服务器列表（可通过界面动态添加）
DEFAULT_SERVERS = {}

# 命令分类库
COMMON_COMMANDS = {
    "📊 系统状态": {
        "uptime": "查看系统运行时间/负载",
        "top -bn1 | head -5": "查看资源占用概况",
        "free -h": "查看内存使用情况",
        "df -h": "查看磁盘使用情况",
        "ps aux --sort=-%cpu | head -8": "CPU占用TOP进程",
        "uname -a": "查看系统版本信息",
    },
    "🌐 网络相关": {
        "ip addr": "查看网络配置",
        "netstat -tlnp": "查看监听端口",
        "ss -tlnp": "查看监听端口(ss)",
        "ping -c 3 baidu.com": "测试网络连通性",
        "curl -I http://localhost": "测试本地HTTP服务",
    },
    "🔧 服务管理": {
        "systemctl status ssh": "SSH服务状态",
        "systemctl status nginx": "Nginx状态",
        "systemctl restart nginx": "重启Nginx",
        "systemctl status mysql": "MySQL状态",
        "systemctl status docker": "Docker状态",
        "systemctl list-units --type=service --state=running | head -15": "运行中的服务",
    },
    "🐳 Docker相关": {
        "docker ps": "查看运行中的容器",
        "docker ps -a": "查看所有容器",
        "docker images": "查看镜像列表",
        "docker stats --no-stream": "容器资源占用",
        "docker logs --tail 20 $(docker ps -q | head -1)": "最新容器日志",
    },
    "📁 文件与磁盘": {
        "df -h": "磁盘使用情况",
        "du -sh /* 2>/dev/null | sort -rh | head -10": "根目录占用排名",
        "lsblk": "查看块设备",
        "ls -la /var/log": "查看日志目录",
    },
    "📜 日志查看": {
        "tail -30 /var/log/syslog": "系统日志(30行)",
        "tail -30 /var/log/nginx/error.log": "Nginx错误日志",
        "dmesg | tail -20": "内核日志",
        "journalctl -xe --no-pager | tail -20": "journal日志",
    },
    "👤 用户相关": {
        "who": "查看在线用户",
        "w": "查看用户活动",
        "last -10": "最近登录记录",
        "cat /etc/passwd | tail -10": "用户列表",
    },
    "🔄 系统操作": {
        "reboot": "⚠️ 重启系统",
        "shutdown -h now": "⚠️ 关机",
        "crontab -l": "查看定时任务",
    }
}

# 数据采集间隔（秒）
COLLECT_INTERVAL = 2

# 默认告警阈值
DEFAULT_CPU_THRESHOLD = 80
DEFAULT_MEM_THRESHOLD = 85
DEFAULT_DISK_THRESHOLD = 90
