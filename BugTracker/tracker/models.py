from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Roles choices
ROLE_SUPER_ADMIN = 'Super Admin'
ROLE_ADMIN = 'Admin'
ROLE_PM = 'Project Manager'
ROLE_TEAM_LEAD = 'Team Lead'
ROLE_DEVELOPER = 'Developer'
ROLE_TESTER = 'Tester'
ROLE_CLIENT = 'Client'

ROLE_CHOICES = [
    (ROLE_SUPER_ADMIN, 'Super Admin'),
    (ROLE_ADMIN, 'Admin'),
    (ROLE_PM, 'Project Manager'),
    (ROLE_TEAM_LEAD, 'Team Lead'),
    (ROLE_DEVELOPER, 'Developer'),
    (ROLE_TESTER, 'Tester / QA'),
    (ROLE_CLIENT, 'Client'),
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
STATUS_NEW = 'New'
STATUS_ASSIGNED = 'Assigned'
STATUS_ACKNOWLEDGED = 'Acknowledged'
STATUS_IN_PROGRESS = 'In Progress'
STATUS_CODE_REVIEW = 'Code Review'
STATUS_READY_TESTING = 'Ready for Testing'
STATUS_TESTING = 'Testing'
STATUS_PASSED = 'Passed'
STATUS_CLOSED = 'Closed'
STATUS_REOPENED = 'Reopened'
STATUS_REJECTED = 'Rejected'

STATUS_CHOICES = [
    (STATUS_OPEN, 'Open'),
    (STATUS_NEW, 'New'),
    (STATUS_ASSIGNED, 'Assigned'),
    (STATUS_ACKNOWLEDGED, 'Acknowledged'),
    (STATUS_IN_PROGRESS, 'In Progress'),
    (STATUS_CODE_REVIEW, 'Code Review'),
    (STATUS_READY_TESTING, 'Ready for Testing'),
    (STATUS_TESTING, 'Testing'),
    (STATUS_PASSED, 'Passed'),
    (STATUS_CLOSED, 'Closed'),
    (STATUS_REOPENED, 'Reopened'),
    (STATUS_REJECTED, 'Rejected'),
]


# --- New Project Management Models ---

class Project(models.Model):
    STATUS_ACTIVE = 'Active'
    STATUS_ARCHIVED = 'Archived'
    PROJECT_STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    repository_url = models.URLField(max_length=255, blank=True, null=True)
    technology_stack = models.CharField(max_length=255, blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=PROJECT_STATUS_CHOICES, default=STATUS_ACTIVE)
    members = models.ManyToManyField(User, blank=True, related_name='projects')
    team_leads = models.ManyToManyField(User, blank=True, related_name='led_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Module(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='modules')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    class Meta:
        unique_together = ('project', 'name')
        ordering = ['name']


class Feature(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='features')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.module.name} - {self.name}"

    class Meta:
        unique_together = ('module', 'name')
        ordering = ['name']


class Sprint(models.Model):
    STATUS_PLANNING = 'Planning'
    STATUS_ACTIVE = 'Active'
    STATUS_COMPLETED = 'Completed'
    SPRINT_STATUS_CHOICES = [
        (STATUS_PLANNING, 'Planning'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints')
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=SPRINT_STATUS_CHOICES, default=STATUS_PLANNING)

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    class Meta:
        ordering = ['start_date']


class Release(models.Model):
    STATUS_PLANNING = 'Planning'
    STATUS_RELEASED = 'Released'
    RELEASE_STATUS_CHOICES = [
        (STATUS_PLANNING, 'Planning'),
        (STATUS_RELEASED, 'Released'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='releases')
    version_name = models.CharField(max_length=50)
    release_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=RELEASE_STATUS_CHOICES, default=STATUS_PLANNING)

    def __str__(self):
        return f"{self.project.name} - {self.version_name}"

    class Meta:
        unique_together = ('project', 'version_name')
        ordering = ['-release_date']

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
        return self.user.assigned_bugs.filter(status=STATUS_PASSED).count()

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
    project_name = models.CharField(max_length=100, blank=True, null=True)
    module_name = models.CharField(max_length=100, blank=True, null=True)
    
    # New relationships
    bug_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='bugs')
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True, blank=True, related_name='bugs')
    feature = models.ForeignKey(Feature, on_delete=models.SET_NULL, null=True, blank=True, related_name='bugs')
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='bugs')
    release = models.ForeignKey(Release, on_delete=models.SET_NULL, null=True, blank=True, related_name='bugs')
    
    bug_type = models.CharField(max_length=50, choices=BUG_TYPE_CHOICES, default=BUG_TYPE_FUNCTIONAL)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_MAJOR)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    
    expected_result = models.TextField(blank=True, null=True)
    actual_result = models.TextField(blank=True, null=True)
    steps_to_reproduce = models.TextField(blank=True, null=True)
    
    # Environment info
    environment = models.CharField(max_length=50, default='Development')
    browser = models.CharField(max_length=100, blank=True, null=True)
    operating_system = models.CharField(max_length=100, blank=True, null=True)
    device = models.CharField(max_length=100, blank=True, null=True)
    build_version = models.CharField(max_length=50, blank=True, null=True)
    app_version = models.CharField(max_length=50, blank=True, null=True)
    
    # Classification & Time tracking
    category = models.CharField(max_length=50, blank=True, null=True)
    labels = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated labels")
    tags = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated tags")
    
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    
    # Git integration fields
    git_branch = models.CharField(max_length=100, blank=True, null=True)
    commit_hash = models.CharField(max_length=100, blank=True, null=True)
    pull_request_link = models.CharField(max_length=255, blank=True, null=True)
    
    # Assignment
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_bugs')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_bugs')
    tester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_testing_bugs')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.bug_id:
            count = Bug.objects.count() + 1
            self.bug_id = f"BUG-{1000 + count}"
        
        # Populate project_name & module_name for backward compatibility if possible
        if self.project:
            self.project_name = self.project.name
        if self.module:
            self.module_name = self.module.name
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bug_id or 'NEW'} - {self.title}"

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
