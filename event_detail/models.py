from django.db import models

from events.models import Event


class EventSchedule(models.Model):
    """Represents a schedule item related to a marathon event (e.g., expo, race start)."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="schedules")
    title = models.CharField(max_length=150)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self) -> str:
        return f"{self.event.title} - {self.title}"


class AidStation(models.Model):
    """Aid station or checkpoint details for an event route."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="aid_stations")
    name = models.CharField(max_length=120)
    kilometer_marker = models.DecimalField(max_digits=5, decimal_places=2)
    supplies = models.CharField(max_length=200, help_text="Key supplies provided (water, gels, medical, etc.)")
    is_medical = models.BooleanField(default=False)

    class Meta:
        ordering = ["kilometer_marker"]

    def __str__(self) -> str:
        return f"{self.name} ({self.kilometer_marker} KM)"


class RouteSegment(models.Model):
    """Detailed narrative for a section of the marathon route."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="route_segments")
    order = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=150)
    description = models.TextField()
    distance_km = models.DecimalField(max_digits=5, decimal_places=2)
    elevation_gain = models.PositiveIntegerField(default=0, help_text="Elevation gain in meters.")

    class Meta:
        ordering = ["order"]
        unique_together = ("event", "order")

    def __str__(self) -> str:
        return f"{self.event.title} - Segment {self.order}"


class EventDocument(models.Model):
    """Supporting documents like GPX files, race guide, or waivers."""

    class DocumentType(models.TextChoices):
        GPX = "gpx", "GPX Route"
        GUIDE = "guide", "Race Guide"
        BROCHURE = "brochure", "Brochure"
        OTHER = "other", "Other"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=150)
    document_url = models.URLField()
    document_type = models.CharField(max_length=20, choices=DocumentType.choices, default=DocumentType.OTHER)
    uploaded_by = models.CharField(max_length=120, default="Organizing Committee")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document_type", "title"]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_document_type_display()})"
