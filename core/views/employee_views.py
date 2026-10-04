from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from core.models import Employee, Department, Attendance
from core.forms import EmployeeForm
from core.decorators import hr_staff_required, get_user_role
from core.utils import log_audit, create_notification


@login_required
@hr_staff_required
def employee_list(request):
    query = request.GET.get('search', '')
    department_id = request.GET.get('department', '')
    position_search = request.GET.get('position', '')
    status_filter = request.GET.get('status', '')

    employees = Employee.objects.select_related('department', 'user').all()

    if query:
        employees = employees.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(email_address__icontains=query)
        )
    if department_id:
        employees = employees.filter(department_id=department_id)
    if position_search:
        employees = employees.filter(position__icontains=position_search)
    if status_filter:
        employees = employees.filter(employment_status=status_filter)

    employees = employees.order_by('last_name', 'first_name')

    paginator = Paginator(employees, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    departments = Department.objects.all()

    context = {
        'page_obj': page_obj,
        'employees': page_obj,
        'departments': departments,
        'search_query': query,
        'selected_department': department_id,
        'selected_position': position_search,
        'selected_status': status_filter,
    }
    return render(request, 'employee/list.html', context)


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(
        Employee.objects.select_related('department', 'user'),
        pk=pk
    )
    user_role = get_user_role(request.user)
    if user_role not in ['admin', 'hr_staff', 'manager']:
        if not request.user.is_superuser and employee.user != request.user:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
    recent_attendance = Attendance.objects.filter(employee=employee.full_name)[:10]
    recent_leaves = employee.leave_requests.all()[:10]
    context = {
        'employee': employee,
        'recent_attendance': recent_attendance,
        'recent_leaves': recent_leaves,
    }
    return render(request, 'employee/detail.html', context)


@login_required
@hr_staff_required
def employee_add(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']

            user = User.objects.create_user(
                username=username,
                password=password or 'default123',
                email=email,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
            )
            employee = form.save(commit=False)
            employee.user = user
            employee.save()

            log_audit(request.user, 'CREATE', 'Employee', employee.id,
                      f"Created employee {employee.employee_id}", request)
            create_notification(
                user, "Employee Added",
                f"Your employee record has been created. Welcome!",
                'Employee Added'
            )
            messages.success(request, f"Employee {employee.full_name} added successfully!")
            return redirect('employee_detail', pk=employee.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeForm()

    departments = Department.objects.all()
    return render(request, 'employee/add.html', {'form': form, 'departments': departments})


@login_required
@hr_staff_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']

            user = employee.user
            user.username = username
            user.email = email
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            if password:
                user.set_password(password)
            user.save()

            employee = form.save()

            log_audit(request.user, 'UPDATE', 'Employee', employee.id,
                      f"Updated employee {employee.employee_id}", request)
            messages.success(request, f"Employee {employee.full_name} updated successfully!")
            return redirect('employee_detail', pk=employee.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'employee/edit.html', {'form': form, 'employee': employee})


@login_required
@hr_staff_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        emp_id = employee.employee_id
        user = employee.user
        employee.delete()
        user.delete()
        log_audit(request.user, 'DELETE', 'Employee', pk,
                  f"Deleted employee {emp_id}", request)
        messages.success(request, f"Employee deleted successfully!")
        return redirect('employee_list')

    return render(request, 'employee/confirm_delete.html', {'employee': employee})
