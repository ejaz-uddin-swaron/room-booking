from rest_framework import serializers
from .models import Room


class RoomSerializer(serializers.ModelSerializer):
    # Map camelCase to snake_case for API compatibility
    maxGuests = serializers.IntegerField(source='max_guests')

    class Meta:
        model = Room
        fields = [
            'id', 'name', 'type', 'price', 'rating', 'reviews', 'images', 'amenities', 'description',
            'location', 'maxGuests', 'bedrooms', 'bathrooms', 'size', 'available'
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
