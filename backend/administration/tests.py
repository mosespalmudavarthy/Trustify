from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from auditlog.models import AuditEvent
from auditlog.services import verify_event_chain
from documents.models import Document, DocumentVersion


User = get_user_model()


class AdministrationDashboardTests(APITestCase):

    dashboard_url = "/api/administration/dashboard/"

    def create_user(self, username, is_staff=False, is_superuser=False):
        return User.objects.create_user(
            username=username,
            password="TestPassword123!",
            is_staff=is_staff,
            is_superuser=is_superuser,
        )

    def authenticate_user(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

    def test_anonymous_user_is_denied(self):
        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 401)

    def test_ordinary_user_is_denied(self):
        user = self.create_user("dashboard_ordinary")
        self.authenticate_user(user)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 403)

    def test_staff_user_without_superuser_status_is_denied(self):
        user = self.create_user(
            "dashboard_staff",
            is_staff=True,
        )
        self.authenticate_user(user)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 403)

    def test_inactive_superuser_is_denied(self):
        user = User.objects.create_superuser(
            username="dashboard_inactive_admin",
            email="dashboard_inactive@example.com",
            password="TestPassword123!",
        )
        user.is_active = False
        user.save(update_fields=["is_active"])

        self.authenticate_user(user)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 401)

    def test_active_superuser_can_access_dashboard(self):
        user = User.objects.create_superuser(
            username="dashboard_admin",
            email="dashboard_admin@example.com",
            password="TestPassword123!",
        )
        self.authenticate_user(user)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            set(response.data.keys()),
            {
                "users",
                "documents",
                "versions",
                "storage",
                "audit",
                "recent_security_events",
            },
        )

        self.assertEqual(response.data["users"]["total"], 1)
        self.assertEqual(response.data["documents"]["total"], 0)
        self.assertEqual(response.data["versions"]["total"], 0)


    def test_superuser_can_list_users(self):
        admin = User.objects.create_superuser(
            username="list_admin",
            email="list_admin@example.com",
            password="TestPassword123!",
        )
        self.create_user("list_ordinary")
        self.authenticate_user(admin)

        response = self.client.get(
            "/api/administration/users/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 2)

        first_user = response.data["results"][0]

        self.assertIn("username", first_user)
        self.assertNotIn("password", first_user)

    def test_user_list_search(self):
        admin = User.objects.create_superuser(
            username="search_admin",
            email="search_admin@example.com",
            password="TestPassword123!",
        )
        self.create_user("search_target")
        self.create_user("another_user")
        self.authenticate_user(admin)

        response = self.client.get(
            "/api/administration/users/?search=search_target"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["username"],
            "search_target",
        )

    def test_ordinary_user_cannot_list_users(self):
        user = self.create_user("list_denied_user")
        self.authenticate_user(user)

        response = self.client.get(
            "/api/administration/users/"
        )

        self.assertEqual(response.status_code, 403)
    def test_superuser_can_view_user_details(self):
        admin = User.objects.create_superuser(
            username="detail_admin",
            email="detail_admin@example.com",
            password="TestPassword123!",
        )
        target = self.create_user("detail_target")
        self.authenticate_user(admin)

        response = self.client.get(
            f"/api/administration/users/{target.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "detail_target")
        self.assertNotIn("password", response.data)

    def test_user_details_returns_404_for_missing_user(self):
        admin = User.objects.create_superuser(
            username="detail_admin_404",
            email="detail_admin_404@example.com",
            password="TestPassword123!",
        )
        self.authenticate_user(admin)

        response = self.client.get(
            "/api/administration/users/999999/"
        )

        self.assertEqual(response.status_code, 404)

    def test_ordinary_user_cannot_view_user_details(self):
        ordinary = self.create_user("detail_denied")
        target = self.create_user("detail_private")
        self.authenticate_user(ordinary)

        response = self.client.get(
            f"/api/administration/users/{target.id}/"
        )

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_deactivate_user(self):
        admin = User.objects.create_superuser(
            username="status_admin",
            email="status_admin@example.com",
            password="TestPassword123!",
        )
        target = self.create_user("status_target")
        self.authenticate_user(admin)

        response = self.client.patch(
            f"/api/administration/users/{target.id}/status/",
            {"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        target.refresh_from_db()
        self.assertFalse(target.is_active)

        event = AuditEvent.objects.get(
            action="USER_DEACTIVATED",
            target_user=target,
        )
        self.assertEqual(event.actor, admin)
        self.assertTrue(verify_event_chain()["valid"])

    def test_superuser_can_activate_user(self):
        admin = User.objects.create_superuser(
            username="activate_admin",
            email="activate_admin@example.com",
            password="TestPassword123!",
        )
        target = self.create_user("activate_target")
        target.is_active = False
        target.save(update_fields=["is_active"])

        self.authenticate_user(admin)

        response = self.client.patch(
            f"/api/administration/users/{target.id}/status/",
            {"is_active": True},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        target.refresh_from_db()
        self.assertTrue(target.is_active)

        self.assertTrue(
            AuditEvent.objects.filter(
                action="USER_ACTIVATED",
                target_user=target,
                actor=admin,
            ).exists()
        )

    def test_superuser_cannot_deactivate_own_account(self):
        admin = User.objects.create_superuser(
            username="self_status_admin",
            email="self_status_admin@example.com",
            password="TestPassword123!",
        )
        self.authenticate_user(admin)

        response = self.client.patch(
            f"/api/administration/users/{admin.id}/status/",
            {"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        admin.refresh_from_db()
        self.assertTrue(admin.is_active)

        self.assertFalse(
            AuditEvent.objects.filter(
                action="USER_DEACTIVATED",
                target_user=admin,
            ).exists()
        )
    def test_superuser_can_promote_user(self):
        admin = User.objects.create_superuser(
            username="privilege_admin",
            email="privilege_admin@example.com",
            password="TestPassword123!",
        )
        target = self.create_user("privilege_target")
        self.authenticate_user(admin)

        response = self.client.patch(
            f"/api/administration/users/{target.id}/privileges/",
            {"is_superuser": True},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        target.refresh_from_db()
        self.assertTrue(target.is_superuser)
        self.assertTrue(target.is_staff)

        self.assertTrue(
            AuditEvent.objects.filter(
                action="SUPERUSER_PRIVILEGE_CHANGED",
                actor=admin,
                target_user=target,
            ).exists()
        )
        self.assertTrue(verify_event_chain()["valid"])

    def test_superuser_can_demote_another_superuser(self):
        admin = User.objects.create_superuser(
            username="demote_admin",
            email="demote_admin@example.com",
            password="TestPassword123!",
        )
        target = User.objects.create_superuser(
            username="demote_target",
            email="demote_target@example.com",
            password="TestPassword123!",
        )
        self.authenticate_user(admin)

        response = self.client.patch(
            f"/api/administration/users/{target.id}/privileges/",
            {"is_superuser": False},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        target.refresh_from_db()
        self.assertFalse(target.is_superuser)
        self.assertFalse(target.is_staff)

        self.assertTrue(
            AuditEvent.objects.filter(
                action="SUPERUSER_PRIVILEGE_CHANGED",
                actor=admin,
                target_user=target,
            ).exists()
        )
        self.assertTrue(verify_event_chain()["valid"])
        self.assertTrue(
            AuditEvent.objects.filter(
                action="STAFF_PRIVILEGE_CHANGED",
                actor=admin,
                target_user=target,
            ).exists()
        )

    def test_superuser_cannot_remove_own_superuser_privileges(self):
        admin = User.objects.create_superuser(
            username="self_privilege_admin",
            email="self_privilege_admin@example.com",
            password="TestPassword123!",
        )
        self.authenticate_user(admin)

        response = self.client.patch(
            f"/api/administration/users/{admin.id}/privileges/",
            {"is_superuser": False},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        admin.refresh_from_db()
        self.assertTrue(admin.is_superuser)

    def test_demoting_another_superuser_preserves_an_active_superuser(self):
        admin = User.objects.create_superuser(
            username="remaining_admin",
            email="remaining_admin@example.com",
            password="TestPassword123!",
        )

        target = User.objects.create_superuser(
            username="demotion_target",
            email="demotion_target@example.com",
            password="TestPassword123!",
        )

        self.authenticate_user(admin)

        response = self.client.patch(
            f"/api/administration/users/{target.id}/privileges/",
            {"is_superuser": False},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        admin.refresh_from_db()
        target.refresh_from_db()

        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_superuser)
        self.assertFalse(target.is_superuser)

        self.assertEqual(
            User.objects.filter(
                is_active=True,
                is_superuser=True,
            ).count(),
            1,
        )