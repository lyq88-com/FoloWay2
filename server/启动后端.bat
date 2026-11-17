@echo off
chcp 65001 >nul
title 循途 - 后端服务
cd /d %~dp0
echo [循途] 正在启动后端 FastAPI (0.0.0.0:8000)...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
