"""采集器基类 + SSH 连接管理"""
import os
import asyncio
import asyncssh
from typing import Optional
from asyncio import Lock


class SSHClientPool:
    """SSH 连接池（每个 host 一个连接，复用）"""

    def __init__(self):
        self._connections: dict[str, asyncssh.SSHClientConnection] = {}
        self._lock = Lock()

    async def connect(
        self,
        host: str,
        port: int = 22,
        username: str = "root",
        auth_type: str = "key",
        private_key_path: str = "",
        password: str = "",
    ) -> asyncssh.SSHClientConnection:
        key = f"{username}@{host}:{port}"
        if key in self._connections:
            conn = self._connections[key]
            if conn.is_closed():
                del self._connections[key]
            else:
                return conn

        kwargs = {
            "host": host,
            "port": port,
            "username": username,
            "known_hosts": None,
            "connect_timeout": 10,
        }
        if auth_type == "key" and private_key_path:
            kwargs["client_keys"] = [os.path.expanduser(private_key_path)]
        elif auth_type == "password" and password:
            kwargs["password"] = password

        conn = await asyncssh.connect(**kwargs)
        self._connections[key] = conn
        return conn

    async def close(self, host: str, port: int = 22, username: str = "root"):
        key = f"{username}@{host}:{port}"
        if key in self._connections:
            self._connections[key].close()
            del self._connections[key]

    async def close_all(self):
        for key, conn in self._connections.items():
            conn.close()
        self._connections.clear()


ssh_pool = SSHClientPool()


class BaseCollector:
    """采集器基类"""

    def __init__(self, device_id: int, host: str, port: int = 22,
                 username: str = "root", auth_type: str = "key",
                 private_key_path: str = "", password: str = ""):
        self.device_id = device_id
        self.host = host
        self.port = port
        self.username = username
        self.auth_type = auth_type
        self.private_key_path = private_key_path
        self.password = password

    async def _run_cmd(self, cmd: str) -> str:
        """在设备上执行 shell 命令"""
        conn = await ssh_pool.connect(
            self.host, self.port, self.username,
            self.auth_type, self.private_key_path, self.password,
        )
        process = await conn.create_process(cmd)
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15)
        exit_code = process.returncode
        if exit_code != 0:
            raise RuntimeError(f"Command failed [{exit_code}]: {cmd}\n{stderr}")
        return stdout

    async def collect(self) -> dict:
        """子类实现：采集并返回指标字典"""
        raise NotImplementedError
