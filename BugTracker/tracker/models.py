from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Roles choices
ROLE_ADMIN = 'Admin'
ROLE_DEVELOPER = 'Developer'
ROLE_TESTER = 'Tester'

ROLE_CHOICES = [
    (ROLE_ADMIN, 'Admin'),
    (ROLE_DEVELOPER, 'Developer'),
    (ROLE_TESTER, 'Tester'),
]

# Bug Types choices
BUG_TYPE_UI = 'UI Bug'
BUG_TYPE_FUNCTIONAL = 'Functional Bug'
BUG_TYPE_PERFORMANCE = 'Performance Bug'
BUG_TYPE_SECURITY = 'Security Bug'
BUG_TYPE_DATABASE = 'Database Bug'
BUG_TYPE_API = 'API Bug'

BUG_TYPE_CHOICES = [
    (BUG_TYPE_UI, 'UI Bug'),
    (BUG_TYPE_FUNCTIONAL, 'Functional Bug'),
    (BUG_TYPE_PERFORMANCE, 'Performance Bug'),
    (BUG_TYPE_SECURITY, 'Security Bug'),
    (BUG_TYPE_DATABASE, 'Database Bug'),
    (BUG_TYPE_API, 'API Bug'),
]

# Priority choices
PRIORITY_LOW = 'Low'
PRIORITY_MEDIUM = 'Medium'
PRIORITY_HIGH = 'High'
PRIORITY_CRITICAL = 'Critical'

PRIORITY_CHOICES = [
    (PRIORITY_LOW, 'Low'),
    (PRIORITY_MEDIUM, 'Medium'),
    (PRIORITY_HIGH, 'High'),
    (PRIORITY_CRITICAL, 'Critical'),
]

# Severity choices
SEVERITY_MINOR = 'Minor'
SEVERITY_MAJOR = 'Major'
SEVERITY_CRITICAL = 'Critical'
SEVERITY_BLOCKER = 'Blocker'

SEVERITY_CHOICES = [
    (SEVERITY_MINOR, 'Minor'),
    (SEVERITY_MAJOR, 'Major'),
    (SEVERITY_CRITICAL, 'Critical'),
    (SEVERITY_BLOCKER, 'Blocker'),
]

# Status choices
STATUS_OPEN = 'Open'
STATUS_ASSIGNED = 'Assigned'
STATUS_IN_PROGRESS = 'In Progress'
STATUS_RESOLVED = 'Resolved'
STATUS_TESTING = 'Testing'
STATUS_CLOSED = 'Closed'
STATUS_REOPENED = 'Reopened'
STATUS_REJECTED = 'Rejected'

STATUS_CHOICES = [
    (STATUS_OPEN, 'Open'),
    (STATUS_ASSIGNED, 'Assigned'),
    (STATUS_IN_PROGRESS, 'In Progress'),
    (STATUS_RESOLVED, 'Resolved'),
    (STATUS_TESTING, 'Testing'),
    (STATUS_CLOSED, 'Closed'),
    (STATUS_REOPENED, 'Reopened'),
    (STATUS_REJECTED, 'Rejected'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_DEVELOPER)
    photo = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    joined_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    @property
    def assigned_bugs_count(self):
        return self.user.assigned_bugs.count()

    @property
    def resolved_bugs_count(self):
        return self.user.assigned_bugs.filter(status=STATUS_RESOLVED).count()

    @property
    def closed_bugs_count(self):
        return self.user.assigned_bugs.filter(status=STATUS_CLOSED).count()


# Signals to automatically create/update UserProfile when User is created/updated
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)


class Bug(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    project_name = models.CharField(max_length=100)
    module_name = models.CharField(max_length=100)
    bug_type = models.CharField(max_length=50, choices=BUG_TYPE_CHOICES, default=BUG_TYPE_FUNCTIONAL)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_MAJOR)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_bugs')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_bugs')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class BugAttachment(models.Model):
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='bug_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.bug.title}"

    @property
    def filename(self):
        return self.file.name.split('/')[-1]

    @property
    def is_image(self):
        name = self.file.name.lower()
        return name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))


class Comment(models.Model):
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    comment_text = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.bug.title}"

    class Meta:
        ordering = ['created_at']


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message[:30]}"

    class Meta:
        ordering = ['-created_at']


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_logs')
    action = models.CharField(max_length=100) # e.g. Created Bug, Assigned Developer, Changed Status, Comment Added
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"

    class Meta:
        ordering = ['-created_at']


class AssignmentHistory(models.Model):
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE, related_name='assignment_history')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_by_history')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_to_history')
    assigned_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bug {self.bug.id} assigned to {self.assigned_to.username} by {self.assigned_by.username}"

    class Meta:
        ordering = ['-assigned_date']


class DeveloperIssue(models.Model):
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_COMPLETED = 'Completed'
    STATUS_BLOCKED = 'Blocked'
    DEV_STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_BLOCKED, 'Blocked'),
    ]

    TESTER_STATUS_PENDING = 'Pending'
    TESTER_STATUS_TESTING = 'Testing'
    TESTER_STATUS_FIXED = 'Fixed'
    TESTER_STATUS_REJECTED = 'Rejected'
    TESTER_STATUS_MORE_INFO = 'Need More Info'
    TESTER_STATUS_COMPLETED = 'Completed'
    TESTER_STATUS_CHOICES = [
        (TESTER_STATUS_PENDING, 'Pending'),
        (TESTER_STATUS_TESTING, 'Testing'),
        (TESTER_STATUS_FIXED, 'Fixed'),
        (TESTER_STATUS_REJECTED, 'Rejected'),
        (TESTER_STATUS_MORE_INFO, 'Need More Info'),
        (TESTER_STATUS_COMPLETED, 'Completed'),
    ]

    issue_id = models.CharField(max_length=20, unique=True, blank=True)
    developer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='developer_issues')
    project_name = models.CharField(max_length=100)
    current_task = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=DEV_STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    error_encountered = models.CharField(max_length=255)
    error_description = models.TextField()
    files_affected = models.TextField()
    expected_solution = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    tester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_developer_issues')
    tester_status = models.CharField(max_length=20, choices=TESTER_STATUS_CHOICES, default=TESTER_STATUS_PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.issue_id:
            count = DeveloperIssue.objects.count() + 1
            self.issue_id = f"DEV-{1000 + count}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.issue_id} - {self.error_encountered}"

    class Meta:
        ordering = ['-created_at']


class DeveloperIssueAttachment(models.Model):
    developer_issue = models.ForeignKey(DeveloperIssue, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='developer_issue_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.developer_issue.issue_id}"

    @property
    def filename(self):
        return self.file.name.split('/')[-1]

    @property
    def is_image(self):
        name = self.file.name.lower()
        return name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))


class DeveloperIssueComment(models.Model):
    developer_issue = models.ForeignKey(DeveloperIssue, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.developer_issue.issue_id}"

    class Meta:
        ordering = ['created_at']


class DeveloperIssueActivity(models.Model):
    developer_issue = models.ForeignKey(DeveloperIssue, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} on {self.developer_issue.issue_id}"

    class Meta:
        ordering = ['-created_at']
