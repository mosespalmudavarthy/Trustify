from django.contrib.auth import get_user_model
from rest_framework import serializers


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