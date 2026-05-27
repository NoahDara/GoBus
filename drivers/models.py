from django.db import models
from django.contrib.auth.models import User
from helpers.models import BaseModel


class Driver(BaseModel):
    """
    Represents a bus driver in the system.
    User account is created in the view when the driver is onboarded,
    and a password setup email is sent via send_onboarding_reset_password_mail().
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='driver',
        null=True,
        blank=True
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    license_number = models.CharField(max_length=50, unique=True)
    license_expiry = models.DateField()
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ]
    )
    profile_picture = models.ImageField(
        upload_to='drivers/profiles/',
        null=True,
        blank=True
    )
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.license_number}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"