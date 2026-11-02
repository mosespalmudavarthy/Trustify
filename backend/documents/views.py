
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
