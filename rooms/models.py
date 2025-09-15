from django.db import models


class Room(models.Model):
    ROOM_TYPES = (
        ('villa', 'Villa'),
        ('apartment', 'Apartment'),
        ('suite', 'Suite'),
    )

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=ROOM_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.FloatField(default=0)
    reviews = models.IntegerField(default=0)
    images = models.JSONField(default=list)  # list of image URLs
    amenities = models.JSONField(default=list)  # list of strings
    description = models.TextField()
    location = models.CharField(max_length=255)
    maxGuests = models.IntegerField()
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    size = models.IntegerField()  # in square meters
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
