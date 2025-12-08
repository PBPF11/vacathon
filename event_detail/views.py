from urllib.parse import quote_plus

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.generic import DetailView
from django.urls import NoReverseMatch, reverse

from events.models import Event


class EventDetailView(LoginRequiredMixin, DetailView):
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

        # Import form for modal
        from registrations.forms import RegistrationForm
        from registrations.models import EventRegistration

        # Check if user is already registered
        existing_registration = None
        if self.request.user.is_authenticated:
            existing_registration = EventRegistration.objects.filter(
                user=self.request.user, event=event
            ).select_related("category").first()

        # Create form for modal
        form = RegistrationForm(event=event, user=self.request.user, instance=existing_registration)

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
                "marathon_map_url": self._build_map_url(event),
                "breadcrumbs": [
                    {"label": "Events", "url": reverse("events:list")},
                    {"label": event.title, "url": ""},
                ],
                "form": form,
            }
        )
        return context

    @staticmethod
    def _build_map_url(event: Event) -> str:
        parts = []
        if event.venue:
            parts.append(event.venue)
        if event.city:
            parts.append(event.city)
        if event.country:
            parts.append(event.country)
        if not parts:
            return ""
        query = quote_plus(" ".join(parts) + " marathon")
        return f"https://www.google.com/maps?q={query}&output=embed"


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
        "registration_open_date": event.registration_open_date.isoformat()
        if event.registration_open_date
        else None,
        "status": event.status,
        "status_display": event.get_status_display(),
        "participant_limit": event.participant_limit,
        "registered_count": event.registered_count,
        "is_registration_open": event.is_registration_open,
        "map_url": EventDetailView._build_map_url(event),
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
                "id": segment.id,
                "event": event.id,
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
                "id": station.id,
                "event": event.id,
                "name": station.name,
                "kilometer_marker": float(station.kilometer_marker),
                "supplies": station.supplies,
                "is_medical": station.is_medical,
            }
            for station in event.aid_stations.all()
        ],
        "schedules": [
            {
                "id": item.id,
                "event": event.id,
                "title": item.title,
                "start_time": item.start_time.isoformat(),
                "end_time": item.end_time.isoformat() if item.end_time else None,
                "description": item.description,
            }
            for item in event.schedules.all()
        ],
        "documents": [
            {
                "id": doc.id,             
                "event": event.id,      
                "title": doc.title,
                "url": doc.document_url,
                "type": doc.document_type,
                "uploaded_by": doc.uploaded_by,
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
            "registration_open_date": event.registration_open_date.isoformat()
            if event.registration_open_date
            else None,
            "status": event.status,
        }
    )
