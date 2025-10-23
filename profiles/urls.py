from django.urls import path

from .views import (
    AccountSettingsView,
    DashboardView,
    ProfileUpdateView,
    achievements_api,
    delete_achievement,
    profile_json,
)

app_name = "profiles"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("edit/", ProfileUpdateView.as_view(), name="edit"),
    path("settings/", AccountSettingsView.as_view(), name="settings"),
    path("api/profile/", profile_json, name="profile-json"),
    path("api/achievements/", achievements_api, name="achievements"),
    path("api/achievements/<int:achievement_id>/", delete_achievement, name="achievement-delete"),
]
