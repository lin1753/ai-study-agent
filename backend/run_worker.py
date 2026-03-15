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

import sys
from redis import Redis
from rq.worker import SimpleWorker

if __name__ == '__main__':
    redis_conn = Redis(host='localhost', port=6379, db=0)
    print("Starting RQ SimpleWorker on Windows...")
    worker = SimpleWorker(['ai_study_tasks'], connection=redis_conn)
    worker.work()
