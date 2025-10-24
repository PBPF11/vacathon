from django.urls import reverse

from .models import Notification


def send_notification(
    *,
    recipient,
    title: str,
    message: str,
    category: Notification.Category = Notification.Category.SYSTEM,
    url_name: str | None = None,
    url_kwargs: dict | None = None,
    link_url: str | None = None,
) -> Notification:
    """Create a notification entry for the given recipient."""

    if url_name and not link_url:
        try:
            link_url = reverse(url_name, kwargs=url_kwargs or {})
        except Exception:
            link_url = None

    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        category=category,
        link_url=link_url or "",
    )
