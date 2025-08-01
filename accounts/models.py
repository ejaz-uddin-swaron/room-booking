from django.db import models
from django.contrib.auth.models import User

# Create your models here.

ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    )


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client')
    image = models.ImageField(upload_to='accounts/images')
    mobile_no = models.CharField(max_length=12)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'