from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import models
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.generic import ListView

from .forms import EventFilterForm
from .models import Event


class EventListView(LoginRequiredMixin, ListView):
    template_name = "events/event_list.html"
    context_object_name = "events"
    paginate_by = 9

    def get_queryset(self):
        queryset = Event.objects.prefetch_related("categories").order_by("start_date")
        self.filter_form = EventFilterForm(self.request.GET or None)
        queryset = self.filter_form.filter_queryset(queryset)

        highlight = self.request.GET.get("highlight")
        if highlight:
            queryset = queryset.order_by(
                models.Case(
                    models.When(title__icontains=highlight, then=0),
                    default=1,
                ),
                "start_date",
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["today"] = timezone.localdate()
        return context


@require_GET
def events_json(request):
    queryset = Event.objects.prefetch_related("categories").order_by("start_date")
    form = EventFilterForm(request.GET or None)
    queryset = form.filter_queryset(queryset)

    paginator = Paginator(queryset, 9)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    events_payload = []
    for event in page_obj.object_list:
        events_payload.append(
            {
                "id": event.id,
                "title": event.title,
                "slug": event.slug,
                "url": event.get_absolute_url(),
                "city": event.city,
                "country": event.country,
                "venue": event.venue,
                "start_date": event.start_date.isoformat(),
                "end_date": event.end_date.isoformat() if event.end_date else None,
                "status": event.status,
                "status_display": event.get_status_display(),
                "registration_deadline": event.registration_deadline.isoformat(),
                "is_registration_open": event.is_registration_open,
                "popularity_score": event.popularity_score,
                "banner_image": event.banner_image,
                "participant_limit": event.participant_limit,
                "registered_count": event.registered_count,
                "categories": [
                    {
                        "id": category.id,
                        "display_name": category.display_name,
                        "distance_km": float(category.distance_km),
                    }
                    for category in event.categories.all()
                ],
            }
        )

    return JsonResponse(
        {
            "results": events_payload,
            "pagination": {
                "page": page_obj.number,
                "pages": paginator.num_pages,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
                "total": paginator.count,
            },
        }
    )
