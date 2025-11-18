'''
Adds a job in a redis queue
'''

import redis
import json
import uuid

class Producer:
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379)
    
    def add_job(self, job: dict):
        job_id = uuid.uuid1()
        job.update({"id": str(job_id)})
        res = self.r.lpush('job_queue', json.dumps(job))
        return {"result": res, "job_id": job_id}