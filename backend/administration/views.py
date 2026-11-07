from django.db.models import Q

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError

from auditlog.services import record_event
from .serializers import UserStatusSerializer

from django.shortcuts import get_object_or_404

from rest_framework.pagination import PageNumberPagination

from .serializers import (
    AdministrationUserSerializer,
    UserStatusSerializer,
    UserPrivilegeSerializer,
)

from django.http import Http404

from django.contrib.auth import get_user_model
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from auditlog.models import AuditEvent
from documents.models import Document, DocumentVersion

from .permissions import IsActiveSuperuser


User = get_user_model()


class AdministrationDashboardView(APIView):

    permission_classes = [IsActiveSuperuser]

    def get(self, request):

        # User statistics
        user_stats = {
            "total": User.objects.count(),
            "active": User.objects.filter(is_active=True).count(),
            "inactive": User.objects.filter(is_active=False).count(),
            "staff": User.objects.filter(is_staff=True).count(),
            "superusers": User.objects.filter(is_superuser=True).count(),
        }

        # Document statistics
        document_stats = {
            "total": Document.objects.count(),
            "active": Document.objects.filter(status="ACTIVE").count(),
            "archived": Document.objects.filter(status="ARCHIVED").count(),
            "deleted": Document.objects.filter(status="DELETED").count(),
        }

        # Version statistics
        version_stats = {
            "total": DocumentVersion.objects.count(),
        }

        # Storage statistics
        document_storage = (
            Document.objects.exclude(status="DELETED")
            .aggregate(total=Sum("file_size"))["total"] or 0
        )

        version_storage = (
            DocumentVersion.objects
            .filter(document__status__in=["ACTIVE", "ARCHIVED"])
            .aggregate(total=Sum("file_size"))["total"] or 0
        )

        storage_stats = {
            "document_bytes": document_storage,
            "version_bytes": version_storage,
            "total_bytes": document_storage + version_storage,
        }

        # Audit statistics
        audit_stats = {
            "total_events": AuditEvent.objects.count(),
        }

        recent_security_events = list(
            AuditEvent.objects.filter(
                action__in=["LOGIN_FAILED", "ACCESS_DENIED"]
            )
            .select_related("actor", "target_user")
            .order_by("-created_at")
            .values(
                "id",
                "action",
                "description",
                "actor__username",
                "target_user__username",
                "ip_address",
                "created_at",
            )[:10]
        )

        return Response({
            "users": user_stats,
            "documents": document_stats,
            "versions": version_stats,
            "storage": storage_stats,
            "audit": audit_stats,
            "recent_security_events": recent_security_events,
        })

class AdministrationUserPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class AdministrationUserListView(APIView):

    permission_classes = [IsActiveSuperuser]

    def get(self, request):

        users = User.objects.all().order_by("id")

        search = request.query_params.get("search", "").strip()

        if search:
            users = users.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        paginator = AdministrationUserPagination()
        page = paginator.paginate_queryset(users, request)

        serializer = AdministrationUserSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(serializer.data)

class AdministrationUserDetailView(APIView):

    permission_classes = [IsActiveSuperuser]

    def get(self, request, user_id):

        user = get_object_or_404(
            User,
            pk=user_id,
        )

        serializer = AdministrationUserSerializer(user)

        return Response(serializer.data)

class AdministrationUserStatusView(APIView):

    permission_classes = [IsActiveSuperuser]

    def patch(self, request, user_id):

        serializer = UserStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["is_active"]

        with transaction.atomic():

            locked_users = list(
                User.objects.select_for_update().order_by("pk")
            )

            users_by_id = {
                user.pk: user for user in locked_users
            }

            target_user = users_by_id.get(user_id)

            if target_user is None:
                raise Http404("User not found.")

            if target_user.pk == request.user.pk and not new_status:
                raise ValidationError(
                    "You cannot deactivate your own account."
                )

            if target_user.is_active == new_status:
                raise ValidationError(
                    "The account already has the requested status."
                )

            if target_user.is_superuser and not new_status:
                active_superusers = sum(
                    1
                    for user in locked_users
                    if user.is_active and user.is_superuser
                )

                if active_superusers <= 1:
                    raise ValidationError(
                        "Cannot deactivate the last active superuser."
                    )

            target_user.is_active = new_status
            target_user.save(update_fields=["is_active"])

            action = (
                "USER_ACTIVATED"
                if new_status
                else "USER_DEACTIVATED"
            )

            record_event(
                action=action,
                request=request,
                actor=request.user,
                target_user=target_user,
                description=(
                    "Administrator activated a user account."
                    if new_status
                    else "Administrator deactivated a user account."
                ),
                metadata={
                    "is_active": new_status,
                },
            )

        return Response({
            "message": "User account status updated successfully.",
            "user": AdministrationUserSerializer(target_user).data,
        }, status=status.HTTP_200_OK)

class AdministrationUserPrivilegesView(APIView):

    permission_classes = [IsActiveSuperuser]

    def patch(self, request, user_id):

        serializer = UserPrivilegeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        changes = serializer.validated_data

        with transaction.atomic():

            locked_users = list(
                User.objects.select_for_update().order_by("pk")
            )

            users_by_id = {
                user.pk: user for user in locked_users
            }

            target_user = users_by_id.get(user_id)

            if target_user is None:
                raise Http404("User not found.")
            new_is_staff = changes.get(
                "is_staff",
                target_user.is_staff,
            )
            new_is_superuser = changes.get(
                "is_superuser",
                target_user.is_superuser,
            )

            if new_is_superuser:
                new_is_staff = True

            elif (
                target_user.is_superuser
                and "is_superuser" in changes
                and not new_is_superuser
                and "is_staff" not in changes
            ):
                new_is_staff = False
            if target_user.pk == request.user.pk:
                if not new_is_superuser:
                    raise ValidationError(
                        "You cannot remove your own superuser privileges."
                    )

            if (
                target_user.is_superuser
                and not new_is_superuser
                and target_user.is_active
            ):
                active_superusers = sum(
                    1
                    for user in locked_users
                    if user.is_active and user.is_superuser
                )

                if active_superusers <= 1:
                    raise ValidationError(
                        "Cannot demote the last active superuser."
                    )

            staff_changed = target_user.is_staff != new_is_staff
            superuser_changed = (
                target_user.is_superuser != new_is_superuser
            )

            if not staff_changed and not superuser_changed:
                raise ValidationError(
                    "The account already has the requested privileges."
                )

            target_user.is_staff = new_is_staff
            target_user.is_superuser = new_is_superuser

            target_user.save(
                update_fields=["is_staff", "is_superuser"]
            )

            if staff_changed:
                record_event(
                    action="STAFF_PRIVILEGE_CHANGED",
                    request=request,
                    actor=request.user,
                    target_user=target_user,
                    description="Administrator changed staff privileges.",
                    metadata={
                        "is_staff": new_is_staff,
                    },
                )

            if superuser_changed:
                record_event(
                    action="SUPERUSER_PRIVILEGE_CHANGED",
                    request=request,
                    actor=request.user,
                    target_user=target_user,
                    description="Administrator changed superuser privileges.",
                    metadata={
                        "is_superuser": new_is_superuser,
                    },
                )

        return Response({
            "message": "User privileges updated successfully.",
            "user": AdministrationUserSerializer(target_user).data,
        }, status=status.HTTP_200_OK)