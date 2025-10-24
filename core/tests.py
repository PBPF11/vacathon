from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event, EventCategory


class HomeViewTests(TestCase):
    def test_home_view_without_events(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["highlight_event"])
        stats = response.context["stats"]
        self.assertEqual(stats[0]["value"], 0)
        self.assertEqual(stats[0]["label"], "Events")
        self.assertTrue(response.context["highlight_headline"])
        self.assertGreaterEqual(len(response.context["highlight_reasons"]), 3)
        self.assertIn("youtube", response.context["news_video_url"])
        map_url = response.context["marathon_map_url"]
        self.assertEqual(map_url, "https://www.google.com/maps?q=marathon+race&output=embed")

    def test_home_view_with_events_sets_highlight_and_stats(self):
        today = timezone.localdate()
        category = EventCategory.objects.create(
            name="42k",
            distance_km=Decimal("42.00"),
            display_name="Full Marathon",
        )

        highlight = Event.objects.create(
            title="Jakarta Marathon",
            description="Event utama untuk para pelari urban.",
            city="Jakarta",
            country="Indonesia",
            start_date=today + timedelta(days=30),
            end_date=today + timedelta(days=31),
            registration_deadline=today + timedelta(days=20),
            status=Event.Status.UPCOMING,
            participant_limit=1500,
            registered_count=450,
            popularity_score=95,
        )
        highlight.categories.add(category)

        secondary = Event.objects.create(
            title="Bandung Night Run",
            description="Lari malam menikmati udara sejuk Bandung.",
            city="Bandung",
            country="Indonesia",
            start_date=today + timedelta(days=45),
            end_date=today + timedelta(days=45),
            registration_deadline=today + timedelta(days=35),
            status=Event.Status.UPCOMING,
            participant_limit=800,
            registered_count=220,
            popularity_score=80,
        )
        secondary.categories.add(category)

        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)

        highlight_event = response.context["highlight_event"]
        self.assertIsNotNone(highlight_event)
        self.assertEqual(highlight_event.pk, highlight.pk)

        headline = response.context["highlight_headline"]
        self.assertIn(highlight.title, headline)

        highlight_cta_url = response.context["highlight_cta_url"]
        expected_cta_url = reverse("registrations:start", kwargs={"slug": highlight.slug})
        self.assertEqual(highlight_cta_url, expected_cta_url)

        map_url = response.context["marathon_map_url"]
        self.assertIn("Jakarta", map_url)

        stats = {item["label"]: item["value"] for item in response.context["stats"]}
        self.assertEqual(stats["Events"], 2)
        self.assertEqual(stats["Registered Runners"], 670)
        self.assertEqual(stats["Active Cities"], 2)

        upcoming_events = response.context["upcoming_events"]
        self.assertTrue(any(event.pk == secondary.pk for event in upcoming_events))
