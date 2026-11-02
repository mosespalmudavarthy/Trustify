
from django.contrib import admin
from .models import (
    Category,
    Document,
    DocumentPermission,
    DocumentVersion
)


admin.site.register(Category)
admin.site.register(Document)
admin.site.register(DocumentPermission)
admin.site.register(DocumentVersion)
