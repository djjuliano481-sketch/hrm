from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from core.models import Employee, LeaveRequest
from core.decorators import manager_required
from core.utils import log_audit, create_notification


@login_required
@manager_required
def manager_team_view(request):
    try:
        manager = request.user.employee
    except:
        messages.error(request, "Employee profile not found.")
        return redirect('dashboard')

    today = timezone.now().date()

    team_members = Employee.objects.filter(
        immediate_supervisor__icontains=manager.full_name
    )

    if not team_members:
        team_members = Employee.objects.filter(department=manager.department) if manager.department else Employee.objects.none()

    team_count = team_members.count()

    team_pending_leaves = LeaveRequest.objects.filter(
        employee__in=team_members,
        status='Pending'
    ).select_related('employee', 'leave_type').order_by('-created_at')

    pending_count = team_pending_leaves.count()

    on_leave_today = LeaveRequest.objects.filter(
        employee__in=team_members,
        status='Approved',
        start_date__lte=today,
        end_date__gte=today
    ).count()

    team_approved_leaves = LeaveRequest.objects.filter(
        employee__in=team_members,
        status='Approved',
        created_at__month=today.month,
        created_at__year=today.year
    ).count()

    context = {
        'manager': manager,
        'team_members': team_members,
        'team_count': team_count,
        'team_pending_leaves': team_pending_leaves,
        'on_leave_today': on_leave_today,
        'team_approved_leaves': team_approved_leaves,
        'pending_count': pending_count,
    }

    return render(request, 'manager/dashboard.html', context)
