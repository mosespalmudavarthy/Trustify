from django.urls import path

from .views import (
    DocumentListView,
    DocumentDetailView,
    DocumentUpdateView,
    GrantDocumentPermissionView,
    DocumentPermissionListView,
    RevokeDocumentPermissionView,
    DocumentUploadView,
    DocumentDownloadView,
    DocumentVersionListView,
    DocumentVersionUploadView,
)


urlpatterns = [
    path(
        '',
        DocumentListView.as_view(),
        name='document-list',
    ),

    path(
        'upload/',
        DocumentUploadView.as_view(),
        name='document-upload',
    ),

    path(
        '<int:document_id>/',
        DocumentDetailView.as_view(),
        name='document-detail',
    ),

    path(
        '<int:document_id>/update/',
        DocumentUpdateView.as_view(),
        name='document-update',
    ),

    path(
        '<int:document_id>/permissions/',
        DocumentPermissionListView.as_view(),
        name='document-permissions',
    ),

    path(
        '<int:document_id>/share/',
        GrantDocumentPermissionView.as_view(),
        name='document-share',
    ),

    path(
        '<int:document_id>/permissions/<int:permission_id>/revoke/',
        RevokeDocumentPermissionView.as_view(),
        name='document-revoke',
    ),

    path(
        '<int:document_id>/download/',
        DocumentDownloadView.as_view(),
        name='document-download',
    ),

    path(
        '<int:document_id>/versions/',
        DocumentVersionListView.as_view(),
        name='document-versions',
    ),

    path(
        '<int:document_id>/versions/upload/',
        DocumentVersionUploadView.as_view(),
        name='document-version-upload',
    ),
]