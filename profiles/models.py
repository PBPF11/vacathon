from django.conf import settings
from django.db import models
from django.utils import timezone

from events.models import Event


class UserProfile(models.Model):
    """Extends the built-in user model with profile and preference data."""

    DISTANCE_CHOICES = [
        ("5K", "5K"),
        ("10K", "10K"),
        ("21K", "Half Marathon"),
        ("42K", "Marathon"),
        ("ULTRA", "Ultra Marathon"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    avatar_url = models.URLField(blank=True)
    favorite_distance = models.CharField(max_length=12, choices=DISTANCE_CHOICES, blank=True)
    emergency_contact_name = models.CharField(max_length=120, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    instagram_handle = models.CharField(max_length=80, blank=True)
    strava_profile = models.URLField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self) -> str:
        return f"{self.user.username} profile"

    @property
    def full_display_name(self) -> str:
        if self.display_name:
            return self.display_name
        full_name = self.user.get_full_name()
        return full_name or self.user.username

    @property
    def completed_races(self) -> int:
        return self.history.filter(status=UserRaceHistory.Status.COMPLETED).count()


class UserRaceHistory(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        REGISTERED = "registered", "Registered"
        COMPLETED = "completed", "Completed"
        DNF = "dnf", "Did Not Finish"
        DNS = "dns", "Did Not Start"
        UPCOMING = "upcoming", "Upcoming"

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="history",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="participant_history",
    )
    category = models.CharField(max_length=50, blank=True)
    registration_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    bib_number = models.CharField(max_length=20, blank=True)
    finish_time = models.DurationField(null=True, blank=True)
    medal_awarded = models.BooleanField(default=False)
    certificate_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-registration_date"]
        unique_together = ("profile", "event", "category")

    def __str__(self) -> str:
        return f"{self.profile.full_display_name} - {self.event.title}"


class RunnerAchievement(models.Model):
    """Spotlight achievements the runner is proud of."""

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="achievements",
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    achieved_on = models.DateField(null=True, blank=True)
    link = models.URLField(blank=True)

    class Meta:
        ordering = ["-achieved_on", "title"]

    def __str__(self) -> str:
        return f"{self.profile.full_display_name} - {self.title}"


