from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tracker.models import (
    UserProfile, Bug, Comment, ActivityLog, AssignmentHistory,
    ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_PM, ROLE_TEAM_LEAD,
    ROLE_DEVELOPER, ROLE_TESTER, ROLE_CLIENT,
    STATUS_OPEN, STATUS_ASSIGNED, STATUS_IN_PROGRESS, STATUS_PASSED,
    STATUS_TESTING, STATUS_CLOSED, STATUS_REOPENED, STATUS_REJECTED,
    STATUS_CODE_REVIEW, STATUS_READY_TESTING, STATUS_NEW, STATUS_ACKNOWLEDGED,
    BUG_TYPE_UI, BUG_TYPE_API, BUG_TYPE_SECURITY, BUG_TYPE_PERFORMANCE, BUG_TYPE_DATABASE,
    PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_CRITICAL,
    SEVERITY_MINOR, SEVERITY_MAJOR, SEVERITY_CRITICAL, SEVERITY_BLOCKER
)


class Command(BaseCommand):
    help = 'Seeds the database with all 7 role-based demo users and sample bugs.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding database with demo data...'))

        # ── 1. CREATE ALL ROLE USERS ──────────────────────────────────────────

        users_config = [
            # (username, password, first, last, email, role)
            ('superadmin', 'super123',  'Super',   'Admin',   'superadmin@bugtracker.com', ROLE_SUPER_ADMIN),
            ('admin',      'admin123',  'Alan',    'Turing',  'admin@bugtracker.com',      ROLE_ADMIN),
            ('pm',         'pm123',     'Project', 'Manager', 'pm@bugtracker.com',         ROLE_PM),
            ('teamlead',   'lead123',   'Team',    'Lead',    'lead@bugtracker.com',        ROLE_TEAM_LEAD),
            ('developer',  'dev123',    'Grace',   'Hopper',  'dev@bugtracker.com',         ROLE_DEVELOPER),
            ('tester',     'tester123', 'Margaret','Hamilton','tester@bugtracker.com',      ROLE_TESTER),
            ('client',     'client123', 'Client',  'User',    'client@bugtracker.com',      ROLE_CLIENT),
        ]

        created_users = {}
        for username, password, first, last, email, role in users_config:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email, 'first_name': first, 'last_name': last}
            )
            # Always ensure password is set (idempotent on re-deploy)
            user.set_password(password)
            user.first_name = first
            user.last_name = last
            user.email = email
            user.is_active = True
            user.save()
            user.profile.role = role
            user.profile.save()
            created_users[username] = user
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {role:<18} | {username:<12} / {password}')

        # Shortcuts
        superadmin_user = created_users['superadmin']
        admin_user      = created_users['admin']
        pm_user         = created_users['pm']
        lead_user       = created_users['teamlead']
        dev_user        = created_users['developer']
        tester_user     = created_users['tester']
        client_user     = created_users['client']

        # ── 2. CLEAR OLD BUGS / LOGS (safe for re-seed) ──────────────────────
        Bug.objects.all().delete()
        ActivityLog.objects.all().delete()
        AssignmentHistory.objects.all().delete()
        Comment.objects.all().delete()

        # ── 3. CREATE SAMPLE BUGS ────────────────────────────────────────────

        bug1 = Bug.objects.create(
            title="UI alignment offset on Login Card component",
            description="The card container alignment shifts slightly left on screen widths between 768px–1024px. Bootstrap container margin layout classes are missing alignment overrides.",
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
            description="The GET /api/v1/analytics fetches all rows sequentially instead of using aggregation, causing timeout on datasets exceeding 10,000 rows.",
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
            description="Search input in user management appends strings directly into raw SQL. A malicious payload can bypass permission gating.",
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
            description="When user cancels registration flow, redirect callback URL exposes client tokens in query parameters of the error response header.",
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
            title="Slow chart rendering during page load on Mobile Safari",
            description="On iOS Safari, Chart.js context creation causes layout reflow loops — animations block CPU for 3–4 seconds on initial load.",
            project_name="Analytics Engine",
            module_name="Charts UI",
            bug_type=BUG_TYPE_PERFORMANCE,
            priority=PRIORITY_MEDIUM,
            severity=SEVERITY_MAJOR,
            status=STATUS_PASSED,
            created_by=tester_user,
            assigned_to=dev_user
        )

        bug6 = Bug.objects.create(
            title="Password reset email not delivered in production",
            description="The password reset flow works locally but emails are not delivered in the production environment. SMTP credentials need verification.",
            project_name="Portal Redesign",
            module_name="Authentication",
            bug_type=BUG_TYPE_API,
            priority=PRIORITY_HIGH,
            severity=SEVERITY_MAJOR,
            status=STATUS_READY_TESTING,
            created_by=client_user,
            assigned_to=dev_user
        )

        bug7 = Bug.objects.create(
            title="Dashboard stats counter resets on page refresh",
            description="The animated counters on the dashboard reset to zero on every page refresh instead of persisting their final values.",
            project_name="Analytics Engine",
            module_name="Dashboard",
            bug_type=BUG_TYPE_UI,
            priority=PRIORITY_LOW,
            severity=SEVERITY_MINOR,
            status=STATUS_NEW,
            created_by=client_user,
            assigned_to=None
        )

        # ── 4. CREATE COMMENTS ────────────────────────────────────────────────

        c1 = Comment.objects.create(
            bug=bug2,
            user=dev_user,
            comment_text="Traced this to missing GROUP BY indexes on activity log datetime columns. Working on a paginated aggregation fix."
        )
        Comment.objects.create(
            bug=bug2,
            user=tester_user,
            parent=c1,
            comment_text="Sounds good — please also verify correct page size offset handling when the fix is ready!"
        )
        Comment.objects.create(
            bug=bug3,
            user=admin_user,
            comment_text="Critical security issue — prioritize this sprint. Use Django ORM parameterized queries only."
        )

        # ── 5. CREATE ACTIVITY LOGS & ASSIGNMENT HISTORY ─────────────────────

        ActivityLog.objects.create(user=tester_user, bug=bug1, action="Created Bug", details="Logged UI margin misalignment.")
        ActivityLog.objects.create(user=admin_user,  bug=bug1, action="Assigned Developer", details="Assigned to developer.")
        AssignmentHistory.objects.create(bug=bug1, assigned_by=admin_user, assigned_to=dev_user)
        ActivityLog.objects.create(user=dev_user,    bug=bug1, action="Status Changed", details="In Progress → Code Review")
        ActivityLog.objects.create(user=dev_user,    bug=bug1, action="Status Changed", details="Code Review → Ready for Testing")
        ActivityLog.objects.create(user=tester_user, bug=bug1, action="Status Changed", details="Ready for Testing → Testing")
        ActivityLog.objects.create(user=tester_user, bug=bug1, action="Status Changed", details="Testing → Passed")
        ActivityLog.objects.create(user=admin_user,  bug=bug1, action="Status Changed", details="Passed → Closed")

        ActivityLog.objects.create(user=tester_user, bug=bug2, action="Created Bug", details="Logged API Timeout issue.")
        ActivityLog.objects.create(user=admin_user,  bug=bug2, action="Assigned Developer", details="Assigned to developer.")
        AssignmentHistory.objects.create(bug=bug2, assigned_by=admin_user, assigned_to=dev_user)
        ActivityLog.objects.create(user=dev_user,    bug=bug2, action="Status Changed", details="Assigned → In Progress")

        ActivityLog.objects.create(user=tester_user, bug=bug3, action="Created Bug", details="Logged SQL Injection Vulnerability.")
        ActivityLog.objects.create(user=admin_user,  bug=bug3, action="Assigned Developer", details="Assigned to developer.")
        AssignmentHistory.objects.create(bug=bug3, assigned_by=admin_user, assigned_to=dev_user)

        ActivityLog.objects.create(user=tester_user, bug=bug4, action="Created Bug", details="Logged OAuth Token Leakage.")
        ActivityLog.objects.create(user=client_user, bug=bug6, action="Created Bug", details="Reported password reset email issue.")
        ActivityLog.objects.create(user=client_user, bug=bug7, action="Created Bug", details="Reported dashboard counter reset.")

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Login Credentials:'))
        self.stdout.write('  superadmin / super123  -> Super Admin')
        self.stdout.write('  admin      / admin123  -> Admin')
        self.stdout.write('  pm         / pm123     -> Project Manager')
        self.stdout.write('  teamlead   / lead123   -> Team Lead')
        self.stdout.write('  developer  / dev123    -> Developer')
        self.stdout.write('  tester     / tester123 -> Tester')
        self.stdout.write('  client     / client123 -> Client')
