from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from auditlog.models import AuditEvent
from auditlog.services import record_event, verify_event_chain
from django.utils import timezone
from datetime import timedelta
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

        # Issue the token while the account is active.
        self.authenticate_user(user)

        # Deactivate the account after token issuance.
        user.is_active = False
        user.save(update_fields=["is_active"])

        # The previously issued token must no longer work.
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

class AdministrationAuditAPITests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="audit_api_admin",
            email="audit_api_admin@example.com",
            password="TestPassword123!",
        )

        self.target = User.objects.create_user(
            username="audit_api_target",
            password="TestPassword123!",
        )

        token = str(RefreshToken.for_user(self.admin).access_token)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

        self.list_url = "/api/administration/audit-events/"
        self.integrity_url = "/api/administration/audit-integrity/"

    def create_event(self, action, description, metadata=None):
        return record_event(
            action=action,
            actor=self.admin,
            target_user=self.target,
            description=description,
            metadata=metadata or {},
        )

    def test_superuser_can_list_audit_events(self):
        self.create_event(
            "LOGIN_SUCCESS",
            "Successful test login",
        )

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["action"],
            "LOGIN_SUCCESS",
        )

    def test_audit_event_search(self):
        self.create_event(
            "LOGIN_SUCCESS",
            "Unique searchable event",
        )
        self.create_event(
            "LOGIN_FAILED",
            "Different event",
        )

        response = self.client.get(
            self.list_url,
            {"search": "Unique searchable"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_audit_event_action_filter(self):
        self.create_event("LOGIN_SUCCESS", "Successful login")
        self.create_event("LOGIN_FAILED", "Failed login")

        response = self.client.get(
            self.list_url,
            {"action": "LOGIN_FAILED"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["action"],
            "LOGIN_FAILED",
        )

    def test_invalid_action_filter_is_rejected(self):
        response = self.client.get(
            self.list_url,
            {"action": "INVALID_ACTION"},
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_date_filter_is_rejected(self):
        response = self.client.get(
            self.list_url,
            {"date_from": "not-a-date"},
        )

        self.assertEqual(response.status_code, 400)

    def test_audit_event_pagination(self):
        for number in range(3):
            self.create_event(
                "LOGIN_SUCCESS",
                f"Pagination event {number}",
            )

        response = self.client.get(
            self.list_url,
            {"page_size": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIsNotNone(response.data["next"])

    def test_superuser_can_view_audit_event_details(self):
        event = self.create_event(
            "LOGIN_SUCCESS",
            "Detailed audit event",
            {
                "username": "audit_api_target",
                "password": "must-not-be-exposed",
                "access_token": "must-not-be-exposed",
                "nested": {
                    "secret": "must-not-be-exposed",
                    "status": "safe",
                },
            },
        )

        response = self.client.get(
            f"{self.list_url}{event.pk}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["event_hash"], event.event_hash)

        self.assertEqual(
            response.data["metadata"]["username"],
            "audit_api_target",
        )

        self.assertEqual(
            response.data["metadata"]["nested"]["status"],
            "safe",
        )

        self.assertNotIn("password", response.data["metadata"])
        self.assertNotIn("access_token", response.data["metadata"])
        self.assertNotIn("secret", response.data["metadata"]["nested"])

    def test_missing_audit_event_returns_404(self):
        response = self.client.get(
            f"{self.list_url}999999/"
        )

        self.assertEqual(response.status_code, 404)

    def test_superuser_can_verify_audit_integrity(self):
        self.create_event(
            "LOGIN_SUCCESS",
            "Integrity verification event",
        )

        response = self.client.get(self.integrity_url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["valid"])
        self.assertEqual(response.data["checked"], 1)

    def test_integrity_endpoint_detects_tampering(self):
        event = self.create_event(
            "LOGIN_SUCCESS",
            "Original audit event",
        )

        AuditEvent.objects.filter(pk=event.pk).update(
            description="Tampered audit event",
        )

        response = self.client.get(self.integrity_url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["valid"])
        self.assertEqual(
            response.data["invalid_event_id"],
            event.pk,
        )

    def test_audit_get_endpoints_do_not_modify_events(self):
        event = self.create_event(
            "LOGIN_SUCCESS",
            "Read-only verification",
        )

        original_hash = event.event_hash
        original_description = event.description

        self.client.get(self.list_url)
        self.client.get(f"{self.list_url}{event.pk}/")
        self.client.get(self.integrity_url)

        event.refresh_from_db()

        self.assertEqual(event.event_hash, original_hash)
        self.assertEqual(event.description, original_description)

    def test_ordinary_user_cannot_access_audit_endpoints(self):
        ordinary = User.objects.create_user(
            username="audit_api_ordinary",
            password="TestPassword123!",
        )

        token = str(
            RefreshToken.for_user(ordinary).access_token
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

        self.assertEqual(
            self.client.get(self.list_url).status_code,
            403,
        )

        self.assertEqual(
            self.client.get(self.integrity_url).status_code,
            403,
        )