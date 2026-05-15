from . import models
from . import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework import status
from rooms.permissions import IsAdmin

# Profile management views.
# Authentication (login/register/password) is handled entirely by Supabase.
# All endpoints are admin-only.


class ProfileView(APIView):
    """Admin-only profile view/update."""
    permission_classes = [IsAdmin]

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
    """Admin-only profile image upload."""
    permission_classes = [IsAdmin]

    def post(self, request):
        if 'profile_image' not in request.FILES:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

        from core.storage_backends import supabase_storage

        profile_image = request.FILES['profile_image']

        try:
            image_url = supabase_storage.upload_image(
                profile_image,
                bucket_name='images',
                folder='profiles'
            )

            client, _ = models.Client.objects.get_or_create(
                user=request.user,
                defaults={'mobile_no': '', 'role': 'admin', 'image': ''}
            )
            client.image = image_url
            client.save()

            return Response({
                'success': True,
                'message': 'Profile image uploaded successfully',
                'image_url': image_url
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)