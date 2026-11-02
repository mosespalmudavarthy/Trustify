
from django.urls import path

from .views import (
    DocumentListView,
    DocumentDetailView,
    DocumentUpdateView,
    GrantDocumentPermissionView,
    DocumentPermissionListView,
    RevokeDocumentPermissionView
)


urlpatterns = [

    path(
        '',
        DocumentListView.as_view(),
        name='document-list'
    ),

    path(
        '<int:document_id>/',
        DocumentDetailView.as_view(),
        name='document-detail'
    ),

    path(
        '<int:document_id>/update/',
        DocumentUpdateView.as_view(),
        name='document-update'
    ),

    path(
        '<int:document_id>/permissions/',
        DocumentPermissionListView.as_view(),
        name='document-permissions'
    ),

    path(
        '<int:document_id>/share/',
        GrantDocumentPermissionView.as_view(),
        name='document-share'
    ),

    path(
        '<int:document_id>/permissions/<int:permission_id>/revoke/',
        RevokeDocumentPermissionView.as_view(),
        name='document-revoke'
    ),

]
