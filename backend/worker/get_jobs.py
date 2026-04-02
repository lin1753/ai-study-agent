from redis import Redis; from rq import Queue; q = Queue('ai_study_tasks', connection=Redis()); print(q.jobs)
