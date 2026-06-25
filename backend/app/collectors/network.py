"""网络指标采集器 — 接口流量 / conntrack / TCP 状态"""

import ipaddress
import csv
import io
from collections import Counter, defaultdict

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
if command -v conntrack >/dev/null 2>&1; then
  timeout 5 conntrack -L -o extended 2>/dev/null | awk '{
    proto=$1
    for (i=1; i<=NF; i++) {
      if ($i=="tcp" || $i=="udp" || $i=="icmp" || $i=="icmpv6" || $i=="gre" || $i=="esp") {
        proto=$i
        break
      }
    }
    print proto
  }' | sort | uniq -c | sort -rn 2>/dev/null || true
fi
echo "---LOCAL_NETS---"
ip -4 addr show scope global 2>/dev/null | awk '
  /^[0-9]+:/ {
    iface=$2
    sub(/:$/, "", iface)
  }
  /^[[:space:]]*inet / {
    print iface "|" $2
  }
' || true
echo "---DHCP_HOSTS---"
cat /tmp/dhcp.leases 2>/dev/null | awk '{print $3 "|" $4 "|" toupper($2)}' || true
echo "---ARP_HOSTS---"
awk 'NR>1 && $4!="00:00:00:00:00:00" && $4!="(incomplete)" {print $1 "|" toupper($4) "|" $6}' /proc/net/arp 2>/dev/null || true
echo "---NLBW_RANK---"
if command -v nlbw >/dev/null 2>&1; then
  timeout 6 nlbw -c csv -g ip,mac -q 2>/dev/null | sed -n '1,240p' || true
fi
echo "---NLBW_LAYER7---"
if command -v nlbw >/dev/null 2>&1; then
  timeout 6 nlbw -c csv -g ip,mac,layer7 -q 2>/dev/null | sed -n '1,500p' || true
fi
echo "---CONNTRACK_CMD_FLOWS---"
if command -v conntrack >/dev/null 2>&1; then
  timeout 5 conntrack -L -o extended 2>/dev/null | sed -n '1,3000p' || true
fi
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
echo "---PUBLIC_IP---"
get_openwrt_iface_ip() {
  local logical="$1"
  local status=""

  status="$(ubus call network.interface."$logical" status 2>/dev/null || ifstatus "$logical" 2>/dev/null || true)"
  if [ -n "$status" ] && command -v jsonfilter >/dev/null 2>&1; then
    printf '%s\n' "$status" | jsonfilter -e '@["ipv4-address"][0].address' 2>/dev/null | head -n1
  elif [ -n "$status" ]; then
    printf '%s\n' "$status" | awk '
      /"ipv4-address"/ { in_ipv4=1; next }
      in_ipv4 && /"address"/ {
        gsub(/[",]/, "", $2)
        print $2
        exit
      }
    '
  fi
}

public_ip="$(get_openwrt_iface_ip wan)"
if [ -z "$public_ip" ]; then
  wan_dev="$(ip -4 route show default 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')"
  if [ -n "$wan_dev" ]; then
    public_ip="$(ip -4 addr show dev "$wan_dev" scope global 2>/dev/null | awk '/inet / {sub(/\/.*/, "", $2); print $2; exit}')"
  fi
fi
printf '%s\n' "$public_ip"
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
            "public_ip": "",
            "local_networks": [],
            "local_addresses": [],
            "traffic_rank": self._empty_traffic_rank(),
        }

        lines = raw.split("\n")
        section = None
        local_network_entries = []
        dhcp_hosts = {}
        arp_hosts = {}
        nlbw_rank_lines = []
        nlbw_layer7_lines = []
        conntrack_lines = []

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
            elif line == "---LOCAL_NETS---":
                section = "local_nets"
                continue
            elif line == "---DHCP_HOSTS---":
                section = "dhcp_hosts"
                continue
            elif line == "---ARP_HOSTS---":
                section = "arp_hosts"
                continue
            elif line == "---NLBW_RANK---":
                section = "nlbw_rank"
                continue
            elif line == "---NLBW_LAYER7---":
                section = "nlbw_layer7"
                continue
            elif line == "---CONNTRACK_CMD_FLOWS---":
                section = "conntrack_cmd_flows"
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
            elif line == "---PUBLIC_IP---":
                section = "public_ip"
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

            elif section == "local_nets":
                entry = self._parse_interface_network(line)
                if entry:
                    local_network_entries.append(entry)

            elif section == "dhcp_hosts":
                ip, hostname, mac = self._split_pipe(line, 3)
                if ip:
                    dhcp_hosts[ip] = {
                        "hostname": "" if hostname == "*" else hostname,
                        "mac": mac,
                    }

            elif section == "arp_hosts":
                ip, mac, iface = self._split_pipe(line, 3)
                if ip:
                    arp_hosts[ip] = {
                        "mac": mac,
                        "interface": iface,
                    }

            elif section == "nlbw_rank":
                if line:
                    nlbw_rank_lines.append(line)

            elif section == "nlbw_layer7":
                if line:
                    nlbw_layer7_lines.append(line)

            elif section == "conntrack_cmd_flows":
                if line:
                    conntrack_lines.append(line)

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

            elif section == "public_ip":
                if line and len(line) <= 64:
                    result["public_ip"] = line
                    section = None

        if result["conntrack_max"] > 0:
            result["conntrack_percent"] = round(
                result["conntrack_count"] / result["conntrack_max"] * 100, 1
            )

        client_network_entries = self._select_client_network_entries(local_network_entries)
        local_networks = [entry["network"] for entry in client_network_entries]
        local_addresses = {entry["address"] for entry in client_network_entries}
        result["local_networks"] = [str(network) for network in local_networks]
        result["local_addresses"] = sorted(local_addresses)
        result["traffic_rank"] = self._build_nlbw_traffic_rank(
            nlbw_rank_lines,
            nlbw_layer7_lines,
            local_networks,
            local_addresses,
            dhcp_hosts,
            arp_hosts,
        )
        if not result["traffic_rank"]["available"]:
            result["traffic_rank"] = self._build_conntrack_traffic_rank(
                conntrack_lines,
                local_networks,
                local_addresses,
                dhcp_hosts,
                arp_hosts,
            )

        return result

    def _empty_traffic_rank(self) -> dict:
        return {
            "available": False,
            "mode": "unavailable",
            "source": "unavailable",
            "sampled_flows": 0,
            "has_byte_counters": False,
            "items": [],
            "note": "未读取到 nlbwmon 或 conntrack 命令输出",
        }

    def _split_pipe(self, line: str, size: int) -> list[str]:
        parts = line.split("|")
        return (parts + [""] * size)[:size]

    def _parse_interface_network(self, value: str):
        iface = ""
        cidr = value
        if "|" in value:
            iface, cidr = self._split_pipe(value, 2)
        try:
            interface = ipaddress.ip_interface(cidr)
        except ValueError:
            return None
        network = interface.network
        if network.version != 4 or network.is_loopback:
            return None
        return {
            "interface": iface,
            "address": str(interface.ip),
            "network": network,
        }

    def _select_client_network_entries(self, entries: list[dict]) -> list:
        private_entries = [
            entry for entry in entries
            if entry["network"].is_private and not entry["network"].is_link_local
        ]
        lan_entries = [
            entry for entry in private_entries
            if self._looks_like_lan_interface(entry.get("interface", ""))
        ]
        if lan_entries:
            return lan_entries
        if private_entries:
            return private_entries
        return [
            entry for entry in entries
            if not entry["network"].is_link_local and entry["network"].prefixlen < 32
        ]

    def _looks_like_lan_interface(self, iface: str) -> bool:
        name = (iface or "").lower()
        return (
            name == "br-lan"
            or name == "lan"
            or name.startswith("lan")
            or ".lan" in name
            or name.startswith("br-guest")
            or name.startswith("guest")
        )

    def _is_local_ip(self, value: str, local_networks: list) -> bool:
        try:
            ip = ipaddress.ip_address(value)
        except ValueError:
            return False

        if ip.version != 4 or ip.is_loopback or ip.is_multicast or ip.is_unspecified:
            return False

        if local_networks:
            return any(ip in network for network in local_networks)

        # 兜底：老固件没有 ip 命令时，至少能识别常见私网客户端。
        return ip.is_private

    def _parse_conntrack_flow(self, line: str) -> dict:
        parts = line.split()
        proto = "other"
        for token in parts[:6]:
            lower = token.lower()
            if lower in {"tcp", "udp", "icmp", "icmpv6", "gre", "esp"}:
                proto = lower
                break

        values = {
            "src": [],
            "dst": [],
            "bytes": [],
            "packets": [],
        }
        for token in parts:
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            if key in values:
                values[key].append(value)

        return {
            "proto": proto,
            "src": values["src"],
            "dst": values["dst"],
            "bytes": [self._safe_int(v) for v in values["bytes"]],
            "packets": [self._safe_int(v) for v in values["packets"]],
        }

    def _safe_int(self, value) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _parse_table(self, lines: list[str]) -> list[dict]:
        text = "\n".join(line for line in lines if line.strip()).strip()
        if not text or "\n" not in text:
            return []

        sample = text[:2048]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters="\t,;")
        except csv.Error:
            dialect = csv.excel_tab

        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        return [row for row in reader if row]

    def _normalize_mac(self, value: str) -> str:
        mac = (value or "").strip().upper()
        return "" if mac == "00:00:00:00:00:00" else mac

    def _build_nlbw_traffic_rank(
        self,
        nlbw_rank_lines: list[str],
        nlbw_layer7_lines: list[str],
        local_networks: list,
        local_addresses: set[str],
        dhcp_hosts: dict,
        arp_hosts: dict,
    ) -> dict:
        rows = {}
        rank_rows = self._parse_table(nlbw_rank_lines)
        layer7_rows = self._parse_table(nlbw_layer7_lines)

        applications = defaultdict(Counter)
        protocols = defaultdict(Counter)
        for row in layer7_rows:
            ip = (row.get("ip") or "").strip()
            if not ip or ip in local_addresses or not self._is_local_ip(ip, local_networks):
                continue
            conns = self._safe_int(row.get("conns"))
            app = (row.get("layer7") or "").strip()
            proto = (row.get("proto") or "other").strip().lower() or "other"
            if app:
                applications[ip][app] += conns
            protocols[ip][proto] += conns

        for row in rank_rows:
            ip = (row.get("ip") or "").strip()
            if not ip or ip in local_addresses or not self._is_local_ip(ip, local_networks):
                continue

            dhcp = dhcp_hosts.get(ip, {})
            arp = arp_hosts.get(ip, {})
            mac = self._normalize_mac(row.get("mac")) or dhcp.get("mac") or arp.get("mac", "")
            download_bytes = self._safe_int(row.get("rx_bytes"))
            upload_bytes = self._safe_int(row.get("tx_bytes"))
            connections = self._safe_int(row.get("conns"))
            rx_packets = self._safe_int(row.get("rx_pkts"))
            tx_packets = self._safe_int(row.get("tx_pkts"))

            rows[ip] = {
                "ip": ip,
                "hostname": dhcp.get("hostname", ""),
                "mac": mac,
                "interface": arp.get("interface", ""),
                "download_bytes": download_bytes,
                "upload_bytes": upload_bytes,
                "total_bytes": download_bytes + upload_bytes,
                "connections": connections,
                "packets": rx_packets + tx_packets,
                "protocols": dict(protocols[ip].most_common()),
                "applications": dict(applications[ip].most_common(4)),
            }

        items = sorted(
            rows.values(),
            key=lambda item: (item["total_bytes"], item["connections"]),
            reverse=True,
        )

        if not items:
            rank = self._empty_traffic_rank()
            rank["source"] = "nlbwmon"
            rank["note"] = "nlbwmon 暂无可用排行数据"
            return rank

        normalized_items = []
        for item in items[:30]:
            normalized_items.append({
                **item,
                "score": item["total_bytes"],
            })

        return {
            "available": True,
            "mode": "bytes",
            "source": "nlbwmon",
            "sampled_flows": sum(item["connections"] for item in normalized_items),
            "has_byte_counters": True,
            "items": normalized_items,
            "note": "来自 nlbwmon 统计数据库，按累计流量排序",
        }

    def _build_conntrack_traffic_rank(
        self,
        conntrack_lines: list[str],
        local_networks: list,
        local_addresses: set[str],
        dhcp_hosts: dict,
        arp_hosts: dict,
    ) -> dict:
        rows = {}
        sampled_flows = 0
        has_byte_counters = False

        def ensure_row(ip: str) -> dict:
            if ip not in rows:
                dhcp = dhcp_hosts.get(ip, {})
                arp = arp_hosts.get(ip, {})
                rows[ip] = {
                    "ip": ip,
                    "hostname": dhcp.get("hostname", ""),
                    "mac": dhcp.get("mac") or arp.get("mac", ""),
                    "interface": arp.get("interface", ""),
                    "download_bytes": 0,
                    "upload_bytes": 0,
                    "total_bytes": 0,
                    "connections": 0,
                    "packets": 0,
                    "protocols": defaultdict(int),
                }
            return rows[ip]

        for line in conntrack_lines:
            flow = self._parse_conntrack_flow(line)
            src = flow["src"]
            dst = flow["dst"]
            bytes_values = flow["bytes"]
            packets_values = flow["packets"]
            if bytes_values:
                has_byte_counters = True

            original_src = src[0] if len(src) > 0 else ""
            original_dst = dst[0] if len(dst) > 0 else ""
            reply_src = src[1] if len(src) > 1 else ""
            reply_dst = dst[1] if len(dst) > 1 else ""

            client_ip = ""
            upload_bytes = 0
            download_bytes = 0

            if original_src and self._is_local_ip(original_src, local_networks):
                client_ip = original_src
                upload_bytes = bytes_values[0] if len(bytes_values) > 0 else 0
                download_bytes = bytes_values[1] if len(bytes_values) > 1 else 0
            elif original_dst and self._is_local_ip(original_dst, local_networks):
                client_ip = original_dst
                download_bytes = bytes_values[0] if len(bytes_values) > 0 else 0
                upload_bytes = bytes_values[1] if len(bytes_values) > 1 else 0
            elif reply_dst and self._is_local_ip(reply_dst, local_networks):
                client_ip = reply_dst
                upload_bytes = bytes_values[0] if len(bytes_values) > 0 else 0
                download_bytes = bytes_values[1] if len(bytes_values) > 1 else 0
            elif reply_src and self._is_local_ip(reply_src, local_networks):
                client_ip = reply_src
                download_bytes = bytes_values[0] if len(bytes_values) > 0 else 0
                upload_bytes = bytes_values[1] if len(bytes_values) > 1 else 0

            if not client_ip:
                continue
            if client_ip in local_addresses:
                continue

            sampled_flows += 1
            row = ensure_row(client_ip)
            row["download_bytes"] += download_bytes
            row["upload_bytes"] += upload_bytes
            row["total_bytes"] += download_bytes + upload_bytes
            row["connections"] += 1
            row["packets"] += sum(packets_values[:2])
            row["protocols"][flow["proto"]] += 1

        items = list(rows.values())
        mode = "bytes" if has_byte_counters else "connections"
        items.sort(
            key=lambda item: (
                item["total_bytes"] if mode == "bytes" else item["connections"],
                item["connections"],
            ),
            reverse=True,
        )

        normalized_items = []
        for item in items[:20]:
            score = item["total_bytes"] if mode == "bytes" else item["connections"]
            normalized_items.append({
                **item,
                "protocols": dict(sorted(
                    item["protocols"].items(),
                    key=lambda entry: entry[1],
                    reverse=True,
                )),
                "score": score,
            })

        if not normalized_items:
            rank = self._empty_traffic_rank()
            rank["sampled_flows"] = sampled_flows
            rank["has_byte_counters"] = has_byte_counters
            return rank

        return {
            "available": True,
            "mode": mode,
            "source": "conntrack-command",
            "sampled_flows": sampled_flows,
            "has_byte_counters": has_byte_counters,
            "items": normalized_items,
            "note": "来自 conntrack 命令输出，按实时字节统计排序" if mode == "bytes" else "conntrack 命令未暴露字节计数，已按活跃连接数排序",
        }
