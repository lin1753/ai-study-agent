import os
import multiprocessing
if os.name == 'nt':
    original_get_context = multiprocessing.get_context
    def patched_get_context(method=None):
        try:
            return original_get_context(method)
        except ValueError:
            return original_get_context('spawn')
    multiprocessing.get_context = patched_get_context

import redis
from rq import Queue

# 默认连接到 localhost:6379, db 0
redis_conn = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
task_queue = Queue('ai_study_tasks', connection=redis_conn, default_timeout=3600)  # 考虑大文件可能解析较慢，超时设为1小时
