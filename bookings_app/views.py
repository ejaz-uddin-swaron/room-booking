from datetime import datetime
from django.utils import timezone
from django.db.models import Sum, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from rooms.models import Room
from .models import Booking


def _is_admin(user):
    return (hasattr(user, 'client') and getattr(user.client, 'role', None) == 'admin') or user.is_staff


class BookingsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = []  # allow public create

    def get(self, request):
        if not (request.user and request.user.is_authenticated and _is_admin(request.user)):
            return Response({'success': False, 'error': 'Forbidden', 'status': 403}, status=403)

        qs = Booking.objects.select_related('room').all()
        data = []
        for b in qs:
            data.append({
                'id': b.id,
                'roomId': str(b.room.id),
                'checkIn': b.check_in.isoformat(),
                'checkOut': b.check_out.isoformat(),
                'guests': b.guests,
                'totalPrice': float(b.total_price),
                'status': b.status,
                'guestInfo': b.guest_info,
                'createdAt': b.created_at.isoformat(),
                'updatedAt': b.updated_at.isoformat(),
                'room': {
                    'id': str(b.room.id),
                    'name': b.room.name,
                    'location': b.room.location,
                }
            })
        return Response({'success': True, 'data': data})

    def post(self, request):
        # Accept camelCase fields
        payload = request.data
        room_id = payload.get('roomId') or payload.get('room_id')
        check_in = payload.get('checkIn') or payload.get('check_in')
        check_out = payload.get('checkOut') or payload.get('check_out')
        guests = payload.get('guests')
        guest_info = payload.get('guestInfo') or payload.get('guest_info') or {}

        if not all([room_id, check_in, check_out, guests]):
            return Response({'success': False, 'error': 'Validation failed', 'status': 422, 'details': 'Missing required fields'}, status=422)

        # Parse dates
        try:
            if isinstance(check_in, str):
                check_in_dt = datetime.fromisoformat(check_in).date()
            else:
                check_in_dt = check_in
            if isinstance(check_out, str):
                check_out_dt = datetime.fromisoformat(check_out).date()
            else:
                check_out_dt = check_out
        except Exception:
            return Response({'success': False, 'error': 'Invalid date format', 'status': 422}, status=422)

        # Date validation
        if check_in_dt >= check_out_dt:
            return Response({'success': False, 'error': 'Check-in must be before check-out', 'status': 422}, status=422)
        if check_in_dt < timezone.now().date():
            return Response({'success': False, 'error': 'Check-in must be in the future', 'status': 422}, status=422)

        # Room existence and capacity
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response({'success': False, 'error': 'Room not found', 'status': 404}, status=404)

        if int(guests) > room.max_guests:
            return Response({'success': False, 'error': 'Guest count exceeds room capacity', 'status': 422}, status=422)

        # Availability check (no overlaps)
        overlap = Booking.objects.filter(
            room=room,
            check_in__lt=check_out_dt,
            check_out__gt=check_in_dt,
            status__in=['pending', 'confirmed']
        ).exists()
        if overlap:
            return Response({'success': False, 'error': 'Room not available for selected dates', 'status': 422}, status=422)

        nights = (check_out_dt - check_in_dt).days
        total_price = room.price * nights

        booking = Booking.objects.create(
            room=room,
            check_in=check_in_dt,
            check_out=check_out_dt,
            guests=guests,
            total_price=total_price,
            guest_info=guest_info,
            status='pending'
        )

        data = {
            'id': booking.id,
            'roomId': str(room.id),
            'checkIn': booking.check_in.isoformat(),
            'checkOut': booking.check_out.isoformat(),
            'guests': booking.guests,
            'totalPrice': float(booking.total_price),
            'status': booking.status,
            'guestInfo': booking.guest_info,
            'createdAt': booking.created_at.isoformat(),
            'updatedAt': booking.updated_at.isoformat(),
        }
        return Response({'success': True, 'data': data}, status=201)


class UpdateBookingStatusView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, booking_id):
        if not _is_admin(request.user):
            return Response({'success': False, 'error': 'Forbidden', 'status': 403}, status=403)

        status_val = request.data.get('status')
        if status_val not in ['pending', 'confirmed', 'cancelled', 'completed']:
            return Response({'success': False, 'error': 'Invalid status', 'status': 422}, status=422)

        try:
            b = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({'success': False, 'error': 'Booking not found', 'status': 404}, status=404)

        b.status = status_val
        b.save(update_fields=['status', 'updated_at'])
        return Response({'success': True, 'data': {'id': b.id, 'status': b.status, 'updatedAt': b.updated_at.isoformat()}})
