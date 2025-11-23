'''
Send slack message asynchronously
'''

import aiohttp
import os

WEBHOOK = os.getenv('SLACK_WEBHOOK')


async def send_slack_message(msg: str):
    payload = {"text": msg}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(WEBHOOK, json=payload) as resp:
                if resp.status != 200:
                    print(f"Slack post failed: {resp.status}")
                    print(f"Response: {await resp.text()}")
                else:
                    print("Message sent successfully:", await resp.text())
    except aiohttp.ClientError as e:
        print(f"Network/client error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")