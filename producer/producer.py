'''
Adds a job in a redis queue
'''

import redis.asyncio as redis
import json
import uuid

class AsyncProducer:
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379)
    
    async def add_job(self, job: dict):
        job_id = str(uuid.uuid1())
        job.update({"id": job_id})
        res = await self.r.lpush('job_queue', json.dumps(job))
        # set initial status
        try:
            await self.r.set(f"job_status:{job_id}", json.dumps({"status": "queued"}), ex=60)
        except Exception:
            # non-fatal: queue push succeeded, status write failed
            pass
        return {"result": res, "job_id": job_id}