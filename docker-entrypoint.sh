#!/bin/bash
# ============================================================
# Docker 入口脚本
# 
# 功能：
# 1. 等待 MySQL 就绪
# 2. 切换为 Docker 环境配置
# 3. 初始化目录结构
# 4. 启动 Flask 应用
# ============================================================

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  博客管理系统 - Docker 启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# ============================================================
# 步骤 1：等待 MySQL 就绪
# ============================================================
echo -e "${YELLOW}[1/4] 等待 MySQL 数据库就绪...${NC}"

MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_PORT="${MYSQL_PORT:-3306}"

echo "  尝试连接 ${MYSQL_HOST}:${MYSQL_PORT} ..."
for i in $(seq 1 30); do
    if python -c "
import socket
try:
    s = socket.create_connection(('${MYSQL_HOST}', ${MYSQL_PORT}), timeout=2)
    s.close()
    print('ok')
except:
    exit(1)
" 2>/dev/null | grep -q 'ok'; then
        echo -e "${GREEN}  ✅ MySQL 已就绪！${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}  ❌ MySQL 连接超时，请检查数据库配置${NC}"
        echo -e "${YELLOW}  容器将继续启动，但数据库可能不可用${NC}"
    else
        echo "  等待 MySQL 启动... ($i/30)"
        sleep 2
    fi
done

# ============================================================
# 步骤 2：切换为 Docker 环境配置
# ============================================================
echo -e "${YELLOW}[2/4] 切换为 Docker 环境配置...${NC}"

# 将 env 从 dev 切换为 docker，从而加载 app-docker.yml
# app-docker.yml 使用服务名连接 mysql/redis
sed -i "s/env: 'dev'/env: 'docker'/" /app/owl_admin/config/app.yml
echo -e "${GREEN}  ✅ 已切换为 Docker 配置${NC}"

# ============================================================
# 步骤 3：创建必要的目录
# ============================================================
echo -e "${YELLOW}[3/4] 初始化目录结构...${NC}"

mkdir -p /app/uploads/upload/article
mkdir -p /app/logs
echo -e "${GREEN}  ✅ 目录创建完成${NC}"

# ============================================================
# 步骤 4：启动应用
# ============================================================
echo -e "${YELLOW}[4/4] 启动 Flask 应用...${NC}"
echo -e "${GREEN}  🚀 服务地址: http://0.0.0.0:9000${NC}"
echo -e "${GREEN}========================================${NC}"

exec python owl_admin/app.py