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
from rq import Worker, Queue, SimpleWorker
from redis_client import redis_conn

listen = ['ai_study_tasks']

if __name__ == '__main__':
    queues = [Queue(name, connection=redis_conn) for name in listen]
    if os.name == 'nt':
        print("Using SimpleWorker (Sync) for Windows local development.")
        worker = SimpleWorker(queues, connection=redis_conn)
    else:
        worker = Worker(queues, connection=redis_conn)

    print("Worker is listening for tasks...")
    worker.work()
