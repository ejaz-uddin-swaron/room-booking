from django.db import models
from django.contrib.auth.models import User


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
        ('id', 'ID Document'),
        ('proof_of_address', 'Proof of Address'),
        ('reference', 'Reference Letter'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expiring-soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('renewed', 'Renewed'),
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    property_id = models.CharField(max_length=255, db_index=True)  # Required consolidated field
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='property_documents', null=True, blank=True)
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_documents', null=True, blank=True)
    assignment = models.ForeignKey(
        'bookings_app.TenantAssignment', on_delete=models.SET_NULL, related_name='property_documents', null=True, blank=True
    )
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents')
    
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, default='other')
    description = models.TextField(blank=True, default='')
    file_url = models.TextField()
    upload_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    renewal_date = models.DateField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    reminder_days = models.IntegerField(default=30)
    notes = models.TextField(blank=True, default='')
    admin_notes = models.TextField(blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-upload_date']

    def __str__(self):
        return f"{self.property_id} - {self.name} ({self.type})"



class PropertyImage(models.Model):
    """Property-level images (not room-level). Identified by property_name which matches Room.location."""
    property_name = models.CharField(max_length=255, db_index=True)
    image_url = models.TextField()
    caption = models.CharField(max_length=255, blank=True, default='')
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return f"{self.property_name} - Image {self.pk}"


class BookingInterest(models.Model):
    """Public users expressing interest in a property/room."""
    STATUS_CHOICES = (
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('closed', 'Closed'),
    )

    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, default='')
    message = models.TextField(blank=True, default='')
    room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL, related_name='interests')
    property_name = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Interest from {self.name} - {self.property_name or 'General'}"
