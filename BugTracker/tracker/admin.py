from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, Bug, BugAttachment, Comment, Notification, ActivityLog, AssignmentHistory

# Inline profile for default User Admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'UserProfile'

# Re-register UserAdmin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_active', 'is_staff')
    list_filter = ('profile__role', 'is_active', 'is_staff')

    def get_role(self, obj):
        return obj.profile.role
    get_role.short_description = 'Role'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Bug Attachment Inline
class BugAttachmentInline(admin.TabularInline):
    model = BugAttachment
    extra = 1

# Custom Bug Admin
@admin.register(Bug)
class BugAdmin(admin.ModelAdmin):
    list_display = ('title', 'project_name', 'bug_type', 'priority', 'severity', 'status', 'assigned_to', 'created_by', 'created_at')
    list_filter = ('status', 'priority', 'severity', 'bug_type', 'project_name')
    search_fields = ('title', 'description', 'project_name', 'module_name')
    inlines = [BugAttachmentInline]
    date_hierarchy = 'created_at'

# Other Models
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'bug', 'comment_text', 'parent', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('comment_text', 'user__username', 'bug__title')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'bug', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('message', 'recipient__username', 'sender__username')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'bug', 'action', 'details', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('action', 'details', 'user__username', 'bug__title')

@admin.register(AssignmentHistory)
class AssignmentHistoryAdmin(admin.ModelAdmin):
    list_display = ('bug', 'assigned_by', 'assigned_to', 'assigned_date')
    list_filter = ('assigned_date',)
    search_fields = ('bug__title', 'assigned_by__username', 'assigned_to__username')


# Developer Issues Module
from .models import DeveloperIssue, DeveloperIssueAttachment, DeveloperIssueComment, DeveloperIssueActivity

class DeveloperIssueAttachmentInline(admin.TabularInline):
    model = DeveloperIssueAttachment
    extra = 0

class DeveloperIssueCommentInline(admin.TabularInline):
    model = DeveloperIssueComment
    extra = 0

class DeveloperIssueActivityInline(admin.TabularInline):
    model = DeveloperIssueActivity
    extra = 0

@admin.register(DeveloperIssue)
class DeveloperIssueAdmin(admin.ModelAdmin):
    list_display = ('issue_id', 'developer', 'project_name', 'current_task', 'priority', 'status', 'tester_status', 'tester', 'created_at', 'updated_at')
    list_filter = ('status', 'tester_status', 'priority', 'project_name')
    search_fields = ('issue_id', 'project_name', 'error_encountered', 'current_task', 'developer__username')
    inlines = [DeveloperIssueCommentInline, DeveloperIssueActivityInline, DeveloperIssueAttachmentInline]
    date_hierarchy = 'created_at'

@admin.register(DeveloperIssueComment)
class DeveloperIssueCommentAdmin(admin.ModelAdmin):
    list_display = ('developer_issue', 'user', 'comment_text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('comment_text', 'user__username')

@admin.register(DeveloperIssueActivity)
class DeveloperIssueActivityAdmin(admin.ModelAdmin):
    list_display = ('developer_issue', 'user', 'action', 'details', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('action', 'details', 'user__username')

