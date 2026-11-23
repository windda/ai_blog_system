# ============================================================
# Dockerfile - AI 博客系统（多阶段构建，一键部署）
#
# 阶段 1：构建 Vue 前端（owl-ui/dist）
# 阶段 2：Python 后端 + SQLite + 前端内置托管
#
# 部署：docker compose up -d
# 访问：http://localhost:9000
# 默认账号：admin / admin123
#
# 说明：
#   - 数据库用 SQLite（免装 MySQL），缓存用内存版 Redis（免装 Redis）；
#   - 前端产物由后端 Flask 同源托管，单容器即可跑整套前后端；
#   - 数据持久化见 docker-compose.yml 的 volumes 配置。
# ============================================================

# ---------- 阶段 1：构建 Vue 前端 ----------
FROM node:16-alpine AS frontend-build
WORKDIR /build/owl-ui
# 只复制 package.json（package-lock.json 被 .gitignore 排除，不进 git，用 npm install 生成依赖）
COPY owl-ui/package.json ./
RUN npm install --registry=https://registry.npmmirror.com
COPY owl-ui/ ./
# node16 + webpack4 需要 openssl-legacy-provider；加大内存上限防 OOM
ENV NODE_OPTIONS=--openssl-legacy-provider
RUN node --max-old-space-size=2048 node_modules/.bin/vue-cli-service build

# ---------- 阶段 2：Python 后端 ----------
FROM python:3.10-slim-bookworm

WORKDIR /app

# 依赖基本都是纯 Python 或带 wheel，仅保留 gcc 以备个别扩展编译
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn

# 复制后端代码
COPY . .

# 复制前端构建产物（阶段 1 产物）
COPY --from=frontend-build /build/owl-ui/dist ./owl-ui/dist

# 数据目录：SQLite 数据库（instance/）+ 上传文件（uploads/）+ 日志（logs/）
RUN mkdir -p /app/instance /app/uploads /app/logs

EXPOSE 9000

# dev 配置 = SQLite + 内存 Redis + 前端内置托管，启动即建表 + 迁移
CMD ["python", "run.py"]
