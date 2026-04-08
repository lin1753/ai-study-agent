@echo off
chcp 65001 > nul
TITLE AI Study Agent - One Click Launcher

echo ======================================================
echo           AI Study Agent - 一键启动脚本
echo ======================================================

:: 检查运行环境 (Docker + Ollama)
echo [1/3] 请确保以下环境已就绪：
echo       - Docker 中的 pgvector 数据库已启动 (端口: 5433)
echo       - Ollama 已运行并拉取了所需模型 (deepseek-r1:7b, nomic-embed-text)   
echo.

:: 检查并清理被占用的 8000 端口
echo 正在检查并清理 8000 端口残留进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "0.0:8000 127.0.0.1:8000"') do (
    taskkill /F /PID %%a > nul 2> nul
)

:: 启动后端
echo [2/3] 正在后台启动后端服务 (FastAPI)...
start "AI-Backend" cmd /k "chcp 65001 > nul && cd /d %~dp0backend && ..\.venv\Scripts\activate && uvicorn app:app --host 127.0.0.1 --port 8000 --reload"        

:: 启动 RQ Worker (Celery 替代方案) 处理排队的任务
echo [3/4] 正在后台启动 RQ Worker 任务处理进程...
start "AI-Worker" cmd /k "chcp 65001 > nul && cd /d %~dp0backend && ..\.venv\Scripts\activate && set PYTHONPATH=. && python -m worker.run_worker"

:: 等待几秒
timeout /t 3 /nobreak > nul

:: 启动前端
echo [4/4] 正在启动前端服务 (Vite)...
start "AI-Frontend" cmd /k "chcp 65001 > nul && cd /d %~dp0frontend && npm run dev"                                                                             
echo.
echo ======================================================
echo  服务启动中！
echo  - 后端接口: http://127.0.0.1:8000
echo  - 前端页面: http://127.0.0.1:5173 (请根据终端实际输出确认端口)
echo ======================================================
echo.
pause
