"""Optional email notification for daily notices."""

from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class MailConfig:
    host: str
    port: int
    user: str
    password: str
    recipients: tuple[str, ...]
    use_ssl: bool


def load_mail_config() -> MailConfig | None:
    """Read SMTP settings from environment variables."""

    host = os.getenv("SMTP_HOST", "").strip()
    port_text = os.getenv("SMTP_PORT", "").strip()
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    recipients = _split_recipients(os.getenv("MAIL_TO", ""))
    use_ssl = os.getenv("SMTP_SSL", "").strip().lower() in {"1", "true", "yes", "on"}

    if not all((host, port_text, user, password, recipients)):
        return None

    try:
        port = int(port_text)
    except ValueError:
        return None

    if not os.getenv("SMTP_SSL"):
        use_ssl = port == 465

    return MailConfig(
        host=host,
        port=port,
        user=user,
        password=password,
        recipients=recipients,
        use_ssl=use_ssl,
    )


def send_daily_email(report_path: str | Path = "daily.md") -> dict[str, object]:
    """Send daily.md by email when SMTP settings are available."""

    config = load_mail_config()
    if config is None:
        return {
            "enabled": False,
            "sent": False,
            "error": "SMTP settings are incomplete; skipped email notification.",
        }

    path = Path(report_path)
    if not path.exists():
        return {
            "enabled": True,
            "sent": False,
            "error": f"Report file not found: {path}",
        }

    subject = f"青岛农业大学每日通知摘要 - {_today_beijing()}"
    body = path.read_text(encoding="utf-8")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.user
    message["To"] = ", ".join(config.recipients)
    message.set_content(body, subtype="plain", charset="utf-8")

    try:
        if config.use_ssl:
            with smtplib.SMTP_SSL(config.host, config.port, timeout=20) as smtp:
                smtp.login(config.user, config.password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(config.host, config.port, timeout=20) as smtp:
                smtp.starttls()
                smtp.login(config.user, config.password)
                smtp.send_message(message)
    except Exception as exc:
        return {
            "enabled": True,
            "sent": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    return {
        "enabled": True,
        "sent": True,
        "error": None,
        "recipients": list(config.recipients),
    }


def _split_recipients(raw: str) -> tuple[str, ...]:
    items = raw.replace(";", ",").split(",")
    return tuple(item.strip() for item in items if item.strip())


def _today_beijing() -> str:
    try:
        now = datetime.now(ZoneInfo("Asia/Shanghai"))
    except Exception:
        now = datetime.now(timezone(timedelta(hours=8)))
    return now.strftime("%Y-%m-%d")
