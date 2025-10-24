from django.contrib import admin

from .models import Event, EventCategory


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ("display_name", "distance_km")
    ordering = ("distance_km",)
    search_fields = ("display_name",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "city",
        "start_date",
        "status",
        "registration_deadline",
        "is_registration_open",
    )
    list_filter = ("status", "city", "start_date")
    search_fields = ("title", "description", "city")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("categories",)

    @admin.display(boolean=True)
    def is_registration_open(self, obj):
        return obj.is_registration_open
