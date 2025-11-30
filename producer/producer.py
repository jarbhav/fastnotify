'''
Adds a job in a redis queue
'''

import os
import redis.asyncio as redis
import json
import uuid

class AsyncProducer:
    def __init__(self):
        host = os.getenv('REDIS_HOST', 'localhost')
        port = int(os.getenv('REDIS_PORT', '6379'))
        self.r = redis.Redis(host=host, port=port)
    
    async def add_job(self, job: dict):
        job_id = str(uuid.uuid1())
        job.update({"id": job_id})
        res = await self.r.lpush('job_queue', json.dumps(job))
        # set initial status
        try:
            await self.r.set(f"job_status:{job_id}", json.dumps({"status": "queued"}), ex=3600)
        except Exception:
            # non-fatal: queue push succeeded, status write failed
            pass
        return {"result": res, "job_id": job_id}