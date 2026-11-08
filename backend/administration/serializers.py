from django.contrib.auth import get_user_model
from rest_framework import serializers

from auditlog.models import AuditEvent


User = get_user_model()


class AdministrationUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
        ]
        read_only_fields = fields


class UserStatusSerializer(serializers.Serializer):

    is_active = serializers.BooleanField(required=True)


class UserPrivilegeSerializer(serializers.Serializer):

    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "At least one privilege field must be provided."
            )

        if attrs.get("is_superuser") is True:
            attrs["is_staff"] = True

        return attrs


class AuditEventListSerializer(serializers.ModelSerializer):

    actor_username = serializers.CharField(
        source="actor.username",
        read_only=True,
        allow_null=True,
    )

    target_username = serializers.CharField(
        source="target_user.username",
        read_only=True,
        allow_null=True,
    )

    document_title = serializers.CharField(
        source="document.title",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "actor_username",
            "target_username",
            "document_title",
            "action",
            "description",
            "created_at",
        ]
        read_only_fields = fields


class AuditEventDetailSerializer(AuditEventListSerializer):

    metadata = serializers.SerializerMethodField()

    class Meta(AuditEventListSerializer.Meta):
        fields = AuditEventListSerializer.Meta.fields + [
            "ip_address",
            "user_agent",
            "metadata",
            "previous_hash",
            "event_hash",
        ]

    def get_metadata(self, obj):
        sensitive_terms = (
            "password",
            "token",
            "secret",
            "credential",
            "authorization",
        )

        def clean(value):
            if isinstance(value, dict):
                return {
                    key: clean(item)
                    for key, item in value.items()
                    if not any(
                        term in str(key).lower()
                        for term in sensitive_terms
                    )
                }

            if isinstance(value, list):
                return [clean(item) for item in value]

            return value

        return clean(obj.metadata or {})