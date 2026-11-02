
from .models import DocumentPermission


def is_platform_admin(user):
    """
    Only Django superusers receive global document access.
    """
    return (
        user.is_authenticated
        and user.is_superuser
    )


def is_document_owner(user, document):
    """
    Check whether the authenticated user owns the document.
    """
    return (
        user.is_authenticated
        and document.owner_id == user.pk
    )


def get_active_permission(user, document):
    """
    Retrieve the user's currently active document permission.
    """
    if not user.is_authenticated:
        return None

    return DocumentPermission.objects.filter(
        document=document,
        user=user,
        revoked_at__isnull=True
    ).first()


def can_view_document(user, document):
    """
    Determine whether the user can view a document.
    """

    if not user.is_authenticated:
        return False

    if is_platform_admin(user):
        return True

    if document.status != 'ACTIVE':
        return False

    if is_document_owner(user, document):
        return True

    permission = get_active_permission(user, document)

    return permission is not None and permission.access_level in [
        'READ',
        'EDIT'
    ]


def can_edit_document(user, document):
    """
    Determine whether the user can modify a document.
    """

    if not user.is_authenticated:
        return False

    if is_platform_admin(user):
        return True

    if document.status != 'ACTIVE':
        return False

    if is_document_owner(user, document):
        return True

    permission = get_active_permission(user, document)

    return (
        permission is not None
        and permission.access_level == 'EDIT'
    )


def can_manage_permissions(user, document):
    """
    Only the document owner or platform superuser
    can manage document permissions.
    """

    return (
        is_document_owner(user, document)
        or is_platform_admin(user)
    )
