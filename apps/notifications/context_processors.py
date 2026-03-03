from .services import get_unread_count


def notifications(request):
    if not hasattr(request, "user") or not request.user.is_authenticated:
        return {"unread_notification_count": 0}
    return {"unread_notification_count": get_unread_count(request.user)}
