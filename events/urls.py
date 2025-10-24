from django.urls import path

from .views import EventListView, events_json

app_name = "events"

urlpatterns = [
    path("", EventListView.as_view(), name="list"),
    path("api/", events_json, name="json"),
]
