
from django.urls import path

from .views import (
    MyRegistrationsView,
    RegistrationDetailView,
    RegistrationStartView,
    my_registrations_json,
    register_ajax,
)

app_name = "registrations"

urlpatterns = [
    path("events/<slug:slug>/register/", RegistrationStartView.as_view(), name="start"),
    path("events/<slug:slug>/register/ajax/", register_ajax, name="register-ajax"),
    path("account/registrations/", MyRegistrationsView.as_view(), name="mine"),
    path(
        "account/registrations/<slug:reference>/",
        RegistrationDetailView.as_view(),
        name="detail",
    ),
    path("account/registrations/api/", my_registrations_json, name="mine-json"),
]
