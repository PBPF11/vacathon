from django.db import models
from django.urls import NoReverseMatch, reverse
from django.utils.text import slugify


class EventCategory(models.Model):
    """Represents a single race category inside an event (e.g., 5K, 21K)."""

    name = models.CharField(max_length=100, unique=True)
    distance_km = models.DecimalField(max_digits=5, decimal_places=2)
    display_name = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ["distance_km"]

    def __str__(self) -> str:
        return self.display_name


class Event(models.Model):
    """A marathon event that can host multiple race categories."""

    class Status(models.TextChoices):
        UPCOMING = "upcoming", "Upcoming"
        ONGOING = "ongoing", "Ongoing"
        COMPLETED = "completed", "Completed"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, editable=False)
    description = models.TextField()
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=120, default="Indonesia")
    venue = models.CharField(max_length=150, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    registration_open_date = models.DateField(blank=True, null=True)
    registration_deadline = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPCOMING,
    )
    popularity_score = models.PositiveIntegerField(default=0)
    participant_limit = models.PositiveIntegerField(default=0)
    registered_count = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)
    banner_image = models.URLField(blank=True)
    categories = models.ManyToManyField(EventCategory, related_name="events", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_date", "title"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["start_date"]),
            models.Index(fields=["city"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        try:
            return reverse("event_detail:detail", kwargs={"slug": self.slug})
        except NoReverseMatch:
            return ""

    @property
    def is_registration_open(self) -> bool:
        from django.utils import timezone

        today = timezone.localdate()
        open_date = self.registration_open_date or today
        return (
            open_date <= today <= self.registration_deadline
            and self.status != self.Status.COMPLETED
        )

    @property
    def duration_days(self) -> int | None:
        if self.end_date:
            return (self.end_date - self.start_date).days + 1
        return None

