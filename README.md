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

## 🤖 多模型 Token 聚合网关（面试重点）

### 一、双密钥模式（对应 JD：Token 聚合平台）

| 模式 | 说明 | 存储 |
|------|------|------|
| 模式 A：平台全局 Key | 管理员后台统一配置，所有用户共用 | sys_config（`ai.platform.api.key`）|
| 模式 B：用户自有 Key | 用户在个人中心填写自己的模型密钥 | ai_config.json（对称加密，禁止明文入库）|

- **优先级**：用户自有 Key → 平台全局 Key → 环境变量兜底；
- **两层限额**：
  1. 厂商侧余额：DeepSeek / 混元等厂商自己管控，网关只捕获报错（401/403/429）分类返回前端；
  2. 平台侧限额：每个用户独立单日 Token 上限（软防护），不管走哪个 Key 都生效，保护服务不被打垮；
- 用户个人用量面板：只能查看自己的对话记录、token 消耗明细；管理员不变，查看全量记录。

### 二、多厂商容灾 + 故障切换

- 支持 DeepSeek / 腾讯混元 / 文心一言，统一请求封装（OpenAI 兼容协议）；
- 失败自动重试 + 降级切换备用模型（超时 / 500 自动切下一个供应商）；
- 异常分类：超时 / 限流 / 鉴权 / 解析失败，统一返回结构。

### 三、Token 统计 + 用量面板

- 每次 LLM / ASR 调用自动入库 `ai_token_record`，区分 `api` / `local_estimate` 统计来源；
- 用户用量面板：`/ai/daily-usage`（汇总）+ `/ai/my-token-records`（个人明细）；
- 管理员后台：`/admin/ai/token-records`（全量）+ `/admin/ai/token-summary`（汇总）。

### 四、ASR 语音输入（轻量版）

- 前端浏览器麦克风录音（MediaRecorder，audio/webm）→ 上传后端 `/ai/asr`；
- 后端调用第三方云 ASR（OpenAI whisper，可切火山/讯飞）转文字；
- 识别结果自动填充输入框，发送给大模型，同样走 token 统计入库。

### 五、Electron 打包方案

- `electron/main.js`：主进程 spawn 启动 Flask 后端 + 加载 Vue 打包产物；
- `electron/package.json`：electron-builder 配置，`npm run build:win` 打包 Windows x64 安装包（NSIS）；
- 完整打包流程注释见 `electron/main.js` 顶部（面试重点讲，不纠结打包调试）。

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
# 前端（nginx）：http://localhost
# 后端（Flask）：http://localhost:9000
# 默认账号：admin / admin123
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
├── owl_ai/                 # AI 网关（多模型调度、双密钥、ASR、Token 统计）
├── owl_common/             # 公共基础库（内存 Redis、异常、模型）
├── owl_framework/          # 框架支撑（权限、Token）
├── owl_system/             # 系统管理（用户/角色/菜单）
├── owl-ui/                 # Vue 前端（含 AI 对话、录音、用量面板）
├── electron/               # Electron 打包（main.js + electron-builder 配置）
├── run.py                  # 打包入口
├── app.spec                # PyInstaller 打包配置
├── installer.iss           # Inno Setup 安装包脚本
├── config.yaml             # AI 服务商/ASR 配置（多供应商、超时重试）
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
| POST /ai/chat | AI 对话（HTTP）| 登录 |
| POST /ai/chat/stream | AI 对话（SSE 流式）| 登录 |
| GET /ai/providers | 启用的供应商+模型列表 | 登录 |
| GET /ai/config | AI 配置状态（打码）| 登录 |
| GET /ai/daily-usage | 个人用量汇总（今日/累计/限额）| 登录 |
| GET /ai/my-token-records | 个人 token 消耗明细 | 登录 |
| POST /ai/asr | ASR 语音转文字 | 登录 |
| GET /admin/ai/token-records | 全量 token 记录 | 管理员 |
| GET /admin/ai/token-summary | token 汇总统计 | 管理员 |
| POST /common/upload | 图片上传 | 登录 |
| GET /uploads/article/{filename} | 图片访问 | 无 |

---

## 🏗️ 架构亮点

1. **全局统一异常处理**：ServiceException / HTTPException / Exception 三级异常，Controller 不再写 try/except；
2. **RBAC 权限模型**：用户 → 角色 → 菜单/按钮三级权限，`@PreAuthorize` 装饰器控制；
3. **内存 Redis 接口兼容**：40+ 处缓存调用零改动，成本最低的去依赖方案；
4. **BYOK 密钥隔离**：AI Key 用户自填、按用户隔离、本地存储、不打包不泄露。

---

## 🐳 Docker 部署踩坑记录

上线过程中踩过的真实坑及解决方案：

| 问题 | 根因 | 修复 |
|------|------|------|
| 后端崩溃循环 | `requirements.txt` 缺 `requests` | 补充依赖 |
| healthcheck 永远 unhealthy | `/health` 走动态注册流程，业务模块挂掉就中断 | `/health` 硬编码到 `app.py` 主应用 |
| nginx 反代 502 | Flask 绑 `127.0.0.1`，容器间连不上 | Docker 环境绑 `0.0.0.0` |
| 中文乱码 | MySQL 客户端 latin1 导入 UTF-8 数据 | SQL 开头 `SET NAMES utf8mb4` + 强制客户端 utf8mb4 |
| 博客菜单丢失 | 菜单数据不在 SQL 里，重建后丢 | 补 `blog_menu.sql` 兜底 |
| 封面图上传 413 | nginx 默认 `client_max_body_size=1MB` | 调至 20m |
| 封面图预览空白 | `send_from_directory` 相对路径被 `app.root_path` 解析错 | `_upload_dir` 用绝对路径 |
