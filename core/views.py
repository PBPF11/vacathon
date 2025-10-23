from datetime import date
from django.db.models import Sum
from django.views.generic import TemplateView

from events.models import Event

class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_year"] = date.today().year
        events_qs = Event.objects.prefetch_related("categories").all()
        total_events = events_qs.count()
        distinct_cities = events_qs.values("city").distinct().count()
        total_runners = events_qs.aggregate(total=Sum("registered_count")).get("total") or 0

        context["stats"] = {
            "events": total_events,
            "cities": distinct_cities,
            "runners": total_runners,
            "partners": 14,
        }

        featured_events = events_qs.filter(featured=True).order_by("start_date")[:3]
        if not featured_events:
            featured_events = events_qs.order_by("start_date")[:3]
        context["featured_events"] = featured_events
        return context


class AboutView(TemplateView):
    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_year"] = date.today().year
        context["team_members"] = [
            "Ganesha Taqwa",
            "Tazkia Nur Alyani",
            "Josiah Naphta Simorangkir",
            "Muhammad Rafi Ghalib Fideligo",
            "Naufal Zafran Fadil",
            "Prama Ardend Narendradhipa",
        ]
        return context
