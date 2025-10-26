from django.urls import path

from .views import EventDetailView, event_availability_json, event_detail_json

app_name = "event_detail"

urlpatterns = [
    path("events/<slug:slug>/", EventDetailView.as_view(), name="detail"),
    path("events/<slug:slug>/api/", event_detail_json, name="detail-json"),
    path("events/<slug:slug>/availability/", event_availability_json, name="availability-json"),
]
