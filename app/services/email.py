from typing import Optional, Tuple
from email.message import EmailMessage
from aiosmtplib import SMTP
from aiosmtplib.errors import SMTPConnectError, SMTPException
from ..config import settings
import asyncio

SMTP_HOST = settings.smtp_host
SMTP_PORT = settings.smtp_port
SMTP_USER = settings.smtp_user
SMTP_PASS = settings.smtp_pass
SMTP_FROM = settings.smtp_from

def email_enabled() -> bool:
    return all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM])

async def send_email_async(to: str, subject: str, body: str) -> Tuple[bool, Optional[str]]:
    if not email_enabled():
        print("[Email Service] Skipped: Email service is not configured.")
        return False, "Email service is not configured."
    
    print(f"[Email Service] Attempting to send email to {to}...")
    
    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        async with SMTP(hostname=SMTP_HOST, port=SMTP_PORT, start_tls=True, timeout=20) as client:
            await client.login(SMTP_USER, SMTP_PASS)
            await client.send_message(msg)
        print(f"[Email Service] Successfully dispatched email to {to}.")
        return True, None
    except SMTPException as e:
        error_message = f"Failed to send email to {to}: {e}"
        print(f"[Email Error] {error_message}")
        return False, error_message
    except asyncio.TimeoutError:
        error_message = f"Timeout sending email to {to}."
        print(f"[Email Error] {error_message}")
        return False, error_message
    except Exception as e:
        error_message = f"An unexpected error occurred while sending email to {to}: {e}"
        print(f"[Email Error] {error_message}")
        return False, error_message