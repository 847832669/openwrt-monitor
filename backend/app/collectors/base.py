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
        self._connecting: dict[str, asyncio.Task] = {}
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
        async with self._lock:
            conn = self._connections.get(key)
            if conn and not conn.is_closed():
                return conn
            if conn and conn.is_closed():
                del self._connections[key]

            task = self._connecting.get(key)
            if not task:
                task = asyncio.create_task(self._connect_new(
                    host=host,
                    port=port,
                    username=username,
                    auth_type=auth_type,
                    private_key_path=private_key_path,
                    password=password,
                ))
                self._connecting[key] = task

        try:
            conn = await task
        except Exception:
            async with self._lock:
                if self._connecting.get(key) is task:
                    del self._connecting[key]
            raise

        async with self._lock:
            if self._connecting.get(key) is task:
                del self._connecting[key]
            if conn.is_closed():
                raise RuntimeError(f"SSH connection closed immediately: {key}")
            self._connections[key] = conn
            return conn

    async def _connect_new(
        self,
        host: str,
        port: int,
        username: str,
        auth_type: str,
        private_key_path: str,
        password: str,
    ) -> asyncssh.SSHClientConnection:
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

        return await asyncio.wait_for(asyncssh.connect(**kwargs), timeout=15)

    async def close(self, host: str, port: int = 22, username: str = "root"):
        key = f"{username}@{host}:{port}"
        if key in self._connections:
            conn = self._connections[key]
            conn.close()
            await conn.wait_closed()
            del self._connections[key]

    async def close_all(self):
        connections = list(self._connections.values())
        self._connections.clear()
        for task in self._connecting.values():
            task.cancel()
        self._connecting.clear()
        for conn in connections:
            conn.close()
        if connections:
            await asyncio.gather(
                *(conn.wait_closed() for conn in connections),
                return_exceptions=True,
            )


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
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15)
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.wait_closed()
            raise TimeoutError(f"Command timed out: {cmd[:120]}") from exc
        exit_code = process.returncode
        if exit_code != 0:
            raise RuntimeError(f"Command failed [{exit_code}]: {cmd}\n{stderr}")
        return stdout

    async def collect(self) -> dict:
        """子类实现：采集并返回指标字典"""
        raise NotImplementedError
