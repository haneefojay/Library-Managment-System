from typing import Optional
from email.message import EmailMessage
from aiosmtplib import SMTP
from ..config import settings

SMTP_HOST = settings.smtp_host
SMTP_PORT = settings.smtp_port
SMTP_USER = settings.smtp_user
SMTP_PASS = settings.smtp_pass
SMTP_FROM = settings.smtp_from

def email_enabled() -> bool:
    return all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM])

async def send_email_async(to: str, subject: str, body: str) -> Optional[bool]:
    if not email_enabled():
        return None
    
    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    
    async with SMTP(hostname=SMTP_HOST, port=SMTP_PORT, start_tls=True) as client:
        await client.connect()
        await client.starttls()
        await client.login(SMTP_USER, SMTP_PASS)
        await client.send_message(msg)        
    
    return True