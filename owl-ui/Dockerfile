# ============================================================
# Dockerfile - 博客管理系统前端（多阶段构建）
#
# 阶段1：node 编译前端（npm run build）
# 阶段2：nginx 托管编译产物
#
# 说明：仅在本地/CI 构建镜像；2G 服务器上不要执行 build（会 OOM）
# ============================================================

# ---- 构建阶段 ----
FROM node:16-alpine AS build-stage
WORKDIR /app

# 先复制依赖清单，利用 Docker 层缓存
COPY package.json package-lock.json ./
RUN npm ci --registry=https://registry.npmmirror.com

# 复制源码
COPY . .

# node16 + webpack4 需要 openssl-legacy-provider；加大内存上限防 OOM
ENV NODE_OPTIONS=--openssl-legacy-provider
RUN node --max-old-space-size=2048 node_modules/.bin/vue-cli-service build

# ---- 生产阶段 ----
FROM nginx:alpine

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
