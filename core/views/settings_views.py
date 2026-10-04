from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages


@login_required
def settings_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was updated successfully!')
            return redirect('settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)

    try:
        employee = request.user.employee
        role_display = employee.get_role_display()
    except:
        employee = None
        role_display = 'HR Administrator' if request.user.is_superuser else 'Employee'

    context = {
        'form': form,
        'employee': employee,
        'role_display': role_display,
    }
    return render(request, 'settings.html', context)
