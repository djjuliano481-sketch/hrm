from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.forms import LoginForm
from core.utils import log_audit
from core.decorators import get_user_role


def _get_role_redirect(user):
    role = get_user_role(user)
    if role == 'admin':
        return 'dashboard'
    elif role == 'hr_staff':
        return 'dashboard'
    elif role == 'manager':
        return 'dashboard'
    else:
        return 'dashboard'


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                log_audit(user, 'LOGIN', 'User', user.id, f"User {username} logged in", request)
                messages.success(request, f"Welcome back, {user.username}!")
                next_url = request.GET.get('next')
                if not next_url:
                    next_url = _get_role_redirect(user)
                return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})


@login_required
def logout_view(request):
    log_audit(request.user, 'LOGOUT', 'User', request.user.id,
              f"User {request.user.username} logged out", request)
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')
