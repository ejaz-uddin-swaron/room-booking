from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rooms.permissions import IsAdmin
from rooms.models import Room
from .models import Booking
from . import serializers


class BookingsView(APIView):
    """
    Admin-only booking management.
    GET: retrieve all bookings.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Booking.objects.select_related('room', 'user').all()
        data = []
        for b in qs:
            data.append({
                'id': b.id,
                'userId': b.user.id if b.user else None,
                'username': b.user.username if b.user else 'Guest',
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


class UpdateBookingStatusView(APIView):
    """Admin-only booking status update."""
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        status_val = request.data.get('status')
        if status_val not in ['pending', 'confirmed', 'cancelled', 'completed']:
            return Response({'success': False, 'error': 'Invalid status', 'status': 422}, status=422)

        try:
            b = Booking.objects.get(id=pk)
        except Booking.DoesNotExist:
            return Response({'success': False, 'error': 'Booking not found', 'status': 404}, status=404)

        b.status = status_val
        b.save(update_fields=['status', 'updated_at'])
        return Response({'success': True, 'data': {'id': b.id, 'status': b.status, 'updatedAt': b.updated_at.isoformat()}})


class RentScheduleView(APIView):
    """Admin-only rent schedule management."""
    permission_classes = [IsAdmin]

    def get(self, request):
        from .models import RentSchedule
        schedules = RentSchedule.objects.all().prefetch_related('payment_history')
        serializer = serializers.RentScheduleSerializer(schedules, many=True)
        return Response({'success': True, 'data': serializer.data})

    def post(self, request):
        from .models import RentSchedule
        serializer = serializers.RentScheduleCreateSerializer(data=request.data)
        if serializer.is_valid():
            schedule = serializer.save()
            return Response({'success': True, 'data': serializers.RentScheduleSerializer(schedule).data}, status=201)
        return Response({'success': False, 'error': serializer.errors}, status=400)


class RentScheduleDetailView(APIView):
    """Admin-only rent schedule detail, update, delete."""
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        from .models import RentSchedule
        try:
            schedule = RentSchedule.objects.prefetch_related('payment_history').get(pk=pk)
            return Response({'success': True, 'data': serializers.RentScheduleSerializer(schedule).data})
        except RentSchedule.DoesNotExist:
            return Response({'success': False, 'error': 'Schedule not found', 'status': 404}, status=404)

    def put(self, request, pk):
        from .models import RentSchedule
        try:
            schedule = RentSchedule.objects.get(pk=pk)
            serializer = serializers.RentScheduleSerializer(schedule, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'success': True, 'data': serializer.data})
            return Response({'success': False, 'error': serializer.errors}, status=400)
        except RentSchedule.DoesNotExist:
            return Response({'success': False, 'error': 'Schedule not found', 'status': 404}, status=404)

    def delete(self, request, pk):
        from .models import RentSchedule
        try:
            schedule = RentSchedule.objects.get(pk=pk)
            schedule.delete()
            return Response({'success': True, 'message': 'Schedule deleted'})
        except RentSchedule.DoesNotExist:
            return Response({'success': False, 'error': 'Schedule not found', 'status': 404}, status=404)


class RentPaymentView(APIView):
    """Admin-only rent payment recording."""
    permission_classes = [IsAdmin]

    def post(self, request, schedule_id):
        from .models import RentSchedule, RentPayment
        try:
            schedule = RentSchedule.objects.get(pk=schedule_id)
        except RentSchedule.DoesNotExist:
            return Response({'success': False, 'error': 'Schedule not found', 'status': 404}, status=404)

        serializer = serializers.RentPaymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save(schedule=schedule)
            return Response({'success': True, 'data': serializers.RentPaymentSerializer(payment).data}, status=201)
        return Response({'success': False, 'error': serializer.errors}, status=400)


class RentReminderView(APIView):
    """Admin-only rent due reminders."""
    permission_classes = [IsAdmin]

    def get(self, request):
        from .models import RentSchedule
        today = timezone.now().date()
        reminders = []

        schedules = RentSchedule.objects.all().prefetch_related('payment_history')
        for schedule in schedules:
            if schedule.status != 'active':
                continue

            last_day = (timezone.datetime(today.year, today.month, 28) + timezone.timedelta(days=4)).replace(day=1) - timezone.timedelta(days=1)
            safe_due_day = min(schedule.due_day, last_day.day)
            due_date = timezone.datetime(today.year, today.month, safe_due_day).date()
            days_until_due = (due_date - today).days

            if days_until_due <= 5 and days_until_due >= -30:
                current_month = today.strftime('%Y-%m')
                payment_exists = any(
                    p.due_date.strftime('%Y-%m') == current_month and p.status == 'paid'
                    for p in schedule.payment_history.all()
                )
                if not payment_exists:
                    reminders.append({
                        'id': f"rent-{schedule.id}-{current_month}",
                        'scheduleId': schedule.id,
                        'roomName': schedule.room_name,
                        'tenantName': schedule.tenant_name,
                        'dueDate': due_date.isoformat(),
                        'amount': float(schedule.monthly_rent),
                        'dismissed': False,
                    })

        return Response({'success': True, 'data': reminders})
