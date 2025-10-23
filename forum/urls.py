from django.urls import path

from .views import (
    ForumIndexView,
    ThreadCreateView,
    ThreadDetailView,
    create_post,
    report_post,
    threads_json,
    toggle_like,
)

app_name = "forum"

urlpatterns = [
    path("", ForumIndexView.as_view(), name="index"),
    path("threads/new/", ThreadCreateView.as_view(), name="thread-create"),
    path("threads/<slug:slug>/", ThreadDetailView.as_view(), name="thread-detail"),
    path("threads/<slug:slug>/posts/", create_post, name="post-create"),
    path("posts/<int:post_id>/like/", toggle_like, name="post-like"),
    path("posts/<int:post_id>/report/", report_post, name="post-report"),
    path("api/threads/", threads_json, name="threads-json"),
]
