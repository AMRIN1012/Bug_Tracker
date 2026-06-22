import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.contrib import messages

from .models import (
    UserProfile, Bug, BugAttachment, Comment, Notification, 
    ActivityLog, AssignmentHistory,
    ROLE_ADMIN, ROLE_DEVELOPER, ROLE_TESTER,
    STATUS_OPEN, STATUS_ASSIGNED, STATUS_IN_PROGRESS, STATUS_RESOLVED,
    STATUS_TESTING, STATUS_CLOSED, STATUS_REOPENED, STATUS_REJECTED,
    PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_CRITICAL,
    STATUS_CHOICES, PRIORITY_CHOICES, SEVERITY_CHOICES, BUG_TYPE_CHOICES
)
from .forms import RegistrationForm, LoginForm, BugForm, CommentForm, UserProfileForm

# Helpers for logging and notifications
def log_activity(user, action, bug=None, details=None):
    ActivityLog.objects.create(user=user, bug=bug, action=action, details=details)

def create_notification(recipient, sender, message, bug=None):
    if recipient != sender:
        Notification.objects.create(recipient=recipient, sender=sender, message=message, bug=bug)

# Role check decorators
def admin_only(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.role == ROLE_ADMIN:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Only Admin users can access this page.")
    return _wrapped_view

def developer_or_admin(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.role in [ROLE_DEVELOPER, ROLE_ADMIN]:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Access denied.")
    return _wrapped_view

def tester_or_admin(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.role in [ROLE_TESTER, ROLE_ADMIN]:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Access denied.")
    return _wrapped_view


# --- Authentication Views ---

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create User
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            
            # Map full name
            full_name = form.cleaned_data['full_name']
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = name_parts[1]
                
            user.save()
            
            # Update Profile
            profile = user.profile
            profile.role = form.cleaned_data['role']
            if form.cleaned_data['photo']:
                profile.photo = form.cleaned_data['photo']
            profile.save()
            
            log_activity(user, "User Registered", details=f"Registered as role: {profile.role}")
            
            # Automatically log in the user
            login(request, user)
            messages.success(request, f"Welcome {user.username}! Your registration was successful.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()
    return render(request, 'tracker/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    log_activity(user, "User Logged In")
                    messages.success(request, f"Logged in successfully as {user.username}!")
                    return redirect('dashboard')
                else:
                    messages.error(request, "This account has been disabled. Please contact the administrator.")
            else:
                messages.error(request, "Invalid username/email or password.")
    else:
        form = LoginForm()
    return render(request, 'tracker/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        log_activity(request.user, "User Logged Out")
        logout(request)
        messages.info(request, "You have been logged out.")
    return redirect('login')


def password_reset_view(request):
    # Mock Password Reset Flow for UX completeness
    if request.method == 'POST':
        email = request.POST.get('email')
        users = User.objects.filter(email__iexact=email)
        if users.exists():
            messages.success(request, f"A password reset link has been simulated & sent to {email}.")
        else:
            messages.error(request, "No account was found with that email address.")
        return redirect('login')
    return render(request, 'tracker/password_reset.html')


# --- Core Dashboard ---

@login_required
def dashboard_view(request):
    user = request.user
    role = user.profile.role

    # Apply role filtration for developer dashboard scope
    if role == ROLE_DEVELOPER:
        bugs_qs = Bug.objects.filter(assigned_to=user)
    else:
        bugs_qs = Bug.objects.all()

    # Metric counts
    total_bugs = bugs_qs.count()
    open_bugs = bugs_qs.filter(status=STATUS_OPEN).count()
    assigned_bugs = bugs_qs.filter(status=STATUS_ASSIGNED).count()
    in_progress_bugs = bugs_qs.filter(status=STATUS_IN_PROGRESS).count()
    resolved_bugs = bugs_qs.filter(status=STATUS_RESOLVED).count()
    closed_bugs = bugs_qs.filter(status=STATUS_CLOSED).count()
    reopened_bugs = bugs_qs.filter(status=STATUS_REOPENED).count()
    critical_bugs = bugs_qs.filter(priority=PRIORITY_CRITICAL).count()

    # Recent Activity logs
    if role == ROLE_ADMIN:
        recent_activities = ActivityLog.objects.all()[:10]
    else:
        recent_activities = ActivityLog.objects.filter(
            Q(user=user) | Q(bug__assigned_to=user) | Q(bug__created_by=user)
        )[:10]

    # Data for charts (Breakdown of ALL bugs to give admin/team view, or user-specific if Developer)
    priority_counts = bugs_qs.values('priority').annotate(count=Count('id'))
    status_counts = bugs_qs.values('status').annotate(count=Count('id'))

    priority_data = {item['priority']: item['count'] for item in priority_counts}
    status_data = {item['status']: item['count'] for item in status_counts}

    # Monthly statistics for last 6 months
    monthly_reports = []
    current_date = timezone.now()
    for i in range(5, -1, -1):
        target_date = current_date - datetime.timedelta(days=i*30)
        month_name = target_date.strftime('%B %Y')
        month_bugs = bugs_qs.filter(
            created_at__year=target_date.year,
            created_at__month=target_date.month
        ).count()
        monthly_reports.append({'month': month_name, 'count': month_bugs})

    context = {
        'total_bugs': total_bugs,
        'open_bugs': open_bugs,
        'assigned_bugs': assigned_bugs,
        'in_progress_bugs': in_progress_bugs,
        'resolved_bugs': resolved_bugs,
        'closed_bugs': closed_bugs,
        'reopened_bugs': reopened_bugs,
        'critical_bugs': critical_bugs,
        'recent_activities': recent_activities,
        'priority_data': priority_data,
        'status_data': status_data,
        'monthly_reports': monthly_reports,
    }
    return render(request, 'tracker/dashboard.html', context)


# --- Bug CRUD Modules ---

@login_required
def bug_list_view(request):
    user = request.user
    role = user.profile.role

    # Core queryset
    if role == ROLE_DEVELOPER:
        # Developers only view bugs assigned to them
        bugs_qs = Bug.objects.filter(assigned_to=user)
    else:
        bugs_qs = Bug.objects.all()

    # Searching logic (Instant Search compatible)
    search_query = request.GET.get('q', '')
    if search_query:
        bugs_qs = bugs_qs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(project_name__icontains=search_query) |
            Q(assigned_to__username__icontains=search_query) |
            Q(assigned_to__first_name__icontains=search_query)
        )

    # Filtering logic
    status_filter = request.GET.getlist('status')
    priority_filter = request.GET.getlist('priority')
    severity_filter = request.GET.getlist('severity')
    bug_type_filter = request.GET.getlist('bug_type')
    assignee_filter = request.GET.get('assignee')
    date_range = request.GET.get('date_range')

    if status_filter:
        bugs_qs = bugs_qs.filter(status__in=status_filter)
    if priority_filter:
        bugs_qs = bugs_qs.filter(priority__in=priority_filter)
    if severity_filter:
        bugs_qs = bugs_qs.filter(severity__in=severity_filter)
    if bug_type_filter:
        bugs_qs = bugs_qs.filter(bug_type__in=bug_type_filter)
    if assignee_filter:
        bugs_qs = bugs_qs.filter(assigned_to_id=assignee_filter)
        
    if date_range:
        today = timezone.now().date()
        if date_range == 'today':
            bugs_qs = bugs_qs.filter(created_at__date=today)
        elif date_range == 'week':
            bugs_qs = bugs_qs.filter(created_at__date__gte=today - datetime.timedelta(days=7))
        elif date_range == 'month':
            bugs_qs = bugs_qs.filter(created_at__date__gte=today - datetime.timedelta(days=30))

    # All lists for options
    all_developers = User.objects.filter(profile__role=ROLE_DEVELOPER, is_active=True)
    all_statuses = [s[0] for s in STATUS_CHOICES]
    all_priorities = [p[0] for p in PRIORITY_CHOICES]
    all_severities = [s[0] for s in SEVERITY_CHOICES]
    all_types = [t[0] for t in BUG_TYPE_CHOICES]

    context = {
        'bugs': bugs_qs,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'severity_filter': severity_filter,
        'bug_type_filter': bug_type_filter,
        'assignee_filter': assignee_filter,
        'date_range': date_range,
        'all_developers': all_developers,
        'all_statuses': all_statuses,
        'all_priorities': all_priorities,
        'all_severities': all_severities,
        'all_types': all_types,
    }
    return render(request, 'tracker/bug_list.html', context)


@login_required
def bug_detail_view(request, pk):
    bug = get_object_or_404(Bug, pk=pk)
    
    # Permission gating: Dev can only see assigned bugs
    if request.user.profile.role == ROLE_DEVELOPER and bug.assigned_to != request.user:
        raise PermissionDenied("You can only access bugs assigned to you.")

    if request.method == 'POST' and 'comment_submit' in request.POST:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.bug = bug
            comment.user = request.user
            
            # Handle comment replies
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id)
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    pass
                    
            comment.save()
            
            log_activity(request.user, "Added Comment", bug=bug, details=f"Comment: {comment.comment_text[:50]}...")
            
            # Notify owner/assignee
            notify_targets = set()
            if bug.created_by:
                notify_targets.add(bug.created_by)
            if bug.assigned_to:
                notify_targets.add(bug.assigned_to)
                
            for target in notify_targets:
                create_notification(
                    recipient=target,
                    sender=request.user,
                    message=f"{request.user.username} commented on bug '{bug.title}'",
                    bug=bug
                )
            messages.success(request, "Comment posted successfully.")
            return redirect('bug_detail', pk=bug.pk)
    else:
        comment_form = CommentForm()

    # Assignment & Workflows lists for templates
    developers = User.objects.filter(profile__role=ROLE_DEVELOPER, is_active=True)
    all_statuses = [choice[0] for choice in STATUS_CHOICES]

    context = {
        'bug': bug,
        'comment_form': comment_form,
        'comments': bug.comments.filter(parent=None), # get root comments
        'developers': developers,
        'all_statuses': all_statuses,
        'history': bug.assignment_history.all(),
        'activity_logs': bug.activity_logs.all(),
    }
    return render(request, 'tracker/bug_detail.html', context)


@login_required
def bug_create_view(request):
    user = request.user
    role = user.profile.role

    # Only Admin and Tester can file new bugs
    if role not in [ROLE_ADMIN, ROLE_TESTER]:
        raise PermissionDenied("Only Administrators and Testers can log bugs.")

    if request.method == 'POST':
        form = BugForm(request.POST)
        if form.is_valid():
            bug = form.save(commit=False)
            bug.created_by = user
            bug.status = STATUS_OPEN
            bug.save()

            # Handle attachments
            files = request.FILES.getlist('attachments')
            for f in files:
                BugAttachment.objects.create(bug=bug, file=f)

            log_activity(user, "Logged Bug", bug=bug, details=f"Created bug: {bug.title}")

            # Notify all Admin users
            admin_users = User.objects.filter(profile__role=ROLE_ADMIN)
            for admin in admin_users:
                create_notification(
                    recipient=admin,
                    sender=user,
                    message=f"New bug '{bug.title}' logged by {user.username}",
                    bug=bug
                )

            messages.success(request, f"Bug '{bug.title}' created successfully.")
            return redirect('bug_detail', pk=bug.pk)
    else:
        form = BugForm()
    return render(request, 'tracker/bug_form.html', {'form': form, 'action': 'Create'})


@login_required
def bug_edit_view(request, pk):
    bug = get_object_or_404(Bug, pk=pk)
    user = request.user
    role = user.profile.role

    # Admin can edit any, Tester can edit any created by them or open, Dev cannot full edit details.
    if role == ROLE_DEVELOPER:
        raise PermissionDenied("Developers can only change bug workflow status, not details.")
    elif role == ROLE_TESTER and bug.created_by != user:
        raise PermissionDenied("You can only edit bugs you created.")

    if request.method == 'POST':
        form = BugForm(request.POST, instance=bug)
        if form.is_valid():
            bug = form.save()

            # Handle attachments
            files = request.FILES.getlist('attachments')
            for f in files:
                BugAttachment.objects.create(bug=bug, file=f)

            log_activity(user, "Modified Bug Details", bug=bug)
            
            # Notify assignee
            if bug.assigned_to:
                create_notification(
                    recipient=bug.assigned_to,
                    sender=user,
                    message=f"Bug details for '{bug.title}' were updated by {user.username}",
                    bug=bug
                )

            messages.success(request, "Bug details updated.")
            return redirect('bug_detail', pk=bug.pk)
    else:
        form = BugForm(instance=bug)
    return render(request, 'tracker/bug_form.html', {'form': form, 'action': 'Edit', 'bug': bug})


# --- Bug Actions and Workflow Transitions ---

@login_required
def bug_assign_view(request, pk):
    if request.method != 'POST':
        return redirect('bug_detail', pk=pk)

    bug = get_object_or_404(Bug, pk=pk)
    user = request.user
    role = user.profile.role

    # Only admin can assign developer or change assignee
    if role != ROLE_ADMIN:
        return HttpResponseForbidden("Only administrators can assign bugs.")

    developer_id = request.POST.get('developer_id')
    if developer_id:
        developer = get_object_or_404(User, pk=developer_id)
        
        # Guard: Check developer profile role
        if developer.profile.role != ROLE_DEVELOPER:
            messages.error(request, "User selected is not a developer.")
            return redirect('bug_detail', pk=pk)

        old_assignee = bug.assigned_to
        bug.assigned_to = developer
        bug.status = STATUS_ASSIGNED
        bug.save()

        # Log Assignment History
        AssignmentHistory.objects.create(
            bug=bug,
            assigned_by=user,
            assigned_to=developer
        )

        log_activity(user, "Assigned Developer", bug=bug, details=f"Assigned to {developer.username}")
        
        # Notify developer
        create_notification(
            recipient=developer,
            sender=user,
            message=f"You have been assigned to bug: {bug.title}",
            bug=bug
        )
        
        # Notify old developer if changed
        if old_assignee and old_assignee != developer:
            create_notification(
                recipient=old_assignee,
                sender=user,
                message=f"You have been unassigned from bug: {bug.title}",
                bug=bug
            )

        messages.success(request, f"Bug successfully assigned to {developer.username}.")
    else:
        # Unassign bug
        bug.assigned_to = None
        bug.status = STATUS_OPEN
        bug.save()
        log_activity(user, "Unassigned Developer", bug=bug)
        messages.success(request, "Developer unassigned from this bug.")

    return redirect('bug_detail', pk=pk)


@login_required
def bug_status_update_view(request, pk):
    if request.method != 'POST':
        return redirect('bug_detail', pk=pk)

    bug = get_object_or_404(Bug, pk=pk)
    user = request.user
    role = user.profile.role
    new_status = request.POST.get('status')

    # Security check on roles workflow permissions
    if role == ROLE_DEVELOPER:
        if bug.assigned_to != user:
            raise PermissionDenied("You can only progress bugs assigned to you.")
        # Developers can only set: Assigned, In Progress, Resolved
        if new_status not in [STATUS_IN_PROGRESS, STATUS_RESOLVED]:
            messages.error(request, f"Developers cannot change status to {new_status}.")
            return redirect('bug_detail', pk=pk)

    elif role == ROLE_TESTER:
        # Testers can set: Open, In Progress, Resolved, Testing, Closed, Reopened, Rejected
        # Standard: Testing, Closed, Reopened, Rejected.
        if new_status not in [STATUS_CLOSED, STATUS_REOPENED, STATUS_TESTING, STATUS_REJECTED]:
            messages.error(request, f"Testers cannot change status to {new_status}.")
            return redirect('bug_detail', pk=pk)

    elif role != ROLE_ADMIN:
        raise PermissionDenied("Access denied.")

    # All checks passed, let's change status
    old_status = bug.status
    bug.status = new_status
    bug.save()

    log_activity(user, "Status Changed", bug=bug, details=f"Changed status from '{old_status}' to '{new_status}'")

    # Target notifications
    notify_targets = set()
    if bug.created_by:
        notify_targets.add(bug.created_by)
    if bug.assigned_to:
        notify_targets.add(bug.assigned_to)
    # Notify admin
    admin_users = User.objects.filter(profile__role=ROLE_ADMIN)
    for admin in admin_users:
        notify_targets.add(admin)

    for target in notify_targets:
        create_notification(
            recipient=target,
            sender=user,
            message=f"Bug '{bug.title}' status changed to '{new_status}' by {user.username}",
            bug=bug
        )

    messages.success(request, f"Bug status updated to '{new_status}'.")
    return redirect('bug_detail', pk=pk)


# --- Threaded Comment Deletion ---

@login_required
def comment_delete_view(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    
    # Enforce own comment deletion (Admins can delete any comment)
    if comment.user != request.user and request.user.profile.role != ROLE_ADMIN:
        raise PermissionDenied("You can only delete your own comments.")
        
    bug_pk = comment.bug.pk
    comment_text = comment.comment_text[:20]
    comment.delete()
    
    log_activity(request.user, "Deleted Comment", details=f"Removed comment: '{comment_text}...'")
    messages.info(request, "Comment deleted.")
    return redirect('bug_detail', pk=bug_pk)


# --- Activity Log Page ---

@login_required
def activity_logs_view(request):
    user = request.user
    role = user.profile.role
    
    # Enforce access context
    if role == ROLE_ADMIN:
        logs = ActivityLog.objects.all()
    else:
        logs = ActivityLog.objects.filter(
            Q(user=user) | Q(bug__assigned_to=user) | Q(bug__created_by=user)
        )

    # Simple text/search logs
    search = request.GET.get('q')
    if search:
        logs = logs.filter(
            Q(action__icontains=search) |
            Q(details__icontains=search) |
            Q(user__username__icontains=search) |
            Q(bug__title__icontains=search)
        )

    return render(request, 'tracker/activity_logs.html', {'logs': logs, 'search_query': search})


# --- Notifications Handling ---

@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    return render(request, 'tracker/notifications.html', {'notifications': notifications})


@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications')


@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'ok'})


# --- User Management Module (Admin Only) ---

@admin_only
def user_list_view(request):
    users = User.objects.all().select_related('profile')

    search = request.GET.get('q')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    return render(request, 'tracker/user_list.html', {'tracker_users': users, 'search_query': search})


@admin_only
def user_toggle_status_view(request, pk):
    user_to_mod = get_object_or_404(User, pk=pk)
    if user_to_mod == request.user:
        messages.error(request, "You cannot disable your own admin account.")
        return redirect('user_list')
        
    user_to_mod.is_active = not user_to_mod.is_active
    user_to_mod.save()
    
    state = "enabled" if user_to_mod.is_active else "disabled"
    log_activity(request.user, "Toggled User Account Status", details=f"User {user_to_mod.username} set to {state}")
    
    messages.success(request, f"User {user_to_mod.username} has been {state}.")
    return redirect('user_list')


@admin_only
def user_delete_view(request, pk):
    user_to_del = get_object_or_404(User, pk=pk)
    if user_to_del == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('user_list')

    username = user_to_del.username
    user_to_del.delete()
    
    log_activity(request.user, "Deleted User Account", details=f"User account: {username}")
    messages.info(request, f"User {username} account deleted.")
    return redirect('user_list')


@admin_only
def user_edit_role_view(request, pk):
    user_to_edit = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in [ROLE_ADMIN, ROLE_DEVELOPER, ROLE_TESTER]:
            profile = user_to_edit.profile
            old_role = profile.role
            profile.role = new_role
            profile.save()
            log_activity(request.user, "Modified User Role", details=f"Changed {user_to_edit.username} role from {old_role} to {new_role}")
            messages.success(request, f"Role for {user_to_edit.username} updated to {new_role}.")
        else:
            messages.error(request, "Invalid role choice.")
    return redirect('user_list')


# --- User Profile Module ---

@login_required
def profile_view(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile, user=user)
        if form.is_valid():
            form.save()
            log_activity(user, "Updated User Profile details")
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile, user=user)

    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'tracker/profile.html', context)


# --- Analytics / Reports Module ---

@login_required
def analytics_view(request):
    user = request.user
    role = user.profile.role

    # Filtering parameters
    project_filter = request.GET.get('project')
    
    bugs_qs = Bug.objects.all()
    if project_filter:
        bugs_qs = bugs_qs.filter(project_name=project_filter)

    # Unique projects list
    projects = Bug.objects.values_list('project_name', flat=True).distinct()

    # Priorities breakdown
    priority_stats = bugs_qs.values('priority').annotate(count=Count('id'))
    # Statuses breakdown
    status_stats = bugs_qs.values('status').annotate(count=Count('id'))
    
    # Bug trends weekly (last 4 weeks)
    weekly_trends = []
    today = timezone.now().date()
    for w in range(3, -1, -1):
        start = today - datetime.timedelta(days=(w+1)*7)
        end = today - datetime.timedelta(days=w*7)
        label = f"{start.strftime('%d %b')} - {end.strftime('%d %b')}"
        count = bugs_qs.filter(created_at__date__gte=start, created_at__date__lte=end).count()
        weekly_trends.append({'label': label, 'count': count})

    # Developer Performance (Assigned vs Resolved count)
    developers = User.objects.filter(profile__role=ROLE_DEVELOPER)
    dev_performance = []
    for dev in developers:
        assigned = bugs_qs.filter(assigned_to=dev).count()
        resolved = bugs_qs.filter(assigned_to=dev, status=STATUS_RESOLVED).count()
        closed = bugs_qs.filter(assigned_to=dev, status=STATUS_CLOSED).count()
        dev_performance.append({
            'username': dev.username,
            'assigned': assigned,
            'resolved_or_closed': resolved + closed
        })

    context = {
        'projects': projects,
        'selected_project': project_filter,
        'priority_stats': {item['priority']: item['count'] for item in priority_stats},
        'status_stats': {item['status']: item['count'] for item in status_stats},
        'weekly_trends': weekly_trends,
        'dev_performance': dev_performance,
    }
    return render(request, 'tracker/analytics.html', context)
