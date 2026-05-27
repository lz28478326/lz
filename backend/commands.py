import paramiko
from config import DEFAULT_SERVERS, COMMON_COMMANDS

# 全局服务器字典
SERVERS = dict(DEFAULT_SERVERS)

def ssh_connect(server):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=server["host"],
        port=server.get("port", 22),
        username=server.get("username", "root"),
        password=server.get("password", ""),
        timeout=5
    )
    return ssh

def exec_cmd(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

def add_server(ip, password, username="root", port=22, name=None):
    server_id = "server-" + ip.replace(".", "-")
    if name is None:
        name = f"服务器 ({ip})"
    SERVERS[server_id] = {
        "host": ip,
        "port": port,
        "username": username,
        "password": password,
        "name": name
    }
    return server_id

def remove_server(server_id):
    if server_id in SERVERS:
        del SERVERS[server_id]
        return True
    return False

def get_remote_stats(server_id):
    server = SERVERS.get(server_id)
    if not server:
        return None
    try:
        ssh = ssh_connect(server)
        
        # CPU
        cpu_out, _ = exec_cmd(ssh, "top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}'")
        try:
            cpu = round(float(cpu_out), 1)
        except:
            cpu_out2, _ = exec_cmd(ssh, "vmstat 1 2 | tail -1 | awk '{print 100-$15}'")
            try:
                cpu = round(float(cpu_out2), 1)
            except:
                cpu = 0
        
        # 内存
        mem_out, _ = exec_cmd(ssh, "free | grep Mem | awk '{printf \"%.1f\", $3/$2*100}'")
        try:
            memory = round(float(mem_out), 1)
        except:
            memory = 0
        
        # 磁盘
        disk_out, _ = exec_cmd(ssh, "df -h / | tail -1 | awk '{print $5}' | sed 's/%//'")
        try:
            disk = round(float(disk_out), 1)
        except:
            disk = 0
        
        # 负载
        load_out, _ = exec_cmd(ssh, "uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//'")
        try:
            load = round(float(load_out), 2)
        except:
            load = 0
        
        # 运行时间
        uptime_out, _ = exec_cmd(ssh, "uptime -p | sed 's/up //'")
        
        ssh.close()
        return {
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "load": load,
            "uptime": uptime_out,
            "online": True
        }
    except Exception as e:
        return {
            "cpu": 0, "memory": 0, "disk": 0,
            "load": 0, "uptime": "N/A",
            "online": False, "error": str(e)
        }

def execute_remote(server_id, command):
    server = SERVERS.get(server_id)
    if not server:
        return {"error": "Server not found"}
    try:
        ssh = ssh_connect(server)
        out, err = exec_cmd(ssh, command)
        ssh.close()
        return {"stdout": out, "stderr": err, "server": server_id}
    except Exception as e:
        return {"error": str(e)}
