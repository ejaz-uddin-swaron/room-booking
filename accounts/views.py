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
from rest_framework import status
import environ
from drf_yasg import openapi
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

# Create your views here.

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = serializers.CustomTokenObtainPairSerializer

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

            return Response({
                'success': True,
                'message': 'Registration successful. Check your email.'
            }, status=201)

        return Response(serializer.errors, status=400)
    
class UserLogoutView(APIView):
    """Logout user by blacklisting their refresh token"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_description="Logout a user by blacklisting their refresh token.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token')
            },
            required=['refresh']
        )
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {'success': False, 'error': 'Refresh token is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'success': True, 'message': 'Logged out successfully'}, 
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        

class GetUserInfoByUsername(APIView):

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
            serializer = serializers.UserDetailSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        serializer = serializers.UserDetailSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = serializers.ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'message': 'Profile updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = serializers.ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['current_password']):
                return Response({'error': 'Incorrect current password'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'success': True, 'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UploadProfileImageView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        if 'profile_image' not in request.FILES:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        client = request.user.client
        client.image = request.FILES['profile_image']
        client.save()
        
        return Response({
            'success': True, 
            'message': 'Profile image uploaded successfully',
            'image_url': client.image.url
        })