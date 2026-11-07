
from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import AuditEvent
from .services import (
    AuditChainIntegrityError,
    build_event_hash,
    record_event,
    verify_event_chain,
)


User = get_user_model()


class AuditServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="audit_test_user",
            password="TestPassword123!",
        )

    def test_event_hash_is_64_character_sha256(self):
        event = AuditEvent.objects.create(
            actor=self.user,
            action="DOCUMENT_UPLOAD",
            description="Test event",
        )

        event.refresh_from_db()

        event_hash = build_event_hash(event)

        self.assertEqual(len(event_hash), 64)
        self.assertEqual(event_hash, build_event_hash(event))

    def test_record_event_creates_hashed_event(self):
        event = record_event(
            action="DOCUMENT_UPLOAD",
            actor=self.user,
            description="Test document upload",
        )

        event.refresh_from_db()

        self.assertTrue(event.event_hash)
        self.assertEqual(len(event.event_hash), 64)
        self.assertEqual(event.previous_hash, "")

    def test_consecutive_events_are_linked(self):
        first_event = record_event(
            action="DOCUMENT_UPLOAD",
            actor=self.user,
            description="First event",
        )

        second_event = record_event(
            action="DOCUMENT_UPDATE",
            actor=self.user,
            description="Second event",
        )

        self.assertEqual(
            second_event.previous_hash,
            first_event.event_hash,
        )

    def test_valid_chain_passes_verification(self):
        record_event(
            action="DOCUMENT_UPLOAD",
            actor=self.user,
            description="First event",
        )

        record_event(
            action="DOCUMENT_UPDATE",
            actor=self.user,
            description="Second event",
        )

        result = verify_event_chain()

        self.assertTrue(result["valid"])
        self.assertEqual(result["checked"], 2)

    def test_modified_event_is_detected(self):
        event = record_event(
            action="DOCUMENT_UPLOAD",
            actor=self.user,
            description="Original description",
        )

        AuditEvent.objects.filter(pk=event.pk).update(
            description="Modified description",
        )

        result = verify_event_chain()

        self.assertFalse(result["valid"])
        self.assertEqual(
            result["invalid_event_id"],
            event.pk,
        )

    def test_invalid_chain_rejects_new_event(self):
        event = record_event(
            action="DOCUMENT_UPLOAD",
            actor=self.user,
            description="Original event",
        )

        AuditEvent.objects.filter(pk=event.pk).update(
            description="Tampered event",
        )

        with self.assertRaises(AuditChainIntegrityError):
            record_event(
                action="DOCUMENT_UPDATE",
                actor=self.user,
                description="Should be rejected",
            )
