# AI 博客系统（Flask + Vue）

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![Vue](https://img.shields.io/badge/Vue-2.x-brightgreen)](https://vuejs.org)
[![SQLite](https://img.shields.io/badge/SQLite-✓-orange)](https://sqlite.org)
[![PyInstaller](https://img.shields.io/badge/PyInstaller-✓-red)](https://pyinstaller.org)

基于 Flask + Vue 的 AI 博客系统，支持文章发布、评论互动、分类标签、AI 智能对话。
**核心特性：可打包成 Windows 独立 exe，双击即用，零部署。**

---

## 📋 项目概述

原架构为 **MySQL + Redis + 前后端分离**，为满足"打包成 Windows 独立 exe"的交付需求，
做了"去外部依赖 + 打包"改造，最终支持三种运行形态：

| 形态 | 数据库 | 缓存 | 运行方式 |
|------|--------|------|----------|
| 本地开发 | MySQL | Redis | 前后端分离 |
| 打包版（exe）| **SQLite** | **内存版 Redis** | 单进程，双击即用 |
| 上线部署 | SQLite / MySQL | 内存版 / Redis | Docker 容器 |

---

## 🔧 基于本地开发的技术调整（核心改造）

原项目是 MySQL + Redis + 前后端分离架构，打包成 exe 前做了如下调整：

### 1. MySQL → SQLite（零部署）
- 连接串从 `mysql://...` 改为 `sqlite:///app.db`，嵌入式文件数据库，用户无需安装 MySQL；
- MySQL 方言类型（BIGINT/LONGTEXT/TINYINT）替换为 SQLAlchemy 通用类型（Integer/Text/SmallInteger）；
- 方言函数 `date_format()` 替换为 SQLite 的 `strftime()`；
- `db.create_all()` 自动建表，首次启动自动初始化。

### 2. Redis → 内存版 Redis（去依赖）
- 实现 `memory_redis.py`：接口兼容 `redis.Redis` 常用方法（get/set/incr/keys/zrevrange/hgetall 等）；
- 项目 40+ 处 Redis 调用**零改动**，只替换 `ext.py` 中的引用点；
- 单机场景进程内缓存，无需安装 Redis。

### 3. 前端分离 → 前端内置托管
- 前端 `npm run build` 生成 dist，Flask 同源托管；
- 剥掉 `/prod-api` 前缀，SPA history 路由兜底。

### 4. AI 密钥 → BYOK（Bring Your Own Key）
- DeepSeek API Key 由用户自行填写，按 user_id 隔离存储到本地 `ai_config.json`；
- Key 不打包进 exe、不写死在代码里、不上传，避免泄露；
- 支持模型选择（deepseek-chat / reasoner / flash）、清除 Key、打码显示。

### 5. PyInstaller 打包 + Inno Setup 安装包
- `run.py` 作为打包入口，`app.spec` 收集依赖与数据文件；
- `installer.iss` 将 exe 再打包成带安装向导、桌面快捷方式、卸载功能的安装包。

---

## 🚀 快速启动

### 方式一：本地开发（MySQL + Redis）

```bash
pip install -r requirements.txt
# 启动 MySQL 和 Redis，导入 sql/ 目录脚本
python owl_admin/app.py          # 后端 http://localhost:9000
cd owl-ui && npm install && npm run dev   # 前端 http://localhost:80
```

### 方式二：打包 exe（SQLite + 内存 Redis，零部署）

```bash
# 1. 前端构建
cd owl-ui && npm run build:prod

# 2. PyInstaller 打包
pyinstaller app.spec --clean
# 产物：dist/AI_Blog_System.exe（双击即用）
```

### 方式三：Docker 部署（上线）

```bash
docker compose up -d
# 访问 http://localhost:9000
```

---

## 📦 打包说明

### 打包 exe（PyInstaller）
```bash
pyinstaller app.spec --noconfirm --clean
```
- 单文件 exe：`dist/AI_Blog_System.exe`；
- 首次运行自动生成 `app.db`（数据库）、`uploads/`（图片）、`ai_config.json`（AI key）到 exe 同目录。

### 打安装包（Inno Setup）
```bash
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```
- 产物：`installer_output/AI博客系统_Setup_1.0.0.exe`；
- 安装向导 + 桌面快捷方式 + 卸载。

---

## 🌐 上线部署

### 方案 A：云服务器（正式上线）
```bash
docker compose up -d
```
- 单机个人博客可继续用 SQLite；多用户高并发可切回 MySQL（改 `app-dev.yml` 连接串 + `strftime`→`date_format` + `ext.py` 换回 FlaskRedis）。

### 方案 B：Vercel 应急演示（免费临时）
```
前端 dist → 部署到 Vercel（公网）
后端 Flask → 本机跑 exe
两者之间 → 内网穿透（frp/ngrok）
```
- 适合面试临时甩链接；局限：依赖本机开机、穿透不稳定。

---

## 📚 项目结构

```
├── owl_admin/              # Flask 应用核心（app.py、ext.py、controller）
├── owl_blog/               # 博客业务（文章/评论/分类/标签/仪表盘）
├── owl_ai/                 # AI 对话（BYOK 配置、DeepSeek 客户端）
├── owl_common/             # 公共基础库（内存 Redis、异常、模型）
├── owl_framework/          # 框架支撑（权限、Token）
├── owl_system/             # 系统管理（用户/角色/菜单）
├── owl-ui/                 # Vue 前端
├── run.py                  # 打包入口
├── app.spec                # PyInstaller 打包配置
├── installer.iss           # Inno Setup 安装包脚本
├── migrate_to_sqlite.py    # MySQL → SQLite 数据迁移脚本
└── docker-compose.yml      # Docker 编排
```

---

## 🌐 API 接口清单

| 接口 | 功能 | 权限 |
|------|------|------|
| GET /blog/article/list | 文章管理列表 | blog:article:list |
| GET /front/article/list | 前台文章列表 | 无 |
| GET /front/hot-articles | 热门文章 | 无 |
| GET /blog/dashboard | 后台仪表盘 | 登录 |
| POST /blog/article | 新增文章 | blog:article:add |
| POST /comment | 发表评论 | 无 |
| POST /ai/chat | AI 对话 | 登录 |
| GET /ai/config | AI 配置状态 | 登录 |
| POST /common/upload | 图片上传 | 登录 |
| GET /uploads/article/{filename} | 图片访问 | 无 |

---

## 🏗️ 架构亮点

1. **全局统一异常处理**：ServiceException / HTTPException / Exception 三级异常，Controller 不再写 try/except；
2. **RBAC 权限模型**：用户 → 角色 → 菜单/按钮三级权限，`@PreAuthorize` 装饰器控制；
3. **内存 Redis 接口兼容**：40+ 处缓存调用零改动，成本最低的去依赖方案；
4. **BYOK 密钥隔离**：AI Key 用户自填、按用户隔离、本地存储、不打包不泄露。
