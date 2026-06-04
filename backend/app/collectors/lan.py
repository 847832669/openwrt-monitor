"""局域网设备采集器 — DHCP 租约 / ARP 表"""
from datetime import datetime, timezone
from .base import BaseCollector


def _parse_lease_expiry(ts_secs: str) -> tuple[str, bool]:
    """解析租约到期时间，返回 (剩余时间字符串, 是否过期)"""
    try:
        expiry = int(ts_secs)
        now = datetime.now(timezone.utc).timestamp()
        remain = expiry - now
        if remain <= 0:
            return "已过期", True
        if remain < 3600:
            mins = int(remain / 60)
            return f"{mins}分钟", False
        if remain < 86400:
            hours = int(remain / 3600)
            mins = int((remain % 3600) / 60)
            return f"{hours}小时{mins}分钟", False
        days = int(remain / 86400)
        return f"{days}天", False
    except (ValueError, TypeError):
        return "永久", False


class LANCollector(BaseCollector):
    """采集局域网内连接设备信息"""

    async def collect(self) -> dict:
        script = r"""
echo "---DHCP_LEASES---"
cat /tmp/dhcp.leases 2>/dev/null || echo ""
echo "---ARP---"
cat /proc/net/arp 2>/dev/null || echo ""
echo "---HOSTNAME---"
cat /proc/sys/kernel/hostname 2>/dev/null || echo "openwrt"
"""
        raw = await self._run_cmd(script)
        return self._parse(raw)

    def _parse(self, raw: str) -> dict:
        result = {
            "leases": [],
            "arp": [],
            "online_count": 0,
            "total_count": 0,
            "router_hostname": "openwrt",
        }

        lines = raw.split("\n")
        section = None

        for line in lines:
            line = line.strip()
            if line == "---DHCP_LEASES---":
                section = "dhcp"
                continue
            elif line == "---ARP---":
                section = "arp"
                continue
            elif line == "---HOSTNAME---":
                section = "hostname"
                continue

            if section == "hostname" and line:
                result["router_hostname"] = line
                section = None

            elif section == "dhcp" and line:
                parts = line.split()
                if len(parts) >= 4:
                    expiry_str, mac, ip, hostname = parts[0], parts[1], parts[2], parts[3]
                    remain_text, expired = _parse_lease_expiry(expiry_str)
                    result["leases"].append({
                        "mac": mac.upper(),
                        "ip": ip,
                        "hostname": hostname if hostname != "*" else "",
                        "expiry": expiry_str,
                        "remain": remain_text,
                        "expired": expired,
                    })

            elif section == "arp" and line and not line.startswith("IP address"):
                parts = line.split()
                if len(parts) >= 4:
                    ip = parts[0]
                    hw_type = parts[1]
                    flags = parts[2]
                    mac = parts[3]
                    # flags: 0x2 = 在线, 0x0 = 未解析
                    online = flags == "0x2"
                    if mac and mac != "(incomplete)":
                        result["arp"].append({
                            "ip": ip,
                            "mac": mac.upper(),
                            "online": online,
                            "device": parts[5] if len(parts) > 5 else "",
                        })

        # 合并：用 ARP 状态标记 DHCP 设备是否在线
        arp_by_ip = {a["ip"]: a for a in result["arp"]}
        arp_by_mac = {a["mac"]: a for a in result["arp"]}

        online_ips = set(a["ip"] for a in result["arp"] if a["online"])

        for lease in result["leases"]:
            # 先按 MAC 找 ARP，再按 IP 找
            arp_entry = arp_by_mac.get(lease["mac"]) or arp_by_ip.get(lease["ip"])
            lease["online"] = bool(arp_entry and arp_entry["online"]) or lease["ip"] in online_ips

        result["total_count"] = len(result["leases"])

        # 在线设备 = 在线 ARP 条目（去重）+ DHCP 中标记为在线的
        online_leases = sum(1 for l in result["leases"] if l["online"])
        online_arp = sum(1 for a in result["arp"] if a["online"])
        result["online_count"] = max(online_leases, online_arp)

        return result
