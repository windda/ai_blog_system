#!/bin/bash
# ============================================================
# 博客管理系统 - 一键启动脚本（Linux/Mac）
# 
# 用法：
#   ./start.sh          # 启动所有服务（Docker）
#   ./start.sh dev      # 本地开发模式
#   ./start.sh stop     # 停止所有服务
#   ./start.sh logs     # 查看日志
# ============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

MODE="${1:-docker}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  博客管理系统 - 启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"

case "$MODE" in
    docker)
        echo -e "${YELLOW}[启动] Docker 全栈部署...${NC}"
        docker compose up -d --build
        echo -e "${GREEN}[完成] 服务已启动！${NC}"
        echo -e "  后端: ${GREEN}http://localhost:9000${NC}"
        echo -e "  前端: ${GREEN}http://localhost${NC}"
        echo -e "  数据库: localhost:3307 (root/123456)"
        echo -e "  Redis: localhost:6380"
        echo ""
        echo -e "  查看日志: ./start.sh logs"
        echo -e "  停止服务: ./start.sh stop"
        ;;
    
    dev)
        echo -e "${YELLOW}[启动] 本地开发模式...${NC}"
        
        # 检查依赖
        echo "  检查 Python 依赖..."
        pip install -r requirements.txt
        
        echo "  检查前端依赖..."
        cd owl-ui
        npm install
        cd ..
        
        echo ""
        echo -e "${GREEN}[提示] 请确保 MySQL 和 Redis 已启动${NC}"
        echo "  请在两个终端分别执行："
        echo ""
        echo -e "  终端 1 (后端): ${YELLOW}python owl_admin/app.py${NC}"
        echo -e "  终端 2 (前端): ${YELLOW}cd owl-ui && npm run dev${NC}"
        ;;
    
    stop)
        echo -e "${YELLOW}[停止] 停止 Docker 服务...${NC}"
        docker compose down
        echo -e "${GREEN}[完成] 所有服务已停止${NC}"
        ;;
    
    logs)
        echo -e "${YELLOW}[日志] 查看后端日志...${NC}"
        docker compose logs -f backend
        ;;
    
    restart)
        echo -e "${YELLOW}[重启] 重启 Docker 服务...${NC}"
        docker compose down
        docker compose up -d --build
        echo -e "${GREEN}[完成] 服务已重启${NC}"
        ;;
    
    *)
        echo "用法: $0 {docker|dev|stop|logs|restart}"
        exit 1
        ;;
esac