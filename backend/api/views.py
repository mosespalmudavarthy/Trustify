from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    # Keep your existing health-check implementation here.

    connection.ensure_connection()

    data = {
        "message": "Welcome to Trustify!",
        "backend": "Django",
        "database": "PostgreSQL Connected",
        "status": "Success"
    }

    return Response(data)