from rest_framework import serializers
from .models import Booking, RentSchedule, RentPayment


class BookingSerializer(serializers.ModelSerializer):
    roomId = serializers.CharField(source='room.id', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'roomId', 'check_in', 'check_out', 'guests', 'total_price', 'status', 'guest_info',
            'created_at', 'updated_at'
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    roomId = serializers.CharField(write_only=True)

    class Meta:
        model = Booking
        fields = ['roomId', 'check_in', 'check_out', 'guests', 'guest_info']


class RentPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentPayment
        fields = [
            'id', 'due_date', 'paid_date', 'amount', 'paid_amount', 'status',
            'payment_method', 'notes', 'created_at'
        ]


class RentScheduleSerializer(serializers.ModelSerializer):
    payment_history = RentPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = RentSchedule
        fields = [
            'id', 'room_name', 'tenant_name', 'tenant_email', 'tenant_phone',
            'monthly_rent', 'due_day', 'start_date', 'end_date', 'status',
            'payment_history', 'created_at', 'updated_at'
        ]


class RentScheduleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentSchedule
        fields = [
            'room_name', 'tenant_name', 'tenant_email', 'tenant_phone',
            'monthly_rent', 'due_day', 'start_date', 'end_date'
        ]


class RentPaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentPayment
        fields = ['due_date', 'paid_date', 'amount', 'paid_amount', 'status', 'payment_method', 'notes']
