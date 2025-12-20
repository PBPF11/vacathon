
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    template_name = "notifications/inbox.html"
    context_object_name = "notifications"
    paginate_by = 12

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["unread_count"] = Notification.objects.filter(
            recipient=self.request.user, is_read=False
        ).count()
        return context


@login_required
@require_GET
def notifications_json(request):
    base_qs = Notification.objects.filter(recipient=request.user).order_by("-created_at")
    notifications = list(base_qs[:50])
    unread_count = base_qs.filter(is_read=False).count()
    return JsonResponse(
        {
            "results": [
                {
                    "id": note.id,
                    "title": note.title,
                    "message": note.message,
                    "category": note.category,
                    "is_read": note.is_read,
                    "created_at": note.created_at.isoformat(),
                    "link_url": note.link_url,
                }
                for note in notifications
            ],
            "unread": unread_count,
        }
    )


@login_required
@require_POST
def mark_notification_read(request, pk):
    note = get_object_or_404(Notification, pk=pk, recipient=request.user)
    note.mark_read()
    return JsonResponse({"success": True})


@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"success": True})
