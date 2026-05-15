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
    images = models.JSONField(default=list, blank=True)  # list of image URLs
    amenities = models.JSONField(default=list, blank=True)  # list of strings
    description = models.TextField(blank=True, default='')
    location = models.CharField(max_length=255)
    max_guests = models.IntegerField()
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    size = models.IntegerField()  # in square meters
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PropertyDocument(models.Model):
    DOCUMENT_TYPES = (
        ('license', 'License'),
        ('permit', 'Permit'),
        ('insurance', 'Insurance'),
        ('contract', 'Contract'),
        ('certificate', 'Certificate'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expiring-soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('renewed', 'Renewed'),
    )

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, default='other')
    description = models.TextField(blank=True, default='')
    file_url = models.TextField()
    upload_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    renewal_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    reminder_days = models.IntegerField(default=30)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-upload_date']

    def __str__(self):
        return self.name
