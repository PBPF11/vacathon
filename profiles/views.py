import json
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, JsonResponse
from forum.models import ForumThread, ForumPost, PostReport

from .forms import (
    EventForm,
    ProfileForm,
    AccountSettingsForm,
    AccountPasswordForm,
    ProfileAchievementForm,
)
from django.db.models import Count
from .models import UserRaceHistory, RunnerAchievement, UserProfile
from events.models import Event, EventCategory
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, UpdateView
from core import models # Dipertahankan karena ada di impor Anda sebelumnya
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db import IntegrityError

def is_admin(user):
    return user.is_staff or user.is_superuser

def admin_required(view_func):
    return user_passes_test(is_admin)(view_func)

@login_required
@user_passes_test(admin_required)
def admin_event_list(request):
    events = Event.objects.all().order_by("start_date")
    return render(request, "profiles/admin_event_list.html", {"events": events})

@login_required
@user_passes_test(admin_required)
def admin_event_add(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    is_partial = request.GET.get('partial') == 'true'

    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Event created successfully!',
                }, status=201)
            messages.success(request, "Event created successfully")
            return redirect("profiles:admin-event-list")
        else:
            if is_ajax:
                context = {"form": form, "title": "Add Event"}
                html_form = render_to_string("profiles/admin_event_form_partial.html", context, request=request)
                
                return JsonResponse({
                    'status': 'error',
                    'form_html': html_form,
                    'message': 'Form validation failed.',
                }, status=400)
            
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return render(request, "profiles/admin_event_form.html", {"form": form, "title": "Add Event"})
    
    # Handle GET request
    form = EventForm()
    context = {"form": form, "title": "Add Event"}
    
    if is_partial:
        # Mengembalikan HTML murni untuk modal AJAX
        return render(request, "profiles/admin_event_form_partial.html", context)
    
    # Fallback untuk GET non-AJAX
    return render(request, "profiles/admin_event_form.html", context)

@login_required
@user_passes_test(admin_required)
def admin_event_edit(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Event updated successfully")
            return redirect("profiles:admin-event-list")
    else:
        form = EventForm(instance=event)
    return render(request, "profiles/admin_event_form.html", {"form": form, "title": "Edit Event"})

@login_required
@user_passes_test(admin_required)
def admin_event_delete(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    messages.success(request, "Event deleted successfully")
    return redirect("profiles:admin-event-list")


@method_decorator(user_passes_test(is_admin), name="dispatch")
class AdminDashboardView(TemplateView):
    template_name = "profiles/admin_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        total_peserta = UserRaceHistory.objects.count()
        total_event = Event.objects.count()
        event_aktif = Event.objects.filter(status="upcoming").count()
        event_selesai = Event.objects.filter(status="completed").count()
        
        peserta_per_event = (
            UserRaceHistory.objects.values("event__title")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        context.update({
            "total_participants": total_peserta,
            "total_events": total_event,
            "events_active": event_aktif,
            "events_completed": event_selesai,
            "participants_per_event": peserta_per_event,
        })
        return context

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created. You can now log in.')
            return redirect('profiles:login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_staff:
                return redirect("profiles:admin-dashboard")
            return redirect("profiles:dashboard")
    else:
        form = AuthenticationForm()
    return render(request, "registration/login.html", {"form": form})

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "profiles/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        history = (
            profile.history.select_related("event")
            .order_by("-registration_date")
        )
        upcoming = history.filter(status__in=["upcoming", "registered"])
        completed = history.filter(status="completed")

        context.update(
            {
                "profile": profile,
                "upcoming_history": upcoming[:5],
                "completed_history": completed[:5],
                "achievements": profile.achievements.all(),
                "stats": {
                    "total_events": history.count(),
                    "completed": completed.count(),
                    "upcoming": upcoming.count(),
                },
                "next_event": upcoming.order_by("event__start_date").first(),
            }
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = ProfileForm
    template_name = "profiles/profile_form.html"

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("profiles:dashboard")


class AccountSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "profiles/account_settings.html"

    def get_forms(self):
        user = self.request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile_form = ProfileForm(instance=profile, prefix="profile")
        account_form = AccountSettingsForm(instance=user, prefix="account")
        password_form = AccountPasswordForm(user, prefix="password")
        return profile_form, account_form, password_form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forms = kwargs.get("forms") or self.get_forms()
        context["profile_form"], context["account_form"], context["password_form"] = forms
        context["achievements"] = self.request.user.profile.achievements.all()
        context["achievement_form"] = ProfileAchievementForm(prefix="achievement")
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        profile_form = ProfileForm(
            data=request.POST if action == "profile" else None,
            instance=profile,
            prefix="profile",
        )
        account_form = AccountSettingsForm(
            data=request.POST if action == "account" else None,
            instance=user,
            prefix="account",
        )
        password_form = AccountPasswordForm(
            user,
            data=request.POST if action == "password" else None,
            prefix="password",
        )

        success = False
        if action == "profile" and profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Profile information updated.")
            success = True
        elif action == "account" and account_form.is_valid():
            account_form.save()
            messages.success(request, "Account details updated.")
            success = True
        elif action == "password" and password_form.is_valid():
            password_form.save()
            update_session_auth_hash(request, password_form.user)
            messages.success(request, "Password updated successfully.")
            success = True

        if success:
            return redirect("profiles:settings")

        return self.render_to_response(
            self.get_context_data(
                forms=(profile_form, account_form, password_form)
            )
        )


@login_required
@require_http_methods(["GET"])
def profile_json(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    history = profile.history.select_related("event")

    data = {
        "username": request.user.username,
        "display_name": profile.full_display_name,
        "bio": profile.bio,
        "city": profile.city,
        "country": profile.country,
        "favorite_distance": profile.favorite_distance,
        "avatar_url": profile.avatar_url,
        "achievements": [
            {
                "id": achievement.id,
                "title": achievement.title,
                "description": achievement.description,
                "achieved_on": achievement.achieved_on.isoformat()
                if achievement.achieved_on
                else None,
                "link": achievement.link,
                "delete_url": reverse("profiles:achievement-delete", args=[achievement.id]),
            }
            for achievement in profile.achievements.all()
        ],
        "history": [
            {
                "event": item.event.title,
                "event_slug": item.event.slug,
                "status": item.status,
                "registration_date": item.registration_date.isoformat(),
                "category": item.category,
                "finish_time": item.finish_time.total_seconds() if item.finish_time else None,
                "certificate_url": item.certificate_url,
            }
            for item in history
        ],
    }
    return JsonResponse(data)


@login_required
@require_http_methods(["GET", "POST"])
def achievements_api(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "GET":
        achievements = [
            {
                "id": achievement.id,
                "title": achievement.title,
                "description": achievement.description,
                "achieved_on": achievement.achieved_on.isoformat()
                if achievement.achieved_on
                else None,
                "link": achievement.link,
                "delete_url": reverse("profiles:achievement-delete", args=[achievement.id]),
            }
            for achievement in profile.achievements.all()
        ]
        return JsonResponse({"results": achievements})

    payload = json.loads(request.body or "{}")
    form = ProfileAchievementForm(payload)
    if form.is_valid():
        achievement = form.save(commit=False)
        achievement.profile = profile
        achievement.save()
        return JsonResponse(
            {
                "success": True,
                "achievement": {
                    "id": achievement.id,
                    "title": achievement.title,
                    "description": achievement.description,
                    "achieved_on": achievement.achieved_on.isoformat()
                    if achievement.achieved_on
                    else None,
                    "link": achievement.link,
                    "delete_url": reverse("profiles:achievement-delete", args=[achievement.id]),
                },
            },
            status=201,
        )

    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_http_methods(["DELETE"])
def delete_achievement(request, achievement_id):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    achievement = get_object_or_404(RunnerAchievement, pk=achievement_id, profile=profile)
    achievement.delete()
    return JsonResponse({"success": True})


@login_required
@user_passes_test(is_admin)
def admin_participant_list(request):
    participants = UserRaceHistory.objects.select_related(
        'profile__user', 'event'
    ).all().order_by('-registration_date')
    
    context = {
        'participants': participants,
    }
    return render(request, 'profiles/admin_participant_list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_participant_confirm(request, participant_id):
    if request.method == "POST":
        participant = get_object_or_404(UserRaceHistory, id=participant_id)
        participant.status = UserRaceHistory.Status.UPCOMING  # Changed to UPCOMING to match CONFIRMED sync
        # Generate BIB number kalau belum ada
        if not participant.bib_number:
            import random
            participant.bib_number = f"{participant.event.id}{participant.profile.user.id}{random.randint(100, 999)}"
        participant.save()

        # Also update the EventRegistration status to CONFIRMED
        from registrations.models import EventRegistration
        registration = EventRegistration.objects.filter(
            user=participant.profile.user,
            event=participant.event
        ).first()
        if registration:
            registration.status = EventRegistration.Status.CONFIRMED
            registration.save()

        messages.success(request, f"Participant {participant.profile.full_display_name} confirmed!")
    return redirect('profiles:admin-participant-list')


@login_required
@user_passes_test(is_admin)
def admin_participant_delete(request, participant_id):
    if request.method == "POST":
        participant = get_object_or_404(UserRaceHistory, id=participant_id)
        # Also delete the EventRegistration
        from registrations.models import EventRegistration
        registration = EventRegistration.objects.filter(
            user=participant.profile.user,
            event=participant.event
        ).first()
        if registration:
            # Send cancellation notification before deleting
            from notifications.utils import send_notification
            from notifications.models import Notification
            detail_kwargs = {"reference": registration.reference_code}
            send_notification(
                recipient=registration.user,
                title=f"Registration cancelled - {registration.event.title}",
                message="Your registration has been cancelled by an administrator. Contact support for more details.",
                category=Notification.Category.REGISTRATION,
                url_name="registrations:detail",
                url_kwargs=detail_kwargs,
            )
            registration.delete()
        participant.delete()
        messages.success(request, "Participant deleted successfully!")
    return redirect('profiles:admin-participant-list')


@login_required
@user_passes_test(is_admin)
def admin_forum(request):
    reported_posts = PostReport.objects.filter(
        resolved=False
    ).select_related(
        'post__author',
        'post__thread__event',
        'reporter'
    ).prefetch_related('post__reports').order_by('-created_at')
    
    posts_with_reports = []
    seen_posts = set()
    
    for report in reported_posts:
        post = report.post
        if post.id not in seen_posts:
            seen_posts.add(post.id)
            posts_with_reports.append({
                'post': post,
                'thread': post.thread,
                'reports': post.reports.filter(resolved=False)
            })
    
    context = {
        'posts': posts_with_reports,
        'total_reports': reported_posts.count(),
    }
    return render(request, 'profiles/admin_forum.html', context)


@login_required
@user_passes_test(is_admin)
def admin_forum_delete(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(ForumPost, id=post_id)
        
        post.reports.all().update(resolved=True)
        author_username = post.author.username
        post.delete()

        messages.success(request, f"Post by {author_username} has been deleted!")
    return redirect('profiles:admin-forum')


@login_required
@user_passes_test(is_admin)
def admin_forum_pinned(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(ForumPost, id=post_id)
        thread = post.thread
        
        thread.is_pinned = not thread.is_pinned
        thread.save()
        
        status = "pinned" if thread.is_pinned else "unpinned"
        messages.success(request, f"Thread '{thread.title}' has been {status}!")
    return redirect('profiles:admin-forum')


@login_required
@user_passes_test(is_admin)
def admin_forum_resolve(request, report_id):
    if request.method == "POST":
        report = get_object_or_404(PostReport, id=report_id)
        report.resolved = True
        report.save()
        messages.success(request, "Report has been resolved!")
    return redirect('profiles:admin-forum')

@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        # --- UPDATE DISINI: Handle JSON atau Form Data ---
        try:
            # Coba baca sebagai JSON
            data = json.loads(request.body)
        except json.JSONDecodeError:
            # Jika error, berarti dikirim sebagai Form Data biasa (request.POST)
            data = request.POST
        
        # Ambil username/password dari data yang sudah diproses
        username = data.get('username')
        password = data.get('password')
        # --------------------------------------------------

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({
                "status": True,
                "message": "Berhasil login!",
                "username": username,
            }, status=200)
        else:
            return JsonResponse({
                "status": False,
                "message": "Username atau password salah.",
            }, status=401)
    return JsonResponse({"status": False, "message": "Method not allowed"}, status=405)

@csrf_exempt
def logout_api(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({
            "status": True,
            "message": "Berhasil logout!",
        }, status=200)
    return JsonResponse({"status": False, "message": "Method not allowed"}, status=405)

@csrf_exempt
def register_api(request):
    if request.method == 'POST':
        # --- UPDATE DISINI JUGA ---
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST
        
        username = data.get('username')
        password = data.get('password')
        # --------------------------
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({"status": False, "message": "Username sudah digunakan"}, status=400)
        
        try:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            return JsonResponse({"status": True, "message": "Akun berhasil dibuat!"}, status=201)
        except Exception as e:
            return JsonResponse({"status": False, "message": str(e)}, status=500)
            
    return JsonResponse({"status": False, "message": "Method not allowed"}, status=405)

def user_profile_json(request):
    # Mengambil data user yang sedang login (Session-based)
    if not request.user.is_authenticated:
        return JsonResponse({"status": False, "message": "Belum login"}, status=401)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    # Format JSON sesuai UserProfile.fromJson di Flutter
    return JsonResponse({
        "id": profile.id,
        "username": request.user.username,
        "display_name": profile.full_display_name,
        "bio": profile.bio,
        "city": profile.city,
        "country": profile.country,
        "avatar_url": profile.avatar_url,
        "favorite_distance": profile.favorite_distance,
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
        "history": [], # Tambahkan logika history jika perlu
        "achievements": [], # Tambahkan logika achievements jika perlu
        "is_superuser": request.user.is_superuser,
        "is_staff": request.user.is_staff
    })

@csrf_exempt
@login_required
@require_POST
def update_profile_json(request):
    try:
        data = json.loads(request.body)
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        # Update User fields (jika ada)
        # user.first_name = data.get('first_name', user.first_name)
        # user.save()

        # Update Profile fields
        profile.display_name = data.get('display_name', profile.display_name)
        profile.bio = data.get('bio', profile.bio)
        profile.city = data.get('city', profile.city)
        profile.country = data.get('country', profile.country)
        profile.favorite_distance = data.get('favorite_distance', profile.favorite_distance)
        profile.emergency_contact_name = data.get('emergency_contact_name', profile.emergency_contact_name)
        profile.emergency_contact_phone = data.get('emergency_contact_phone', profile.emergency_contact_phone)
        profile.website = data.get('website', profile.website)
        profile.instagram_handle = data.get('instagram_handle', profile.instagram_handle)
        
        # Handle tanggal lahir (parse string ISO 8601 dari Flutter)
        birth_date_str = data.get('birth_date')
        if birth_date_str:
            try:
                # Ambil bagian tanggal saja 'YYYY-MM-DD' jika formatnya panjang
                profile.birth_date = birth_date_str.split('T')[0] 
            except:
                pass

        profile.save()

        return JsonResponse({
            'status': True, 
            'message': 'Profil berhasil diperbarui',
            # Kembalikan data profil terbaru agar UI bisa langsung update
            'profile': {
                "id": profile.id,
                "username": user.username,
                "display_name": profile.full_display_name,
                "bio": profile.bio,
                "city": profile.city,
                "country": profile.country,
                # ... tambahkan field lain jika perlu untuk respons instan
            }
        })

    except Exception as e:
        return JsonResponse({'status': False, 'message': str(e)}, status=500)