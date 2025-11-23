'''
Send slack message asynchronously
'''

import aiohttp
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

WEBHOOK = os.getenv('SLACK_WEBHOOK')


async def send_slack_message(msg: str):
    payload = {"text": msg}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(WEBHOOK, json=payload) as resp:
                if resp.status != 200:
                    logging.error(f"Slack post failed with status {resp.status}")
                    logging.error(f"Response: {await resp.text()}")
                else:
                    logging.info("Message sent successfully")
    except aiohttp.ClientError as e:
        logging.error(f"Network/client error: {e}")
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")