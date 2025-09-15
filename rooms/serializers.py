from rest_framework import serializers
from .models import Room


class RoomSerializer(serializers.ModelSerializer):
    # createdAt/updatedAt are omitted because current schema doesn't have them in migration
    images = serializers.SerializerMethodField()

    def get_images(self, obj):
        val = getattr(obj, 'images', None)
        if isinstance(val, list):
            return val
        if isinstance(val, str) and val:
            return [val]
        return []

    class Meta:
        model = Room
        fields = [
            'id', 'name', 'type', 'price', 'rating', 'reviews', 'images', 'amenities', 'description',
            'location', 'maxGuests', 'bedrooms', 'bathrooms', 'size', 'available'
        ]
