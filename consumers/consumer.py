import asyncio
import json
import redis.asyncio as redis
from slack_service import send_slack_message   # Async slack function
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def process_messages():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)

    while True:
        # Async blocking pop, wait for new job from 'job_queue'
        task = await r.brpop('job_queue')
        message_info = json.loads(task[1])

        logging.info(f"Processing message ID: {message_info['id']}")

        msg = message_info.get("message", "No message content")

        # Call asynchronous slack function without blocking event loop
        await send_slack_message(msg)

if __name__ == "__main__":
    asyncio.run(process_messages())
