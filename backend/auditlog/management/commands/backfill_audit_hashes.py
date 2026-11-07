from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from auditlog.models import AuditEvent
from auditlog.services import (
    acquire_audit_lock,
    build_event_hash,
    _verify_event_chain,
)


class Command(BaseCommand):

    help = "Safely backfill SHA-256 hashes for historical audit events."

    def handle(self, *args, **options):

        try:
            with transaction.atomic():

                acquire_audit_lock()

                total = AuditEvent.objects.count()

                if total == 0:
                    self.stdout.write(
                        self.style.WARNING(
                            "No audit events found. Nothing to backfill."
                        )
                    )
                    return

                unhashed = AuditEvent.objects.filter(
                    event_hash=""
                ).count()

                hashed = AuditEvent.objects.exclude(
                    event_hash=""
                ).count()

                if unhashed == 0:
                    verification = _verify_event_chain()

                    if not verification["valid"]:
                        raise CommandError(
                            "Existing audit chain is invalid. "
                            f'Event ID: {verification["invalid_event_id"]}. '
                            f'Reason: {verification["reason"]}'
                        )

                    if verification["checked"] != total:
                        raise CommandError(
                            "Audit verification count does not match "
                            "the total event count."
                        )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"All {verification['checked']} audit events "
                            "are already hashed and verified. "
                            "No changes made."
                        )
                    )
                    return

                if unhashed != total or hashed != 0:
                    raise CommandError(
                        "Expected every audit event to be unhashed. "
                        "Mixed or inconsistent hash state detected. "
                        "Refusing to modify the audit chain."
                    )

                self.stdout.write(
                    f"Preparing to backfill {total} historical events."
                )

                previous_hash = ""

                events = AuditEvent.objects.order_by("pk")

                for event in events:

                    if event.previous_hash:
                        raise CommandError(
                            f"Event {event.pk} already has a previous hash. "
                            "Refusing to overwrite existing data."
                        )

                    event.previous_hash = previous_hash

                    event.event_hash = build_event_hash(event)

                    event.save(
                        update_fields=[
                            "previous_hash",
                            "event_hash",
                        ]
                    )

                    previous_hash = event.event_hash

                verification = _verify_event_chain()

                if not verification["valid"]:
                    raise CommandError(
                        "Backfill verification failed. "
                        f'Event ID: {verification["invalid_event_id"]}. '
                        f'Reason: {verification["reason"]}'
                    )

                if verification["checked"] != total:
                    raise CommandError(
                        "Backfill verification count does not match "
                        "the original event count."
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully hashed and verified "
                        f"{verification['checked']} audit events."
                    )
                )

        except Exception as error:

            if isinstance(error, CommandError):
                raise

            raise CommandError(
                f"Audit backfill failed: {error}"
            ) from error