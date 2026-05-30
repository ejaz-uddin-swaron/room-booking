from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from rooms.models import Room


class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='bookings',
        null=True,  # Allow null for existing records during migration
        blank=True
    )
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    guest_info = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['check_in', 'check_out']),
            models.Index(fields=['room', 'status']),
        ]

    def __str__(self):
        username = self.user.username if self.user else 'Guest'
        return f"Booking #{self.pk} - {self.room.name} by {username}"


class TenantAssignment(models.Model):
    """Links a tenant user to a specific room/property."""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('pending', 'Pending'),
    )

    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='tenant_assignments')
    property_name = models.CharField(max_length=255, db_index=True)  # matches Room.location
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'room'],
                condition=models.Q(status='active'),
                name='unique_active_tenant_room'
            )
        ]

    def __str__(self):
        return f"{self.tenant.username} → {self.room.name} ({self.status})"


class RentSchedule(models.Model):
    room_name = models.CharField(max_length=255)
    tenant_name = models.CharField(max_length=255)
    tenant_email = models.EmailField(blank=True, default='')
    tenant_phone = models.CharField(max_length=50, blank=True, default='')
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    due_day = models.IntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='active')
    # New FK links to proper user/assignment (nullable for backward compat)
    tenant_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='rent_schedules')
    assignment = models.ForeignKey(TenantAssignment, null=True, blank=True, on_delete=models.SET_NULL, related_name='rent_schedules')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.room_name} - {self.tenant_name} (${self.monthly_rent}/month)"


class RentPayment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('overdue', 'Overdue'),
    )

    schedule = models.ForeignKey(RentSchedule, on_delete=models.CASCADE, related_name='payment_history')
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=100, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f"Payment {self.due_date} - {self.status}"
