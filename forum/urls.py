from django.urls import path

from .views import (
    ForumIndexView,
    ThreadCreateView,
    ThreadDetailView,
    create_post,
    report_post,
    threads_json,
    toggle_like,
    api_thread_posts,
    create_thread_json,
    delete_thread_api,
    delete_post_api,
    api_thread_detail,
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
    path("api/threads/create/", create_thread_json, name="api-thread-create"),
    path("api/threads/<slug:slug>/", api_thread_detail, name="api-thread-detail"),
    path("api/threads/<slug:slug>/posts/", api_thread_posts, name="api-thread-posts"),
    path("api/threads/<slug:slug>/delete/", delete_thread_api, name="api-thread-delete"),
    path("api/posts/<int:post_id>/delete/", delete_post_api, name="api-post-delete"),
]
