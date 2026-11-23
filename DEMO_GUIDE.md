# 部署与使用指南

本文档说明本地启动、构建、账号与密钥配置，以及主要功能的使用方式。

---

## 一、环境准备

### 1. 安装后端依赖
```bash
cd e:\env\ai_blog_system
pip install -r requirements.txt
```

### 2. 准备模型 Key
| 供应商 | 环境变量 | 申请地址 |
|--------|----------|----------|
| DeepSeek | `DEEPSEEK_API_KEY` | platform.deepseek.com |
| 腾讯混元 | `HUNYUAN_API_KEY` | cloud.tencent.com |

**Windows 设置方式（当前终端有效）：**
```powershell
$env:DEEPSEEK_API_KEY = "sk-你的key"
```

也可以不设环境变量，启动后到【后台 → AI Token 统计 → 平台全局 API Key 配置】里填写平台 Key（加密存数据库，改完即生效）。

### 3. 构建前端
```bash
cd owl-ui
npm install
npm run build:prod
```

---

## 二、启动方式

### 方式 A：开发模式
```bash
cd e:\env\ai_blog_system
python run.py
# 看到 "AI 博客系统已启动" 即成功
# 浏览器访问 http://127.0.0.1:9000
```

### 方式 B：打包 exe
```bash
pyinstaller app.spec --noconfirm --clean
# 产物 dist/AI_Blog_System.exe，双击即用
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

## 四、主要功能使用

1. **配置平台全局 Key**：后台【AI Token 统计 → 平台全局 API Key 配置】填写并保存，加密存数据库，改完即生效。

2. **AI 对话**：进入 AI 对话页，输入消息发送，SSE 流式返回。

3. **调用模式选择**：对话页顶部下拉选择「平台统一额度 / 使用自己的 Key / 自动（自有优先）」。

4. **语音识别**：后台开启「语音识别」开关后，对话页显示录音按钮（功能在 feature-asr 分支）。

5. **Token 报表**：后台【AI Token 统计】查看 Token 趋势、模型用量、供应商成功率、调用日志。

6. **多供应商容灾**：某供应商 429/500/超时失败时自动切换下一个供应商，日志记录切换过程。

---

## 五、常见问题排查

| 问题 | 排查 |
|------|------|
| 后端起不来 | 确认 `pip install -r requirements.txt` 已执行 |
| 前端白屏 | 确认 `owl-ui/dist` 已构建（`npm run build:prod`）|
| 发消息报"请先配置 Key" | 确认平台 Key 已配，或环境变量 `DEEPSEEK_API_KEY` 已设 |
| 额度耗尽提示 | 属于平台额度限额逻辑，可清空 token 记录或等次日 |
| 图表空白 | 确认有 token 记录（先发几条消息）|
