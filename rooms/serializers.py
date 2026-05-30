from rest_framework import serializers
from .models import Room, PropertyDocument, PropertyImage, BookingInterest


class RoomSerializer(serializers.ModelSerializer):
    # Map camelCase to snake_case for API compatibility
    maxGuests = serializers.IntegerField(source='max_guests')
    presenceStatus = serializers.CharField(read_only=True, default='')

    class Meta:
        model = Room
        fields = [
            'id', 'name', 'type', 'price', 'rating', 'reviews', 'images', 'amenities', 'description',
            'location', 'maxGuests', 'bedrooms', 'bathrooms', 'size', 'available', 'presenceStatus'
        ]

    def to_representation(self, instance):
        """Normalize images field on output to always be a list."""
        data = super().to_representation(instance)
        val = data.get('images')
        if isinstance(val, list):
            data['images'] = val
        elif isinstance(val, str) and val:
            data['images'] = [val]
        else:
            data['images'] = []
        return data


class PublicRoomSerializer(serializers.ModelSerializer):
    """Limited serializer for public-facing room data. No sensitive admin metadata."""
    maxGuests = serializers.IntegerField(source='max_guests')

    class Meta:
        model = Room
        fields = [
            'id', 'name', 'type', 'price', 'rating', 'reviews', 'images', 'amenities',
            'description', 'location', 'maxGuests', 'bedrooms', 'bathrooms', 'size', 'available'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        val = data.get('images')
        if isinstance(val, list):
            data['images'] = val
        elif isinstance(val, str) and val:
            data['images'] = [val]
        else:
            data['images'] = []
        return data


class PropertyDocumentSerializer(serializers.ModelSerializer):
    propertyId = serializers.CharField(source='property_id', required=False, allow_blank=True)
    roomId = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    tenantId = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    assignmentId = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    fileUrl = serializers.CharField(source='file_url')
    adminNotes = serializers.CharField(source='admin_notes', required=False, allow_blank=True)
    expiryDate = serializers.DateField(source='expiry_date', required=False, allow_null=True)
    renewalDate = serializers.DateField(source='renewal_date', required=False, allow_null=True)
    reminderDays = serializers.IntegerField(source='reminder_days', required=False)
    uploadDate = serializers.DateField(source='upload_date', read_only=True)
    reviewedAt = serializers.DateTimeField(source='reviewed_at', read_only=True)

    class Meta:
        model = PropertyDocument
        fields = [
            'id', 'propertyId', 'roomId', 'tenantId', 'assignmentId',
            'name', 'type', 'description', 'fileUrl', 'status',
            'reminderDays', 'notes', 'adminNotes', 'metadata',
            'uploadDate', 'expiryDate', 'renewalDate', 'reviewedAt'
        ]
        read_only_fields = ['id', 'uploadDate', 'reviewedAt']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Add read-only representation for relations
        ret['roomId'] = instance.room_id
        ret['tenantId'] = instance.tenant_id
        ret['tenantUsername'] = instance.tenant.username if instance.tenant else None
        ret['tenantEmail'] = instance.tenant.email if instance.tenant else None
        ret['assignmentId'] = instance.assignment_id
        ret['uploadedBy'] = instance.uploaded_by.username if instance.uploaded_by else None
        return ret

    def create(self, validated_data):
        room_id = validated_data.pop('roomId', None)
        tenant_id = validated_data.pop('tenantId', None)
        assignment_id = validated_data.pop('assignmentId', None)

        if room_id:
            validated_data['room_id'] = room_id
        if tenant_id:
            validated_data['tenant_id'] = tenant_id
        if assignment_id:
            validated_data['assignment_id'] = assignment_id

        # Set uploaded_by automatically if request is available
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['uploaded_by'] = request.user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        room_id = validated_data.pop('roomId', None)
        tenant_id = validated_data.pop('tenantId', None)
        assignment_id = validated_data.pop('assignmentId', None)

        # Handle explicit FK updates if passed in initial_data
        initial = self.initial_data
        if 'roomId' in initial:
            instance.room_id = room_id
        if 'tenantId' in initial:
            instance.tenant_id = tenant_id
        if 'assignmentId' in initial:
            instance.assignment_id = assignment_id

        return super().update(instance, validated_data)


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'property_name', 'image_url', 'caption', 'is_primary', 'sort_order', 'created_at']
        read_only_fields = ['id', 'created_at']


class BookingInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingInterest
        fields = ['id', 'name', 'email', 'phone', 'message', 'room', 'property_name', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']


class BookingInterestCreateSerializer(serializers.ModelSerializer):
    roomId = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = BookingInterest
        fields = ['name', 'email', 'phone', 'message', 'roomId', 'property_name']

    def create(self, validated_data):
        room_id = validated_data.pop('roomId', None)
        if room_id:
            from rooms.models import Room
            validated_data['room'] = Room.objects.filter(id=room_id).first()
        return super().create(validated_data)
