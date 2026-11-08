
from django.db import models
from django.conf import settings
from django.utils import timezone


class AuditEvent(models.Model):

    ACTION_CHOICES = [
        ('LOGIN_SUCCESS', 'Login Successful'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('DOCUMENT_UPLOAD', 'Document Uploaded'),
        ('DOCUMENT_VIEW', 'Document Viewed'),
        ('DOCUMENT_DOWNLOAD', 'Document Downloaded'),
        ('DOCUMENT_UPDATE', 'Document Updated'),
        ('DOCUMENT_DELETE', 'Document Deleted'),
        ('VERSION_CREATED', 'New Version Created'),
        ('PERMISSION_GRANTED', 'Permission Granted'),
        ('PERMISSION_REVOKED', 'Permission Revoked'),
        ('ACCESS_DENIED', 'Access Denied'),
        ('USER_ACTIVATED', 'User Activated'),
        ('USER_DEACTIVATED', 'User Deactivated'),
        ('STAFF_PRIVILEGE_CHANGED', 'Staff Privilege Changed'),
        ('SUPERUSER_PRIVILEGE_CHANGED', 'Superuser Privilege Changed'),
        ('USER_DETAILS_UPDATED', 'User Details Updated'),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='audit_events'
    )

    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='audit_events'
    )

    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='received_audit_events'
    )

    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES
    )

    description = models.TextField(blank=True)

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    user_agent = models.TextField(blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    previous_hash = models.CharField(max_length=64, blank=True)

    event_hash = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(
    default=timezone.now,
    editable=False,
)

    class Meta:

        ordering = ['-created_at']

        indexes = [
            models.Index(
                fields=['created_at'],
                name='audit_created_idx'
            ),
            models.Index(
                fields=['actor', 'created_at'],
                name='audit_actor_date_idx'
            ),
            models.Index(
                fields=['document', 'created_at'],
                name='audit_doc_date_idx'
            )
        ]

    def __str__(self):
        return f"{self.action} - {self.created_at}"
