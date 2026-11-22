@echo off
REM ============================================================
REM Electron 打包脚本（Windows）
REM 一键：构建前端 -> 安装 electron 依赖 -> 打包 exe 安装包
REM 产物：electron\release\AI对话后台 Setup 1.0.0.exe
REM 前置：已安装 Node.js 16+、Python 3.10+
REM ============================================================

echo [1/3] 构建 Vue 前端...
cd /d %~dp0..\owl-ui
call npm install --registry=https://registry.npmmirror.com
set NODE_OPTIONS=--openssl-legacy-provider
call npx vue-cli-service build
if errorlevel 1 (echo 前端构建失败 & pause & exit /b 1)

echo [2/3] 安装 electron 依赖...
cd /d %~dp0
call npm install --registry=https://registry.npmmirror.com

echo [3/3] 打包 Windows 安装包...
call npx electron-builder --win nsis --x64
if errorlevel 1 (echo 打包失败 & pause & exit /b 1)

echo.
echo ============================================================
echo  打包完成！产物在 electron\release\ 目录
echo  注意：安装包依赖本机 Python 环境运行后端，
echo        如需免 Python，请先用 PyInstaller 打包 run.py（见 ELECTRON_GUIDE.md）
echo ============================================================
pause
