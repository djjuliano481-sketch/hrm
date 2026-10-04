from .models import Notification
from .decorators import get_user_role, ROLE_DISPLAY


def notification_count(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        recent_notifications = Notification.objects.filter(
            recipient=request.user
        )[:5]
        user_role = get_user_role(request.user)
        return {
            'unread_notifications': unread_count,
            'recent_notifications': recent_notifications,
            'user_role': user_role,
            'user_role_display': ROLE_DISPLAY.get(user_role, 'Employee'),
        }
    return {
        'unread_notifications': 0,
        'recent_notifications': [],
        'user_role': None,
        'user_role_display': None,
    }
