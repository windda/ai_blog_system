# ============================================================
# Dockerfile - 博客管理系统后端
# 
# 基于 Python 3.10 轻量镜像
# 支持 Linux/Windows/macOS 跨平台部署
# ============================================================

FROM python:3.10-slim

LABEL maintainer="shaw-lee"
LABEL description="博客管理系统后端"
LABEL version="2.0"

WORKDIR /app

# 安装系统依赖（减少层数，合并命令）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装（利用 Docker 缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn

# 复制项目代码
COPY . .

# 设置执行权限
RUN chmod +x docker-entrypoint.sh

# 创建必要目录
RUN mkdir -p /app/uploads/upload/article /app/logs

# 暴露端口
EXPOSE 9000

# 使用入口脚本启动
ENTRYPOINT ["/bin/bash", "docker-entrypoint.sh"]