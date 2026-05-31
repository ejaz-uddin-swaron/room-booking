from rest_framework import serializers
from .models import Booking, RentSchedule, RentPayment, TenantAssignment


class BookingSerializer(serializers.ModelSerializer):
    roomId = serializers.CharField(source='room.id', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'roomId', 'check_in', 'check_out', 'guests', 'total_price', 'status', 'guest_info',
            'created_at', 'updated_at'
        ]


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
            'tenant_user', 'assignment',
            'payment_history', 'created_at', 'updated_at'
        ]


class RentScheduleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentSchedule
        fields = [
            'room_name', 'tenant_name', 'tenant_email', 'tenant_phone',
            'monthly_rent', 'due_day', 'start_date', 'end_date',
            'tenant_user', 'assignment'
        ]


class RentPaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentPayment
        fields = ['due_date', 'paid_date', 'amount', 'paid_amount', 'status', 'payment_method', 'notes']


class TenantAssignmentSerializer(serializers.ModelSerializer):
    tenantId = serializers.IntegerField(source='tenant.id', read_only=True)
    tenantUsername = serializers.CharField(source='tenant.username', read_only=True)
    tenantEmail = serializers.CharField(source='tenant.email', read_only=True)
    roomId = serializers.IntegerField(source='room.id', read_only=True)
    roomName = serializers.CharField(source='room.name', read_only=True)
    roomLocation = serializers.CharField(source='room.location', read_only=True)

    class Meta:
        model = TenantAssignment
        fields = [
            'id', 'tenantId', 'tenantUsername', 'tenantEmail',
            'roomId', 'roomName', 'roomLocation',
            'property_name', 'start_date', 'end_date', 'status',
            'monthly_rent', 'deposit', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TenantAssignmentCreateSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(write_only=True)
    room_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TenantAssignment
        fields = [
            'tenant_id', 'room_id', 'property_name',
            'start_date', 'end_date', 'status',
            'monthly_rent', 'deposit', 'notes'
        ]

    def create(self, validated_data):
        from django.contrib.auth.models import User
        from rooms.models import Room
        from .models import RentSchedule

        tenant_id = validated_data.pop('tenant_id')
        room_id = validated_data.pop('room_id')

        try:
            tenant = User.objects.get(id=tenant_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({'tenant_id': 'User not found'})

        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            raise serializers.ValidationError({'room_id': 'Room not found'})

        # Auto-fill property_name from room location if not provided
        if not validated_data.get('property_name'):
            validated_data['property_name'] = room.location

        assignment = TenantAssignment.objects.create(
            tenant=tenant,
            room=room,
            **validated_data
        )

        # Create a matching rent schedule so tenant views populate immediately.
        tenant_client = getattr(tenant, 'client', None)
        tenant_phone = getattr(tenant_client, 'mobile_no', '') if tenant_client else ''
        RentSchedule.objects.create(
            room_name=room.name,
            tenant_name=tenant.get_full_name() or tenant.username,
            tenant_email=tenant.email or '',
            tenant_phone=tenant_phone or '',
            monthly_rent=assignment.monthly_rent,
            due_day=1,
            start_date=assignment.start_date,
            end_date=assignment.end_date,
            status='active' if assignment.status == 'active' else assignment.status,
            tenant_user=tenant,
            assignment=assignment,
        )

        return assignment
