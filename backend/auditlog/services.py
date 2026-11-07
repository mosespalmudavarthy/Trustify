
import hashlib
import hmac
import json

from django.db import connection, transaction

from .models import AuditEvent


class AuditChainIntegrityError(Exception):
    """Raised when the audit chain cannot be trusted."""


# PostgreSQL advisory-lock identifiers.
AUDIT_LOCK_NAMESPACE = 170219
AUDIT_LOCK_ID = 1


def acquire_audit_lock():
    """
    Serialize audit-chain writes using a PostgreSQL transaction lock.
    """

    if connection.vendor != "postgresql":
        raise RuntimeError(
            "Audit-chain locking requires PostgreSQL."
        )

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_xact_lock(%s, %s)",
            [AUDIT_LOCK_NAMESPACE, AUDIT_LOCK_ID],
        )


def build_event_hash(event):
    """
    Generate a SHA-256 hash from canonical audit-event data.
    """

    event_data = {
        "id": event.pk,
        "actor_id": event.actor_id,
        "document_id": event.document_id,
        "target_user_id": event.target_user_id,
        "action": event.action,
        "description": event.description,
        "ip_address": event.ip_address,
        "user_agent": event.user_agent,
        "metadata": event.metadata,
        "previous_hash": event.previous_hash,
        "created_at": event.created_at.isoformat(),
    }

    canonical_data = json.dumps(
        event_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        canonical_data.encode("utf-8")
    ).hexdigest()


def _verify_event_chain():
    """
    Verify every event in primary-key order.
    Must be called inside a database transaction.
    """

    previous_hash = ""
    checked = 0

    events = AuditEvent.objects.order_by("pk").iterator()

    for event in events:

        if event.previous_hash != previous_hash:
            return {
                "valid": False,
                "checked": checked,
                "invalid_event_id": event.pk,
                "reason": "Previous hash mismatch.",
            }

        calculated_hash = build_event_hash(event)

        if not event.event_hash or not hmac.compare_digest(
            event.event_hash,
            calculated_hash,
        ):
            return {
                "valid": False,
                "checked": checked,
                "invalid_event_id": event.pk,
                "reason": "Event hash mismatch or missing hash.",
            }

        previous_hash = event.event_hash
        checked += 1

    return {
        "valid": True,
        "checked": checked,
        "invalid_event_id": None,
        "reason": None,
    }


def verify_event_chain():
    """
    Public read-only audit-chain verification function.
    """

    with transaction.atomic():
        acquire_audit_lock()
        return _verify_event_chain()


def record_event(
    *,
    action,
    request=None,
    actor=None,
    document=None,
    target_user=None,
    description="",
    metadata=None,
):
    """
    Create and hash an audit event transactionally.

    Refuses to append events if the existing chain is invalid.
    """

    with transaction.atomic():

        acquire_audit_lock()

        verification = _verify_event_chain()

        if not verification["valid"]:
            raise AuditChainIntegrityError(
                "Cannot append audit event: "
                f'{verification["reason"]} '
                f'Event ID: {verification["invalid_event_id"]}'
            )

        if actor is None and request is not None:
            request_user = getattr(request, "user", None)

            if request_user and request_user.is_authenticated:
                actor = request_user

        ip_address = None
        user_agent = ""

        if request is not None:
            # Use REMOTE_ADDR rather than trusting an unverified
            # X-Forwarded-For header.
            ip_address = request.META.get("REMOTE_ADDR")
            user_agent = request.META.get("HTTP_USER_AGENT", "")

        previous_event = (
            AuditEvent.objects.order_by("-pk").first()
        )

        previous_hash = (
            previous_event.event_hash
            if previous_event
            else ""
        )

        event = AuditEvent.objects.create(
            actor=actor,
            document=document,
            target_user=target_user,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
            previous_hash=previous_hash,
        )

        event.event_hash = build_event_hash(event)

        event.save(update_fields=["event_hash"])

        return event
