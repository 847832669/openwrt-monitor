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

## 二、本地 Docker Compose

```bash
git clone https://github.com/847832669/openwrt-monitor.git
cd openwrt-monitor

docker compose up -d
```

访问：

```text
http://你的内网IP:8000
```

## 三、直接运行已发布镜像

```bash
docker run -d \
  --name openwrt-monitor \
  --restart unless-stopped \
  -p 8000:8000 \
  -v openwrt-monitor-data:/app/data \
  ghcr.io/847832669/openwrt-monitor:latest
```

## 四、Unraid 上拉取运行

```bash
docker pull ghcr.io/847832669/openwrt-monitor:latest

docker run -d \
  --name openwrt-monitor \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /mnt/user/appdata/openwrt-monitor/data:/app/data \
  ghcr.io/847832669/openwrt-monitor:latest
```

## 五、手动打包测试

```bash
# 在项目根目录执行
docker build -t openwrt-monitor:local .

docker run --rm -p 8000:8000 \
  -v openwrt-monitor-data:/app/data \
  openwrt-monitor:local
```
