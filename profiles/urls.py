from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = "profiles"

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("admin-dashboard/", views.AdminDashboardView.as_view(), name="admin-dashboard"),
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("edit/", views.ProfileUpdateView.as_view(), name="edit"),
    path("settings/", views.AccountSettingsView.as_view(), name="settings"),
    path("api/profile/", views.profile_json, name="profile-json"),
    path("api/achievements/", views.achievements_api, name="achievements"),
    path("api/achievements/<int:achievement_id>/", views.delete_achievement, name="achievement-delete"),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='profiles:login'), name='logout'),

    # Admin Event
    path("admin/events/", views.admin_event_list, name="admin-event-list"),
    path("admin/events/add/", views.admin_event_add, name="admin-event-add"),
    path("admin/events/edit/<int:event_id>/", views.admin_event_edit, name="admin-event-edit"),
    path("admin/events/delete/<int:event_id>/", views.admin_event_delete, name="admin-event-delete"),
    
    # Admin Participants
    path("admin/participants/", views.admin_participant_list, name="admin-participant-list"),
    path("admin/participants/confirm/<int:participant_id>/", views.admin_participant_confirm, name="admin-participant-confirm"),
    path("admin/participants/delete/<int:participant_id>/", views.admin_participant_delete, name="admin-participant-delete"),
    
    # Admin Forum
    path("admin/forum/", views.admin_forum, name="admin-forum"),
    path("admin/forum/delete/<int:post_id>/", views.admin_forum_delete, name="admin-forum-delete"),
    path("admin/forum/pinned/<int:post_id>/", views.admin_forum_pinned, name="admin-forum-pinned"),
    path("admin/forum/resolve/<int:report_id>/", views.admin_forum_resolve, name="admin-forum-resolve"),
]