@echo off
chcp 65001 >nul
rem 一键把本机当前局域网 IP 写回 frontend/common/env.js
rem 换 WiFi / 换电脑后双击运行即可，避免 App 真机调试时连不上后端
cd /d "%~dp0"
node tools\sync-lan-host.js
pause
