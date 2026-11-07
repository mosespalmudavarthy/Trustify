import logging

from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from auditlog.services import record_event


logger = logging.getLogger(__name__)


class AuditedTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        username = attrs.get(self.username_field, "")

        try:
            data = super().validate(attrs)

        except (AuthenticationFailed, ValidationError):
            try:
                record_event(
                    action="LOGIN_FAILED",
                    request=self.context.get("request"),
                    description="Login attempt failed.",
                    metadata={"username": username},
                )
            except Exception:
                logger.exception("Failed to record a login failure audit event.")

            raise

        record_event(
            action="LOGIN_SUCCESS",
            request=self.context.get("request"),
            actor=self.user,
            description="User logged in successfully.",
        )

        return data