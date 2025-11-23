import asyncio
from email.mime.text import MIMEText
import aiosmtplib

async def send_email_async(sender_email: str, receiver_email: str, subject: str, body: str, password: str):
    message = MIMEText(body, "plain")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    try:
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",  # Change if needed
            port=587,
            start_tls=True,
            username=sender_email,
            password=password,
        )
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

# Example usage
# asyncio.run(send_email_async("your@email.com", "recipient@email.com", "Test Subject", "Test Body", "your_password"))
