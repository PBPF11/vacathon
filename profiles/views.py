import json

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView, UpdateView
from .forms import (
    AccountPasswordForm,
    AccountSettingsForm,
    ProfileAchievementForm,
    ProfileForm,
)
from .models import RunnerAchievement, UserProfile


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
