import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from events.models import Event, EventCategory
from profiles.models import UserProfile, UserRaceHistory


class EventRegistration(models.Model):
    """Represents a user's registration request for a specific event."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        CONFIRMED = "confirmed", "Confirmed"
        WAITLISTED = "waitlisted", "Waitlisted"
        CANCELLED = "cancelled", "Cancelled"
        REJECTED = "rejected", "Rejected"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_code = models.CharField(max_length=18, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_registrations",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        related_name="registrations",
        null=True,
    )
    distance_label = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=30)
    emergency_contact_name = models.CharField(max_length=120)
    emergency_contact_phone = models.CharField(max_length=30)
    medical_notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    payment_status = models.CharField(
        max_length=15,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    form_payload = models.JSONField(default=dict, blank=True)
    decision_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "event")
        indexes = [
            models.Index(fields=["event", "status"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.event.title} ({self.status})"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        previous_status = None
        previous_payment_status = None
        if not is_new and self.pk:
            previous = (
                EventRegistration.objects.filter(pk=self.pk)
                .values("status", "payment_status")
                .first()
            )
            if previous:
                previous_status = previous["status"]
                previous_payment_status = previous["payment_status"]
        if not self.reference_code:
            self.reference_code = f"VAC-{uuid.uuid4().hex[:10].upper()}"
        if self.status == self.Status.CONFIRMED and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        if self.status == self.Status.CANCELLED and not self.cancelled_at:
            self.cancelled_at = timezone.now()
        super().save(*args, **kwargs)
        self.sync_history()
        self.update_event_counter()
        self._dispatch_notifications(is_new=is_new, old_status=previous_status, old_payment=previous_payment_status)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.update_event_counter()

    def update_event_counter(self):
        active_statuses = [
            self.Status.PENDING,
            self.Status.CONFIRMED,
            self.Status.WAITLISTED,
        ]
        count = EventRegistration.objects.filter(
            event=self.event, status__in=active_statuses
        ).count()
        Event.objects.filter(pk=self.event.pk).update(registered_count=count)

    def sync_history(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        distance_label = self.category.display_name if self.category else self.distance_label
        if not distance_label:
            distance_label = "Open Category"
        history, _ = UserRaceHistory.objects.get_or_create(
            profile=profile,
            event=self.event,
            category=distance_label,
            defaults={
                "status": UserRaceHistory.Status.REGISTERED,
                "registration_date": timezone.now().date(),
            },
        )

        if self.status == self.Status.CONFIRMED:
            history.status = UserRaceHistory.Status.UPCOMING
        elif self.status == self.Status.CANCELLED:
            history.status = UserRaceHistory.Status.DNS
        elif self.status == self.Status.REJECTED:
            history.status = UserRaceHistory.Status.DNS
        else:
            history.status = UserRaceHistory.Status.REGISTERED
        history.save(update_fields=["status", "updated_at"])

    @property
    def is_active(self) -> bool:
        return self.status in {
            self.Status.PENDING,
            self.Status.CONFIRMED,
            self.Status.WAITLISTED,
        }

    @property
    def is_confirmed(self) -> bool:
        return self.status == self.Status.CONFIRMED

    def _dispatch_notifications(self, *, is_new: bool, old_status: str | None, old_payment: str | None):
        from notifications.utils import send_notification
        from notifications.models import Notification

        detail_kwargs = {"reference": self.reference_code}

        if is_new:
            if self.status == self.Status.WAITLISTED:
                send_notification(
                    recipient=self.user,
                    title=f"Waitlist for {self.event.title}",
                    message=(
                        "The event has reached capacity but we've placed you on the waitlist. "
                        "We'll notify you if a slot opens."
                    ),
                    category=Notification.Category.REGISTRATION,
                    url_name="registrations:detail",
                    url_kwargs=detail_kwargs,
                )
            else:
                send_notification(
                    recipient=self.user,
                    title=f"Registration received for {self.event.title}",
                    message="Your registration is pending confirmation. We'll keep you posted.",
                    category=Notification.Category.REGISTRATION,
                    url_name="registrations:detail",
                    url_kwargs=detail_kwargs,
                )
            return

        if old_status and old_status != self.status:
            if self.status == self.Status.CONFIRMED:
                send_notification(
                    recipient=self.user,
                    title=f"You're confirmed for {self.event.title}",
                    message="See your registration summary for race-day details.",
                    category=Notification.Category.REGISTRATION,
                    url_name="registrations:detail",
                    url_kwargs=detail_kwargs,
                )
            elif self.status == self.Status.REJECTED:
                send_notification(
                    recipient=self.user,
                    title=f"Registration update for {self.event.title}",
                    message="We were unable to confirm your registration. Contact support for more details.",
                    category=Notification.Category.REGISTRATION,
                    url_name="registrations:detail",
                    url_kwargs=detail_kwargs,
                )
            elif self.status == self.Status.CANCELLED:
                send_notification(
                    recipient=self.user,
                    title=f"Registration cancelled - {self.event.title}",
                    message="Your registration has been cancelled. If this is unexpected please reach out.",
                    category=Notification.Category.REGISTRATION,
                    url_name="registrations:detail",
                    url_kwargs=detail_kwargs,
                )

        if (
            old_payment
            and old_payment != self.payment_status
            and self.payment_status == self.PaymentStatus.PAID
        ):
            send_notification(
                recipient=self.user,
                title="Payment received",
                message=f"We've recorded your payment for {self.event.title}. See the summary for confirmation.",
                category=Notification.Category.REGISTRATION,
                url_name="registrations:detail",
                url_kwargs=detail_kwargs,
            )
