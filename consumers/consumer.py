import asyncio
import json
import os
import redis.asyncio as redis
import logging

from .redis_client import set_job_status
from .slack_service import send_slack_message   # Async slack function
from .email_service import send_email_async

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


async def wait_for_redis(host: str, port: int, timeout: float = 30.0) -> redis.Redis:
    """Wait for Redis to become available before returning a connection.
    
    Retries every second for up to `timeout` seconds.
    """
    start = asyncio.get_event_loop().time()
    deadline = start + timeout
    attempt = 0
    
    while asyncio.get_event_loop().time() < deadline:
        attempt += 1
        try:
            r = redis.Redis(host=host, port=port, decode_responses=True)
            await r.ping()  # Test connection
            logging.info(f"Connected to Redis at {host}:{port} (attempt {attempt})")
            return r
        except Exception as e:
            elapsed = asyncio.get_event_loop().time() - start
            if elapsed >= timeout - 1:
                raise ConnectionError(f"Failed to connect to Redis at {host}:{port} after {timeout}s: {e}")
            logging.warning(f"Redis not ready (attempt {attempt}): {e}. Retrying in 1s...")
            await asyncio.sleep(1)
    
    raise ConnectionError(f"Timeout waiting for Redis at {host}:{port}")


async def process_messages():
    host = os.getenv('REDIS_HOST', 'localhost')
    port = int(os.getenv('REDIS_PORT', '6379'))
    
    # Wait for Redis to be ready
    r = await wait_for_redis(host, port)

    while True:
        # Async blocking pop, wait for new job from 'job_queue'
        task = await r.brpop('job_queue')
        message_info = json.loads(task[1])

        job_id = message_info.get('id')
        logging.info(f"Processing message ID: {job_id}")

        # mark as processing
        try:
            if job_id:
                await set_job_status(job_id, 'processing')
        except Exception:
            logging.exception("Failed to set processing status")

        msg = message_info.get("message", "No message content")

        try:
            job_tpe = message_info.get('job_tpe')
            if job_tpe == 1:
                # Attempt to send email; if details are missing this may raise
                sender = message_info.get('sender')
                receiver = message_info.get('receiver')
                subject = message_info.get('subject', '')
                password = message_info.get('password')
                await send_email_async(sender, receiver, subject, msg, password)
            else:
                await send_slack_message(msg)

            # mark complete
            if job_id:
                await set_job_status(job_id, 'completed')
            logging.info(f"Completed message ID: {job_id}")
        except Exception as e:
            logging.exception(f"Error processing job {job_id}: {e}")
            if job_id:
                await set_job_status(job_id, 'failed', {"error": str(e)})

if __name__ == "__main__":
    asyncio.run(process_messages())
