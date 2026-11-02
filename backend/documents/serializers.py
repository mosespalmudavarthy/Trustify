
from rest_framework import serializers
from .models import Document, DocumentPermission


class DocumentSerializer(serializers.ModelSerializer):

    owner_username = serializers.CharField(
        source='owner.username',
        read_only=True
    )

    category_name = serializers.CharField(
        source='category.name',
        read_only=True
    )

    class Meta:
        model = Document

        fields = [
            'id',
            'title',
            'description',
            'owner',
            'owner_username',
            'category',
            'category_name',
            'original_filename',
            'mime_type',
            'file_size',
            'status',
            'created_at',
            'updated_at'
        ]

        read_only_fields = fields


class DocumentPermissionSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = DocumentPermission

        fields = [
            'id',
            'user',
            'username',
            'access_level',
            'granted_by',
            'granted_at',
            'revoked_at'
        ]

        read_only_fields = fields

class DocumentUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document

        fields = [
            'title',
            'description',
            'category'
        ]
