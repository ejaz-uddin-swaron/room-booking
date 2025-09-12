from rest_framework import serializers
from .models import Booking


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
