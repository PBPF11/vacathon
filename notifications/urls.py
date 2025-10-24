from django.urls import path

from .views import NotificationListView, mark_notification_read, notifications_json

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="inbox"),
    path("api/", notifications_json, name="inbox-json"),
    path("api/<int:pk>/read/", mark_notification_read, name="mark-read"),
]
