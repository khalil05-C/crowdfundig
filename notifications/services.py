from django.conf import settings
from django.core.mail import send_mail

from .models import Notification


def send_sms_notification(phone_number, message):
    """Mock SMS sender prepared for future Twilio or provider integration."""
    return {
        "sent": bool(phone_number),
        "phone_number": phone_number,
        "message": message,
    }


def send_email_notification(user, title, message):
    """Send a notification email using Django's configured email backend."""
    if not user.email:
        return 0

    return send_mail(
        subject=title,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@fundrise.ma"),
        recipient_list=[user.email],
        fail_silently=True,
    )


def create_notification(recipient, notification_type, title, message, link=""):
    """Create an in-app notification and deliver it using user preferences."""
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
    )

    preference = getattr(recipient, "notification_preference", "email")

    if preference in ("email", "both"):
        send_email_notification(recipient, title, message)

    if preference in ("phone", "both"):
        send_sms_notification(getattr(recipient, "phone", ""), message)

    return notification
