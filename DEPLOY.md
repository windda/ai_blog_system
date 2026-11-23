# 线上服务器手动部署指南

> 适用：低内存（2G）云服务器，通过 SSH 分步执行。核心思路：先加 swap 缓解内存不足，再构建镜像。

服务器：Ubuntu 22.04，Docker + Docker Compose，2G 内存。

---

## 一、清理卡死的构建（如果之前 build 卡住）

```bash
# SSH 登录（build 卡住时 sshd 响应慢，多等一会儿再连）
ssh root@<服务器IP>

# 清理卡住的容器
docker ps -a
docker rm -f $(docker ps -aq) 2>/dev/null

# 清理构建缓存
docker builder prune -f
docker system prune -f
```

---

## 二、增加 swap（关键：2G 内存 build 会 OOM，先加 4G swap）

```bash
# 创建 4G swap 文件
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# 永久生效（重启后仍有效）
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# 验证（应看到 4G swap）
free -h
swapon --show
```

---

## 三、拉取最新代码

```bash
cd /root/ai_blog_system

# 丢弃本地临时修改、删除冲突文件
git checkout -- .
rm -f sql/blog_menu.sql owl-ui/dist.tar.gz owl-ui/frontend.tar.gz

# 拉取最新代码
git pull origin main

# 确认最新提交（应包含 0ad8047）
git log --oneline -3
```

---

## 四、配置密钥（config.yaml + .env，不入 git）

```bash
cd /root/ai_blog_system

# config.yaml（从模板复制，密钥通过环境变量引用）
cp config.example.yaml config.yaml

# .env（真实密钥，仅服务器保存，禁止提交）
cat > .env << 'EOF'
DEEPSEEK_API_KEY=sk-你的真实key
REGISTER_ENABLE=true
EOF
```

---

## 五、构建镜像

```bash
cd /root/ai_blog_system

# 确认 Dockerfile 前端构建部分（应是 npm install，且无 NODE_OPTIONS）
sed -n '16,26p' Dockerfile

# 若内容不对，手动修正：
#   sed -i 's|COPY owl-ui/package.json owl-ui/package-lock.json ./|COPY owl-ui/package.json ./|' Dockerfile
#   sed -i 's|RUN npm ci |RUN npm install |' Dockerfile
#   sed -i '/ENV NODE_OPTIONS=--openssl-legacy-provider/d' Dockerfile

# 构建（加 swap 后不会 OOM；前端 node build + 后端 pip install 约 5-10 分钟）
docker compose build
```

---

## 六、启动服务

```bash
cd /root/ai_blog_system

docker compose up -d

# 查看容器状态
docker compose ps

# 查看启动日志（确认无报错）
docker compose logs -f app
```

---

## 七、自测

```bash
# 健康检查（应返回 ok）
curl http://127.0.0.1:9000/health

# 浏览器访问
# http://<服务器IP>:9000
# 默认账号 admin / admin123
```

验证项：
1. 登录后台，【AI Token 统计】页面正常（报表、成功率、调用日志）；
2. 对话页发消息，SSE 流式正常返回；
3. 切换「平台统一额度 / 自己的 Key / 自动」三种模式；
4. 后台配置平台 Key，验证「今日平台额度」统计。

---

## 附：如果 build 仍 OOM

降低前端 node 内存上限（Dockerfile 内 `--max-old-space-size=2048` 改为 `1024`），或继续加大 swap。
