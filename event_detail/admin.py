from django.contrib import admin

from .models import AidStation, EventDocument, EventSchedule, RouteSegment


class ScheduleInline(admin.TabularInline):
    model = EventSchedule
    extra = 1


class AidStationInline(admin.TabularInline):
    model = AidStation
    extra = 1


class RouteSegmentInline(admin.TabularInline):
    model = RouteSegment
    extra = 1


@admin.register(EventSchedule)
class EventScheduleAdmin(admin.ModelAdmin):
    list_display = ("title", "event", "start_time", "end_time")
    list_filter = ("event",)
    search_fields = ("title", "event__title")


@admin.register(AidStation)
class AidStationAdmin(admin.ModelAdmin):
    list_display = ("name", "event", "kilometer_marker", "is_medical")
    list_filter = ("event", "is_medical")
    search_fields = ("name", "event__title")


@admin.register(RouteSegment)
class RouteSegmentAdmin(admin.ModelAdmin):
    list_display = ("event", "order", "title", "distance_km", "elevation_gain")
    list_filter = ("event",)
    search_fields = ("title", "event__title")
    ordering = ("event", "order")


@admin.register(EventDocument)
class EventDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "event", "document_type", "uploaded_at")
    list_filter = ("document_type", "event")
    search_fields = ("title", "event__title")
