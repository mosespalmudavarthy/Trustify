
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():

            user = serializer.save()

            return Response(
                {
                    'message': 'Account created successfully.',
                    'user': UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(TokenObtainPairView):

    permission_classes = [AllowAny]


class ProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserSerializer(request.user)

        return Response(serializer.data)


class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        refresh_token = request.data.get('refresh')

        if not refresh_token:

            return Response(
                {'error': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            token = RefreshToken(refresh_token)

            if str(token['user_id']) != str(request.user.pk):
                return Response(
                    {'error': 'Invalid refresh token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token.blacklist()

            return Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_205_RESET_CONTENT
            )

        except TokenError:

            return Response(
                {'error': 'Invalid or expired refresh token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
