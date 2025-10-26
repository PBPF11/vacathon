from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from events.models import Event, EventCategory
from core.views import HomeView, AboutView

User = get_user_model()


class HomeViewTests(TestCase):
    """Comprehensive tests for HomeView."""

    def setUp(self):
        self.factory = RequestFactory()
        self.today = timezone.localdate()
        self.category = EventCategory.objects.create(
            name="42k",
            distance_km=Decimal("42.00"),
            display_name="Full Marathon",
        )

    def test_home_view_without_events(self):
        """Test home view renders correctly with no events."""
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
        """Test home view with multiple events sets correct highlight and stats."""
        highlight = Event.objects.create(
            title="Jakarta Marathon",
            description="Event utama untuk para pelari urban.",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            end_date=self.today + timedelta(days=31),
            registration_deadline=self.today + timedelta(days=20),
            status=Event.Status.UPCOMING,
            participant_limit=1500,
            registered_count=450,
            popularity_score=95,
        )
        highlight.categories.add(self.category)

        secondary = Event.objects.create(
            title="Bandung Night Run",
            description="Lari malam menikmati udara sejuk Bandung.",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=45),
            end_date=self.today + timedelta(days=45),
            registration_deadline=self.today + timedelta(days=35),
            status=Event.Status.UPCOMING,
            participant_limit=800,
            registered_count=220,
            popularity_score=80,
        )
        secondary.categories.add(self.category)

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

    def test_home_view_ongoing_event_as_highlight(self):
        """Test that ongoing events are prioritized as highlights."""
        ongoing = Event.objects.create(
            title="Ongoing Marathon",
            description="Currently happening",
            city="Surabaya",
            country="Indonesia",
            start_date=self.today - timedelta(days=1),
            end_date=self.today + timedelta(days=1),
            registration_deadline=self.today - timedelta(days=5),
            status=Event.Status.ONGOING,
            popularity_score=90,
        )
        
        upcoming = Event.objects.create(
            title="Future Marathon",
            description="Coming soon",
            city="Bali",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
            status=Event.Status.UPCOMING,
            popularity_score=85,
        )

        response = self.client.get(reverse("core:home"))
        highlight_event = response.context["highlight_event"]
        self.assertEqual(highlight_event.pk, ongoing.pk)

    def test_home_view_completed_event_fallback(self):
        """Test completed events are used as fallback when no upcoming/ongoing events."""
        completed = Event.objects.create(
            title="Past Marathon",
            description="Already finished",
            city="Yogyakarta",
            country="Indonesia",
            start_date=self.today - timedelta(days=30),
            end_date=self.today - timedelta(days=29),
            registration_deadline=self.today - timedelta(days=40),
            status=Event.Status.COMPLETED,
            popularity_score=100,
        )

        response = self.client.get(reverse("core:home"))
        highlight_event = response.context["highlight_event"]
        self.assertEqual(highlight_event.pk, completed.pk)

    def test_home_view_upcoming_events_excludes_highlight(self):
        """Test that upcoming events list excludes the highlight event."""
        highlight = Event.objects.create(
            title="Highlight Event",
            description="This is the highlight",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=10),
            registration_deadline=self.today + timedelta(days=5),
            status=Event.Status.UPCOMING,
            popularity_score=100,
        )

        other1 = Event.objects.create(
            title="Other Event 1",
            description="Another event",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=20),
            registration_deadline=self.today + timedelta(days=15),
            status=Event.Status.UPCOMING,
            popularity_score=80,
        )

        response = self.client.get(reverse("core:home"))
        upcoming = response.context["upcoming_events"]
        
        self.assertNotIn(highlight, upcoming)
        self.assertIn(other1, upcoming)

    def test_home_view_upcoming_events_limit_three(self):
        """Test that upcoming events are limited to 3 items."""
        highlight = Event.objects.create(
            title="Highlight",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=10),
            registration_deadline=self.today + timedelta(days=5),
            status=Event.Status.UPCOMING,
        )

        for i in range(5):
            Event.objects.create(
                title=f"Event {i}",
                city=f"City {i}",
                country="Indonesia",
                start_date=self.today + timedelta(days=20 + i),
                registration_deadline=self.today + timedelta(days=15 + i),
                status=Event.Status.UPCOMING,
            )

        response = self.client.get(reverse("core:home"))
        upcoming = response.context["upcoming_events"]
        self.assertLessEqual(len(upcoming), 3)

    def test_home_view_map_url_with_full_location(self):
        """Test map URL generation with complete location data."""
        event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            venue="Gelora Bung Karno",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )

        response = self.client.get(reverse("core:home"))
        map_url = response.context["marathon_map_url"]
        
        self.assertIn("Jakarta", map_url)
        self.assertIn("Indonesia", map_url)
        self.assertIn("output=embed", map_url)

    def test_home_view_stats_calculation(self):
        """Test correct calculation of statistics."""
        Event.objects.create(
            title="Event 1",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=10),
            registration_deadline=self.today + timedelta(days=5),
            registered_count=100,
        )

        Event.objects.create(
            title="Event 2",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=20),
            registration_deadline=self.today + timedelta(days=15),
            registered_count=200,
        )

        Event.objects.create(
            title="Event 3",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=25),
            registered_count=150,
        )

        response = self.client.get(reverse("core:home"))
        stats = {item["label"]: item["value"] for item in response.context["stats"]}
        
        self.assertEqual(stats["Events"], 3)
        self.assertEqual(stats["Registered Runners"], 450)
        self.assertEqual(stats["Active Cities"], 2)  # Jakarta and Bandung

    def test_home_view_highlight_reasons_with_duration(self):
        """Test highlight reasons adapt to event duration."""
        event = Event.objects.create(
            title="Multi-day Marathon",
            city="Bali",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            end_date=self.today + timedelta(days=32),  # 3 days
            registration_deadline=self.today + timedelta(days=20),
            participant_limit=500,
        )

        response = self.client.get(reverse("core:home"))
        reasons = response.context["highlight_reasons"]
        
        # Check that duration is mentioned in reasons
        self.assertTrue(any("3 days" in reason["description"] for reason in reasons))

    def test_home_view_highlight_reasons_with_participant_limit(self):
        """Test highlight reasons include participant limit."""
        event = Event.objects.create(
            title="Limited Marathon",
            city="Surabaya",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
            participant_limit=1000,
        )

        response = self.client.get(reverse("core:home"))
        reasons = response.context["highlight_reasons"]
        
        # Check that participant limit is mentioned
        self.assertTrue(any("1,000" in reason["description"] for reason in reasons))

    def test_home_view_safe_reverse_with_invalid_url(self):
        """Test _safe_reverse handles invalid URL names gracefully."""
        view = HomeView()
        result = view._safe_reverse("non:existent:url")
        self.assertEqual(result, "")

    def test_home_view_highlight_summary_truncation(self):
        """Test that long descriptions are truncated properly."""
        long_description = " ".join(["word"] * 100)
        event = Event.objects.create(
            title="Verbose Marathon",
            description=long_description,
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )

        response = self.client.get(reverse("core:home"))
        summary = response.context["highlight_summary"]
        
        # Should be truncated and end with ...
        self.assertTrue(len(summary) < len(long_description))
        self.assertTrue(summary.endswith("..."))

    def test_home_view_empty_city_excluded_from_stats(self):
        """Test events without city are excluded from city count."""
        Event.objects.create(
            title="Event with city",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=10),
            registration_deadline=self.today + timedelta(days=5),
        )

        Event.objects.create(
            title="Event without city",
            city="",
            country="Indonesia",
            start_date=self.today + timedelta(days=20),
            registration_deadline=self.today + timedelta(days=15),
        )

        response = self.client.get(reverse("core:home"))
        stats = {item["label"]: item["value"] for item in response.context["stats"]}
        
        self.assertEqual(stats["Active Cities"], 1)

    def test_home_view_current_year_in_context(self):
        """Test current year is included in context."""
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.context["current_year"], self.today.year)


class AboutViewTests(TestCase):
    """Comprehensive tests for AboutView."""

    def test_about_view_renders_successfully(self):
        """Test about page renders with correct status code."""
        response = self.client.get(reverse("core:about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/about.html")

    def test_about_view_team_members_in_context(self):
        """Test team members are included in context."""
        response = self.client.get(reverse("core:about"))
        team_members = response.context["team_members"]
        
        self.assertIsInstance(team_members, list)
        self.assertGreater(len(team_members), 0)
        
        # Check for specific team members
        expected_members = [
            "Ganesha Taqwa",
            "Tazkia Nur Alyani",
            "Josiah Naphta Simorangkir",
            "Muhammad Rafi Ghalib Fideligo",
            "Naufal Zafran Fadil",
            "Prama Ardend Narendradhipa",
        ]
        
        for member in expected_members:
            self.assertIn(member, team_members)

    def test_about_view_current_year_in_context(self):
        """Test current year is included in context."""
        response = self.client.get(reverse("core:about"))
        current_year = timezone.localdate().year
        self.assertEqual(response.context["current_year"], current_year)

    def test_about_view_contains_mission_text(self):
        """Test about page contains mission-related content."""
        response = self.client.get(reverse("core:about"))
        self.assertContains(response, "About Vacathon")
        self.assertContains(response, "Our Mission")

    def test_about_view_contains_team_section(self):
        """Test about page contains team section."""
        response = self.client.get(reverse("core:about"))
        self.assertContains(response, "Team Vacathon")

    def test_about_view_template_extends_base(self):
        """Test about template extends base.html."""
        response = self.client.get(reverse("core:about"))
        self.assertTemplateUsed(response, "base.html")


class HomeViewEdgeCasesTests(TestCase):
    """Test edge cases and boundary conditions for HomeView."""

    def setUp(self):
        self.today = timezone.localdate()

    def test_home_view_with_null_registered_count(self):
        """Test handling of events with null registered count."""
        Event.objects.create(
            title="Test Event",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=10),
            registration_deadline=self.today + timedelta(days=5),
            registered_count=0,
        )

        response = self.client.get(reverse("core:home"))
        stats = {item["label"]: item["value"] for item in response.context["stats"]}
        self.assertEqual(stats["Registered Runners"], 0)

    def test_home_view_with_no_end_date(self):
        """Test events without end date are handled correctly."""
        event = Event.objects.create(
            title="Single Day Event",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=10),
            end_date=None,
            registration_deadline=self.today + timedelta(days=5),
        )

        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)

    def test_home_view_with_empty_description(self):
        """Test event with empty description uses default summary."""
        Event.objects.create(
            title="No Description Event",
            description="",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=10),
            registration_deadline=self.today + timedelta(days=5),
        )

        response = self.client.get(reverse("core:home"))
        summary = response.context["highlight_summary"]
        
        # Should use default summary
        self.assertIn("Vacathon", summary)

    def test_home_view_events_ordered_by_popularity(self):
        """Test events with same start date are ordered by popularity."""
        same_date = self.today + timedelta(days=30)
        
        low_popularity = Event.objects.create(
            title="Low Popularity",
            city="Jakarta",
            country="Indonesia",
            start_date=same_date,
            registration_deadline=self.today + timedelta(days=20),
            status=Event.Status.UPCOMING,
            popularity_score=50,
        )
        
        high_popularity = Event.objects.create(
            title="High Popularity",
            city="Bandung",
            country="Indonesia",
            start_date=same_date,
            registration_deadline=self.today + timedelta(days=20),
            status=Event.Status.UPCOMING,
            popularity_score=100,
        )

        response = self.client.get(reverse("core:home"))
        highlight = response.context["highlight_event"]
        
        # Higher popularity should be highlight
        self.assertEqual(highlight.pk, high_popularity.pk)

    def test_home_view_with_special_characters_in_location(self):
        """Test map URL generation with special characters in location."""
        Event.objects.create(
            title="Special Location Event",
            city="São Paulo",
            country="Côte d'Ivoire",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )

        response = self.client.get(reverse("core:home"))
        map_url = response.context["marathon_map_url"]
        
        # Should handle special characters
        self.assertIsNotNone(map_url)
        self.assertIn("output=embed", map_url)


class URLConfigTests(TestCase):
    """Test URL configuration for core app."""

    def test_home_url_resolves(self):
        """Test home URL resolves correctly."""
        url = reverse("core:home")
        self.assertEqual(url, "/")

    def test_about_url_resolves(self):
        """Test about URL resolves correctly."""
        url = reverse("core:about")
        self.assertEqual(url, "/about/")