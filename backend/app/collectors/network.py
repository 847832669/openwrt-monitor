"""网络指标采集器 — 接口流量 / conntrack / TCP 状态"""
from .base import BaseCollector


class NetworkCollector(BaseCollector):
    """采集网络接口流量、连接跟踪等指标"""

    async def collect(self) -> dict:
        script = r"""
echo "---NET_DEV---"
cat /proc/net/dev 2>/dev/null
echo "---CONNTRACK---"
cat /proc/sys/net/netfilter/nf_conntrack_count 2>/dev/null || echo "0"
echo "---NF_CONNTRACK---"
cat /proc/sys/net/netfilter/nf_conntrack_max 2>/dev/null || echo "65535"
echo "---CONNTRACK_DETAIL---"
cat /proc/net/nf_conntrack 2>/dev/null | awk '{print $1}' | sort | uniq -c | sort -rn 2>/dev/null || true
echo "---TCP_STATES---"
# 从 /proc/net/tcp 读取 TCP 状态（无需 ss 命令）
cat /proc/net/tcp 2>/dev/null | tail -n +2 | awk '{
  state=$4;
  if(state=="01") print "ESTAB";
  else if(state=="02") print "SYN-SENT";
  else if(state=="03") print "SYN-RECV";
  else if(state=="04") print "FIN-WAIT-1";
  else if(state=="05") print "FIN-WAIT-2";
  else if(state=="06") print "TIME-WAIT";
  else if(state=="07") print "CLOSE";
  else if(state=="08") print "CLOSE-WAIT";
  else if(state=="09") print "LAST-ACK";
  else if(state=="0A") print "LISTEN";
  else if(state=="0B") print "CLOSING";
  else print "UNKNOWN";
}' | sort | uniq -c | sort -rn 2>/dev/null || true
echo "---WIFI_IFACES---"
iwinfo 2>/dev/null | grep -E '^[a-z0-9]+' | awk '{print $1}' | sort -u || true
"""
        raw = await self._run_cmd(script)
        return self._parse(raw)

    def _parse(self, raw: str) -> dict:
        result = {
            "interfaces": {},
            "conntrack_count": 0,
            "conntrack_max": 0,
            "conntrack_percent": 0.0,
            "tcp_states": {},
            "conntrack_protocols": {},
        }

        lines = raw.split("\n")
        section = None

        for line in lines:
            line = line.strip()
            if line == "---NET_DEV---":
                section = "netdev"
                continue
            elif line == "---CONNTRACK---":
                section = "conntrack"
                continue
            elif line == "---CONNTRACK_DETAIL---":
                section = "conntrack_detail"
                continue
            elif line == "---TCP_STATES---":
                section = "tcp"
                continue
            elif line == "---NF_CONNTRACK---":
                section = "nf"
                continue
            elif line == "---WIFI_IFACES---":
                section = "wifi"
                continue

            if section == "netdev":
                if ":" in line and not line.startswith("Inter-") and not line.startswith("face"):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        # 跳过 lo
                        if name == "lo":
                            continue
                        stats = parts[1].split()
                        if len(stats) >= 9:
                            result["interfaces"][name] = {
                                "rx_bytes": int(stats[0]),
                                "rx_packets": int(stats[1]),
                                "rx_errors": int(stats[2]),
                                "rx_dropped": int(stats[3]),
                                "tx_bytes": int(stats[8]),
                                "tx_packets": int(stats[9]),
                                "tx_errors": int(stats[10]),
                                "tx_dropped": int(stats[11]),
                            }

            elif section == "conntrack":
                if line and line != "0":
                    result["conntrack_count"] = int(line)

            elif section == "conntrack_detail":
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        proto = parts[1].strip()
                        count = int(parts[0])
                        # proto 可能是 "tcp" "udp" "icmp" 等
                        result["conntrack_protocols"][proto] = count

            elif section == "tcp":
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        state = parts[1].strip()
                        count = int(parts[0])
                        result["tcp_states"][state] = count

            elif section == "nf":
                if line and line != "N/A" and line.isdigit():
                    result["conntrack_max"] = int(line)

        if result["conntrack_max"] > 0:
            result["conntrack_percent"] = round(
                result["conntrack_count"] / result["conntrack_max"] * 100, 1
            )

        return result
