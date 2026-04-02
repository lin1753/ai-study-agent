import os
import multiprocessing
if os.name == 'nt':
    # Windows 兼容性补丁: 防止 rq 包导入时因缺失 fork 抛出错误
    original_get_context = multiprocessing.get_context
    def patched_get_context(method=None):
        try:
            return original_get_context(method)
        except ValueError:
            return original_get_context('spawn')
    multiprocessing.get_context = patched_get_context

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 安全初始化数据库架构
from core.db import engine, Base
from sqlalchemy import text
import models.database as models
try:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    print("Database tables verified.")
except Exception as e:
    print("DB Init Error:", e)

from api.routers import spaces, files, threads, chat

app = FastAPI(title="AI Study Agent V1")

# Logging Setup
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# CORS Setup - 修复 allow_credentials 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # 只有设为 False 才能使用 '*' Origins，否则浏览器会产生无声跨域报错
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(spaces.router)
app.include_router(files.router)
app.include_router(threads.router)
app.include_router(chat.router)
