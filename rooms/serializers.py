from rest_framework import serializers
from .models import Room, PropertyDocument


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


class PropertyDocumentSerializer(serializers.ModelSerializer):
    roomId = serializers.IntegerField(source='room.id', required=False, allow_null=True)

    class Meta:
        model = PropertyDocument
        fields = [
            'id', 'roomId', 'name', 'type', 'description', 'file_url', 'upload_date',
            'expiry_date', 'renewal_date', 'status', 'reminder_days', 'notes'
        ]


class PropertyDocumentCreateSerializer(serializers.ModelSerializer):
    roomId = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = PropertyDocument
        fields = [
            'roomId', 'name', 'type', 'description', 'file_url', 'expiry_date',
            'renewal_date', 'status', 'reminder_days', 'notes'
        ]
