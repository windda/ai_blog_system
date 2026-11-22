/*
 * Electron 主进程 —— 把 Vue 前端 + Flask 后端打包成 Windows 桌面应用。
 *
 * ============================================================
 * 打包流程（面试重点，按顺序讲）：
 * ============================================================
 * 1. 前端构建：
 *      cd owl-ui && npm install && npm run build
 *      -> 产物 owl-ui/dist/index.html（Vue 静态资源）
 *
 * 2. 后端依赖：
 *      pip install -r requirements.txt（或打包时用 PyInstaller 打成 exe）
 *      本示例直接 spawn python run.py（开发版）；生产打包建议 PyInstaller
 *      把 run.py 打成 ai_backend.exe，主进程改为 spawn exe。
 *
 * 3. 安装 Electron 依赖并打包 Windows 安装包：
 *      cd electron && npm install && npm run build:win
 *      -> 产物 electron/release/*.exe（NSIS 安装包，支持 x64）
 *
 * 4. 安装包双击安装，启动后 Electron 主进程：
 *      a. spawn 启动 Flask 后端（监听 127.0.0.1:端口）
 *      b. BrowserWindow 加载打包进 resources 的 owl-ui/dist/index.html
 *      c. 前端通过相对 API 前缀访问本地后端，形成「前端壳 + 本地服务」的桌面应用
 *
 * 说明：本文件是「打包准备」，重点是配置 + 流程注释，不纠结打包调试细节。
 * ============================================================
 */

const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

let backendProcess = null

// 打包环境：extraResources 复制到 resources/ 目录；开发环境：electron 目录的上级（项目根）
const isPackaged = app.isPackaged
const resourcesRoot = isPackaged ? process.resourcesPath : path.join(__dirname, '..')

// 启动 Flask 后端
function startBackend() {
  // 开发：spawn 项目根目录的 python run.py；打包：spawn resources/ 下的 run.py
  // 说明：后端依赖完整 Python 环境，生产打包建议用 PyInstaller 把 run.py 打成 exe 再 spawn
  const backendDir = resourcesRoot
  const pythonExecutable = process.env.PYTHON_EXECUTABLE || 'python'
  backendProcess = spawn(pythonExecutable, ['run.py'], {
    cwd: backendDir,
    env: Object.assign({}, process.env),
    windowsHide: true
  })
  backendProcess.stdout.on('data', d => console.log('[后端]', d.toString()))
  backendProcess.stderr.on('data', d => console.error('[后端]', d.toString()))
  backendProcess.on('exit', code => console.log('[后端] 退出，code =', code))
}

// 创建主窗口，加载 Vue 打包产物
function createWindow() {
  const win = new BrowserWindow({
    width: 1366,
    height: 860,
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  })

  // 前端产物：打包后从 resources/owl-ui/dist 加载；开发环境从项目根目录加载
  win.loadFile(path.join(resourcesRoot, 'owl-ui', 'dist', 'index.html'))

  // 开发：加载 Vue dev server（取消下面注释即可）
  // win.loadURL('http://localhost:8080')
}

app.whenReady().then(() => {
  startBackend()
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (backendProcess) {
    try { backendProcess.kill() } catch (e) { /* ignore */ }
  }
  if (process.platform !== 'darwin') app.quit()
})
