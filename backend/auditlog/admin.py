
from django.contrib import admin
from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):

    list_display = (
        'action',
        'actor',
        'document',
        'target_user',
        'created_at'
    )

    list_filter = ('action', 'created_at')

    search_fields = (
        'description',
        'actor__username',
        'document__title'
    )

    readonly_fields = (
        'actor',
        'document',
        'target_user',
        'action',
        'description',
        'ip_address',
        'user_agent',
        'metadata',
        'previous_hash',
        'event_hash',
        'created_at'
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
