from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.generic import DetailView
from django.urls import NoReverseMatch, reverse

from events.models import Event


class EventDetailView(DetailView):
    model = Event
    template_name = "event_detail/event_detail.html"
    context_object_name = "event"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Event.objects.prefetch_related(
            "categories",
            "route_segments",
            "aid_stations",
            "schedules",
            "documents",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = context["event"]
        today = timezone.localdate()

        schedules = list(event.schedules.all())
        aid_stations = list(event.aid_stations.all())
        route_segments = list(event.route_segments.all())
        documents = list(event.documents.all())

        capacity = event.participant_limit or 0
        registered = event.registered_count or 0
        capacity_ratio = 0
        if capacity:
            capacity_ratio = min(100, round((registered / capacity) * 100))

        try:
            registration_url = reverse("registrations:start", kwargs={"slug": event.slug})
        except NoReverseMatch:
            registration_url = ""

        context.update(
            {
                "today": today,
                "schedules": schedules,
                "aid_stations": aid_stations,
                "route_segments": route_segments,
                "documents": documents,
                "capacity_ratio": capacity_ratio,
                "remaining_slots": max(capacity - registered, 0) if capacity else None,
                "is_registration_open": event.is_registration_open,
                "registration_cta_url": registration_url,
                "forum_threads_url": f"{reverse('forum:index')}?event={event.id}",
                "breadcrumbs": [
                    {"label": "Events", "url": reverse("events:list")},
                    {"label": event.title, "url": ""},
                ],
            }
        )
        return context


@require_GET
def event_detail_json(request, slug):
    event = get_object_or_404(
        Event.objects.prefetch_related(
            "categories", "route_segments", "aid_stations", "schedules", "documents"
        ),
        slug=slug,
    )

    data = {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "city": event.city,
        "country": event.country,
        "venue": event.venue,
        "start_date": event.start_date.isoformat(),
        "end_date": event.end_date.isoformat() if event.end_date else None,
        "flag_off": event.start_date.isoformat(),
        "cut_off": event.end_date.isoformat() if event.end_date else None,
        "registration_deadline": event.registration_deadline.isoformat(),
        "status": event.status,
        "status_display": event.get_status_display(),
        "participant_limit": event.participant_limit,
        "registered_count": event.registered_count,
        "is_registration_open": event.is_registration_open,
        "categories": [
            {
                "id": category.id,
                "display_name": category.display_name,
                "distance_km": float(category.distance_km),
            }
            for category in event.categories.all()
        ],
        "route_segments": [
            {
                "order": segment.order,
                "title": segment.title,
                "distance_km": float(segment.distance_km),
                "elevation_gain": segment.elevation_gain,
                "description": segment.description,
            }
            for segment in event.route_segments.all()
        ],
        "aid_stations": [
            {
                "name": station.name,
                "kilometer_marker": float(station.kilometer_marker),
                "supplies": station.supplies,
                "is_medical": station.is_medical,
            }
            for station in event.aid_stations.all()
        ],
        "schedules": [
            {
                "title": item.title,
                "start_time": item.start_time.isoformat(),
                "end_time": item.end_time.isoformat() if item.end_time else None,
                "description": item.description,
            }
            for item in event.schedules.all()
        ],
        "documents": [
            {
                "title": doc.title,
                "url": doc.document_url,
                "type": doc.document_type,
                "uploaded_at": doc.uploaded_at.isoformat(),
            }
            for doc in event.documents.all()
        ],
    }

    return JsonResponse(data)


@require_GET
def event_availability_json(request, slug):
    event = get_object_or_404(Event, slug=slug)
    capacity = event.participant_limit or 0
    registered = event.registered_count or 0
    remaining = max(capacity - registered, 0) if capacity else None
    capacity_ratio = 0
    if capacity:
        capacity_ratio = min(100, round((registered / capacity) * 100))

    return JsonResponse(
        {
            "event_id": event.id,
            "capacity": capacity,
            "registered": registered,
            "remaining": remaining,
            "capacity_ratio": capacity_ratio,
            "is_registration_open": event.is_registration_open,
            "registration_deadline": event.registration_deadline.isoformat(),
            "status": event.status,
        }
    )
