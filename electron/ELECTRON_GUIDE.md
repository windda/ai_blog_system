# Electron 打包说明（Windows 桌面端）

> 把 Vue 前端 + Flask 后端打包成 Windows 安装包。本文档说明打包流程、产物、以及「自动更新」「代码签名」的实现方案（这两项未实际实现）。

---

## 一、打包步骤

### 前置环境
- Node.js 16+（前端构建 + electron-builder）
- Python 3.10+（后端运行）
- Windows x64

### 一键打包（推荐）
```bat
cd electron
build-win.bat
```
脚本会自动：构建前端 → 安装 electron 依赖 → 打包 NSIS 安装包。

### 手动分步打包
```bash
# 1. 构建前端
cd owl-ui && npm install && npm run build:prod

# 2. 安装 electron 依赖
cd ../electron && npm install

# 3. 打包 Windows 安装包
npx electron-builder --win nsis --x64
```

### 产物
```
electron/release/
  AI对话后台 Setup 1.0.0.exe   # NSIS 安装包（支持选安装目录、桌面快捷方式）
```

---

## 二、运行原理

Electron 主进程（`main.js`）启动后：
1. `spawn python run.py` 拉起 Flask 后端（监听 127.0.0.1:9000）
2. `BrowserWindow` 加载 `owl-ui/dist/index.html`（前端静态资源）
3. 前端通过同源 API 访问本地后端，形成「前端壳 + 本地服务」桌面应用

**路径处理**（`main.js` 已处理）：
- 开发环境：`resourcesRoot = 项目根目录`
- 打包环境：`resourcesRoot = process.resourcesPath`（extraResources 复制到这里）

---

## 三、静态资源 / 依赖路径处理

`electron/package.json` 的 `build.extraResources` 已把后端代码、前端 dist、run.py、config.yaml 打进安装包：
```
resources/
  owl-ui/dist/       # 前端产物
  owl_admin/ owl_ai/ owl_blog/ owl_common/ owl_system/  # 后端模块
  run.py requirements.txt config.yaml
```

---

## 四、自动更新方案（仅文档，未实现）

**实现思路**（不实际做，证书/服务器成本高）：
1. 后端托管一个 `latest.yml`（含版本号、下载地址、sha512 校验值）
2. 前端用 `electron-updater` 库，启动时请求 `latest.yml` 比对版本
3. 有新版本 → 下载新安装包 → 校验 hash → 提示用户重启安装
4. 关键：**更新包必须用代码签名证书签名**，否则 Windows 会拦截

```js
// 伪代码示例
const { autoUpdater } = require('electron-updater')
autoUpdater.checkForUpdatesAndNotify()
```

---

## 五、代码签名方案（仅文档，未实现）

**为什么需要签名**：未签名的 exe 会被 Windows SmartScreen / 杀软拦截，提示"未知发布者"，影响安装体验。

**实现思路**：
1. 购买代码签名证书（EV 证书约 ¥2000-4000/年，OV 证书约 ¥1000-2000/年）
2. 在 electron-builder 配置证书：
```yaml
# electron-builder.yml
win:
  signingHashAlgorithms: [sha256]
  certificateFile: cert.pfx
  certificatePassword: ${CERT_PASSWORD}
```
3. 打包时 electron-builder 自动签名

**降级方案**（未购买证书时）：
- 本地自签名证书（`makecert` / `signtool`），仅本机信任，可用于测试安装；
- 或打包成免安装的 `--dir` 目录版，不触发 SmartScreen。

---

## 六、已知局限与后续规划

| 局限 | 后续规划 |
|------|----------|
| 打包版依赖本机 Python 环境 | 用 PyInstaller 把 run.py 打成 `ai_backend.exe`，免 Python |
| 未做自动更新 | 见第四节方案，需证书 + 更新服务器 |
| 未做代码签名 | 见第五节方案，需购买证书 |
| 仅 Windows x64 | 后续可扩展 macOS/Linux（electron-builder 天然支持，改 target 即可）|
