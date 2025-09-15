from django.db import models

class Room(models.Model):
    ROOM_TYPES = (
        ('delux','Delux'),
        ('double delux','Double Delux'),
    )

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=ROOM_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.FloatField(default=0)
    reviews = models.IntegerField(default=0)
    images = models.URLField(default=list)  # list of image URLs
    amenities = models.JSONField(default=list)  # list of strings
    description = models.TextField()
    location = models.CharField(max_length=255)
    max_guests = models.IntegerField()
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    size = models.IntegerField()  # in square meters
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
