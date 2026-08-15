# ============================================================
# Dockerfile - 博客管理系统前端
#
# 注意：构建上下文是项目根目录（docker-compose 中设置）
# 所以 COPY 路径相对于项目根目录
# ============================================================

# ---- 构建阶段 ----
FROM node:16-alpine AS build-stage

WORKDIR /app

# 复制依赖文件
COPY owl-ui/package.json owl-ui/package-lock.json ./
RUN npm install --registry=https://registry.npmmirror.com

# 复制前端源码
COPY owl-ui/ .

# 构建
RUN npm run build:prod

# ---- 生产阶段 ----
FROM nginx:alpine AS production-stage

# 复制编译产物
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
