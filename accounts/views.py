from rest_framework import viewsets
from . import models
from . import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
import environ
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from drf_yasg import openapi

# Create your views here.

class ClientViewset(viewsets.ModelViewSet):
    queryset = models.Client.objects.all()
    serializer_class = serializers.ClientSerializer

class UserRegistrationApiView(APIView):
    serializer_class = serializers.RegistratonSerializer

    @swagger_auto_schema(request_body=serializers.RegistratonSerializer)
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            user.is_active = True
            user.save()

            email_subject = 'Welcome to Our Platform!'
            email_body = render_to_string('confirm_email.html', {
                'username': user.username,
                # Add more context if needed
            })
            email = EmailMultiAlternatives(email_subject, '', to=[user.email])
            email.attach_alternative(email_body, 'text/html')
            email.send()

            # Optional: issue JWT tokens immediately
            refresh = RefreshToken.for_user(user)

            return Response({
                'success': True,
                'data': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': 'Registration successful. Check your email.'
            }, status=201)

        return Response(serializer.errors, status=400)
    
class CustomUserLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_description="JWT login and return token with extra user info",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
            }
        ),
        responses={200: openapi.Response(
            description='Login successful',
            examples={
                "application/json": {
                    "refresh": "<refresh_token>",
                    "access": "<access_token>",
                    "user_id": 1,
                    "username": "exampleuser",
                    "phone": "01234567890",
                    "role": "client"
                }
            }
        )}
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200 and isinstance(response.data, dict):
            # Wrap into { success, data }
            data = response.data.copy()
            token = data.pop('access', None)
            refresh = data.pop('refresh', None)
            user_payload = {
                'id': data.pop('user_id', None),
                'username': data.pop('username', None),
                'role': data.pop('role', None)
            }
            wrapped = {
                'success': True,
                'data': {
                    'token': token,
                    'refresh': refresh,
                    'user': user_payload,
                }
            }
            response.data = wrapped
        return response
    
class UserLogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Logout a user by blacklisting the refresh token.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['refresh']
        ),
        security=[{'Bearer': []}]
    )

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist() 

            return Response({'success': True, 'message': 'Logged out successfully'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'success': False, 'error': 'Invalid token or already blacklisted', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)
        

class GetUserInfoByUsername(APIView):

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
            serializer = serializers.UserDetailSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)