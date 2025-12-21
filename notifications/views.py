
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView
from django.views.decorators.csrf import csrf_exempt

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
def notifications_json(request):
    notifications = Notification.objects.filter(recipient=request.user)
    
    # LOGIKA BARU: Tangkap parameter 'unread' dari Flutter
    unread_only = request.GET.get('unread') == 'true'
    if unread_only:
        notifications = notifications.filter(is_read=False)
    
    notifications = notifications.order_by('-created_at')
    
    results = []
    for notif in notifications:
        results.append({
            "id": notif.id,
            "title": notif.title,
            "message": notif.message,
            "category": notif.category,
            "is_read": notif.is_read,
            "link_url": notif.link_url,
            "created_at": notif.created_at.isoformat(),
        })
        
    return JsonResponse({
        "results": results,
        "unread": Notification.objects.filter(recipient=request.user, is_read=False).count()
    })


@csrf_exempt
@login_required
def mark_notification_read(request, notif_id):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
        notification.mark_read() # Ganti .save() manual pake method ini
        return JsonResponse({"status": "success", "message": "Notification marked as read"})
    return JsonResponse({"status": "error"}, status=400)


@csrf_exempt
@login_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        # Update semua notifikasi user ini sekaligus
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({"status": "success", "message": "All notifications marked as read"})
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)
