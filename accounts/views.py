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
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token

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

            return Response({
                'success': True,
                'message': 'Registration successful. Check your email.'
            }, status=201)

        return Response(serializer.errors, status=400)
    
class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    @swagger_auto_schema(
        operation_description="Logout a user by deleting their token.",
    )
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({'success': True, 'message': 'Logged out successfully'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'success': False, 'error': 'Token not found or already deleted', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)
        

class GetUserInfoByUsername(APIView):

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
            serializer = serializers.UserDetailSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)