from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserProfile, Bug, ROLE_ADMIN, ROLE_DEVELOPER, ROLE_TESTER, STATUS_OPEN, STATUS_ASSIGNED, STATUS_IN_PROGRESS, STATUS_RESOLVED

class BugTrackerTests(TestCase):

    def setUp(self):
        self.client = Client()
        
        # Create user accounts
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='Password123'
        )
        self.admin_user.profile.role = ROLE_ADMIN
        self.admin_user.profile.save()

        self.dev_user = User.objects.create_user(
            username='dev_test',
            email='dev@test.com',
            password='Password123'
        )
        self.dev_user.profile.role = ROLE_DEVELOPER
        self.dev_user.profile.save()

        self.tester_user = User.objects.create_user(
            username='tester_test',
            email='tester@test.com',
            password='Password123'
        )
        self.tester_user.profile.role = ROLE_TESTER
        self.tester_user.profile.save()

    def test_user_profile_creation(self):
        # Verify that post_save signals created profiles and saved roles correctly
        self.assertEqual(self.admin_user.profile.role, ROLE_ADMIN)
        self.assertEqual(self.dev_user.profile.role, ROLE_DEVELOPER)
        self.assertEqual(self.tester_user.profile.role, ROLE_TESTER)

    def test_email_or_username_authentication(self):
        # Authenticate using username
        login_username = self.client.login(username='dev_test', password='Password123')
        self.assertTrue(login_username)
        self.client.logout()

        # Authenticate using email
        login_email = self.client.login(username='dev@test.com', password='Password123')
        self.assertTrue(login_email)
        self.client.logout()

    def test_dashboard_gating_unauthenticated(self):
        # Unauthenticated users should be redirected to login page
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, '/login/?next=/dashboard/')

    def test_bug_creation_permissions(self):
        # Developers cannot create bugs (should return 403 Forbidden)
        self.client.login(username='dev_test', password='Password123')
        response = self.client.post(reverse('bug_create'), {
            'title': 'Developer Bug',
            'description': 'Dev should not be allowed to submit',
            'project_name': 'TestProj',
            'module_name': 'TestMod',
            'bug_type': 'UI Bug',
            'priority': 'Medium',
            'severity': 'Minor'
        })
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # Tester CAN create bugs
        self.client.login(username='tester_test', password='Password123')
        response = self.client.post(reverse('bug_create'), {
            'title': 'Tester Logged Bug',
            'description': 'Tester log test',
            'project_name': 'TestProj',
            'module_name': 'TestMod',
            'bug_type': 'Functional Bug',
            'priority': 'High',
            'severity': 'Major'
        })
        self.assertEqual(response.status_code, 302) # Should redirect to detail view
        self.assertTrue(Bug.objects.filter(title='Tester Logged Bug').exists())
        self.client.logout()

    def test_bug_workflow_permissions(self):
        # Create a test bug
        bug = Bug.objects.create(
            title='Sample Bug',
            description='Test bug flow',
            project_name='TestProj',
            module_name='TestMod',
            bug_type='UI Bug',
            priority='Low',
            severity='Minor',
            created_by=self.tester_user,
            status=STATUS_OPEN
        )

        # Developer trying to modify status of unassigned bug (should fail/403)
        self.client.login(username='dev_test', password='Password123')
        response = self.client.post(reverse('bug_status_update', args=[bug.pk]), {'status': STATUS_IN_PROGRESS})
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # Admin assigns developer to the bug
        self.client.login(username='admin_test', password='Password123')
        response = self.client.post(reverse('bug_assign', args=[bug.pk]), {'developer_id': self.dev_user.id})
        self.assertEqual(response.status_code, 302)
        bug.refresh_from_db()
        self.assertEqual(bug.assigned_to, self.dev_user)
        self.assertEqual(bug.status, STATUS_ASSIGNED)
        self.client.logout()

        # Developer can now change status to In Progress
        self.client.login(username='dev_test', password='Password123')
        response = self.client.post(reverse('bug_status_update', args=[bug.pk]), {'status': STATUS_IN_PROGRESS})
        self.assertEqual(response.status_code, 302)
        bug.refresh_from_db()
        self.assertEqual(bug.status, STATUS_IN_PROGRESS)

        # Developer resolves the bug
        response = self.client.post(reverse('bug_status_update', args=[bug.pk]), {'status': STATUS_RESOLVED})
        self.assertEqual(response.status_code, 302)
        bug.refresh_from_db()
        self.assertEqual(bug.status, STATUS_RESOLVED)
        self.client.logout()
