from .models import AuditLog, Notification
from django.contrib.auth.models import User
import json


def log_audit(user, action, model_name, object_id=None, details=None, request=None):
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        details=details,
        ip_address=ip_address,
    )


def create_notification(recipient, title, message, notification_type='System', link=None):
    if isinstance(recipient, User):
        users = [recipient]
    else:
        users = User.objects.filter(is_superuser=True)

    for user in users:
        Notification.objects.create(
            recipient=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
        )


def notify_managers(title, message, notification_type='System', link=None):
    managers = User.objects.filter(
        groups__name='Manager'
    ).distinct()
    for manager in managers:
        Notification.objects.create(
            recipient=manager,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
        )


def notify_hr_admins(title, message, notification_type='System', link=None):
    hr_admins = User.objects.filter(is_superuser=True)
    for admin in hr_admins:
        Notification.objects.create(
            recipient=admin,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
        )


def calculate_working_hours(time_in, time_out, break_in=None, break_out=None):
    if not time_in or not time_out:
        return 0

    total_seconds = (time_out - time_in).total_seconds()

    if break_in and break_out:
        break_seconds = (break_out - break_in).total_seconds()
        total_seconds -= break_seconds

    hours = total_seconds / 3600
    return round(hours, 2)


def calculate_late_minutes(time_in, scheduled_start=None):
    if not time_in:
        return 0

    if scheduled_start:
        late_seconds = (time_in - scheduled_start).total_seconds()
        if late_seconds > 0:
            return int(late_seconds / 60)

    return 0
