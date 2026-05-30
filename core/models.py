from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    """In-app notification for users (tenants, admins)."""
    TYPES = (
        ('rent_due', 'Rent Due'),
        ('rent_overdue', 'Rent Overdue'),
        ('document_review', 'Document Review'),
        ('assignment', 'Assignment'),
        ('general', 'General'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=30, choices=TYPES, default='general')
    read = models.BooleanField(default=False)
    link = models.CharField(max_length=500, blank=True, default='')  # optional deep link
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title} ({'read' if self.read else 'unread'})"
