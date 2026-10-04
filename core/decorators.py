from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def get_user_role(user):
    if user.is_superuser:
        return 'admin'
    try:
        employee = user.employee
        role = getattr(employee, 'role', 'employee')
        return role
    except:
        return 'employee'


ROLE_MAP = {
    'admin': ['admin'],
    'hr_staff': ['admin', 'hr_staff', 'manager'],
    'manager': ['admin', 'hr_staff', 'manager'],
    'employee': ['admin', 'hr_staff', 'manager', 'employee'],
}

ROLE_DISPLAY = {
    'admin': 'Admin',
    'hr_staff': 'HR Staff',
    'manager': 'Manager',
    'employee': 'Employee',
}


def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            user_role = get_user_role(request.user)

            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)

            for allowed in allowed_roles:
                if user_role in ROLE_MAP.get(allowed, []):
                    return view_func(request, *args, **kwargs)

            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
        return _wrapped_view
    return decorator


def hr_admin_required(view_func):
    return role_required(['admin'])(view_func)


def admin_required(view_func):
    return role_required(['admin'])(view_func)


def hr_staff_required(view_func):
    return role_required(['admin', 'hr_staff', 'manager'])(view_func)


def manager_required(view_func):
    return role_required(['admin', 'hr_staff', 'manager'])(view_func)
