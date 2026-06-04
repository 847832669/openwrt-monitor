# 🚀 OpenWrt Monitor

> **OpenWrt 性能监控可视化平台** — 部署在局域网内，通过 SSH 采集 OpenWrt 路由器性能数据，提供实时、多维度的可视化监控。

---

## ✨ 功能特性

| 模块 | 内容 |
|:-----|:-----|
| 📊 **仪表盘** | CPU / 内存 / 温度 / 磁盘 / 负载 / 连接跟踪 / 实时流量曲线 |
| 📈 **系统分析** | CPU 每核使用率趋势、内存分布面积图、进程 TOP 排行 |
| 🌐 **网络分析** | 全接口列表、上下行总量、丢包统计、连接协议分布饼图、TCP 状态分布 |
| 🖥️ **连接设备** | DHCP 租约列表、ARP 在线探测、搜索过滤、设备备注 |
| ⚙️ **设备管理** | 添加/删除 OpenWrt 设备（SSH 密码或密钥认证） |

### 交互特性
- 🔄 **WebSocket 实时推送**，数据毫秒级到达浏览器
- ⏱ **采集间隔可调** — 1s / 3s / 5s / 10s 自由切换
- 🔁 **单位切换** — b/s ↔ B/s，比特与字节一键互换
- 🌙 **暗色主题** — 专业监控面板风格
- 🖥️ **响应式布局** — PC / 平板 / 手机均可使用

## 🧱 技术栈

```
┌─────────────────────────────────────┐
│  Vue 3 + ECharts + TailwindCSS      │  ← 前端
├─────────────────────────────────────┤
│  FastAPI + asyncssh + SQLAlchemy     │  ← 后端
├─────────────────────────────────────┤
│  WebSocket 实时推送                   │  ← 通信
├─────────────────────────────────────┤
│  SSH ↔ OpenWrt (Unraid VM)          │  ← 采集
└─────────────────────────────────────┘
```

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
git clone https://github.com/847832669/openwrt-monitor.git
cd openwrt-monitor

# 把 SSH 密钥放到 ./ssh-keys/ 目录下（如果用密码认证则跳过）

docker compose up -d
```

浏览器打开 `http://你内网IP:8000` 即可访问。

### 方式二：开发模式

**后端：**
```bash
cd backend
pip install -r requirements.txt
mkdir -p data
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**
```bash
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:3000`（热更新）或 `http://localhost:8000`（生产模式）。

## 🖥️ Unraid 图形化安装（推荐）

### 方法一：Docker Compose Manager 插件

1. **Apps** → 安装 **Docker Compose Manager** 插件
2. 打开 **Docker Compose Manager** → **Add New Stack**
3. 填：
   ```
   Name: openwrt-monitor
   Path to Stack File: /mnt/user/appdata/openwrt-monitor/docker-compose.yml
   ```
4. **Create Stack** 完成 🎉

### 方法二：Docker 模板（原生 UI）

1. **Docker** → **Settings** → **Template Repositories**
2. 在输入框粘贴：
   ```
   https://raw.githubusercontent.com/847832669/openwrt-monitor/main/unraid-template.xml
   ```
3. 点 **Add** → **Apply**
4. 回到 **Docker** → **Add Container**
5. **Template** 下拉选择 **OpenWrtMonitor**
6. **Apply** 完成 🎉

> 或者手动添加：
> - 仓库: `ghcr.io/847832669/openwrt-monitor:latest`
> - 端口: `8000`
> - 路径: `/mnt/user/appdata/openwrt-monitor/data/` → `/app/data`

安装后打开 `http://你的UnraidIP:8000` 即可使用。

## 📖 使用指南

1. 打开网页 → **设备管理** → 添加你的 OpenWrt 路由器
2. 填入 IP（如 `192.168.0.1`）、端口、用户名、密码或 SSH 密钥
3. 回到 **仪表盘** → 选择设备 → 实时数据开始跳动！
4. 进入 **连接设备** → 查看家里所有联网设备，支持备注名称
5. 进入 **系统分析** → 监控 CPU 每核趋势和进程排行

## 📊 采集指标

| 类别 | 指标 |
|:-----|:-----|
| 🖥️ 系统 | CPU 使用率、每核负载、内存、磁盘、运行时间、进程 TOP |
| 🌐 网络 | 10 接口流量、conntrack 连接跟踪、TCP 状态、协议分布 |
| 🖥️ 在线设备 | DHCP 租约、ARP 表、在线/离线状态 |

## 📁 项目结构

```
openwrt-monitor/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 主入口
│   │   ├── config.py             # 配置
│   │   ├── database.py           # SQLite 数据库
│   │   ├── models.py             # ORM 模型
│   │   ├── schemas.py            # Pydantic 数据模型
│   │   ├── collectors/
│   │   │   ├── base.py           # SSH 连接池基类
│   │   │   ├── system.py         # 系统指标采集
│   │   │   ├── network.py        # 网络指标采集
│   │   │   ├── lan.py            # 局域网设备采集
│   │   │   └── scheduler.py      # 定时调度器
│   │   └── routers/
│   │       ├── devices.py        # 设备管理 API
│   │       ├── metrics.py        # 指标数据 API
│   │       ├── ws.py             # WebSocket 推送
│   │       └── settings.py       # 系统设置 API
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.vue               # 主布局 + 侧边导航
│   │   ├── router/
│   │   ├── views/
│   │   │   ├── Dashboard.vue     # 仪表盘
│   │   │   ├── SystemAnalysis.vue # 系统分析
│   │   │   ├── Network.vue       # 网络分析
│   │   │   ├── LanDevices.vue    # 连接设备
│   │   │   └── Devices.vue       # 设备管理
│   │   ├── components/
│   │   │   ├── MetricCard.vue    # 指标卡片
│   │   │   └── TrafficChart.vue  # 流量曲线
│   │   └── composables/
│   │       ├── useApi.js         # HTTP API 封装
│   │       └── useWebSocket.js   # WebSocket 连接
│   ├── Dockerfile
│   └── package.json
├── docs/
│   └── REQUIREMENTS.md
├── docker-compose.yml
└── README.md
```

## ⚙️ 采集间隔配置

仪表盘左上角下拉菜单可选：
- **1s** — 极速模式，适合调试时观察实时变化
- **3s** — 默认，均衡性能与实时性
- **5s** — 省资源模式
- **10s** — 最低采集频率

## 🤖 关于本项目

> **整个项目由 AI 全程生成。**  
> 从需求分析、架构设计、代码编写、到部署运维，全部由 AI 助手（爱莉 💕）在与用户的对话交互中逐步完成。  
> 用户仅提供需求方向、OpenWrt 设备信息和功能反馈。

## 📄 许可证

MIT License
