from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
import json
from datetime import timedelta, date
from core.models import Employee, Attendance, LeaveRequest, LeaveType, Department
from core.decorators import get_user_role


@login_required
def dashboard(request):
    user_role = get_user_role(request.user)
    today = timezone.now().date()
    first_of_month = today.replace(day=1)

    if user_role == 'employee':
        return _employee_dashboard(request)
    elif user_role == 'hr_staff':
        return _hr_staff_dashboard(request)
    else:
        return _admin_dashboard(request)


def _admin_dashboard(request):
    today = timezone.now().date()
    first_of_month = today.replace(day=1)

    total_employees = Employee.objects.filter(employment_status='Active').count()
    new_employees = Employee.objects.filter(date_hired__gte=first_of_month).count()
    departments_count = Department.objects.count()
    total_users = Employee.objects.count()

    attendances_today = Attendance.objects.filter(date=today)
    present_today = attendances_today.filter(status='Present').count()
    late_today = attendances_today.filter(status='Late').count()
    absent_today = total_employees - Attendance.objects.filter(date=today).count()
    if absent_today < 0:
        absent_today = 0

    on_leave_today = LeaveRequest.objects.filter(
        status='Approved',
        start_date__lte=today,
        end_date__gte=today
    ).count()

    pending_leaves = LeaveRequest.objects.filter(status='Pending').count()
    approved_leaves = LeaveRequest.objects.filter(
        status='Approved',
        created_at__month=today.month,
        created_at__year=today.year
    ).count()
    rejected_leaves = LeaveRequest.objects.filter(
        status='Rejected',
        created_at__month=today.month,
        created_at__year=today.year
    ).count()

    employees_by_dept = Department.objects.annotate(
        emp_count=Count('employees', filter=Q(employees__employment_status='Active'))
    ).values('name', 'emp_count')

    dept_labels = [d['name'] for d in employees_by_dept]
    dept_data = [d['emp_count'] for d in employees_by_dept]

    last_6_months = []
    monthly_attendance = []
    for i in range(5, -1, -1):
        month = today.month - i
        year = today.year
        while month < 1:
            month += 12
            year -= 1
        last_6_months.append(f"{year}-{month:02d}")

    for ym in last_6_months:
        year, month = map(int, ym.split('-'))
        count = Attendance.objects.filter(
            date__year=year,
            date__month=month,
            status='Present'
        ).count()
        monthly_attendance.append(count)

    employee_growth = []
    for i in range(5, -1, -1):
        month = today.month - i
        year = today.year
        while month < 1:
            month += 12
            year -= 1
        count = Employee.objects.filter(
            date_hired__year=year,
            date_hired__month=month
        ).count()
        employee_growth.append(count)

    leave_trend = []
    for ym in last_6_months:
        year, month = map(int, ym.split('-'))
        count = LeaveRequest.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).count()
        leave_trend.append(count)

    recent_attendance = Attendance.objects.filter(date=today)[:10]
    recent_leaves = LeaveRequest.objects.filter(status='Pending')[:5]

    month_names = []
    for ym in last_6_months:
        year, month = map(int, ym.split('-'))
        from datetime import datetime
        month_names.append(datetime(year, month, 1).strftime('%b %Y'))

    context = {
        'dashboard_role': 'admin',
        'total_employees': total_employees,
        'new_employees': new_employees,
        'departments_count': departments_count,
        'total_users': total_users,
        'present_today': present_today,
        'late_today': late_today,
        'absent_today': absent_today if absent_today >= 0 else 0,
        'on_leave_today': on_leave_today,
        'pending_leaves': pending_leaves,
        'approved_leaves': approved_leaves,
        'rejected_leaves': rejected_leaves,
        'dept_labels': json.dumps(list(dept_labels)),
        'dept_data': json.dumps(list(dept_data)),
        'attendance_labels': json.dumps(month_names),
        'attendance_data': json.dumps(monthly_attendance),
        'employee_growth_labels': json.dumps(month_names),
        'employee_growth_data': json.dumps(employee_growth),
        'leave_trend_labels': json.dumps(month_names),
        'leave_trend_data': json.dumps(leave_trend),
        'recent_attendance': recent_attendance,
        'recent_leaves': recent_leaves,
    }

    return render(request, 'dashboard.html', context)


def _hr_staff_dashboard(request):
    today = timezone.now().date()
    first_of_month = today.replace(day=1)

    total_employees = Employee.objects.filter(employment_status='Active').count()
    new_employees = Employee.objects.filter(date_hired__gte=first_of_month).count()

    attendances_today = Attendance.objects.filter(date=today)
    present_today = attendances_today.filter(status='Present').count()
    late_today = attendances_today.filter(status='Late').count()
    absent_today = total_employees - Attendance.objects.filter(date=today).count()
    if absent_today < 0:
        absent_today = 0

    on_leave_today = LeaveRequest.objects.filter(
        status='Approved',
        start_date__lte=today,
        end_date__gte=today
    ).count()

    context = {
        'dashboard_role': 'hr_staff',
        'total_employees': total_employees,
        'new_employees': new_employees,
        'present_today': present_today,
        'late_today': late_today,
        'absent_today': absent_today if absent_today >= 0 else 0,
        'on_leave_today': on_leave_today,
    }

    return render(request, 'dashboard.html', context)


def _employee_dashboard(request):
    today = timezone.now().date()
    try:
        employee = request.user.employee
    except:
        context = {
            'dashboard_role': 'employee',
            'employee': None,
        }
        return render(request, 'dashboard.html', context)

    recent_attendance = Attendance.objects.filter(employee=employee.full_name)[:10]
    pending_leaves = LeaveRequest.objects.filter(employee=employee, status='Pending').count()
    approved_leaves = LeaveRequest.objects.filter(employee=employee, status='Approved').count()
    rejected_leaves = LeaveRequest.objects.filter(employee=employee, status='Rejected').count()
    recent_leaves = LeaveRequest.objects.filter(employee=employee)[:5]

    context = {
        'dashboard_role': 'employee',
        'employee': employee,
        'recent_attendance': recent_attendance,
        'recent_leaves': recent_leaves,
        'pending_leaves': pending_leaves,
        'approved_leaves': approved_leaves,
        'rejected_leaves': rejected_leaves,
    }

    return render(request, 'dashboard.html', context)
