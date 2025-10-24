from django.contrib import admin

from .models import EventRegistration


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "reference_code",
        "user",
        "event",
        "category",
        "status",
        "payment_status",
        "created_at",
    )
    list_filter = ("status", "payment_status", "event")
    search_fields = ("reference_code", "user__username", "event__title")
    readonly_fields = ("reference_code", "created_at", "updated_at", "confirmed_at", "cancelled_at")
