
from django.db import models
from django.conf import settings


class Category(models.Model):

    name = models.CharField(max_length=100, unique=True)

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Document(models.Model):

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ARCHIVED', 'Archived'),
        ('DELETED', 'Deleted'),
    ]

    title = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_documents'
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )

    original_filename = models.CharField(max_length=255)

    storage_key = models.CharField(
        max_length=500,
        unique=True
    )

    mime_type = models.CharField(max_length=150)

    file_size = models.PositiveBigIntegerField()

    checksum = models.CharField(max_length=64, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class DocumentVersion(models.Model):

    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name='versions'
    )

    version_number = models.PositiveIntegerField()

    storage_key = models.CharField(
        max_length=500,
        unique=True
    )

    original_filename = models.CharField(max_length=255)

    mime_type = models.CharField(max_length=150)

    file_size = models.PositiveBigIntegerField()

    checksum = models.CharField(max_length=64, blank=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_versions'
    )

    change_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['document', 'version_number'],
                name='unique_document_version'
            )
        ]

        ordering = ['-version_number']

    def __str__(self):
        return f"{self.document.title} - v{self.version_number}"

class DocumentPermission(models.Model):

    ACCESS_CHOICES = [
        ('READ', 'Read Only'),
        ('EDIT', 'Read and Edit'),
    ]

    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name='permissions'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='document_permissions'
    )

    access_level = models.CharField(
        max_length=10,
        choices=ACCESS_CHOICES
    )

    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='granted_permissions'
    )

    granted_at = models.DateTimeField(auto_now_add=True)

    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=['document', 'user'],
                condition=models.Q(revoked_at__isnull=True),
                name='unique_active_document_permission'
            )
        ]

        ordering = ['-granted_at']

    @property
    def is_active(self):
        return self.revoked_at is None

    def __str__(self):
        return f"{self.user} - {self.document} - {self.access_level}"
