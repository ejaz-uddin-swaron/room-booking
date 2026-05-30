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

        from bookings_app.models import Booking, TenantAssignment
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

        # New: tenant stats
        total_tenants = TenantAssignment.objects.filter(status='active').count()

        return Response({
            'success': True,
            'data': {
                'totalRooms': total_rooms,
                'totalBookings': total_bookings,
                'totalRevenue': float(total_revenue),
                'occupancyRate': round(occupancy_rate, 2),
                'totalActiveTenants': total_tenants,
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


# ─── Notification Views ──────────────────────────────────────────────────────


class NotificationListView(APIView):
    """List notifications for the authenticated user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from core.models import Notification
        unread_only = request.query_params.get('unread') == 'true'
        qs = Notification.objects.filter(user=request.user)
        if unread_only:
            qs = qs.filter(read=False)
        qs = qs[:50]  # Limit to last 50

        data = [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'read': n.read,
            'link': n.link,
            'createdAt': n.created_at.isoformat(),
        } for n in qs]

        unread_count = Notification.objects.filter(user=request.user, read=False).count()

        return Response({
            'success': True,
            'data': data,
            'unreadCount': unread_count,
        })


class NotificationMarkReadView(APIView):
    """Mark a notification as read."""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        from core.models import Notification
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.read = True
            notification.save(update_fields=['read'])
            return Response({'success': True})
        except Notification.DoesNotExist:
            return Response({'success': False, 'error': 'Notification not found'}, status=404)


class NotificationMarkAllReadView(APIView):
    """Mark all notifications as read for the authenticated user."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from core.models import Notification
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({'success': True, 'message': 'All notifications marked as read'})
