# 演示启动步骤文档（DEMO GUIDE）

> 面试现场 / 录屏演示专用。照着这份文档操作，保证流程顺滑、不翻车。

---

## 一、环境准备（首次演示前一次性完成）

### 1. 安装后端依赖
```bash
cd e:\env\ai_blog_system
pip install -r requirements.txt
```

### 2. 准备模型 Key（任选其一，推荐 DeepSeek）
| 供应商 | 环境变量 | 申请地址 |
|--------|----------|----------|
| DeepSeek | `DEEPSEEK_API_KEY` | platform.deepseek.com |
| 腾讯混元 | `HUNYUAN_API_KEY` | cloud.tencent.com（可选，用于容灾演示）|

**Windows 设置方式（临时，当前终端有效）：**
```powershell
$env:DEEPSEEK_API_KEY = "sk-你的key"
```

> 也可以不设环境变量，启动后到【后台 → AI Token 统计 → 平台全局 API Key 配置】里填写平台 Key（加密存数据库，改完即生效）。

### 3. 构建前端（录屏前先跑一次，产物由后端同源托管）
```bash
cd owl-ui
npm install
npm run build:prod
```

---

## 二、启动步骤

### 方式 A：开发模式（推荐面试现场，改动即时生效）
```bash
# 终端 1：启动后端（会自动建表 + 迁移 + 托管前端）
cd e:\env\ai_blog_system
python run.py
# 看到 "AI 博客系统已启动" 即成功

# 浏览器访问
# http://127.0.0.1:9000
```

### 方式 B：打包 exe（录屏演示"零部署"卖点时用）
```bash
pyinstaller app.spec --noconfirm --clean
# 产物 dist/AI_Blog_System.exe，双击即用，自动打开浏览器
```

---

## 三、账号与密钥

| 项 | 值 |
|----|-----|
| 管理员账号 | `admin` / `admin123` |
| 普通用户 | 后台【用户管理】自建，或注册 |
| 平台全局 Key | 后台【AI Token 统计 → 平台全局 API Key 配置】填写 |
| 用户自有 Key | 用户登录后在 AI 对话页【设置 Key】填写 |

---

## 四、演示流程顺序（建议按此顺序，逻辑最顺）

1. **启动**（10 秒）——双击 exe / `python run.py`，强调"零部署，SQLite 免装数据库"。

2. **登录后台**（20 秒）——admin 登录，快速扫一眼后台菜单，证明"完整管理系统"。

3. **配置平台全局 Key**（30 秒）——【AI Token 统计】→【平台全局 API Key 配置】填 Key → 保存 → 强调"**加密存数据库，改完即生效，不重启**"。

4. **AI 对话（流式）**（2 分钟，核心）——切到 AI 对话页 → 发消息看 SSE 打字机 → 顶部「今日已用」实时跳动。

5. **双密钥模式**（1 分钟，重点）——顶部模式标签显示「平台统一额度模式」→ 打开【设置 Key】弹窗讲清两种模式区别 → 填一个用户自有 Key 演示切换。

6. **语音识别**（40 秒，feature-asr 分支）——提示"语音功能在 feature-asr 分支迭代，作为后续扩展"（主分支已隐藏按钮，代码保留）。

7. **Token 报表**（1 分钟）——后台【AI Token 统计】看 ECharts 折线图 + 饼图 + 供应商成功率 + 调用日志（含失败原因）。

8. **容灾演示**（30 秒，可选）——把平台 Key 换成错误的，发消息看自动切换供应商 + 后台失败日志标红。

---

## 五、常见问题（演示前自查）

| 问题 | 排查 |
|------|------|
| 后端起不来 | 确认 `pip install -r requirements.txt` 已执行 |
| 前端白屏 | 确认 `owl-ui/dist` 已构建（`npm run build:prod`）|
| 发消息报"请先配置 Key" | 确认平台 Key 已配，或环境变量 `DEEPSEEK_API_KEY` 已设 |
| 额度耗尽提示 | 这是正常限额逻辑，演示前可清空 token 记录或等次日 |
| 图表空白 | 确认有 token 记录（先发几条消息）|
