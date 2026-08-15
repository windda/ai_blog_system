# 个人博客管理系统（Flask + Vue + MySQL + Redis + Docker）

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![Vue](https://img.shields.io/badge/Vue-2.x-brightgreen)](https://vuejs.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)](https://mysql.com)
[![Redis](https://img.shields.io/badge/Redis-7.0-red)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-✓-blue)](https://docker.com)

## 📋 项目概述

基于 **RuoYi-Vue-Flask** 框架开发的企业级博客管理系统，实现完整的 RBAC 权限控制、文章管理、评论审核、分类标签管理等核心功能。

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | Flask 3.0 + Pydantic V2 | RESTful API + 参数校验 + 自动序列化 |
| ORM | SQLAlchemy 2.0 | 多表关联查询 + 事务管理 |
| 权限认证 | JWT + Redis | Token 无状态认证 + 登录态缓存 |
| 缓存 | Redis 7 | 文章列表缓存（降低数据库压力） |
| 数据库 | MySQL 8.0 | 业务数据持久化 |
| 前端 | Vue 2 + ElementUI | 若依前端框架 + 路由懒加载 |
| 全文检索 | Elasticsearch 8.x | ik 分词 + 降级 MySQL LIKE |
| 实时通信 | WebSocket (Flask-SocketIO) | 审核通知实时推送 |
| AI 对话 | DeepSeek / OpenAI API | 多轮对话记忆 + 上下文管理 |
| 部署 | Docker + Compose | 容器化一键部署 |

---

## 🚀 快速启动

### 方式一：本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 确保 MySQL 和 Redis 在运行
# MySQL: 创建数据库 ry-vue-py，导入 sql/ 目录下的脚本
# Redis: 默认端口 6379

# 3. 修改配置
# 编辑 owl_admin/config/app-dev.yml 中的数据库连接信息

# 4. 启动后端
python owl_admin/app.py
# 访问 http://localhost:9000

# 5. 启动前端（新开终端）
cd owl-ui
npm install
npm run dev
# 访问 http://localhost:80
```

### 方式二：Docker 一键部署（推荐）

```bash
# 确保已安装 Docker 和 Docker Compose

# 一键启动所有服务
docker compose up -d

# 查看运行状态
docker compose ps

# 查看日志
docker compose logs -f backend

# 访问 http://localhost:9000
```

---

## ⚙️ 环境变量配置说明

复制 `.env.example` 为 `.env` 后按需修改：

| 变量 | 说明 | 示例 |
|------|------|------|
| APP_ENV | 运行环境（dev/production） | dev |
| APP_PORT | 后端服务端口 | 9000 |
| REGISTER_ENABLE | 是否开放注册（true/false） | false |
| MYSQL_HOST | MySQL 地址 | 127.0.0.1 |
| MYSQL_PORT | MySQL 端口 | 3306 |
| MYSQL_DATABASE | 数据库名 | ry-vue-py |
| MYSQL_USER | MySQL 用户名 | root |
| MYSQL_PASSWORD | MySQL 密码 | your_mysql_password_here |
| REDIS_HOST | Redis 地址 | 127.0.0.1 |
| REDIS_PORT | Redis 端口 | 6379 |
| UPLOAD_DIR | 上传文件目录 | ./uploads |
| DEEPSEEK_API_KEY | DeepSeek API 密钥 | your_deepseek_api_key_here |
| DEEPSEEK_BASE_URL | DeepSeek 接口地址 | https://api.deepseek.com/v1 |
| DEEPSEEK_MODEL | 模型名称（deepseek-chat / deepseek-flash） | deepseek-chat |

---

## 📚 项目结构

```
├── owl_admin/              # Flask 应用核心
│   ├── app.py              # 应用工厂 + 全局异常处理
│   ├── ext.py              # 扩展初始化（db, redis, cors）
│   ├── controller/common/  # 通用接口（文件上传/下载）
│   └── config/             # YAML 配置
├── owl_blog/               # 博客业务模块
│   ├── controller/         # API 控制器（文章/评论/分类/标签/仪表盘）
│   ├── service/            # 业务逻辑层（含 Redis 缓存）
│   ├── mapper/             # 数据访问层（SQLAlchemy）
│   ├── domain/             # 实体类（Pydantic Model + ORM Model）
│   └── utils.py            # 公共工具类（用户认证、权限判断）
├── owl_common/             # 公共基础库
│   ├── base/model.py       # AjaxResponse、分页、序列化
│   └── exception.py        # 全局异常体系
├── owl_framework/          # 框架支撑
│   ├── descriptor/         # 权限装饰器、操作日志
│   └── service/token.py    # JWT + Redis Token 管理
├── owl_system/             # 系统管理（用户/角色/菜单）
├── owl-ui/                 # Vue 前端
├── sql/                    # 数据库脚本
├── uploads/                # 上传文件存储
├── docker-compose.yml      # Docker 编排
└── Dockerfile              # 后端容器镜像
```

---

## 🌐 API 接口清单

### 博客文章
| 接口 | 功能 | 权限 |
|------|------|------|
| GET /blog/article/list | 文章管理列表 | blog:article:list |
| GET /blog/article/pub/list | 公开文章列表（首页） | 需登录 |
| GET /blog/article/{id} | 文章详情 | 需登录 |
| POST /blog/article | 新增文章 | blog:article:add |
| PUT /blog/article | 修改文章 | blog:article:edit |
| DELETE /blog/article/{ids} | 删除文章 | blog:article:remove |
| PUT /blog/article/view/{id} | 增加浏览量 | 无 |

### 评论管理
| 接口 | 功能 | 权限 |
|------|------|------|
| GET /blog/comment/list | 评论管理列表 | blog:comment:list |
| GET /blog/comment/list/{article_id} | 前台评论列表 | 无 |
| POST /blog/comment | 发表评论 | 无 |
| PUT /blog/comment/status | 审核评论 | blog:comment:edit |
| DELETE /blog/comment/{ids} | 删除评论 | blog:comment:remove |

### 分类/标签
| 接口 | 功能 |
|------|------|
| GET /blog/category/list | 分类列表 |
| GET /blog/tag/list | 标签列表 |

### 通用
| 接口 | 功能 |
|------|------|
| POST /common/upload | 图片上传 |
| GET /uploads/article/{filename} | 图片访问 |

---

## 🏗️ 架构设计亮点

### 1. 全局统一异常处理
```python
# owl_admin/app.py - 类似 Spring @ControllerAdvice
@app.errorhandler(ServiceException)  # 业务异常 → 自定义code+msg
@app.errorhandler(HTTPException)     # HTTP异常 → 404/405等
@app.errorhandler(Exception)         # 未知异常 → 500 + 堆栈
```
- 所有 Controller 不再写 try/except
- 异常在一个地方统一处理，返回统一 JSON 格式

### 2. RBAC 权限模型
- 用户 → 角色 → 菜单/按钮三级权限
- `@PreAuthorize(HasPerm("blog:article:edit"))` 装饰器控制接口权限
- 前端 `v-hasPermi` 指令控制按钮可见性
- 管理员看全部，普通用户数据隔离

### 3. Redis 缓存策略
- 用户登录态存储在 Redis（自动过期）
- 公开文章列表缓存 5 分钟
- 新增/修改/删除自动清除缓存（保证数据一致性）

### 4. 代码质量（DRY 原则）
- 重复的 `get_current_user()` / `is_admin()` 抽离到公共工具类
- 5 个 Controller 共减少约 200 行重复代码

---

## 🚀 近期更新

### v2.0 仪表盘重构（2024-06）

| 改进项 | 之前 | 之后 |
|--------|------|------|
| 统计数据 | 全量查询后 `len()`，数据量大时OOM | COUNT聚合查询，毫秒级返回 |
| 文章列表 | `pageSize=999` 全量返回 | 分页查询，默认5条/页 |
| 分类筛选 | 前端假过滤（全量数据中filter） | 后端SQL条件过滤 |
| 发布趋势 | ❌ 无 | ✅ ECharts柱状图展示近7天趋势 |
| 评论动态 | ❌ 无 | ✅ 联表查询最新5条评论 |
| 今日浏览 | ❌ 无 | ✅ SUM聚合 |
| 待审核提醒 | ❌ 无 | ✅ 卡片上红色Badge |

## 📈 遗留待优化功能

1. **AI 集成**：文章 AI 摘要生成、评论 AI 审核（对接 DeepSeek API）
2. **RAG 知识库**：将博客文章向量化，支持自然语言检索
3. **前台博客**：公开博客首页 + 文章详情 + 评论区
4. **性能优化**：Nginx 反向代理、CDN 静态资源、数据库读写分离
5. **监控告警**：Prometheus + Grafana 接口监控 + 慢查询日志
6. **CI/CD**：GitHub Actions 自动化测试 + 部署
