import os
import json
import redis.asyncio as redis
from typing import Optional, Dict, Any

# Single Redis client for status operations
_REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
_REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
_r = redis.Redis(host=_REDIS_HOST, port=_REDIS_PORT, decode_responses=True)


async def set_job_status(job_id: str, status: str, meta: Optional[Dict[str, Any]] = None) -> None:
    """Set the status for a job.

    Stored under key `job_status:<job_id>` as a JSON blob: {"status": ..., "meta": ...}
    """
    key = f"job_status:{job_id}"
    payload: Dict[str, Any] = {"status": status}
    if meta is not None:
        payload["meta"] = meta
    await _r.set(key, json.dumps(payload), ex=3600)


async def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get the status JSON for a job, or None if not found."""
    key = f"job_status:{job_id}"
    val = await _r.get(key)
    if val is None:
        return None
    try:
        return json.loads(val)
    except Exception:
        return {"status": val}
