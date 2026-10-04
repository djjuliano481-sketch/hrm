from django.urls import path
from django.contrib.auth import views as auth_views
from core.views import auth_views as local_auth
from core.views import dashboard_views
from core.views import employee_views
from core.views import attendance_views
from core.views import leave_views
from core.views import notification_views
from core.views import report_views
from core.views import settings_views
from core.views import manager_views
from core.views import forecast_views
urlpatterns = [
    path('', dashboard_views.dashboard, name='dashboard'),

    path('login/', local_auth.login_view, name='login'),
    path('logout/', local_auth.logout_view, name='logout'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset.html'
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'password-reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),
    path(
        'password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    path('employees/', employee_views.employee_list, name='employee_list'),
    path('employees/add/', employee_views.employee_add, name='employee_add'),
    path('employees/<int:pk>/', employee_views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/edit/', employee_views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', employee_views.employee_delete, name='employee_delete'),

    path('attendance/', attendance_views.attendance_list, name='attendance_list'),
    path('attendance/add/', attendance_views.attendance_add, name='attendance_add'),
    path('attendance/<int:pk>/edit/', attendance_views.attendance_edit, name='attendance_edit'),
    path('attendance/report/', attendance_views.attendance_report, name='attendance_report'),

    path('leave/', leave_views.leave_list, name='leave_list'),
    path('leave/request/', leave_views.leave_request, name='leave_request'),
    path('leave/<int:pk>/', leave_views.leave_detail, name='leave_detail'),
    path('leave/<int:pk>/cancel/', leave_views.leave_cancel, name='leave_cancel'),
    path('leave/<int:pk>/review/', leave_views.leave_review, name='leave_review'),
    path('leave/<int:pk>/decision/', leave_views.leave_decision_api, name='leave_decision_api'),

    path('notifications/', notification_views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', notification_views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', notification_views.notification_mark_all_read, name='notification_mark_all_read'),

    path('reports/', report_views.reports_index, name='reports_index'),
    path('reports/employees/', report_views.report_employees, name='report_employees'),
    path('reports/attendance/', report_views.report_attendance, name='report_attendance'),
    path('reports/leaves/', report_views.report_leaves, name='report_leaves'),

    path('settings/', settings_views.settings_view, name='settings'),

    path('manager/team/', manager_views.manager_team_view, name='manager_team'),

    path('forecast/', forecast_views.forecast_index, name='forecast_index'),

]
