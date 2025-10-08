import random
import string
from pathlib import Path

import aiosmtplib
from email.message import EmailMessage
from os import getenv

from dotenv import load_dotenv


def create_cookie(length: int = 16) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


async def send_verification_email(to_email: str, code: str):
    load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)
    msg = EmailMessage()
    msg["From"] = getenv("SMTP_FROM")
    msg["To"] = to_email
    msg["Subject"] = "Ваш код подтверждения"
    msg.set_content(
        f"Ваш 6-значный код: {code}\nОн действителен в течении {getenv('VERIFICATION_TTL_MIN', '30')} минут.")

    host = getenv("SMTP_HOST")
    port = int(getenv("SMTP_PORT", "587"))
    user = getenv("SMTP_USER")
    pwd = getenv("SMTP_PASS")

    await aiosmtplib.send(
        msg, hostname=host, port=port, start_tls=True, username=user, password=pwd
    )
