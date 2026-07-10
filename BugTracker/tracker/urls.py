from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    # Redirect root to dashboard/login
    path('', lambda r: redirect('dashboard') if r.user.is_authenticated else redirect('login')),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_view, name='password_reset'),

    # Core Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Bug Management
    path('bugs/', views.bug_list_view, name='bug_list'),
    path('bugs/create/', views.bug_create_view, name='bug_create'),
    path('bugs/<int:pk>/', views.bug_detail_view, name='bug_detail'),
    path('bugs/<int:pk>/edit/', views.bug_edit_view, name='bug_edit'),
    path('bugs/<int:pk>/assign/', views.bug_assign_view, name='bug_assign'),
    path('bugs/<int:pk>/status/', views.bug_status_update_view, name='bug_status_update'),

    # Comments
    path('comments/<int:pk>/delete/', views.comment_delete_view, name='comment_delete'),

    # Activity Logs
    path('activity-logs/', views.activity_logs_view, name='activity_logs'),

    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/<int:pk>/mark-read/', views.mark_notification_read, name='mark_notification_read'),

    # User Management (Admin only)
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:pk>/toggle/', views.user_toggle_status_view, name='user_toggle_status'),
    path('users/<int:pk>/delete/', views.user_delete_view, name='user_delete'),
    path('users/<int:pk>/edit-role/', views.user_edit_role_view, name='user_edit_role'),

    # Profile
    path('profile/', views.profile_view, name='profile'),

    # Analytics / Reports
    path('analytics/', views.analytics_view, name='analytics'),

    # Developer Issues
    path('dev-issues/', views.dev_issue_list_view, name='dev_issue_list'),
    path('dev-issues/create/', views.dev_issue_create_view, name='dev_issue_create'),
    path('dev-issues/<int:pk>/', views.dev_issue_detail_view, name='dev_issue_detail'),
    path('dev-issues/<int:pk>/edit/', views.dev_issue_edit_view, name='dev_issue_edit'),
    path('dev-issues/<int:pk>/tester-status/', views.dev_issue_tester_status_view, name='dev_issue_tester_status'),
    path('dev-issues/<int:pk>/upload/', views.dev_issue_upload_attachment, name='dev_issue_upload_attachment'),

    # Built-in IDE for Testers
    path('ide/', views.ide_view, name='ide'),
    path('ide/api/files/', views.ide_api_files, name='ide_api_files'),
    path('ide/api/file/read/', views.ide_api_read_file, name='ide_api_read_file'),
    path('ide/api/file/write/', views.ide_api_write_file, name='ide_api_write_file'),
    path('ide/api/run/', views.ide_api_run_code, name='ide_api_run_code'),
    path('ide/api/build/', views.ide_api_build, name='ide_api_build'),
    path('ide/api/test/', views.ide_api_test, name='ide_api_test'),
]
