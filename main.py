from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel
from enum import IntEnum

app = FastAPI()

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


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/notifications")
def add_task(task: Task):
    # add to redis queue
    pass