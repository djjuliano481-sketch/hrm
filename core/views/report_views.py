from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q
from django.http import HttpResponse
from django.utils import timezone
from datetime import date, timedelta
from core.models import Employee, Attendance, LeaveRequest, LeaveType, Department
from core.decorators import hr_staff_required
from core.forms import DateRangeForm
import csv


@login_required
@hr_staff_required
def reports_index(request):
    return render(request, 'reports/index.html')


@login_required
@hr_staff_required
def report_employees(request):
    employees = Employee.objects.select_related('department').all()

    department_id = request.GET.get('department', '')
    status_filter = request.GET.get('status', '')

    if department_id:
        employees = employees.filter(department_id=department_id)
    if status_filter:
        employees = employees.filter(employment_status=status_filter)

    employees = employees.order_by('last_name', 'first_name')
    departments = Department.objects.all()
    total = employees.count()

    export_csv = request.GET.get('export') == 'csv'
    if export_csv:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="employee_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Employee ID', 'Full Name', 'Department', 'Position', 'Employment Type',
                        'Employment Status', 'Date Hired', 'Email', 'Contact Number'])
        for emp in employees:
            writer.writerow([
                emp.employee_id, emp.full_name, emp.department.name if emp.department else 'N/A',
                emp.position or 'N/A', emp.employment_type,
                emp.employment_status, emp.date_hired, emp.email_address, emp.contact_number
            ])
        return response

    context = {
        'employees': employees,
        'departments': departments,
        'total': total,
        'selected_department': department_id,
        'selected_status': status_filter,
    }
    return render(request, 'reports/employees.html', context)


@login_required
@hr_staff_required
def report_attendance(request):
    form = DateRangeForm(request.GET or None)
    records = []

    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']

        records = Attendance.objects.filter(
            date__gte=start_date, date__lte=end_date
        )

        records = records.order_by('date')

        export_csv = request.GET.get('export') == 'csv'
        if export_csv:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'
            writer = csv.writer(response)
            writer.writerow(['Employee Name', 'Date', 'Time In', 'Time Out',
                           'Status', 'Late Minutes', 'Overtime Hours', 'Working Hours'])
            for r in records:
                writer.writerow([
                    r.employee or 'N/A', r.date,
                    r.time_in.strftime('%H:%M') if r.time_in else 'N/A',
                    r.time_out.strftime('%H:%M') if r.time_out else 'N/A',
                    r.status, r.late_minutes, r.overtime_hours, r.total_working_hours
                ])
            return response

    context = {
        'form': form,
        'records': records,
        'report_type': 'attendance',
    }
    return render(request, 'reports/attendance.html', context)


@login_required
@hr_staff_required
def report_leaves(request):
    form = DateRangeForm(request.GET or None)
    records = []

    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        department = form.cleaned_data.get('department')

        records = LeaveRequest.objects.select_related(
            'employee', 'leave_type', 'employee__department'
        ).filter(created_at__gte=start_date, created_at__lte=end_date)

        if department:
            records = records.filter(employee__department=department)

        records = records.order_by('-created_at')

        export_csv = request.GET.get('export') == 'csv'
        if export_csv:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="leave_report.csv"'
            writer = csv.writer(response)
            writer.writerow(['Employee ID', 'Employee Name', 'Leave Type', 'Start Date',
                           'End Date', 'Days', 'Status', 'Created At'])
            for r in records:
                writer.writerow([
                    r.employee.employee_id, r.employee.full_name, r.leave_type.name,
                    r.start_date, r.end_date, r.number_of_days, r.status, r.created_at
                ])
            return response

    context = {
        'form': form,
        'records': records,
        'report_type': 'leaves',
    }
    return render(request, 'reports/leaves.html', context)
