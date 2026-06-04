"""系统指标采集器 — CPU / 内存 / 负载 / 温度 / 运行时间"""
from .base import BaseCollector


class SystemCollector(BaseCollector):
    """采集 CPU、内存、负载、温度等系统指标"""

    async def collect(self) -> dict:
        # 使用单次 SSH 会话批量获取
        script = r"""
cat /proc/stat
echo "---MEM---"
cat /proc/meminfo
echo "---LOAD---"
cat /proc/loadavg
echo "---UPTIME---"
cat /proc/uptime
echo "---TEMP---"
for f in /sys/class/thermal/thermal_zone*/temp; do
  echo "$(basename $(dirname $f)):$(cat $f 2>/dev/null)"
done
echo "---DISK---"
df / /overlay /tmp 2>/dev/null | tail -n +2
echo "---PROC---"
cat /proc/stat | grep '^cpu' 2>/dev/null
echo "---TOP_CPU---"
top -b -n1 2>/dev/null | tail -n +5 | head -15
"""
        raw = await self._run_cmd(script)
        return self._parse(raw)

    def _parse(self, raw: str) -> dict:
        result = {
            "cpu_percent": 0.0,
            "cpu_per_core": [],
            "load_1m": 0.0,
            "load_5m": 0.0,
            "load_15m": 0.0,
            "memory_total_mb": 0,
            "memory_used_mb": 0,
            "memory_available_mb": 0,
            "memory_percent": 0.0,
            "swap_total_mb": 0,
            "swap_used_mb": 0,
            "temperature_c": [],
            "uptime_seconds": 0,
            "disk_usage": [],
            "top_cpu": [],
            "top_mem": [],
        }

        lines = raw.split("\n")
        section = None
        cpu_lines = []

        for line in lines:
            line = line.strip()
            if line == "---MEM---":
                section = "mem"
                continue
            elif line == "---LOAD---":
                section = "load"
                continue
            elif line == "---UPTIME---":
                section = "uptime"
                continue
            elif line == "---TEMP---":
                section = "temp"
                continue
            elif line == "---DISK---":
                section = "disk"
                continue
            elif line == "---PROC---":
                section = "proc"
                continue
            elif line == "---TOP_CPU---":
                section = "top_cpu"
                continue
            elif line == "---TOP_MEM---":
                section = "top_mem"
                continue

            if section == "mem":
                if line.startswith("MemTotal:"):
                    total_kb = int(line.split()[1])
                    result["memory_total_mb"] = round(total_kb / 1024, 1)
                elif line.startswith("MemAvailable:"):
                    avail_kb = int(line.split()[1])
                    result["memory_available_mb"] = round(avail_kb / 1024, 1)
                    result["memory_used_mb"] = round(
                        (result["memory_total_mb"] * 1024 - avail_kb) / 1024, 1
                    )
                    if result["memory_total_mb"] > 0:
                        result["memory_percent"] = round(
                            (result["memory_total_mb"] - result["memory_available_mb"])
                            / result["memory_total_mb"] * 100, 1
                        )
                elif line.startswith("SwapTotal:"):
                    result["swap_total_mb"] = round(int(line.split()[1]) / 1024, 1)
                elif line.startswith("SwapFree:"):
                    free_kb = int(line.split()[1])
                    result["swap_used_mb"] = round(
                        result["swap_total_mb"] - free_kb / 1024, 1
                    )

            elif section == "load":
                parts = line.split()
                if len(parts) >= 3:
                    result["load_1m"] = float(parts[0])
                    result["load_5m"] = float(parts[1])
                    result["load_15m"] = float(parts[2])

            elif section == "uptime":
                parts = line.split()
                if parts:
                    result["uptime_seconds"] = int(float(parts[0]))

            elif section == "temp":
                if ":" in line:
                    parts = line.split(":")
                    temp_milli = parts[1].strip()
                    if temp_milli.isdigit():
                        result["temperature_c"].append({
                            "zone": parts[0],
                            "temp_c": round(int(temp_milli) / 1000, 1),
                        })

            elif section == "disk":
                parts = line.split()
                if len(parts) >= 6:
                    total = int(parts[1]) * 1024
                    used = int(parts[2]) * 1024
                    pct = parts[4].strip("%")
                    result["disk_usage"].append({
                        "mount": parts[5],
                        "total_gb": round(total / (1024**3), 1),
                        "used_gb": round(used / (1024**3), 1),
                        "percent": int(pct),
                    })

            elif section == "proc":
                if line.startswith("cpu"):
                    cpu_lines.append(line)

            elif section == "top_cpu":
                if line and not line.startswith("PID") and not line.startswith("Mem:") and not line.startswith("CPU:") and not line.startswith("Load"):
                    parts = line.split()
                    if len(parts) >= 8:
                        # top -b -n1 格式: PID PPID USER STAT VSZ %VSZ %CPU COMMAND
                        proc = {
                            "pid": parts[0],
                            "cpu": parts[6].rstrip("%"),
                            "mem": parts[5].rstrip("%"),
                            "name": " ".join(parts[7:]),
                        }
                        result.setdefault("top_cpu", []).append(proc)
                        result.setdefault("top_mem", []).append(proc)

        # CPU 使用率估算（对比 /proc/stat 两次调用更好，但这只是快照近似）
        # 用 idle 比例估算
        if len(cpu_lines) >= 1:
            parts = cpu_lines[0].split()
            if len(parts) >= 5:
                user, nice, sys, idle = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                total = user + nice + sys + idle + sum(int(x) for x in parts[5:8] if x.isdigit())
                if total > 0:
                    result["cpu_percent"] = round((1 - idle / total) * 100, 1)

            # 每核
            for cl in cpu_lines[1:]:
                parts = cl.split()
                if len(parts) >= 5:
                    u, n, s, i = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                    t = u + n + s + i + sum(int(x) for x in parts[5:8] if x.isdigit())
                    result["cpu_per_core"].append(
                        round((1 - i / t) * 100, 1) if t > 0 else 0
                    )

        # top_mem 按内存占用排序（取前15）
        if "top_mem" in result:
            result["top_mem"] = sorted(
                result["top_mem"],
                key=lambda p: float(p.get("mem", 0) or 0),
                reverse=True
            )[:15]

        return result
