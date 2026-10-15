# ============================================================
# Dockerfile - 博客管理系统前端（预编译方案）
#
# 前端已在本地用 npm run build:prod 打包好 owl-ui/dist，
# 这里只负责用 nginx 托管静态文件，不在容器内编译（避免服务器内存不足 OOM）。
# ============================================================

FROM nginx:alpine

# 复制本地打包好的前端产物（构建上下文是 owl-ui 目录）
COPY dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
