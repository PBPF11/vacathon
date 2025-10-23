from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from events.models import Event


class ForumThread(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="threads")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="forum_threads",
    )
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, editable=False)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(default=timezone.now)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-is_pinned", "-last_activity_at"]
        indexes = [
            models.Index(fields=["event"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:130]
            slug = base_slug or "thread"
            counter = 1
            while ForumThread.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
        else:
            slug = self.slug
        self.slug = slug
        super().save(*args, **kwargs)

    def touch(self):
        self.last_activity_at = timezone.now()
        self.save(update_fields=["last_activity_at"])


class ForumPost(models.Model):
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="forum_posts",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="liked_forum_posts", blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["thread", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Post by {self.author} on {self.thread}"

    @property
    def like_count(self) -> int:
        return self.likes.count()


class PostReport(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="forum_reports",
    )
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("post", "reporter")

    def __str__(self) -> str:
        return f"Report by {self.reporter} on {self.post_id}"
