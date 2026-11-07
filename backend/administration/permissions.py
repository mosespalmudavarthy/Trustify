from rest_framework.permissions import BasePermission


class IsActiveSuperuser(BasePermission):
    """
    Allow access only to authenticated, active superuser accounts.
    """

    message = "Only active superusers can access administration features."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.is_superuser
        )
