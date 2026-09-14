from __future__ import annotations

import logging
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from html import escape
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from open_ux.auth import IssuedInvite
    from open_ux.settings import Settings

logger = logging.getLogger(__name__)

RESEND_SMTP_HOST = "smtp.resend.com"
RESEND_SMTP_PORT = 465
RESEND_SMTP_STARTTLS_PORT = 587
RESEND_SMTP_USER = "resend"
INVITE_SUBJECT = "Your Open UX invite"
DEFAULT_PUBLIC_URL = "https://open-ux.dev"

# F3 tokens (packages/web/src/styles.css)
_COLOR_PAPER = "#F9F6F2"
_COLOR_CARD = "#ffffff"
_COLOR_INK = "#1F1B16"
_COLOR_MUTED = "#6A6056"
_COLOR_LINE = "#DED4C8"
_COLOR_PIP = "#FF4B00"
_COLOR_PIP_SOFT = "#FFECE0"
_FONT = '"IBM Plex Sans", ui-sans-serif, system-ui, sans-serif'


def mail_configured(settings: Settings) -> bool:
    return bool(
        settings.mail_provider
        and settings.mail_api_key
        and settings.mail_from
    )


def mail_not_sent_hint(*, configured: bool) -> str:
    """Operator-facing reason when approval succeeded but mail did not send."""
    if configured:
        return (
            "Email not sent — delivery failed. "
            "Send the redeem_url above yourself."
        )
    return (
        "Email not sent — mail isn't configured. "
        "Send the redeem_url above yourself."
    )


def _public_base(settings: Settings) -> str:
    return settings.public_url or DEFAULT_PUBLIC_URL


def _format_expires(expires_at: str) -> str:
    try:
        dt = datetime.fromisoformat(expires_at)
        return dt.strftime("%d %b %Y").replace(" 0", " ")
    except ValueError:
        return expires_at


def _invite_body_text(*, redeem_url: str, expires_at: str, public_base: str) -> str:
    expires_label = _format_expires(expires_at)
    return (
        "Your Open UX invite is ready.\n\n"
        f"Redeem (one time): {redeem_url}\n\n"
        f"This link expires {expires_label}.\n\n"
        f"After redeem you get a uxmcp_ key for {public_base}/mcp. "
        "Store it in your MCP client — it is shown once.\n"
    )


def _invite_body_html(*, redeem_url: str, expires_at: str, public_base: str) -> str:
    safe_url = escape(redeem_url, quote=True)
    expires_label = escape(_format_expires(expires_at))
    pip_url = escape(f"{public_base}/pip.svg", quote=True)
    icon_url = escape(f"{public_base}/icon.png", quote=True)
    site_url = escape(public_base, quote=True)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>{escape(INVITE_SUBJECT)}</title>
</head>
<body style="margin:0;padding:0;background:{_COLOR_PAPER};">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:{_COLOR_PAPER};">
    <tr>
      <td align="center" style="padding:32px 16px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:520px;background:{_COLOR_CARD};border:1px solid {_COLOR_LINE};border-radius:6px;overflow:hidden;">
          <tr>
            <td align="center" style="padding:20px 28px 12px;background:{_COLOR_PIP_SOFT};border-bottom:1px solid {_COLOR_LINE};">
              <img src="{pip_url}" width="140" height="110" alt="Pip, Open UX mascot" style="display:block;border:0;margin:0 auto;">
            </td>
          </tr>
          <tr>
            <td style="padding:20px 28px 8px;font-family:{_FONT};">
              <table role="presentation" cellspacing="0" cellpadding="0">
                <tr>
                  <td style="padding-right:8px;vertical-align:middle;">
                    <span style="display:inline-block;width:8px;height:8px;border-radius:999px;background:{_COLOR_PIP};"></span>
                  </td>
                  <td style="font-size:13px;line-height:20px;color:{_COLOR_MUTED};vertical-align:middle;">
                    Invite · one key after redeem
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 28px 0;font-family:{_FONT};">
              <h1 style="margin:0;font-size:28px;line-height:34px;font-weight:600;color:{_COLOR_INK};">
                Your invite is ready
              </h1>
            </td>
          </tr>
          <tr>
            <td style="padding:12px 28px 0;font-family:{_FONT};font-size:15px;line-height:22px;color:{_COLOR_MUTED};">
              Open the link below to redeem your one-time invite and copy your
              <span style="font-family:monospace;color:{_COLOR_INK};">uxmcp_</span>
              key for the hosted catalog.
            </td>
          </tr>
          <tr>
            <td style="padding:20px 28px 0;font-family:{_FONT};font-size:15px;line-height:22px;">
              <a href="{safe_url}" style="color:{_COLOR_PIP};font-weight:600;text-decoration:underline;">Redeem invite</a>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 28px 0;font-family:{_FONT};font-size:13px;line-height:20px;color:{_COLOR_MUTED};">
              Link expires {expires_label}. Shown once — store the key in your MCP client.
            </td>
          </tr>
          <tr>
            <td style="padding:20px 28px 28px;font-family:{_FONT};font-size:12px;line-height:18px;color:{_COLOR_MUTED};border-top:1px solid {_COLOR_LINE};">
              <img src="{icon_url}" width="20" height="20" alt="" style="vertical-align:middle;margin-right:6px;border-radius:4px;">
              <a href="{site_url}" style="color:{_COLOR_INK};text-decoration:none;font-weight:600;">Open UX</a>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _invite_message(
    *, to: str, subject: str, text: str, html: str, mail_from: str
) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = mail_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    return msg


def _smtp_login_and_send(
    smtp: smtplib.SMTP, msg: EmailMessage, settings: Settings
) -> None:
    smtp.login(RESEND_SMTP_USER, settings.mail_api_key)
    smtp.send_message(msg)


def _send_resend_starttls(
    msg: EmailMessage, settings: Settings, context: ssl.SSLContext
) -> None:
    with smtplib.SMTP(
        RESEND_SMTP_HOST, RESEND_SMTP_STARTTLS_PORT, timeout=30
    ) as smtp:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()
        _smtp_login_and_send(smtp, msg, settings)


def _send_resend(
    *, to: str, subject: str, text: str, html: str, settings: Settings
) -> None:
    # Fly egress to api.resend.com is blocked (Cloudflare 1010). SMTP still
    # works from the same machines: smtp.resend.com:465 / :587.
    msg = _invite_message(
        to=to,
        subject=subject,
        text=text,
        html=html,
        mail_from=settings.mail_from,
    )
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(
            RESEND_SMTP_HOST,
            RESEND_SMTP_PORT,
            context=context,
            timeout=30,
        ) as smtp:
            _smtp_login_and_send(smtp, msg, settings)
    except (TimeoutError, OSError, smtplib.SMTPException) as exc:
        # SMTPException subclasses OSError. Only retry STARTTLS when the SMTPS
        # socket never came up — not on auth or recipient rejections.
        if isinstance(exc, smtplib.SMTPException) and not isinstance(
            exc, (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected)
        ):
            raise
        _send_resend_starttls(msg, settings, context)


def send_invite_email(
    issued: IssuedInvite, *, settings: Settings | None = None
) -> bool:
    """Best-effort invite delivery. Returns True when sent, False if skipped or failed."""
    from open_ux.settings import Settings as SettingsCls

    settings = settings or SettingsCls.load()
    if not mail_configured(settings):
        return False
    provider = settings.mail_provider.lower()
    public_base = _public_base(settings)
    text = _invite_body_text(
        redeem_url=issued.redeem_url,
        expires_at=issued.expires_at,
        public_base=public_base,
    )
    html = _invite_body_html(
        redeem_url=issued.redeem_url,
        expires_at=issued.expires_at,
        public_base=public_base,
    )
    try:
        if provider == "resend":
            _send_resend(
                to=issued.email,
                subject=INVITE_SUBJECT,
                text=text,
                html=html,
                settings=settings,
            )
        else:
            logger.warning("invite mail skipped: unknown provider %r", provider)
            return False
    except (
        smtplib.SMTPException,
        OSError,
        TimeoutError,
        RuntimeError,
    ) as exc:
        logger.warning(
            "invite mail failed for %s via %s: %s",
            issued.email,
            provider,
            exc,
        )
        return False
    return True
