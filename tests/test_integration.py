import asyncio
import pytest

from producer.producer import AsyncProducer
from consumers.redis_client import get_job_status
from consumers.consumer import process_messages


@pytest.mark.asyncio
async def test_enqueue_and_process_job():
    """Integration test: enqueue a job and assert it reaches 'completed' status."""

    # Start the consumer loop in background
    consumer_task = asyncio.create_task(process_messages())

    # Give the consumer a moment to start
    await asyncio.sleep(0.1)

    prod = AsyncProducer()
    job_payload = {"name": "itest", "job_tpe": 2, "message": "integration test message"}

    res = await prod.add_job(job_payload)
    job_id = res.get("job_id")
    assert job_id, "Producer did not return job_id"

    # Poll for status until completed or timeout
    timeout = 10.0
    deadline = asyncio.get_event_loop().time() + timeout
    final_status = None
    while asyncio.get_event_loop().time() < deadline:
        st = await get_job_status(job_id)
        if st:
            final_status = st.get("status")
            if final_status in ("completed", "failed"):
                break
        await asyncio.sleep(0.2)

    # Stop the consumer loop
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    assert final_status == "completed", f"Job ended with unexpected status: {final_status}"
