def notifications_summary(request):
    if request.user.is_authenticated:
        unread = request.user.notifications.filter(is_read=False).count()
        return {"notifications_unread_count": unread}
    return {}
