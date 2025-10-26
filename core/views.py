from urllib.parse import quote_plus

from django.db.models import Sum
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.text import Truncator
from django.views.generic import TemplateView

from events.models import Event


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        context["current_year"] = today.year

        events_qs = Event.objects.prefetch_related("categories").order_by("start_date")

        total_events = events_qs.count()
        distinct_cities = (
            events_qs.exclude(city__isnull=True)
            .exclude(city="")
            .values("city")
            .distinct()
            .count()
        )
        total_runners = (
            events_qs.aggregate(total=Sum("registered_count")).get("total") or 0
        )

        highlight_event = self._get_highlight_event(events_qs, today)

        context["stats"] = [
            {"label": "Events", "value": total_events},
            {"label": "Registered Runners", "value": total_runners},
            {"label": "Active Cities", "value": distinct_cities},
            {"label": "Partners & Sponsors", "value": 14},
        ]

        context["highlight_event"] = highlight_event
        context["highlight_headline"] = self._build_highlight_headline(highlight_event)
        context["highlight_summary"] = self._build_highlight_summary(highlight_event)
        context["highlight_reasons"] = self._build_highlight_reasons(highlight_event)
        context["highlight_cta_url"] = self._get_highlight_cta_url(highlight_event)
        context["highlight_detail_url"] = (
            highlight_event.get_absolute_url() if highlight_event else ""
        )
        context["marathon_map_url"] = self._build_marathon_map_url(highlight_event)
        context["events_list_url"] = self._safe_reverse("events:list")
        context["news_video_url"] = (
            "https://www.youtube.com/embed/aZ9HQJoMPWc?si=PjB2VCz3BuYbw8t2"
        )

        context["upcoming_events"] = self._get_upcoming_events(events_qs, highlight_event)
        return context

    def _get_highlight_event(self, events_qs, today):
        upcoming = events_qs.filter(
            status__in=[Event.Status.UPCOMING, Event.Status.ONGOING],
        ).order_by("start_date", "-popularity_score")
        highlight = upcoming.first()
        if highlight:
            return highlight
        fallback = (
            events_qs.filter(start_date__lte=today)
            .order_by("-start_date", "-popularity_score")
            .first()
        )
        return fallback or events_qs.first()

    def _get_upcoming_events(self, events_qs, highlight_event):
        exclude_ids = []
        if highlight_event:
            exclude_ids.append(highlight_event.pk)

        prioritized = events_qs.filter(
            status__in=[Event.Status.UPCOMING, Event.Status.ONGOING]
        ).exclude(pk__in=exclude_ids)

        events = list(prioritized[:3])
        if len(events) < 3:
            already_ids = exclude_ids + [event.pk for event in events]
            fallback = events_qs.exclude(pk__in=already_ids)
            events.extend(list(fallback[: 3 - len(events)]))
        return events

    def _build_highlight_headline(self, highlight_event):
        if highlight_event:
            return f"Why run {highlight_event.title}?"
        return "Why run with Vacathon?"

    def _build_highlight_summary(self, highlight_event):
        if highlight_event and highlight_event.description:
            return Truncator(highlight_event.description).words(40, truncate="...")
        return (
            "Vacathon curates remarkable running getaways so you can chase every "
            "finish line with confidence, community, and adventure."
        )

    def _build_highlight_reasons(self, highlight_event):
        duration_days = getattr(highlight_event, "duration_days", None)
        participant_limit = getattr(highlight_event, "participant_limit", 0) or None

        reasons = [
            {
                "icon": "2",
                "title": "Two race days.",
                "description": (
                    "A two-day schedule welcomes more runners and gives you flexibility "
                    "to choose the race that fits your plan."
                ),
            },
            {
                "icon": "*",
                "title": "Inclusive for every runner.",
                "description": (
                    "Certified routes and multiple categories support both first-timers "
                    "and seasoned athletes to perform their best."
                ),
            },
            {
                "icon": "!",
                "title": "Strict marathon regulation.",
                "description": (
                    "Safety-first cut-offs and climate-aware planning deliver a "
                    "comfortable, well-managed race experience."
                ),
            },
        ]

        if duration_days and duration_days > 1:
            reasons[0]["description"] = (
                f"{highlight_event.title} unfolds across {duration_days} days, giving you "
                "even more chances to join the excitement."
            )

        if participant_limit:
            reasons[1]["description"] = (
                f"With capacity for {participant_limit:,} runners, everyone from "
                "newcomers to elite racers has room to shine."
            )

        return reasons

    def _build_marathon_map_url(self, highlight_event):
        if highlight_event:
            parts = []
            if highlight_event.city:
                parts.append(highlight_event.city)
            if highlight_event.country:
                parts.append(highlight_event.country)
            if parts:
                query = quote_plus(" ".join(parts) + " marathon")
                return f"https://www.google.com/maps?q={query}&output=embed"
        return "https://www.google.com/maps?q=marathon+race&output=embed"

    def _get_highlight_cta_url(self, highlight_event):
        if not highlight_event:
            return self._safe_reverse("events:list")
        registration_url = self._safe_reverse(
            "registrations:start", kwargs={"slug": highlight_event.slug}
        )
        if registration_url:
            return registration_url
        detail_url = highlight_event.get_absolute_url()
        if detail_url:
            return detail_url
        return self._safe_reverse("events:list")

    def _safe_reverse(self, url_name, *, kwargs=None):
        try:
            return reverse(url_name, kwargs=kwargs)
        except NoReverseMatch:
            return ""


class AboutView(TemplateView):
    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_year"] = timezone.localdate().year
        context["team_members"] = [
            "Ganesha Taqwa",
            "Tazkia Nur Alyani",
            "Josiah Naphta Simorangkir",
            "Muhammad Rafi Ghalib Fideligo",
            "Naufal Zafran Fadil",
            "Prama Ardend Narendradhipa",
        ]
        return context
