from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event, EventCategory
from forum.forms import PostForm, ThreadForm
from forum.models import ForumPost, ForumThread, PostReport

User = get_user_model()


class ForumThreadModelTests(TestCase):
    """Tests for ForumThread model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )

    def test_thread_form_missing_title(self):
        """Test form with missing title."""
        form = ThreadForm(data={
            'event': self.event.id,
            'body': 'Thread content',
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_thread_form_missing_body(self):
        """Test form with missing body."""
        form = ThreadForm(data={
            'event': self.event.id,
            'title': 'New Thread',
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('body', form.errors)

    def test_thread_form_missing_event(self):
        """Test form with missing event."""
        form = ThreadForm(data={
            'title': 'New Thread',
            'body': 'Thread content',
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('event', form.errors)


class PostFormTests(TestCase):
    """Tests for PostForm."""

    def test_post_form_valid_data(self):
        """Test form with valid data."""
        form = PostForm(data={'content': 'This is a valid post'})
        self.assertTrue(form.is_valid())

    def test_post_form_empty_content(self):
        """Test form with empty content."""
        form = PostForm(data={'content': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)

    def test_post_form_whitespace_only_content(self):
        """Test form with whitespace-only content."""
        form = PostForm(data={'content': '   '})
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)

    def test_post_form_strips_whitespace(self):
        """Test form strips leading/trailing whitespace."""
        form = PostForm(data={'content': '  Valid content  '})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['content'], 'Valid content')


class ForumIndexViewTests(TestCase):
    """Tests for ForumIndexView."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )

    def test_forum_index_requires_login(self):
        """Test forum index requires authentication."""
        response = self.client.get(reverse('forum:index'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_forum_index_accessible_when_logged_in(self):
        """Test forum index accessible to logged-in users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('forum:index'))
        self.assertEqual(response.status_code, 200)

    def test_forum_index_uses_correct_template(self):
        """Test forum index uses correct template."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('forum:index'))
        self.assertTemplateUsed(response, 'forum/index.html')

    def test_forum_index_displays_threads(self):
        """Test forum index displays threads."""
        self.client.login(username='testuser', password='testpass123')
        
        thread = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Test Thread",
            body="Test content",
        )
        
        response = self.client.get(reverse('forum:index'))
        self.assertContains(response, "Test Thread")

    def test_forum_index_pagination(self):
        """Test forum index pagination."""
        self.client.login(username='testuser', password='testpass123')
        
        # Create 15 threads (paginate_by is 10)
        for i in range(15):
            ForumThread.objects.create(
                event=self.event,
                author=self.user,
                title=f"Thread {i}",
                body=f"Content {i}",
            )
        
        response = self.client.get(reverse('forum:index'))
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['threads']), 10)

    def test_forum_index_filter_by_event(self):
        """Test filtering threads by event."""
        self.client.login(username='testuser', password='testpass123')
        
        event2 = Event.objects.create(
            title="Another Marathon",
            city="Bandung",
            country="Indonesia",
            start_date=self.today + timedelta(days=40),
            registration_deadline=self.today + timedelta(days=30),
        )
        
        thread1 = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Thread 1",
            body="Content 1",
        )
        
        thread2 = ForumThread.objects.create(
            event=event2,
            author=self.user,
            title="Thread 2",
            body="Content 2",
        )
        
        response = self.client.get(reverse('forum:index') + f'?event={self.event.id}')
        threads = response.context['threads']
        
        self.assertIn(thread1, threads)
        self.assertNotIn(thread2, threads)

    def test_forum_index_search(self):
        """Test searching threads by keyword."""
        self.client.login(username='testuser', password='testpass123')
        
        thread1 = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Marathon Training",
            body="Training tips",
        )
        
        thread2 = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Race Day Tips",
            body="Tips for race day",
        )
        
        response = self.client.get(reverse('forum:index') + '?q=Training')
        threads = response.context['threads']
        
        self.assertIn(thread1, threads)
        self.assertNotIn(thread2, threads)

    def test_forum_index_sort_by_recent(self):
        """Test sorting threads by recent activity."""
        self.client.login(username='testuser', password='testpass123')
        
        thread1 = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Old Thread",
            body="Old content",
        )
        
        thread2 = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="New Thread",
            body="New content",
        )
        thread2.touch()
        
        response = self.client.get(reverse('forum:index') + '?sort=recent')
        threads = list(response.context['threads'])
        
        self.assertEqual(threads[0], thread2)

    def test_forum_index_sort_by_popular(self):
        """Test sorting threads by popularity (post count)."""
        self.client.login(username='testuser', password='testpass123')
        
        thread1 = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Popular Thread",
            body="Popular content",
        )
        
        thread2 = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Unpopular Thread",
            body="Unpopular content",
        )
        
        # Add posts to thread1
        for i in range(5):
            ForumPost.objects.create(
                thread=thread1,
                author=self.user,
                content=f"Post {i}",
            )
        
        response = self.client.get(reverse('forum:index') + '?sort=popular')
        threads = list(response.context['threads'])
        
        self.assertEqual(threads[0], thread1)


class ThreadCreateViewTests(TestCase):
    """Tests for ThreadCreateView."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )

    def test_thread_create_requires_login(self):
        """Test thread creation requires authentication."""
        response = self.client.get(reverse('forum:thread-create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_thread_create_accessible_when_logged_in(self):
        """Test thread creation accessible to logged-in users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('forum:thread-create'))
        self.assertEqual(response.status_code, 200)

    def test_thread_create_uses_correct_template(self):
        """Test thread creation uses correct template."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('forum:thread-create'))
        self.assertTemplateUsed(response, 'forum/thread_create.html')

    def test_thread_create_valid_submission(self):
        """Test creating thread with valid data."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('forum:thread-create'), {
            'event': self.event.id,
            'title': 'New Thread',
            'body': 'Thread content',
        })
        
        self.assertEqual(ForumThread.objects.count(), 1)
        thread = ForumThread.objects.first()
        self.assertEqual(thread.title, 'New Thread')
        self.assertEqual(thread.author, self.user)

    def test_thread_create_redirects_to_detail(self):
        """Test successful creation redirects to thread detail."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('forum:thread-create'), {
            'event': self.event.id,
            'title': 'New Thread',
            'body': 'Thread content',
        })
        
        thread = ForumThread.objects.first()
        expected_url = reverse('forum:thread-detail', kwargs={'slug': thread.slug})
        self.assertRedirects(response, expected_url)

    def test_thread_create_invalid_submission(self):
        """Test creating thread with invalid data."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('forum:thread-create'), {
            'event': self.event.id,
            'title': '',  # Empty title
            'body': 'Thread content',
        })
        
        self.assertEqual(ForumThread.objects.count(), 0)
        self.assertFormError(response, 'form', 'title', 'This field is required.')


class ThreadDetailViewTests(TestCase):
    """Tests for ThreadDetailView."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        self.thread = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Test Thread",
            body="Test content",
        )

    def test_thread_detail_requires_login(self):
        """Test thread detail requires authentication."""
        response = self.client.get(
            reverse('forum:thread-detail', kwargs={'slug': self.thread.slug})
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_thread_detail_accessible_when_logged_in(self):
        """Test thread detail accessible to logged-in users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('forum:thread-detail', kwargs={'slug': self.thread.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_thread_detail_uses_correct_template(self):
        """Test thread detail uses correct template."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('forum:thread-detail', kwargs={'slug': self.thread.slug})
        )
        self.assertTemplateUsed(response, 'forum/thread_detail.html')

    def test_thread_detail_displays_posts(self):
        """Test thread detail displays posts."""
        self.client.login(username='testuser', password='testpass123')
        
        post = ForumPost.objects.create(
            thread=self.thread,
            author=self.user,
            content="Test post content",
        )
        
        response = self.client.get(
            reverse('forum:thread-detail', kwargs={'slug': self.thread.slug})
        )
        self.assertContains(response, "Test post content")

    def test_thread_detail_increments_view_count(self):
        """Test viewing thread increments view count."""
        self.client.login(username='testuser', password='testpass123')
        
        initial_count = self.thread.view_count
        
        self.client.get(
            reverse('forum:thread-detail', kwargs={'slug': self.thread.slug})
        )
        
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.view_count, initial_count + 1)

    def test_thread_detail_404_for_nonexistent(self):
        """Test 404 for non-existent thread."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('forum:thread-detail', kwargs={'slug': 'nonexistent'})
        )
        self.assertEqual(response.status_code, 404)

    def test_thread_detail_with_replies(self):
        """Test thread detail displays nested replies."""
        self.client.login(username='testuser', password='testpass123')
        
        parent_post = ForumPost.objects.create(
            thread=self.thread,
            author=self.user,
            content="Parent post",
        )
        
        reply = ForumPost.objects.create(
            thread=self.thread,
            author=self.user,
            content="Reply to parent",
            parent=parent_post,
        )
        
        response = self.client.get(
            reverse('forum:thread-detail', kwargs={'slug': self.thread.slug})
        )
        
        self.assertContains(response, "Parent post")
        self.assertContains(response, "Reply to parent")


class CreatePostViewTests(TestCase):
    """Tests for create_post view."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        self.thread = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Test Thread",
            body="Test content",
        )

    def test_create_post_requires_login(self):
        """Test creating post requires authentication."""
        response = self.client.post(
            reverse('forum:post-create', kwargs={'slug': self.thread.slug}),
            {'content': 'Test post'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_create_post_valid_data(self):
        """Test creating post with valid data."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('forum:post-create', kwargs={'slug': self.thread.slug}),
            {'content': 'Test post content'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(ForumPost.objects.count(), 1)

    def test_create_post_invalid_data(self):
        """Test creating post with invalid data."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('forum:post-create', kwargs={'slug': self.thread.slug}),
            {'content': ''}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

    def test_create_post_with_parent(self):
        """Test creating reply to another post."""
        self.client.login(username='testuser', password='testpass123')
        
        parent_post = ForumPost.objects.create(
            thread=self.thread,
            author=self.user,
            content="Parent post",
        )
        
        response = self.client.post(
            reverse('forum:post-create', kwargs={'slug': self.thread.slug}),
            {'content': 'Reply content', 'parent': parent_post.id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        reply = ForumPost.objects.get(parent=parent_post)
        self.assertEqual(reply.content, 'Reply content')

    def test_create_post_updates_thread_activity(self):
        """Test creating post updates thread last_activity_at."""
        self.client.login(username='testuser', password='testpass123')
        
        original_time = self.thread.last_activity_at
        
        self.client.post(
            reverse('forum:post-create', kwargs={'slug': self.thread.slug}),
            {'content': 'Test post'}
        )
        
        self.thread.refresh_from_db()
        self.assertGreater(self.thread.last_activity_at, original_time)


class ToggleLikeViewTests(TestCase):
    """Tests for toggle_like view."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        self.thread = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Test Thread",
            body="Test content",
        )
        self.post = ForumPost.objects.create(
            thread=self.thread,
            author=self.user,
            content="Test post",
        )

    def test_toggle_like_requires_login(self):
        """Test toggling like requires authentication."""
        response = self.client.post(
            reverse('forum:post-like', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_toggle_like_adds_like(self):
        """Test toggling adds like when not already liked."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('forum:post-like', kwargs={'post_id': self.post.id})
        )
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['liked'])
        self.assertEqual(data['like_count'], 1)

    def test_toggle_like_removes_like(self):
        """Test toggling removes like when already liked."""
        self.client.login(username='testuser', password='testpass123')
        
        self.post.likes.add(self.user)
        
        response = self.client.post(
            reverse('forum:post-like', kwargs={'post_id': self.post.id})
        )
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['liked'])
        self.assertEqual(data['like_count'], 0)

    def test_toggle_like_404_for_nonexistent_post(self):
        """Test 404 for non-existent post."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('forum:post-like', kwargs={'post_id': 99999})
        )
        self.assertEqual(response.status_code, 404)


class ReportPostViewTests(TestCase):
    """Tests for report_post view."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.reporter = User.objects.create_user(
            username='reporter',
            password='testpass123'
        )
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        self.thread = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Test Thread",
            body="Test content",
        )
        self.post = ForumPost.objects.create(
            thread=self.thread,
            author=self.user,
            content="Test post",
        )

    def test_report_post_requires_login(self):
        """Test reporting post requires authentication."""
        response = self.client.post(
            reverse('forum:post-report', kwargs={'post_id': self.post.id}),
            {'reason': 'Spam'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_report_post_valid_submission(self):
        """Test reporting post with valid data."""
        self.client.login(username='reporter', password='testpass123')
        
        response = self.client.post(
            reverse('forum:post-report', kwargs={'post_id': self.post.id}),
            {'reason': 'Inappropriate content'}
        )
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(PostReport.objects.count(), 1)

    def test_report_post_without_reason(self):
        """Test reporting post without reason fails."""
        self.client.login(username='reporter', password='testpass123')
        
        response = self.client.post(
            reverse('forum:post-report', kwargs={'post_id': self.post.id}),
            {'reason': ''}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

    def test_report_post_duplicate_report(self):
        """Test reporting same post twice fails."""
        self.client.login(username='reporter', password='testpass123')
        
        PostReport.objects.create(
            post=self.post,
            reporter=self.reporter,
            reason="First report",
        )
        
        response = self.client.post(
            reverse('forum:post-report', kwargs={'post_id': self.post.id}),
            {'reason': 'Second report'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])


class ForumURLTests(TestCase):
    """Test URL configuration for forum app."""

    def test_forum_index_url_resolves(self):
        """Test forum index URL resolves correctly."""
        url = reverse('forum:index')
        self.assertEqual(url, '/forum/')

    def test_thread_create_url_resolves(self):
        """Test thread create URL resolves correctly."""
        url = reverse('forum:thread-create')
        self.assertEqual(url, '/forum/threads/new/')

    def test_thread_detail_url_resolves(self):
        """Test thread detail URL resolves correctly."""
        url = reverse('forum:thread-detail', kwargs={'slug': 'test-thread'})
        self.assertEqual(url, '/forum/threads/test-thread/')

    def test_post_create_url_resolves(self):
        """Test post create URL resolves correctly."""
        url = reverse('forum:post-create', kwargs={'slug': 'test-thread'})
        self.assertEqual(url, '/forum/threads/test-thread/posts/')

    def test_post_like_url_resolves(self):
        """Test post like URL resolves correctly."""
        url = reverse('forum:post-like', kwargs={'post_id': 1})
        self.assertEqual(url, '/forum/posts/1/like/')

    def test_post_report_url_resolves(self):
        """Test post report URL resolves correctly."""
        url = reverse('forum:post-report', kwargs={'post_id': 1})
        self.assertEqual(url, '/forum/posts/1/report/')

    def test_threads_json_url_resolves(self):
        """Test threads JSON API URL resolves correctly."""
        url = reverse('forum:threads-json')
        self.assertEqual(url, '/forum/api/threads/')
    def test_create_forum_thread(self):
        """Test creating a forum thread."""
        thread = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Training Tips",
            body="What are your favorite training routines?",
        )
        
        self.assertEqual(thread.event, self.event)
        self.assertEqual(thread.author, self.user)
        self.assertEqual(thread.title, "Training Tips")
        self.assertFalse(thread.is_pinned)
        self.assertFalse(thread.is_locked)

    def test_forum_thread_slug_auto_generation(self):
        """Test slug is automatically generated."""
        thread = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="My Marathon Experience",
            body="Sharing my story",
        )
        
        self.assertEqual(thread.slug, "my-marathon-experience")

    def test_forum_thread_slug_uniqueness(self):
        """Test duplicate titles get unique slugs."""
        thread1 = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Tips",
            body="First thread",
        )
        
        thread2 = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Tips",
            body="Second thread",
        )
        
        self.assertEqual(thread1.slug, "tips")
        self.assertEqual(thread2.slug, "tips-1")

    def test_forum_thread_str_representation(self):
        """Test string representation of ForumThread."""
        thread = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Test Thread",
            body="Test content",
        )
        
        self.assertEqual(str(thread), "Test Thread")

    def test_forum_thread_ordering(self):
        """Test threads are ordered by pinned then last_activity."""
        thread1 = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Regular Thread",
            body="Regular content",
            is_pinned=False,
        )
        
        thread2 = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Pinned Thread",
            body="Important content",
            is_pinned=True,
        )
        
        threads = list(ForumThread.objects.all())
        self.assertEqual(threads[0], thread2)  # Pinned first
        self.assertEqual(threads[1], thread1)

    def test_forum_thread_touch_method(self):
        """Test touch method updates last_activity_at."""
        thread = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Test Thread",
            body="Test content",
        )
        
        original_time = thread.last_activity_at
        thread.touch()
        thread.refresh_from_db()
        
        self.assertGreater(thread.last_activity_at, original_time)

    def test_forum_thread_default_view_count(self):
        """Test default view count is 0."""
        thread = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Test Thread",
            body="Test content",
        )
        
        self.assertEqual(thread.view_count, 0)


class ForumPostModelTests(TestCase):
    """Tests for ForumPost model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        self.thread = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Test Thread",
            body="Test content",
        )

    def test_create_forum_post(self):
        """Test creating a forum post."""
        post = ForumPost.objects.create(
            thread=self.thread,
            author=self.user,
            content="This is my reply to the thread.",
        )
        
        self.assertEqual(post.thread, self.thread)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.content, "This is my reply to the thread.")
        self.assertIsNone(post.parent)

    def test_forum_post_str_representation(self):
        """Test string representation of ForumPost."""
        post = ForumPost.objects.create(
            thread=self.thread,
            author=self.user,
            content="Test post",
        )
        
        expected_str = f"Post by {self.user} on {self.thread}"
        self.assertEqual(str(post), expected_str)

    def test_forum_post_like_count(self):
        """Test like_count property."""
        post = ForumPost.objects.create(
            thread=self.thread,
            author=self.user,
            content="Test post",
        )
        
        user2 = User.objects.create_user(username='user2', password='pass')
        user3 = User.objects.create_user(username='user3', password='pass')
        
        post.likes.add(user2, user3)
        
        self.assertEqual(post.like_count, 2)

    def test_forum_post_reply_relationship(self):
        """Test parent-reply relationship."""
        parent_post = ForumPost.objects.create(
            thread=self.thread,
            author=self.user,
            content="Parent post",
        )
        
        reply = ForumPost.objects.create(
            thread=self.thread,
            author=self.user,
            content="Reply to parent",
            parent=parent_post,
        )
        
        self.assertEqual(reply.parent, parent_post)
        self.assertIn(reply, parent_post.replies.all())

    def test_forum_post_ordering(self):
        """Test posts are ordered by created_at."""
        post1 = ForumPost.objects.create(
            thread=self.thread, author=self.user, content="First post"
        )
        
        post2 = ForumPost.objects.create(
            thread=self.thread, author=self.user, content="Second post"
        )
        
        post3 = ForumPost.objects.create(
            thread=self.thread, author=self.user, content="Third post"
        )
        
        posts = list(ForumPost.objects.all())
        self.assertEqual(posts[0], post1)
        self.assertEqual(posts[1], post2)
        self.assertEqual(posts[2], post3)


class PostReportModelTests(TestCase):
    """Tests for PostReport model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.reporter = User.objects.create_user(
            username='reporter',
            password='testpass123'
        )
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )
        self.thread = ForumThread.objects.create(
            event=self.event,
            author=self.user,
            title="Test Thread",
            body="Test content",
        )
        self.post = ForumPost.objects.create(
            thread=self.thread,
            author=self.user,
            content="Test post",
        )

    def test_create_post_report(self):
        """Test creating a post report."""
        report = PostReport.objects.create(
            post=self.post,
            reporter=self.reporter,
            reason="Inappropriate content",
        )
        
        self.assertEqual(report.post, self.post)
        self.assertEqual(report.reporter, self.reporter)
        self.assertEqual(report.reason, "Inappropriate content")
        self.assertFalse(report.resolved)

    def test_post_report_str_representation(self):
        """Test string representation of PostReport."""
        report = PostReport.objects.create(
            post=self.post,
            reporter=self.reporter,
            reason="Spam",
        )
        
        expected_str = f"Report by {self.reporter} on {self.post.id}"
        self.assertEqual(str(report), expected_str)

    def test_post_report_unique_together(self):
        """Test one user can only report a post once."""
        PostReport.objects.create(
            post=self.post,
            reporter=self.reporter,
            reason="First report",
        )
        
        with self.assertRaises(Exception):
            PostReport.objects.create(
                post=self.post,
                reporter=self.reporter,
                reason="Second report",
            )

    def test_post_report_default_resolved_false(self):
        """Test default resolved value is False."""
        report = PostReport.objects.create(
            post=self.post,
            reporter=self.reporter,
            reason="Test",
        )
        
        self.assertFalse(report.resolved)


class ThreadFormTests(TestCase):
    """Tests for ThreadForm."""

    def setUp(self):
        self.today = timezone.localdate()
        self.event = Event.objects.create(
            title="Test Marathon",
            city="Jakarta",
            country="Indonesia",
            start_date=self.today + timedelta(days=30),
            registration_deadline=self.today + timedelta(days=20),
        )

    def test_thread_form_valid_data(self):
        """Test form with valid data."""
        form = ThreadForm(data={
            'event': self.event.id,
            'title': 'New Thread',
            'body': 'Thread content',
        })
        
        self.assertTrue(form.is_valid())
