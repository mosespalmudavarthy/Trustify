import hashlib

from django.http import FileResponse

from pathlib import Path

from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404

from rest_framework.parsers import MultiPartParser, FormParser

from .models import Category, Document, DocumentVersion

from .access import can_edit_document, can_view_document


from .storage import (
    validate_file,
    calculate_checksum,
    save_private_file,
    delete_private_file,
    private_storage
)


from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .access import can_edit_document
from .serializers import DocumentUpdateSerializer
from .models import Document, DocumentPermission
from .serializers import (
    DocumentSerializer,
    DocumentPermissionSerializer
)

from .access import (
    is_platform_admin,
    can_view_document,
    can_manage_permissions
)

from auditlog.models import AuditEvent


class DocumentListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        if is_platform_admin(request.user):

            documents = Document.objects.all()

        else:

            documents = Document.objects.filter(
                Q(owner=request.user) |
                Q(
                    permissions__user=request.user,
                    permissions__revoked_at__isnull=True
                )
            )

        documents = (
            documents
            .filter(status='ACTIVE')
            .select_related('owner', 'category')
            .distinct()
            .order_by('-created_at')
        )

        serializer = DocumentSerializer(
            documents,
            many=True
        )

        return Response(serializer.data)


class DocumentDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):

        document = get_object_or_404(
            Document,
            pk=document_id
        )

        if not can_view_document(request.user, document):

            AuditEvent.objects.create(
                actor=request.user,
                document=document,
                action='ACCESS_DENIED',
                description='Unauthorized document access attempt.'
            )

            return Response(
                {'error': 'You do not have permission to access this document.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = DocumentSerializer(document)

        return Response(serializer.data)


class GrantDocumentPermissionView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):

        document = get_object_or_404(
            Document,
            pk=document_id
        )

        if not can_manage_permissions(request.user, document):

            return Response(
                {'error': 'Only the document owner or authorized administrator can share this document.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if document.status != 'ACTIVE':

            return Response(
                {'error': 'Permissions cannot be granted for inactive documents.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        username = request.data.get('username')
        access_level = request.data.get('access_level')

        if access_level not in ['READ', 'EDIT']:

            return Response(
                {'error': 'Access level must be READ or EDIT.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not username:

            return Response(
                {'error': 'Username is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        target_user = User.objects.filter(
            username=username
        ).first()

        if not target_user:

            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if target_user.pk == document.owner_id:

            return Response(
                {'error': 'The document owner already has full access.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not target_user.is_active:

            return Response(
                {'error': 'Cannot share documents with inactive users.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():

            existing = DocumentPermission.objects.filter(
                document=document,
                user=target_user,
                revoked_at__isnull=True
            ).first()

            if existing:

                existing.access_level = access_level
                existing.granted_by = request.user
                existing.save(
                    update_fields=['access_level', 'granted_by']
                )

                permission = existing

            else:

                permission = DocumentPermission.objects.create(
                    document=document,
                    user=target_user,
                    access_level=access_level,
                    granted_by=request.user
                )

            AuditEvent.objects.create(
                actor=request.user,
                document=document,
                target_user=target_user,
                action='PERMISSION_GRANTED',
                description=f'{access_level} permission granted.'
            )

        serializer = DocumentPermissionSerializer(permission)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class DocumentPermissionListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):

        document = get_object_or_404(
            Document,
            pk=document_id
        )

        if not can_manage_permissions(request.user, document):

            return Response(
                {'error': 'Permission management access denied.'},
                status=status.HTTP_403_FORBIDDEN
            )

        permissions = DocumentPermission.objects.filter(
            document=document,
            revoked_at__isnull=True
        ).select_related('user', 'granted_by')

        serializer = DocumentPermissionSerializer(
            permissions,
            many=True
        )

        return Response(serializer.data)


class RevokeDocumentPermissionView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, document_id, permission_id):

        document = get_object_or_404(
            Document,
            pk=document_id
        )

        if not can_manage_permissions(request.user, document):

            return Response(
                {'error': 'Permission management access denied.'},
                status=status.HTTP_403_FORBIDDEN
            )

        with transaction.atomic():

            permission = get_object_or_404(
                DocumentPermission.objects.select_for_update(),
                pk=permission_id,
                document=document,
                revoked_at__isnull=True
            )

            permission.revoked_at = timezone.now()
            permission.save(update_fields=['revoked_at'])

            AuditEvent.objects.create(
                actor=request.user,
                document=document,
                target_user=permission.user,
                action='PERMISSION_REVOKED',
                description='Document permission revoked.'
            )

        return Response(
            {'message': 'Document permission revoked successfully.'},
            status=status.HTTP_200_OK
        )




class DocumentUpdateView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, document_id):

        document = get_object_or_404(
            Document,
            pk=document_id
        )

        if not can_edit_document(request.user, document):

            return Response(
                {'error': 'You do not have permission to edit this document.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = DocumentUpdateSerializer(
            document,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            AuditEvent.objects.create(
                actor=request.user,
                document=document,
                action='DOCUMENT_UPDATE',
                description='Document metadata updated.'
            )

            return Response(
                DocumentSerializer(document).data
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class DocumentUploadView(APIView):

    permission_classes = [IsAuthenticated]

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):

        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            return Response(
                {'error': 'A document file is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mime_type = validate_file(uploaded_file)
            checksum = calculate_checksum(uploaded_file)

        except ValueError as error:
            return Response(
                {'error': str(error)},
                status=status.HTTP_400_BAD_REQUEST
            )

        title = request.data.get('title', '').strip()

        if not title:
            return Response(
                {'error': 'Document title is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        category = None

        category_id = request.data.get('category')

        if category_id:
            category = get_object_or_404(
                Category,
                pk=category_id,
                is_active=True
            )

        storage_key = None

        try:

            storage_key = save_private_file(uploaded_file)

            with transaction.atomic():

                document = Document.objects.create(
                    title=title,
                    description=request.data.get('description', ''),
                    owner=request.user,
                    category=category,
                    original_filename=Path(
                        uploaded_file.name
                    ).name,
                    storage_key=storage_key,
                    mime_type=mime_type,
                    file_size=uploaded_file.size,
                    checksum=checksum
                )

                DocumentVersion.objects.create(
                    document=document,
                    version_number=1,
                    storage_key=storage_key,
                    original_filename=document.original_filename,
                    mime_type=mime_type,
                    file_size=uploaded_file.size,
                    checksum=checksum,
                    uploaded_by=request.user,
                    change_note='Initial document upload'
                )

                AuditEvent.objects.create(
                    actor=request.user,
                    document=document,
                    action='DOCUMENT_UPLOAD',
                    description='Document uploaded successfully.',
                    metadata={
                        'version': 1,
                        'file_size': uploaded_file.size,
                        'checksum': checksum
                    }
                )

            return Response(
                {
                    'message': 'Document uploaded successfully.',
                    'document': DocumentSerializer(
                        document
                    ).data,
                    'version': 1
                },
                status=status.HTTP_201_CREATED
            )

        except Exception:

            if storage_key:
                delete_private_file(storage_key)

            raise

class DocumentDownloadView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):

        document = get_object_or_404(
            Document,
            pk=document_id
        )

        # Verify current document authorization.
        if not can_view_document(request.user, document):

            AuditEvent.objects.create(
                actor=request.user,
                document=document,
                action='ACCESS_DENIED',
                description='Unauthorized document download attempt.'
            )

            return Response(
                {'error': 'Document not found or access denied.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify the file exists in private storage.
        if not private_storage.exists(document.storage_key):

            return Response(
                {'error': 'Document file is unavailable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        file_handle = private_storage.open(
            document.storage_key,
            'rb'
        )

        # Verify file integrity before returning it.
        sha256 = hashlib.sha256()

        for chunk in file_handle.chunks():
            sha256.update(chunk)

        calculated_checksum = sha256.hexdigest()

        file_handle.seek(0)

        if calculated_checksum != document.checksum:

            file_handle.close()

            return Response(
                {'error': 'Document integrity verification failed.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Record successful download.
        AuditEvent.objects.create(
            actor=request.user,
            document=document,
            action='DOCUMENT_DOWNLOAD',
            description='Document downloaded successfully.',
            metadata={
                'checksum_verified': True,
                'file_size': document.file_size
            }
        )

        # Always download as an attachment.
        response = FileResponse(
            file_handle,
            as_attachment=True,
            filename=document.original_filename,
            content_type='application/octet-stream'
        )

        response['X-Content-Type-Options'] = 'nosniff'
        response['Cache-Control'] = 'private, no-store'

        return response

class DocumentVersionListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):

        document = get_object_or_404(
            Document,
            pk=document_id
        )

        if not can_view_document(request.user, document):

            return Response(
                {'error': 'Document not found or access denied.'},
                status=status.HTTP_404_NOT_FOUND
            )

        versions = DocumentVersion.objects.filter(
            document=document
        ).select_related(
            'uploaded_by'
        ).order_by(
            '-version_number'
        )

        data = []

        for version in versions:

            data.append({
                'id': version.id,
                'version_number': version.version_number,
                'filename': version.original_filename,
                'mime_type': version.mime_type,
                'file_size': version.file_size,
                'checksum': version.checksum,
                'uploaded_by': version.uploaded_by.username,
                'change_note': version.change_note,
                'created_at': version.created_at
            })

        return Response(data)
class DocumentVersionUploadView(APIView):

    permission_classes = [IsAuthenticated]

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, document_id):

        document = get_object_or_404(
            Document,
            pk=document_id
        )

        # Only owners, administrators, and users with EDIT
        # permission can upload a new version.
        if not can_edit_document(request.user, document):

            AuditEvent.objects.create(
                actor=request.user,
                document=document,
                action='ACCESS_DENIED',
                description='Unauthorized document version upload attempt.'
            )

            return Response(
                {'error': 'You do not have permission to upload a new version.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if document.status != 'ACTIVE':

            return Response(
                {'error': 'New versions cannot be uploaded to inactive documents.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES.get('file')

        if not uploaded_file:

            return Response(
                {'error': 'A document file is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mime_type = validate_file(uploaded_file)
            checksum = calculate_checksum(uploaded_file)

        except ValueError as error:

            return Response(
                {'error': str(error)},
                status=status.HTTP_400_BAD_REQUEST
            )

        storage_key = None

        try:

            # Save the new file in private storage.
            storage_key = save_private_file(uploaded_file)

            with transaction.atomic():

                # Lock the document while assigning the next version.
                locked_document = Document.objects.select_for_update().get(
                    pk=document_id
                )

                # Recheck authorization after obtaining the lock.
                if not can_edit_document(request.user, locked_document):

                    raise PermissionError(
                        'Document editing permission is no longer available.'
                    )

                if locked_document.status != 'ACTIVE':

                    raise ValueError(
                        'The document is no longer active.'
                    )

                latest_version = (
                    DocumentVersion.objects
                    .filter(document=locked_document)
                    .aggregate(max_version=Max('version_number'))
                    ['max_version']
                    or 0
                )

                new_version_number = latest_version + 1

                original_filename = Path(
                    uploaded_file.name
                ).name[:255]

                version = DocumentVersion.objects.create(
                    document=locked_document,
                    version_number=new_version_number,
                    storage_key=storage_key,
                    original_filename=original_filename,
                    mime_type=mime_type,
                    file_size=uploaded_file.size,
                    checksum=checksum,
                    uploaded_by=request.user,
                    change_note=request.data.get('change_note', '')
                )

                # The document record represents its latest version.
                locked_document.storage_key = storage_key
                locked_document.original_filename = original_filename
                locked_document.mime_type = mime_type
                locked_document.file_size = uploaded_file.size
                locked_document.checksum = checksum

                locked_document.save(
                    update_fields=[
                        'storage_key',
                        'original_filename',
                        'mime_type',
                        'file_size',
                        'checksum',
                        'updated_at'
                    ]
                )

                AuditEvent.objects.create(
                    actor=request.user,
                    document=locked_document,
                    action='VERSION_CREATED',
                    description='New document version uploaded successfully.',
                    metadata={
                        'version': new_version_number,
                        'file_size': uploaded_file.size,
                        'checksum': checksum
                    }
                )

            return Response(
                {
                    'message': 'New document version uploaded successfully.',
                    'version': {
                        'id': version.id,
                        'version_number': version.version_number,
                        'filename': version.original_filename,
                        'mime_type': version.mime_type,
                        'file_size': version.file_size,
                        'checksum': version.checksum,
                        'change_note': version.change_note,
                        'created_at': version.created_at
                    }
                },
                status=status.HTTP_201_CREATED
            )

        except PermissionError as error:

            if storage_key:
                delete_private_file(storage_key)

            return Response(
                {'error': str(error)},
                status=status.HTTP_403_FORBIDDEN
            )

        except ValueError as error:

            if storage_key:
                delete_private_file(storage_key)

            return Response(
                {'error': str(error)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:

            if storage_key:
                delete_private_file(storage_key)

            raise