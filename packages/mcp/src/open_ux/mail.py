from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from open_ux.auth import IssuedInvite
    from open_ux.settings import Settings

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"
INVITE_SUBJECT = "Your Open UX invite"


def mail_configured(settings: Settings) -> bool:
    return bool(
        settings.mail_provider
        and settings.mail_api_key
        and settings.mail_from
    )


def _invite_body(*, redeem_url: str, expires_at: str) -> str:
    return (
        "Your Open UX invite is ready.\n\n"
        f"Redeem (one time): {redeem_url}\n\n"
        f"This link expires {expires_at}.\n\n"
        "After redeem you get a uxmcp_ bearer for https://open-ux.dev/mcp. "
        "Store it in your MCP client — it is shown once.\n"
    )


def _send_resend(*, to: str, subject: str, text: str, settings: Settings) -> None:
    payload = json.dumps(
        {
            "from": settings.mail_from,
            "to": [to],
            "subject": subject,
            "text": text,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        RESEND_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.mail_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30):
        return


def send_invite_email(
    issued: IssuedInvite, *, settings: Settings | None = None
) -> bool:
    """Best-effort invite delivery. Returns True when sent, False if skipped or failed."""
    from open_ux.settings import Settings as SettingsCls

    settings = settings or SettingsCls.load()
    if not mail_configured(settings):
        return False
    provider = settings.mail_provider.lower()
    text = _invite_body(redeem_url=issued.redeem_url, expires_at=issued.expires_at)
    try:
        if provider == "resend":
            _send_resend(
                to=issued.email,
                subject=INVITE_SUBJECT,
                text=text,
                settings=settings,
            )
        else:
            logger.warning("invite mail skipped: unknown provider %r", provider)
            return False
    except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, TimeoutError) as exc:
        logger.warning(
            "invite mail failed for %s via %s: %s",
            issued.email,
            provider,
            exc,
        )
        return False
    return True
