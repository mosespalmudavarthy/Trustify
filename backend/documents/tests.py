
import hashlib
from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from django.utils import timezone

from documents.models import Document, DocumentPermission
from documents.access import (
    is_platform_admin,
    is_document_owner,
    get_active_permission,
    can_view_document,
    can_edit_document,
    can_manage_permissions,
)


class DocumentAccessTests(TestCase):

    def setUp(self):

        self.owner = User.objects.create_user(
            username='document_owner',
            password='TestPassword123!'
        )

        self.reader = User.objects.create_user(
            username='document_reader',
            password='TestPassword123!'
        )

        self.editor = User.objects.create_user(
            username='document_editor',
            password='TestPassword123!'
        )

        self.revoked_user = User.objects.create_user(
            username='revoked_user',
            password='TestPassword123!'
        )

        self.admin = User.objects.create_superuser(
            username='platform_admin',
            email='admin@example.com',
            password='TestPassword123!'
        )

        self.document = Document.objects.create(
            title='Trustify Authorization Test',
            description='Document used for authorization testing.',
            owner=self.owner,
            original_filename='authorization_test.txt',
            storage_key='documents/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.txt',
            mime_type='text/plain',
            file_size=100,
            checksum='a' * 64,
            status='ACTIVE',
        )

        self.read_permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.reader,
            access_level='READ',
            granted_by=self.owner,
        )

        self.edit_permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.editor,
            access_level='EDIT',
            granted_by=self.owner,
        )

        self.revoked_permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.revoked_user,
            access_level='EDIT',
            granted_by=self.owner,
            revoked_at=timezone.now(),
        )

    # Platform administrator tests

    def test_superuser_is_platform_admin(self):
        self.assertTrue(is_platform_admin(self.admin))

    def test_regular_user_is_not_platform_admin(self):
        self.assertFalse(is_platform_admin(self.owner))

    # Document ownership tests

    def test_owner_is_document_owner(self):
        self.assertTrue(
            is_document_owner(self.owner, self.document)
        )

    def test_non_owner_is_not_document_owner(self):
        self.assertFalse(
            is_document_owner(self.reader, self.document)
        )

    # Active permission tests

    def test_active_read_permission_is_retrieved(self):
        permission = get_active_permission(
            self.reader,
            self.document
        )

        self.assertIsNotNone(permission)
        self.assertEqual(permission.access_level, 'READ')

    def test_revoked_permission_is_not_retrieved(self):
        permission = get_active_permission(
            self.revoked_user,
            self.document
        )

        self.assertIsNone(permission)

    # Document viewing tests

    def test_owner_can_view_document(self):
        self.assertTrue(
            can_view_document(self.owner, self.document)
        )

    def test_reader_can_view_document(self):
        self.assertTrue(
            can_view_document(self.reader, self.document)
        )

    def test_editor_can_view_document(self):
        self.assertTrue(
            can_view_document(self.editor, self.document)
        )

    def test_revoked_user_cannot_view_document(self):
        self.assertFalse(
            can_view_document(self.revoked_user, self.document)
        )

    def test_anonymous_user_cannot_view_document(self):
        self.assertFalse(
            can_view_document(AnonymousUser(), self.document)
        )

    # Document editing tests

    def test_owner_can_edit_document(self):
        self.assertTrue(
            can_edit_document(self.owner, self.document)
        )

    def test_editor_can_edit_document(self):
        self.assertTrue(
            can_edit_document(self.editor, self.document)
        )

    def test_reader_cannot_edit_document(self):
        self.assertFalse(
            can_edit_document(self.reader, self.document)
        )

    def test_revoked_user_cannot_edit_document(self):
        self.assertFalse(
            can_edit_document(self.revoked_user, self.document)
        )

    # Permission management tests

    def test_owner_can_manage_permissions(self):
        self.assertTrue(
            can_manage_permissions(self.owner, self.document)
        )

    def test_platform_admin_can_manage_permissions(self):
        self.assertTrue(
            can_manage_permissions(self.admin, self.document)
        )

    def test_editor_cannot_manage_permissions(self):
        self.assertFalse(
            can_manage_permissions(self.editor, self.document)
        )

    def test_reader_cannot_manage_permissions(self):
        self.assertFalse(
            can_manage_permissions(self.reader, self.document)
        )

    # Document status tests

    def test_reader_cannot_view_archived_document(self):
        self.document.status = 'ARCHIVED'
        self.document.save(update_fields=['status'])

        self.assertFalse(
            can_view_document(self.reader, self.document)
        )

    def test_reader_cannot_edit_archived_document(self):
        self.document.status = 'ARCHIVED'
        self.document.save(update_fields=['status'])

        self.assertFalse(
            can_edit_document(self.reader, self.document)
        )

    def test_owner_cannot_view_archived_document(self):
        self.document.status = 'ARCHIVED'
        self.document.save(update_fields=['status'])

        self.assertFalse(
            can_view_document(self.owner, self.document)
        )
    def test_owner_cannot_view_archived_document(self):
        self.document.status = 'ARCHIVED'
        self.document.save(update_fields=['status'])

        self.assertFalse(
            can_view_document(self.owner, self.document)
        )
    def test_admin_cannot_view_deleted_document(self):
        self.document.status = 'DELETED'
        self.document.deleted_at = timezone.now()
        self.document.save(update_fields=['status', 'deleted_at'])

        self.assertFalse(
            can_view_document(self.admin, self.document)
        )

    def test_owner_cannot_view_deleted_document(self):
        self.document.status = 'DELETED'
        self.document.deleted_at = timezone.now()
        self.document.save(update_fields=['status', 'deleted_at'])

        self.assertFalse(
            can_view_document(self.owner, self.document)
        )

    def test_reader_cannot_view_deleted_document(self):
        self.document.status = 'DELETED'
        self.document.deleted_at = timezone.now()
        self.document.save(update_fields=['status', 'deleted_at'])

        self.assertFalse(
            can_view_document(self.reader, self.document)
        )

    def test_admin_cannot_edit_deleted_document(self):
        self.document.status = 'DELETED'
        self.document.deleted_at = timezone.now()
        self.document.save(update_fields=['status', 'deleted_at'])

        self.assertFalse(
            can_edit_document(self.admin, self.document)
        )

# ============================================================
# DOCUMENT API ENDPOINT TESTS
# ============================================================

import tempfile

from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from rest_framework.test import APIClient

from auditlog.models import AuditEvent
from documents.models import DocumentVersion


class DocumentAPITests(TestCase):

    def setUp(self):

        # Create isolated temporary storage for API tests.
        self.temp_directory = tempfile.TemporaryDirectory()

        self.test_storage = FileSystemStorage(
            location=self.temp_directory.name,
            base_url=None
        )

        # Ensure both the storage helpers and document views
        # use the temporary storage directory.
        self.storage_patcher = patch(
            'documents.storage.private_storage',
            self.test_storage
        )

        self.views_storage_patcher = patch(
            'documents.views.private_storage',
            self.test_storage
        )

        self.storage_patcher.start()
        self.views_storage_patcher.start()

        self.client = APIClient()

        self.owner = User.objects.create_user(
            username='api_owner',
            password='TestPassword123!'
        )

        self.reader = User.objects.create_user(
            username='api_reader',
            password='TestPassword123!'
        )

        self.editor = User.objects.create_user(
            username='api_editor',
            password='TestPassword123!'
        )

        self.revoked_user = User.objects.create_user(
            username='api_revoked',
            password='TestPassword123!'
        )

        self.admin = User.objects.create_superuser(
            username='api_admin',
            email='apiadmin@example.com',
            password='TestPassword123!'
        )

        # Create a real file inside the isolated test storage.
        self.original_content = b'Original Trustify document.\n'

        self.storage_key = (
            f'documents/{uuid4().hex}.txt'
        )

        self.test_storage.save(
            self.storage_key,
            SimpleUploadedFile(
                'original.txt',
                self.original_content,
                content_type='text/plain'
            )
        )

        self.document = Document.objects.create(
            title='API Test Document',
            description='Document used for API endpoint tests.',
            owner=self.owner,
            original_filename='original.txt',
            storage_key=self.storage_key,
            mime_type='text/plain',
            file_size=len(self.original_content),
            checksum=hashlib.sha256(
                self.original_content
            ).hexdigest(),
            status='ACTIVE'
        )

        self.version = DocumentVersion.objects.create(
            document=self.document,
            version_number=1,
            storage_key=self.storage_key,
            original_filename='original.txt',
            mime_type='text/plain',
            file_size=len(self.original_content),
            checksum=hashlib.sha256(
                self.original_content
            ).hexdigest(),
            uploaded_by=self.owner,
            change_note='Initial version'
        )

        self.read_permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.reader,
            access_level='READ',
            granted_by=self.owner
        )

        self.edit_permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.editor,
            access_level='EDIT',
            granted_by=self.owner
        )

        self.revoked_permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.revoked_user,
            access_level='EDIT',
            granted_by=self.owner,
            revoked_at=timezone.now()
        )

    def tearDown(self):

        self.storage_patcher.stop()
        self.views_storage_patcher.stop()

        self.temp_directory.cleanup()

    def authenticate_as(self, user):

        self.client.force_authenticate(user=user)

    # --------------------------------------------------------
    # DOCUMENT UPLOAD TESTS
    # --------------------------------------------------------

    def test_owner_can_upload_document(self):

        self.authenticate_as(self.owner)

        uploaded_file = SimpleUploadedFile(
            'new_document.txt',
            b'New Trustify document.',
            content_type='text/plain'
        )

        response = self.client.post(
            reverse('document-upload'),
            {
                'title': 'New API Upload',
                'description': 'Uploaded through the API.',
                'file': uploaded_file
            },
            format='multipart'
        )

        self.assertEqual(response.status_code, 201)

        document = Document.objects.get(
            title='New API Upload'
        )

        self.assertEqual(document.owner, self.owner)
        self.assertEqual(document.file_size, len(b'New Trustify document.'))

        self.assertTrue(
            self.test_storage.exists(document.storage_key)
        )

        self.assertTrue(
            DocumentVersion.objects.filter(
                document=document,
                version_number=1
            ).exists()
        )

        self.assertTrue(
            AuditEvent.objects.filter(
                document=document,
                action='DOCUMENT_UPLOAD'
            ).exists()
        )

    def test_upload_rejects_unsupported_file_extension(self):

        self.authenticate_as(self.owner)

        uploaded_file = SimpleUploadedFile(
            'malicious.exe',
            b'Not an allowed file.',
            content_type='application/octet-stream'
        )

        response = self.client.post(
            reverse('document-upload'),
            {
                'title': 'Invalid Upload',
                'file': uploaded_file
            },
            format='multipart'
        )

        self.assertEqual(response.status_code, 400)

        self.assertFalse(
            Document.objects.filter(
                title='Invalid Upload'
            ).exists()
        )

    def test_upload_requires_document_title(self):

        self.authenticate_as(self.owner)

        uploaded_file = SimpleUploadedFile(
            'no_title.txt',
            b'Valid UTF-8 document.',
            content_type='text/plain'
        )

        response = self.client.post(
            reverse('document-upload'),
            {
                'file': uploaded_file
            },
            format='multipart'
        )

        self.assertEqual(response.status_code, 400)

        self.assertFalse(
            Document.objects.filter(
                original_filename='no_title.txt'
            ).exists()
        )

    def test_anonymous_user_cannot_upload_document(self):

        uploaded_file = SimpleUploadedFile(
            'anonymous.txt',
            b'Anonymous upload attempt.',
            content_type='text/plain'
        )

        response = self.client.post(
            reverse('document-upload'),
            {
                'title': 'Anonymous Upload',
                'file': uploaded_file
            },
            format='multipart'
        )

        self.assertEqual(response.status_code, 401)

    # --------------------------------------------------------
    # DOCUMENT DOWNLOAD TESTS
    # --------------------------------------------------------

    def test_reader_can_download_document(self):

        self.authenticate_as(self.reader)

        response = self.client.get(
            reverse(
                'document-download',
                kwargs={
                    'document_id': self.document.id
                }
            )
        )

        self.assertEqual(response.status_code, 200)

        downloaded_content = b''.join(
            response.streaming_content
        )

        self.assertEqual(
            downloaded_content,
            self.original_content
        )

        self.assertEqual(
            response['X-Content-Type-Options'],
            'nosniff'
        )

        self.assertEqual(
            response['Cache-Control'],
            'private, no-store'
        )

        self.assertTrue(
            AuditEvent.objects.filter(
                document=self.document,
                actor=self.reader,
                action='DOCUMENT_DOWNLOAD'
            ).exists()
        )

    def test_revoked_user_cannot_download_document(self):

        self.authenticate_as(self.revoked_user)

        response = self.client.get(
            reverse(
                'document-download',
                kwargs={
                    'document_id': self.document.id
                }
            )
        )

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            AuditEvent.objects.filter(
                document=self.document,
                actor=self.revoked_user,
                action='ACCESS_DENIED'
            ).exists()
        )

    def test_download_detects_checksum_mismatch(self):

        self.authenticate_as(self.owner)

        self.document.checksum = '0' * 64

        self.document.save(
            update_fields=['checksum']
        )

        response = self.client.get(
            reverse(
                'document-download',
                kwargs={
                    'document_id': self.document.id
                }
            )
        )

        self.assertEqual(response.status_code, 500)

    # --------------------------------------------------------
    # DOCUMENT VERSION LIST TESTS
    # --------------------------------------------------------

    def test_reader_can_list_document_versions(self):

        self.authenticate_as(self.reader)

        response = self.client.get(
            reverse(
                'document-versions',
                kwargs={
                    'document_id': self.document.id
                }
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.data), 1)

        self.assertEqual(
            response.data[0]['version_number'],
            1
        )

    def test_revoked_user_cannot_list_document_versions(self):

        self.authenticate_as(self.revoked_user)

        response = self.client.get(
            reverse(
                'document-versions',
                kwargs={
                    'document_id': self.document.id
                }
            )
        )

        self.assertEqual(response.status_code, 404)

    # --------------------------------------------------------
    # DOCUMENT VERSION UPLOAD TESTS
    # --------------------------------------------------------

    def test_editor_can_upload_new_document_version(self):

        self.authenticate_as(self.editor)

        new_content = b'Updated Trustify document.'

        uploaded_file = SimpleUploadedFile(
            'updated_document.txt',
            new_content,
            content_type='text/plain'
        )

        response = self.client.post(
            reverse(
                'document-version-upload',
                kwargs={
                    'document_id': self.document.id
                }
            ),
            {
                'file': uploaded_file,
                'change_note': 'Updated document content'
            },
            format='multipart'
        )

        self.assertEqual(response.status_code, 201)

        self.assertTrue(
            DocumentVersion.objects.filter(
                document=self.document,
                version_number=2
            ).exists()
        )

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.original_filename,
            'updated_document.txt'
        )

        self.assertEqual(
            self.document.file_size,
            len(new_content)
        )

        self.assertTrue(
            self.test_storage.exists(
                self.document.storage_key
            )
        )

        # The previous version's file must remain available.
        self.assertTrue(
            self.test_storage.exists(
                self.version.storage_key
            )
        )

        self.assertTrue(
            AuditEvent.objects.filter(
                document=self.document,
                actor=self.editor,
                action='VERSION_CREATED'
            ).exists()
        )

    def test_reader_cannot_upload_new_document_version(self):

        self.authenticate_as(self.reader)

        uploaded_file = SimpleUploadedFile(
            'reader_update.txt',
            b'Reader must not upload versions.',
            content_type='text/plain'
        )

        response = self.client.post(
            reverse(
                'document-version-upload',
                kwargs={
                    'document_id': self.document.id
                }
            ),
            {
                'file': uploaded_file
            },
            format='multipart'
        )

        self.assertEqual(response.status_code, 403)

        self.assertEqual(
            DocumentVersion.objects.filter(
                document=self.document
            ).count(),
            1
        )

    # --------------------------------------------------------
    # PERMISSION MANAGEMENT API TESTS
    # --------------------------------------------------------

    def test_owner_can_grant_read_permission(self):

        self.authenticate_as(self.owner)

        response = self.client.post(
            reverse(
                'document-share',
                kwargs={
                    'document_id': self.document.id
                }
            ),
            {
                'username': 'api_revoked',
                'access_level': 'READ'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 201)

        self.assertTrue(
            DocumentPermission.objects.filter(
                document=self.document,
                user=self.revoked_user,
                access_level='READ',
                revoked_at__isnull=True
            ).exists()
        )

        self.assertTrue(
            AuditEvent.objects.filter(
                document=self.document,
                actor=self.owner,
                target_user=self.revoked_user,
                action='PERMISSION_GRANTED'
            ).exists()
        )

    def test_reader_cannot_grant_document_permission(self):

        self.authenticate_as(self.reader)

        response = self.client.post(
            reverse(
                'document-share',
                kwargs={
                    'document_id': self.document.id
                }
            ),
            {
                'username': 'api_revoked',
                'access_level': 'READ'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 403)

    def test_owner_can_revoke_document_permission(self):

        self.authenticate_as(self.owner)

        response = self.client.delete(
            reverse(
                'document-revoke',
                kwargs={
                    'document_id': self.document.id,
                    'permission_id': self.read_permission.id
                }
            )
        )

        self.assertEqual(response.status_code, 200)

        self.read_permission.refresh_from_db()

        self.assertIsNotNone(
            self.read_permission.revoked_at
        )

        self.assertTrue(
            AuditEvent.objects.filter(
                document=self.document,
                actor=self.owner,
                target_user=self.reader,
                action='PERMISSION_REVOKED'
            ).exists()
        )

    def test_reader_cannot_revoke_document_permission(self):

        self.authenticate_as(self.reader)

        response = self.client.delete(
            reverse(
                'document-revoke',
                kwargs={
                    'document_id': self.document.id,
                    'permission_id': self.edit_permission.id
                }
            )
        )

        self.assertEqual(response.status_code, 403)