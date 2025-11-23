from typing import Union

from fastapi import FastAPI, status
from pydantic import BaseModel
from enum import IntEnum

from producer.producer import AsyncProducer
from consumers.redis_client import get_job_status

app = FastAPI()
jq = AsyncProducer()

class JobEnum(IntEnum):
    email = 1
    slack = 2

class Task(BaseModel):
    name: str
    job_tpe: JobEnum
    message: str

@app.get("/")
def read_root():
    return "Welcome to FastNotify"


@app.post("/notifications", status_code=status.HTTP_202_ACCEPTED)
async def add_task(task: Task):
    # add to redis queue
    res = await jq.add_job(task.model_dump())
    return res


@app.get("/status/{job_id}")
async def job_status(job_id: str):
    """Return job status stored in Redis under `job_status:<job_id>`"""
    st = await get_job_status(job_id)
    if st is None:
        return {"job_id": job_id, "status": "not_found"}
    return {"job_id": job_id, **st}