from . import models
from . import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

# Profile management views.
# Authentication (login/register/password) is handled entirely by Supabase.

class GetUserInfoByUsername(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        if request.user.username != username and not request.user.is_staff:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(username=username)
            serializer = serializers.UserDetailSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = serializers.UserDetailSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = serializers.ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'message': 'Profile updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UploadProfileImageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'profile_image' not in request.FILES:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

        client, _ = models.Client.objects.get_or_create(
            user=request.user,
            defaults={'mobile_no': '', 'role': 'customer', 'image': ''}
        )
        client.image = request.FILES['profile_image']
        client.save()
        
        return Response({
            'success': True, 
            'message': 'Profile image uploaded successfully',
            'image_url': client.image.url
        })