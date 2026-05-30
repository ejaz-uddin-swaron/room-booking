from . import models
from . import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework import status
from rooms.permissions import IsAdmin, IsAdminOrTenant

# Profile management views.
# Authentication (login/register/password) is handled entirely by Supabase.


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


class TenantProfileView(APIView):
    """Tenant self-profile view/update."""
    permission_classes = [IsAdminOrTenant]

    def get(self, request):
        serializer = serializers.UserDetailSerializer(request.user)
        return Response({'success': True, 'data': serializer.data})

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


class ManageUserRoleView(APIView):
    """
    Admin-only: Change a user's role.
    POST body: { "user_id": <django_user_id>, "role": "tenant" | "customer" | "admin" }
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        user_id = request.data.get('user_id')
        new_role = request.data.get('role')

        if not user_id or not new_role:
            return Response({'success': False, 'error': 'user_id and role are required'}, status=400)

        if new_role not in ('customer', 'tenant', 'admin'):
            return Response({'success': False, 'error': 'Invalid role. Must be customer, tenant, or admin.'}, status=400)

        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'success': False, 'error': 'User not found'}, status=404)

        client, _ = models.Client.objects.get_or_create(
            user=target_user,
            defaults={'mobile_no': '', 'role': 'customer', 'image': ''}
        )
        client.role = new_role
        client.save(update_fields=['role'])

        return Response({
            'success': True,
            'data': {
                'userId': target_user.id,
                'username': target_user.username,
                'email': target_user.email,
                'role': new_role,
            }
        })


class ListUsersView(APIView):
    """Admin-only: List all users with their roles."""
    permission_classes = [IsAdmin]

    def get(self, request):
        role_filter = request.query_params.get('role')
        users = User.objects.select_related('client').all()
        if role_filter:
            users = users.filter(client__role=role_filter)

        data = []
        for u in users:
            client = getattr(u, 'client', None)
            data.append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'firstName': u.first_name,
                'lastName': u.last_name,
                'role': getattr(client, 'role', 'customer') if client else 'customer',
                'phone': getattr(client, 'mobile_no', '') if client else '',
            })

        return Response({'success': True, 'data': data})