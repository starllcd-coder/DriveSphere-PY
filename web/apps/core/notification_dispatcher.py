from django.conf import settings
from django.core.mail import send_mail

try:
    from twilio.rest import Client
except Exception:  # pragma: no cover - optional channel
    Client = None

from apps.core.models import Notification


def dispatch_notification(
    *,
    user,
    title: str,
    message: str,
    notification_type: str = "GENERAL",
    metadata: dict | None = None,
    send_email_channel: bool = True,
    send_sms_channel: bool = False,
    send_whatsapp_channel: bool = False,
):
    note = Notification.objects.create(
        user=user,
        title=title[:255],
        message=message,
        notification_type=notification_type,
        metadata=metadata or {},
    )

    if send_email_channel and getattr(user, "email", ""):
        try:
            send_mail(
                subject=title,
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass

    should_send_twilio = bool(
        Client
        and
        settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and getattr(user, "phone_number", "")
    )
    if should_send_twilio and (send_sms_channel or send_whatsapp_channel):
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            to_phone = str(user.phone_number)

            if send_whatsapp_channel and settings.TWILIO_WHATSAPP_FROM:
                client.messages.create(
                    from_=settings.TWILIO_WHATSAPP_FROM,
                    to=f"whatsapp:{to_phone}",
                    body=f"{title}\n{message}",
                )
            elif send_sms_channel and settings.TWILIO_SMS_FROM:
                client.messages.create(
                    from_=settings.TWILIO_SMS_FROM,
                    to=to_phone,
                    body=f"{title}\n{message}",
                )
        except Exception:
            pass

    return note
