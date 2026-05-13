import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_pdf_email(
    *,
    to_addrs: list[str],
    subject: str,
    body_text: str,
    pdf_bytes: bytes,
    filename: str,
) -> None:
    if not settings.smtp_configured:
        logger.warning("SMTP not configured; skipping email to %s", to_addrs)
        return

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = ", ".join(to_addrs)
    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    part = MIMEApplication(pdf_bytes, _subtype="pdf")
    part.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(part)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.sendmail(settings.smtp_from, to_addrs, msg.as_string())
