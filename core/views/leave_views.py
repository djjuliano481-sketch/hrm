from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from core.models import LeaveRequest, LeaveType, Employee, Notification
from core.forms import LeaveRequestForm
from core.decorators import admin_required, hr_staff_required, get_user_role
from core.utils import log_audit, create_notification, notify_managers, notify_hr_admins


@login_required
def leave_list(request):
    try:
        employee = request.user.employee
    except:
        employee = None

    status_filter = request.GET.get('status', '')
    user_role = get_user_role(request.user)

    if request.user.is_superuser or user_role in ['admin', 'hr_staff', 'manager']:
        leaves = LeaveRequest.objects.select_related(
            'employee', 'leave_type', 'approved_by'
        ).all()
    elif employee:
        leaves = LeaveRequest.objects.filter(employee=employee)
    else:
        leaves = LeaveRequest.objects.none()

    if status_filter:
        leaves = leaves.filter(status=status_filter)

    leaves = leaves.order_by('-created_at')

    paginator = Paginator(leaves, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'leaves': page_obj,
        'status_filter': status_filter,
        'is_admin': user_role in ['admin'] or request.user.is_superuser,
    }
    return render(request, 'leave/list.html', context)


@login_required
def leave_request(request):
    try:
        employee = request.user.employee
    except:
        messages.error(request, "Employee profile not found.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = employee
            leave.save()

            log_audit(request.user, 'CREATE', 'LeaveRequest', leave.id,
                      f"Leave request created: {leave.leave_type.name}", request)

            notify_managers(
                f"New Leave Request from {employee.full_name}",
                f"{employee.full_name} requested {leave.leave_type.name} from {leave.start_date} to {leave.end_date}.",
                'Leave Request',
                '/leave/'
            )

            messages.success(request, "Leave request submitted successfully!")
            return redirect('leave_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LeaveRequestForm()
        form.fields['leave_type'].queryset = LeaveType.objects.filter(is_active=True)

    return render(request, 'leave/request.html', {'form': form})


@login_required
def leave_detail(request, pk):
    leave = get_object_or_404(
        LeaveRequest.objects.select_related('employee', 'leave_type', 'approved_by'),
        pk=pk
    )
    return render(request, 'leave/detail.html', {'leave': leave})


@login_required
def leave_cancel(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)

    if leave.employee.user != request.user and not request.user.is_superuser:
        messages.error(request, "You can only cancel your own leave requests.")
        return redirect('leave_list')

    if leave.status != 'Pending':
        messages.error(request, "Only pending leave requests can be cancelled.")
        return redirect('leave_list')

    if request.method == 'POST':
        leave.status = 'Cancelled'
        leave.save()

        log_audit(request.user, 'UPDATE', 'LeaveRequest', leave.id,
                  f"Leave request cancelled: {leave.leave_type.name}", request)

        notify_hr_admins(
            f"Leave Cancelled by {leave.employee.full_name}",
            f"{leave.employee.full_name} cancelled their {leave.leave_type.name} request.",
            'Leave Request',
            '/leave/'
        )

        messages.success(request, "Leave request cancelled.")
        return redirect('leave_list')

    return render(request, 'leave/confirm_cancel.html', {'leave': leave})


@login_required
@admin_required
def leave_review(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)

    if leave.status != 'Pending':
        messages.error(request, "This leave request has already been processed.")
        return redirect('leave_list')

    if request.method == 'POST':
        action = request.POST.get('action')
        rejection_reason = request.POST.get('rejection_reason', '')

        try:
            employee = request.user.employee
        except Employee.DoesNotExist:
            employee = None

        if action == 'approve':
            leave.status = 'Approved'
            if employee:
                leave.approved_by = employee
            leave.approved_at = timezone.now()
            leave.save()

            log_audit(request.user, 'UPDATE', 'LeaveRequest', leave.id,
                      f"Leave approved: {leave.leave_type.name}", request)

            create_notification(
                leave.employee.user,
                "Leave Approved",
                f"Your {leave.leave_type.name} request ({leave.start_date} to {leave.end_date}) has been approved.",
                'Leave Approved',
                '/leave/'
            )

            messages.success(request, "Leave request approved!")
        elif action == 'reject':
            if not rejection_reason:
                messages.error(request, "Please provide a reason for rejection.")
                return render(request, 'leave/review.html', {'leave': leave})

            leave.status = 'Rejected'
            if employee:
                leave.approved_by = employee
            leave.approved_at = timezone.now()
            leave.rejection_reason = rejection_reason
            leave.save()

            log_audit(request.user, 'UPDATE', 'LeaveRequest', leave.id,
                      f"Leave rejected: {leave.leave_type.name}. Reason: {rejection_reason}", request)

            create_notification(
                leave.employee.user,
                "Leave Rejected",
                f"Your {leave.leave_type.name} request ({leave.start_date} to {leave.end_date}) has been rejected. Reason: {rejection_reason}",
                'Leave Rejected',
                '/leave/'
            )

            messages.success(request, "Leave request rejected.")

        return redirect('leave_list')

    return render(request, 'leave/review.html', {'leave': leave})


@login_required
@require_POST
def leave_decision_api(request, pk):
    user_role = get_user_role(request.user)
    if user_role != 'admin' and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'You do not have permission to approve or reject leave requests.'}, status=403)

    try:
        leave = LeaveRequest.objects.select_related('employee__user', 'leave_type').get(pk=pk)
    except LeaveRequest.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Leave request not found.'}, status=404)

    if leave.status != 'Pending':
        return JsonResponse({'success': False, 'error': 'This leave request has already been processed.'}, status=400)

    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        employee = None

    action = request.POST.get('action')
    rejection_reason = request.POST.get('rejection_reason', '').strip()

    if action == 'approve':
        leave.status = 'Approved'
        if employee:
            leave.approved_by = employee
        leave.approved_at = timezone.now()
        leave.save()

        log_audit(request.user, 'UPDATE', 'LeaveRequest', leave.id,
                  f"Leave approved: {leave.leave_type.name}", request)

        create_notification(
            leave.employee.user,
            "Leave Approved",
            f"Your {leave.leave_type.name} request ({leave.start_date} to {leave.end_date}) has been approved.",
            'Leave Approved',
            '/leave/'
        )

        return JsonResponse({'success': True, 'status': 'Approved'})

    elif action == 'reject':
        if not rejection_reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for rejection.'}, status=400)

        leave.status = 'Rejected'
        if employee:
            leave.approved_by = employee
        leave.approved_at = timezone.now()
        leave.rejection_reason = rejection_reason
        leave.save()

        log_audit(request.user, 'UPDATE', 'LeaveRequest', leave.id,
                  f"Leave rejected: {leave.leave_type.name}. Reason: {rejection_reason}", request)

        create_notification(
            leave.employee.user,
            "Leave Rejected",
            f"Your {leave.leave_type.name} request ({leave.start_date} to {leave.end_date}) has been rejected. Reason: {rejection_reason}",
            'Leave Rejected',
            '/leave/'
        )

        return JsonResponse({'success': True, 'status': 'Rejected'})

    return JsonResponse({'success': False, 'error': 'Invalid action.'}, status=400)
