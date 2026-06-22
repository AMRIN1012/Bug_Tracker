from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tracker.models import (
    UserProfile, Bug, Comment, ActivityLog, AssignmentHistory,
    ROLE_ADMIN, ROLE_DEVELOPER, ROLE_TESTER,
    STATUS_OPEN, STATUS_ASSIGNED, STATUS_IN_PROGRESS, STATUS_RESOLVED,
    STATUS_TESTING, STATUS_CLOSED, STATUS_REOPENED, STATUS_REJECTED,
    BUG_TYPE_UI, BUG_TYPE_API, BUG_TYPE_SECURITY, BUG_TYPE_PERFORMANCE, BUG_TYPE_DATABASE,
    PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_CRITICAL,
    SEVERITY_MINOR, SEVERITY_MAJOR, SEVERITY_CRITICAL, SEVERITY_BLOCKER
)

class Command(BaseCommand):
    help = 'Seeds the SQLite database with role-based users and dummy issues for demonstration.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database...")

        # 1. Create Users
        admin_user, created = User.objects.get_or_create(username='admin', email='admin@tracker.com')
        if created:
            admin_user.set_password('admin123')
            admin_user.first_name = "Alan"
            admin_user.last_name = "Turing"
            admin_user.save()
            admin_user.profile.role = ROLE_ADMIN
            admin_user.profile.save()
            self.stdout.write("Created Admin: admin / admin123")

        dev_user, created = User.objects.get_or_create(username='developer', email='dev@tracker.com')
        if created:
            dev_user.set_password('dev123')
            dev_user.first_name = "Grace"
            dev_user.last_name = "Hopper"
            dev_user.save()
            dev_user.profile.role = ROLE_DEVELOPER
            dev_user.profile.save()
            self.stdout.write("Created Developer: developer / dev123")

        tester_user, created = User.objects.get_or_create(username='tester', email='tester@tracker.com')
        if created:
            tester_user.set_password('tester123')
            tester_user.first_name = "Margaret"
            tester_user.last_name = "Hamilton"
            tester_user.save()
            tester_user.profile.role = ROLE_TESTER
            tester_user.profile.save()
            self.stdout.write("Created Tester: tester / tester123")

        # 2. Clear old data to prevent duplication
        Bug.objects.all().delete()
        ActivityLog.objects.all().delete()
        AssignmentHistory.objects.all().delete()

        # 3. Create Bugs
        bug1 = Bug.objects.create(
            title="UI alignment offset on Login Card component",
            description="The card container alignment shifts slightly left on screen widths between 768px and 1024px. The Bootstrap container margin layout classes are missing alignment overrides.",
            project_name="Portal Redesign",
            module_name="Authentication",
            bug_type=BUG_TYPE_UI,
            priority=PRIORITY_LOW,
            severity=SEVERITY_MINOR,
            status=STATUS_CLOSED,
            created_by=tester_user,
            assigned_to=dev_user
        )

        bug2 = Bug.objects.create(
            title="API Timeout fetching analytics report",
            description="The GET request to /api/v1/analytics fetches all database rows sequentially rather than using aggregation, leading to high load and timeout exceptions on sets exceeding 10,000 logs.",
            project_name="Analytics Engine",
            module_name="API Layer",
            bug_type=BUG_TYPE_API,
            priority=PRIORITY_HIGH,
            severity=SEVERITY_CRITICAL,
            status=STATUS_IN_PROGRESS,
            created_by=tester_user,
            assigned_to=dev_user
        )

        bug3 = Bug.objects.create(
            title="SQL Injection Vulnerability in User Profile Search",
            description="The search input in user management module appends parameter strings directly into the raw SQL query select statement. A malicious payload can bypass permissions gating.",
            project_name="Core Security",
            module_name="Search",
            bug_type=BUG_TYPE_DATABASE,
            priority=PRIORITY_CRITICAL,
            severity=SEVERITY_BLOCKER,
            status=STATUS_ASSIGNED,
            created_by=tester_user,
            assigned_to=dev_user
        )

        bug4 = Bug.objects.create(
            title="OAuth token leakage in redirect header response",
            description="When user cancels the registration authentication flow, the redirect callback URL appends client tokens in the query parameters of the error response header.",
            project_name="Core Security",
            module_name="OAuth Provider",
            bug_type=BUG_TYPE_SECURITY,
            priority=PRIORITY_CRITICAL,
            severity=SEVERITY_BLOCKER,
            status=STATUS_OPEN,
            created_by=tester_user,
            assigned_to=None
        )

        bug5 = Bug.objects.create(
            title="Slow chart rendering during initial page load on Mobile Safari",
            description="On iOS Safari devices, Chart.js context creation causes layout reflow loops, rendering animations block CPU execution thread for 3-4 seconds.",
            project_name="Analytics Engine",
            module_name="Charts UI",
            bug_type=BUG_TYPE_PERFORMANCE,
            priority=PRIORITY_MEDIUM,
            severity=SEVERITY_MAJOR,
            status=STATUS_RESOLVED,
            created_by=tester_user,
            assigned_to=dev_user
        )

        # 4. Create Comments
        c1 = Comment.objects.create(
            bug=bug2,
            user=dev_user,
            comment_text="I traced this down to the missing GROUP BY SQL indexes on the activity log datetime columns. Working on a pagination fix."
        )
        Comment.objects.create(
            bug=bug2,
            user=tester_user,
            parent=c1,
            comment_text="Sounds good, please verify that it handles page size offsets correctly as well!"
        )

        # 5. Create Activity Logs & Assignment History
        ActivityLog.objects.create(user=tester_user, bug=bug1, action="Created Bug", details="Logged UI margin misalignment.")
        ActivityLog.objects.create(user=admin_user, bug=bug1, action="Assigned Developer", details="Assigned to developer.")
        AssignmentHistory.objects.create(bug=bug1, assigned_by=admin_user, assigned_to=dev_user)
        ActivityLog.objects.create(user=dev_user, bug=bug1, action="Status Changed", details="Changed status from Assigned to In Progress.")
        ActivityLog.objects.create(user=dev_user, bug=bug1, action="Status Changed", details="Changed status from In Progress to Resolved.")
        ActivityLog.objects.create(user=tester_user, bug=bug1, action="Status Changed", details="Changed status from Resolved to Testing.")
        ActivityLog.objects.create(user=tester_user, bug=bug1, action="Status Changed", details="Changed status from Testing to Closed.")

        ActivityLog.objects.create(user=tester_user, bug=bug2, action="Created Bug", details="Logged API Timeout.")
        ActivityLog.objects.create(user=admin_user, bug=bug2, action="Assigned Developer", details="Assigned to developer.")
        AssignmentHistory.objects.create(bug=bug2, assigned_by=admin_user, assigned_to=dev_user)
        ActivityLog.objects.create(user=dev_user, bug=bug2, action="Status Changed", details="Changed status from Assigned to In Progress.")

        ActivityLog.objects.create(user=tester_user, bug=bug3, action="Created Bug", details="Logged SQL Injection Vulnerability.")
        ActivityLog.objects.create(user=admin_user, bug=bug3, action="Assigned Developer", details="Assigned to developer.")
        AssignmentHistory.objects.create(bug=bug3, assigned_by=admin_user, assigned_to=dev_user)

        ActivityLog.objects.create(user=tester_user, bug=bug4, action="Created Bug", details="Logged OAuth Token Leakage.")

        self.stdout.write("Database seeded successfully with users and bugs!")
