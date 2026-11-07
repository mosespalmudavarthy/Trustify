from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auditlog.models import AuditEvent
from auditlog.services import verify_event_chain


class LoginAuditTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.password = "TestPassword@123"
        self.user = User.objects.create_user(
            username="login_test_user",
            email="login_test@example.com",
            password=self.password,
        )

    def test_successful_login_creates_audit_event(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "login_test_user",
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        event = AuditEvent.objects.get(action="LOGIN_SUCCESS")

        self.assertEqual(event.actor, self.user)
        self.assertEqual(event.metadata, {})
        self.assertNotIn(self.password, str(event.metadata))

        self.assertTrue(verify_event_chain()["valid"])

    def test_failed_login_creates_audit_event(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "login_test_user",
                "password": "IncorrectPassword@123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)

        event = AuditEvent.objects.get(action="LOGIN_FAILED")

        self.assertIsNone(event.actor)
        self.assertEqual(
            event.metadata,
            {"username": "login_test_user"},
        )
        self.assertNotIn("password", str(event.metadata))
        self.assertNotIn("token", str(event.metadata).lower())

        self.assertTrue(verify_event_chain()["valid"])