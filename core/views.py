from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from rooms.models import Room
from rooms.permissions import IsAdmin
from core.storage_backends import supabase_storage


class UploadImagesView(APIView):
    """Admin-only image upload to Supabase Storage."""
    permission_classes = [IsAdmin]

    def post(self, request):
        files = request.FILES.getlist('images')
        if not files:
            return Response({
                'success': False,
                'error': 'No files uploaded',
                'status': 400
            }, status=status.HTTP_400_BAD_REQUEST)

        saved_urls = []

        for f in files:
            try:
                url = supabase_storage.upload_image(f, bucket_name='images', folder='uploads')
                saved_urls.append(url)
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e),
                    'status': 500
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'success': True, 'data': {'urls': saved_urls}})


class AdminStatsView(APIView):
    """Admin-only dashboard statistics."""
    permission_classes = [IsAdmin]

    def get(self, request):
        total_rooms = Room.objects.count()

        from bookings_app.models import Booking
        from django.db.models import Sum

        total_bookings = Booking.objects.count()
        total_revenue = Booking.objects.filter(status__in=['confirmed', 'completed']).aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        # Calculate occupancy (very simple version: booked rooms / total rooms)
        occupied_rooms = Booking.objects.filter(
            status__in=['pending', 'confirmed'],
            check_in__lte=timezone.now().date(),
            check_out__gte=timezone.now().date()
        ).values('room').distinct().count()
        
        occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0

        return Response({
            'success': True,
            'data': {
                'totalRooms': total_rooms,
                'totalBookings': total_bookings,
                'totalRevenue': float(total_revenue),
                'occupancyRate': round(occupancy_rate, 2),
            }
        })


class VerifyTokenView(APIView):
    """
    Auth plumbing — returns the authenticated user's identity and role.
    Must remain IsAuthenticated (not IsAdmin) so the frontend login flow
    can determine whether the user is an admin before granting access.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        client = getattr(user, 'client', None)
        return Response({
            'success': True,
            'data': {
                'valid': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': getattr(client, 'role', 'customer') if client else 'customer',
                }
            }
        })


class MeView(APIView):
    """
    Auth plumbing — returns the current user profile including role.
    Must remain IsAuthenticated (not IsAdmin) so the frontend login flow
    can determine whether the user is an admin before granting access.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        client = getattr(user, 'client', None)
        return Response({
            'success': True,
            'data': {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': getattr(client, 'role', 'customer') if client else 'customer',
                }
            }
        })
