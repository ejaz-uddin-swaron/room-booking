from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import os

from rooms.models import Room


class UploadImagesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        files = request.FILES.getlist('images')
        if not files:
            return Response({
                'success': False,
                'error': 'No files uploaded',
                'status': 400
            }, status=status.HTTP_400_BAD_REQUEST)

        allowed = {ext.lower() for ext in settings.ALLOWED_FILE_TYPES}
        max_size = int(getattr(settings, 'MAX_FILE_SIZE', 5 * 1024 * 1024))

        saved_urls = []
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        for f in files:
            ext = os.path.splitext(f.name)[1].lower().lstrip('.')
            if ext not in allowed:
                return Response({'success': False, 'error': f'Unsupported file type: .{ext}', 'status': 422}, status=422)
            if f.size > max_size:
                return Response({'success': False, 'error': f'File too large: {f.name}', 'status': 413}, status=413)

            filename = get_random_string(16) + '.' + ext
            path = os.path.join('uploads', filename)
            full_path = os.path.join(settings.MEDIA_ROOT, filename if path.startswith(settings.MEDIA_ROOT) else path)
            default_storage.save(full_path, ContentFile(f.read()))
            url = request.build_absolute_uri(os.path.join(settings.MEDIA_URL, path))
            saved_urls.append(url)

        return Response({'success': True, 'data': {'urls': saved_urls}})


class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # simple role check
        user = request.user
        is_admin = getattr(getattr(user, 'client', None), 'role', None) == 'admin' or user.is_staff
        if not is_admin:
            return Response({'success': False, 'error': 'Forbidden', 'status': 403}, status=403)

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
