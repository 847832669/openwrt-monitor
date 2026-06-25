# 🚀 部署指南

## 一、自动发布 Docker 镜像到 ghcr.io

项目已配置 GitHub Actions。推送到 `main` 或推送 `v*` 标签时，会自动构建并推送镜像：

```text
ghcr.io/847832669/openwrt-monitor:latest
ghcr.io/847832669/openwrt-monitor:<tag 或 sha>
```

镜像使用根目录 `Dockerfile` 多阶段构建：

1. Node 阶段构建 Vue 前端
2. Python 阶段安装 FastAPI 后端依赖
3. 把前端静态文件复制到后端静态目录
4. 最终一个容器提供前端、API 和 WebSocket

## 二、发布新版本

本地修改完成并提交后，在 `main` 分支执行：

```bash
scripts/release.sh 0.4.1 "简短描述本次发布内容"
```

脚本会自动完成：

- 同步更新 `frontend/package.json`、`frontend/package-lock.json` 和 `backend/app/config.py` 的版本号
- 在 `CHANGELOG.md` 顶部添加版本记录
- 创建 `Release vX.Y.Z` 提交和 `vX.Y.Z` 标签
- 推送 `main` 和标签到 GitHub

推送标签后会触发 Docker 镜像构建，并自动创建 GitHub Release。

## 三、本地 Docker Compose

```bash
git clone https://github.com/847832669/openwrt-monitor.git
cd openwrt-monitor

# 首次部署前建议先修改 docker-compose.yml 中的：
# OWM_SECRET_KEY / OWM_ADMIN_USERNAME / OWM_ADMIN_PASSWORD

docker compose up -d
```

访问：

```text
http://你的内网IP:8000
```

默认管理员账号是 `admin` / `admin`。生产环境请务必设置：

```env
OWM_SECRET_KEY=请改成足够长的随机字符串
OWM_ADMIN_USERNAME=admin
OWM_ADMIN_PASSWORD=请改成你的管理员密码
OWM_HISTORY_RETENTION_DAYS=7
```

`OWM_SECRET_KEY` 同时用于登录 JWT 和设备 SSH 密码加密；修改密钥后，旧密钥加密的密码无法再解密，需要重新录入设备密码。

本地开发可临时设置 `OWM_AUTH_DISABLED=true` 跳过登录，生产环境不要启用。

## 四、直接运行已发布镜像

```bash
docker run -d \
  --name openwrt-monitor \
  --restart unless-stopped \
  -p 8000:8000 \
  -v openwrt-monitor-data:/app/data \
  -e OWM_SECRET_KEY="请改成足够长的随机字符串" \
  -e OWM_ADMIN_PASSWORD="请改成你的管理员密码" \
  ghcr.io/847832669/openwrt-monitor:latest
```

## 五、Unraid 上拉取运行

```bash
docker pull ghcr.io/847832669/openwrt-monitor:latest

docker run -d \
  --name openwrt-monitor \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /mnt/user/appdata/openwrt-monitor/data:/app/data \
  -e OWM_SECRET_KEY="请改成足够长的随机字符串" \
  -e OWM_ADMIN_PASSWORD="请改成你的管理员密码" \
  ghcr.io/847832669/openwrt-monitor:latest
```

Unraid 模板中也提供了 `OWM_SECRET_KEY`、`OWM_ADMIN_USERNAME`、`OWM_ADMIN_PASSWORD`、`OWM_HISTORY_RETENTION_DAYS` 和 `OWM_AUTH_DISABLED` 变量。

## 六、手动打包测试

```bash
# 在项目根目录执行
docker build -t openwrt-monitor:local .

docker run --rm -p 8000:8000 \
  -v openwrt-monitor-data:/app/data \
  -e OWM_SECRET_KEY="dev-secret-change-me" \
  -e OWM_ADMIN_PASSWORD="admin" \
  openwrt-monitor:local
```

## 七、备份恢复与维护

登录后进入 **系统设置**：

- **导出配置 JSON**：包含设备配置、LAN 设备画像、识别规则、OUI 覆盖、告警规则和维护设置。
- **导入配置 JSON**：导入前会校验版本和基础格式；导入后下一轮采集会刷新识别结果。
- **导出数据库备份**：直接下载 SQLite 数据库文件。
- **历史数据保留**：支持 3 / 7 / 14 / 30 天，并可手动立即清理过期 `metric_history` 和 `traffic_history`。

配置 JSON 会包含设备 SSH 密码明文，请只保存到可信位置。
