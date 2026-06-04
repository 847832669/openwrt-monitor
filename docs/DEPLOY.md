# 🚀 部署指南

## 一、手动发布 Docker 镜像到 ghcr.io

```bash
# 1. 生成 GitHub Token（需 repo + write:packages 权限）
# 2. 登录 ghcr.io
echo "你的TOKEN" | docker login ghcr.io -u 847832669 --password-stdin

# 3. 构建镜像
cd backend
docker build -t openwrt-monitor .

# 4. 打标签并推送
docker tag openwrt-monitor:latest ghcr.io/847832669/openwrt-monitor:latest
docker push ghcr.io/847832669/openwrt-monitor:latest
```

## 二、自动发布（GitHub Actions）

> 需要 token 勾选 `workflow` 权限

`.github/workflows/docker-publish.yml` 已经写好，只需：

1. 去 https://github.com/847832669/openwrt-monitor/settings/secrets/actions
2. 添加 `GITHUB_TOKEN`（自动就有，不用配）
3. 每次 `git push` 到 main，自动构建推送

## 三、Unraid 上拉取运行

```bash
# 从 ghcr.io 拉取
docker pull ghcr.io/847832669/openwrt-monitor:latest

docker run -d \
  --name openwrt-monitor \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /mnt/user/appdata/openwrt-monitor/data:/app/data \
  ghcr.io/847832669/openwrt-monitor:latest
```
