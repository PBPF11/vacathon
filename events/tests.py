from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.forms import EventFilterForm
from events.models import Event, EventCategory

User = get_user_model()


class EventCategoryModelTests(TestCase):
    """Tests for EventCategory model."""

    def test_filter_form_initial_state(self):
        """Test form initializes with correct fields."""
        form = EventFilterForm()
        
        self.assertIn('q', form.fields)
        self.assertIn('city', form.fields)
        self.assertIn('status', form.fields)
        self.assertIn('category', form.fields)
        self.assertIn('sort_by', form.fields)

    def test_filter_form_search_query(self):
        """Test filtering by search query."""
        event1 = Event.objects.create(
            title="Jakarta Marathon",
            description="Run in Jakarta",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        event2 = Event.objects.create(
            title="Bali Beach Run",
            description="Beach marathon",
            city="Bali",
            country="Indonesia",
            start_date=self.today + timedelta(days=40),
            registration_deadline=self.today + timedelta(days=30),
        )
        
        form = EventFilterForm(data={'q': 'Jakarta'})
        queryset = form.filter_queryset(Event.objects.all())
        
        self.assertIn(event1, queryset)
        self.assertNotIn(event2, queryset)

    def test_filter_form_city_filter(self):
        """Test filtering by city."""
        event1 = Event.objects.create(
            title="Event 1",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        event2 = Event.objects.create(
            title="Event 2",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=40),
            registration_deadline=self.today + timedelta(days=30),
        )
        
        form = EventFilterForm(data={'city': 'Jakarta'})
        queryset = form.filter_queryset(Event.objects.all())
        
        self.assertIn(event1, queryset)
        self.assertNotIn(event2, queryset)

    def test_filter_form_status_filter(self):
        """Test filtering by status."""
        event1 = Event.objects.create(
            title="Upcoming Event",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
            status=Event.Status.UPCOMING,
        )
        
        event2 = Event.objects.create(
            title="Completed Event",
            city="Bandung",
            country="Indonesia",
            start_date=self.today - timedelta(days=30),
            registration_deadline=self.today - timedelta(days=40),
            status=Event.Status.COMPLETED,
        )
        
        form = EventFilterForm(data={'status': Event.Status.UPCOMING})
        queryset = form.filter_queryset(Event.objects.all())
        
        self.assertIn(event1, queryset)
        self.assertNotIn(event2, queryset)

    def test_filter_form_category_filter(self):
        """Test filtering by category."""
        cat_5k = EventCategory.objects.create(
            name="5k", distance_km=Decimal("5.00"), display_name="5K"
        )
        
        event1 = Event.objects.create(
            title="Marathon Event",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        event1.categories.add(self.category)
        
        event2 = Event.objects.create(
            title="Fun Run Event",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=40),
            registration_deadline=self.today + timedelta(days=30),
        )
        event2.categories.add(cat_5k)
        
        form = EventFilterForm(data={'category': self.category.id})
        queryset = form.filter_queryset(Event.objects.all())
        
        self.assertIn(event1, queryset)
        self.assertNotIn(event2, queryset)

    def test_filter_form_sort_by_popularity(self):
        """Test sorting by popularity."""
        event1 = Event.objects.create(
            title="Less Popular",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
            popularity_score=50,
        )
        
        event2 = Event.objects.create(
            title="More Popular",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=40),
            registration_deadline=self.today + timedelta(days=30),
            popularity_score=100,
        )
        
        form = EventFilterForm(data={'sort_by': 'popularity'})
        queryset = form.filter_queryset(Event.objects.all())
        
        events = list(queryset)
        self.assertEqual(events[0], event2)
        self.assertEqual(events[1], event1)

    def test_filter_form_sort_by_soonest(self):
        """Test sorting by upcoming soonest."""
        event1 = Event.objects.create(
            title="Later Event",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=40),
            registration_deadline=self.today + timedelta(days=30),
        )
        
        event2 = Event.objects.create(
            title="Sooner Event",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=20),
            registration_deadline=self.today + timedelta(days=10),
        )
        
        form = EventFilterForm(data={'sort_by': 'soonest'})
        queryset = form.filter_queryset(Event.objects.all())
        
        events = list(queryset)
        self.assertEqual(events[0], event2)
        self.assertEqual(events[1], event1)

    def test_filter_form_sort_by_latest(self):
        """Test sorting by latest start date."""
        event1 = Event.objects.create(
            title="Earlier Event",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=20),
            registration_deadline=self.today + timedelta(days=10),
        )
        
        event2 = Event.objects.create(
            title="Later Event",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=40),
            registration_deadline=self.today + timedelta(days=30),
        )
        
        form = EventFilterForm(data={'sort_by': 'latest'})
        queryset = form.filter_queryset(Event.objects.all())
        
        events = list(queryset)
        self.assertEqual(events[0], event2)
        self.assertEqual(events[1], event1)

    def test_filter_form_combined_filters(self):
        """Test combining multiple filters."""
        event1 = Event.objects.create(
            title="Jakarta Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
            status=Event.Status.UPCOMING,
            popularity_score=100,
        )
        event1.categories.add(self.category)
        
        event2 = Event.objects.create(
            title="Bandung Run",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=40),
            registration_deadline=self.today + timedelta(days=30),
            status=Event.Status.UPCOMING,
            popularity_score=80,
        )
        event2.categories.add(self.category)
        
        form = EventFilterForm(data={
            'city': 'Jakarta',
            'status': Event.Status.UPCOMING,
            'category': self.category.id,
        })
        queryset = form.filter_queryset(Event.objects.all())
        
        self.assertIn(event1, queryset)
        self.assertNotIn(event2, queryset)

    def test_filter_form_invalid_data(self):
        """Test form handles invalid data gracefully."""
        form = EventFilterForm(data={'status': 'invalid'})
        queryset = form.filter_queryset(Event.objects.all())
        
        # Should return all events when filter is invalid
        self.assertTrue(queryset.exists())


class EventListViewTests(TestCase):
    """Tests for EventListView."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.today = timezone.localdate()

    def test_event_list_view_requires_login(self):
        """Test event list view requires authentication."""
        response = self.client.get(reverse('events:list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_event_list_view_accessible_when_logged_in(self):
        """Test event list view accessible to logged-in users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('events:list'))
        self.assertEqual(response.status_code, 200)

    def test_event_list_view_uses_correct_template(self):
        """Test event list view uses correct template."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('events:list'))
        self.assertTemplateUsed(response, 'events/event_list.html')

    def test_event_list_view_pagination(self):
        """Test pagination works correctly."""
        self.client.login(username='testuser', password='testpass123')
        
        # Create 15 events (paginate_by is 9)
        for i in range(15):
            Event.objects.create(
                title=f"Event {i}",
                city="Jakarta",
                country="Indonesia",
                start_date=self.today + timedelta(days=30 + i),
                registration_deadline=self.today + timedelta(days=20 + i),
            )
        
        response = self.client.get(reverse('events:list'))
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['events']), 9)
        
        # Check second page
        response = self.client.get(reverse('events:list') + '?page=2')
        self.assertEqual(len(response.context['events']), 6)

    def test_event_list_view_with_filters(self):
        """Test event list view respects filter parameters."""
        self.client.login(username='testuser', password='testpass123')
        
        Event.objects.create(
            title="Jakarta Event",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        Event.objects.create(
            title="Bandung Event",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=40),
            registration_deadline=self.today + timedelta(days=30),
        )
        
        response = self.client.get(reverse('events:list') + '?city=Jakarta')
        events = response.context['events']
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].city, "Jakarta")

    def test_event_list_view_highlight_parameter(self):
        """Test highlight parameter affects ordering."""
        self.client.login(username='testuser', password='testpass123')
        
        event1 = Event.objects.create(
            title="Regular Event",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=20),
            registration_deadline=self.today + timedelta(days=10),
        )
        
        event2 = Event.objects.create(
            title="Highlighted Marathon",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=40),
            registration_deadline=self.today + timedelta(days=30),
        )
        
        response = self.client.get(reverse('events:list') + '?highlight=Marathon')
        events = list(response.context['events'])
        
        # Highlighted event should come first
        self.assertEqual(events[0], event2)


class EventsJSONViewTests(TestCase):
    """Tests for events_json API view."""

    def setUp(self):
        self.today = timezone.localdate()
        self.category = EventCategory.objects.create(
            name="42k", distance_km=Decimal("42.00"), display_name="Full Marathon"
        )

    def test_events_json_returns_json_response(self):
        """Test JSON endpoint returns JSON response."""
        response = self.client.get(reverse('events:json'))
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_events_json_structure(self):
        """Test JSON response has correct structure."""
        event = Event.objects.create(
            title="Test Event",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        event.categories.add(self.category)
        
        response = self.client.get(reverse('events:json'))
        data = response.json()
        
        self.assertIn('results', data)
        self.assertIn('pagination', data)
        self.assertEqual(len(data['results']), 1)
        
        event_data = data['results'][0]
        self.assertEqual(event_data['title'], "Test Event")
        self.assertEqual(event_data['city'], "Jakarta")
        self.assertIn('categories', event_data)

    def test_events_json_pagination(self):
        """Test JSON endpoint pagination."""
        for i in range(15):
            Event.objects.create(
                title=f"Event {i}",
                city="Jakarta",
                country="Indonesia",
                start_date=self.today + timedelta(days=30 + i),
                registration_deadline=self.today + timedelta(days=20 + i),
            )
        
        response = self.client.get(reverse('events:json'))
        data = response.json()
        
        self.assertEqual(len(data['results']), 9)
        self.assertEqual(data['pagination']['pages'], 2)
        self.assertTrue(data['pagination']['has_next'])
        
        # Test page 2
        response = self.client.get(reverse('events:json') + '?page=2')
        data = response.json()
        self.assertEqual(len(data['results']), 6)

    def test_events_json_with_filters(self):
        """Test JSON endpoint respects filters."""
        event1 = Event.objects.create(
            title="Jakarta Event",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        Event.objects.create(
            title="Bandung Event",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=40),
            registration_deadline=self.today + timedelta(days=30),
        )
        
        response = self.client.get(reverse('events:json') + '?city=Jakarta')
        data = response.json()
        
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['title'], "Jakarta Event")


class EventModelEdgeCasesTests(TestCase):
    """Test edge cases for Event model."""

    def setUp(self):
        self.today = timezone.localdate()

    def test_event_with_very_long_title(self):
        """Test event handles long titles properly."""
        long_title = "A" * 200
        event = Event.objects.create(
            title=long_title,
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        self.assertEqual(event.title, long_title)
        self.assertLessEqual(len(event.slug), 220)  # max_length for slug

    def test_event_slug_with_special_characters(self):
        """Test slug generation with special characters."""
        event = Event.objects.create(
            title="São Paulo Marathon 2025!",
            city="São Paulo",
            country="Brazil",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        # Should remove special characters
        self.assertNotIn("!", event.slug)
        self.assertIn("sao-paulo", event.slug.lower())

    def test_event_registration_open_without_open_date(self):
        """Test registration open check when registration_open_date is None."""
        event = Event.objects.create(
            title="Test Event",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_open_date=None,
            registration_deadline=self.today + timedelta(days=20),
            status=Event.Status.UPCOMING,
        )
        
        # Should default to today and be open
        self.assertTrue(event.is_registration_open)

    def test_event_ordering(self):
        """Test events are ordered by start_date then title."""
        event3 = Event.objects.create(
            title="C Event",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        event1 = Event.objects.create(
            title="A Event",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=20),
            registration_deadline=self.today + timedelta(days=10),
        )
        
        event2 = Event.objects.create(
            title="B Event",
            city="Bali",
            country="Indonesia",
            start_date=self.today + timedelta(days=20),
            registration_deadline=self.today + timedelta(days=10),
        )
        
        events = list(Event.objects.all())
        self.assertEqual(events[0], event1)
        self.assertEqual(events[1], event2)
        self.assertEqual(events[2], event3)


class EventURLTests(TestCase):
    """Test URL configuration for events app."""

    def test_event_list_url_resolves(self):
        """Test event list URL resolves correctly."""
        url = reverse('events:list')
        self.assertEqual(url, '/events/')

    def test_events_json_url_resolves(self):
        """Test events JSON API URL resolves correctly."""
        url = reverse('events:json')
        self.assertEqual(url, '/events/api/')
    def test_create_event_category(self):
        """Test creating an event category."""
        category = EventCategory.objects.create(
            name="5k",
            distance_km=Decimal("5.00"),
            display_name="5K Fun Run",
        )
        
        self.assertEqual(category.name, "5k")
        self.assertEqual(category.distance_km, Decimal("5.00"))
        self.assertEqual(category.display_name, "5K Fun Run")

    def test_event_category_str_representation(self):
        """Test string representation of EventCategory."""
        category = EventCategory.objects.create(
            name="21k",
            distance_km=Decimal("21.10"),
            display_name="Half Marathon",
        )
        
        self.assertEqual(str(category), "Half Marathon")

    def test_event_category_ordering(self):
        """Test categories are ordered by distance."""
        cat_42k = EventCategory.objects.create(
            name="42k", distance_km=Decimal("42.00"), display_name="Full Marathon"
        )
        cat_5k = EventCategory.objects.create(
            name="5k", distance_km=Decimal("5.00"), display_name="5K"
        )
        cat_21k = EventCategory.objects.create(
            name="21k", distance_km=Decimal("21.10"), display_name="Half Marathon"
        )

        categories = list(EventCategory.objects.all())
        self.assertEqual(categories[0], cat_5k)
        self.assertEqual(categories[1], cat_21k)
        self.assertEqual(categories[2], cat_42k)


class EventModelTests(TestCase):
    """Tests for Event model."""

    def setUp(self):
        self.today = timezone.localdate()
        self.category = EventCategory.objects.create(
            name="42k",
            distance_km=Decimal("42.00"),
            display_name="Full Marathon",
        )

    def test_create_event(self):
        """Test creating an event."""
        event = Event.objects.create(
            title="Jakarta Marathon",
            description="Annual marathon in Jakarta",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        self.assertEqual(event.title, "Jakarta Marathon")
        self.assertEqual(event.city, "Jakarta")
        self.assertTrue(event.slug)

    def test_event_slug_auto_generation(self):
        """Test slug is automatically generated from title."""
        event = Event.objects.create(
            title="Bali Beach Marathon 2025",
            city="Bali",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        self.assertEqual(event.slug, "bali-beach-marathon-2025")

    def test_event_slug_uniqueness(self):
        """Test duplicate titles get unique slugs."""
        event1 = Event.objects.create(
            title="Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        event2 = Event.objects.create(
            title="Marathon",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=40),
            registration_deadline=self.today + timedelta(days=30),
        )
        
        self.assertEqual(event1.slug, "marathon")
        self.assertEqual(event2.slug, "marathon-1")

    def test_event_str_representation(self):
        """Test string representation of Event."""
        event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        self.assertEqual(str(event), "Test Marathon")

    def test_event_get_absolute_url(self):
        """Test get_absolute_url returns correct URL."""
        event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        expected_url = reverse("event_detail:detail", kwargs={"slug": event.slug})
        self.assertEqual(event.get_absolute_url(), expected_url)

    def test_event_is_registration_open_within_dates(self):
        """Test registration is open within valid dates."""
        event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_open_date=self.today - timedelta(days=5),
            registration_deadline=self.today + timedelta(days=20),
            status=Event.Status.UPCOMING,
        )
        
        self.assertTrue(event.is_registration_open)

    def test_event_is_registration_closed_before_open_date(self):
        """Test registration is closed before open date."""
        event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_open_date=self.today + timedelta(days=5),
            registration_deadline=self.today + timedelta(days=20),
            status=Event.Status.UPCOMING,
        )
        
        self.assertFalse(event.is_registration_open)

    def test_event_is_registration_closed_after_deadline(self):
        """Test registration is closed after deadline."""
        event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_open_date=self.today - timedelta(days=30),
            registration_deadline=self.today - timedelta(days=5),
            status=Event.Status.UPCOMING,
        )
        
        self.assertFalse(event.is_registration_open)

    def test_event_is_registration_closed_for_completed_event(self):
        """Test registration is closed for completed events."""
        event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today - timedelta(days=30),
            registration_open_date=self.today - timedelta(days=60),
            registration_deadline=self.today + timedelta(days=20),
            status=Event.Status.COMPLETED,
        )
        
        self.assertFalse(event.is_registration_open)

    def test_event_duration_days_single_day(self):
        """Test duration_days for single-day event."""
        event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            end_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        self.assertEqual(event.duration_days, 1)

    def test_event_duration_days_multi_day(self):
        """Test duration_days for multi-day event."""
        event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            end_date=self.today + timedelta(days=32),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        self.assertEqual(event.duration_days, 3)

    def test_event_duration_days_no_end_date(self):
        """Test duration_days returns None when no end_date."""
        event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        self.assertIsNone(event.duration_days)

    def test_event_categories_relationship(self):
        """Test many-to-many relationship with categories."""
        event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        cat_5k = EventCategory.objects.create(
            name="5k", distance_km=Decimal("5.00"), display_name="5K"
        )
        cat_42k = EventCategory.objects.create(
            name="42k", distance_km=Decimal("42.00"), display_name="Full Marathon"
        )
        
        event.categories.add(cat_5k, cat_42k)
        
        self.assertEqual(event.categories.count(), 2)
        self.assertIn(cat_5k, event.categories.all())
        self.assertIn(cat_42k, event.categories.all())

    def test_event_default_values(self):
        """Test default values for event fields."""
        event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        
        self.assertEqual(event.country, "Indonesia")
        self.assertEqual(event.status, Event.Status.UPCOMING)
        self.assertEqual(event.popularity_score, 0)
        self.assertEqual(event.participant_limit, 0)
        self.assertEqual(event.registered_count, 0)
        self.assertFalse(event.featured)


class EventFilterFormTests(TestCase):
    """Tests for EventFilterForm."""

    def setUp(self):
        self.today = timezone.localdate()
        self.category = EventCategory.objects.create(
            name="42k", distance_km=Decimal("42.00"), display_name="Full Marathon"
        )


