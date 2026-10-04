from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, timedelta
from core.models import Attendance
from core.forms import AttendanceForm, DateRangeForm
from core.decorators import hr_staff_required, get_user_role


@login_required
def attendance_list(request):
    today = timezone.now().date()
    user_role = get_user_role(request.user)
    
    if user_role in ['admin', 'hr_staff', 'manager'] or request.user.is_superuser:
        employee_search = request.GET.get('employee', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        records = Attendance.objects.all()

        if employee_search:
            records = records.filter(employee__icontains=employee_search)
        if date_from:
            records = records.filter(date__gte=date_from)
        if date_to:
            records = records.filter(date__lte=date_to)
    else:
        try:
            employee = request.user.employee
            records = Attendance.objects.filter(employee=employee.full_name)
        except:
            records = Attendance.objects.none()

    records = records.order_by('-date')

    paginator = Paginator(records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    departments = None

    context = {
        'page_obj': page_obj,
        'records': page_obj,
        'departments': departments,
        'today': today,
    }
    return render(request, 'attendance/list.html', context)


@login_required
@hr_staff_required
def attendance_add(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save()
            messages.success(request, "Attendance record added successfully!")
            return redirect('attendance_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AttendanceForm()

    return render(request, 'attendance/add.html', {'form': form})


@login_required
@hr_staff_required
def attendance_edit(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            messages.success(request, "Attendance record updated successfully!")
            return redirect('attendance_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AttendanceForm(instance=attendance)

    return render(request, 'attendance/edit.html', {'form': form, 'attendance': attendance})


@login_required
def attendance_report(request):
    form = DateRangeForm(request.GET or None)
    records = []
    summary = None

    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']

        records = Attendance.objects.filter(
            date__gte=start_date, date__lte=end_date
        )

        records = records.order_by('date')

        total_present = records.filter(status='Present').count()
        total_late = records.filter(status='Late').count()
        total_absent = records.filter(status='Absent').count()
        total_overtime = records.filter(overtime_hours__gt=0).count()
        avg_hours = records.aggregate(Avg('total_working_hours'))['total_working_hours__avg'] or 0
        total_overtime_hours = records.aggregate(Sum('overtime_hours'))['overtime_hours__sum'] or 0

        summary = {
            'total_records': records.count(),
            'total_present': total_present,
            'total_late': total_late,
            'total_absent': total_absent,
            'total_overtime': total_overtime,
            'avg_hours': round(avg_hours, 2),
            'total_overtime_hours': round(total_overtime_hours, 2),
        }

    context = {
        'form': form,
        'records': records,
        'summary': summary,
    }
    return render(request, 'attendance/report.html', context)
