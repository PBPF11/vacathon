from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event, EventCategory
from event_detail.models import AidStation, EventDocument, EventSchedule, RouteSegment

User = get_user_model()


class EventScheduleModelTests(TestCase):
    """Tests for EventSchedule model."""

    def setUp(self):
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )

    def test_create_event_schedule(self):
        """Test creating an event schedule."""
        start_time = timezone.now() + timedelta(days=30)
        end_time = start_time + timedelta(hours=2)
        
        schedule = EventSchedule.objects.create(
            event=self.event,
            title="Race Expo",
            start_time=start_time,
            end_time=end_time,
            description="Pre-race expo and bib collection",
        )
        
        self.assertEqual(schedule.event, self.event)
        self.assertEqual(schedule.title, "Race Expo")
        self.assertEqual(schedule.start_time, start_time)
        self.assertEqual(schedule.end_time, end_time)

    def test_event_schedule_str_representation(self):
        """Test string representation of EventSchedule."""
        start_time = timezone.now() + timedelta(days=30)
        
        schedule = EventSchedule.objects.create(
            event=self.event,
            title="Race Start",
            start_time=start_time,
        )
        
        expected_str = f"{self.event.title} - Race Start"
        self.assertEqual(str(schedule), expected_str)

    def test_event_schedule_ordering(self):
        """Test schedules are ordered by start_time."""
        time1 = timezone.now() + timedelta(days=30, hours=8)
        time2 = timezone.now() + timedelta(days=30, hours=6)
        time3 = timezone.now() + timedelta(days=30, hours=10)
        
        schedule3 = EventSchedule.objects.create(
            event=self.event, title="Late Item", start_time=time3
        )
        schedule1 = EventSchedule.objects.create(
            event=self.event, title="Early Item", start_time=time2
        )
        schedule2 = EventSchedule.objects.create(
            event=self.event, title="Mid Item", start_time=time1
        )
        
        schedules = list(EventSchedule.objects.all())
        self.assertEqual(schedules[0], schedule1)
        self.assertEqual(schedules[1], schedule2)
        self.assertEqual(schedules[2], schedule3)

    def test_event_schedule_without_end_time(self):
        """Test schedule can be created without end_time."""
        start_time = timezone.now() + timedelta(days=30)
        
        schedule = EventSchedule.objects.create(
            event=self.event,
            title="Flag Off",
            start_time=start_time,
            end_time=None,
        )
        
        self.assertIsNone(schedule.end_time)


class AidStationModelTests(TestCase):
    """Tests for AidStation model."""

    def setUp(self):
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )

    def test_create_aid_station(self):
        """Test creating an aid station."""
        station = AidStation.objects.create(
            event=self.event,
            name="Station 1",
            kilometer_marker=Decimal("10.50"),
            supplies="Water, energy gels, bananas",
            is_medical=False,
        )
        
        self.assertEqual(station.event, self.event)
        self.assertEqual(station.name, "Station 1")
        self.assertEqual(station.kilometer_marker, Decimal("10.50"))
        self.assertFalse(station.is_medical)

    def test_aid_station_str_representation(self):
        """Test string representation of AidStation."""
        station = AidStation.objects.create(
            event=self.event,
            name="Midpoint Station",
            kilometer_marker=Decimal("21.00"),
            supplies="Water, sports drink",
        )
        
        self.assertEqual(str(station), "Midpoint Station (21.00 KM)")

    def test_aid_station_ordering(self):
        """Test aid stations are ordered by kilometer_marker."""
        station3 = AidStation.objects.create(
            event=self.event,
            name="Station 3",
            kilometer_marker=Decimal("30.00"),
            supplies="Water",
        )
        
        station1 = AidStation.objects.create(
            event=self.event,
            name="Station 1",
            kilometer_marker=Decimal("10.00"),
            supplies="Water",
        )
        
        station2 = AidStation.objects.create(
            event=self.event,
            name="Station 2",
            kilometer_marker=Decimal("20.00"),
            supplies="Water",
        )
        
        stations = list(AidStation.objects.all())
        self.assertEqual(stations[0], station1)
        self.assertEqual(stations[1], station2)
        self.assertEqual(stations[2], station3)

    def test_aid_station_medical_flag(self):
        """Test medical station flag."""
        medical_station = AidStation.objects.create(
            event=self.event,
            name="Medical Station",
            kilometer_marker=Decimal("15.00"),
            supplies="First aid, paramedics",
            is_medical=True,
        )
        
        self.assertTrue(medical_station.is_medical)


class RouteSegmentModelTests(TestCase):
    """Tests for RouteSegment model."""

    def setUp(self):
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )

    def test_create_route_segment(self):
        """Test creating a route segment."""
        segment = RouteSegment.objects.create(
            event=self.event,
            order=1,
            title="Starting Line to City Center",
            description="Flat urban route through downtown",
            distance_km=Decimal("10.00"),
            elevation_gain=50,
        )
        
        self.assertEqual(segment.event, self.event)
        self.assertEqual(segment.order, 1)
        self.assertEqual(segment.title, "Starting Line to City Center")
        self.assertEqual(segment.elevation_gain, 50)

    def test_route_segment_str_representation(self):
        """Test string representation of RouteSegment."""
        segment = RouteSegment.objects.create(
            event=self.event,
            order=2,
            title="City Center to Park",
            description="Scenic route",
            distance_km=Decimal("12.00"),
        )
        
        expected_str = f"{self.event.title} - Segment 2"
        self.assertEqual(str(segment), expected_str)

    def test_route_segment_ordering(self):
        """Test route segments are ordered by order field."""
        segment3 = RouteSegment.objects.create(
            event=self.event, order=3, title="Segment 3",
            description="Desc", distance_km=Decimal("10.00")
        )
        
        segment1 = RouteSegment.objects.create(
            event=self.event, order=1, title="Segment 1",
            description="Desc", distance_km=Decimal("10.00")
        )
        
        segment2 = RouteSegment.objects.create(
            event=self.event, order=2, title="Segment 2",
            description="Desc", distance_km=Decimal("10.00")
        )
        
        segments = list(RouteSegment.objects.all())
        self.assertEqual(segments[0], segment1)
        self.assertEqual(segments[1], segment2)
        self.assertEqual(segments[2], segment3)

    def test_route_segment_unique_together(self):
        """Test event and order combination is unique."""
        RouteSegment.objects.create(
            event=self.event, order=1, title="Segment 1",
            description="First segment", distance_km=Decimal("10.00")
        )
        
        # Creating another segment with same event and order should raise error
        with self.assertRaises(Exception):
            RouteSegment.objects.create(
                event=self.event, order=1, title="Duplicate Segment",
                description="Should fail", distance_km=Decimal("10.00")
            )

    def test_route_segment_default_elevation(self):
        """Test default elevation gain is 0."""
        segment = RouteSegment.objects.create(
            event=self.event, order=1, title="Flat Segment",
            description="No elevation", distance_km=Decimal("10.00")
        )
        
        self.assertEqual(segment.elevation_gain, 0)


class EventDocumentModelTests(TestCase):
    """Tests for EventDocument model."""

    def setUp(self):
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )

    def test_create_event_document(self):
        """Test creating an event document."""
        doc = EventDocument.objects.create(
            event=self.event,
            title="Race Guide 2025",
            document_url="https://example.com/guide.pdf",
            document_type=EventDocument.DocumentType.GUIDE,
            uploaded_by="Race Director",
        )
        
        self.assertEqual(doc.event, self.event)
        self.assertEqual(doc.title, "Race Guide 2025")
        self.assertEqual(doc.document_type, EventDocument.DocumentType.GUIDE)

    def test_event_document_str_representation(self):
        """Test string representation of EventDocument."""
        doc = EventDocument.objects.create(
            event=self.event,
            title="GPX Track",
            document_url="https://example.com/track.gpx",
            document_type=EventDocument.DocumentType.GPX,
        )
        
        self.assertEqual(str(doc), "GPX Track (GPX Route)")

    def test_event_document_default_type(self):
        """Test default document type is OTHER."""
        doc = EventDocument.objects.create(
            event=self.event,
            title="Miscellaneous Document",
            document_url="https://example.com/misc.pdf",
        )
        
        self.assertEqual(doc.document_type, EventDocument.DocumentType.OTHER)

    def test_event_document_default_uploaded_by(self):
        """Test default uploaded_by value."""
        doc = EventDocument.objects.create(
            event=self.event,
            title="Test Doc",
            document_url="https://example.com/doc.pdf",
        )
        
        self.assertEqual(doc.uploaded_by, "Organizing Committee")

    def test_event_document_ordering(self):
        """Test documents are ordered by document_type then title."""
        doc_guide = EventDocument.objects.create(
            event=self.event, title="Z Guide",
            document_url="https://example.com/guide.pdf",
            document_type=EventDocument.DocumentType.GUIDE,
        )
        
        doc_gpx = EventDocument.objects.create(
            event=self.event, title="A Track",
            document_url="https://example.com/track.gpx",
            document_type=EventDocument.DocumentType.GPX,
        )
        
        doc_brochure = EventDocument.objects.create(
            event=self.event, title="M Brochure",
            document_url="https://example.com/brochure.pdf",
            document_type=EventDocument.DocumentType.BROCHURE,
        )
        
        docs = list(EventDocument.objects.all())
        # Ordered by document_type (brochure, gpx, guide), then title
        self.assertEqual(docs[0], doc_brochure)
        self.assertEqual(docs[1], doc_gpx)
        self.assertEqual(docs[2], doc_guide)

    def test_event_document_auto_timestamp(self):
        """Test uploaded_at is automatically set."""
        doc = EventDocument.objects.create(
            event=self.event,
            title="Test Doc",
            document_url="https://example.com/doc.pdf",
        )
        
        self.assertIsNotNone(doc.uploaded_at)


class EventDetailViewTests(TestCase):
    """Tests for EventDetailView."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.today = timezone.localdate()
        self.category = EventCategory.objects.create(
            name="42k", distance_km=Decimal("42.00"), display_name="Full Marathon"
        )
        self.event = Event.objects.create(
            title="Test Marathon",
            description="A great marathon",
            city="Jakarta",
            country="Indonesia",
            venue="National Stadium",
            start_date=self.today + timedelta(days=30),
            end_date=self.today + timedelta(days=30),
            registration_open_date=self.today - timedelta(days=5),
            registration_deadline=self.today + timedelta(days=20),
            participant_limit=1000,
            registered_count=500,
            status=Event.Status.UPCOMING,
        )
        self.event.categories.add(self.category)

    def test_event_detail_view_requires_login(self):
        """Test event detail view requires authentication."""
        response = self.client.get(
            reverse('event_detail:detail', kwargs={'slug': self.event.slug})
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_event_detail_view_accessible_when_logged_in(self):
        """Test event detail view accessible to logged-in users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('event_detail:detail', kwargs={'slug': self.event.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_event_detail_view_uses_correct_template(self):
        """Test event detail view uses correct template."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('event_detail:detail', kwargs={'slug': self.event.slug})
        )
        self.assertTemplateUsed(response, 'event_detail/event_detail.html')

    def test_event_detail_view_context_data(self):
        """Test event detail view includes all necessary context."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('event_detail:detail', kwargs={'slug': self.event.slug})
        )
        
        self.assertEqual(response.context['event'], self.event)
        self.assertIn('schedules', response.context)
        self.assertIn('aid_stations', response.context)
        self.assertIn('route_segments', response.context)
        self.assertIn('documents', response.context)
        self.assertIn('capacity_ratio', response.context)
        self.assertIn('remaining_slots', response.context)
        self.assertIn('is_registration_open', response.context)

    def test_event_detail_view_capacity_calculation(self):
        """Test capacity ratio is calculated correctly."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('event_detail:detail', kwargs={'slug': self.event.slug})
        )
        
        capacity_ratio = response.context['capacity_ratio']
        remaining_slots = response.context['remaining_slots']
        
        self.assertEqual(capacity_ratio, 50)  # 500/1000 * 100
        self.assertEqual(remaining_slots, 500)  # 1000 - 500

    def test_event_detail_view_with_schedules(self):
        """Test event detail view includes schedules."""
        self.client.login(username='testuser', password='testpass123')
        
        start_time = timezone.now() + timedelta(days=30)
        EventSchedule.objects.create(
            event=self.event,
            title="Race Expo",
            start_time=start_time,
            description="Bib collection",
        )
        
        response = self.client.get(
            reverse('event_detail:detail', kwargs={'slug': self.event.slug})
        )
        
        schedules = response.context['schedules']
        self.assertEqual(len(schedules), 1)
        self.assertEqual(schedules[0].title, "Race Expo")

    def test_event_detail_view_with_aid_stations(self):
        """Test event detail view includes aid stations."""
        self.client.login(username='testuser', password='testpass123')
        
        AidStation.objects.create(
            event=self.event,
            name="Station 1",
            kilometer_marker=Decimal("10.00"),
            supplies="Water, gels",
        )
        
        response = self.client.get(
            reverse('event_detail:detail', kwargs={'slug': self.event.slug})
        )
        
        aid_stations = response.context['aid_stations']
        self.assertEqual(len(aid_stations), 1)
        self.assertEqual(aid_stations[0].name, "Station 1")

    def test_event_detail_view_with_route_segments(self):
        """Test event detail view includes route segments."""
        self.client.login(username='testuser', password='testpass123')
        
        RouteSegment.objects.create(
            event=self.event,
            order=1,
            title="Segment 1",
            description="Starting segment",
            distance_km=Decimal("10.00"),
        )
        
        response = self.client.get(
            reverse('event_detail:detail', kwargs={'slug': self.event.slug})
        )
        
        route_segments = response.context['route_segments']
        self.assertEqual(len(route_segments), 1)
        self.assertEqual(route_segments[0].title, "Segment 1")

    def test_event_detail_view_with_documents(self):
        """Test event detail view includes documents."""
        self.client.login(username='testuser', password='testpass123')
        
        EventDocument.objects.create(
            event=self.event,
            title="Race Guide",
            document_url="https://example.com/guide.pdf",
            document_type=EventDocument.DocumentType.GUIDE,
        )
        
        response = self.client.get(
            reverse('event_detail:detail', kwargs={'slug': self.event.slug})
        )
        
        documents = response.context['documents']
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].title, "Race Guide")

    def test_event_detail_view_map_url_generation(self):
        """Test map URL is generated correctly."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('event_detail:detail', kwargs={'slug': self.event.slug})
        )
        
        map_url = response.context['marathon_map_url']
        self.assertIn("Jakarta", map_url)
        self.assertIn("Indonesia", map_url)
        self.assertIn("output=embed", map_url)

    def test_event_detail_view_breadcrumbs(self):
        """Test breadcrumbs are included in context."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('event_detail:detail', kwargs={'slug': self.event.slug})
        )
        
        breadcrumbs = response.context['breadcrumbs']
        self.assertEqual(len(breadcrumbs), 2)
        self.assertEqual(breadcrumbs[0]['label'], "Events")
        self.assertEqual(breadcrumbs[1]['label'], self.event.title)

    def test_event_detail_view_without_participant_limit(self):
        """Test event detail with unlimited capacity."""
        self.client.login(username='testuser', password='testpass123')
        
        unlimited_event = Event.objects.create(
            title="Unlimited Event",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
            participant_limit=0,  # Unlimited
        )
        
        response = self.client.get(
            reverse('event_detail:detail', kwargs={'slug': unlimited_event.slug})
        )
        
        remaining_slots = response.context['remaining_slots']
        self.assertIsNone(remaining_slots)

    def test_event_detail_view_404_for_nonexistent_event(self):
        """Test 404 is returned for non-existent event."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('event_detail:detail', kwargs={'slug': 'nonexistent-event'})
        )
        self.assertEqual(response.status_code, 404)


class EventDetailJSONViewTests(TestCase):
    """Tests for event_detail_json API view."""

    def setUp(self):
        self.today = timezone.localdate()
        self.category = EventCategory.objects.create(
            name="42k", distance_km=Decimal("42.00"), display_name="Full Marathon"
        )
        self.event = Event.objects.create(
            title="Test Marathon",
            description="A great marathon",
            city="Jakarta",
            country="Indonesia",
            venue="National Stadium",
            start_date=self.today + timedelta(days=30),
            end_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
            status=Event.Status.UPCOMING,
        )
        self.event.categories.add(self.category)

    def test_event_detail_json_returns_json(self):
        """Test JSON endpoint returns JSON response."""
        response = self.client.get(
            reverse('event_detail:detail-json', kwargs={'slug': self.event.slug})
        )
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_event_detail_json_structure(self):
        """Test JSON response has correct structure."""
        response = self.client.get(
            reverse('event_detail:detail-json', kwargs={'slug': self.event.slug})
        )
        data = response.json()
        
        self.assertEqual(data['title'], "Test Marathon")
        self.assertEqual(data['city'], "Jakarta")
        self.assertEqual(data['country'], "Indonesia")
        self.assertIn('categories', data)
        self.assertIn('route_segments', data)
        self.assertIn('aid_stations', data)
        self.assertIn('schedules', data)
        self.assertIn('documents', data)

    def test_event_detail_json_with_all_related_data(self):
        """Test JSON includes all related data."""
        # Add related data
        EventSchedule.objects.create(
            event=self.event,
            title="Race Start",
            start_time=timezone.now() + timedelta(days=30),
        )
        
        AidStation.objects.create(
            event=self.event,
            name="Station 1",
            kilometer_marker=Decimal("10.00"),
            supplies="Water",
        )
        
        RouteSegment.objects.create(
            event=self.event,
            order=1,
            title="Segment 1",
            description="Starting segment",
            distance_km=Decimal("10.00"),
        )
        
        EventDocument.objects.create(
            event=self.event,
            title="Race Guide",
            document_url="https://example.com/guide.pdf",
            document_type=EventDocument.DocumentType.GUIDE,
        )
        
        response = self.client.get(
            reverse('event_detail:detail-json', kwargs={'slug': self.event.slug})
        )
        data = response.json()
        
        self.assertEqual(len(data['schedules']), 1)
        self.assertEqual(len(data['aid_stations']), 1)
        self.assertEqual(len(data['route_segments']), 1)
        self.assertEqual(len(data['documents']), 1)

    def test_event_detail_json_404_for_nonexistent(self):
        """Test 404 for non-existent event."""
        response = self.client.get(
            reverse('event_detail:detail-json', kwargs={'slug': 'nonexistent'})
        )
        self.assertEqual(response.status_code, 404)


class EventAvailabilityJSONViewTests(TestCase):
    """Tests for event_availability_json API view."""

    def setUp(self):
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_open_date=self.today - timedelta(days=5),
            registration_deadline=self.today + timedelta(days=20),
            participant_limit=1000,
            registered_count=750,
            status=Event.Status.UPCOMING,
        )

    def test_availability_json_returns_json(self):
        """Test availability endpoint returns JSON."""
        response = self.client.get(
            reverse('event_detail:availability-json', kwargs={'slug': self.event.slug})
        )
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_availability_json_structure(self):
        """Test JSON response has correct structure."""
        response = self.client.get(
            reverse('event_detail:availability-json', kwargs={'slug': self.event.slug})
        )
        data = response.json()
        
        self.assertIn('event_id', data)
        self.assertIn('capacity', data)
        self.assertIn('registered', data)
        self.assertIn('remaining', data)
        self.assertIn('capacity_ratio', data)
        self.assertIn('is_registration_open', data)

    def test_availability_json_calculations(self):
        """Test availability calculations are correct."""
        response = self.client.get(
            reverse('event_detail:availability-json', kwargs={'slug': self.event.slug})
        )
        data = response.json()
        
        self.assertEqual(data['capacity'], 1000)
        self.assertEqual(data['registered'], 750)
        self.assertEqual(data['remaining'], 250)
        self.assertEqual(data['capacity_ratio'], 75)
        self.assertTrue(data['is_registration_open'])

    def test_availability_json_unlimited_capacity(self):
        """Test availability with unlimited capacity."""
        unlimited_event = Event.objects.create(
            title="Unlimited Event",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
            participant_limit=0,
            registered_count=500,
        )
        
        response = self.client.get(
            reverse('event_detail:availability-json', kwargs={'slug': unlimited_event.slug})
        )
        data = response.json()
        
        self.assertEqual(data['capacity'], 0)
        self.assertIsNone(data['remaining'])
        self.assertEqual(data['capacity_ratio'], 0)

    def test_availability_json_404_for_nonexistent(self):
        """Test 404 for non-existent event."""
        response = self.client.get(
            reverse('event_detail:availability-json', kwargs={'slug': 'nonexistent'})
        )
        self.assertEqual(response.status_code, 404)


class EventDetailAdminTests(TestCase):
    """Tests for admin interface."""

    def test_event_schedule_admin_registered(self):
        """Test EventSchedule is registered in admin."""
        from django.contrib import admin
        from event_detail.models import EventSchedule
        
        self.assertTrue(admin.site.is_registered(EventSchedule))

    def test_aid_station_admin_registered(self):
        """Test AidStation is registered in admin."""
        from django.contrib import admin
        from event_detail.models import AidStation
        
        self.assertTrue(admin.site.is_registered(AidStation))

    def test_route_segment_admin_registered(self):
        """Test RouteSegment is registered in admin."""
        from django.contrib import admin
        from event_detail.models import RouteSegment
        
        self.assertTrue(admin.site.is_registered(RouteSegment))

    def test_event_document_admin_registered(self):
        """Test EventDocument is registered in admin."""
        from django.contrib import admin
        from event_detail.models import EventDocument
        
        self.assertTrue(admin.site.is_registered(EventDocument))


class EventDetailURLTests(TestCase):
    """Test URL configuration for event_detail app."""

    def test_event_detail_url_resolves(self):
        """Test event detail URL resolves correctly."""
        url = reverse('event_detail:detail', kwargs={'slug': 'test-event'})
        # Just verify URL is not empty and contains the slug
        self.assertTrue(url)
        self.assertIn('test-event', url)

    def test_event_detail_json_url_resolves(self):
        """Test event detail JSON API URL resolves correctly."""
        url = reverse('event_detail:detail-json', kwargs={'slug': 'test-event'})
        # Just verify URL is not empty and contains the slug and api
        self.assertTrue(url)
        self.assertIn('test-event', url)
        self.assertIn('api', url)

    def test_availability_json_url_resolves(self):
        """Test availability JSON API URL resolves correctly."""
        url = reverse('event_detail:availability-json', kwargs={'slug': 'test-event'})
        # Just verify URL is not empty and contains the slug and availability
        self.assertTrue(url)
        self.assertIn('test-event', url)
        self.assertIn('availability', url)