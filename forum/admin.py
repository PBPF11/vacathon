from django.contrib import admin

from .models import ForumPost, ForumThread, PostReport


class ForumPostInline(admin.TabularInline):
    model = ForumPost
    extra = 0
    fields = ("author", "content", "created_at", "parent")
    readonly_fields = ("author", "created_at")


@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    list_display = ("title", "event", "author", "is_pinned", "is_locked", "last_activity_at")
    list_filter = ("event", "is_pinned", "is_locked")
    search_fields = ("title", "body", "event__title", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ForumPostInline]


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ("thread", "author", "created_at", "like_count")
    list_filter = ("thread", "author")
    search_fields = ("content", "author__username")
    raw_id_fields = ("thread", "author", "parent")


@admin.register(PostReport)
class PostReportAdmin(admin.ModelAdmin):
    list_display = ("post", "reporter", "reason", "created_at", "resolved")
    list_filter = ("resolved",)
    search_fields = ("reason", "reporter__username", "post__content")
