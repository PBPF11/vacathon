from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import DetailView, ListView, CreateView
from django.template.loader import render_to_string
from django.db.models import Count, Q, F
from django.views.decorators.csrf import csrf_exempt
import json

from events.models import Event
from .forms import PostForm, ThreadForm
from .models import ForumPost, ForumThread, PostReport


class ForumIndexView(LoginRequiredMixin, ListView):
    template_name = "forum/index.html"
    context_object_name = "threads"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            ForumThread.objects.select_related("event", "author")
            .annotate(post_count=Count("posts", distinct=True))
        )
        self.event_filter = self.request.GET.get("event")
        self.search_term = self.request.GET.get("q", "")
        self.sort = self.request.GET.get("sort", "recent")

        if self.event_filter:
            queryset = queryset.filter(event_id=self.event_filter)
        if self.search_term:
            queryset = queryset.filter(
                Q(title__icontains=self.search_term) | Q(body__icontains=self.search_term)
            )

        if self.sort == "popular":
            queryset = queryset.order_by("-is_pinned", "-post_count")
        elif self.sort == "latest":
            queryset = queryset.order_by("-is_pinned", "-created_at")
        else:
            queryset = queryset.order_by("-is_pinned", "-last_activity_at")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["events"] = Event.objects.order_by("title")
        context["active_event"] = self.event_filter
        context["search_term"] = self.search_term
        context["sort"] = self.sort
        if self.request.user.is_authenticated:
            context["thread_form"] = ThreadForm()
        return context


class ThreadCreateView(LoginRequiredMixin, CreateView):
    model = ForumThread
    form_class = ThreadForm
    template_name = "forum/thread_create.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Thread created successfully.")
        return response

    def get_success_url(self):
        return reverse("forum:thread-detail", kwargs={"slug": self.object.slug})


class ThreadDetailView(LoginRequiredMixin, DetailView):
    model = ForumThread
    context_object_name = "thread"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "forum/thread_detail.html"

    def get_queryset(self):
        return ForumThread.objects.select_related("author", "event").prefetch_related(
            "posts__author",
            "posts__likes",
            "posts__replies__author",
            "posts__replies__likes",
        )

    def get_object(self, queryset=None):
        thread = super().get_object(queryset)
        ForumThread.objects.filter(pk=thread.pk).update(view_count=F("view_count") + 1)
        thread.refresh_from_db()
        return thread

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = context["thread"]
        posts = (
            thread.posts.filter(parent__isnull=True)
            .select_related("author")
            .prefetch_related("likes", "replies__author", "replies__likes")
            .order_by("created_at")
        )
        context["posts"] = posts
        context["post_form"] = PostForm()
        context["now"] = timezone.now()
        context["breadcrumbs"] = [
            {"label": "Forum", "url": reverse("forum:index")},
            {"label": thread.title, "url": ""},
        ]
        return context


@require_GET
def threads_json(request):
    queryset = (
        ForumThread.objects.select_related("event", "author")
        .annotate(post_count=Count("posts", distinct=True))
    )
    event_filter = request.GET.get("event")
    search_term = request.GET.get("q", "")
    sort = request.GET.get("sort", "recent")

    if event_filter:
        queryset = queryset.filter(event_id=event_filter)
    if search_term:
        queryset = queryset.filter(Q(title__icontains=search_term) | Q(body__icontains=search_term))

    if sort == "popular":
        queryset = queryset.order_by("-is_pinned", "-post_count")
    elif sort == "latest":
        queryset = queryset.order_by("-is_pinned", "-created_at")
    else:
        queryset = queryset.order_by("-is_pinned", "-last_activity_at")

    threads_payload = [
        {
            "id": thread.id,
            "event": thread.event.id,
            "author": thread.author.id,
            "author_username": thread.author.username,
            "title": thread.title,
            "slug": thread.slug,
            "body": thread.body,
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
            "url": reverse("forum:thread-detail", kwargs={"slug": thread.slug}),
            "event": thread.event.id,
            "event_title": thread.event.title,
            "author": thread.author.username,
            "last_activity_at": thread.last_activity_at.isoformat(),
            "is_pinned": thread.is_pinned,
            "is_locked": thread.is_locked,
            "view_count": thread.view_count,
            "post_count": thread.post_count,
        }
        for thread in queryset[:50]
    ]
    return JsonResponse({"results": threads_payload})

@require_GET
def api_thread_posts(request, slug):
    thread = get_object_or_404(ForumThread, slug=slug)
    posts = thread.posts.select_related("author").order_by("created_at")
    
    # Pagination sederhana jika perlu
    from django.core.paginator import Paginator
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    posts_data = [
        {
            "id": post.id,
            "thread": thread.id,
            "author": post.author.id,
            "author_username": post.author.username,
            "parent": post.parent_id,
            "content": post.content,
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat(),
            "likes_count": post.likes.count(),
            "is_liked_by_user": request.user in post.likes.all() if request.user.is_authenticated else False
        }
        for post in page_obj
    ]

    return JsonResponse({
        "results": posts_data,
        "total": paginator.count,
        "has_next": page_obj.has_next()
    })

@csrf_exempt
@login_required
@require_POST
def create_thread_json(request):
    try:
        data = json.loads(request.body)
        event_id = data.get('event')
        title = data.get('title')
        body = data.get('body')

        if not all([event_id, title, body]):
            return JsonResponse({'status': False, 'message': 'Semua field harus diisi'}, status=400)

        event = get_object_or_404(Event, pk=event_id)
        
        thread = ForumThread.objects.create(
            event=event,
            author=request.user,
            title=title,
            body=body
        )

        # Return full thread data to match ForumThread.fromJson in Flutter
        return JsonResponse({
            "id": thread.id,
            "event": thread.event.id,
            "event_title": thread.event.title,
            "author": thread.author.id,
            "author_username": thread.author.username,
            "title": thread.title,
            "slug": thread.slug,
            "body": thread.body,
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
            "last_activity_at": thread.last_activity_at.isoformat(),
            "is_pinned": thread.is_pinned,
            "is_locked": thread.is_locked,
            "view_count": thread.view_count,
            "post_count": 0, # Newly created thread has 0 posts
        }, status=201)

    except Exception as e:
        return JsonResponse({'status': False, 'message': str(e)}, status=500)

@csrf_exempt # Tambahkan ini
@login_required
@require_POST
def create_post(request, slug):
    thread = get_object_or_404(ForumThread, slug=slug)
    
    # Handle JSON input
    import json
    try:
        data = json.loads(request.body)
        form = PostForm(data)
        parent_id = data.get("parent")
    except:
        form = PostForm(request.POST)
        parent_id = request.POST.get("parent")

    if form.is_valid():
        post = form.save(commit=False)
        post.thread = thread
        post.author = request.user
        
        if parent_id:
            try:
                parent_post = ForumPost.objects.get(pk=parent_id, thread=thread)
                post.parent = parent_post
            except ForumPost.DoesNotExist:
                pass 
        
        post.save()
        thread.touch()
        
        # Return JSON Data Post Lengkap
        return JsonResponse({
            "success": True,
            "post_id": post.id, # Keep for backward compatibility
            "parent_id": post.parent_id,
            # Data objek lengkap untuk Flutter ForumPost.fromJson:
            "id": post.id,
            "thread": thread.id,
            "author": post.author.id,
            "author_username": post.author.username,
            "parent": post.parent_id,
            "content": post.content,
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat(),
            "likes_count": 0,
            "is_liked_by_user": False
        })

    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(ForumPost, pk=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return JsonResponse({"success": True, "liked": liked, "like_count": post.like_count})


@login_required
@require_POST
def report_post(request, post_id):
    post = get_object_or_404(ForumPost, pk=post_id)
    reason = request.POST.get("reason", "").strip()
    if not reason:
        return JsonResponse({"success": False, "message": "Reason is required."}, status=400)

    report, created = PostReport.objects.get_or_create(
        post=post,
        reporter=request.user,
        defaults={"reason": reason},
    )
    if not created:
        return JsonResponse({"success": False, "message": "You already reported this post."}, status=400)
    return JsonResponse({"success": True, "message": "Report submitted. Thank you for keeping the forum safe."})

@csrf_exempt
@login_required
@require_POST
def delete_thread_api(request, slug):
    try:
        thread = get_object_or_404(ForumThread, slug=slug)
        
        # Cek permission: Author atau Admin
        if request.user != thread.author and not request.user.is_staff and not request.user.is_superuser:
             return JsonResponse({
                'status': False,
                'message': 'Anda tidak memiliki izin untuk menghapus thread ini.'
            }, status=403)
            
        thread.delete()
        return JsonResponse({
            'status': True,
            'message': 'Thread berhasil dihapus'
        })
    except Exception as e:
        return JsonResponse({
            'status': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@login_required
@require_POST
def delete_post_api(request, post_id):
    try:
        post = get_object_or_404(ForumPost, pk=post_id)
        
        # Cek permission: Author atau Admin
        if request.user != post.author and not request.user.is_staff and not request.user.is_superuser:
             return JsonResponse({
                'status': False,
                'message': 'Anda tidak memiliki izin untuk menghapus post ini.'
            }, status=403)
            
        post.delete()
        return JsonResponse({
            'status': True,
            'message': 'Post berhasil dihapus'
        })
    except Exception as e:
        return JsonResponse({
            'status': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_GET
def api_thread_detail(request, slug):
    print(f"DEBUG: api_thread_detail called for {slug}")
    thread = get_object_or_404(ForumThread, slug=slug)
    
    # Increment View Count
    ForumThread.objects.filter(pk=thread.pk).update(view_count=F("view_count") + 1)
    thread.refresh_from_db()
    
    thread_data = {
        "id": thread.id,
        "event": thread.event.id,
        "event_title": thread.event.title,
        "author": thread.author.id,
        "author_username": thread.author.username,
        "title": thread.title,
        "slug": thread.slug,
        "body": thread.body,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
        "last_activity_at": thread.last_activity_at.isoformat(),
        "is_pinned": thread.is_pinned,
        "is_locked": thread.is_locked,
        "view_count": thread.view_count,
    }
    return JsonResponse(thread_data)
